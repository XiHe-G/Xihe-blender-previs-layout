"""Explicit AG identity registration; only custom properties are written.

Native properties prove persistence of a registration, not independently inferred ownership.
The manifest is deliberately separate from CSP execution semantics.
"""
import json,hashlib

KEYS={'previs_entity_id','previs_owner_id','previs_event_id','previs_projectile_id','previs_weapon_id','previs_role'}

def instrument(scene,manifest):
    if manifest.get('schema_version')!='RUNTIME-IDENTITY/1.0':raise ValueError('INVALID_IDENTITY_MANIFEST')
    objects={o.name:o for o in scene.objects};entries=manifest['objects']
    ids={p['previs_entity_id'] for p in entries.values()}
    for name,props in entries.items():
        if name not in objects:raise ValueError('IDENTITY_OBJECT_MISSING '+name)
        if set(props)!=KEYS or any(not isinstance(v,str) for v in props.values()):raise ValueError('INVALID_IDENTITY_PROPERTIES '+name)
        if props['previs_owner_id'] and props['previs_owner_id'] not in ids:raise ValueError('IDENTITY_OWNER_MISSING '+name)
    for name,props in entries.items():
        for key,value in props.items():objects[name][key]=value
    return dict(schema_version=manifest['schema_version'],object_count=len(entries),manifest_sha256=hashlib.sha256(json.dumps(manifest,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),behavior_changes=False)

def identity(root,spec):
    native=root.get('previs_entity_id');owner=root.get('previs_owner_id') or None
    return dict(entity_id=native or spec['entity_id'],registered_entity_id=spec['entity_id'],
      identity_evidence='NATIVE_OBJECT_PROPERTY' if native else 'REGISTERED_BINDING',
      ownership_evidence='NATIVE_OBJECT_PROPERTY' if owner else 'REGISTERED_BINDING' if spec.get('owner_id') else 'UNKNOWN',
      identity_strength='STRONG_REGISTRATION_EVIDENCE' if native else 'WEAK_EVIDENCE',
      native_owner=owner)
