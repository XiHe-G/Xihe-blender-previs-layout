"""Six generic motion kernels. No bpy, scene state, or project-specific branches."""
import math
from primitive_sampler import *

def target_at(q,t,reads):
    target=q.get('target_entity',q.get('target'))
    if isinstance(target,str):return sample_track(reads[target],t)
    return q.get('target_point',target or [0,1,0])
def make_motion(p,times,reads):
    typ=p['primitive_type'];q=p['parameters'];entry=p['entry_state'];start=p['start_time'];end=p['end_time'];T=end-start
    origin=q.get('start_position',entry['position']);rows=[];derived={};v0=v1=None
    if typ in ('MOVE_PROFILE','APPROACH_TARGET'):
        dest=q.get('end_position')
        if typ=='APPROACH_TARGET':
            if abs(q.get('arrival_time',end)-end)>1e-9:raise ValueError('ARRIVAL_TIME_CONFLICT')
            target=target_at(q,end,reads);direction=unit(q.get('approach_direction',sub(target,origin)))
            dest=sub(target,mul(direction,q['desired_distance']))
        if dest is None:raise ValueError('MISSING_END_POSITION')
        kind=q.get('path_type','LINEAR');points=q.get('points',[origin,dest])
        if norm(sub(points[0],origin))>1e-8 or norm(sub(points[-1],dest))>1e-8:raise ValueError('PATH_ENDPOINT_CONFLICT')
        length,curve=arclength_path(points,kind);tin=unit(sub(points[1],points[0]));tout=unit(sub(points[-1],points[-2]))
        def speed(name,tangent):
            alias='start_velocity' if name=='entry_velocity' else 'end_velocity';v=q.get(name,q.get(alias))
            if name in q and alias in q and q[name]!=q[alias]:raise ValueError('VELOCITY_ALIAS_CONFLICT')
            if v is None:return None
            if isinstance(v,(int,float)):return v
            if norm(sub(v,mul(tangent,dot(v,tangent))))>1e-5 or dot(v,tangent)<0:raise ValueError('VELOCITY_TANGENT_CONFLICT')
            return norm(v)
        for t in times:
            u,a,b,d=progress(q.get('timing_profile','ACCEL_CRUISE_DECEL'),(t-start)/T,T,length,speed('entry_velocity',tin),speed('exit_velocity',tout),q.get('peak_velocity'),q.get('normalized_curve'))
            if t==end:u=1.
            pos=curve(u);ori=entry['orientation']
            if typ=='APPROACH_TARGET':
                direction=sub(target_at(q,t,reads),pos);wanted=qmul(look_at([0,0,0],direction),[math.sqrt(.5),-math.sqrt(.5),0,0]);desired=slerp(entry['orientation'],wanted,smooth((t-start)/T));prev=rows[-1]['orientation'] if rows else entry['orientation'];angle=qangle(prev,desired);dt=t-rows[-1]['time'] if rows else 0;ori=slerp(prev,desired,min(1,math.radians(q.get('max_angular_speed',90))*dt/angle)) if angle>1e-12 else prev
            rows.append(dict(time=t,position=pos,orientation=ori));derived=d;v0=mul(tin,a);v1=mul(tout,b)
    elif typ=='ORIENT_TO':
        mode=q.get('orientation_mode','SMOOTH');prev=entry['orientation'];limit=math.radians(q['max_angular_speed'])
        if mode not in ('SNAP','SMOOTH','LEAD','LAG'):raise ValueError('UNKNOWN_ORIENTATION_MODE')
        if mode=='SNAP' and not q.get('snap_authorized'):raise ValueError('SNAP_REQUIRES_AUTHORIZATION')
        for i,t in enumerate(times):
            dt=times[i]-times[i-1] if i else 0;u=(t-start)/T;delay=q.get('lead_delay',0)*(1 if mode=='LEAD' else -1 if mode=='LAG' else 0)
            pos=sample_track(reads[p['actor']],t) if p['actor'] in reads else origin
            direction=q['target'] if q.get('target_type')=='WORLD_DIRECTION' else sub(target_at(q,t+delay,reads),pos)
            wanted=qmul(look_at([0,0,0],direction),[math.sqrt(.5),-math.sqrt(.5),0,0])
            if q.get('target_fraction') is not None:
                wanted=slerp(entry['orientation'],wanted,max(0.,min(1.,float(q['target_fraction']))))
            if q.get('channel','BODY') in ('BODY','HEAD'):
                parent=sample_track(reads[q['parent_orientation_track']],t,'orientation') if q.get('parent_orientation_track') else sample_track(reads[p['actor']],t,'orientation') if p['actor'] in reads else [1,0,0,0]
                wanted=qmul([parent[0],-parent[1],-parent[2],-parent[3]],wanted)
            desired=wanted if mode=='SNAP' else slerp(entry['orientation'],wanted,smooth(u))
            if q.get('angular_timing_profile')=='EASE_IN_OUT_ROTATION' and qangle(prev,desired)>limit*dt+1e-6 and i:
                raise ValueError('INFEASIBLE_DURATION: angular speed limit')
            angle=qangle(prev,desired);ori=(prev if i==0 else desired) if mode=='SNAP' else slerp(prev,desired,min(1,limit*dt/angle)) if angle>1e-12 else prev
            rows.append(dict(time=t,position=pos,orientation=ori));prev=ori
        v0=derivative(rows,0);v1=derivative(rows,len(rows)-1)
    elif typ=='OFFSET_PATH':
        peak=q['peak_time'];mode=q['return_mode']
        if not start<peak<end:raise ValueError('INVALID_OFFSET_PEAK')
        if mode not in ('KEEP_OFFSET','RETURN_TO_BASE','TRANSITION_TO_NEW_PATH'):raise ValueError('INVALID_RETURN_MODE')
        direction=unit(q['offset_direction']);base=reads[q['base_primitive']] if 'base_primitive' in q else q['base_path']
        for t in times:
            weight=smooth((t-start)/(peak-start)) if t<=peak else 1-smooth((t-peak)/(end-peak)) if mode=='RETURN_TO_BASE' else 1
            offset=mul(direction,q['offset_distance']*weight)
            if mode=='TRANSITION_TO_NEW_PATH' and t>peak:
                new=sample_track(q['new_path'],t);old=add(sample_track(base,t),offset);offset=sub(lerp(old,new,smooth((t-peak)/(end-peak))),sample_track(base,t))
            rows.append(dict(time=t,position=add(sample_track(base,t),offset),offset=offset,orientation=entry['orientation']))
        v0=sample_track(base,start,'velocity') if 'velocity' in base[0] else derivative(rows,0);v1=sample_track(base,end,'velocity') if 'velocity' in base[0] else derivative(rows,len(rows)-1)
        base_exit=list(v1)
        if mode=='TRANSITION_TO_NEW_PATH':v1=sample_track(q['new_path'],end,'velocity') if 'velocity' in q['new_path'][0] else derivative(q['new_path'],len(q['new_path'])-1)
        derived={'return_mode':mode,'exit_offset_velocity':sub(v1,base_exit)}
    elif typ=='ATTACH_DETACH':
        owner=reads[q['owner']];release=q['detach_time'];socket=q.get('attachment_transform',{}).get('position',[0,0,0]);detach=mul(unit(q['detach_direction']),q['detach_velocity'])
        if not start<release<end:raise ValueError('INVALID_DETACH_TIME')
        def anchor(t):return add(sample_track(owner,t),rotate(sample_track(owner,t,'orientation'),socket))
        dt=times[1]-times[0];owner_v=mul(sub(anchor(release),anchor(release-dt)),1/dt)
        free_v=add(detach,mul(owner_v,q.get('inherit_owner_velocity',0)));release_pos=anchor(release)
        derived={'inherited_owner_velocity':mul(owner_v,q.get('inherit_owner_velocity',0)),'free_velocity':free_v,'native_owner_semantics':'release provenance retained; physical attachment becomes FREE'}
        for t in times:
            state='ATTACHED' if t<release else 'DETACHING' if abs(t-release)<1e-9 else 'FREE'
            elapsed=max(0,t-release);ramp=q.get('release_ramp_duration',0)
            if ramp:
                z=min(1,elapsed/ramp);extra=ramp*smooth_integral(z)+max(0,elapsed-ramp)
                pos=add(release_pos,add(mul(owner_v,elapsed),mul(sub(free_v,owner_v),extra)))
                if t<=release:pos=anchor(t)
            else:pos=anchor(t) if t<=release else add(release_pos,mul(free_v,t-release))
            if q.get('reattach_time') is not None and t>=q['reattach_time']:
                attach_pos=anchor(t)
                if abs(t-q['reattach_time'])<dt/2 and norm(sub(pos,attach_pos))>1e-5:raise ValueError('REATTACH_POSITION_CONFLICT')
                pos=attach_pos;state='REATTACHED'
            rows.append(dict(time=t,position=pos,orientation=entry['orientation'],ownership_state=state,owner=q['owner']))
        v0=derivative(owner,0);v1=free_v
    elif typ=='RECOVERY_PROFILE':
        initial=q['entry_velocity'];final=q.get('exit_velocity',[0,0,0]);retention=q.get('direction_retention',1)
        if not 0<=retention<=1:raise ValueError('INVALID_DIRECTION_RETENTION')
        if q.get('duration',T)!=T:raise ValueError('RECOVERY_DURATION_CONFLICT')
        if norm(initial) and norm(final) and dot(unit(initial),unit(final))<retention-1e-8:raise ValueError('DIRECTION_RETENTION_CONFLICT')
        distance=norm(mul(add(initial,final),T/2))
        if distance>q['displacement_limit']+1e-9:raise ValueError('RECOVERY_DISPLACEMENT_INFEASIBLE')
        for t in times:
            u=(t-start)/T;pos=add(origin,add(mul(initial,T*u),mul(sub(final,initial),T*smooth_integral(u))))
            ori=slerp(entry['orientation'],q.get('orientation_recovery',entry['orientation']),smooth(u))
            rows.append(dict(time=t,position=pos,orientation=ori))
        v0,v1=initial,final
    else:raise ValueError('UNKNOWN_MOTION_PRIMITIVE')
    for i,r in enumerate(rows):
        r['velocity']=v0 if i==0 and v0 is not None else v1 if i==len(rows)-1 and v1 is not None else derivative(rows,i)
    return rows,derived
