"""CSP opt-in perceptual prerequisites; not artistic quality or collision simulation."""
import copy,math
from prop_control import event_list
PHASES=('APPROACHING','CONTACT_PENDING','CONTACT_ESTABLISHED','TRANSFER_ACTIVE','RESULT_VISIBLE','RECOVERY')
DEFAULTS={'actor_height':.12,'prop_height':.06,'contact_height':.003,'visible_fraction':.8,'ray_visibility':.5,'consecutive_frames':6,'result_displacement':.015,'direction_cosine':.5,'source':'TECHNICAL_DEFAULT 480x270 30fps proxy readability; not universal perception'}
def structural_errors(p,c):
 errors=[];events={e['event_id']:e for e in event_list(p)}
 if c.get('outcome') not in ('CONTROLLED','FAILED'):errors.append('INVALID_OUTCOME')
 cause=events.get(c.get('cause_ref'));result=events.get(c.get('result_ref'))
 if not cause or not result or cause['actor']!=c.get('actor') or result['actor']!=c.get('actor') or cause['prop_id']!=c.get('prop') or result['prop_id']!=c.get('prop'):errors.append('RESPONSE_WITHOUT_VISIBLE_CAUSE')
 elif c.get('outcome')=='CONTROLLED' and (cause['kind']!='CONTACT' or result['kind'] not in ('ACQUIRE','TRANSFER') or result.get('contact_ref')!=c['cause_ref']):errors.append('RESPONSE_WITHOUT_VISIBLE_CAUSE')
 elif c.get('outcome')=='FAILED' and result['kind']!='FAIL':errors.append('CAUSE_WITHOUT_RESULT')
 phases=c.get('phases',{});last=0;n=p['timebase']['frames']
 for name in PHASES:
  ph=phases.get(name)
  if not ph:errors.append('CONTACT_PHASE_SKIPPED');continue
  if ph.get('status')=='NA':
   if not ph.get('reason') or name in ('APPROACHING','CONTACT_PENDING','RESULT_VISIBLE') or (name=='CONTACT_ESTABLISHED' and c.get('outcome')=='CONTROLLED'):errors.append('CONTACT_PHASE_SKIPPED')
   continue
  w=ph.get('frames',[])
  if len(w)!=2 or not all(isinstance(f,int) for f in w) or not 1<=w[0]<=w[1]<=n or w[0]<=last:errors.append('CONTACT_PHASE_SKIPPED')
  else:last=w[1]
 for key in ('cause_window','result_window'):
  w=c.get(key,[])
  if len(w)!=2 or not all(isinstance(x,int) for x in w) or not 1<=w[0]<w[1]<=n:errors.append('CONTACT_PHASE_SKIPPED')
 if not errors:
  if c['result_window'][0]<result['frame'] or c['cause_window'][0]>cause['frame'] or c['cause_window'][1]<cause['frame'] or c['cause_window'][0]>c['result_window'][0]:errors.append('RESPONSE_WITHOUT_VISIBLE_CAUSE')
 if not c.get('provenance') or not c.get('expected_response_direction'):errors.append('MISSING_AUTHORED_CONTRACT')
 if c.get('receiver') not in p.get('object_tracks',{}) or c.get('prop') not in p.get('object_tracks',{}):errors.append('MISSING_SUBJECT')
 return sorted(set(errors))
def attach(p,c):
 e=structural_errors(p,c)
 if e:raise ValueError(e)
 q=copy.deepcopy(p)
 from timebase import frame_to_time
 fps=p['timebase']['fps'];first=min(ph['frames'][0] for ph in c['phases'].values() if ph.get('frames'));last=max(ph['frames'][1] for ph in c['phases'].values() if ph.get('frames'))
 q['action_beats'].append({'event_id':c['id'],'type':'CONTACT_READABILITY','interval_s':[frame_to_time(first,fps),frame_to_time(last,fps)],'phases':{k:{'status':'NA','reason':'Observation contract, not new action'} for k in ('PREPARE','COMPRESS','ACCELERATE','PEAK','CONTACT','FOLLOW_THROUGH','RECOVERY')},'breakdowns':[{'time_s':frame_to_time(first,fps),'role':'READABILITY_CONTRACT'}],'contact_readability':copy.deepcopy(c)})
 for r in q['object_tracks'][c['prop']]:
  active=next((name for name,ph in c['phases'].items() if ph.get('frames') and ph['frames'][0]<=r['frame']<=ph['frames'][1]),None)
  if active:r['state'].setdefault('contact_readability_state',{})[c['id']]=active
 return q
def longest(flags):
 best=run=0
 for x in flags:run=run+1 if x else 0;best=max(best,run)
 return best
def evaluate(p,c,trace=None):
 errors=structural_errors(p,c)
 if errors:return {'status':'FAIL','errors':errors,'basis':'CONTRACT_STRUCTURE'}
 if trace is None:return {'status':'NOT_REVIEWED','errors':[],'reason':'Native camera/geometry trace required'}
 t=c.get('thresholds',DEFAULTS);rows={int(r['frame']):r for r in trace};a,b=c['cause_window'];u,v=c['result_window'];required=set(range(a,b+1))|set(range(u,v+1))
 for ph in c['phases'].values():
  if ph.get('frames'):required.update(range(ph['frames'][0],ph['frames'][1]+1))
 if not required.issubset(rows):return {'status':'NOT_REVIEWED','errors':[],'reason':'Incomplete evidence window'}
 if c['outcome']=='CONTROLLED':
  cf=next(e['frame'] for e in event_list(p) if e['event_id']==c['cause_ref']);e=rows.get(cf,{})
  if e.get('contact_gap') is None or e.get('contact_radius') is None:return {'status':'NOT_REVIEWED','errors':[],'reason':'Missing native contact geometry'}
  if e['contact_gap']>e['contact_radius']:errors.append('RESPONSE_WITHOUT_VISIBLE_CAUSE')
 def visible(row,key,height):
  m=row.get(key)
  if not m:return None
  if m.get('projection_state') in ('OUT_OF_FRAME','BEHIND_OR_DEPTH_CLIPPED') or m.get('clipped_bounds') is None:return False
  if m.get('occlusion_ratio') is None:return None
  return m['clipped_bounds'] is not None and m['visible_fraction_estimate']>=t['visible_fraction'] and m['screen_height_ratio']>=height and 1-m['occlusion_ratio']>=t['ray_visibility']
 cause_flags=[];result_flags=[]
 for f in range(a,b+1):
  checks=[visible(rows[f],k,h) for k,h in (('actor',t['actor_height']),('prop',t['prop_height']),('contact',t['contact_height']))]
  if None in checks:return {'status':'NOT_REVIEWED','errors':[],'reason':'Missing camera/ray evidence'}
  cause_flags.append(all(checks))
 for f in range(u,v+1):
  checks=[visible(rows[f],k,h) for k,h in (('actor',t['actor_height']),('prop',t['prop_height']))]
  if None in checks:return {'status':'NOT_REVIEWED','errors':[],'reason':'Missing camera/ray evidence'}
  result_flags.append(all(checks))
 visible_cause=longest(cause_flags)>=t['consecutive_frames'];visible_result=longest(result_flags)>=t['consecutive_frames']
 if not visible_cause:errors+=['CONTACT_NOT_VISIBLE','RESPONSE_WITHOUT_VISIBLE_CAUSE']
 phase_runs={}
 for name,ph in c['phases'].items():
  if not ph.get('frames'):continue
  first,last=ph['frames'];flags=[]
  for f in range(first,last+1):
   checks=[visible(rows[f],k,h) for k,h in (('actor',t['actor_height']),('prop',t['prop_height']))]
   if None in checks:return {'status':'NOT_REVIEWED','errors':sorted(set(errors)),'reason':'Incomplete phase visibility'}
   flags.append(all(checks))
  phase_runs[name]=longest(flags)
  if phase_runs[name]<min(t['consecutive_frames'],last-first+1):errors.append('CONTACT_NOT_VISIBLE' if name in PHASES[:3] else 'CAUSE_WITHOUT_RESULT')
 centers=[rows[f]['receiver_screen'] for f,ok in zip(range(u,v+1),result_flags) if ok and rows[f].get('receiver_screen') is not None]
 disp=max((math.dist(x,y) for x in centers for y in centers),default=0.)
 if not visible_result or disp<t['result_displacement']:errors.append('CAUSE_WITHOUT_RESULT')
 world=[rows[v]['receiver_world'][i]-rows[u]['receiver_world'][i] for i in range(3)];desired=c['expected_response_direction'];norm=lambda x:math.sqrt(sum(v*v for v in x));cos=sum(x*y for x,y in zip(world,desired))/(norm(world)*norm(desired)) if norm(world)*norm(desired)>1e-9 else None
 if cos is None or cos<t['direction_cosine']:errors.append('WRONG_CONTACT_DIRECTION')
 controls=[rows[f].get('controller') for f in range(u,v+1)]
 if any(x is None for x in controls):return {'status':'NOT_REVIEWED','errors':sorted(set(errors)),'reason':'Missing native control evidence'}
 expected=c['actor'] if c['outcome']=='CONTROLLED' else ''
 if any(x!=expected for x in controls):errors.append('CAUSE_WITHOUT_RESULT')
 return {'status':'FAIL' if errors else 'PASS','errors':sorted(set(errors)),'measurements':{'visible_cause_run':longest(cause_flags),'visible_result_run':longest(result_flags),'phase_visible_runs':phase_runs,'screen_displacement':disp,'world_direction_cosine':cos,'cause_failed_frames':[f for f,x in zip(range(a,b+1),cause_flags) if not x]},'thresholds':t,'evidence':'NATIVE_EVALUATED_GEOMETRY_AND_CAMERA_RAYS_ESTIMATED','scope':'Measurable visual prerequisites only; not human recognition or director approval'}
