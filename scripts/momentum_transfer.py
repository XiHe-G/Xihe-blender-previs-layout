"""Explicit director-level motion consequences on CSP; no mass/force solver."""
import copy,math
from timebase import frame_to_time
from primitive_runtime import compile_primitive
from primitive_sampler import sub,add,mul,norm,unit
from prop_control import event_list

def position(p,obj,f):return p['object_tracks'][obj][f-1]['state']['location']
def velocity(p,obj,f):return mul(sub(position(p,obj,f),position(p,obj,f-1)),p['timebase']['fps'])

def recovery_segment(p,pid,obj,first,last,origin,v0,v1):
    """Reuse S51, including its unchanged C0/C1 contract. No duplicate curve code."""
    fps=p['timebase']['fps'];a=frame_to_time(first,fps);z=frame_to_time(last,fps);duration=z-a
    q={'primitive_version':'EXECUTION-PRIMITIVE/1.0','primitive_id':'PRIM_'+pid,'primitive_type':'RECOVERY_PROFILE','actor':obj,'subjects':[],
       'start_time':a,'end_time':z,'entry_state':{'position':origin,'velocity':v0,'movement_direction':unit(v0),'orientation':[1,0,0,0],'angular_velocity':0.,'ownership_state':'FREE','support_state':'DECLARED_CSP_SUPPORT'},
       'parameters':{'entry_velocity':v0,'exit_velocity':v1,'duration':duration,'displacement_limit':norm(mul(add(v0,v1),duration/2))+1e-5,'direction_retention':0},
       'exit_requirements':{'velocity':v1},'continuity_contract':{'C0_REQUIRED':True,'C1_REQUIREMENT':'REQUIRED','C2_POLICY':'RECORD'},
       'provenance':{'source':'EXPLICIT_MOTION_CONSEQUENCE','boundary_semantics':'AUTHORED_ENVELOPE/1.0','not_physics':True}}
    fragment,diagnostic=compile_primitive(q,{'fps':fps,'time_unit':'seconds','frame_origin':1,'duration':p['timebase']['frames']/fps})
    if any(fragment['continuity_report']['dimensions'][k]!='PASS' for k in ('C0','C1')):raise ValueError('MOMENTUM_BOUNDARY_FAIL')
    return q,fragment,diagnostic

def write_segment(p,obj,fragment,hold=False):
    for r in fragment['world_samples']:p['object_tracks'][obj][r['frame']-1]['state']['location']=list(r['position'])
    if hold:
        r=fragment['world_samples'][-1]
        for f in range(r['frame']+1,p['timebase']['frames']+1):p['object_tracks'][obj][f-1]['state']['location']=list(r['position'])

def refresh_control_geometry(p,original,first):
    """Maintain existing translation-anchor contract; no acquisition is invented."""
    n=p['timebase']['frames']
    for prop,rows in p['object_tracks'].items():
        if not rows or 'prop_control' not in rows[0]['state']:continue
        b=rows[0]['state']['prop_control']['contract']
        for f in range(first,n+1):
            s=rows[f-1]['state']['prop_control'];controller=s['controller'];pos=position(p,prop,f)
            if b['handle_id'] in p['object_tracks']:p['object_tracks'][b['handle_id']][f-1]['state']['location']=add(pos,b['handle_offset'])
            if controller:
                anchor=b['anchors'][controller];offset=sub(position(original,anchor,f),position(original,prop,f));p['object_tracks'][anchor][f-1]['state']['location']=add(pos,offset)
            for member in b.get('members',[]):
                rel=sub(position(original,member,f),position(original,prop,f));p['object_tracks'][member][f-1]['state']['location']=add(pos,rel)

def attach(p,c):
    from combat_sequence_package import PHASES
    p=copy.deepcopy(p);eid=c['transfer_id'];fps=p['timebase']['fps']
    if any(b['event_id']==eid for b in p['action_beats']):raise ValueError('DUPLICATE_MOMENTUM_EVENT')
    p['action_beats'].append({'event_id':eid,'type':'MOTION_CONSEQUENCE','interval_s':[frame_to_time(c['first_frame'],fps),frame_to_time(c['recovery_end_frame'],fps)],'phases':{k:{'status':'NA','reason':'Kinematic consequence; no combat primitive'} for k in PHASES},'breakdowns':[{'time_s':frame_to_time(c['first_frame'],fps),'role':'CAUSAL_RESPONSE'}],'momentum_transfer':copy.deepcopy(c)})
    for obj in (c['source'],c['receiver']):
        for f in range(c['first_frame'],p['timebase']['frames']+1):
            # Causal sequence phase, not an inferred per-object physical phase.
            phase='STOPPING' if f>=c['recovery_end_frame'] else 'RECOVERY' if f>=c['response_end_frame'] else 'TRANSFER'
            p['object_tracks'][obj][f-1]['state']['motion_consequence']={'event_id':eid,'source':c['source'],'receiver':c['receiver'],'contact_ref':c['contact_ref'],'phase':phase}
    return p

def structural_errors(p,c):
    errors=[];events={e['event_id']:e for e in event_list(p)};e=events.get(c.get('contact_ref'));n=p['timebase']['frames']
    if not e or e['kind']!='CONTACT' or e['actor']!=c['actor'] or e['prop_id']!=c['prop']:errors.append('RESPONSE_WITHOUT_SOURCE')
    if {c['source'],c['receiver']}!={c['actor_root'],c['prop']}:errors.append('RESPONSE_WITHOUT_SOURCE')
    if c['mode'] not in ('COUPLED_STOP','DRAG_RESPONSE','IMPACT_RESPONSE','OBSERVE_CONTROLLED_STOP'):errors.append('UNSUPPORTED_MOMENTUM_MODE')
    if not 2<=c['first_frame']<c['response_end_frame']<c['recovery_end_frame']<n:errors.append('RECOVERY_MISSING')
    if not c['first_frame']<c['source_stop_frame']<=c['recovery_end_frame']:errors.append('RECOVERY_MISSING')
    if c['mode'] in ('DRAG_RESPONSE','IMPACT_RESPONSE') and not 0<c['response_gain']<=1:errors.append('INVALID_RESPONSE_GAIN')
    if c['mode']=='COUPLED_STOP' and c['source_stop_frame']!=c['recovery_end_frame']:errors.append('RECOVERY_MISSING')
    if e and e['frame']>c['first_frame']:errors.append('RESPONSE_WITHOUT_SOURCE')
    if c['mode']!='IMPACT_RESPONSE':
        acq=events.get(c.get('acquire_ref'))
        if not acq or acq['kind'] not in ('ACQUIRE','TRANSFER') or acq['actor']!=c['actor'] or acq['prop_id']!=c['prop'] or acq['contact_ref']!=c['contact_ref'] or acq['frame']>c['first_frame']:errors.append('RESPONSE_WITHOUT_SOURCE')
    if not c.get('reason') or not c.get('provenance'):errors.append('UNEXPLAINED_SPEED_CHANGE')
    return sorted(set(errors))

def compile_consequence(csp,contract,locked=()):
    if locked:raise ValueError('BLOCKED_BY_OVERRIDE')
    c=copy.deepcopy(contract);p=copy.deepcopy(csp);errors=structural_errors(p,c)
    if errors:raise ValueError(str(errors))
    a=c['first_frame'];source=c['source'];recipient=c['receiver'];v0=velocity(p,source,a);vr=velocity(p,recipient,a);fragments=[];primitives=[];diagnostics=[]
    if norm(v0)<c['limits']['moving_speed_epsilon']:raise ValueError('SOURCE_NOT_MOVING')
    c['incoming_source_velocity']=v0;c['incoming_recipient_velocity']=vr;c['velocity_source']='PREVIOUS_EVALUATED_SAMPLES';c['response_gain_source']='DIRECTOR_AUTHORED not mass ratio'
    if c['mode']=='OBSERVE_CONTROLLED_STOP':return attach(p,c),{'primitives':[],'fragments':[],'note':'Measure unchanged existing controlled stop; no new trajectory'}
    def segment(obj,first,last,pos,vin,vout,hold=False):
        q,f,d=recovery_segment(p,c['transfer_id']+'_'+str(len(fragments)),obj,first,last,pos,vin,vout);primitives.append(q);fragments.append(f);diagnostics.append(d);write_segment(p,obj,f,hold);return f
    f=segment(source,a,c['source_stop_frame'],position(p,source,a),v0,[0,0,0],True)
    if c['mode']=='COUPLED_STOP':
        if norm(sub(v0,vr))>c['limits']['entry_velocity_tolerance']:raise ValueError('COUPLED_ENTRY_VELOCITY_CONFLICT')
        offset=sub(position(csp,recipient,a),position(csp,source,a))
        for frame in range(a,p['timebase']['frames']+1):p['object_tracks'][recipient][frame-1]['state']['location']=add(position(p,source,frame),offset)
    else:
        goal=mul(v0,c['response_gain']);c['response_velocity_target']=goal
        f=segment(recipient,a,c['response_end_frame'],position(p,recipient,a),vr,goal)
        segment(recipient,c['response_end_frame'],c['recovery_end_frame'],f['exit_state_actual']['position'],goal,[0,0,0],True)
    refresh_control_geometry(p,csp,a)
    return attach(p,c),{'primitives':primitives,'fragments':fragments,'diagnostics':diagnostics,'contract':c}

def validate_consequence(p,c,observed=None):
    errors=structural_errors(p,c);measure={};missing=False
    if observed is None:return {'status':'FAIL' if errors else 'NOT_REVIEWED','errors':errors,'evidence_sufficiency':'INSUFFICIENT','measurements':measure}
    fps=p['timebase']['fps'];a=c['first_frame'];end=c['recovery_end_frame'];limits=c['limits'];positions=observed.get('positions',{});eps=limits['moving_speed_epsilon']
    if observed.get('support_status') in (None,'NOT_REVIEWED'):missing=True
    elif observed.get('support_status')!='PASS':errors.append('SUPPORT_NOT_VERIFIED')
    e=next((e for e in event_list(p) if e['event_id']==c['contact_ref']),None)
    native=observed.get('contacts',{}).get(c['contact_ref'])
    if native is None:missing=True
    elif not native.get('valid') or native.get('actor')!=c['actor'] or native.get('prop')!=c['prop']:errors.append('RESPONSE_WITHOUT_SOURCE')
    if c['mode']!='IMPACT_RESPONSE':
        ctrl=observed.get('controller_at_response')
        if ctrl is None:missing=True
        elif ctrl.get('controller')!=c['actor']:errors.append('RESPONSE_WITHOUT_SOURCE')
    for obj in (c['source'],c['receiver']):
        rows=positions.get(obj,{})
        if any(f not in rows for f in range(a-2,end+3)):missing=True;continue
        velocities={f:mul(sub(rows[f],rows[f-1]),fps) for f in range(a-1,end+3)};speeds={f:norm(v) for f,v in velocities.items()}
        spikes=[];instant=[]
        for f in range(a,end+3):
            if norm(sub(velocities[f],velocities[f-1]))*fps>limits['max_acceleration']+1e-4:spikes.append(f)
            if speeds[f-1]>eps and speeds[f]<eps*.1:instant.append(f)
        if spikes:errors.append('UNEXPLAINED_SPEED_CHANGE')
        if instant:errors.append('INSTANT_STOP_AFTER_CONTACT')
        if obj==c['source'] and speeds[a]<eps:errors.append('RESPONSE_WITHOUT_SOURCE')
        last_moving=max((f for f in range(a,end+1) if speeds[f]>eps),default=a)
        if last_moving-a<limits['minimum_response_frames']:errors.append('INSTANT_STOP_AFTER_CONTACT')
        if speeds[end+2]>limits['rest_speed_epsilon']:errors.append('RECOVERY_MISSING')
        displacement=norm(sub(rows[end],rows[a]));delta=max(norm(sub(velocities[f],velocities[a])) for f in range(a,end+1))
        if obj==c['receiver'] and (displacement<limits['minimum_response_displacement'] or delta<eps):errors.append('CONTACT_WITHOUT_RESPONSE')
        if obj==c['receiver'] and max(speeds[f] for f in range(c['response_end_frame'],end+1))<eps:errors.append('RECOVERY_MISSING')
        measure[obj]={'incoming_velocity':velocities[a],'speed_start':speeds[a],'speed_response_end':speeds[c['response_end_frame']],'speed_final':speeds[end+2],'displacement':displacement,'max_velocity_change':delta,'acceleration_spike_frames':spikes,'instant_stop_frames':instant,'last_moving_frame':last_moving,'phase_times':{'transfer':a,'recovery':c['response_end_frame'],'stop':end}}
    return {'status':'FAIL' if errors else 'NOT_REVIEWED' if missing else 'PASS','errors':sorted(set(errors)),'evidence_sufficiency':'INSUFFICIENT' if missing else 'ENOUGH','measurements':measure,'scope':'Director-authored kinematic consequence, no physical momentum/force conservation claim'}
