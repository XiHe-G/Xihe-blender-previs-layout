"""Opt-in, evidence-scoped shot review. No project IDs, artistic scores or auto approval."""
import math

def facing_relation(world_forward, origin, target, max_angle_deg=45):
    """Actual proxy front vs intended target, not eye gaze or artistic approval.

    Caller transforms the documented local front by evaluated orientation.
    There is no universal +Y front or inferred character identity.
    """
    vectors=[world_forward,origin,target]
    if any(len(v)!=3 or not all(math.isfinite(x) for x in v) for v in vectors):raise ValueError('FINITE_3D_VECTORS_REQUIRED')
    if not math.isfinite(max_angle_deg) or not 0<=max_angle_deg<=180:raise ValueError('ANGLE_RANGE')
    delta=[b-a for a,b in zip(origin,target)]
    lf=math.sqrt(sum(x*x for x in world_forward));ld=math.sqrt(sum(x*x for x in delta))
    if min(lf,ld)<1e-8:return dict(status='NOT_REVIEWED',reason='undefined facing or coincident target')
    dot=sum(a*b for a,b in zip(world_forward,delta))/(lf*ld)
    angle=math.degrees(math.acos(max(-1,min(1,dot))))
    return dict(status='WITHIN_REQUESTED_CONE' if angle<=max_angle_deg else 'OUTSIDE_REQUESTED_CONE',angle_deg=angle,gaze='NOT_REVIEWED')

def frame_relation(bounds, depths):
    if len(bounds)!=4 or not depths or not all(math.isfinite(x) for x in [*bounds,*depths]):
        return 'UNKNOWN'
    if max(depths)<=0:return 'BEHIND_CAMERA'
    if min(depths)<=0:return 'NEAR_PLANE_REVIEW'
    x0,y0,x1,y1=bounds
    if x1<x0 or y1<y0:return 'UNKNOWN'
    if x1<0 or x0>1 or y1<0 or y0>1:return 'OUTSIDE'
    if 0<=x0<=x1<=1 and 0<=y0<=y1<=1:return 'INSIDE'
    return 'PARTIAL'

def solo_frame(subject, others, required=False):
    """Bounds establish exclusion only, not visibility through walls or performance."""
    own=frame_relation(subject['bounds'],subject['depths'])
    other={key:frame_relation(v['bounds'],v['depths']) for key,v in others.items()}
    if not required:return dict(status='NOT_REQUIRED',others=other)
    if own in ('UNKNOWN','NEAR_PLANE_REVIEW') or any(v in ('UNKNOWN','NEAR_PLANE_REVIEW') for v in other.values()):return dict(status='NOT_REVIEWED',others=other)
    visible=[k for k,v in other.items() if v in ('INSIDE','PARTIAL')]
    return dict(status='FAIL' if visible or own in ('OUTSIDE','BEHIND_CAMERA') else 'PASS_GEOMETRIC_EXCLUSION_ONLY',visible_others=visible,others=other)

def exit_window(samples, required=False, min_hold_frames=1):
    if not required:return {'status':'NOT_REQUIRED','reason':'Departure does not imply full-frame exit.'}
    if min_hold_frames<1:raise ValueError('POSITIVE_HOLD_REQUIRED')
    count=0
    for row in reversed(samples):
        if frame_relation(row['bounds'],row['depths']) in ('OUTSIDE','BEHIND_CAMERA'):count+=1
        else:break
    return dict(status='PASS_GEOMETRIC_EXIT_ONLY' if count>=min_hold_frames else 'FAIL',outside_tail_frames=count)

def depth_order(foreground_depth,subject_depth,required=False):
    if not required:return {'status':'NOT_REQUIRED'}
    if min(foreground_depth,subject_depth)<=0:return {'status':'NOT_REVIEWED'}
    return {'status':'PASS_DEPTH_ONLY' if foreground_depth<subject_depth else 'FAIL','gap':subject_depth-foreground_depth}

def event_window(event,shot_start,shot_end):
    if event['end']<event['start']:raise ValueError('INVALID_EVENT')
    if event.get('allowed_offscreen'):return {'status':'NOT_REQUIRED'}
    return {'status':'PASS_TIMING_ONLY' if shot_start<=event['start']<=event['end']<=shot_end else 'FAIL_EVENT_TRUNCATED'}

def cut_direction(before,after,policy='REVIEW'):
    if policy not in ('REVIEW','MATCH_REQUIRED','INTENTIONAL_REVERSAL'):raise ValueError('UNKNOWN_POLICY')
    if policy=='INTENTIONAL_REVERSAL':return {'status':'NOT_REQUIRED'}
    if abs(before)<1e-6 or abs(after)<1e-6:return {'status':'NOT_REVIEWED','reason':'No reliable movement direction'}
    opposite=before*after<0
    return {'status':('FAIL' if policy=='MATCH_REQUIRED' else 'REVIEW_REQUIRED') if opposite else 'PASS_DIRECTION_ONLY'}

def evidence_frames(start,end,events=(),step=12):
    if start>end or step<1:raise ValueError('INVALID_RANGE')
    frames={start,end,*range(start,end+1,step)}
    for f in events:
        frames.update(k for k in [f-1,f,f+1] if start<=k<=end)
    return sorted(frames)

def authorize_iteration(issue,history):
    """New numbering cannot reset the budget; reuse the stable root-cause key."""
    if not issue.get('root_cause') or not issue.get('evidence') or not issue.get('authorized_channels'):raise ValueError('UNBOUND_REPAIR')
    rounds=sum(1 for row in history if row['root_cause']==issue['root_cause'])
    if rounds>=4:raise ValueError('ITERATION_BUDGET_EXHAUSTED')
    if set(issue['authorized_channels'])-{'CAMERA','ACTION','PROP','SCENE','EDITING'}:raise ValueError('UNKNOWN_CHANNEL')
    if len(issue['authorized_channels'])!=1:raise ValueError('INDEPENDENT_CONTROLS_REQUIRED')
    return rounds+1

def protected_signature(before,after,allowed_keys):
    changed={k for k in set(before)|set(after) if before.get(k)!=after.get(k)}
    unauthorized=changed-set(allowed_keys)
    if unauthorized:raise ValueError('PROTECTED_CHANNEL_CHANGED: '+','.join(sorted(unauthorized)))
    return sorted(changed)

def event_aim_track(samples,start,end,height_start,height_end):
    """Bind attention XY to evaluated actor timing; never move the camera position.

    Height is an explicit independent composition choice. No inferred choreography.
    """
    if end<=start or len(samples)!=end-start+1 or [s['frame'] for s in samples]!=list(range(start,end+1)):
        raise ValueError('COMPLETE_ORDERED_EVENT_SAMPLES_REQUIRED')
    result=[]
    for row in samples:
        if len(row['position'])!=3 or not all(math.isfinite(x) for x in row['position']):raise ValueError('INVALID_EVENT_POSITION')
        u=(row['frame']-start)/(end-start);smooth=u*u*(3-2*u)
        result.append([u,[row['position'][0],row['position'][1],height_start+(height_end-height_start)*smooth]])
    return result
