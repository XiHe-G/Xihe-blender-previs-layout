"""Independent path geometry, progress and aim; world-space contract, no noise.

No scene-specific coordinates or shot IDs. Pure Python; native adapter is separate.
"""
import math
KINDS={'STRAIGHT_TRANSLATION','STATIC_ROTATION','STRAIGHT_TRACKING','VERTICAL_CRANE','INTENTIONAL_ARC','ORBIT','FOLLOW_WITH_LAG','COMPOUND_MOVE','STATIC_HOLD'}
def add(a,b):return tuple(x+y for x,y in zip(a,b))
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def mul(a,s):return tuple(x*s for x in a)
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def length(a):return math.sqrt(dot(a,a))
def mix(a,b,u):return add(a,mul(sub(b,a),u))
def progress(u,curve='LINEAR',beats=None):
 u=max(0.,min(1.,u))
 if curve=='LINEAR':return u
 if curve=='EASE_IN':return u*u
 if curve=='EASE_OUT':return 1-(1-u)**2
 if curve=='SMOOTHSTEP':return u*u*(3-2*u)
 if curve=='EASE_IN_OUT':return u*u*u*(10+u*(-15+6*u))
 if curve=='BEAT':
  if not beats or beats[0]!=[0,0] or beats[-1]!=[1,1]:raise ValueError('BEAT_ENDPOINTS')
  if any(b[0]<=a[0] or b[1]<a[1] for a,b in zip(beats,beats[1:])):raise ValueError('BEAT_MONOTONICITY')
  for a,b in zip(beats,beats[1:]):
   if a[0]<=u<=b[0]:return a[1]+(b[1]-a[1])*progress((u-a[0])/(b[0]-a[0]),'EASE_IN_OUT')
 raise ValueError('UNKNOWN_PROGRESS')
def position(plan,u):
 k=plan['kind']
 if k not in KINDS:raise ValueError('UNSUPPORTED_MOTION')
 v=progress(u,plan.get('curve','LINEAR'),plan.get('beats'));a=tuple(plan['start']);b=tuple(plan.get('end',a))
 if not all(math.isfinite(x) for x in a+b) or len(a)!=3 or len(b)!=3:raise ValueError('NONFINITE_POSITION')
 if k in {'STATIC_HOLD','STATIC_ROTATION'}:
  if length(sub(b,a))>1e-9:raise ValueError('FIXED_POSITION_CONFLICT')
  if k=='STATIC_HOLD' and 'aim_start' in plan and length(sub(plan.get('aim_end',plan['aim_start']),plan['aim_start']))>1e-9:raise ValueError('STATIC_AIM_CONFLICT')
  return a
 if k=='VERTICAL_CRANE' and length(sub(a[:2],b[:2]))>1e-9:raise ValueError('VERTICAL_AXIS_CONFLICT')
 if k in {'STRAIGHT_TRANSLATION','STRAIGHT_TRACKING','VERTICAL_CRANE'}:return mix(a,b,v)
 if k in {'INTENTIONAL_ARC','ORBIT'}:
  p=plan['pivot'];r=length(sub(a[:2],p[:2]));angle=math.atan2(a[1]-p[1],a[0]-p[0])+plan['sweep_radians']*v
  re=plan.get('end_radius',r)
  if k=='ORBIT' and abs(re-r)>1e-9:raise ValueError('ORBIT_RADIUS_CONFLICT')
  final_angle=math.atan2(a[1]-p[1],a[0]-p[0])+plan['sweep_radians']
  if length(sub((p[0]+re*math.cos(final_angle),p[1]+re*math.sin(final_angle)),b[:2]))>1e-6:raise ValueError('ARC_ENDPOINT_CONFLICT')
  rr=r+(re-r)*v
  return (p[0]+rr*math.cos(angle),p[1]+rr*math.sin(angle),a[2]+(b[2]-a[2])*v)
 if k=='FOLLOW_WITH_LAG':
  nodes=plan['target_path'];lag=plan.get('lag_fraction',0.)
  if len(nodes)<2:raise ValueError('FOLLOW_REQUIRES_TARGET_HISTORY')
  if not 0<=lag<=1:raise ValueError('INVALID_LAG')
  t=max(0.,min(1.,u-lag));idx=min(int(t*(len(nodes)-1)),len(nodes)-2)
  return add(mix(nodes[idx],nodes[idx+1],t*(len(nodes)-1)-idx),plan['offset'])
 parts=plan['segments']
 if parts[0]['at']!=0 or parts[-1]['until']!=1:raise ValueError('COMPOUND_COVERAGE')
 for x,y in zip(parts,parts[1:]):
  if x['until']!=y['at'] or length(sub(position(x['plan'],1),position(y['plan'],0)))>1e-8:raise ValueError('COMPOUND_DISCONTINUITY')
 for seg in parts:
  if seg['at']<=u<=seg['until']:return position(seg['plan'],(u-seg['at'])/(seg['until']-seg['at']))
 raise ValueError('COMPOUND_GAP')
def aim(plan,u):
 if 'aim_waypoints' in plan:
  nodes=plan['aim_waypoints']
  if len(nodes)<2 or nodes[0][0]!=0 or nodes[-1][0]!=1 or any(b[0]<=a[0] for a,b in zip(nodes,nodes[1:])):raise ValueError('AIM_WAYPOINT_ORDER')
  if any(len(p)!=3 or not all(math.isfinite(x) for x in p) for _,p in nodes):raise ValueError('AIM_WAYPOINT_VALUE')
  t=max(0.,min(1.,u))
  for a,b in zip(nodes,nodes[1:]):
   if a[0]<=t<=b[0]:return mix(a[1],b[1],(t-a[0])/(b[0]-a[0]))
 return mix(plan['aim_start'],plan.get('aim_end',plan['aim_start']),progress(u,plan.get('aim_curve',plan.get('curve','LINEAR')),plan.get('aim_beats',plan.get('beats'))))
def diagnose(points,fps,quaternions=None,tolerance=1e-4):
 if len(points)<2 or fps<=0:raise ValueError('SAMPLES_AND_TIMEBASE_REQUIRED')
 chord=sub(points[-1],points[0]);den=dot(chord,chord);dist=math.sqrt(den)
 dev=[length(sub(sub(p,points[0]),mul(chord,dot(sub(p,points[0]),chord)/den))) if den>1e-20 else length(sub(p,points[0])) for p in points]
 delta=[sub(b,a) for a,b in zip(points,points[1:])];speeds=[length(d)*fps for d in delta]
 acc=[length(sub(b,a))*fps*fps for a,b in zip(delta,delta[1:])]
 curvature=[]
 for a,b in zip(delta,delta[1:]):
  la,lb=length(a),length(b)
  curvature.append(math.acos(max(-1,min(1,dot(a,b)/la/lb)))/((la+lb)/2) if min(la,lb)>1e-8 else None)
 angles=[]
 if quaternions:
  for a,b in zip(quaternions,quaternions[1:]):
   angles.append(math.degrees(2*math.acos(min(1,abs(dot(a,b)/length(a)/length(b)))))*fps)
 return {'endpoint_distance':dist,'path_length':sum(speeds)/fps,'path_ratio':sum(speeds)/fps/dist if dist>1e-8 else None,'max_line_deviation':max(dev),'deviation':dev,'speed':speeds,'acceleration':acc,'curvature':curvature,'angular_speed_deg_s':angles,'straight_within_tolerance':max(dev)<=tolerance,'tolerance':tolerance,'backtracking_steps':sum(dot(d,chord)<-tolerance for d in delta),'stationary':max(length(sub(p,points[0])) for p in points)<=tolerance}
