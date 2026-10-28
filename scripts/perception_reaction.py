"""Opt-in causal compilation. No bpy, new motion math, implicit cognition or clock."""
import copy,math
from primitive_sampler import sha,norm,sub,dot,unit
from timebase import frame_to_time,time_to_frame

MODES={'EXPLICIT_AUTHOR_TRIGGER','SPATIAL_VISUAL_TRIGGER'}
def validate_binding(b):
    if b.get('schema_version')!='PERCEPTION-REACTION/1.0':raise ValueError('BINDING_VERSION')
    for k in ('binding_id','actor','target','source_event','perception_event','fps','window','trigger','reaction_delay_frames','response_steps','provenance'):
        if k not in b:raise ValueError('MISSING_'+k)
    if b['actor']==b['target']:raise ValueError('SELF_PERCEPTION_TARGET')
    frame_to_time(b['window'][0],b['fps'])
    if b['window'][0]>b['window'][1]:raise ValueError('INVALID_WINDOW')
    if b['trigger']['mode'] not in MODES:raise ValueError('UNSUPPORTED_TRIGGER')
    if b['trigger']['mode']=='EXPLICIT_AUTHOR_TRIGGER' and (not b['trigger'].get('author_reason') or not isinstance(b['trigger'].get('frame'),int)):raise ValueError('EXPLICIT_AUTHORITY_REQUIRED')
    if b['trigger']['mode']=='EXPLICIT_AUTHOR_TRIGGER' and b['trigger']['frame']<=b['source_event']['frame']:raise ValueError('EXPLICIT_CUE_MUST_FOLLOW_SOURCE')
    if not isinstance(b['reaction_delay_frames'],int) or b['reaction_delay_frames']<0:raise ValueError('INVALID_DELAY')
    if b['reaction_delay_frames']==0 and not b.get('immediate_reaction_authorized'):raise ValueError('UNAUTHORIZED_IMMEDIATE_REACTION')
    ids=[b['source_event']['event_id'],b['perception_event']]+[s['event_id'] for s in b['response_steps']]
    if len(ids)!=len(set(ids)) or not b['response_steps']:raise ValueError('EVENT_ID_CONFLICT')
    for s in b['response_steps']:
        if s['duration_frames']<1 or not isinstance(s['duration_frames'],int):raise ValueError('INVALID_RESPONSE_DURATION')
    if b.get('locked_channels'):raise ValueError('BLOCKED_BY_OVERRIDE')
    if b['trigger']['mode']=='SPATIAL_VISUAL_TRIGGER':
        q=b['trigger']
        for k in ('max_distance','half_cone_deg'):
            if not isinstance(q.get(k),(int,float)) or isinstance(q[k],bool) or not math.isfinite(q[k]):raise ValueError('INVALID_TRIGGER_LIMIT')
        if q['max_distance']<=0 or not 0<q['half_cone_deg']<=180:raise ValueError('INVALID_TRIGGER_LIMIT')

def condition(b,row):
    q=b['trigger'];mode=q['mode']
    if row.get('actor')!=b['actor'] or row.get('target')!=b['target']:return None,{'reason':'ENTITY_BINDING_MISMATCH'}
    if not row.get('actor_exists') or not row.get('target_exists'):return None,{'reason':'ENTITY_MISSING'}
    if mode=='EXPLICIT_AUTHOR_TRIGGER':return row['frame']>=q['frame'],{'basis':'AUTHOR_CUE_NOT_VISUAL_DETECTION','author_reason':q['author_reason']}
    if q.get('require_line_of_sight') or q.get('unoccluded_context') is not True:return None,{'reason':'ACTOR_LOS_UNAVAILABLE'}
    try:
        vectors=[row[k] for k in ('actor_position','target_position','actor_forward')]
        if any(len(v)!=3 or any(not math.isfinite(x) for x in v) for v in vectors):raise ValueError()
        delta=sub(row['target_position'],row['actor_position']);distance=norm(delta)
        if norm(row['actor_forward'])<1e-9:raise ValueError()
        angle=math.degrees(math.acos(max(-1,min(1,dot(unit(delta),unit(row['actor_forward'])))))) if distance>1e-9 else 0.
        speed=row.get('target_speed')
        if q.get('min_target_speed') is not None and (speed is None or not math.isfinite(speed)):return None,{'reason':'TARGET_MOTION_UNAVAILABLE'}
        ok=distance<=q['max_distance']+1e-8 and angle<=q['half_cone_deg']+1e-8 and (q.get('min_target_speed') is None or speed>=q['min_target_speed'])
        return ok,{'basis':'WORLD_PROXY_DISTANCE_FACING; UNOCCLUDED_CONTEXT_AUTHOR_ASSUMPTION','distance':distance,'facing_angle_deg':angle,'target_speed':speed}
    except (KeyError,ValueError,TypeError):return None,{'reason':'SPATIAL_MEASUREMENT_UNAVAILABLE'}

def resolve(b,rows):
    validate_binding(b)
    root={'schema_version':'PERCEPTION-RESOLUTION/1.0','binding_id':b['binding_id'],'binding_sha256':sha(b),'input_evidence_sha256':sha(rows),'evidence_state':'PLANNED','actor':b['actor'],'target':b['target'],'perception_event':b['perception_event'],'source_event':b['source_event'],'response_events':[]}
    source=b['source_event']['frame'];lo=max(b['window'][0],source+1);hi=b['window'][1]
    index={r['frame']:r for r in rows}
    if len(index)!=len(rows):raise ValueError('DUPLICATE_EVIDENCE_FRAME')
    unknown=[];history=[];chosen=None
    for f in range(lo,hi+1):
        if f not in index:unknown.append(f);continue
        valid,measurement=condition(b,index[f]);history.append({'frame':f,'condition':valid,'measurement':measurement})
        if valid is None:unknown.append(f)
        if valid:
            if unknown:return dict(root,status='NOT_REVIEWED',code='INCOMPLETE_FIRST_TRIGGER_EVIDENCE',missing_frames=unknown)
            chosen=f;break
    if chosen is None:return dict(root,status='NOT_REVIEWED' if unknown else 'UNTRIGGERED',code='INSUFFICIENT_EVIDENCE' if unknown else 'CONDITION_NEVER_MET',condition_samples=history)
    delay=b['reaction_delay_frames'];start=chosen+delay;events=[];previous=b['perception_event']
    for step in b['response_steps']:
        end=start+step['duration_frames']
        if end>b.get('execution_end_frame',10**12):return dict(root,status='BLOCKED',code='RESPONSE_OUTSIDE_EXECUTION_WINDOW')
        events.append({'event_id':step['event_id'],'kind':step['kind'],'actor':b['actor'],'perception_ref':b['perception_event'],'depends_on':previous,'start_frame':start,'end_frame':end,'start_time':frame_to_time(start,b['fps']),'end_time':frame_to_time(end,b['fps'])})
        previous=step['event_id'];start=end
    return dict(root,status='READY',perception_frame=chosen,perception_time=frame_to_time(chosen,b['fps']),reaction_start_frame=chosen,reaction_start_time=frame_to_time(chosen,b['fps']),response_events=events,condition_samples=history,condition_evidence=history[-1],attention_states=[{'state':'UNAWARE','frame':source},{'state':'POTENTIALLY_AWARE','frame':chosen},{'state':'PERCEIVED','frame':chosen},{'state':'REACTING','frame':chosen},{'state':'RESPONDED','frame':events[0]['start_frame']}])

def verify(b,planned,native_rows,observed_responses):
    """Recompute the condition from native samples and verify measured response onset.
    Metadata event windows are never accepted as observed movement.
    """
    errors=[]
    try:actual=resolve(b,native_rows)
    except ValueError as e:return {'status':'FAIL','errors':[str(e)],'evidence_state':'OBSERVED'}
    if planned.get('binding_sha256')!=sha(b):errors.append('STALE_BINDING')
    if any(planned.get(k)!=actual.get(k) for k in ('actor','target','source_event','perception_event')):errors.append('IDENTITY_OR_SOURCE_MISMATCH')
    if planned.get('status')!='READY' or actual.get('status')!='READY':
        return {'status':'NOT_REVIEWED' if actual.get('status')=='NOT_REVIEWED' else 'FAIL','errors':errors+['PERCEPTION_NOT_EVIDENCED'],'actual_resolution':actual,'evidence_state':'OBSERVED'}
    if planned['perception_frame']!=actual['perception_frame']:errors.append('NATIVE_TRIGGER_MISMATCH')
    source=b['source_event']['frame'];p=planned['perception_frame'];r=planned['reaction_start_frame'];first=planned['response_events'][0]['start_frame']
    if not(source<p<=r and (r<first or b.get('immediate_reaction_authorized') and r==first)):errors.append('CAUSAL_TIME_ORDER')
    if first-p!=b['reaction_delay_frames']:errors.append('REACTION_DELAY_MISMATCH')
    if planned['response_events']!=actual['response_events']:errors.append('RESOLVED_DEPENDENCY_MISMATCH')
    obs={o['event_id']:o for o in observed_responses}
    for e in actual['response_events']:
        o=obs.get(e['event_id'])
        if not o or o.get('basis')!='NATIVE_MEASURED_CHANGE':errors.append('RESPONSE_EVIDENCE_MISSING:'+e['event_id']);continue
        if o.get('perception_ref')!=b['perception_event'] or o.get('depends_on')!=e['depends_on']:errors.append('WRONG_PERCEPTION_DEPENDENCY:'+e['event_id'])
        onset=o.get('onset_frame')
        if onset is None or onset<e['start_frame'] or onset>min(e['end_frame'],e['start_frame']+b.get('measurement_onset_allowance_frames',6)):errors.append('RESPONSE_ONSET_MISMATCH:'+e['event_id'])
    return {'status':'FAIL' if errors else 'PASS','errors':errors,'evidence_state':'OBSERVED' if errors else 'VERIFIED','actual_resolution':actual,'native_evidence_sha256':sha(native_rows),'observed_responses':observed_responses,'limit':'Authored recognition model; no human cognition or actor LOS claim'}

def verify_response_stationarity(samples,first_response_frame,chase_frame,grounded=False):
    """Observe no early response. Grounded proxies rotate around a corrected root.

    Root translation before the first response must remain fixed. During an
    authorized turn, use measured root XY + mesh-bottom Z for grounded actors;
    report raw root drift separately. This is not a support/physics validator.
    """
    tolerance=1e-5
    if not samples or [r['frame'] for r in samples[:chase_frame]]!=list(range(1,chase_frame+1)):
        return {'status':'NOT_REVIEWED','reason':'MISSING_STATIONARITY_SAMPLES'}
    if grounded and any(r.get('basis')!='NATIVE_ROOT_XY_AND_EVALUATED_MESH_BOTTOM_Z' or 'ground_anchor' not in r for r in samples[:chase_frame]):
        return {'status':'NOT_REVIEWED','reason':'GROUNDED_ANCHOR_NOT_OBSERVED'}
    anchor='ground_anchor' if grounded else 'root_position'
    early=max(norm(sub(r['root_position'],samples[0]['root_position'])) for r in samples[:first_response_frame])
    chase=max(norm(sub(r[anchor],samples[0][anchor])) for r in samples[:chase_frame])
    raw=max(norm(sub(r['root_position'],samples[0]['root_position'])) for r in samples[:chase_frame])
    return {'status':'PASS' if max(early,chase)<=tolerance else 'FAIL','pre_response_root_drift':early,'pre_chase_anchor_drift':chase,'raw_root_drift':raw,'basis':anchor,'tolerance':tolerance,'tolerance_source':'existing native position measurement precision; unchanged','limit':'Grounded proxy geometry anchor; no support/contact quality claim'}


def attach_csp(csp,b,resolution):
    """Project onto existing action_beats/causal_links; Builder receives ordinary CSP."""
    if resolution.get('status')!='READY' or resolution['binding_sha256']!=sha(b):raise ValueError('UNRESOLVED_OR_STALE_PERCEPTION')
    from combat_sequence_package import PHASES,validate
    out=copy.deepcopy(csp);fps=b['fps'];src=b['source_event'];pid=b['perception_event']
    items=[(src['event_id'],src['frame'],src['frame']+1,'WORLD_SOURCE'),(pid,resolution['perception_frame'],resolution['perception_frame']+1,'PERCEPTION_METADATA')]+[(e['event_id'],e['start_frame'],e['end_frame'],e['kind']) for e in resolution['response_events']]
    existing={x['event_id'] for x in out['action_beats']}
    for eid,a,z,kind in items:
        if eid in existing:raise ValueError('CAUSAL_EVENT_ID_COLLISION')
        out['action_beats'].append({'event_id':eid,'type':kind,'interval_s':[frame_to_time(a,fps),frame_to_time(z,fps)],'phases':{p:{'status':'NA','reason':'Causal timing metadata; no combat phase claimed'} for p in PHASES},'breakdowns':[{'time_s':frame_to_time(a,fps),'role':'CAUSAL_BINDING','actor':b['actor']} ]})
    out['causal_links'].append({'cause_event':src['event_id'],'reaction_event':pid,'trigger_s':frame_to_time(src['frame'],fps),'response_s':resolution['perception_time'],'direction_rule':'spatial/explicit authored perception predicate','strength_rule':'no force claim','perception_binding_sha256':sha(b)})
    previous=pid;trigger=resolution['perception_time']
    for e in resolution['response_events']:
        out['causal_links'].append({'cause_event':previous,'reaction_event':e['event_id'],'trigger_s':trigger,'response_s':e['start_time'],'direction_rule':'DEPENDENT_RESPONSE','strength_rule':'no force claim','perception_event':pid,'perception_binding_sha256':sha(b)});previous=e['event_id'];trigger=e['end_time']
    errors=validate(out)
    if errors:raise ValueError('INVALID_CAUSAL_CSP '+str(errors))
    return out

def narrative_location(action,frame,state):
    """Opt-in dense S51 sample adapter; no replacement interpolation or motion model."""
    binding=action.get('causal_execution')
    if binding is None:return state
    if binding.get('schema_version')!='CAUSAL-LOCATION/1.0' or binding.get('samples_sha256')!=sha(binding['samples']):raise ValueError('INVALID_CAUSAL_LOCATION')
    rows=binding['samples'];i=frame-action['start']
    if i<0 or i>=len(rows) or rows[i]['frame']!=frame:raise ValueError('CAUSAL_SAMPLE_FRAME_MISMATCH')
    out=dict(state);out['position']=list(rows[i]['position']);return out
