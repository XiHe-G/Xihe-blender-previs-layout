"""Opt-in body support records on the existing CSP timeline. No dynamics/IK."""
import copy,math
from motion_builder import smooth
from timebase import frame_to_time
STATES={'SITTING','WEIGHT_SHIFT','STANDING','LEANING','HAND_SUPPORTED','SUPPORTED_PUSH','RUNNING','DECELERATION','SUPPORT_SHIFT','LOST_SUPPORT','RECOVERY'}
TRANSITION_STATES={'WEIGHT_SHIFT','SUPPORT_SHIFT','DECELERATION','RECOVERY'}

def sample_offsets(keys,frame):
    """Explicit pose offset parameters; reuse existing smooth interpolation."""
    if frame<=keys[0][0]:return keys[0][1:]
    for a,b in zip(keys,keys[1:]):
        if a[0]<=frame<=b[0]:
            u=smooth((frame-a[0])/(b[0]-a[0]));return [x+(y-x)*u for x,y in zip(a[1:],b[1:])]
    return keys[-1][1:]

def compile_support(csp,binding,phases,locked=()):
    if locked:raise ValueError('BLOCKED_BY_OVERRIDE')
    p=copy.deepcopy(csp);n=p['timebase']['frames'];root=binding['root'];fps=p['timebase']['fps']
    if root not in p['object_tracks']:raise ValueError('SUPPORT_REQUIRES_BAKED_ROOT_TRACK')
    if [r['frame'] for r in p['object_tracks'][root]]!=list(range(1,n+1)):raise ValueError('SUPPORT_SAMPLE_GAP')
    cursor=1;last=None
    from combat_sequence_package import PHASES
    for phase in phases:
        if phase['first_frame']!=cursor or phase['end_frame']<cursor or phase['state'] not in STATES:raise ValueError('INVALID_SUPPORT_PHASE')
        if last=='SITTING' and phase['state'] not in ('SITTING','WEIGHT_SHIFT'):raise ValueError('SUDDEN_SUPPORT_CHANGE')
        if phase['state'] in TRANSITION_STATES and phase['end_frame']-cursor+1<binding['minimum_transition_frames']:raise ValueError('SUDDEN_SUPPORT_CHANGE')
        eid=phase['event_id'];beat={'event_id':eid,'type':'SUPPORT_TRANSITION','interval_s':[frame_to_time(cursor,fps),frame_to_time(phase['end_frame'],fps)],'phases':{k:{'status':'NA','reason':'Body support evidence, no combat dynamics'} for k in PHASES},'breakdowns':[{'time_s':frame_to_time(cursor,fps),'role':'SUPPORT_TRANSITION'}],'support_transition':{'actor':binding['actor'],'from_state':last,'to_state':phase['state'],'first_frame':cursor,'end_frame':phase['end_frame'],'reason':phase['reason']}}
        if any(b['event_id']==eid for b in p['action_beats']):raise ValueError('DUPLICATE_SUPPORT_EVENT')
        p['action_beats'].append(beat)
        for f in range(cursor,phase['end_frame']+1):
            u=smooth(min(1,(f-cursor)/max(1,phase.get('blend_frames',phase['end_frame']-cursor))))
            weights={k:(v[0]+(v[1]-v[0])*u if isinstance(v,list) else v) for k,v in phase['weights'].items()}
            record={'actor':binding['actor'],'support_state':phase['state'],'transition_event':eid,'weights':weights,'force_prop':phase.get('force_prop'),'contract':copy.deepcopy(binding)}
            p['object_tracks'][root][f-1]['state']['support_contact']=record
        cursor=phase['end_frame']+1;last=phase['state']
    if cursor!=n+1:raise ValueError('SUPPORT_TIMELINE_NOT_COVERED')
    for cut in p['continuity_states']:
        cut.setdefault('support',{})[binding['actor']]={s:copy.deepcopy(p['object_tracks'][root][cut[k]-1]['state']['support_contact']) for s,k in [('before','before_frame'),('after','after_frame')]}
    errors=structural_errors(p)
    if errors:raise ValueError(str(errors))
    return p

def structural_errors(p):
    errors=[];events={b['event_id']:b['support_transition'] for b in p.get('action_beats',[]) if 'support_transition' in b};n=p['timebase']['frames']
    for root,rows in p['object_tracks'].items():
        if not any('support_contact' in r['state'] for r in rows):continue
        if [r['frame'] for r in rows]!=list(range(1,n+1)):errors.append('SUPPORT_SAMPLE_GAP');continue
        prev=None;lost=None
        for r in rows:
            s=r['state'].get('support_contact');f=r['frame']
            if s is None:errors.append('SUPPORT_SAMPLE_GAP');continue
            b=s['contract'];ev=events.get(s['transition_event']);state=s['support_state'];weights=s['weights']
            if state not in STATES or not ev or ev['actor']!=s['actor'] or ev['to_state']!=state or not ev['first_frame']<=f<=ev['end_frame']:errors.append('SUDDEN_SUPPORT_CHANGE')
            if prev and state!=prev['support_state']:
                if not ev or ev['first_frame']!=f or s['transition_event']==prev['transition_event']:errors.append('SUDDEN_SUPPORT_CHANGE')
                if prev['support_state']=='SITTING' and state!='WEIGHT_SHIFT':errors.append('SUDDEN_SUPPORT_CHANGE')
            if prev and (b!=prev['contract'] or any(abs(weights.get(k,0)-prev['weights'].get(k,0))>b.get('max_weight_step',.15) for k in set(weights)|set(prev['weights']))):errors.append('SUDDEN_SUPPORT_CHANGE')
            if any(k not in b['contacts'] or not math.isfinite(v) or v<0 for k,v in weights.items()):errors.append('INVALID_SUPPORT_WEIGHTS')
            if state!='LOST_SUPPORT' and abs(sum(weights.values())-1)>1e-6:errors.append('INVALID_SUPPORT_WEIGHTS')
            if state=='LOST_SUPPORT':
                if lost is None:lost=f
            elif lost is not None:
                if state!='RECOVERY' or f-lost>b['max_recovery_delay_frames']:errors.append('LOST_SUPPORT_WITHOUT_RECOVERY')
                lost=None
            if s.get('force_prop') and (state not in ('SUPPORTED_PUSH','HAND_SUPPORTED','LEANING') or not any(b['contacts'][k]['role'] in ('BASE','SEAT') and v>0 for k,v in weights.items())):errors.append('OBJECT_FORCE_WITHOUT_BODY_SUPPORT')
            prev=s
        if lost is not None:errors.append('LOST_SUPPORT_WITHOUT_RECOVERY')
    for cut in p.get('continuity_states',[]):
        for actor,values in cut.get('support',{}).items():
            for side,key in [('before','before_frame'),('after','after_frame')]:
                root=values[side]['contract']['root']
                if values[side]!=p['object_tracks'][root][cut[key]-1]['state']['support_contact']:errors.append('SUDDEN_SUPPORT_CHANGE')
    return sorted(set(errors))

def validate_support(p,observed=None):
    errors=structural_errors(p);missing=False;count=0
    for root,rows in p['object_tracks'].items():
        if not any('support_contact' in r['state'] for r in rows):continue
        for r in rows:
            s=r['state'].get('support_contact');f=r['frame']
            if not s:continue
            b=s['contract'];o=observed.get(s['actor'],{}).get(f) if observed is not None else None
            if not o or not o.get('native_support'):missing=True;continue
            count+=1
            if o['native_support']!={k:v for k,v in s.items() if k!='contract'}:errors.append('SUDDEN_SUPPORT_CHANGE')
            active=[];contact_missing=False
            for key,weight in s['weights'].items():
                c=b['contacts'][key]
                if weight<=1e-8 and not (c['role']=='HAND' and s.get('force_prop')):continue
                m=o.get('contacts',{}).get(key)
                if not m:missing=True;contact_missing=True;continue
                if not m['inside'] or abs(m['gap'])>b['contact_tolerance'] or m['span']>c['max_span']:errors.append('INVALID_SUPPORT_WITHOUT_CONTACT')
                if m.get('link_error',0)>b['contact_tolerance']:errors.append('FLOATING_ACTION')
                if weight>0 and c['role'] in ('BASE','SEAT') and m['inside'] and abs(m['gap'])<=b['contact_tolerance']:active.append(m['point'])
            if s['support_state']!='LOST_SUPPORT' and not active and not contact_missing:errors.append('FLOATING_ACTION')
            if o['max_body_point_step']>b['max_pose_step']:errors.append('SUDDEN_SUPPORT_CHANGE')
            if active:
                center=o['body_center'];margin=b['balance_margin']
                if not all(min(x[i] for x in active)-margin<=center[i]<=max(x[i] for x in active)+margin for i in (0,1)):errors.append('UNSTABLE_SUPPORT_PROJECTION')
            if s.get('force_prop'):
                control=o.get('prop_control');hands=[v for k,v in o['contacts'].items() if b['contacts'][k]['role']=='HAND']
                if control is None or contact_missing:missing=True
                elif not active or control.get('controller')!=s['actor'] or not hands or any(not v['inside'] or abs(v['gap'])>b['contact_tolerance'] for v in hands):errors.append('OBJECT_FORCE_WITHOUT_BODY_SUPPORT')
    return {'status':'FAIL' if errors else 'NOT_REVIEWED' if missing or not count else 'PASS','errors':sorted(set(errors)),'evidence_sufficiency':'INSUFFICIENT' if missing else 'ENOUGH','observed_samples':count,'scope':'Geometric proxy support; no anatomical IK, mass/force/friction or gait solver'}
