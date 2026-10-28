"""Six camera execution tools sharing S3.5 HOLD policy. No artistic selection."""
import math
from primitive_sampler import *
from checker_calibration import PROFILES,camera_hold

def make_camera(p,times,reads):
    q=p['parameters'];e=p['entry_state'];typ=p['primitive_type'];start=p['start_time'];T=p['end_time']-start
    origin=e['position'];ori=e['orientation'];lens=e.get('lens',50.);rows=[];derived={};aspect=q.get('aspect_ratio',16/9)
    target_name=q.get('target',q.get('subject'));target_track=reads.get(target_name) if isinstance(target_name,str) else None
    def target(t):return add(sample_track(target_track,t),q.get('target_offset',[0,0,0])) if target_track else q.get('target_point',[0,0,1])
    first=target(start);offset=q.get('tracking_offset',sub(origin,first))
    if q.get('distance') is not None and abs(norm(offset)-q['distance'])>1e-5:raise ValueError('CAMERA_ENTRY_DISTANCE_CONFLICT')
    state=origin[:];velocity=e.get('camera_velocity',e.get('velocity',[0,0,0]))[:]
    for i,t in enumerate(times):
        u=clamp((t-start)/T);dt=times[i]-times[i-1] if i else 0;pos=origin[:];rotation=ori[:];l=lens
        if typ=='CAM_HOLD':
            profile=q['behavior_profile']
            if profile not in PROFILES:raise ValueError('UNKNOWN_HOLD_PROFILE')
            derived['hold_limits']={'source':'S35/1.0 TECHNICAL_DEFAULT','limits':dict(PROFILES[profile])}
            if profile=='COMPOSITION_HOLD':pos=add(origin,mul(sub(target(start+T),first),smooth(u)))
            elif profile=='SOFT_HOLD':pos=add(origin,mul(sub(target(t),first),q.get('follow_strength',.05)*smooth(u)))
        elif typ=='CAM_REFRAME':
            region=q['target_screen_region'];anchor=[(region[0]+region[2])/2,(region[1]+region[3])/2]
            wanted=look_at(origin,target(t));dx=math.atan((anchor[0]-.5)*36/lens);dy=math.atan((anchor[1]-.5)*36/lens/aspect)
            wanted=qmul(wanted,qmul([math.cos(dy/2),math.sin(dy/2),0,0],[math.cos(dx/2),0,math.sin(dx/2),0]))
            if math.degrees(qangle(ori,wanted))>q['max_rotation']+1e-6:raise ValueError('REFRAME_ROTATION_LIMIT')
            rotation=slerp(ori,wanted,smooth(u))
            translation=q.get('translation',[0,0,0])
            if norm(translation)>q.get('max_translation',0)+1e-9:raise ValueError('REFRAME_TRANSLATION_LIMIT')
            pos=add(origin,mul(translation,smooth(u)))
        elif typ=='CAM_PUSH_PULL':
            delta=q['distance_delta'];mode=q['mode']
            if delta<0 or mode not in ('PUSH','PULL'):raise ValueError('INVALID_DOLLY')
            a,_,_,_=progress(q.get('profile','EASE_IN_OUT'),u,T,delta)
            pos=add(origin,mul(unit(sub(first,origin)),delta*a*(1 if mode=='PUSH' else -1)))
            if q.get('lens_policy','FIXED')=='EXPLICIT_ZOOM':l=lens+(q['exit_lens']-lens)*smooth(u)
            elif 'exit_lens' in q:raise ValueError('ZOOM_REQUIRES_EXPLICIT_POLICY')
        elif typ in ('CAM_FOLLOW','CAM_LEAD_LAG','CAM_CATCH_UP'):
            lag=q.get('lag',q.get('lag_time',0));desired=add(target(t-lag),offset)
            if typ=='CAM_LEAD_LAG':
                a=target(t);b=target(t+1/30);direction=unit(sub(b,a));gain=smooth((t-start)/max(q.get('transition_duration',T),1e-6))
                desired=add(desired,mul(direction,q.get('lead_distance',0)*gain))
            if typ=='CAM_CATCH_UP':
                catch=q.get('catchup_start',.25);settle=q.get('settle_start',.8)
                if not 0<catch<settle<1:raise ValueError('INVALID_CATCHUP_PHASES')
                gain=smooth((u-catch)/(settle-catch));desired=lerp(add(target(t-q.get('entry_lag',.5)),offset),add(target(t),offset),gain)
                strength=q.get('follow_strength',8)*(0.15+.85*gain)
                derived['phases']={'entry_lag':[start,start+catch*T],'acceleration_catchup':[start+catch*T,start+settle*T],'settle':[start+settle*T,start+T]}
            else:strength=q.get('follow_strength',4)
            initial_lag=q.get('entry_lag',.5) if typ=='CAM_CATCH_UP' else lag
            entry_bias=sub(origin,add(target(start-initial_lag),offset))
            # Acquire the delayed trajectory from the declared entry pose. Removing this
            # correction would introduce an initial backwards lurch when a read uses guards.
            desired=add(desired,mul(entry_bias,1-smooth(u)))
            if strength<=0:raise ValueError('INVALID_FOLLOW_STRENGTH')
            # Critically damped spring, fixed substeps; carries velocity rather than rigid offset copying.
            if i:
                n=8;h=dt/n
                for _ in range(n):
                    accel=sub(mul(sub(desired,state),strength*strength),mul(velocity,2*strength));velocity=add(velocity,mul(accel,h));state=add(state,mul(velocity,h))
            pos=state[:]
            # Retain orientation unless explicit screen-anchor tracking is requested.
            if q.get('track_rotation',True):
                wanted=look_at(pos,target(t));anchor=q.get('screen_anchor',[.5,.5]);bias=q.get('screen_bias',0)
                angle=math.atan((anchor[0]-.5+bias)*36/lens)
                pitch=math.atan((anchor[1]-.5)*36/lens/aspect);wanted=qmul(wanted,qmul([math.cos(pitch/2),math.sin(pitch/2),0,0],[math.cos(angle/2),0,math.sin(angle/2),0]));rotation=slerp(ori,wanted,smooth(u))
        else:raise ValueError('UNKNOWN_CAMERA_PRIMITIVE')
        uv=project(pos,rotation,l,target(t),aspect);depth=norm(sub(target(t),pos))
        rows.append(dict(time=t,position=pos,orientation=rotation,lens=l,subject_screen_position=uv,subject_screen_size=q.get('subject_height',1.8)*l*aspect/(36*max(depth,1e-9)),subject_position=target(t)))
    for i,r in enumerate(rows):r['velocity']=derivative(rows,i)
    if typ in ('CAM_FOLLOW','CAM_LEAD_LAG','CAM_CATCH_UP'):rows[0]['velocity']=e.get('camera_velocity',e.get('velocity',[0,0,0]))
    if typ in ('CAM_HOLD','CAM_REFRAME','CAM_PUSH_PULL'):
        rows[0]['velocity']=[0,0,0]
        if typ!='CAM_HOLD' or q['behavior_profile']!='SOFT_HOLD':rows[-1]['velocity']=[0,0,0]
    if typ=='CAM_HOLD':
        projected=[{'camera_transform':{'object':p['actor'],'position':r['position'],'quaternion':r['orientation']},'camera_lens':r['lens'],'entities':{'SUBJECT':{'screen_center':r['subject_screen_position'],'screen_height_ratio':r['subject_screen_size'],'screen_bounds':{'clipped_bounds':[0,0,1,1] if r['subject_screen_position'] and all(0<=v<=1 for v in r['subject_screen_position']) else None},'entity_world_state':{'position':r['subject_position']}}}} for r in rows]
        status,code,actual,_=camera_hold({'behavior_profile':q['behavior_profile'],'subjects':['SUBJECT']},projected)
        derived['shared_checker_preview']={'status':status,'code':code,'actual':actual,'basis':'POINT_PROJECTION_ESTIMATE; native mesh check required after build'}
        if status=='FAIL':raise ValueError('HOLD_PROFILE_CONSTRAINT '+str(actual))
    return rows,derived
