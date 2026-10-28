"""Causal response windows -> existing S51 primitives. No trajectory implementation."""
import copy
from perception_reaction import resolve
from primitive_runtime import compile_program,compile_primitive
from primitive_sampler import sample_track,frame_to_time
from event_lowering import composition

def evaluated_tracks(program,bundle):
    tracks=copy.deepcopy(program.get('read_tracks',{}))
    for f in bundle['fragments']:
        tracks[f['primitive_id']]=f['world_samples']
        if 'ROOT_LOCATION' not in f['channel_ownership']['WRITES'] and 'PROJECTILE_TRANSFORM' not in f['channel_ownership']['WRITES']:continue
        key=f['affected_entity'];old={r['frame']:r for r in tracks.get(key,[]) if 'frame' in r};old.update({r['frame']:r for r in f['world_samples']});tracks[key]=[old[k] for k in sorted(old)]
    return tracks

def native_position_track(matrix_rows,object_name,fps):
    """Import evaluated target positions; includes proxy grounding / support transforms.

    Input is the saved-scene matrix capture, not authored root coordinates. Caller
    retains source-file hashes. No target orientation or cognition is inferred.
    """
    from primitive_sampler import derivative
    rows=[]
    for r in matrix_rows:
        m=r['values'][object_name]
        if len(m)!=16:raise ValueError('INVALID_NATIVE_MATRIX')
        rows.append({'frame':r['frame'],'time':frame_to_time(r['frame'],fps),'position':[m[3],m[7],m[11]]})
    if len(rows)<2 or any(b['frame']!=a['frame']+1 for a,b in zip(rows,rows[1:])):raise ValueError('NATIVE_TARGET_SAMPLE_GAP')
    for i,r in enumerate(rows):r['velocity']=derivative(rows,i)
    return rows


def evidence_from_tracks(binding,tracks,timebase):
    from primitive_sampler import rotate,norm
    from timebase import duration_frames
    rows=[]
    for frame in range(1,duration_frames(timebase['duration'],timebase['fps'])+1):
        t=frame_to_time(frame,timebase['fps']);a=tracks.get(binding['actor']);b=tracks.get(binding['target'])
        r={'frame':frame,'actor':binding['actor'],'target':binding['target'],'actor_exists':bool(a),'target_exists':bool(b)}
        if a and b:r.update(actor_position=sample_track(a,t),target_position=sample_track(b,t),actor_forward=rotate(sample_track(a,t,'orientation'),[0,1,0]),target_speed=norm(sample_track(b,t,'velocity')))
        rows.append(r)
    return rows

def inherited_response_state(previous,fragment,reads,end_time):
    """Only writers own state updates; orientation samples do not own translation."""
    result=copy.deepcopy(previous);actual=fragment['exit_state_actual'];writes=fragment['channel_ownership']['WRITES']
    if any(c in writes for c in ('ROOT_LOCATION','PROJECTILE_TRANSFORM','WEAPON_TRANSFORM')):
        for k in ('position','velocity','movement_direction'):result[k]=copy.deepcopy(actual[k])
    elif fragment['affected_entity'] in reads:
        for k in ('position','velocity'):result[k]=sample_track(reads[fragment['affected_entity']],end_time,k)
    if any(c in writes for c in ('ROOT_ROTATION','PROJECTILE_TRANSFORM','WEAPON_TRANSFORM')):
        for k in ('orientation','angular_velocity'):result[k]=copy.deepcopy(actual[k])
    if 'ATTACHMENT_STATE' in writes:result['ownership_state']=actual['ownership_state']
    return result


def lower(binding,base_program,evidence_rows,templates,actor_state,truncate_primitive=None):
    resolution=resolve(binding,evidence_rows)
    if resolution['status']!='READY':return {'status':resolution['status'],'resolution':resolution,'program':None,'bundle':None}
    if set(templates)!={e['event_id'] for e in resolution['response_events']}:raise ValueError('RESPONSE_TEMPLATE_REFERENCES')
    p=copy.deepcopy(base_program);tb=p['timebase'];base_bundle,_=compile_program(p)
    reads=evaluated_tracks(p,base_bundle)
    actor=binding['actor'];state=copy.deepcopy(actor_state)
    first=resolution['response_events'][0]['start_time']
    if actor in reads:
        for k in ('position','velocity','orientation'):state[k]=sample_track(reads[actor],first,k)
    if truncate_primitive:
        prior=next(x for x in p['primitives'] if x['primitive_id']==truncate_primitive)
        if prior['primitive_type']!='MOVE_PROFILE' or prior['parameters'].get('timing_profile')!='CONSTANT':raise ValueError('TRUNCATION_REQUIRES_CONSTANT_PRE_RESPONSE_MOTION')
        prior['end_time']=first;prior['parameters']['end_position']=list(state['position']);prior['parameters']['exit_velocity']=list(state['velocity'])
    for e in resolution['response_events']:
        primitive=copy.deepcopy(templates[e['event_id']]);primitive.update(start_time=e['start_time'],end_time=e['end_time'],entry_state=copy.deepcopy(state))
        primitive.setdefault('provenance',{}).update(perception_ref=binding['perception_event'],response_event=e['event_id'],binding_sha256=resolution['binding_sha256'],boundary_semantics='AUTHORED_ENVELOPE/1.0')
        if primitive['actor']!=actor:raise ValueError('RESPONSE_ACTOR_MISMATCH')
        q=primitive['parameters']
        if primitive['primitive_type'] in ('MOVE_PROFILE','RECOVERY_PROFILE'):q['entry_velocity']=list(state['velocity'])
        if primitive['primitive_type']=='RECOVERY_PROFILE':q['duration']=e['end_time']-e['start_time']
        frag,_=compile_primitive(primitive,tb,reads)
        if any(frag['continuity_report']['dimensions'][d]!='PASS' for d in ('C0','C1')):raise ValueError('RESPONSE_BOUNDARY_FAILED '+e['event_id'])
        state=inherited_response_state(state,frag,reads,e['end_time']);p['primitives'].append(primitive)
        if 'ROOT_LOCATION' in frag['channel_ownership']['WRITES']:
            reads[actor]=frag['world_samples']
    p['composition']=composition(p['primitives'])
    bundle,diag=compile_program(p)
    if any(any(f['continuity_report']['dimensions'][d]!='PASS' for d in ('C0','C1')) for f in bundle['fragments']):raise ValueError('PROGRAM_BOUNDARY_FAILED')
    return {'status':'READY','resolution':resolution,'program':p,'bundle':bundle,'diagnostics':diag}
