"""Opt-in, grounded Box layout expression. Explicit authoring, not a physics solver.

Reuses S008/S51 speed integration; emits ordinary actor_pose_tracks for CSP.
No Blender access, scene reset, automatic combat tactics, or old-kernel mutation.
"""
import argparse
import copy
import json
import math
from pathlib import Path

from primitive_sampler import arclength_path, norm, sub, unit, smooth

POSE_CHANNELS = {'body_pitch', 'body_roll', 'body_yaw', 'lower_pitch',
                 'lower_roll', 'head_pitch', 'head_yaw', 'compression'}


def scalar_envelope(spec, tb, policy):
    """Use unchanged S51 integration without silently weakening S008's gate.

    Short, authored ramps can fail S45's sampled acceleration/near-zero heuristic.
    Opt-in author policy retains those failures AND records exact shared knot
    positions/velocities. This is not an override of S45 or a native/visual PASS.
    """
    from primitive_runtime import compile_primitive
    if policy not in ('LEGACY_STRICT','AUTHORED_SPEED_ENVELOPE'):
        raise ValueError('UNKNOWN_BOUNDARY_POLICY')
    rows=[];fragments=[];origin=[0.,0.,0.];primitives=[]
    for i,(a,b) in enumerate(zip(spec['knots'],spec['knots'][1:])):
        first=(a['frame']-1)/tb['fps'];last=(b['frame']-1)/tb['fps'];duration=last-first
        v0=[a['speed'],0,0];v1=[b['speed'],0,0]
        p=dict(primitive_version='EXECUTION-PRIMITIVE/1.0',primitive_id='PRIM_'+spec['id']+'_'+str(i),
               primitive_type='RECOVERY_PROFILE',actor=spec['actor'],subjects=[],start_time=first,end_time=last,
               entry_state=dict(position=origin,velocity=v0,movement_direction=[1,0,0],orientation=[1,0,0,0],
                                angular_velocity=0,ownership_state='FREE',support_state='AUTHORED_GROUNDED'),
               parameters=dict(entry_velocity=v0,exit_velocity=v1,duration=duration,
                               displacement_limit=(a['speed']+b['speed'])*duration/2+1e-6,direction_retention=1),
               exit_requirements=dict(velocity=v1),
               continuity_contract=dict(C0_REQUIRED=True,C1_REQUIREMENT='REQUIRED',C2_POLICY='RECORD'),
               provenance=dict(source=spec['provenance'],boundary_semantics='AUTHORED_ENVELOPE/1.0',not_physics=True))
        f,d=compile_primitive(p,tb)
        if f['continuity_report']['dimensions']['C0']!='PASS':raise ValueError('POSITION_BOUNDARY_FAILURE')
        if policy=='LEGACY_STRICT' and f['continuity_report']['dimensions']['C1']!='PASS':
            raise ValueError('LEGACY_C1_FAIL: use explicit authored policy only after inspecting diagnostics')
        if fragments and (norm(sub(fragments[-1]['exit_state_actual']['position'],f['entry_state_actual']['position']))>1e-8 or
                          norm(sub(fragments[-1]['exit_state_actual']['velocity'],f['entry_state_actual']['velocity']))>1e-8):
            raise ValueError('ANALYTIC_KNOT_DISCONTINUITY')
        primitives.append(p);fragments.append(f);rows.extend(f['world_samples'][bool(rows):]);origin=f['exit_state_actual']['position']
    return dict(rows=rows,bundle=dict(fragments=fragments),primitives=primitives,
                analytic_scalar_c0_c1='PASS',policy=policy)


def number(value, name, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('INVALID_NUMBER ' + name)
    if positive and value <= 0:
        raise ValueError('NONPOSITIVE ' + name)
    return float(value)


def vector(value, name):
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError('INVALID_VECTOR ' + name)
    return [number(x, name) for x in value]


def check_timebase(tb):
    fps = number(tb['fps'], 'fps', True)
    frames = tb['frames']
    if isinstance(frames, bool) or not isinstance(frames, int) or frames < 2:
        raise ValueError('INVALID_FRAME_RANGE')
    return fps, frames


def check_knots(knots, frames, value_key):
    if len(knots) < 2:
        raise ValueError('TOO_FEW_KNOTS')
    for k in knots:
        f = k['frame']
        if isinstance(f, bool) or not isinstance(f, int) or not 1 <= f <= frames:
            raise ValueError('INVALID_KNOT_FRAME')
        number(k[value_key], value_key)
    if any(b['frame'] - a['frame'] < 2 for a, b in zip(knots, knots[1:])):
        raise ValueError('PHASE_NEEDS_TWO_FRAME_INTERVAL')


def pose_channels(spec, first, last, frames):
    channels = spec.get('pose_channels', {})
    if set(channels) - POSE_CHANNELS:
        raise ValueError('UNKNOWN_POSE_CHANNEL')
    for name, keys in channels.items():
        check_knots(keys, frames, 'value')
        if keys[0]['frame'] != first or keys[-1]['frame'] != last:
            raise ValueError('POSE_MUST_COVER_EXPRESSION ' + name)
        if name == 'compression' and any(k['value'] <= 0 for k in keys):
            raise ValueError('NONPOSITIVE_COMPRESSION')
    return channels


def sample_channel(keys, frame):
    if frame <= keys[0]['frame']:
        return keys[0]['value']
    if frame >= keys[-1]['frame']:
        return keys[-1]['value']
    for a, b in zip(keys, keys[1:]):
        if a['frame'] <= frame <= b['frame']:
            u = smooth((frame-a['frame'])/(b['frame']-a['frame']))
            return a['value'] + (b['value']-a['value'])*u


def compile_travel(spec, timebase):
    """Fit a relative speed envelope to an explicit horizontal route and time.

    A range target is an author constraint; infeasible route/time is rejected,
    never silently retimed. Bézier paths use existing arc-length sampling.
    """
    fps, frames = check_timebase(timebase)
    if not spec.get('id') or not spec.get('actor') or not spec.get('provenance'):
        raise ValueError('MISSING_ID_ACTOR_PROVENANCE')
    height = number(spec['body_height'], 'body_height', True)
    meters = number(spec['meters_per_unit'], 'meters_per_unit', True)
    points = [vector(p, 'route') for p in spec['points']]
    kind = spec.get('path_type', 'LINEAR')
    if kind not in ('LINEAR', 'BEZIER_SIMPLE'):
        raise ValueError('USE_SMOOTH_ROUTE_OR_SEPARATE_STOPPED_SEGMENTS')
    if not points or max(p[2] for p in points)-min(p[2] for p in points) > 1e-7:
        raise ValueError('GROUNDED_PLANAR_ONLY_USE_TAKEOFF_LAND_FOR_FLIGHT')
    length, curve = arclength_path(points, kind)
    if length <= 1e-8:
        raise ValueError('ZERO_ROUTE')
    if any(norm(sub(b,a)) <= 1e-8 for a,b in zip(points,points[1:])):
        raise ValueError('DEGENERATE_ROUTE_TANGENT')
    knots = copy.deepcopy(spec['speed_knots'])
    check_knots(knots, frames, 'weight')
    if any(k['weight'] < 0 for k in knots):
        raise ValueError('NEGATIVE_SPEED_WEIGHT')
    area = sum((a['weight']+b['weight'])*.5*(b['frame']-a['frame'])/fps
               for a,b in zip(knots,knots[1:]))
    if area <= 1e-10:
        raise ValueError('ZERO_SPEED_ENVELOPE')
    factor = length/area
    peak = max(k['weight'] for k in knots)*factor
    target = spec.get('peak_speed_range_hps')
    if target is not None:
        if len(target)!=2 or number(target[0], 'minimum')<0 or number(target[1], 'maximum')<target[0]:
            raise ValueError('INVALID_SPEED_RANGE')
        if not target[0]-1e-7 <= peak/height <= target[1]+1e-7:
            raise ValueError('ROUTE_TIME_SPEED_CONFLICT: derived %.4f body-heights/s' % (peak/height))
    first, last = knots[0]['frame'], knots[-1]['frame']
    channels = pose_channels(spec, first, last, frames)
    facing = spec.get('facing', {'mode':'TANGENT'})
    if facing['mode'] not in ('FIXED','TANGENT'):
        raise ValueError('UNSUPPORTED_FACING')
    if facing['mode']=='FIXED':
        number(facing['yaw_deg'], 'yaw_deg')
    scalar_spec = dict(id=spec['id'], actor=spec['actor'], intensity_class='BURST',
                       trend='APPROACH', direction=[1,0,0], start_position=[0,0,0],
                       provenance=spec['provenance'], facing_yaw=-90,
                       knots=[dict(frame=k['frame'], speed=k['weight']*factor,
                                   phase=k.get('phase','CRUISE')) for k in knots])
    scalar = scalar_envelope(scalar_spec, dict(fps=fps, duration=frames/fps,
                                             frame_origin=1, time_unit='seconds'),
                             spec.get('boundary_policy','LEGACY_STRICT'))
    rows=[]; previous_yaw=None
    for r in scalar['rows']:
        u=max(0.,min(1.,r['position'][0]/length))
        tangent=unit(sub(curve(min(1.,u+1e-5)),curve(max(0.,u-1e-5))))
        if norm(tangent)<.5:
            raise ValueError('ROUTE_CUSP_REQUIRES_EXPLICIT_REDESIGN')
        yaw=facing['yaw_deg'] if facing['mode']=='FIXED' else math.degrees(math.atan2(-tangent[0],tangent[1]))
        if previous_yaw is not None:
            yaw=previous_yaw+(yaw-previous_yaw+180)%360-180
        state=dict(position=curve(u),yaw=yaw,grounded=True)
        state.update({ch:sample_channel(keys,r['frame']) for ch,keys in channels.items()})
        rows.append(dict(frame=r['frame'],state=state))
        previous_yaw=yaw
    speeds=[norm(sub(b['state']['position'],a['state']['position']))*fps for a,b in zip(rows,rows[1:])]
    return dict(expression_version='ACTION-EXPRESSION/1', kind='TRAVEL',
                id=spec['id'],actor=spec['actor'],timebase=copy.deepcopy(timebase),
                spec=copy.deepcopy(spec),rows=rows,
                writes=['position','yaw','grounded']+sorted(channels),
                entry_speed=knots[0]['weight']*factor,exit_speed=knots[-1]['weight']*factor,
                metrics=dict(route_length=length,route_meters=length*meters,
                             duration_s=(last-first)/fps,peak_speed_units_s=peak,
                             peak_speed_m_s=peak*meters,peak_speed_body_heights_s=peak/height,
                             sampled_peak_speed=max(speeds),
                             frame_phase_knots=[k['frame'] for k in knots]),
                kernel_evidence=scalar['bundle'],
                boundary_policy=scalar['policy'],analytic_scalar_c0_c1=scalar['analytic_scalar_c0_c1'],
                evidence_scope='S51 scalar continuity; mapped route/body/native and visual review separate',
                visual_review='NOT_REVIEWED')


def compile_impact(spec, timebase, source_rows):
    """Author-controlled recoil/slide, arbitrary horizontal direction.

    Requires a planned source/contact and source approach at the contact frame.
    This compiles the consequence; native contact must still be verified.
    Initially stationary receiver only. No automatic mass/friction or falling.
    """
    fps, frames = check_timebase(timebase)
    contact=spec['contact'];frame=contact['frame']
    if not isinstance(frame,int) or isinstance(frame,bool) or not 2<=frame<frames:
        raise ValueError('INVALID_CONTACT_FRAME')
    if not contact.get('event_id') or not contact.get('source_actor') or contact.get('target_actor')!=spec['actor'] or contact['source_actor']==spec['actor']:
        raise ValueError('MISSING_CONTACT_CAUSE')
    source={r['frame']:r for r in source_rows}
    if frame not in source or frame-1 not in source:
        raise ValueError('MISSING_SOURCE_MOTION')
    if any(source[f].get('actor')!=contact['source_actor'] for f in (frame-1,frame)):
        raise ValueError('SOURCE_IDENTITY_MISMATCH')
    incoming=sub(source[frame]['position'],source[frame-1]['position'])
    direction=unit(vector(spec['direction'],'direction'))
    if norm(direction)<.5 or abs(direction[2])>1e-8:
        raise ValueError('HORIZONTAL_IMPACT_ONLY')
    if norm(incoming)*fps <= 1e-6:
        raise ValueError('SOURCE_NOT_MOVING')
    alignment=sum(x*y for x,y in zip(unit(incoming),direction))
    if alignment<.5 and not spec.get('redirect_reason'):
        raise ValueError('REDIRECT_REQUIRES_AUTHOR_REASON')
    if spec.get('response_kind') not in ('RECOIL','SLIDE','BRACED','DEFLECT'):
        raise ValueError('UNSUPPORTED_RESPONSE_KIND')
    height=number(spec['body_height'],'height',True)
    peak=number(spec['response_speed_hps'],'response_speed_hps',True)*height
    phase=spec['phase_frames']
    if len(phase)!=4 or phase[0]!=frame:
        raise ValueError('IMPACT_REQUIRES_CONTACT_RISE_COAST_STOP_FRAMES')
    keys=[dict(frame=f,weight=w,phase=p) for f,w,p in zip(phase,[0,1,1,0],['PREPARE','ACCELERATE','CRUISE','DECELERATE'])]
    check_knots(keys,frames,'weight')
    duration_weight=sum((a['weight']+b['weight'])*.5*(b['frame']-a['frame'])/fps for a,b in zip(keys,keys[1:]))
    distance=peak*duration_weight
    origin=vector(spec['start_position'],'start_position')
    stop=[x+d*distance for x,d in zip(origin,direction)]
    travel=dict(id=spec['id'],actor=spec['actor'],provenance=spec['provenance'],
                body_height=height,meters_per_unit=spec['meters_per_unit'],
                points=[origin,stop],speed_knots=keys,facing=spec['facing'],
                boundary_policy=spec.get('boundary_policy','LEGACY_STRICT'),
                pose_channels=spec.get('pose_channels',{}))
    result=compile_travel(travel,timebase)
    result.update(kind='IMPACT_RESPONSE',spec=copy.deepcopy(spec),
                  contact=copy.deepcopy(contact),planned_contact_only=True,
                  source_incoming_speed=norm(incoming)*fps)
    result['metrics']['response_distance_body_heights']=distance/height
    return result


def full_track(compiled, total_frames):
    """For NEW candidate tracks only; no arbitrary freezing of moving endpoints."""
    rows=compiled['rows'];first,last=rows[0]['frame'],rows[-1]['frame']
    if total_frames < last or total_frames!=compiled['timebase']['frames']:
        raise ValueError('TRACK_TIMEBASE_MISMATCH')
    if (first>1 and compiled['entry_speed']>1e-7) or (last<total_frames and compiled['exit_speed']>1e-7):
        raise ValueError('MOVING_ENDPOINT_NEEDS_CONTINUATION')
    index={r['frame']:r['state'] for r in rows}
    return [dict(frame=f,state=copy.deepcopy(index.get(f,rows[0 if f<first else -1]['state']))) for f in range(1,total_frames+1)]


def patch_csp(csp, compiled, *, allowed_actors, locked_channels=None):
    """Local, rejoining pose-track patch. Never edits cameras, props or other actors.

    Caller audits attachments/contact/support dependencies before use. Root
    boundary positions and finite-difference velocities must rejoin old tracks.
    """
    actor=compiled['actor'];locks=(locked_channels or {}).get(actor,[])
    if actor not in allowed_actors or '*' in locks or set(locks)&set(compiled['writes']):
        raise ValueError('BLOCKED_BY_SCOPE_OR_LOCK')
    if csp.get('layout_mode')!='COMBAT_DYNAMIC' or csp.get('scene_asset'):
        raise ValueError('USE_EXISTING_SCENE_ADAPTER_FOR_BAKED_SCENES')
    if csp['timebase']!=compiled['timebase']:
        raise ValueError('TIMEBASE_MISMATCH')
    original=csp['actor_pose_tracks'][actor]
    index={r['frame']:r['state'] for r in original}
    new={r['frame']:r['state'] for r in compiled['rows']}
    first,last=min(new),max(new)
    if any(f not in index for f in new):
        raise ValueError('DENSE_EXISTING_TRACK_REQUIRED')
    for f in (first,last):
        for ch in compiled['writes']:
            a=index[f].get(ch,1 if ch=='compression' else True if ch=='grounded' else 0)
            b=new[f][ch]
            error=norm(sub(a,b)) if ch=='position' else abs(a-b)
            if ch=='yaw': error=abs((a-b+180)%360-180)
            if error>1e-5:raise ValueError('PATCH_BOUNDARY_MISMATCH '+ch)
    fps=csp['timebase']['fps']
    for f,neighbor in ((first,first+1),(last,last-1)):
        # Preserve old edge displacement; a local patch cannot introduce a new seam.
        if norm(sub(sub(new[f]['position'],new[neighbor]['position']),
                    sub(index[f]['position'],index[neighbor]['position'])))*fps>1e-4:
            raise ValueError('PATCH_VELOCITY_BOUNDARY_MISMATCH')
        for ch in set(compiled['writes'])-{'position','grounded'}:
            default=1 if ch=='compression' else 0
            delta=(new[f][ch]-new[neighbor][ch])-(index[f].get(ch,default)-index[neighbor].get(ch,default))
            if ch=='yaw':delta=(delta+180)%360-180
            if abs(delta)*fps>1e-4:raise ValueError('PATCH_POSE_VELOCITY_BOUNDARY_MISMATCH '+ch)
    result=copy.deepcopy(csp)
    for row in result['actor_pose_tracks'][actor]:
        if row['frame'] in new:
            row['state'].update(copy.deepcopy(new[row['frame']]))
    for gate in result.get('review_gates',{}).values():
        gate.update(status='NOT_REVIEWED',evidence=[],reason='Action expression changed; recheck dependencies and output')
    return result


def contact_evidence(rows, contact_frame, tolerance):
    """Native point/region witness only, NOT a mesh swept-collision solver."""
    number(tolerance,'contact tolerance',True)
    row=next((r for r in rows if r['frame']==contact_frame),None)
    if row is None or row.get('source_point') is None or row.get('target_point') is None:
        return dict(status='NOT_REVIEWED',reason='MISSING_NATIVE_CONTACT_WITNESS')
    gap=norm(sub(vector(row['source_point'],'source'),vector(row['target_point'],'target')))
    return dict(status='PASS' if gap<=tolerance else 'FAIL',gap=gap,tolerance=tolerance,
                scope='explicit native control-point contact, not anatomical collision')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('plan');parser.add_argument('--output',required=True)
    args=parser.parse_args();plan=json.loads(Path(args.plan).read_text(encoding='utf-8'))
    operation=plan.get('operation','TRAVEL')
    if operation=='TRAVEL':result=compile_travel(plan['spec'],plan['timebase'])
    elif operation=='IMPACT_RESPONSE':result=compile_impact(plan['spec'],plan['timebase'],plan['source_rows'])
    else:raise ValueError('UNKNOWN_OPERATION')
    out=Path(args.output)
    if out.exists():raise FileExistsError('Use a new versioned output')
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps(result['metrics'],ensure_ascii=False))
