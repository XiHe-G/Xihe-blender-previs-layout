"""Opt-in combat semantics on CSP action beats; no collision physics or motion solver."""
import copy,math
from primitive_sampler import norm,sub,sha
from timebase import frame_to_time
RESULTS={'BLOCK','EVADE','HIT','MISS'}
INTENSITIES={'LIGHT_ATTACK','NORMAL_ATTACK','HEAVY_ATTACK','BURST_ATTACK'}

def attach(csp,contract):
    from combat_sequence_package import PHASES
    p=copy.deepcopy(csp);c=copy.deepcopy(contract);eid=c['id'];fps=p['timebase']['fps']
    if c['result'] not in RESULTS or c['attack_intensity'] not in INTENSITIES:raise ValueError('UNSUPPORTED_COMBAT_INTENT')
    if c['attacker']==c['defender']:raise ValueError('SELF_ATTACK_UNSUPPORTED')
    if not c.get('threat_route') or not c['threat_route'].get('path'):raise ValueError('ATTACK_WITHOUT_THREAT_ROUTE')
    if any(b['event_id']==eid for b in p['action_beats']):raise ValueError('DUPLICATE_COMBAT_EVENT')
    c['threat_route']['commit_sha256']=sha(c['threat_route']['path'])
    p['action_beats'].append({'event_id':eid,'type':'COMBAT_INTENT','interval_s':[frame_to_time(c['cue_frame'],fps),frame_to_time(c['recovery_end'],fps)],'phases':{k:{'status':'NA','reason':'Explicit scoped combat contract'} for k in PHASES},'breakdowns':[{'time_s':frame_to_time(c['contact_frame'],fps),'role':c['result']+'_RESULT'}],'combat_intent':c})
    p['causal_links'].append({'cause_event':c['perception_event'],'reaction_event':eid,'trigger_s':frame_to_time(c['notice_frame'],fps),'response_s':frame_to_time(c['defense_frame'],fps),'direction_rule':'EXPLICIT_COMBAT_RESPONSE','strength_rule':'DIRECTOR_KINEMATIC_NOT_MASS'})
    return p

def contracts(csp):return [b['combat_intent'] for b in csp.get('action_beats',[]) if 'combat_intent' in b]

def attention_and_initiative(c,f,previous=None):
    """Diagnostic projection of the existing beat, never a second scheduler."""
    state,initiative=state_at(c,f)
    defense='NEUTRAL'
    if c['notice_frame']<=f<c['defense_frame']:defense='DEFEND_PREPARE'
    elif c['defense_frame']<=f<c['contact_frame']:
        defense='EVADE_ATTEMPT' if c['result']=='EVADE' else 'BLOCK_ATTEMPT' if c['result']=='BLOCK' else 'DEFEND_PREPARE'
    elif c['contact_frame']<=f<=c['recovery_end']:defense=state
    changed=bool(previous and previous['attacker']!=c['attacker'] and f==c['cue_frame'])
    return {'attacker_state':state,'defender_state':defense,'initiative':initiative,'initiative_transition':'initiative_changed' if changed else None,'source':c['id'],'previous_source':previous['id'] if changed else None}

def state_at(c,f):
    if f<c['cue_frame']:return 'NEUTRAL','initiative_neutral'
    if f<c['commit_frame']:return 'PREPARE_ATTACK','attacker_has_initiative'
    if f<c['contact_frame']:return 'ATTACK_COMMIT','defender_reacting'
    if f==c['contact_frame']:return 'CONTACT' if c['result'] in ('BLOCK','HIT') else 'NEAR_MISS','defender_reacting'
    if f<c['source_stop_frame']:return c['result']+'_RESULT','attacker_has_initiative' if c['result']=='HIT' else 'initiative_neutral'
    if f<=c['recovery_end']:return 'RECOVERY','initiative_neutral'
    return 'NEUTRAL','initiative_neutral'

def validate(csp,c,observed=None):
    errors=[];route=c.get('threat_route');result=c.get('result');missing=[]
    if not route or not route.get('path'):errors.append('ATTACK_WITHOUT_THREAT_ROUTE')
    elif route.get('commit_sha256')!=sha(route['path']):errors.append('ATTACK_TRACKS_TARGET_ILLEGALLY')
    if result not in RESULTS:errors.append('CONTACT_WITHOUT_COMBAT_RESULT')
    if not c.get('anticipation_authority') and not(c['cue_frame']<c['notice_frame']<c['defense_frame']<=c['contact_frame']):errors.append('DEFENSE_BEFORE_ATTACK_CUE')
    causal=[x for x in csp.get('causal_links',[]) if x.get('reaction_event')==c['id']]
    if not causal or causal[0]['cause_event']!=c['perception_event']:errors.append('DEFENSE_BEFORE_ATTACK_CUE')
    if not c.get('recovery_end') or c['recovery_end']<=c['contact_frame']:errors.append('RECOVERY_MISSING_AFTER_ATTACK')
    if observed is None:return {'status':'FAIL' if errors else 'NOT_REVIEWED','errors':errors,'missing':['NATIVE_EVIDENCE']}
    if observed.get('basis')!='SAVED_REOPENED_NATIVE_GEOMETRY':missing.append('NATIVE_EVIDENCE')
    rows=observed.get('rows',[]);idx={r['frame']:r for r in rows};window=c['contact_window'];rr=[idx[f] for f in range(window[0],window[1]+1) if f in idx]
    if len(rr)!=window[1]-window[0]+1:missing.append('CONTACT_WINDOW')
    for dep in ('support','control','perception','boundary'):
        if observed.get(dep) is None or observed.get(dep)=='NOT_REVIEWED':missing.append(dep)
        elif observed[dep]!='PASS':errors.append(dep.upper()+'_NOT_VERIFIED')
    if rr:
        hits=[r for r in rr if r['contact_gap']<=c['limits']['contact_distance']]
        actual=bool(hits)
        if result=='BLOCK' and not actual:errors.append('BLOCK_WITHOUT_CONTACT')
        if result=='HIT' and not actual:errors.append('HIT_WITHOUT_CONTACT')
        if result in ('EVADE','MISS') and actual:errors.append('EVADE_STILL_INSIDE_THREAT_ROUTE' if result=='EVADE' else 'MISS_WITH_CONTACT')
        if actual and result not in ('BLOCK','HIT'):errors.append('CONTACT_WITHOUT_COMBAT_RESULT')
        if result=='EVADE':
            if c.get('defense_trend') not in ('DODGE','RETREAT') or c.get('defense_ref')!=c['perception_event']:errors.append('EVADE_STILL_INSIDE_THREAT_ROUTE')
            a=idx.get(c['defense_frame']);z=idx.get(c['contact_frame'])
            if not a or not z:missing.append('EVADE_MOTION')
            elif norm(sub(z['defender_position'],a['defender_position']))<c['limits']['minimum_evade_displacement']:errors.append('EVADE_STILL_INSIDE_THREAT_ROUTE')
    if route:
        for r in route['path']:
            a=idx.get(r['frame'])
            if a is None:missing.append('THREAT_SAMPLES');break
            if norm(sub(a['weapon_position'],r['position']))>c['limits']['route_tolerance']:errors.append('ATTACK_TRACKS_TARGET_ILLEGALLY');break
    if result in ('BLOCK','HIT'):
        if c.get('momentum_source')!=c['attack_contact_event'] or observed.get('momentum')!='PASS':errors.append('HIT_RESPONSE_WITHOUT_SOURCE')
        if not c.get('response_event'):errors.append('HIT_RESPONSE_WITHOUT_SOURCE')
    if any(r.get('controller')!=c['attacker'] for r in rows if c['cue_frame']<=r['frame']<=c['recovery_end']):errors.append('WEAPON_CONTROL_CHANGED_ON_CONTACT')
    end=idx.get(c['recovery_end']);contact=idx.get(c['contact_frame'])
    if end and contact and end['weapon_speed']>c['limits']['rest_speed']:errors.append('RECOVERY_MISSING_AFTER_ATTACK')
    if result in ('BLOCK','HIT') and end and contact and norm(sub(end['defender_position'],contact['defender_position']))<c['limits']['minimum_response_displacement']:errors.append('HIT_RESPONSE_WITHOUT_SOURCE')
    return {'status':'FAIL' if errors else 'NOT_REVIEWED' if missing else 'PASS','errors':sorted(set(errors)),'missing':sorted(set(missing)),'result':result,'contact_frames': [r['frame'] for r in rr if r['contact_gap']<=c['limits']['contact_distance']],'near_miss':{'minimum_distance':min((r['contact_gap'] for r in rr),default=None),'time_window':window,'threat_path_source':c['id']+'.threat_route','target_path_source':'native defender region'},'human_review':'PENDING','thresholds':c['limits'],'scope':'Simplified attack endpoint/target region evidence; not exact weapon-body collision'}
