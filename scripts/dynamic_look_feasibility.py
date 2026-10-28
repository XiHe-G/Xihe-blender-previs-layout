"""Target-track orientation feasibility; read-only."""
import math
from primitive_sampler import sub,norm,qangle,unit
from orientation_feasibility import orientation_budget

def dynamic_look_feasibility(target_track,subject_track,start,end,max_angular_speed,head_lead_time=0.,body_delay=0.):
    samples=[x for x in target_track if start-1e-9<=x['time']<=end+1e-9]
    subject={round(x['time'],6):x for x in subject_track}
    if len(samples)<2:return {'status':'NEEDS_AUTHOR_INPUT','failure_code':'TARGET_TRACK_UNAVAILABLE','samples':len(samples)}
    required=[];prev=None
    for x in samples:
        s=subject.get(round(x['time'],6)) or subject_track[min(range(len(subject_track)),key=lambda i:abs(subject_track[i]['time']-x['time']))]
        direction=sub(x['position'],s['position']);
        if norm(direction)<1e-8:continue
        if prev is not None:
            dt=x['time']-prev[0];ang=math.acos(max(-1.,min(1.,sum(a*b for a,b in zip(unit(prev[1]),unit(direction))))));required.append({'time':x['time'],'angular_velocity':ang/dt if dt else float('inf'),'delta':ang})
        prev=(x['time'],direction)
    peak=max([r['angular_velocity'] for r in required] or [0.]);allowed=math.radians(max_angular_speed)
    head='PASS' if peak<=allowed+1e-9 else 'INFEASIBLE_TRACKING'
    if head!='PASS' and (body_delay>0 or head_lead_time>0):
        # Split changes the channel ownership and available window; it does not change the target track.
        head_window=max(head_lead_time,1/30);body_window=max((end-start)-body_delay,1/30)
        split='FEASIBLE_WITH_CHANNEL_SPLIT' if peak*head_window<=allowed*max(head_window,body_window) else 'INFEASIBLE_TRACKING'
    else:split=head
    return {'status':split,'peak_required_angular_speed':peak,'allowed_angular_speed':allowed,'samples':len(samples),'required_samples':required,'head_lead_time':head_lead_time,'body_delay':body_delay,'source':'EVALUATED_TARGET_RESOLUTION'}
