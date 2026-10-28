"""LOCKED protection before writes; explicit, hash-bound resolutions only."""
from copy import deepcopy
from s2_common import digest,projection,schema_check

class OverrideConflict(ValueError):
    pass

def register_override(registry,override,csp,protections,source):
    if override['status']!='LOCKED': raise ValueError('Registration captures LOCKED values only')
    if not source.get('reason') or not source.get('version') or not source.get('source') or not source.get('blend_sha256'):
        raise ValueError('Manual registration requires version, source, reason and engineering fingerprint')
    if override['scope']=='SHOT' and override['channel']=='camera_transform' and not isinstance(source.get('parent_chain'),list):
        raise ValueError('Camera lock requires explicit inspected parent_chain (empty for unparented Camera)')
    r=deepcopy(registry)
    if any(x['override_id']==override['override_id'] for x in r['overrides']): raise ValueError('Duplicate override')
    record=deepcopy(override);record.update(protections=deepcopy(protections),source=source,
        protected_sha256=digest(projection(csp,protections)))
    r['overrides'].append(record);return r

def verify_registry(registry,csp):
    if registry.get('registry_version')!='OVERRIDE-REGISTRY/1.0': raise ValueError('Invalid override registry')
    ids=set()
    for lock in registry['overrides']:
        if lock['override_id'] in ids: raise ValueError('Duplicate override')
        ids.add(lock['override_id'])
        if lock['status'] not in ('LOCKED','RELEASED','PROPOSED'):raise ValueError('Invalid lock status')
        if lock['status']=='LOCKED' and lock['protected_sha256']!=digest(projection(csp,lock['protections'])):
            raise ValueError('LOCKED_BASE_DIVERGED: '+lock['override_id'])

def resolve_registry(registry,resolution,patch_id):
    r=deepcopy(registry);replacements=[]
    if resolution is None:return r,replacements
    schema_check(resolution,'override-resolution.schema.json')
    if resolution['base_registry_sha256']!=digest(registry) or resolution['patch_id']!=patch_id: raise ValueError('STALE_OVERRIDE_RESOLUTION')
    seen=set()
    for d in resolution['resolutions']:
        if d['override_id'] in seen:raise ValueError('Duplicate override resolution')
        seen.add(d['override_id'])
        found=[x for x in r['overrides'] if x['override_id']==d['override_id']]
        if len(found)!=1:raise ValueError('Unknown override resolution target')
        lock=found[0]
        if d['decision'] in ('RELEASE','REPLACE_LOCK'):
            lock['status']='RELEASED'
            lock['resolution_authority']=deepcopy(d['authorization'])
            if d['decision']=='REPLACE_LOCK': replacements.append(lock['override_id'])
    return r,replacements

def protect(registry,csp,paths,patch_id,changed_authors=()):
    paths=set(paths)
    for lock in registry['overrides']:
        if lock['status']!='LOCKED':continue
        hit=paths & set(projection(csp,lock['protections']))
        author_hit=any(c['target']==lock['override_id'] or (c['target']==lock['target'] and
          (c['channel']==lock['channel'] or c['change_type']=='SHOT_INTENT_CHANGE' and lock['channel']=='camera_transform' and c['channel'] in ('camera_behavior_intent','shot_size_intent','screen_direction_intent'))) for c in changed_authors)
        if hit or author_hit:
            raise OverrideConflict('OVERRIDE_CONFLICT '+str(dict(override=lock['override_id'],target=lock['target'],channel=lock['channel'],patch=patch_id,paths=sorted(hit)[:3])))

def finish_registry(registry,replacements,csp):
    r=deepcopy(registry)
    for lock in r['overrides']:
        if lock['override_id'] in replacements:
            lock['status']='LOCKED';lock['protected_sha256']=digest(projection(csp,lock['protections']))
            lock['source']={**lock['source'],'source':'EXPLICIT_REPLACE_LOCK','csp_sha256':digest(csp)}
    verify_registry(r,csp);return r
