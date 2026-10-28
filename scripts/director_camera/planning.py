"""Semantic lowering and finite candidate planning; no free-text fiction generator."""
import math
from .motion import sub,length,mul,add
MOVES={'固定':'STATIC_HOLD','上摇':'STATIC_ROTATION','横摇':'STATIC_ROTATION','横移':'STRAIGHT_TRANSLATION','缓推':'STRAIGHT_TRANSLATION','拉升':'VERTICAL_CRANE','缓升':'VERTICAL_CRANE','缓降':'VERTICAL_CRANE','跟拍':'STRAIGHT_TRACKING','环绕':'ORBIT'}
def shot_card(source,interpretation):
 required=['purpose','first_focus','subject','space_gaze','beats','camera_reason','follow_or_hold','start_end','cut_reason','proxy_split']
 missing=[x for x in required if not interpretation.get(x)]
 if missing:raise ValueError('MISSING_DIRECTOR_BINDINGS:'+','.join(missing))
 return {'source':source,'interpretation':interpretation,'authority':{'LOCKED':source.get('locked',{}),'GUIDED':source.get('guided',{}),'OPTIONAL':interpretation.get('optional',{})},'status':'PLAN_NOT_ART_ACCEPTANCE'}
def lower_move(move,fixed_position_tilt=False):
 if fixed_position_tilt:return 'STATIC_ROTATION'
 if move not in MOVES:raise ValueError('UNRESOLVED_CAMERA_SEMANTICS:'+move)
 return MOVES[move]
def fit_camera(target,subject_height,frame_height_fraction,lens=50,sensor_width=36,aspect=16/9,view_direction=(0,-1,0),elevation=0):
 if subject_height<=0 or not 0<frame_height_fraction<=1 or lens<=0:raise ValueError('INVALID_FRAMING')
 d=subject_height*lens*aspect/(sensor_width*frame_height_fraction)
 n=length(view_direction)
 if n<1e-9:raise ValueError('INVALID_VIEW_DIRECTION')
 p=add(target,mul(view_direction,d/n));return (p[0],p[1],p[2]+elevation)
def bounded_candidates(base,attempts,issues,max_rounds=4):
 if attempts>=max_rounds:return {'status':'HUMAN_REVIEW_BUDGET_REACHED','candidates':[]}
 if any(x.get('locked_conflict') for x in issues):return {'status':'LOCKED_CONSTRAINT_REVIEW','candidates':[]}
 options=[]
 for x in issues:
  if x['code']=='UNINTENDED_CURVE' and base['kind'].startswith('STRAIGHT'):options.append({'operation':'rebuild_scalar_progress','plan':base,'reason':x})
  elif x['code']=='FRAME_EDGE' and 'framing' not in base.get('locked',[]):options.append({'operation':'reframe_candidate','fraction_scale':.9,'reason':x})
 return {'status':'CANDIDATES' if options else 'NOT_REVIEWED','candidates':options[:2]}
def axis_side(camera,first_subject,second_subject,epsilon=1e-6):
 """Signed horizontal axis evidence; crossing is not an automatic directing error."""
 a=sub(second_subject,first_subject);b=sub(camera,first_subject);cross=a[0]*b[1]-a[1]*b[0]
 if abs(cross)<=epsilon:return 'ON_AXIS'
 return 'LEFT' if cross>0 else 'RIGHT'
def continuity_review(previous,current,explicit_exceptions=()):
 if previous['shot'] in explicit_exceptions or current['shot'] in explicit_exceptions:return {'status':'INTENTIONAL_TRANSITION_REVIEW','automatic_repair':False}
 if previous.get('axis_pair')!=current.get('axis_pair'):return {'status':'AXIS_BINDING_REQUIRED','automatic_repair':False}
 sides=(previous.get('side'),current.get('side'))
 return {'status':'CROSSING_REVIEW' if set(sides)=={'LEFT','RIGHT'} else 'SAME_SIDE_MEASURED','automatic_repair':False,'artistic_acceptance':'NOT_REVIEWED'}
