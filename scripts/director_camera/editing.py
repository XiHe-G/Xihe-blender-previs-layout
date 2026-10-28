"""Opt-in camera/edit review helpers. Technical evidence, never art acceptance."""
import math
from .motion import mix,progress,diagnose

def attention_track(nodes,samples,curve='SMOOTHSTEP'):
    """Independent ordered attention nodes; never modifies camera translation."""
    if samples<2 or len(nodes)<2 or nodes[0][0]!=0 or nodes[-1][0]!=1:raise ValueError('ATTENTION_COVERAGE')
    if any(b[0]<=a[0] for a,b in zip(nodes,nodes[1:])):raise ValueError('ATTENTION_ORDER')
    if any(len(p)!=3 or not all(math.isfinite(x) for x in p) for _,p in nodes):raise ValueError('ATTENTION_POINT')
    out=[]
    for i in range(samples):
        t=i/(samples-1)
        for a,b in zip(nodes,nodes[1:]):
            if a[0]<=t<=b[0]:
                out.append([t,list(mix(a[1],b[1],progress((t-a[0])/(b[0]-a[0]),curve)))]);break
    return out

def validate_cuts(shots,markers,evaluated):
    """Require unique per-shot cameras and exact marker/actual boundary bindings."""
    failures=[];rows=[]
    if not shots:raise ValueError('EMPTY_SHOT_LIST')
    bound=[m for m in markers if m.get('camera')]
    if len({s['camera'] for s in shots})!=len(shots):failures.append('INDEPENDENT_CAMERAS_REQUIRED')
    for index,s in enumerate(shots):
        if s['end']<s['start']:failures.append('REVERSED_RANGE')
        if index and s['start']!=shots[index-1]['end']+1:failures.append('GAP_OR_OVERLAP')
        exact=[m for m in bound if m['frame']==s['start']]
        good=len(exact)==1 and exact[0]['camera']==s['camera']
        if not good:failures.append('CUT_MARKER_MISMATCH:'+s['id'])
        observed=[evaluated.get(f) for f in range(s['start'],s['end']+1)]
        if any(c!=s['camera'] for c in observed):failures.append('EVALUATED_CAMERA_MISMATCH:'+s['id'])
        extra=[m for m in bound if s['start']<m['frame']<=s['end']]
        if extra:failures.append('UNAUTHORIZED_INTERNAL_CUT:'+s['id'])
        rows.append(dict(shot=s['id'],start=s['start'],end=s['end'],camera=s['camera'],marker_ok=good))
    return dict(status='FAIL' if failures else 'PASS',failures=failures,shots=rows,artistic_status='NOT_REVIEWED')

def axis_side(a,b,camera,epsilon=1e-6):
    x=(b[0]-a[0])*(camera[1]-a[1])-(b[1]-a[1])*(camera[0]-a[0])
    if math.hypot(b[0]-a[0],b[1]-a[1])<epsilon:return 'UNDEFINED'
    return 'NEUTRAL' if abs(x)<epsilon else 'LEFT' if x>0 else 'RIGHT'

def axis_transition(before,after,policy='REVIEW'):
    if policy=='INTENTIONAL_REVERSE':return 'AUTHORIZED_REVERSE_REVIEW_VISUAL'
    if before in {'NEUTRAL','UNDEFINED'} or after in {'NEUTRAL','UNDEFINED'}:return 'NOT_REVIEWED'
    return 'SAME_SIDE_ONLY' if before==after else 'CROSSING_REVIEW_REQUIRED'

def motion_contract(points,fps,kind,quaternions=None,tolerance=1e-4):
    result=diagnose(points,fps,quaternions,tolerance)
    if kind in {'STRAIGHT_TRANSLATION','STRAIGHT_TRACKING','VERTICAL_CRANE'}:
        ok=result['straight_within_tolerance'] and not result['backtracking_steps']
        if kind=='VERTICAL_CRANE':ok=ok and max(math.hypot(p[0]-points[0][0],p[1]-points[0][1]) for p in points)<=tolerance
    elif kind in {'STATIC_HOLD','STATIC_ROTATION'}:
        ok=result['stationary']
        if kind=='STATIC_HOLD':
            if quaternions is None:
                return dict(status='PASS' if ok else 'FAIL',scope='TRANSLATION_ONLY',orientation_status='NOT_REVIEWED',measurements=result,artistic_status='NOT_REVIEWED')
            ok=ok and max(result['angular_speed_deg_s'],default=0)<=math.degrees(tolerance)*fps
    elif kind in {'INTENTIONAL_ARC','ORBIT','COMPOUND_MOVE'}:return dict(status='INTENT_REVIEW_REQUIRED',measurements=result)
    else:raise ValueError('UNBOUND_MOTION_KIND')
    return dict(status='PASS' if ok else 'FAIL',measurements=result,artistic_status='NOT_REVIEWED')

def reserve_round(ledger,shot,root_cause,limit=3):
    """Budget belongs to shot across root causes/renamed variants."""
    if not shot or not root_cause:raise ValueError('UNBOUND_ISSUE')
    n=sum(x['shot']==shot for x in ledger)
    if n>=limit:raise ValueError('SHOT_BUDGET_EXHAUSTED')
    entry=dict(shot=shot,root_cause=root_cause,round=n+1,status='RESERVED');ledger.append(entry);return entry
