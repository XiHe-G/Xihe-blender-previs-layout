"""Opt-in director speed/phase compilation using unchanged S51 kernels. No bpy."""
import copy, math, bisect
from timebase import frame_to_time
from primitive_sampler import norm,sub,add,mul,unit,dot,yaw_quat
from primitive_runtime import compile_primitive

CLASSES=('SLOW','WALK','FAST_WALK','RUN','SPRINT','BURST')
TRENDS=('APPROACH','CHASE','RETREAT','LUNGE','DODGE','PULL','PUSH','TURN_AND_GO','STOP_AND_REACT','RECOVER','HARD_STOP')
PHASES=('PREPARE','ACCELERATE','CRUISE','BURST','DECELERATE','STOP','RECOVER')
RELATIVE_DEFAULTS={'speed_ratio':1.2,'gain_ratio':1.5,'hard_stop_ratio':1.5,'direction_cosine':.5,'source':'TECHNICAL_DEFAULT relative scene-scale comparisons, not human/physical norms'}

def compile_profile(spec,timebase):
    """Phase knots carry authored frames/speeds; same global timebase as CSP."""
    s=copy.deepcopy(spec);knots=s['knots'];fps=timebase['fps']
    if s['intensity_class'] not in CLASSES or s['trend'] not in TRENDS:raise ValueError('UNKNOWN_INTENSITY_OR_TREND')
    if len(knots)<2 or not s.get('provenance'):raise ValueError('MISSING_PROFILE_EVIDENCE')
    if any(not math.isfinite(k['speed']) or k['speed']<0 or not isinstance(k['frame'],int) for k in knots):raise ValueError('INVALID_SPEED_KNOT')
    if any(b['frame']-a['frame']<2 for a,b in zip(knots,knots[1:])):raise ValueError('INVALID_PHASE_WINDOW')
    if norm(s['direction'])<1e-8:raise ValueError('MISSING_MOVEMENT_DIRECTION')
    direction=unit(s['direction']);pos=list(s['start_position']);frags=[];prims=[];rows=[];phase_rows=[]
    orientation=yaw_quat(math.radians(s.get('facing_yaw',-90)))
    for i,(a,b) in enumerate(zip(knots,knots[1:])):
        phase=b['phase'];T=frame_to_time(b['frame'],fps)-frame_to_time(a['frame'],fps)
        if phase not in PHASES:raise ValueError('UNKNOWN_MOTION_PHASE')
        v0=mul(direction,a['speed']);v1=mul(direction,b['speed']);distance=(a['speed']+b['speed'])*T/2
        q={'primitive_version':'EXECUTION-PRIMITIVE/1.0','primitive_id':'PRIM_'+s['id']+'_'+str(i),'primitive_type':'RECOVERY_PROFILE','actor':s['actor'],'subjects':[],
           'start_time':frame_to_time(a['frame'],fps),'end_time':frame_to_time(b['frame'],fps),
           'entry_state':{'position':pos,'velocity':v0,'movement_direction':direction,'orientation':orientation,'angular_velocity':0,'ownership_state':'FREE','support_state':'DECLARED_CSP_SUPPORT'},
           'parameters':{'entry_velocity':v0,'exit_velocity':v1,'duration':T,'displacement_limit':distance+1e-6,'direction_retention':1},
           'exit_requirements':{'velocity':v1},'continuity_contract':{'C0_REQUIRED':True,'C1_REQUIREMENT':'REQUIRED','C2_POLICY':'RECORD'},
           'provenance':{'source':s['provenance'],'boundary_semantics':'AUTHORED_ENVELOPE/1.0','phase':phase,'not_physics':True}}
        f,d=compile_primitive(q,timebase)
        if any(f['continuity_report']['dimensions'][k]!='PASS' for k in ('C0','C1')):raise ValueError('INTENSITY_BOUNDARY_FAIL '+str(d))
        prims.append(q);frags.append(f);rows.extend(f['world_samples'][bool(rows):]);pos=f['exit_state_actual']['position'];phase_rows.append({'phase':phase,'first_frame':a['frame'],'last_frame':b['frame'],'entry_speed':a['speed'],'exit_speed':b['speed'],'displacement':distance})
    return {'spec':s,'primitives':prims,'bundle':{'fragments':frags,'composition':[{'type':'SEQUENTIAL','members':[a['primitive_id'],b['primitive_id']]} for a,b in zip(prims,prims[1:])]},'rows':rows,'profile':{'intensity_class':s['intensity_class'],'entry_speed':knots[0]['speed'],'target_speed':max(k['speed'] for k in knots),'exit_speed':knots[-1]['speed'],'phases':phase_rows,'total_displacement':sum(p['displacement'] for p in phase_rows),'durations':{p:sum((r['last_frame']-r['first_frame'])/fps for r in phase_rows if r['phase']==p) for p in PHASES},'source':s['provenance'],'body_trend':s.get('body_trend',{})}}

def apply_body_trend(csp,compiled):
    """Existing body pitch/roll pose fields only. No limb/rig changes."""
    p=copy.deepcopy(csp);s=compiled['spec'];trend=s.get('body_trend',{});peak=compiled['profile']['target_speed'];samples={r['frame']:r for r in compiled['rows']}
    for row in p['actor_pose_tracks'][s['actor']]:
        f=row['frame'];r=samples.get(f)
        if r:
            strength=norm(r['velocity'])/peak if peak else 0
            row['state']['body_pitch']=trend.get('forward_lean_deg',0)*strength
            row['state']['body_roll']=trend.get('lateral_lean_deg',0)*strength
            row['state']['yaw']=s.get('facing_yaw',-90)
            row['state']['motion_intensity']={'profile':s['id'],'class':s['intensity_class'],'trend':s['trend'],'phase':next(x['phase'] for x in compiled['profile']['phases'] if x['first_frame']<=f<=x['last_frame'])}
    return p

def measure(rows,fps):
    if len(rows)<4:return {'status':'NOT_REVIEWED','reason':'INSUFFICIENT_SAMPLES'}
    velocities=[mul(sub(b['position'],a['position']),fps/(b['frame']-a['frame'])) for a,b in zip(rows,rows[1:])]
    speeds=[norm(v) for v in velocities];acc=[(b-a)*fps for a,b in zip(speeds,speeds[1:])]
    screen=[norm(sub(b['screen'],a['screen']))*fps/(b['frame']-a['frame']) for a,b in zip(rows,rows[1:]) if a.get('screen') is not None and b.get('screen') is not None]
    return {'status':'OBSERVED','peak_speed':max(speeds),'mean_speed':sum(speeds)/len(speeds),'entry_speed':speeds[0],'exit_speed':speeds[-1],'max_acceleration':max(acc),'max_deceleration':-min(acc),'peak_screen_speed':max(screen) if screen else None,'speeds':speeds,'frames':[r['frame'] for r in rows[1:]],'screen_speeds':screen,'path_length':sum(norm(sub(b['position'],a['position'])) for a,b in zip(rows,rows[1:]))}

def validate_profile(compiled,rows,fps,reference=None):
    s=compiled['spec'];m=measure(rows,fps);errors=[];missing=[]
    if s['trend'] not in ('APPROACH','CHASE','LUNGE','DODGE','RETREAT','HARD_STOP'):missing.append('TREND_DIAGNOSTIC_NOT_IMPLEMENTED')
    if m['status']=='NOT_REVIEWED':return {'status':'NOT_REVIEWED','errors':[],'measurements':m}
    for p in compiled['profile']['phases']:
        rr=[r for r in rows if p['first_frame']<=r['frame']<=p['last_frame']]
        mm=measure(rr,fps)
        if mm['status']=='NOT_REVIEWED':missing.append(p['phase']);continue
        speeds=mm['speeds'];k=max(1,len(speeds)//5);early=sum(speeds[:k])/k;late=sum(speeds[-k:])/k
        if p['phase'] in ('ACCELERATE','BURST') and p['exit_speed']>p['entry_speed']:
            code='BURST_WITHOUT_SPEED_GAIN' if p['phase']=='BURST' else 'ACCELERATION_NOT_VISIBLE'
            if late<=early*RELATIVE_DEFAULTS['gain_ratio']+1e-6:errors.append(code)
            ss=mm['screen_speeds']
            if not ss:missing.append('SCREEN_ACCELERATION')
            elif sum(ss[-k:])<=sum(ss[:k])*RELATIVE_DEFAULTS['gain_ratio']:errors.append('ACCELERATION_NOT_VISIBLE')
        if p['phase']=='DECELERATE' and p['exit_speed']<p['entry_speed'] and early<=late*RELATIVE_DEFAULTS['gain_ratio']+1e-6:errors.append('DECELERATION_NOT_VISIBLE')
    moving=[(a,b) for a,b in zip(rows,rows[1:]) if norm(sub(b['position'],a['position']))>1e-5]
    dots=[dot(unit(sub(b['position'],a['position'])),unit(a['forward'])) for a,b in moving if 'forward' in a]
    if not dots:missing.append('FACING_EVIDENCE')
    elif s['trend'] in ('APPROACH','CHASE','LUNGE','PUSH') and min(dots)<RELATIVE_DEFAULTS['direction_cosine']:errors.append('ACTION_TREND_MISMATCH')
    elif s['trend']=='RETREAT' and max(dots)>-RELATIVE_DEFAULTS['direction_cosine']:errors.append('ACTION_TREND_MISMATCH')
    elif s['trend']=='DODGE' and max(abs(d) for d in dots)>.5:errors.append('ACTION_TREND_MISMATCH')
    if s['trend'] in ('APPROACH','CHASE','LUNGE'):
        if not all('target' in r for r in rows):missing.append('TARGET_RELATION')
        elif norm(sub(rows[-1]['position'],rows[-1]['target']))>=norm(sub(rows[0]['position'],rows[0]['target'])):errors.append('ACTION_TREND_MISMATCH')
    if s['trend']=='HARD_STOP':
        if reference is None:missing.append('NORMAL_STOP_REFERENCE')
        elif m['max_deceleration']<reference['max_deceleration']*RELATIVE_DEFAULTS['hard_stop_ratio']:errors.append('HARD_STOP_TOO_SOFT')
    return {'status':'FAIL' if errors else 'NOT_REVIEWED' if missing else 'PASS','errors':sorted(set(errors)),'missing':missing,'measurements':m,'thresholds':RELATIVE_DEFAULTS,'scope':'Mechanical trend only; human/director readability PENDING'}

def validate_ladder(measurements,order=CLASSES):
    errors=[]
    for a,b in zip(order,order[1:]):
        if a not in measurements or b not in measurements:return {'status':'NOT_REVIEWED','errors':['MISSING_CLASS']}
        if measurements[b]['peak_speed']<measurements[a]['peak_speed']*RELATIVE_DEFAULTS['speed_ratio']:errors.append({'code':'SPEED_CLASS_NOT_SEPARATED','pair':[a,b]})
    return {'status':'FAIL' if errors else 'PASS','errors':errors,'thresholds':RELATIVE_DEFAULTS}

def redistribute_path(csp,spec,locked=()):
    """Explicit opt-in dense CSP spacing edit; actor group only, contact endpoints protected.
    Reuses RECOVERY_PROFILE for scalar arc progress; preserves route and all state metadata.
    Caller supplies allowed objects/windows and must replay native support/control validation.
    """
    if locked:raise ValueError('BLOCKED_BY_OVERRIDE')
    p=copy.deepcopy(csp);root=spec['root'];first,last=spec['window'];fps=p['timebase']['fps'];names=spec['objects']
    if root not in names or any(x['camera_id'] in names for x in p['shot_plan']):raise ValueError('INVALID_ACTOR_SCOPE')
    old=csp['object_tracks'][root];points=[r['state']['location'] for r in old[first-1:last]];lengths=[0.]
    for a,b in zip(points,points[1:]):lengths.append(lengths[-1]+norm(sub(b,a)))
    if lengths[-1]<1e-8:raise ValueError('NO_ROUTE')
    v0=norm(sub(points[1],points[0]))*fps;v1=norm(sub(points[-1],points[-2]))*fps
    frames=spec['phase_frames'];low=spec['prepare_speed']
    if frames[0]!=first or frames[-1]!=last or len(frames)!=5:raise ValueError('INVALID_PHASE_PLAN')
    durations=[(b-a)/fps for a,b in zip(frames,frames[1:])]
    t0,t1,t2,t3=durations;peak=(lengths[-1]-(v0+low)*t0/2-low*t1/2-v1*t3/2)/(t1/2+t2+t3/2)
    if peak<=max(v0,v1,low):raise ValueError('INFEASIBLE_SPEED_BUDGET')
    profile={'id':spec['id'],'actor':root,'intensity_class':spec['intensity_class'],'trend':spec['trend'],'start_position':[0,0,0],'direction':[1,0,0],'knots':[{'frame':f,'speed':v,'phase':phase} for f,v,phase in zip(frames,[v0,low,peak,peak,v1],['PREPARE','PREPARE','BURST','CRUISE','DECELERATE'])],'provenance':'DIRECTOR_AUTHORED phase allocation; peak DERIVED_FROM_ROUTE_AND_FIXED_TIMING'}
    result=compile_profile(profile,{'fps':fps,'duration':p['timebase']['frames']/fps,'frame_origin':1,'time_unit':'seconds'})
    for r in result['rows']:
        f=r['frame'];distance=r['position'][0]
        i=min(len(lengths)-2,max(0,bisect.bisect_right(lengths,distance)-1));u=(distance-lengths[i])/(lengths[i+1]-lengths[i]) if lengths[i+1]>lengths[i] else 0;u=max(0,min(1,u))
        for obj in names:
            st=p['object_tracks'][obj][f-1]['state'];a=csp['object_tracks'][obj][first-1+i]['state'];b=csp['object_tracks'][obj][first+i]['state']
            if st.get('motion_consequence'):raise ValueError('PROTECTED_MOMENTUM_WINDOW')
            st['location']=[x+(y-x)*u for x,y in zip(a['location'],b['location'])]
        # Preserve exact endpoints (no floating-point edit to contact bridge).
        if f in (first,last):
            for obj in names:p['object_tracks'][obj][f-1]['state']['location']=copy.deepcopy(csp['object_tracks'][obj][f-1]['state']['location'])
    result['mapping']={'route_length':lengths[-1],'peak_derived':peak,'objects':names,'window':[first,last],'only_modified_field':'location','state_metadata_unchanged':True,'rotation_unchanged':True}
    return p,result

def validate_spacing_boundary(rows,window,fps,subject,authored_envelope=False):
    """Reuse S53R zero-speed semantics, keep raw S45 dimensions and C2 evidence."""
    from motion_boundary_validator import validate_boundary
    lo,hi=window;index={r['frame']:r for r in rows};selected=[]
    for f in range(lo,hi+1):
        r=dict(index[f]);r['velocity']=mul(sub(index[f]['position'],index[f-1]['position']),fps);selected.append(r)
    semantic={'rows':selected,'primitive':{'primitive_type':'MOVE_PROFILE','parameters':{}}} if authored_envelope else None
    report=validate_boundary(rows,window,fps,'CHARACTER_ROOT_CONTINUITY_PROFILE',subject,interpolation_evidence={'kind':'AUTHORED_CONTINUOUS_PIECEWISE_LINEAR'},boundary_semantic=semantic)
    report['semantic_source']='EXPLICIT_S008_PROFILE_REUSING_S53R_AUTHORED_ENVELOPE' if semantic else 'STRICT_CONTINUOUS'
    return report


