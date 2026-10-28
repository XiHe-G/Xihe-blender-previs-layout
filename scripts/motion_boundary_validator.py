"""C0/C1/C2 sampled boundary diagnostics. No repair, smoothing, or animation writes."""
import math,statistics
from s2_common import digest
from motion_analysis import norm,distance,sub

PROFILES={
 'PROJECTILE_CONTINUITY_PROFILE':dict(object_type='PROJECTILE',velocity_ratio_warning=2.,velocity_ratio_fail=4.,relative_vector_warning=.6,relative_vector_fail=2.,direction_warning_deg=45.,direction_fail_deg=100.,acceleration_ratio_warning=4.,acceleration_ratio_fail=10.),
 'CHARACTER_ROOT_CONTINUITY_PROFILE':dict(object_type='CHARACTER_ROOT',velocity_ratio_warning=1.8,velocity_ratio_fail=3.,relative_vector_warning=.5,relative_vector_fail=1.5,direction_warning_deg=45.,direction_fail_deg=90.,acceleration_ratio_warning=4.,acceleration_ratio_fail=10.)
}
EVENT_DERIVATIVES={'CONTACT':{'C1','C2'},'IMPACT':{'C1','C2'},'LAND':{'C1','C2'},'TELEPORT':{'C0','C1','C2'},'CUT_RESET':{'C0','C1','C2'}}

def _angle(a,b,floor):
    if min(norm(a),norm(b))<=floor:return None
    return math.degrees(math.acos(max(-1.,min(1.,sum(x*y for x,y in zip(a,b))/(norm(a)*norm(b))))))

def _level(value,warn,fail):return 'FAIL' if value>fail else 'WARNING' if value>warn else 'PASS'
def _worst(statuses):return next((s for s in ['FAIL','WARNING','NOT_REVIEWED','PASS'] if s in statuses),'NOT_REVIEWED')

def validate_authorizations(declarations,graph,subject):
    if not declarations:return []
    if graph is None:raise ValueError('AUTHORIZED_DISCONTINUITY_REQUIRES_GRAPH')
    events={e['event_id']:e for e in graph['events']};fps=graph['timebase']['fps'];valid=[]
    for d in declarations:
        from s45_protocol import validate_protocol
        validate_protocol(d,'authorized-discontinuity.schema.json')
        if d['graph_sha256']!=digest(graph) or d['subject']!=subject:raise ValueError('STALE_OR_WRONG_DISCONTINUITY_AUTHORITY')
        e=events.get(d['event_id'])
        if not e or e['event_type'] not in EVENT_DERIVATIVES:raise ValueError('EVENT_DOES_NOT_AUTHORIZE_DISCONTINUITY')
        participants=e.get('actor',[])+e.get('targets',[])
        if subject not in participants:raise ValueError('DISCONTINUITY_SUBJECT_NOT_IN_EVENT')
        a,b=d['frame_range'];derivatives=set(d['derivatives'])
        if a>b or not derivatives or not derivatives<=EVENT_DERIVATIVES[e['event_type']]:raise ValueError('INVALID_DISCONTINUITY_DERIVATIVES')
        if (a-1)/fps<e['start']-1e-7 or (b-1)/fps>e['end']+1e-7:raise ValueError('DISCONTINUITY_OUTSIDE_EVENT')
        if d['requirement_source'] not in ('USER_AUTHORED','DIRECTOR_AUTHORED') or not d['reason']:raise ValueError('DISCONTINUITY_NEEDS_EXPLICIT_AUTHORITY')
        valid.append(d)
    return valid

def _legacy_validate_boundary(samples,patch_range,fps,profile_name,subject,scene_scale=1.,interpolation_evidence=None,seam_limits=None,authorized=None,graph=None):
    """Samples are world positions by frame. Linear evidence proves C0, not C1/C2.

    C1/C2 are finite-difference quality tests, not a claim of analytic differentiability.
    At least four guard samples on both sides are needed for an outside-motion reference.
    """
    if profile_name not in PROFILES or not math.isfinite(fps) or not fps>0 or not math.isfinite(scene_scale) or not scene_scale>0:raise ValueError('INVALID_BOUNDARY_PROFILE_OR_UNITS')
    if graph is not None and graph['timebase']['fps']!=fps:raise ValueError('BOUNDARY_GRAPH_TIMEBASE_MISMATCH')
    lo,hi=patch_range
    if not (isinstance(lo,int) and isinstance(hi,int) and 1<lo<=hi):raise ValueError('INVALID_PATCH_RANGE')
    p={s['frame']:s['position'] for s in samples}
    if len(p)!=len(samples) or any(len(v)!=3 or any(not math.isfinite(x) for x in v) for v in p.values()):raise ValueError('INVALID_POSITION_SAMPLES')
    profile=dict(PROFILES[profile_name],profile_id=profile_name,requirement_source='TECHNICAL_DEFAULT',confidence='MEDIUM',scene_scale_world_units=scene_scale,threshold_basis='RELATIVE_TO_UNPATCHED_ENTRY_EXIT_TRENDS; not an artistic approval')
    auth=validate_authorizations(authorized or [],graph,subject)
    missing=[f for f in range(lo-4,hi+5) if f not in p]
    root=dict(schema_version='MOTION-BOUNDARY/1.0',diagnostic_only=True,subject=subject,patch_range=list(patch_range),fps=fps,profile=profile,authorized_discontinuities=auth,automatic_repair=False)
    if missing:return dict(root,status='NOT_REVIEWED',reason='INSUFFICIENT_GUARD_SAMPLES',missing_frames=missing,dimensions={k:'NOT_REVIEWED' for k in ['C0','C1','C2']},intervals=[])
    dt=1/fps;v={f:[x/dt for x in sub(p[f],p[f-1])] for f in p if f-1 in p}
    a={f:[x/dt for x in sub(v[f],v[f-1])] for f in v if f-1 in v}
    j={f:[x/dt for x in sub(a[f],a[f-1])] for f in a if f-1 in a}
    outside=[f for f in v if lo-3<=f<lo or hi+2<=f<=hi+4]
    speed_floor=scene_scale*fps*1e-4
    speed_ref=max(statistics.median(norm(v[f]) for f in outside),speed_floor)
    outside_a=[norm(a[f]) for f in outside if f in a and (f<lo or f>=hi+3)]
    acceleration_floor=max(speed_ref*fps*.05,scene_scale*fps*fps*1e-5)
    accel_ref=max(statistics.median(outside_a or [0.]),acceleration_floor)
    profile.update(reference_speed=speed_ref,reference_acceleration=accel_ref,speed_floor=speed_floor,acceleration_floor=acceleration_floor)
    def qualify(status,derivative,frame):
        matches=[d['event_id'] for d in auth if derivative in d['derivatives'] and d['frame_range'][0]<=frame<=d['frame_range'][1]]
        return dict(raw_status=status,status='PASS' if matches and status in ('WARNING','FAIL') else status,authorization=matches,basis='AUTHORIZED_DISCONTINUITY' if matches else 'TECHNICAL_DEFAULT')
    # A discontinuous pair of explicit one-sided limits is C0 evidence. Sampled
    # positions alone cannot prove absence of a subframe jump.
    c0=[]
    for f in [lo,hi+1]:
        seam=next((s for s in (seam_limits or []) if s['frame']==f),None)
        if seam:
            gap=distance(seam['left'],seam['right']);q=qualify('FAIL' if gap>scene_scale*1e-5 else 'PASS','C0',f);q.update(frame=f,gap=gap,measurement_basis='EXPLICIT_ONE_SIDED_POSITION_LIMITS')
        elif interpolation_evidence and interpolation_evidence.get('kind') in ('NATIVE_LINEAR_FCURVES','AUTHORED_CONTINUOUS_PIECEWISE_LINEAR'):
            q=dict(qualify('PASS','C0',f),frame=f,gap=0.,measurement_basis=interpolation_evidence['kind'])
        else:q=dict(frame=f,status='NOT_REVIEWED',raw_status='NOT_REVIEWED',gap=None,measurement_basis='SAMPLES_DO_NOT_PROVE_C0')
        c0.append(q)
    rows=[]
    # Include guard transition after exit so a boundary spike is not hidden by
    # a short patch or a symmetric magnitude with changed direction.
    for f in range(lo,hi+3):
        before=v[f-1];inside=v[f];after=v[f+1];ratio=(max(norm(before),norm(inside))+speed_floor)/(min(norm(before),norm(inside))+speed_floor)
        relative=distance(before,inside)/speed_ref;angle=_angle(before,inside,speed_floor)
        c1=_worst([_level(ratio,profile['velocity_ratio_warning'],profile['velocity_ratio_fail']),_level(relative,profile['relative_vector_warning'],profile['relative_vector_fail']),_level(angle or 0,profile['direction_warning_deg'],profile['direction_fail_deg'])])
        ar=norm(a[f])/accel_ref;c2=_level(ar,profile['acceleration_ratio_warning'],profile['acceleration_ratio_fail'])
        rows.append(dict(frame=f,interval=[f-1,f],zone='ENTRY' if f==lo else 'EXIT' if f==hi+1 else 'POST_EXIT' if f>hi+1 else 'INSIDE',position_delta=sub(p[f],p[f-1]),position_step=distance(p[f],p[f-1]),velocity_before=before,velocity_inside=inside,velocity_after=after,speed=norm(inside),boundary_velocity_ratio=ratio,relative_velocity_change=relative,direction_change_deg=angle,acceleration_before=a[f-1],acceleration_boundary=a[f],acceleration_after=a[f+1],acceleration_spike_ratio=ar,jerk_estimate=j[f],jerk_is_hard_gate=False,C1=qualify(c1,'C1',f),C2=qualify(c2,'C2',f)))
    dims=dict(C0=_worst([q['status'] for q in c0]),C1=_worst([q['C1']['status'] for q in rows]),C2=_worst([q['C2']['status'] for q in rows]))
    return dict(root,status=_worst(list(dims.values())),dimensions=dims,c0=c0,intervals=rows,interpolation_evidence=interpolation_evidence,limitations='Finite-difference diagnostics; C1/C2 here are relative sampled quality, not universal physical limits; jerk informational only')

def validate_boundary(samples,patch_range,fps,profile_name,subject,scene_scale=1.,interpolation_evidence=None,seam_limits=None,authorized=None,graph=None,boundary_semantic=None):
    report=_legacy_validate_boundary(samples,patch_range,fps,profile_name,subject,scene_scale,interpolation_evidence,seam_limits,authorized,graph)
    if boundary_semantic is not None:
        from boundary_semantics import apply_semantics
        if report['dimensions']['C0']=='NOT_REVIEWED':return report
        report=apply_semantics(report,boundary_semantic['rows'],boundary_semantic['primitive'])
    return report


def result_dimensions(historical_result,side_effect_result,boundary):
    if side_effect_result not in ('PASS','FAIL','WARNING','NOT_REVIEWED'):raise ValueError('INVALID_SIDE_EFFECT_RESULT')
    motion=boundary['status']
    target=historical_result['status']
    overall='REGRESSION_INTRODUCED' if side_effect_result=='FAIL' else 'FIXED_WITH_WARNING' if target=='FIXED' and (motion!='PASS' or side_effect_result!='PASS') else target
    return dict(schema_version='REPAIR-ASSESSMENT/1.1',TARGET_RESULT=target,SIDE_EFFECT_RESULT=side_effect_result,MOTION_QUALITY_RESULT=motion,overall=overall,historical_result_sha256=digest(historical_result),historical_result_unchanged=True,automatic_repair=False)

if __name__=='__main__':
    import argparse
    from s2_common import read,write
    ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--output',required=True);args=ap.parse_args()
    write(args.output,validate_boundary(**read(args.input)))
