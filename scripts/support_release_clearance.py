"""Restricted support departure preflight. No bpy, dynamics, route or scene edits."""
import math,copy
CONTACT_TOLERANCE=.015

def valid_bounds(b):
    try:
        return isinstance(b,(list,tuple)) and len(b)==2 and all(len(v)==3 for v in b) and all(math.isfinite(x) for v in b for x in v) and all(b[0][i]<=b[1][i] for i in range(3))
    except (TypeError,ValueError):return False

def overlap(body,surface):
    return [min(body[1][i],surface[1][i])-max(body[0][i],surface[0][i]) for i in range(3)]

def penetrates(body,surface):
    # Exact S009 Native AABB audit predicate, unchanged .015 tolerance.
    return min(overlap(body,surface))>CONTACT_TOLERANCE

def separation(body,surface,axis,sign):
    return body[0][axis]-surface[1][axis] if sign>0 else surface[0][axis]-body[1][axis]

def swept(a,b,surface):
    """Conservative envelope, only callers with reliable translation interpolation qualify."""
    hull=[[min(a[0][i],b[0][i]) for i in range(3)],[max(a[1][i],b[1][i]) for i in range(3)]]
    return {'envelope':hull,'overlap':overlap(hull,surface),'clear':not penetrates(hull,surface),'proof':'ENDPOINT_AABB_ENVELOPE_CONTAINS_LINEAR_TRANSLATION'}

def evaluate(contract,samples):
    c=copy.deepcopy(contract);errors=[]
    required=('actor','support_surface','support_region','body_clearance_proxy','movement_direction','release_candidate_frame','minimum_clearance','evidence_source','transition_event','mode')
    if any(k not in c for k in required) or not valid_bounds(c.get('support_region')) or not samples or any(not valid_bounds(r.get('bounds')) for r in samples):
        return {'status':'NOT_REVIEWED','errors':['CLEARANCE_PROXY_UNRESOLVED']}
    if not c['body_clearance_proxy'] or not c['evidence_source'] or not isinstance(c['transition_event'],dict):return {'status':'NOT_REVIEWED','errors':['CLEARANCE_PROXY_UNRESOLVED']}
    if c.get('interpolation')!='FIXED_ORIENTATION_LINEAR_TRANSLATION':return {'status':'NOT_REVIEWED','errors':['CLEARANCE_PROXY_UNRESOLVED'],'reason':'No conservative interpolation proof'}
    if c['minimum_clearance']<0 or c['mode'] not in ('ACTIVE_TAKEOFF','PASSIVE_SUPPORT_LOSS'):raise ValueError('INVALID_CLEARANCE_CONTRACT')
    frames=[r['frame'] for r in samples]
    if any(b<=a for a,b in zip(frames,frames[1:])):raise ValueError('INVALID_CLEARANCE_SAMPLES')
    if c['release_candidate_frame'] not in frames:return {'status':'NOT_REVIEWED','errors':['CLEARANCE_PROXY_UNRESOLVED'],'reason':'candidate frame missing'}
    # Only axis-aligned departure evidence supported; never assume a diagonal force direction.
    direction=c['movement_direction'];axis=2 if c['mode']=='ACTIVE_TAKEOFF' else max((0,1),key=lambda i:abs(direction[i]));sign=1 if direction[axis]>=0 else -1
    if c['mode']=='PASSIVE_SUPPORT_LOSS' and (abs(direction[axis])<1e-8 or abs(direction[1-axis])>1e-7):return {'status':'NOT_REVIEWED','errors':['CLEARANCE_PROXY_UNRESOLVED'],'reason':'Non-axis-aligned exit outside V0.1'}
    first=None;rows=[];sweeps=[];previous=None
    event=c['transition_event'];authority=event.get('actor')==c['actor'] and event.get('surface')==c['support_surface'] and event.get('mode')==c['mode'] and bool(event.get('id'))
    for r in samples:
        b=r['bounds'];f=r['frame'];gap=separation(b,c['support_region'],axis,sign)
        center=(b[0][axis]+b[1][axis])/2;edge=c['support_region'][1 if sign>0 else 0][axis]
        center_clear=sign*(center-edge)>=c['minimum_clearance'];body_clear=gap>=c['minimum_clearance']
        if body_clear and f>=c['release_candidate_frame'] and first is None:first=f
        if previous:
            sw=swept(previous['bounds'],b,c['support_region']);sw['frames']=[previous['frame'],f];sweeps.append(sw)
            if (r.get('airborne') or previous.get('airborne')) and not sw['clear']:errors.append('SWEPT_EDGE_INTERSECTION')
        if r.get('airborne'):
            if not authority or r.get('support_weight')!=0:errors.append('SUPPORT_RELEASE_GEOMETRY_CONFLICT')
            if not body_clear:
                errors.append('SUPPORT_RELEASE_BEFORE_BODY_CLEAR')
                if center_clear:errors.append('CENTER_CLEAR_BUT_BODY_OVERLAP')
            if penetrates(b,c['support_region']):errors.append('AIRBORNE_WHILE_INTERSECTING_SUPPORT')
        rows.append({'frame':f,'gap':gap,'center_cleared':center_clear,'body_cleared':body_clear,'support_weight_released':r.get('support_weight')==0,'transition_valid':authority,'airborne_admissible':authority and r.get('support_weight')==0 and body_clear and not penetrates(b,c['support_region'])})
        previous=r
    candidate=next(r for r in rows if r['frame']==c['release_candidate_frame'])
    if not authority:errors.append('SUPPORT_RELEASE_GEOMETRY_CONFLICT')
    if c['mode']=='PASSIVE_SUPPORT_LOSS':
        if not candidate['body_cleared']:errors.append('SUPPORT_RELEASE_BEFORE_BODY_CLEAR')
        if not candidate['support_weight_released']:errors.append('SUPPORT_RELEASE_GEOMETRY_CONFLICT')
    # Active push-off can depart upward from surface contact; evaluate the next outgoing sample.
    outgoing=[r for r in rows if r['frame']>c['release_candidate_frame']]
    if c['mode']=='ACTIVE_TAKEOFF' and (not outgoing or not outgoing[0]['airborne_admissible']):errors.append('SUPPORT_RELEASE_GEOMETRY_CONFLICT')
    return {'status':'FAIL' if errors else 'PASS','errors':sorted(set(errors)),'contract':c,'first_valid_clear_frame':first,'candidate':candidate,'samples':rows,'sweeps':sweeps,'threshold_source':'TECHNICAL_DEFAULT / unchanged S009 .015 penetration tolerance','scope':'Conservative simple-box departure proof, not general collision physics'}

def resolve_passive(contract,samples):
    """Read-only proposal; no new motion, time or landing approval is created."""
    report=evaluate(contract,samples)
    f=report.get('first_valid_clear_frame')
    return {'status':'CLEARANCE_PROXY_UNRESOLVED' if f is None else 'READY' if f==contract['release_candidate_frame'] else 'RELEASE_FRAME_ADJUSTMENT_REQUIRED','release_candidate_frame':contract['release_candidate_frame'],'first_valid_clear_frame':f,'airborne_not_before_frame':None if f is None else f+1,'reason':'clearance constraint','preflight':report}

def preflight_rows(contract,rows,release,land):
    """Translate measured fixed-size native bounds along existing runtime COM samples.

    This prediction requires a later native geometry audit; never substitutes for it.
    """
    if not contract or not valid_bounds(contract.get('body_local_bounds')):
        return {'status':'NOT_REVIEWED','errors':['CLEARANCE_PROXY_UNRESOLVED']}
    samples=[]
    for r in rows:
        if release<=r['frame']<land:
            b=[[v+r['position'][i] for i,v in enumerate(side)] for side in contract['body_local_bounds']]
            samples.append({'frame':r['frame'],'bounds':b,'support_weight':0,'airborne':r['frame']>release})
    c=copy.deepcopy(contract);c['release_candidate_frame']=release
    return evaluate(c,samples)
