"""Channel ownership is checked before any samples are emitted."""
CHANNELS=('ROOT_LOCATION','ROOT_ROTATION','BODY_ROTATION','HEAD_ROTATION','WEAPON_TRANSFORM','PROJECTILE_TRANSFORM','ATTACHMENT_STATE','CAMERA_LOCATION','CAMERA_ROTATION','CAMERA_LENS')
MOTION=('MOVE_PROFILE','ORIENT_TO','APPROACH_TARGET','OFFSET_PATH','ATTACH_DETACH','RECOVERY_PROFILE')
CAMERA=('CAM_HOLD','CAM_REFRAME','CAM_FOLLOW','CAM_LEAD_LAG','CAM_PUSH_PULL','CAM_CATCH_UP')
def channels(p):
    typ=p['primitive_type'];q=p['parameters'];read=[]
    location=q.get('channel','ROOT_LOCATION')
    if typ in ('MOVE_PROFILE','OFFSET_PATH','RECOVERY_PROFILE'):write=[location]
    elif typ=='ORIENT_TO':write=[{'ROOT':'ROOT_ROTATION','BODY':'BODY_ROTATION','HEAD':'HEAD_ROTATION','WEAPON':'WEAPON_TRANSFORM'}[q.get('channel','BODY')]]
    elif typ=='APPROACH_TARGET':write=['ROOT_LOCATION','ROOT_ROTATION']
    elif typ=='ATTACH_DETACH':write=[q.get('channel','PROJECTILE_TRANSFORM'),'ATTACHMENT_STATE']
    elif typ in CAMERA:
        write=['CAMERA_LOCATION','CAMERA_ROTATION']
        if q.get('lens_policy')=='EXPLICIT_ZOOM':write.append('CAMERA_LENS')
    else:raise ValueError('UNKNOWN_PRIMITIVE')
    for k in ('target_entity','target','subject','owner','base_primitive','entry_from','parent_orientation_track'):
        if isinstance(q.get(k),str):read.append(q[k])
    if any(c not in CHANNELS for c in write):raise ValueError('UNKNOWN_CHANNEL')
    if typ=='RECOVERY_PROFILE' and 'orientation_recovery' in q:write.append('BODY_ROTATION')
    return {'READS':read,'READ_CHANNELS':{n:['ROOT_LOCATION','ROOT_ROTATION'] for n in read},'WRITES':write}
def validate_composition(primitives,operators):
    ids=[p['primitive_id'] for p in primitives]
    if len(ids)!=len(set(ids)):raise ValueError('DUPLICATE_PRIMITIVE_ID')
    for op in operators:
        if op['type'] not in ('SEQUENTIAL','ORTHOGONAL_CHANNEL','EXPLICIT_ADDITIVE_OFFSET'):raise ValueError('UNKNOWN_COMPOSITION')
        if len(op['members'])!=2 or any(x not in ids for x in op['members']):raise ValueError('INVALID_COMPOSITION_MEMBERS')
    for i,a in enumerate(primitives):
        for b in primitives[i+1:]:
            if a['actor']!=b['actor']:continue
            def effective_end(p):return float('inf') if p['primitive_type']=='OFFSET_PATH' and p['parameters'].get('return_mode')!='RETURN_TO_BASE' else p['end_time']
            overlap=min(effective_end(a),effective_end(b))-max(a['start_time'],b['start_time'])
            if overlap < -1e-9:continue
            common=set(channels(a)['WRITES'])&set(channels(b)['WRITES'])
            ops=[o for o in operators if set(o['members'])=={a['primitive_id'],b['primitive_id']}]
            if not common:
                if overlap>0 and not any(o['type']=='ORTHOGONAL_CHANNEL' for o in ops):raise ValueError('ORTHOGONAL_COMPOSITION_NOT_DECLARED')
                continue
            if abs(overlap)<1e-9 and any(o['type']=='SEQUENTIAL' for o in ops):continue
            if any(o['type']=='EXPLICIT_ADDITIVE_OFFSET' for o in ops):
                offset=a if a['primitive_type']=='OFFSET_PATH' else b
                base=b if offset is a else a
                if offset['primitive_type']=='OFFSET_PATH' and offset['parameters'].get('base_primitive')==base['primitive_id'] and common<= {'ROOT_LOCATION','PROJECTILE_TRANSFORM'}:continue
            raise ValueError('CHANNEL_CONFLICT '+a['primitive_id']+' '+b['primitive_id']+' '+','.join(sorted(common)))
