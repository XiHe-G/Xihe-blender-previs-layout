"""PREVIEW_ONLY orchestration: original S3.5 Checker, no decision or execution API."""
from pathlib import Path
from contextlib import contextmanager
from s2_common import digest,projection
from repair_audit import filehash
from repair_impact_graph import impact_graph
from override_guard import verify_registry
from plan_actual_checker import check

STATUSES={'FEASIBLE','FEASIBLE_WITH_RISK','HIGH_RISK','INFEASIBLE','NOT_ENOUGH_EVIDENCE'}

def lens_projection_preview(bounds,lens_ratio,optical_center=(.5,.5)):
    """Low-cost perspective-camera preview using the existing projection utility.

    Requires unchanged perspective camera/near-far clipping and supplied optical
    center (runner only enables it for zero shift). Does not infer occlusion.
    """
    from screen_projection import summarize_projection
    if lens_ratio<=0:raise ValueError('INVALID_LENS_RATIO')
    if bounds is None:return summarize_projection([])
    points=[[(x-optical_center[0])*lens_ratio+optical_center[0],(y-optical_center[1])*lens_ratio+optical_center[1]] for x,y in [(bounds[0],bounds[1]),(bounds[2],bounds[3])]]
    return summarize_projection(points)

def output_directory(path,protected_roots):
    out=Path(path).resolve()
    if 'PREVIEW_ONLY' not in out.parts:raise ValueError('PREVIEW_ONLY_DIRECTORY_REQUIRED')
    for root in protected_roots:
        root=Path(root).resolve()
        if out==root or root in out.parents or out in root.parents:raise ValueError('PRODUCTION_OUTPUT_FORBIDDEN')
    if out.exists() and any(out.iterdir()):raise ValueError('PREVIEW_OUTPUT_ALREADY_USED')
    return out

@contextmanager
def preserve_files(paths):
    before={str(Path(p).resolve()):filehash(p) for p in paths}
    try:yield before
    finally:
        if any(not Path(p).is_file() or filehash(p)!=h for p,h in before.items()):raise ValueError('PREVIEW_MODIFIED_PRODUCTION_FILE')

def collisions(proposal,strategy_id,expected,report,baseline,registry,csp):
    verify_registry(registry,csp)
    impact=impact_graph(proposal,expected,strategy_id);paths=set(projection(csp,impact['directly_modified_channels']));issues=[]
    for lock in registry['overrides']:
        if lock['status']=='LOCKED' and paths & set(projection(csp,lock['protections'])):
            issues.append(dict(status='CONSTRAINT_COLLISION',kind='LOCKED_OVERRIDE',override_id=lock['override_id'],reason='Candidate intersects protected execution channels; preview grants no release'))
    old={r['observable_id']:r for r in baseline['results']};target=impact['target_observable']
    for r in report['results']:
        if r['observable_id']==target:continue
        if r['observable_id'] in impact['potentially_affected_observables'] and r['status']=='FAIL':
            issues.append(dict(status='CONSTRAINT_COLLISION',kind='OTHER_EXPECTED_OBSERVABLE',observable_id=r['observable_id'],code=r['code'],preexisting=old.get(r['observable_id'],{}).get('status')=='FAIL',reason='Candidate cannot satisfy this existing protected observable',frames=[e['frame'] for e in r['evidence']]))
        elif old.get(r['observable_id'],{}).get('status')=='PASS' and r['status']!='PASS':
            issues.append(dict(status='CONSTRAINT_COLLISION',kind='LOST_PROTECTED_PASS',observable_id=r['observable_id'],code=r['code'],reason='Previously evidenced PASS lost'))
    return issues

def protected_content_collisions(baseline_trace,trace,strategy_id):
    """Camera previews must preserve all world states, cuts, identity and visibility keys.

    Projected measurements may change. Native pointer tokens are process-local,
    not identity. Unknown non-camera preview preservation is not auto-certified.
    """
    if strategy_id not in ('LENS_CHANGE','CAMERA_DOLLY','CAMERA_REFRAME','CAMERA_LENS_COMBINED','RESTORE_CAMERA_ANCHOR'):return None
    old={r['frame']:r for r in baseline_trace['frames']};issues=[]
    if set(old)!={r['frame'] for r in trace['frames']}:return [dict(status='CONSTRAINT_COLLISION',kind='PROTECTED_CONTENT',reason='Frame coverage changed')]
    for row in trace['frames']:
        previous=old[row['frame']];changed=[]
        if previous['shot_id']!=row['shot_id'] or previous['time']!=row['time']:changed.append('Cut / timing')
        if strategy_id=='LENS_CHANGE' and digest(previous['camera_transform'])!=digest(row['camera_transform']):changed.append('Camera Transform')
        if strategy_id in ('CAMERA_DOLLY','CAMERA_REFRAME','RESTORE_CAMERA_ANCHOR') and previous['camera_lens']!=row['camera_lens']:changed.append('Lens')
        for name,b in previous['entities'].items():
            a=row['entities'].get(name)
            # Hidden viewport proxies can retain stale evaluated matrices from
            # the previously evaluated frame. Never treat those as motion evidence.
            fields=['entity_id','exists','object_ids','proxy_state']
            if b.get('proxy_state',{}).get('render_enabled') and (a or {}).get('proxy_state',{}).get('render_enabled'):fields.append('entity_world_state')
            if a is None or any(digest(b.get(key))!=digest(a.get(key)) for key in fields):changed.append(name+' world / identity / visibility')
            elif b['ownership_state']['native_owner']!=a['ownership_state']['native_owner']:changed.append(name+' owner')
        if changed:issues.append(dict(status='CONSTRAINT_COLLISION',kind='PROTECTED_CONTENT',frames=[row['frame']],reason='Protected values changed: '+', '.join(changed)))
    return issues

def summarize_preview(proposal,strategy_id,expected,report,baseline,trace,registry,csp,protected_collisions=None):
    impact=impact_graph(proposal,expected,strategy_id);issues=collisions(proposal,strategy_id,expected,report,baseline,registry,csp)
    issues.extend(protected_collisions or [])
    target=next(r for r in report['results'] if r['observable_id']==impact['target_observable'])
    shot=proposal['source_checker_result']['result']['shot_id'];subjects=proposal['affected_subjects'];window=proposal['time_range']
    screen={}
    for subject in subjects:
        rows=[r for r in trace['frames'] if r['shot_id']==shot and window[0]-1e-8<=r['time']<window[1]-1e-8]
        valid=[(r,r['entities'].get(subject)) for r in rows];valid=[(r,e) for r,e in valid if e and e['exists'] and e.get('screen_bounds')]
        if not valid:screen[subject]=dict(evidence='INSUFFICIENT');continue
        height=[e['screen_height_ratio'] for r,e in valid if e['screen_height_ratio'] is not None]
        outside=[r['frame'] for r,e in valid if e['screen_bounds']['clipped_bounds'] is None]
        clipped=[r['frame'] for r,e in valid if e['screen_bounds']['clipped_bounds'] is not None and e['screen_bounds']['visible_fraction_estimate']<.999999]
        screen[subject]=dict(evidence='PROJECTED_RECT_AND_ESTIMATED_RAYS',height_range=[min(height),max(height)] if height else None,out_of_frame=outside,partially_clipped=clipped,frames=[dict(frame=r['frame'],screen_center=e['screen_center'],projected_bounds=e['screen_bounds']['projected_bounds'],clipped_bounds=e['screen_bounds']['clipped_bounds'],visible_fraction_estimate=e['screen_bounds']['visible_fraction_estimate'],occlusion_ratio=e['occlusion_ratio']) for r,e in valid])
        if outside:issues.append(dict(status='CONSTRAINT_COLLISION',kind='TARGET_VISIBILITY_LOSS',subject=subject,frames=outside,reason='Projected target has no intersection with effective screen; target size alone is insufficient'))
    relevant=[r for r in report['results'] if r['observable_id'] in impact['potentially_affected_observables']]
    unknown=[r['observable_id'] for r in relevant if r['status']=='NOT_REVIEWED']
    reasons=[i['reason'] for i in issues]
    if any(i['kind']=='LOCKED_OVERRIDE' for i in issues):status='INFEASIBLE'
    elif any(i['kind']=='TARGET_VISIBILITY_LOSS' for i in issues) or issues:status='HIGH_RISK'
    elif target['status']=='FAIL':status='INFEASIBLE';reasons.append('This specified candidate fails the unchanged target; no search or alternative selected')
    elif target['status'] not in ('PASS','WARNING'):status='NOT_ENOUGH_EVIDENCE';reasons.append('Target lacks measurement evidence')
    elif protected_collisions is None or unknown or target['status']=='WARNING' or any(r['status']=='WARNING' for r in relevant):status='FEASIBLE_WITH_RISK';reasons.append('Known candidate measurements incomplete or warning-qualified, or protected values not independently compared')
    else:status='FEASIBLE';reasons.append('Measured declared conditions pass for this candidate; unmeasured couplings remain unreviewed')
    return dict(schema_version='REPAIR-FEASIBILITY/1.0',preview_only=True,proposal_id=proposal['proposal_id'],proposal_sha256=digest(proposal),strategy_id=strategy_id,status=status,reasons=reasons,impact_graph=impact,constraint_collisions=issues,target_result=target,predicted_screen=screen,unknown_observables=unknown,protected_content_result='NOT_REVIEWED' if protected_collisions is None else 'FAIL' if protected_collisions else 'PASS',checker_report_sha256=digest(report),expected_sha256=digest(expected),production_csp_sha256=digest(csp),selection=None,decision_created=False,automatic_repair=False,coverage_limit='Finite known couplings and registered Expected Observables; protected world-state comparison covers render-enabled proxies only. Inactive matrices need native curve evidence. Not pixel or artistic approval')

def preview_check(graph,expected,trace,binding,proposal,strategy_id,baseline,registry,csp,baseline_trace=None):
    if digest(graph)!=proposal['graph_sha256'] or digest(csp)!=proposal['csp_sha256'] or digest(baseline)!=proposal['source_checker_result']['report_sha256']:raise ValueError('STALE_PREVIEW_SOURCE')
    # No alternate thresholds, modified Expected, or new checker family.
    report=check(graph,expected,trace,binding)
    report.update(preview_only=True,evidence_context='Hypothetical in-memory scene; source_blend is the immutable input, not a saved candidate',automatic_repair=False)
    protected=protected_content_collisions(baseline_trace,trace,strategy_id) if baseline_trace is not None else None
    return summarize_preview(proposal,strategy_id,expected,report,baseline,trace,registry,csp,protected),report
