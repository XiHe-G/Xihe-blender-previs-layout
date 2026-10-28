"""Calibration-only data governance. Never selects or repairs a camera."""
import copy,math
FACTORS=('scale','relation','occlusion','body','witness','exposure')
def changed_factors(anchor,variant):return [k for k in FACTORS if anchor[k]!=variant[k]]
def resolve_direction(momentum=None,positions=None):
 if momentum and momentum.get('response_velocity_target'):
  v=momentum['response_velocity_target'];source='ACCEPTED_MOMENTUM_RESPONSE_TARGET'
 elif positions and len(positions)==2:
  v=[b-a for a,b in zip(*positions)];source='ACCEPTED_CSP_EXECUTION_PATH_TANGENT_NOT_FORCE'
 else:return {'status':'NOT_REVIEWED','reason':'No trusted direction source'}
 if len(v)!=3 or any(not math.isfinite(x) for x in v) or sum(x*x for x in v)<1e-12:return {'status':'NOT_REVIEWED','reason':'No reliable nonzero direction'}
 return {'status':'RESOLVED','value':v,'source':source}
def calibration_diagnostics(spec,mechanical,extra):
 out=[]
 if spec['witness']=='POINT_ONLY':out+=['BODY_CONTACT_DISCONNECTED','CONTACT_WITNESS_TOO_ABSTRACT']
 if extra.get('axis_projection_ratio',1)<.25:out.append('VIEW_CONFLICTS_WITH_FORCE_AXIS')
 if extra.get('cause_result_gap_frames',0)>30:out.append('CAUSE_RESULT_SEPARATION_TOO_LARGE')
 if spec['body']=='BODY_CONFLICTING_WITH_FORCE':out.append('BODY_CONTACT_DISCONNECTED')
 return {'status':'EXPERIMENTAL_DIAGNOSTICS_ONLY','diagnostics':sorted(set(out)),'mechanical_status':mechanical['status'],'human_review':'PENDING_HUMAN_REVIEW','not_global_gates':True}
def envelope(rows):
 good=[r for r in rows if r['mechanical_status']=='PASS' and r['direction_status']=='RESOLVED']
 return {'status':'MECHANICALLY_READABLE_CANDIDATE' if good else 'INSUFFICIENT_EVIDENCE','scope':'Only sampled configurations, proxy geometry, resolution and fps; no interpolation or human claim','variants':[r['id'] for r in good],'human_review_status':'PENDING_HUMAN_REVIEW','threshold_changes':False,'basis':'Unchanged S006 mechanical validator; candidate conditions are not a classifier of human understanding'}
def review_template(ids):return {'status':'PENDING_HUMAN_REVIEW','reviewer':None,'independent':None,'answers':[{'variant':i,'R1':None,'R2':None,'R3':None,'R4':None,'R5':None,'interpretation':None,'note':''} for i in ids]}
def validate_review(r):
 if not r.get('reviewer') or r.get('independent') is not True:return {'status':'PENDING_HUMAN_REVIEW'}
 if not r.get('answers'):return {'status':'PENDING_HUMAN_REVIEW'}
 for row in r.get('answers',[]):
  if any(row.get(k) not in ('PASS','FAIL','UNCERTAIN') for k in ('R1','R2','R3','R4','R5')):return {'status':'PENDING_HUMAN_REVIEW'}
 return {'status':'RECORDED_HUMAN_REVIEW','automatic_promotion':False}
