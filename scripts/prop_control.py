"""Opt-in control transitions on CSP object samples; no bpy or motion kernel."""
import copy,math
from primitive_sampler import sha,norm,sub,add
from timebase import frame_to_time
STATES=('FREE','CONTACT_PENDING','CONTROLLED','RELEASING','PLACED')
KINDS={'CONTACT','ACQUIRE','FAIL','RELEASE','PLACE','FREE','TRANSFER'}

def translation_anchor(controller_positions,offset,scale=.065):
    """Bake an explicit world-axis controller proxy attachment; not motion design."""
    return [{'frame':f,'state':{'location':add(p,offset),'rotation_mode':'QUATERNION','rotation':[1,0,0,0],'scale':[scale]*3,'hide_render':False,'hide_viewport':False}} for f,p in enumerate(controller_positions,1)]

def transition(s,e):
    s=copy.deepcopy(s);kind=e['kind'];actor=e.get('actor');old=s['controller']
    if kind=='CONTACT':
        if s['control_state'] in ('RELEASING',):raise ValueError('CONTACT_DURING_RELEASE')
        s.update(contact_actor=actor,contact_event=e['event_id'])
        if old is None:s['control_state']='CONTACT_PENDING'
    elif kind in ('ACQUIRE','TRANSFER'):
        if s.get('contact_actor')!=actor or s.get('contact_event')!=e.get('contact_ref'):raise ValueError('INVALID_CONTROL_WITHOUT_CONTACT')
        if kind=='ACQUIRE' and old is not None:raise ValueError('CONTROLLER_TELEPORT')
        if kind=='TRANSFER' and (old is None or e.get('previous_controller')!=old or old==actor):raise ValueError('CONTROLLER_TELEPORT')
        s.update(previous_controller=old,controller=actor,control_state='CONTROLLED',control_method='TRANSLATION_ANCHOR')
    elif kind=='FAIL':
        if old is not None:raise ValueError('FAILED_GRAB_BECOMES_CONTROL')
        s.update(controller=None,control_state='FREE',contact_actor=None,contact_event=None,control_method=None)
    elif kind=='RELEASE':
        if old is None or actor!=old or s['control_state']!='CONTROLLED':raise ValueError('RELEASE_WITHOUT_CONTROL')
        s.update(previous_controller=old,controller=None,control_state='RELEASING',contact_actor=None,contact_event=None,control_method=None)
    elif kind=='PLACE':
        if s['control_state']!='RELEASING' or s['previous_controller']!=actor:raise ValueError('PLACE_WITHOUT_RELEASE')
        if e.get('support_plane_z') is None:raise ValueError('PLACEMENT_SUPPORT_UNDECLARED')
        s['control_state']='PLACED'
    elif kind=='FREE':
        if s['control_state']!='RELEASING':raise ValueError('FREE_WITHOUT_RELEASE')
        s['control_state']='FREE'
    else:raise ValueError('UNKNOWN_CONTROL_TRANSITION')
    s['transition_event']=e['event_id'];return s

def initial(prop):return dict(prop_id=prop,controller=None,previous_controller=None,control_state='FREE',contact_actor=None,contact_event=None,control_method=None,transition_event=None)

def event_list(p):
    return [dict(b['prop_control_transition'],event_id=b['event_id']) for b in p.get('action_beats',[]) if 'prop_control_transition' in b]

def compile_control(csp,bindings,events,controller_positions,locked=()):
    """Fresh output only. Driver anchors must already be sampled by existing runtime.
    Piecewise translation attachment, preserving world position at acquisition.
    Free post-release HOLD is explicit; no inferred ballistic motion.
    """
    if locked:raise ValueError('BLOCKED_BY_OVERRIDE')
    p=copy.deepcopy(csp);n=p['timebase']['frames'];fps=p['timebase']['fps'];ids={b['event_id'] for b in p['action_beats']}
    from combat_sequence_package import PHASES
    for e in events:
        if e['event_id'] in ids:raise ValueError('DUPLICATE_CONTROL_EVENT')
        ids.add(e['event_id'])
        if e['kind'] not in KINDS or e['actor'] not in controller_positions or not 1<=e['frame']<=n:raise ValueError('INVALID_CONTROL_EVENT')
        p['action_beats'].append({'event_id':e['event_id'],'type':'PROP_CONTROL','interval_s':[frame_to_time(e['frame'],fps)]*2,'phases':{x:{'status':'NA','reason':'Prop control state only; no combat phase'} for x in PHASES},'breakdowns':[{'time_s':frame_to_time(e['frame'],fps),'role':'CONTROL_TRANSITION'}],'prop_control_transition':{k:v for k,v in e.items() if k!='event_id'}})
    for b in bindings:
        prop=b['prop_id'];track=p['object_tracks'][prop];byf={x['frame']:x for x in track};es=[e for e in events if e['prop_id']==prop]
        if [r['frame'] for r in track]!=list(range(1,n+1)) or len({e['frame'] for e in es})!=len(es):raise ValueError('DENSE_CONTROL_TRACK_OR_EVENT_ORDER')
        if b['release_continuation']!='HOLD_WORLD':raise ValueError('UNSUPPORTED_RELEASE_CONTINUATION')
        if b['contact_radius']<=0 or b['max_reach']<=0 or b['minimum_contact_frames']<1:raise ValueError('INVALID_CONTROL_TOLERANCE')
        poses={a:[r['state']['location'] for r in p['object_tracks'][obj]] for a,obj in b['anchors'].items()}
        s=initial(prop);offset=None;released=False;released_position=None;relative_members={}
        for f in range(1,n+1):
            st=byf[f]['state'];pos=list(st['location']);old=copy.deepcopy(s)
            if s['controller'] is not None:pos=add(poses[s['controller']][f-1],offset)
            elif released:pos=list(released_position)
            handle=add(pos,b['handle_offset'])
            for e in (x for x in es if x['frame']==f):
                actor=e['actor'];anchor=poses[actor][f-1];root=controller_positions[actor][f-1]
                if e['kind'] in ('CONTACT','ACQUIRE','TRANSFER'):
                    if norm(sub(anchor,handle))>b['contact_radius']:raise ValueError('INVALID_CONTROL_WITHOUT_CONTACT')
                    if norm(sub(anchor,root))>b['max_reach']:raise ValueError('CONTROL_ANCHOR_OUT_OF_REACH')
                if e['kind'] in ('ACQUIRE','TRANSFER'):
                    contact=next((x for x in es if x['event_id']==e.get('contact_ref')),None)
                    if not contact or contact.get('kind')!='CONTACT' or contact.get('actor')!=actor:raise ValueError('INVALID_CONTROL_WITHOUT_CONTACT')
                    if f-contact['frame']<b['minimum_contact_frames']:raise ValueError('CONTACT_DWELL_INSUFFICIENT')
                s=transition(s,e)
                if e['kind'] in ('ACQUIRE','TRANSFER'):
                    offset=sub(pos,anchor);released=False
                    relative_members={name:sub(p['object_tracks'][name][f-1]['state']['location'],pos) for name in b.get('members',[])}
                if e['kind']=='RELEASE':released=True;released_position=list(pos)
            if s['controller']:
                if norm(sub(poses[s['controller']][f-1],controller_positions[s['controller']][f-1]))>b['max_reach']:raise ValueError('CONTROL_ANCHOR_OUT_OF_REACH')
            st['location']=pos;st['prop_control']=copy.deepcopy(s)
            # Contract accompanies ordinary sampled state, not a parallel frame sequence.
            st['prop_control']['contract']=copy.deepcopy(b)
            if s['controller'] or released:
                for name,rel in relative_members.items():p['object_tracks'][name][f-1]['state']['location']=add(pos,rel)
        # Add handle marker as an ordinary object track. Contact point is visibly explicit.
        p['primitive_assets'].append({'id':b['handle_id'],'type':'SPHERE','color':[1,.7,.1]})
        p['object_tracks'][b['handle_id']]=[{'frame':r['frame'],'state':dict(copy.deepcopy(r['state']),location=add(r['state']['location'],b['handle_offset']),scale=[b['contact_radius']*.6]*3)} for r in track]
        for r in p['object_tracks'][b['handle_id']]:r['state'].pop('prop_control',None)
    for cut in p['continuity_states']:
        cut.setdefault('ownership',{})['prop_control']={b['prop_id']:{'before':copy.deepcopy(p['object_tracks'][b['prop_id']][cut['before_frame']-1]['state']['prop_control']),'after':copy.deepcopy(p['object_tracks'][b['prop_id']][cut['after_frame']-1]['state']['prop_control'])} for b in bindings}
    errors=validate_control(p,controller_positions)
    if errors:raise ValueError(str(errors))
    return p

def validate_control(p,controller_positions=None,observed=None):
    """Replay events, inspect geometry and transform continuity. Observed overrides
    carry native metadata/positions; missing native evidence cannot be substituted.
    """
    errors=[];events=event_list(p);n=p['timebase']['frames'];fps=p['timebase']['fps'];known={e['event_id']:e for e in events}
    if any(e['prop_id'] not in p['object_tracks'] for e in events):errors.append('CONTROL_PROP_MISSING')
    if any(not any('prop_control' in row['state'] for row in p['object_tracks'].get(e['prop_id'],[])) for e in events):errors.append('CONTROL_EVIDENCE_MISSING')
    for prop,track in p['object_tracks'].items():
        if not any('prop_control' in r['state'] for r in track):continue
        if len(track)!=n:errors.append('CONTROL_SAMPLE_GAP');continue
        es=[e for e in events if e['prop_id']==prop];s=initial(prop);previous=None;rel=None
        for r in track:
            f=r['frame'];expected=r['state'].get('prop_control');native=observed.get(prop,{}).get(f) if observed is not None else None
            if expected is None:errors.append('CONTROL_SAMPLE_GAP');continue
            b=expected['contract'];now=native.get('control') if native else expected if observed is None else None
            if now is None:errors.append('CONTROL_EVIDENCE_MISSING');continue
            pos=native['position'] if native else r['state']['location'];handle=add(pos,b['handle_offset'])
            for e in (x for x in es if x['frame']==f):
                a=e['actor'];anchor=native['anchors'].get(a) if native else p['object_tracks'][b['anchors'][a]][f-1]['state']['location']
                if e['kind'] in ('CONTACT','ACQUIRE','TRANSFER'):
                    if anchor is None or norm(sub(anchor,handle))>b['contact_radius']+1e-5:errors.append('INVALID_CONTROL_WITHOUT_CONTACT')
                    if e['kind'] in ('ACQUIRE','TRANSFER'):
                        contact=known.get(e.get('contact_ref'))
                        if not contact or contact.get('kind')!='CONTACT' or contact.get('prop_id')!=prop or contact.get('actor')!=a or f-contact['frame']<b['minimum_contact_frames']:errors.append('INVALID_CONTROL_WITHOUT_CONTACT')
                        else:
                            for cf in range(contact['frame'],f+1):
                                if observed is not None:
                                    sample=observed.get(prop,{}).get(cf)
                                    if sample is None:errors.append('CONTROL_EVIDENCE_MISSING');continue
                                    ca=sample['anchors'].get(a);cp=sample['position']
                                else:ca=p['object_tracks'][b['anchors'][a]][cf-1]['state']['location'];cp=track[cf-1]['state']['location']
                                if ca is None or norm(sub(ca,add(cp,b['handle_offset'])))>b['contact_radius']+1e-5:errors.append('CONTACT_DWELL_BROKEN')
                try:s=transition(s,e)
                except ValueError as err:errors.append(str(err))
                if e['kind']=='FAIL' and now.get('controller') is not None:errors.append('FAILED_GRAB_BECOMES_CONTROL')
                if e['kind']=='PLACE' and native is not None and abs(native['mesh_bottom_z']-e['support_plane_z'])>b['placement_tolerance']:errors.append('PLACEMENT_SUPPORT_MISMATCH')
            for key in initial(prop):
                if now.get(key)!=s.get(key):errors.append('CONTROLLER_TELEPORT' if key=='controller' else 'CONTROL_STATE_MISMATCH')
            controller=s['controller']
            if controller:
                anchor=native['anchors'].get(controller) if native else p['object_tracks'][b['anchors'][controller]][f-1]['state']['location']
                root=native['controllers'].get(controller) if native else controller_positions.get(controller,[None]*n)[f-1] if controller_positions else None
                if root is not None and norm(sub(anchor,root))>b['max_reach']+1e-5:errors.append('CONTROL_ANCHOR_OUT_OF_REACH')
                relative=sub(pos,anchor)
                if previous and previous['controller']==controller and norm(sub(relative,rel))>b['position_tolerance']:errors.append('CONTROLLED_PROP_DISCONTINUITY')
                rel=relative
            if previous:
                step=norm(sub(pos,previous['position']))
                if step>b['max_speed'] / fps + b['position_tolerance']:errors.append('CONTROLLED_PROP_DISCONTINUITY')
                if s['control_state']=='PLACED' and previous['control_state']=='PLACED' and step>b['position_tolerance']:errors.append('PLACED_PROP_DRIFT')
            previous=dict(s,position=pos)
    # Cut snapshots must agree with canonical samples; same controller cannot reset at a cut.
    for c in p.get('continuity_states',[]):
        for prop,states in c.get('ownership',{}).get('prop_control',{}).items():
            for side,key in (('before','before_frame'),('after','after_frame')):
                if states[side]!=p['object_tracks'][prop][c[key]-1]['state']['prop_control']:errors.append('CUT_CONTROL_STATE_MISMATCH')
    return sorted(set(errors))

