"""Shot semantic quantities -> fixed Camera rules; no camera curves or candidate search."""
import copy
from primitive_sampler import norm,sub,add,sample_track,frame_to_time
from timebase import duration_frames
from shot_camera_lowering_registry import REGISTRY,AUTHOR_FIELDS,FIELDS_BY_BEHAVIOR
from lowering_validator import *

def camera_plan(graph,shot,context,previous=None,execution_bundle=None):
    from event_lowering import new_primitive,read_value,binding
    p=plan(graph,shot['shot_id'],'CAMERA_INTENT',shot['camera_behavior_intent'])
    try:
        v,confidence=parse_evidence(shot['camera_behavior_intent']);p['confidence']=confidence
        if set(v)-AUTHOR_FIELDS:raise StopLowering('NEEDS_AUTHOR_INPUT','UNRECOGNIZED_CAMERA_FIELDS',sorted(set(v)-AUTHOR_FIELDS))
        mode=read_value(p,v,'behavior',required=True)
        if mode not in REGISTRY:raise StopLowering('AMBIGUOUS','CAMERA_BEHAVIOR_NOT_EXPLICIT',['Dolly or Lens / explicit behavior'])
        if set(v)-FIELDS_BY_BEHAVIOR[mode]:raise StopLowering('NEEDS_AUTHOR_INPUT','CAMERA_FIELD_NOT_APPLICABLE',sorted(set(v)-FIELDS_BY_BEHAVIOR[mode]))
        p['event_type']='CAMERA_'+mode;p['constraints']=constraints_for(graph,shot['shot_id'],None,shot['time_range'],shot['shot_id']);v=constraint_inputs(p['constraints'],v,p)
        start=v.get('start',shot['time_range'][0]);end=v.get('end',shot['time_range'][1])
        if not shot['time_range'][0]<=start<end<=shot['time_range'][1]:raise StopLowering('BLOCKED_BY_CONSTRAINT','CAMERA_INTERVAL_OUTSIDE_SHOT')
        last=frame_to_time(duration_frames(graph['timebase']['duration'],graph['timebase']['fps']),graph['timebase']['fps']);end=min(end,last)
        if end<=start:need(p,'camera_sampling_interval')
        event={'event_id':shot['shot_id'],'event_type':'CAMERA_'+mode,'start':start,'end':end}
        declared_end=v.get('end',shot['time_range'][1])
        record(p,'start_time',start,'AUTHOR_EXPLICIT',shot['shot_id']+('.camera_behavior_intent.start' if 'start' in v else '.time_range'))
        record(p,'end_time',end,'DERIVED' if end!=declared_end else 'AUTHOR_EXPLICIT',shot['shot_id']+('.camera_behavior_intent.end' if 'end' in v else '.time_range'),'END_EXCLUSIVE_TO_LAST_AVAILABLE_SAMPLE' if end!=declared_end else 'DIRECT_VALUE')
        st=copy.deepcopy(previous['provenance']['actual_exit'] if previous else context.get('camera_state'))
        if not st:need(p,'approved_camera_entry_state')
        st['camera_velocity']=st['velocity'];p['entry_state']=copy.deepcopy(st)
        for k,val in st.items():record(p,'entry.'+k,val,'PREVIOUS_EXIT_STATE' if previous else 'ENTITY_STATE',previous['event_id']+'.exit_state' if previous else 'execution_context.camera_state','CONTINUITY_INHERITANCE' if previous else 'APPROVED_ENTRY_STATE')
        subject=read_value(p,v,'subject',shot['subjects'][0] if len(shot['subjects'])==1 else None)
        if subject is None:need(p,'subject')
        record(p,'subject',subject,'AUTHOR_EXPLICIT',shot['shot_id']+'.subjects');target=binding(context,subject)
        offset=[0,0,read_value(p,v,'height_offset',0)];q={'target':target,'target_offset':offset}
        target_world=None
        candidates=[f for f in (execution_bundle or {}).get('fragments',[]) if f['affected_entity']==target and any(ch in f['channel_ownership']['WRITES'] for ch in ('ROOT_LOCATION','PROJECTILE_TRANSFORM'))]
        if candidates:
            f=max(candidates,key=lambda f:min(f['time_range'][0],start));target_world=add(sample_track(f['world_samples'],start),offset)
        else:
            ent=next(e for e in graph['entities'] if e['id']==subject);facts,_=parse_evidence(ent['persistent_state'])
            if 'position' in facts and facts.get('at_time')==start:target_world=add(facts['position'],offset)
        if mode=='HOLD':
            profile=read_value(p,v,'profile',required=True)
            if profile not in ('LOCKED_HOLD','COMPOSITION_HOLD','SOFT_HOLD'):need(p,'explicit_hold_profile')
            q['behavior_profile']=profile
            if 'tracking_strength' in v:q['follow_strength']=read_value(p,v,'tracking_strength')
        elif mode=='REFRAME':q.update(target_screen_region=read_value(p,v,'target_screen_region',required=True),max_rotation=read_value(p,v,'max_rotation_degrees',required=True),max_translation=read_value(p,v,'max_translation',required=True))
        elif mode=='FOLLOW':
            q.update(screen_anchor=read_value(p,v,'screen_anchor',required=True),follow_strength=read_value(p,v,'tracking_strength',required=True),lag=read_value(p,v,'lag_seconds',required=True))
            distance=read_value(p,v,'distance')
            if distance is None:
                if target_world is None:need(p,'camera_subject_entry_relation')
                distance=record(p,'distance',norm(sub(st['position'],target_world)),'DERIVED','camera entry + subject evaluated entry','DERIVED_FROM_ENTRY_STATE')
            q['distance']=distance
        elif mode=='LEAD_LAG':q.update(lead_distance=read_value(p,v,'lead_distance',required=True),lag_time=read_value(p,v,'lag_seconds',required=True),screen_bias=read_value(p,v,'screen_bias',required=True),transition_duration=read_value(p,v,'transition_seconds',required=True))
        elif mode=='PUSH_PULL':
            direction=read_value(p,v,'direction',required=True)
            if direction not in ('PUSH','PULL'):raise StopLowering('AMBIGUOUS','DOLLY_OR_LENS_UNRESOLVED',['direction'])
            if 'travel_distance' not in v:raise StopLowering('AMBIGUOUS','COMPOSITION_GOAL_DOES_NOT_SELECT_DOLLY_OR_LENS',['travel_distance'])
            if v.get('lens_change'):raise StopLowering('UNSUPPORTED','LENS_LOWERING_NOT_IN_SAFE_SUBSET')
            q.update(mode=direction,distance_delta=read_value(p,v,'travel_distance'),profile='EASE_IN_OUT',lens_policy='FIXED')
        elif mode=='CATCH_UP':q.update(entry_lag=read_value(p,v,'entry_lag_seconds',required=True),follow_strength=read_value(p,v,'tracking_strength',required=True),catchup_start=read_value(p,v,'catchup_fraction',required=True),settle_start=read_value(p,v,'settle_fraction',required=True))
        relation=previous['provenance'].get('tracking_offset') if previous else None
        if relation is None and target_world is not None:relation=sub(st['position'],target_world)
        if relation is not None:
            p['provenance']['tracking_offset']=relation
            if mode in ('CATCH_UP','LEAD_LAG'):q['tracking_offset']=record(p,'tracking_offset',relation,'PREVIOUS_EXIT_STATE' if previous else 'DERIVED','previous camera relation' if previous else 'entry transform / subject','PRESERVE_DECLARED_CAMERA_RELATION')
        # Explicit screen anchor + fixed orientation may be requested by the execution
        # context to preserve an approved camera orientation; never choose an artistic aim.
        if context.get('camera_rotation_policy')=='PRESERVE_APPROVED_ORIENTATION':q['track_rotation']=False
        if previous:q['entry_from']=previous['primitive_sequence'][-1]['primitive_id']
        pr=new_primitive(p,REGISTRY[mode],context.get('camera_actor','CAM'),event,st,q);p['primitive_sequence']=[pr]
        check_locks(graph,p,[pr],shot['shot_id'],[start,end],context.get('overrides'))
        if any(x['source']=='TECHNICAL_DEFAULT' for x in p['resolved_inputs'].values()) and p['confidence']=='HIGH':p['confidence']='MEDIUM'
        if confidence=='LOW':raise StopLowering('NEEDS_AUTHOR_INPUT','LOW_CONFIDENCE_CAMERA_INTENT',['confirmed camera behavior'])
        p['lowering_status']='READY';return p,None
    except StopLowering as stop:return p,request(p,stop)
