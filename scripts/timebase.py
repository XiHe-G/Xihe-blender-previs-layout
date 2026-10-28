"""Author Graph global seconds / CSP frame mapping. No shot-local clocks."""
from decimal import Decimal, ROUND_HALF_EVEN
import math


def _number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(label + ' must be a finite number')
    return value


def _check(fps, frame_origin):
    if _number(fps, 'fps') <= 0 or int(fps) != fps:
        raise ValueError('CSP/1.0 requires positive integer fps')
    if isinstance(frame_origin, bool) or frame_origin != 1:
        raise ValueError('CSP/1.0 requires frame_origin=1')


def time_to_frame(time_s, fps, frame_origin=1):
    """Nearest frame, ties to even; decimal arithmetic makes ties reproducible.

    End-exclusive duration maps to N+1, not the final sample N.
    """
    _check(fps, frame_origin)
    if _number(time_s, 'time') < 0:
        raise ValueError('Negative global time')
    return frame_origin + int((Decimal(str(time_s)) * Decimal(str(fps))).to_integral_value(rounding=ROUND_HALF_EVEN))


def frame_to_time(frame, fps, frame_origin=1):
    _check(fps, frame_origin)
    if isinstance(frame, bool) or not isinstance(frame, int) or frame < frame_origin:
        raise ValueError('Frame must be an integer >= frame_origin')
    return (frame - frame_origin) / fps


def duration_frames(duration, fps):
    n = time_to_frame(duration, fps) - 1
    if n < 1 or abs(duration - n / fps) > 1e-9:
        raise ValueError('Duration must span an integer number of frames')
    return n


# Explicit project-level alignment; old time_to_frame remains byte-for-byte semantic compatible.
def align_author_time(author_time, fps, policy, max_error):
    from decimal import ROUND_FLOOR, ROUND_CEILING
    _check(fps,1);_number(author_time,'author_time');_number(max_error,'max_error')
    if author_time<0 or max_error<0:raise ValueError('INVALID_TIME_ALIGNMENT_INPUT')
    modes={'NEAREST_FRAME':ROUND_HALF_EVEN,'FLOOR_FRAME':ROUND_FLOOR,'CEIL_FRAME':ROUND_CEILING}
    if policy=='SUBFRAME_IF_SUPPORTED':raise ValueError('SUBFRAME_UNSUPPORTED_BY_CSP_SAMPLING')
    if policy not in modes:raise ValueError('TIME_ALIGNMENT_POLICY_REQUIRED')
    n=int((Decimal(str(author_time))*Decimal(str(fps))).to_integral_value(rounding=modes[policy]))
    frame=n+1;execution_time=frame_to_time(frame,fps);error=execution_time-author_time
    if abs(error)>max_error+1e-12:raise ValueError('NEEDS_AUTHOR_INPUT: MAX_TIME_QUANTIZATION_ERROR')
    return dict(author_time=author_time,execution_frame=frame,execution_time=execution_time,quantization_error=error,policy=policy,max_time_quantization_error=max_error,tie_rule='ROUND_HALF_EVEN',requirement_source='TECHNICAL_DEFAULT TIME-ALIGNMENT/1.0')


def align_execution_graph(graph, settings):
    import copy
    if not settings or 'time_alignment_policy' not in settings:raise ValueError('TIME_ALIGNMENT_POLICY_REQUIRED')
    out=copy.deepcopy(graph);fps=graph['timebase']['fps'];maps=[]
    def align(value,source):
        item=align_author_time(value,fps,settings['time_alignment_policy'],settings['max_time_quantization_error']);item['source']=source;maps.append(item);return item['execution_time']
    for e in out['events']:
        for k in ('start','peak','end'):e[k]=align(e[k],e['event_id']+'.'+k)
        if e['end']<=e['start']:raise ValueError('TIME_ORDER_COLLISION')
    for s in out['shot_intents']:s['time_range']=[align(t,s['shot_id']+'.time_range') for t in s['time_range']]
    ordered=sorted(maps,key=lambda x:x['author_time'])
    for a,b in zip(ordered,ordered[1:]):
        if a['author_time']<b['author_time'] and a['execution_frame']>=b['execution_frame']:raise ValueError('TIME_ORDER_COLLISION')
    return out,maps
