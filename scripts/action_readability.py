"""Measure world and image motion separately. No automatic artistic PASS."""
import math
from statistics import mean
from action_expression import number, vector
from primitive_sampler import norm, sub


def measure_readability(rows, fps, body_height, meters_per_unit=1.0):
    fps=number(fps,'fps',True);height=number(body_height,'height',True)
    meters=number(meters_per_unit,'meters_per_unit',True)
    if len(rows)<2:
        return dict(status='NOT_REVIEWED',reason='INSUFFICIENT_SAMPLES')
    if any(not isinstance(r['frame'],int) for r in rows) or any(b['frame']<=a['frame'] for a,b in zip(rows,rows[1:])):
        raise ValueError('INVALID_FRAME_ORDER')
    world=[];screen=[];landmarks=[];scale=[];used=0;cuts=0
    for a,b in zip(rows,rows[1:]):
        if a.get('shot_id')!=b.get('shot_id'):
            cuts+=1;continue
        dt=(b['frame']-a['frame'])/fps
        world.append(norm(sub(vector(b['position'],'position'),vector(a['position'],'position')))/dt)
        if not (a.get('visible') is True and b.get('visible') is True):continue
        used+=1
        if a.get('center_uv') is not None and b.get('center_uv') is not None:
            screen.append(norm(sub(b['center_uv'],a['center_uv']))/dt)
        if a.get('height_uv',0)>0 and b.get('height_uv',0)>0:
            scale.append(abs(math.log(b['height_uv']/a['height_uv']))/dt)
        shared=set(a.get('landmark_uv',{}))&set(b.get('landmark_uv',{}))
        for key in shared:
            av,bv=a['landmark_uv'][key],b['landmark_uv'][key]
            if av is not None and bv is not None:
                landmarks.append(norm(sub(bv,av))/dt)
    def stats(values):
        return dict(mean=mean(values),peak=max(values)) if values else None
    return dict(status='MEASURED' if world else 'NOT_REVIEWED',
                world_speed_units_s=stats(world),world_speed_m_s=stats([v*meters for v in world]),
                world_speed_body_heights_s=stats([v/height for v in world]),
                actor_screen_uv_s=stats(screen),landmark_screen_uv_s=stats(landmarks),
                scale_log_change_s=stats(scale),visible_pair_fraction=used/max(1,len(rows)-1-cuts),
                cut_pairs_excluded=cuts,visual_review='NOT_REVIEWED',
                interpretation='Track center, environment flow, scale change and framing together; a centered tracking shot need not fail.')
