"""Explicit channel merge into ordinary CSP/1.0. Fresh technical packages only.

Existing registered LOCKED work must use S2, not this fresh-fixture adapter.
"""
import copy
import math
from primitive_sampler import *
from combat_sequence_package import validate

def euler(q):
    w,x,y,z=q
    return [math.atan2(2*(w*x+y*z),1-2*(x*x+y*y)),math.asin(max(-1,min(1,2*(w*y-z*x)))),math.atan2(2*(w*z+x*y),1-2*(y*y+z*z))]

def merge_fragments(csp,bundle,registry=None):
    if registry and any(o['status']=='LOCKED' for o in registry.get('overrides',[])):raise ValueError('LOCKED_CONTENT_REQUIRES_S2')
    if not csp.get('primitive_fixture_fresh'):raise ValueError('EXISTING_EXECUTION_REQUIRES_S2')
    result=copy.deepcopy(csp);n=csp['timebase']['frames'];fps=csp['timebase']['fps'];frags=bundle['fragments']
    for f in frags:
        import json,jsonschema
        from pathlib import Path
        jsonschema.validate(f,json.loads((Path(__file__).resolve().parents[1]/'authoring'/'primitive-execution-fragment.schema.json').read_text()))
        if f.get('execution_sha256')!=sha({k:f[k] for k in ('world_samples','ownership_samples','channel_ownership','entry_state_actual','exit_state_actual','continuity_report')}):raise ValueError('FRAGMENT_EXECUTION_HASH_MISMATCH')
        pose=[{'frame':r['frame'],'channel':ch,'orientation':r['orientation']} for ch in f['channel_ownership']['WRITES'] if ch in ('BODY_ROTATION','HEAD_ROTATION') for r in f['world_samples']]
        if f['pose_samples']!=pose:raise ValueError('POSE_SAMPLE_MISMATCH')
        if f['continuity_report']['dimensions']['C0']!='PASS' or f['continuity_report']['dimensions']['C1']!='PASS':raise ValueError('FRAGMENT_CONTINUITY_CONTRACT_FAILED')
        if f['timebase']['fps']!=fps:raise ValueError('FRAGMENT_TIMEBASE_MISMATCH')
        if f['world_samples'][-1]['frame']>n:raise ValueError('FRAGMENT_OUTSIDE_CSP')
    # Declare owners on each affected channel/frame before applying. Additive offsets
    # carry only the offset relative to the named base, never replace another path.
    writes={};additive={}
    for op in bundle.get('composition',[]):
        if op['type']=='EXPLICIT_ADDITIVE_OFFSET':
            fs=[next(f for f in frags if f['primitive_id']==i) for i in op['members']]
            offset=next(f for f in fs if f['metadata']['primitive_type']=='OFFSET_PATH');additive[offset['primitive_id']]=True
    for f in frags:
        for row in f['world_samples']:
            for ch in f['channel_ownership']['WRITES']:
                key=(f['affected_entity'],ch,row['frame']);existing=writes.get(key)
                if existing and f['primitive_id'] not in additive and existing not in additive:
                    op=next((o for o in bundle.get('composition',[]) if o['type']=='SEQUENTIAL' and set(o['members'])=={existing,f['primitive_id']}),None)
                    if not op:raise ValueError('MERGE_CHANNEL_CONFLICT')
                writes[key]=f['primitive_id']
    byactor={a['id'] for a in result.get('actors',[])}
    for f in sorted(frags,key=lambda f:bool(additive.get(f['primitive_id']))):
        actor=f['affected_entity'];isactor=actor in byactor;tracks=result['actor_pose_tracks'] if isactor else result['object_tracks']
        if actor not in tracks:raise ValueError('FRAGMENT_ACTOR_BINDING_MISSING '+actor)
        original=tracks[actor];base={r['frame']:r['state'] for r in original}
        if len(base)!=n:raise ValueError('FRESH_TEMPLATE_REQUIRES_DENSE_STATIC_TRACKS')
        samples=f['world_samples'];lo,hi=samples[0]['frame'],samples[-1]['frame'];chans=f['channel_ownership']['WRITES']
        for frame in range(1,n+1):
            if lo<=frame<=hi:r=samples[frame-lo]
            else:
                # Explicit continuation contract; no project-specific exterior motion code.
                edge=samples[0] if frame<lo else samples[-1];r=dict(edge)
                r['position']=add(edge['position'],mul(edge['velocity'],(frame-edge['frame'])/fps))
                if f['primitive_id'] in additive:
                    policy=f['metadata']['derived_parameters'].get('return_mode','RETURN_TO_BASE')
                    if frame<lo or policy=='RETURN_TO_BASE':continue
                    r['offset']=add(edge['offset'],mul(f['metadata']['derived_parameters'].get('exit_offset_velocity',[0,0,0]),(frame-hi)/fps))
                peers=[g for g in frags if g['affected_entity']==actor and set(chans)&set(g['channel_ownership']['WRITES']) and g['primitive_id'] not in additive]
                if f['primitive_id'] not in additive:
                    if frame<lo and f is not min(peers,key=lambda g:g['time_range'][0]):continue
                    if frame>hi and f is not max(peers,key=lambda g:g['time_range'][1]):continue
                # Another fragment on this channel owns this exterior interval.
                if f['primitive_id'] not in additive and any(g is not f and g['affected_entity']==actor and set(chans)&set(g['channel_ownership']['WRITES']) and g['world_samples'][0]['frame']<=frame<=g['world_samples'][-1]['frame'] for g in frags):continue
            st=base[frame]
            for ch in chans:
                if ch=='ATTACHMENT_STATE':continue
                if ch in ('ROOT_LOCATION','CAMERA_LOCATION','PROJECTILE_TRANSFORM','WEAPON_TRANSFORM'):
                    field='position' if isactor else 'location';st[field]=add(st[field],r['offset']) if f['primitive_id'] in additive else r['position']
                if 'ROTATION' in ch or ch in ('WEAPON_TRANSFORM','PROJECTILE_TRANSFORM'):
                    if isactor:
                        angles=[math.degrees(x) for x in euler(r['orientation'])]
                        if ch=='BODY_ROTATION':
                            st['body_yaw']=angles[2];st['body_pitch']=-angles[0]
                            if abs(angles[1])>1e-8 or 'body_roll' in st:st['body_roll']=angles[1]
                        elif ch=='HEAD_ROTATION':
                            if abs(angles[1])>1e-5:raise ValueError('HEAD_ROLL_OUTSIDE_EXISTING_BUILDER_CONTRACT')
                            st['head_yaw']=angles[2];st['head_pitch']=-angles[0]
                        else:st['yaw']=angles[2];st['root_pitch']=angles[0];st['root_roll']=angles[1]
                    else:st['rotation_mode']='QUATERNION';st['rotation']=r['orientation']
                if ch=='CAMERA_LENS':st['lens']=r['lens']
    errors=validate(result)
    if errors:raise ValueError('MERGED_CSP_INVALID '+str(errors))
    return result
