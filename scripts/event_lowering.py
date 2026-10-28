"""Safe fixed registry lowering. This module only fills parameters and composes S51 calls."""
import copy,json,math
from jsonschema import ValidationError
from primitive_sampler import sha,norm,sub,mul,add,unit,frames,sample_track
from primitive_runtime import compile_program
from primitive_channel_registry import channels
from author_graph_validator import require_valid
from execution_state_chain import ExecutionStateChain
from event_lowering_registry import REGISTRY,SPACING,AUTHOR_FIELDS,FIELDS_BY_EVENT
from lowering_validator import *
from orientation_feasibility import channel_plan

def binding(context,actor):
    if actor not in context['entity_bindings']:raise StopLowering('NEEDS_AUTHOR_INPUT','EXECUTION_BINDING_MISSING',[actor])
    return context['entity_bindings'][actor]
def new_primitive(p,typ,actor,event,entry,params,suffix=''):
    return dict(primitive_version='EXECUTION-PRIMITIVE/1.0',primitive_id='PRIM_'+event['event_id'].upper()+suffix,primitive_type=typ,actor=actor,subjects=[],start_time=event['start'],end_time=event['end'],entry_state=copy.deepcopy(entry),parameters=params,exit_requirements={},continuity_contract=copy.deepcopy(p['continuity_contract']),provenance={'source':'S52 fixed registry '+event['event_type'],'source_author_id':event['event_id'],'graph_sha256':p['provenance']['graph_sha256']})
def read_value(p,values,key,default=None,required=False,source='AUTHOR_EXPLICIT'):
    if required and key not in p['required_inputs']:p['required_inputs'].append(key)
    if key in values:
        if key in p['resolved_inputs']:return p['resolved_inputs'][key]['value']
        return record(p,key,values[key],source,p['event_id']+'.world_intent.'+key)
    if required:need(p,key)
    if default is not None:return record(p,key,default,'TECHNICAL_DEFAULT','S52 fixed rule default: '+key,'EXPLICIT_LOW_RISK_DEFAULT','MEDIUM')
    return default
def composition(primitives):
    ops=[]
    for i,a in enumerate(primitives):
        for b in primitives[i+1:]:
            if a['actor']!=b['actor']:continue
            overlap=min(a['end_time'],b['end_time'])-max(a['start_time'],b['start_time'])
            if overlap< -1e-8:continue
            common=set(channels(a)['WRITES'])&set(channels(b)['WRITES'])
            if a['primitive_type']=='OFFSET_PATH' and a['parameters'].get('base_primitive')==b['primitive_id'] or b['primitive_type']=='OFFSET_PATH' and b['parameters'].get('base_primitive')==a['primitive_id']:kind='EXPLICIT_ADDITIVE_OFFSET'
            elif common and abs(overlap)<1e-8:kind='SEQUENTIAL'
            elif not common and overlap>0:kind='ORTHOGONAL_CHANNEL'
            elif common:raise StopLowering('BLOCKED_BY_CONSTRAINT','CHANNEL_CONFLICT',[a['primitive_id'],b['primitive_id']])
            else:continue
            members=[a['primitive_id'],b['primitive_id']] if a['start_time']<=b['start_time'] else [b['primitive_id'],a['primitive_id']]
            ops.append({'type':kind,'members':members})
    return ops
def move_params(p,v,entry,dest):
    spacing=read_value(p,v,'spacing',required=True)
    if spacing not in SPACING:raise StopLowering('UNSUPPORTED','UNSUPPORTED_SPACING',[spacing])
    q={'end_position':dest,'path_type':'LINEAR','timing_profile':SPACING[spacing],'entry_velocity':entry['velocity']}
    exit_v=read_value(p,v,'arrival_velocity')
    if exit_v is not None:q['exit_velocity']=exit_v
    elif v.get('allow_speed_derivation') is True:record(p,'arrival_velocity',None,'DERIVED',p['event_id']+'.spacing','S51_BOUNDARY_SPEED_SOLVE','MEDIUM')
    else:need(p,'arrival_velocity_or_allow_speed_derivation')
    if 'peak_speed' in v:q['peak_velocity']=read_value(p,v,'peak_speed')
    if 'path' in v:q['points']=read_value(p,v,'path');q['path_type']='POLYLINE'
    return q

def event_plan(graph,event,context,chain):
    p=plan(graph,event['event_id'],event['event_type'],event['world_intent']);typ=event['event_type']
    try:
        if typ not in REGISTRY:raise StopLowering('UNSUPPORTED','NO_SAFE_EVENT_RULE',[typ])
        v,confidence=parse_evidence(event['world_intent']);p['confidence']=confidence
        if set(v)-AUTHOR_FIELDS:raise StopLowering('NEEDS_AUTHOR_INPUT','UNRECOGNIZED_AUTHOR_FIELDS',sorted(set(v)-AUTHOR_FIELDS))
        if set(v)-FIELDS_BY_EVENT[typ]:raise StopLowering('NEEDS_AUTHOR_INPUT','AUTHOR_FIELD_NOT_APPLICABLE_TO_EVENT',sorted(set(v)-FIELDS_BY_EVENT[typ]))
        for key in ('destination','exit_point','entry_point','target_direction','target_point','incoming_threat_direction','dodge_direction','base_destination','release_direction','attachment_offset'):
            if key in v and (not isinstance(v[key],list) or len(v[key])!=3 or any(not isinstance(x,(int,float)) or isinstance(x,bool) or not math.isfinite(x) for x in v[key])):raise StopLowering('NEEDS_AUTHOR_INPUT','INVALID_AUTHOR_VECTOR',[key])
            if key in v and key.endswith('direction') and norm(v[key])<1e-9:raise StopLowering('NEEDS_AUTHOR_INPUT','ZERO_DIRECTION',[key])
        for key in ('return_to_route','allow_speed_derivation'):
            if key in v and not isinstance(v[key],bool):raise StopLowering('NEEDS_AUTHOR_INPUT','INVALID_AUTHOR_BOOLEAN',[key])
        if len(event['actor'])!=1:need(p,'single_actor')
        actor=event['actor'][0]
        if typ=='RELEASE' and not actor.startswith('PROJ_'):
            candidates=[e for e in graph['entities'] if e['id'] in event['targets'] and e['owner']==actor]
            if len(candidates)!=1:raise StopLowering('AMBIGUOUS','RELEASE_OBJECT_NOT_UNIQUE',['object'],[e['id'] for e in candidates])
            actor=candidates[0]['id']
        runtime_actor=binding(context,actor);p['provenance']['affected_entity']=actor
        p['dependencies']=[d for d in graph['dependencies'] if d['event_id']==event['event_id'] or d['depends_on']==event['event_id']]
        p['constraints']=constraints_for(graph,event['event_id'],actor,[event['start'],event['end']]);v=constraint_inputs(p['constraints'],v,p)
        channel='PROJECTILE_TRANSFORM' if typ in ('RELEASE','PROJECTILE_TRAVEL') else 'HEAD_ROTATION' if typ=='LOOK' else 'ROOT_ROTATION' if typ=='TURN' else 'ROOT_LOCATION'
        if typ in ('LOOK','TURN'):
            level=read_value(p,v,'body_level')
            if level is None:level=record(p,'body_level','HEAD' if typ=='LOOK' else 'ROOT','TECHNICAL_DEFAULT','S52 explicit LOOK/ TURN channel policy','LOW_RISK_CHANNEL_DEFAULT','MEDIUM')
            if level not in ('ROOT','BODY','HEAD'):raise StopLowering('AMBIGUOUS','UNKNOWN_BODY_LEVEL',['body_level'])
            channel=level+'_ROTATION'
        st=chain.entry(actor,event,channel,p,v.get('entry'),typ=='RECOVERY')
        record(p,'actor',actor,'AUTHOR_EXPLICIT',event['event_id']+'.actor');record(p,'start_time',event['start'],'AUTHOR_EXPLICIT',event['event_id']+'.start');record(p,'end_time',event['end'],'AUTHOR_EXPLICIT',event['event_id']+'.end')
        primitives=[]
        if typ in ('MOVE','ENTER','EXIT','PROJECTILE_TRAVEL'):
            dest=read_value(p,v,'destination')
            if dest is None and 'exit_point' in v:dest=read_value(p,v,'exit_point')
            if dest is None and 'path' in v:dest=read_value(p,v,'path')[-1]
            if typ=='ENTER':
                point=read_value(p,v,'entry_point',required=True)
                if norm(sub(point,st['position']))>1e-5:raise StopLowering('BLOCKED_BY_CONSTRAINT','STATE_CONFLICT',['entry_point'])
            if dest is None and typ=='PROJECTILE_TRAVEL':
                contacts=[e for e in graph['events'] if e['event_type']=='CONTACT' and any(d['event_id']==e['event_id'] and d['depends_on']==event['event_id'] for d in graph['dependencies'])]
                values=[parse_evidence(e['world_intent'])[0].get('target_point') for e in contacts];values=[x for x in values if x is not None]
                if len(values)==1:dest=record(p,'destination',values[0],'DEPENDENCY',[e['event_id'] for e in contacts],'CONTACT_REGION_ONLY; no Contact action')
                elif len(values)>1:raise StopLowering('AMBIGUOUS','MULTIPLE_TERMINAL_REGIONS',['destination'],values)
            if dest is None:need(p,'destination_or_explicit_exit_point')
            if 'destination' not in p['resolved_inputs']:record(p,'destination',dest,'AUTHOR_EXPLICIT',event['event_id']+'.world_intent.endpoint')
            q=move_params(p,v,st,dest)
            if typ=='PROJECTILE_TRAVEL':
                if st['ownership_state']!='FREE':raise StopLowering('BLOCKED_BY_CONSTRAINT','PROJECTILE_NOT_RELEASED',['previous_RELEASE_exit'])
                q['channel']='PROJECTILE_TRANSFORM'
            primitives=[new_primitive(p,'MOVE_PROFILE',runtime_actor,event,st,q)]
        elif typ in ('LOOK','TURN'):
            choices=[k for k in ('target_direction','target_point','target_entity') if k in v]
            if not choices:need(p,'target_direction_or_point_or_entity')
            if len(choices)>1:raise StopLowering('AMBIGUOUS','MULTIPLE_ORIENTATION_TARGETS',choices)
            key=choices[0];target=read_value(p,v,key);strategy=read_value(p,v,'orientation_strategy')
            if strategy is None: strategy='HEAD_ONLY' if typ=='LOOK' else 'BODY_ROOT_TURN'
            if strategy not in ('HEAD_ONLY','HEAD_LEAD_BODY_FOLLOW','BODY_ROOT_TURN'):raise StopLowering('AMBIGUOUS','UNKNOWN_ORIENTATION_STRATEGY',['orientation_strategy'])
            q={'channel':level,'target_type':{'target_direction':'WORLD_DIRECTION','target_point':'WORLD_POINT','target_entity':'ENTITY'}[key],'target':binding(context,target) if key=='target_entity' else target,'orientation_mode':read_value(p,v,'turn_mode','SMOOTH'),'lead_delay':read_value(p,v,'lead_delay_s',0),'max_angular_speed':read_value(p,v,'max_turn_rate_deg_s',required=True)}
            if q['orientation_mode']=='SNAP':raise StopLowering('NEEDS_AUTHOR_INPUT','SCOPED_DISCONTINUITY_AUTHORITY_REQUIRED',['angular discontinuity authorization'])
            p['provenance']['orientation_strategy']=strategy
            p['provenance']['orientation_channel_plan']=channel_plan(strategy,read_value(p,v,'head_lead_time',0),read_value(p,v,'body_delay',0),read_value(p,v,'root_delay',0)) if strategy=='HEAD_LEAD_BODY_FOLLOW' else {'strategy':strategy,'primitive':'ORIENT_TO','source':'DIRECTOR_PREFLIGHT/1.0'}
            if strategy=='HEAD_LEAD_BODY_FOLLOW':
                lead=read_value(p,v,'head_lead_time',required=True);delay=read_value(p,v,'body_delay',required=True)
                if lead<0 or delay<0 or lead+delay>=event['end']-event['start']:raise StopLowering('NEEDS_AUTHOR_INPUT','INVALID_ORIENTATION_PHASES',['head_lead_time','body_delay'])
                head=copy.deepcopy(q);head['channel']='HEAD';head.pop('angular_timing_profile',None);head['target_fraction']=read_value(p,v,'head_target_fraction',0.15)
                body=copy.deepcopy(q);body['channel']=read_value(p,v,'body_level','BODY');body.pop('angular_timing_profile',None)
                hp=new_primitive(p,'ORIENT_TO',runtime_actor,event,st,head,'_HEAD');bp=new_primitive(p,'ORIENT_TO',runtime_actor,event,st,body,'_BODY')
                hp['end_time']=min(event['end'],event['start']+lead);bp['start_time']=event['start']+lead+delay
                if bp['start_time']>=bp['end_time']:raise StopLowering('NEEDS_AUTHOR_INPUT','INVALID_ORIENTATION_PHASES',['body_delay'])
                primitives=[hp,bp]
                p['provenance']['allow_runtime_clamp']=True
            else:
                primitives=[new_primitive(p,'ORIENT_TO',runtime_actor,event,st,q)]
        elif typ=='DODGE':
            read_value(p,v,'incoming_threat_direction',required=True);direction=read_value(p,v,'dodge_direction')
            if direction is None:
                choices=[x for c in p['constraints'] for x in json.loads(c['requirement']).get('allowed_dodge_directions',[])]
                if len(choices)>1:raise StopLowering('AMBIGUOUS','MULTIPLE_SAFE_DODGE_DIRECTIONS',['dodge_direction'],choices)
                if len(choices)==1:direction=record(p,'dodge_direction',choices[0],'CONSTRAINT',[c['constraint_id'] for c in p['constraints']],'EXPLICIT_SINGLE_ALLOWED_DIRECTION')
                else:need(p,'dodge_direction')
            offset=read_value(p,v,'offset_m',required=True);dest=read_value(p,v,'base_destination',required=True);return_route=read_value(p,v,'return_to_route',required=True)
            q=move_params(p,v,st,dest);base=new_primitive(p,'MOVE_PROFILE',runtime_actor,event,st,q,'_BASE')
            off=new_primitive(p,'OFFSET_PATH',runtime_actor,event,st,{'base_primitive':base['primitive_id'],'offset_direction':direction,'offset_distance':offset,'peak_time':event['peak'],'return_mode':'RETURN_TO_BASE' if return_route else 'KEEP_OFFSET'},'_OFFSET');primitives=[base,off]
        elif typ=='RELEASE':
            ent=next(e for e in graph['entities'] if e['id']==actor);owner=ent['owner']
            if not owner:need(p,'owner')
            if st['ownership_state']!='ATTACHED':raise StopLowering('BLOCKED_BY_CONSTRAINT','ATTACHMENT_STATE_CONFLICT',['ATTACHED entry'])
            direction=read_value(p,v,'release_direction');speed=read_value(p,v,'release_speed')
            if direction is None:
                children=[e for e in graph['events'] if e['event_type']=='PROJECTILE_TRAVEL' and e['actor']==[actor] and any(d['event_id']==e['event_id'] and d['depends_on']==event['event_id'] for d in graph['dependencies'])]
                targets=[parse_evidence(e['world_intent'])[0].get('destination') for e in children];targets=[x for x in targets if x is not None]
                if len(targets)>1:raise StopLowering('AMBIGUOUS','MULTIPLE_PROJECTILE_PATHS',['release_direction'],targets)
                if len(targets)==1:
                    release_time=read_value(p,v,'release_time',required=True);socket=read_value(p,v,'attachment_offset',required=True)
                    owners=[x for x in chain.entries if x['actor']==owner and 'ROOT_LOCATION' in x['channels'] and x['start']<=release_time<=x['end']]
                    if not owners:need(p,'owner_evaluated_position_at_release')
                    # S51 attachment offset is explicitly in world axes; reuse its path sampler.
                    release_position=add(sample_track(owners[-1]['fragment']['world_samples'],release_time),socket)
                    direction=record(p,'release_direction',unit(sub(targets[0],release_position)),'DERIVED',[e['event_id'] for e in children]+[owners[-1]['event_id']],'DERIVED_FROM_DEPENDENCY; evaluated release origin to explicit endpoint')
                else:need(p,'release_direction_or_dependent_path')
            if speed is None:need(p,'release_speed')
            q={'owner':binding(context,owner),'detach_time':read_value(p,v,'release_time',required=True),'detach_velocity':speed,'detach_direction':direction,'inherit_owner_velocity':read_value(p,v,'owner_velocity_fraction',required=True),'attachment_transform':{'position':read_value(p,v,'attachment_offset',required=True)},'release_ramp_duration':read_value(p,v,'release_acceleration_duration',0)}
            record(p,'owner',owner,'ENTITY_STATE',actor+'.owner');pr=new_primitive(p,'ATTACH_DETACH',runtime_actor,event,st,q);pr['native_identity']={'previs_entity_id':actor,'previs_owner_id':owner,'previs_event_id':event['event_id'],'previs_projectile_id':actor if actor.startswith('PROJ_') else '', 'previs_weapon_id':actor if actor.startswith('WPN_') else '', 'previs_role':ent['type']};pr['exit_requirements']={'ownership_state':'FREE'};primitives=[pr]
        elif typ=='RECOVERY':
            exit_v=read_value(p,v,'arrival_velocity')
            if exit_v is None:
                stable=read_value(p,v,'stability',required=True)
                if stable not in ('stop','stable'):need(p,'explicit_stability_target')
                exit_v=record(p,'arrival_velocity',[0.,0.,0.],'DERIVED',event['event_id']+'.world_intent.stability','EXPLICIT_STOP_INTENT_TO_ZERO_VELOCITY')
            q={'entry_velocity':st['velocity'],'exit_velocity':exit_v,'duration':event['end']-event['start'],'displacement_limit':read_value(p,v,'displacement_limit',required=True),'direction_retention':read_value(p,v,'retain_direction',1.)}
            primitives=[new_primitive(p,'RECOVERY_PROFILE',runtime_actor,event,st,q)]
        p['primitive_sequence']=primitives;p['exit_requirements']={a['primitive_id']:a['exit_requirements'] for a in primitives};check_locks(graph,p,primitives,actor,[event['start'],event['end']],context.get('overrides'))
        if confidence=='LOW':raise StopLowering('NEEDS_AUTHOR_INPUT','LOW_CONFIDENCE_REQUIRES_CONFIRMATION',['confirmed author values'])
        p['lowering_status']='READY';return p,None
    except StopLowering as stop:return p,request(p,stop)

def ordered_events(graph):
    events={e['event_id']:e for e in graph['events']};deps={k:set() for k in events}
    for d in graph['dependencies']:deps[d['event_id']].add(d['depends_on'])
    for e in events.values():
        if e['source_event']:deps[e['event_id']].add(e['source_event'])
        try:v,_=parse_evidence(e['world_intent'])
        except StopLowering:v={}
        targets=[v.get('target_entity')]
        if e['event_type']=='RELEASE':
            actor=e['actor'][0] if e['actor'] else None;targets+=[x['owner'] for x in graph['entities'] if x['id']==actor]
        for other in events.values():
            if other['event_id']!=e['event_id'] and other['event_type'] in ('MOVE','ENTER','EXIT','DODGE','PROJECTILE_TRAVEL','RECOVERY') and other['start']<=e['end'] and other['end']>=e['start'] and any(t in other['actor'] for t in targets):deps[e['event_id']].add(other['event_id'])
    out=[]
    while deps:
        ready=sorted([k for k,v in deps.items() if not v],key=lambda k:(events[k]['start'],events[k]['event_type'] not in ('MOVE','ENTER','EXIT'),k))
        if not ready:raise ValueError('LOWERING_READ_DEPENDENCY_CYCLE')
        k=ready[0];out.append(events[k]);deps.pop(k)
        for v in deps.values():v.discard(k)
    return out

def lower_graph(graph,context):
    require_valid(graph,for_compile=True)
    original_graph=graph
    stabilized=context.get('contract_policy')=='S53R/1.0'
    alignment=[];evaluation=None
    if stabilized:
        from timebase import align_execution_graph
        from lowering_scheduler import schedule
        graph,alignment=align_execution_graph(graph,context.get('time_alignment'))
        evaluation=schedule(graph)
    chain=ExecutionStateChain(graph,context);plans=[];requests=[];primitives=[];bundle=None;runtime_calls=0
    program={'program_version':'EXECUTION-PRIMITIVE/1.0','timebase':copy.deepcopy(graph['timebase']),'primitives':primitives,'composition':[],'entity_ids':{v:k for k,v in context['entity_bindings'].items()}}
    def execute(p,actor):
        nonlocal bundle,runtime_calls
        if p['lowering_status']!='READY' or p['confidence']=='LOW':return
        try:
            for primitive in p['primitive_sequence']:
                if stabilized:
                    primitive['provenance']['boundary_semantics']='AUTHORED_ENVELOPE/1.0'
                    if primitive['primitive_type']=='ORIENT_TO' and not p['provenance'].get('allow_runtime_clamp'):primitive['parameters']['angular_timing_profile']='EASE_IN_OUT_ROTATION'
                primitive['provenance']['parameter_sources']={k:{'value':copy.deepcopy(v),'source':'DERIVED','derived_from':copy.deepcopy(p['resolved_inputs']),'method':'FIXED_REGISTRY_PARAMETER_TRANSLATION','confidence':p['confidence']} for k,v in primitive['parameters'].items()}
            prospective=copy.deepcopy(program);prospective['primitives']=primitives+p['primitive_sequence'];prospective['composition']=composition(prospective['primitives'])
            available={a['primitive_id'] for a in prospective['primitives']}|{a['actor'] for a in prospective['primitives'] if any(ch in channels(a)['WRITES'] for ch in ('ROOT_LOCATION','PROJECTILE_TRANSFORM'))}
            missing=sorted({ref for a in p['primitive_sequence'] for ref in channels(a)['READS'] if ref not in available})
            if missing:raise StopLowering('NEEDS_AUTHOR_INPUT','MISSING_EVALUATED_READ_TRACK',missing)
            runtime_calls+=1;compiled,diag=compile_program(prospective);ids={a['primitive_id'] for a in p['primitive_sequence']};fs=[f for f in compiled['fragments'] if f['primitive_id'] in ids]
            if any(f['continuity_report']['dimensions'][dim]!='PASS' for f in fs for dim in ('C0','C1')):raise StopLowering('BLOCKED_BY_CONSTRAINT','LOWERING_VALIDATION_FAIL',['C0/C1 contract'])
            for f in fs:
                for key,value in f['metadata'].get('derived_parameters',{}).items():record(p,'runtime.'+f['primitive_id']+'.'+key,value.get('value',value) if isinstance(value,dict) else value,'DERIVED',{'primitive_id':f['primitive_id'],'resolved_inputs':copy.deepcopy(p['resolved_inputs'])},'S51_RUNTIME_PROFILE_SOLVE','MEDIUM')
            post_constraints(p,fs,context);p['validation_status']='PASS';p['provenance']['runtime_diagnostics']={k:v for k,v in diag.items() if k in ids};p['provenance']['actual_exit']=copy.deepcopy(fs[-1]['exit_state_actual'])
            primitives.extend(p['primitive_sequence']);program['composition']=prospective['composition'];bundle=compiled
            if actor:chain.commit(p['event_id'],actor,fs)
        except StopLowering as stop:requests.append(request(p,stop))
        except (ValueError,KeyError,TypeError,ValidationError) as exc:requests.append(request(p,StopLowering('NEEDS_AUTHOR_INPUT' if stabilized and 'INFEASIBLE_DURATION' in str(exc) else 'BLOCKED_BY_CONSTRAINT','INFEASIBLE_DURATION' if stabilized and 'INFEASIBLE_DURATION' in str(exc) else 'LOWERING_VALIDATION_FAIL',[str(exc)])))
    for e in ([next(e for e in graph['events'] if e['event_id']==k) for k in evaluation['order']] if stabilized else ordered_events(graph)):
        p,r=event_plan(graph,e,context,chain)
        if stabilized:
            p['provenance']['execution_graph_sha256']=sha(graph)
            p['provenance']['graph_sha256']=sha(original_graph)
            p['provenance']['time_alignment']=[x for x in alignment if x['source'].startswith(e['event_id']+'.')]
            for item in p['provenance']['time_alignment']:
                key=item['source'].split('.')[-1]+'_time'
                if key in p['resolved_inputs']:
                    record(p,key,item['execution_time'],'DERIVED',item,'EXPLICIT_TIME_ALIGNMENT',p['confidence'])
            for primitive in p['primitive_sequence']:
                primitive['provenance']['graph_sha256']=sha(original_graph)
                primitive['provenance']['time_alignment']=p['provenance']['time_alignment']

        prerequisites=[d['depends_on'] for d in graph['dependencies'] if d['event_id']==e['event_id']]+([e['source_event']] if e['source_event'] else [])
        if stabilized:prerequisites=evaluation['dependencies'][e['event_id']]
        failed=[q['event_id'] for q in plans if q['event_id'] in prerequisites and q['validation_status']!='PASS']
        if failed:r=request(p,StopLowering('BLOCKED_BY_UPSTREAM' if stabilized else 'NEEDS_AUTHOR_INPUT','BLOCKED_BY_UPSTREAM' if stabilized else 'UNRESOLVED_DEPENDENCY',failed))
        plans.append(p)
        if r:requests.append(r)
        else:execute(p,p['provenance'].get('affected_entity'))
    if context.get('lower_cameras',False):
        from camera_intent_lowering import camera_plan
        previous=None
        for shot in graph['shot_intents']:
            p,r=camera_plan(graph,shot,context,previous,bundle)
            if stabilized:
                needed=[x['producer'] for x in evaluation['camera_edges'] if x['consumer']==shot['shot_id']]
                failed=[x['event_id'] for x in plans if x['event_id'] in needed and x['validation_status']!='PASS']
                if failed:r=request(p,StopLowering('BLOCKED_BY_UPSTREAM','BLOCKED_BY_UPSTREAM',failed))
            plans.append(p)
            if r:requests.append(r)
            else:
                execute(p,None)
                if p['validation_status']=='PASS':previous=p
    ready=bool(plans) and all(p['lowering_status']=='READY' and p['validation_status']=='PASS' and p['confidence'] in ('HIGH','MEDIUM') for p in plans)
    result={'lowering_version':'EVENT-LOWERING-PLAN/1.0','graph_id':graph['graph_id'],'graph_sha256':sha(graph),'context_sha256':sha(context),'plans':plans,'ready_for_execution':ready,'state_chain':chain.links,'runtime_invocations':runtime_calls,'builder_allowed':ready,'automatic_execution_of_unresolved':False}
    if stabilized:
        result['graph_sha256']=sha(original_graph)
        result['execution_graph_sha256']=sha(graph)
        result['time_alignment']=alignment
        result['evaluation_schedule']=evaluation
        for p in plans:p['provenance']['author_graph_sha256']=sha(original_graph)
    validate_protocol(result,'event-lowering-plan.schema.json')
    for item in requests:validate_protocol(item,'author-input-request.schema.json')
    return result,program if ready else None,bundle if ready else None,requests

if __name__=='__main__':
    import argparse
    from pathlib import Path
    ap=argparse.ArgumentParser(description='Safe S52 lowering; never invokes Blender')
    ap.add_argument('--graph',required=True);ap.add_argument('--context',required=True);ap.add_argument('--output',required=True)
    a=ap.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    g=json.loads(Path(a.graph).read_text(encoding='utf8'));c=json.loads(Path(a.context).read_text(encoding='utf8'))
    report,program,bundle,requests=lower_graph(g,c)
    for name,value in [('LOWERING-PLAN.json',report),('AUTHOR-INPUT-REQUEST.json',requests)]+([('PRIMITIVES.json',program),('EXECUTION-FRAGMENT.json',bundle)] if report['builder_allowed'] else []):
        (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')
