"""Perspective projected-center preflight; no pixel visibility or repair claims.

The S3.5 checker owns directional thresholds. Missing samples never disappear.
Radial directions remain unsupported until the checker has an audited contract.
"""
import math
from primitive_sampler import project
from motion_analysis import direction_summary
from plan_actual_checker import measured


def screen_trajectory(points, camera_positions, camera_orientations, lens=50., time_values=None):
    n = len(points)
    if n < 2 or len(camera_positions) != n or len(camera_orientations) != n:
        return {'status': 'NOT_REVIEWED', 'failure_code': 'UNALIGNED_PROJECTED_SAMPLES'}
    times = list(range(n)) if time_values is None else list(time_values)
    if len(times) != n or any(not math.isfinite(t) for t in times) or any(b <= a for a, b in zip(times, times[1:])):
        return {'status': 'NOT_REVIEWED', 'failure_code': 'INVALID_SAMPLE_TIMES'}
    if not math.isfinite(lens) or lens <= 0:
        return {'status': 'NOT_REVIEWED', 'failure_code': 'INVALID_LENS'}
    uv = [project(c, o, lens, p) for p, c, o in zip(points, camera_positions, camera_orientations)]
    result = {'screen_points': uv, 'sample_times': times, 'direction_basis': 'PROJECTED_CENTER',
              'camera_reference': 'PREDICTED_CAMERA_TRAJECTORY',
              'projection_contract': 'PERSPECTIVE_36MM_SENSOR_16_9_NO_SHIFT',
              'visibility_evidence': 'CENTER_ONLY_NOT_PIXEL_VISIBILITY'}
    if any(p is None or len(p) != 2 or not all(math.isfinite(v) for v in p) for p in uv):
        return dict(result, status='NOT_REVIEWED', failure_code='INCOMPLETE_PROJECTED_SAMPLES')
    d = direction_summary(uv)
    return dict(result, status='PASS', screen_delta=d['delta'], screen_path_length=d['path_length'],
                coherence=d['coherence'], projected_interval=[times[0], times[-1]])


def classify_direction(result, wanted, min_displacement=.02, region_range=None, tolerance=0.):
    if result.get('status') != 'PASS':
        return 'NOT_REVIEWED', result.get('failure_code', 'UNKNOWN')
    if wanted not in ('LEFT_TO_RIGHT', 'RIGHT_TO_LEFT', 'UP', 'DOWN', 'DIAGONAL', 'HOLD_REGION'):
        return 'NOT_REVIEWED', 'UNSUPPORTED_DIRECTION'
    if not math.isfinite(min_displacement) or min_displacement < 0 or not math.isfinite(tolerance) or tolerance < 0:
        return 'NOT_REVIEWED', 'INVALID_TOLERANCE'
    if wanted == 'HOLD_REGION':
        if region_range is None:
            return 'NOT_REVIEWED', 'MISSING_REGION_REQUIREMENT'
        if len(region_range) != 4 or not all(math.isfinite(x) for x in region_range) or not (0 <= region_range[0] <= region_range[2] <= 1 and 0 <= region_range[1] <= region_range[3] <= 1):
            return 'NOT_REVIEWED', 'INVALID_REGION_REQUIREMENT'
    points = result.get('screen_points')
    if not points or len(points) < 2:
        # Legacy delta-only callers retain negative diagnostics, never positive certification.
        delta = result.get('screen_delta')
        if delta is not None and wanted in ('LEFT_TO_RIGHT', 'RIGHT_TO_LEFT', 'UP', 'DOWN'):
            x, y = delta
            tests = {'LEFT_TO_RIGHT': x >= min_displacement and abs(y) <= abs(x),
                     'RIGHT_TO_LEFT': x <= -min_displacement and abs(y) <= abs(x),
                     'UP': y >= min_displacement and abs(x) <= abs(y),
                     'DOWN': y <= -min_displacement and abs(x) <= abs(y)}
            if not tests[wanted]:
                return 'SCREEN_SPACE_CONFLICT', 'WORLD_CAMERA_SCREEN_CONFLICT'
        return 'NOT_REVIEWED', 'PROJECTED_SAMPLES_REQUIRED'
    if any(p is None or len(p) != 2 or not all(math.isfinite(v) for v in p) for p in points):
        return 'NOT_REVIEWED', 'INCOMPLETE_PROJECTED_SAMPLES'
    if any(not (0 <= p[0] <= 1 and 0 <= p[1] <= 1) for p in points):
        return 'NOT_REVIEWED', 'CENTER_OUTSIDE_FRAME_BOUNDS_REQUIRED'
    # Adapter rows expose only point projection evidence, not occlusion or mesh area.
    rows = [{'shot_id': 'PREFLIGHT', 'frame': i, 'entities': {'SUBJECT': {
        'exists': True, 'screen_center': p,
        'screen_bounds': {'clipped_bounds': [p[0], p[1], p[0], p[1]], 'visible_fraction_estimate': 0.},
        'proxy_state': {'render_enabled': True}, 'occlusion_ratio': None}}} for i, p in enumerate(points)]
    o = {'type': 'SCREEN_DIRECTION', 'subjects': ['SUBJECT'], 'tolerance': tolerance,
         'expected_state': {'direction': wanted, 'min_displacement': min_displacement, 'region_range': region_range}}
    status, code, _, _ = measured(o, rows)
    if status == 'PASS':
        return 'PASS', code
    if status == 'FAIL':
        return 'SCREEN_SPACE_CONFLICT', 'WORLD_CAMERA_SCREEN_CONFLICT'
    return 'NOT_REVIEWED', code
