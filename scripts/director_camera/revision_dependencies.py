"""Conservative render invalidation. No project names, coordinates, or shot IDs."""
GLOBAL_CHANNELS=frozenset({'world','shared_lighting','shared_material','shared_scene'})
LOCAL_CHANNELS=frozenset({'camera','action','prop','local_scene','caption'})

def render_dependencies(shots, changes):
    """Return ordered render IDs and caption-only IDs; fail closed on unknown scope.

    shots: [{'id': unique str, 'start': int, 'end': int}].
    changes: [{'channel': str, 'frames': [first,last]}]; global channels need no range.
    A local change without a reliable influence range invalidates all shots.
    Caller must include constraint/parent/transition dependencies in frames.
    """
    ids=[s['id'] for s in shots]
    if len(ids)!=len(set(ids)):raise ValueError('duplicate shot ID')
    if any(s['start']>s['end'] for s in shots):raise ValueError('invalid shot interval')
    render=set();captions=set();reasons={i:[] for i in ids}
    for change in changes:
        channel=change['channel']
        if channel not in GLOBAL_CHANNELS|LOCAL_CHANNELS:raise ValueError('unknown channel')
        span=change.get('frames')
        if span is not None and (len(span)!=2 or span[0]>span[1]):raise ValueError('invalid influence range')
        affected=[s['id'] for s in shots if channel in GLOBAL_CHANNELS or span is None or s['start']<=span[1] and s['end']>=span[0]]
        (captions if channel=='caption' else render).update(affected)
        for i in affected:reasons[i].append(channel)
    return {'render':[i for i in ids if i in render], 'caption_only':[i for i in ids if i in captions-render], 'reuse':[i for i in ids if i not in render], 'reasons':reasons}

def copy_unparented_local_transform(source,target):
    """Unlinked library objects need not have an evaluated world matrix.

    Only supports unparented, unconstrained, undriven TRS objects. Other cases
    must be linked/evaluated by the caller, not silently treated as world space.
    """
    if source.parent or target.parent or source.constraints or target.constraints:
        raise ValueError('requires evaluated parent/constraint transfer')
    if any(obj.animation_data and obj.animation_data.drivers for obj in (source,target)):
        raise ValueError('driven transform requires evaluated transfer')
    target.location=source.location.copy();target.rotation_mode=source.rotation_mode
    if source.rotation_mode=='QUATERNION':target.rotation_quaternion=source.rotation_quaternion.copy()
    elif source.rotation_mode=='AXIS_ANGLE':target.rotation_axis_angle=tuple(source.rotation_axis_angle)
    else:target.rotation_euler=source.rotation_euler.copy()
    target.scale=source.scale.copy()
