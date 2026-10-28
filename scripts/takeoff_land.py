"""Opt-in CSP air-chain composition of existing intensity/recovery primitives. No bpy."""
import copy, math, bisect
from primitive_sampler import norm, sub, mul, add
from motion_intensity import compile_profile
from momentum_transfer import recovery_segment
from support_contact import compile_support
from timebase import frame_to_time

LIMITS={'source':'TECHNICAL_DEFAULT; existing support tolerance and scene-relative motion checks',
        'contact_tolerance':.015,'target_tolerance':.015,'velocity_tolerance':.02,'minimum_response_samples':8}

def compression_at(height,cal):
    rows=cal['rows'];hs=[r['com_height'] for r in rows]
    if height<hs[0]-1e-5 or height>hs[-1]+1e-5:raise ValueError('COMPRESSION_ENVELOPE_INFEASIBLE')
    i=max(0,min(len(rows)-2,bisect.bisect_right(hs,height)-1));u=max(0,min(1,(height-hs[i])/(hs[i+1]-hs[i])))
    return rows[i]['compression']+(rows[i+1]['compression']-rows[i]['compression'])*u

def compile_air(spec,cal):
    s=copy.deepcopy(spec);n=s['frames'];fps=s['fps'];t=s['timing'];drop=s['mode']=='DROP'
    if s['mode'] not in ('JUMP','DROP'):raise ValueError('UNSUPPORTED_AIR_MODE')
    if not s.get('provenance') or not s.get('land_surface'):raise ValueError('LAND_SURFACE_UNRESOLVED')
    if s.get('locked'):raise ValueError('BLOCKED_BY_OVERRIDE')
    required=['approach_end','load_start','release','land','absorb_end','recover_end']+([] if drop else ['push_start','apex'])
    if any(not isinstance(t[k],int) or not 1<t[k]<n for k in required):raise ValueError('INVALID_GLOBAL_FRAME')
    seq=[1,t['approach_end'],t['load_start']]+([] if drop else [t['push_start']])+[t['release']]+([] if drop else [t['apex']])+[t['land'],t['absorb_end'],t['recover_end'],n]
    if any(b<a for a,b in zip(seq,seq[1:])):raise ValueError('TIME_ORDER_COLLISION')
    h0=cal['rows'][-1]['com_height'];ground=s['start_point'][2];landz=s['land_surface']['height']
    if not drop and abs(ground-landz)>1e-7:raise ValueError('UNEQUAL_LEVEL_JUMP_NOT_IMPLEMENTED')
    if drop and ground<=landz:raise ValueError('DROP_REQUIRES_LOWER_SURFACE')
    tb={'fps':fps,'duration':n/fps,'time_unit':'seconds','frame_origin':1}
    profile=copy.deepcopy(s['intensity_profile']);profile['actor']=s['actor'];profile['start_position']=add(s['start_point'],[0,0,h0])
    initial=compile_profile(profile,tb)
    if initial['rows'][-1]['frame']!=t['approach_end']:raise ValueError('INTENSITY_ENTRY_TIME_CONFLICT')
    rows=list(initial['rows']);frags=list(initial['bundle']['fragments']);prims=list(initial['primitives']);phase_ranges=[]
    pos=rows[-1]['position'];vel=rows[-1]['velocity'];horizontal=vel[:2]+[0]
    if abs(vel[2])>1e-7:raise ValueError('GROUND_ENTRY_VERTICAL_CONFLICT')
    p={'timebase':{'fps':fps,'frames':n}}
    def seg(label,end,v):
        nonlocal pos,vel
        first=rows[-1]['frame']
        if end==first:return
        if end-first<2:raise ValueError('INSUFFICIENT_PHASE_SAMPLES')
        q,f,d=recovery_segment(p,s['id']+'_'+label,s['actor'],first,end,pos,vel,v)
        prims.append(q);frags.append(f);rows.extend(f['world_samples'][1:]);phase_ranges.append({'phase':label,'first_frame':first,'end_frame':end,'entry_velocity':vel,'exit_velocity':v,'source':'S005 recovery_segment -> unchanged S51 RECOVERY_PROFILE'})
        pos=f['exit_state_actual']['position'];vel=v
    seg('GROUND_APPROACH',t['load_start'],horizontal)
    if drop:
        seg('EDGE_EXIT',t['release'],horizontal)
        vd=-2*(ground-landz)/((t['land']-t['release'])/fps)
    else:
        vu=2*s['apex_height']/((t['apex']-t['release'])/fps)
        vd=-2*s['apex_height']/((t['land']-t['apex'])/fps)
        loading=vu*(t['release']-t['push_start'])/fps/2
        mid=(t['load_start']+t['push_start'])//2
        down=-2*loading/((t['push_start']-t['load_start'])/fps)
        seg('LOAD',mid,add(horizontal,[0,0,down]));seg('LOAD_SETTLE',t['push_start'],horizontal)
        seg('PUSH_OFF',t['release'],add(horizontal,[0,0,vu]))
        seg('AIRBORNE_ASCENT',t['apex'],horizontal)
    seg('AIRBORNE_DESCENT',t['land'],add(horizontal,[0,0,vd]))
    landpoint=[pos[0],pos[1],pos[2]-h0]
    if norm(sub(landpoint,s['intended_land_point']))>LIMITS['target_tolerance']:raise ValueError('TRAJECTORY_TARGET_MISMATCH')
    seg('LAND_DECELERATION',t['absorb_end'],horizontal)
    absorb=h0+landz-pos[2];mid=(t['absorb_end']+t['recover_end'])//2
    up=2*absorb/((t['recover_end']-t['absorb_end'])/fps)
    seg('RECOVERY_EXTENSION',mid,add(mul(horizontal,.5),[0,0,up]));seg('RECOVERY_SETTLE',t['recover_end'],[0,0,0]);seg('REST',n,[0,0,0])
    rows=copy.deepcopy(rows)
    for r in rows:
        f=r['frame'];air=t['release']<f<t['land']
        plane=ground if f<=t['release'] else landz
        r['compression']=1. if air else compression_at(r['position'][2]-plane,cal)
        r['airborne_state']=('GROUNDED' if f<t['load_start'] else 'SUPPORT_LOSS' if drop and f<=t['release'] else 'LOADING' if not drop and f<t['push_start'] else 'PUSH_OFF' if f<=t['release'] else 'APEX' if not drop and f==t['apex'] else 'AIRBORNE_ASCENT' if not drop and f<t['apex'] else 'AIRBORNE_DESCENT' if f<t['land'] else 'LAND_CONTACT' if f==t['land'] else 'LAND_DECELERATION' if f<=t['absorb_end'] else 'RECOVERY' if f<=t['recover_end'] else 'GROUNDED')
    if drop:
        from support_release_clearance import preflight_rows
        clearance=preflight_rows(s.get('release_clearance'),rows,t['release'],t['land'])
        if clearance['status']!='PASS':raise ValueError('SUPPORT_RELEASE_GEOMETRY_CONFLICT: '+','.join(clearance['errors']))
    # Fragment hashes remain original; pose/air metadata are separate ordinary CSP fields.
    bundle={'fragments':frags,'composition':[{'type':'SEQUENTIAL','members':[a['primitive_id'],b['primitive_id']]} for a,b in zip(prims,prims[1:])]}
    return {'spec':s,'calibration':cal,'intensity':initial,'primitives':prims,'bundle':bundle,'rows':rows,'phases':phase_ranges,'contract':{'schema_version':'AIR-TRAJECTORY-CONTRACT/1.0','support_release_clearance':s.get('release_clearance'),'semantic_support_release_frame':s.get('support_release_frame',t['release']),'mode':s['mode'],'takeoff_point':next(r['position'] for r in rows if r['frame']==t['release']),'takeoff_direction':horizontal,'entry_velocity':next(r['velocity'] for r in rows if r['frame']==t['release']),'horizontal_direction':profile['direction'],'vertical_trend':'DESCENT_ONLY' if drop else 'ASCENT_APEX_DESCENT','apex_time':None if drop else frame_to_time(t['apex'],fps),'apex_height':None if drop else s['apex_height'],'intended_land_point':s['intended_land_point'],'intended_land_surface':s['land_surface'],'exit_direction':horizontal,'recovery_state':'GROUNDED_REST','landing_response_source':'S005 recovery_segment','single_timebase':True,'limits':LIMITS}}

def attach_support(csp,compiled):
    s=compiled['spec'];t=s['timing'];n=s['frames'];actor=s['actor'];root='CHAR_'+actor
    binding={'actor':actor,'root':root,'body_control':actor+'__LOWER_CTRL','meshes':csp['actors'][0]['meshes'],'minimum_transition_frames':8,'max_recovery_delay_frames':t['absorb_end']-t['load_start']+2,'contact_tolerance':.015,'max_pose_step':.15,'balance_margin':.35,'tolerance_source':'Unchanged S004 tolerances; recovery delay derived from explicit authorized flight window','contacts':{'START':{'role':'SEAT','source':s['start_surface']['id'],'max_span':0},'LAND':{'role':'SEAT','source':s['land_surface']['id'],'max_span':0}}}
    # Existing SEAT measurement computes the lower body hull / finite planar surface, not anatomical feet.
    phases=[]
    def phase(id,a,b,state,weights):
        if b<a:return
        phases.append({'event_id':s['id']+'_'+id,'first_frame':a,'end_frame':b,'state':state,'weights':weights,'reason':'AUTHOR_EXPLICIT air-chain '+id})
    phase('GROUND',1,t['load_start']-1,'STANDING',{'START':1})
    semantic_release=s.get('support_release_frame',t['release'])
    release_start=semantic_release-18
    phase('SHIFT',t['load_start'],release_start-1,'SUPPORT_SHIFT',{'START':1})
    phase('UNLOAD',release_start,semantic_release,'LOST_SUPPORT',{'START':[1,0]})
    phase('AIR',semantic_release+1,t['land']-1,'LOST_SUPPORT',{'START':0,'LAND':0})
    phase('CONTACT',t['land'],t['absorb_end'],'LOST_SUPPORT',{'LAND':[0,1]})
    phase('RECOVER',t['absorb_end']+1,t['recover_end'],'RECOVERY',{'LAND':1})
    phase('REST',t['recover_end']+1,n,'STANDING',{'LAND':1})
    out=compile_support(csp,binding,phases)
    from combat_sequence_package import PHASES
    out['action_beats'].append({'event_id':s['id']+'_AIR_CONTRACT','type':'AIR_TRAJECTORY','interval_s':[frame_to_time(t['load_start'],s['fps']),frame_to_time(t['recover_end'],s['fps'])],'phases':{k:{'status':'NA','reason':'Explicit air-chain technical event'} for k in PHASES},'breakdowns':[{'time_s':frame_to_time(t['land'],s['fps']),'role':'LAND_CONTACT'}],'air_trajectory':compiled['contract']})
    for row,air in zip(out['object_tracks'][root],compiled['rows']):row['state']['airborne_state']={'state':air['airborne_state'],'event_id':s['id']+'_AIR_CONTRACT','frame':row['frame']}
    return out,binding,phases

def validate_air(compiled,observed):
    s=compiled['spec'];t=s['timing'];fps=s['fps'];errors=[]
    if observed is None:return {'status':'NOT_REVIEWED','errors':[],'reason':'NATIVE_EVIDENCE_REQUIRED'}
    rows=observed.get('rows',[])
    if [r.get('frame') for r in rows]!=list(range(1,s['frames']+1)):return {'status':'FAIL','errors':['AIRBORNE_WITHOUT_TRAJECTORY']}
    if not observed.get('native_geometry') or not observed.get('reopened'):return {'status':'NOT_REVIEWED','errors':[],'reason':'NATIVE_EVIDENCE_REQUIRED'}
    if s['mode']=='DROP':
        from support_release_clearance import evaluate
        contract=copy.deepcopy(s.get('release_clearance'))
        if not contract or not observed.get('support_region') or any('clearance_bounds' not in r for r in rows):
            return {'status':'NOT_REVIEWED','errors':['CLEARANCE_PROXY_UNRESOLVED'],'reason':'Native support bounds and body bounds required'}
        contract['support_region']=observed['support_region']
        samples=[{'frame':r['frame'],'bounds':r['clearance_bounds'],'support_weight':r['support_weight'],'airborne':r['frame']>t['release']} for r in rows if t['release']<=r['frame']<t['land']]
        clearance=evaluate(contract,samples)
        errors.extend(clearance.get('errors',[]))
    p={r['frame']:r for r in rows};v={f:mul(sub(p[f]['position'],p[f-1]['position']),fps) for f in range(2,s['frames']+1)}
    if observed.get('support_status')!='PASS':errors.append('TAKEOFF_WITHOUT_SUPPORT_RELEASE')
    if any(p[f].get('support_weight',1)>1e-7 for f in range(t['release']+1,t['land'])):errors.append('TAKEOFF_WITHOUT_SUPPORT_RELEASE')
    if not p[t['land']].get('surface_inside') or abs(p[t['land']]['bottom']-s['land_surface']['height'])>.015:errors.append('LAND_WITHOUT_CONTACT')
    if any(not p[f].get('surface_inside') or abs(p[f]['bottom']-s['land_surface']['height'])>.015 for f in range(t['land'],s['frames']+1)):errors.append('LAND_SURFACE_UNRESOLVED')
    point=p[t['land']]['position'][:2]+[p[t['land']]['bottom']]
    if norm(sub(point,s['intended_land_point']))>.015:errors.append('TRAJECTORY_TARGET_MISMATCH')
    lo,hi=t['release']+2,t['land']
    horizontal=[v[f][:2]+[0] for f in range(lo,hi+1)]
    if any(norm(sub(x,horizontal[0]))>.02 for x in horizontal):errors.append('MID_AIR_UNAUTHORIZED_ACCELERATION')
    if any(v[f+1][2]>v[f][2]+.02 for f in range(lo,hi)):errors.append('MID_AIR_UNAUTHORIZED_ACCELERATION')
    if s['mode']=='JUMP':
        peak=max(range(t['release'],t['land']+1),key=lambda f:p[f]['position'][2])
        if abs(peak-t['apex'])>1 or max(v[f][2] for f in range(lo,hi))<.02 or min(v[f][2] for f in range(lo,hi))>-.02:errors.append('APEX_MISSING')
    elif any(v[f][2]>.02 for f in range(lo,hi)):errors.append('DROP_BECOMES_TAKEOFF')
    if abs(v[t['land']+1][2])<abs(v[t['land']][2])*.5:errors.append('INSTANT_STOP_ON_LAND')
    if t['absorb_end']-t['land']<LIMITS['minimum_response_samples'] or norm(v[s['frames']])>.02:errors.append('LAND_RECOVERY_MISSING')
    error=max(norm(sub(a['position'],b['position'])) for a,b in zip(rows,compiled['rows']))
    if error>1e-4:errors.append('AIRBORNE_WITHOUT_TRAJECTORY')
    return {'status':'FAIL' if errors else 'PASS','errors':sorted(set(errors)),'max_native_com_error':error,'landing_velocity_before':v[t['land']],'landing_velocity_after':v[t['land']+1],'flight_horizontal_speed':norm(horizontal[0]),'land_point':point,'thresholds':LIMITS,'human_review':'PENDING','scope':'Director kinematic trajectory and state continuity; not ballistic physics or final animation'}

def boundary_report(compiled,rows):
    """S45/S53R semantics are event scoped; a complete jump is not one monotone start."""
    from motion_boundary_validator import validate_boundary
    from motion_intensity import validate_spacing_boundary
    fps=compiled['spec']['fps'];index={r['frame']:r for r in rows};n=len(rows);reports=[];seams=[]
    raw=validate_spacing_boundary(rows,[5,n-4],fps,'A_COM',authored_envelope=True)
    for prim,frag in zip(compiled['primitives'],compiled['bundle']['fragments']):
        source=frag['world_samples'];lo=source[0]['frame'];hi=source[-1]['frame'];shift=max(0,5-lo)
        samples=[]
        for f in range(lo-4,hi+5):
            if f in index:pos=index[f]['position']
            else:
                edge=source[0] if f<lo else source[-1];pos=add(edge['position'],mul(edge['velocity'],(f-edge['frame'])/fps))
            samples.append({'frame':f+shift,'position':pos})
        measured=[dict(r,position=index[r['frame']]['position']) for r in source]
        report=validate_boundary(samples,[lo+shift,hi+shift],fps,'CHARACTER_ROOT_CONTINUITY_PROFILE',compiled['spec']['actor'],interpolation_evidence={'kind':'AUTHORED_CONTINUOUS_PIECEWISE_LINEAR'},boundary_semantic={'rows':measured,'primitive':prim})
        reports.append({'primitive_id':prim['primitive_id'],'report':report})
    for a,b in zip(compiled['bundle']['fragments'],compiled['bundle']['fragments'][1:]):
        x=a['world_samples'][-1];y=b['world_samples'][0];f=x['frame'];error=norm(sub(x['velocity'],y['velocity']))
        measured_error=max(norm(sub(mul(sub(index[f]['position'],index[f-1]['position']),fps),x['velocity'])),norm(sub(mul(sub(index[f+1]['position'],index[f]['position']),fps),y['velocity'])))
        seams.append({'frame':f,'position_gap':norm(sub(x['position'],y['position'])),'declared_velocity_gap':error,'native_velocity_error':measured_error,'status':'PASS' if error<1e-6 and measured_error<LIMITS['velocity_tolerance'] else 'FAIL'})
    dims={k:'PASS' if all(r['report']['dimensions'][k]=='PASS' for r in reports) and all(r['status']=='PASS' for r in seams) else 'FAIL' for k in ('C0','C1')}
    dims['C2']=raw['dimensions']['C2']
    return {'dimensions':dims,'status':'PASS' if dims['C0']==dims['C1']=='PASS' else 'FAIL','raw_whole_sequence':raw,'event_reports':reports,'actual_neighbor_seams':seams,'scope':'C0/C1 by explicit phase and actual neighboring samples; unchanged thresholds. C2 retained, no false analytic smoothness claim.'}
