"""S3.5 measurement policy. Profiles are technical assumptions, never approvals."""
from motion_analysis import distance,quaternion_angle,mean

PROFILES={
 'LOCKED_HOLD':dict(max_translation=.02,max_rotation_deg=.2,max_lens_delta=.05),
 'COMPOSITION_HOLD':dict(max_center_drift=.05,max_relative_size_drift=.10,max_translation=1.,max_rotation_deg=3.,max_lens_delta=.5),
 'SOFT_HOLD':dict(max_translation=1.,max_rotation_deg=3.,max_lens_delta=.5,max_net_translation=.5,max_relative_distance_change=.05),
}
GROSS=dict(translation=2.,rotation_deg=10.,lens_delta=5.)

def evidence_gap(o,rows):
    """Field availability gate, not a new checker family. Strong collision evidence survives absent rays."""
    if not rows:return 'NO_SAMPLES'
    subjects=o['subjects'];typ=o['type'];state=o.get('expected_state') or {}
    if any(s not in r['entities'] for r in rows for s in subjects):return 'MISSING_SUBJECT_TRACE'
    if typ in ('CONTACT','NEAR_MISS'):
        pairs=[r['pairwise_distance'].get('|'.join(subjects)) or r['pairwise_distance'].get('|'.join(reversed(subjects))) for r in rows]
        if any(p is None or p.get('contact') is None or p.get('geometry_clearance') is None for p in pairs):return 'MISSING_GEOMETRY'
        collision=any(p['contact'] and p.get('both_render_enabled') for p in pairs)
        active=[(r,p) for r,p in zip(rows,pairs) if p.get('both_render_enabled')]
        if typ=='NEAR_MISS' and not collision and active:
            closest=min(active,key=lambda rp:rp[1]['geometry_clearance'])[0]
            if any(closest['entities'][s].get('occlusion_ratio') is None for s in subjects):return 'MISSING_NEAR_MISS_VISIBILITY_EVIDENCE'
    if typ in ('SHOT_SIZE','SCREEN_POSITION') and state.get('max_occlusion') is not None:
        if any(r['entities'][s].get('occlusion_ratio') is None for r in rows for s in subjects):return 'MISSING_REQUIRED_OCCLUSION_EVIDENCE'
    return None

def camera_hold(o,rows):
    name=o['behavior_profile']; limits=dict(PROFILES[name]);limits.update(o.get('tolerance_profile',{}).get('limits',{}))
    subject=o['subjects'][0]; samples=[r['entities'][subject] for r in rows]
    cams=[r['camera_transform'] for r in rows];positions=[c['position'] for c in cams]
    if len({c['object'] for c in cams})!=1:return 'NOT_REVIEWED','CAMERA_STATE_CROSSES_CUT',{},[]
    travel=sum(distance(a,b) for a,b in zip(positions,positions[1:]));net=distance(positions[0],positions[-1])
    angle=max(quaternion_angle(cams[0]['quaternion'],c['quaternion']) for c in cams)
    lens=max(r['camera_lens'] for r in rows)-min(r['camera_lens'] for r in rows)
    actual=dict(profile=name,path_translation=travel,net_translation=net,max_rotation_deg=angle,lens_range=lens,limits=limits,
      gross_violation=net>GROSS['translation'] or travel>GROSS['translation']*1.5 or angle>GROSS['rotation_deg'] or lens>GROSS['lens_delta'])
    ok=travel<=limits['max_translation'] and angle<=limits['max_rotation_deg'] and lens<=limits['max_lens_delta']
    if name=='COMPOSITION_HOLD':
        centers=[s.get('screen_center') for s in samples];sizes=[s.get('screen_height_ratio') for s in samples]
        if any(c is None or not s.get('screen_bounds',{}).get('clipped_bounds') for c,s in zip(centers,samples)) or not sizes[0]:
            if actual['gross_violation']:return 'FAIL','CAMERA_STATE_MISMATCH',actual,[rows[0],rows[-1]]
            return 'NOT_REVIEWED','COMPOSITION_EVIDENCE_UNAVAILABLE',actual,[]
        actual['center_drift']=max(distance(c,centers[0]) for c in centers)
        actual['relative_size_drift']=max(abs(s/sizes[0]-1) for s in sizes)
        ok=ok and actual['center_drift']<=limits['max_center_drift'] and actual['relative_size_drift']<=limits['max_relative_size_drift']
    if name=='SOFT_HOLD':
        ds=[distance(c['position'],s['entity_world_state']['position']) for c,s in zip(cams,samples)]
        actual['relative_distance_change']=abs(ds[-1]-ds[0])/max(ds[0],1e-8)
        actual['translation_coherence']=net/max(travel,1e-8)
        # Subject motion alone cannot prove a PUSH/PULL. Require camera travel too.
        active=travel>.02
        ok=ok and net<=limits['max_net_translation'] and (not active or actual['relative_distance_change']<=limits['max_relative_distance_change'])
    return ('PASS' if ok else 'FAIL'),'CAMERA_STATE_MATCH' if ok else 'CAMERA_STATE_MISMATCH',actual,[rows[0],rows[-1]]

def qualify(o,status,code,actual,evidence):
    """Separate measurement sufficiency from requirement authority; preserve strong failures."""
    source=o.get('requirement_source','TECHNICAL_DEFAULT')
    strong=bool(evidence) and (actual.get('gross_violation') or bool(set(actual.get('violations',[])) & {'OWNER_MISMATCH','ENTITY_ID_MISMATCH','IDENTITY_RECREATED','PROJECTILE_TELEPORT','PROJECTILE_RELEASE_DETACHMENT'}) or actual.get('classification')=='CONTACT')
    level='INSUFFICIENT' if status=='NOT_REVIEWED' else 'ENOUGH'
    reasons=[]
    if status not in ('NOT_REVIEWED','NA') and not evidence:
        level='INSUFFICIENT';status='NOT_REVIEWED';reasons.append('NO_MEASUREMENT_EVIDENCE')
    if source in ('HISTORICAL_LABEL','INFERRED') or o.get('confidence')=='LOW':
        if level!='INSUFFICIENT':level='PARTIAL'
        reasons.append('REQUIREMENT_OR_TOLERANCE_NOT_AUTHOR_CONFIRMED')
        if status in ('PASS','FAIL') and not (status=='FAIL' and strong):status='WARNING'
    if actual.get('projection_evidence')=='PARTIAL':
        if level!='INSUFFICIENT':level='PARTIAL'
        reasons.append('PROJECTED_RECT_CENTER_OUTSIDE_FRAME; trajectory measurable but not visible-pixel evidence')
        if status in ('PASS','FAIL') and not strong:status='WARNING'
    if status=='NOT_REVIEWED':level='INSUFFICIENT'
    return status,dict(level=level,strong_evidence=bool(strong),reasons=reasons,requirement_source=source,
      confidence=o.get('confidence','LOW'),assumption='DEFAULT ASSUMPTION' if source=='TECHNICAL_DEFAULT' or o.get('tolerance_profile',{}).get('source')=='TECHNICAL_DEFAULT' else None)
