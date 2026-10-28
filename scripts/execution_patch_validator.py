"""Validate sparse execution patches against recomputed scope and fresh inputs."""
from s2_common import digest,schema_check,selector_paths,get,differences,parts
from change_analyzer import analyze,apply_changeset
from author_graph_validator import require_valid

def check_updated_graph(base,updated,changeset,scope,resolution=None):
    require_valid(updated)
    direct=apply_changeset(base,changeset)
    for c in changeset['changes']:
        table,key=('events','event_id') if c['change_type'].startswith('EVENT_') else ('shot_intents','shot_id') if c['change_type']=='SHOT_INTENT_CHANGE' else ('overrides','override_id')
        row=next(v for v in updated[table] if v[key]==c['target'])
        actual=[row[k] for k in ('start','peak','end')] if c['channel']=='time_range' else row[c['channel']]
        if digest(actual)!=digest(c['new_value']):raise ValueError('CHANGESET_RESULT_MISMATCH: '+c['change_id'])
    released={x['override_id'] for x in (resolution or {}).get('resolutions',[]) if x['decision'] in ('RELEASE','REPLACE_LOCK')}
    for path in differences(direct,updated):
        pp=parts(path);allowed=False
        if pp[0]=='events':
            e=updated['events'][int(pp[1])]
            allowed=e['event_id'] in scope['affected_events'] and pp[2] in ('start','peak','end','world_intent','screen_intent','result')
        if pp[0]=='shot_intents':
            s=updated['shot_intents'][int(pp[1])]
            allowed=s['shot_id'] in scope['affected_shots'] and pp[2] in ('primary_information','camera_behavior_intent','screen_direction_intent','shot_size_intent')
        if pp[0]=='overrides':allowed=updated['overrides'][int(pp[1])]['override_id'] in released and pp[2]=='status'
        if not allowed:raise ValueError('STALE: untracked author/topology edit '+path)

def validate_patch(base,patch,graph,updated_graph,changeset,binding,scope,registry,resolution=None):
    schema_check(patch,'execution-patch.schema.json')
    checks=[('BASE_CSP_HASH_MISMATCH','base_csp_sha256',digest(base)),('AUTHOR_GRAPH_HASH_MISMATCH','author_graph_sha256',digest(updated_graph)),
      ('STALE_CHANGESET','changeset_sha256',digest(changeset)),('STALE_AFFECTED_SCOPE','affected_scope_sha256',digest(scope)),
      ('STALE_EXECUTION_BINDING','execution_binding_sha256',digest(binding)),('STALE_OVERRIDE_REGISTRY','override_registry_sha256',digest(registry))]
    for error,key,expected in checks:
        if patch[key]!=expected:raise ValueError(error)
    recomputed,_=analyze(graph,changeset,binding,base,registry,enforce_locks=False)
    if digest(recomputed)!=digest(scope):raise ValueError('TAMPERED_AFFECTED_SCOPE')
    check_updated_graph(graph,updated_graph,changeset,scope,resolution)
    if changeset.get('execution_repair'):
        from repair_to_changeset import validate_execution_authorization
        validate_execution_authorization(base,patch,graph,updated_graph,changeset,binding,registry,resolution)
    allowed={r['region_id']:set(selector_paths(base,r)) for r in scope['affected_execution_channels']}
    bysection={}
    for r in scope['affected_execution_channels']:bysection.setdefault(r['section'],set()).update(allowed[r['region_id']])
    paths=set();sections=set()
    for op in patch['execution_payload']:
        path=op['path'];section=op['section']
        if path in paths:raise ValueError('Duplicate execution write')
        paths.add(path);sections.add(section)
        if path not in bysection.get(section,set()):raise ValueError('PATCH_OUTSIDE_AFFECTED_SCOPE: '+path)
        if digest(get(base,path))!=digest(op['old_value']):raise ValueError('STALE_PATCH_OLD_VALUE: '+path)
        if digest(op['old_value'])==digest(op['new_value']):raise ValueError('UNCHANGED_PAYLOAD_FORBIDDEN: '+path)
    if set(patch['modified_sections'])!=sections:raise ValueError('Undeclared/misdeclared patch section')
    decisions={d['region_id']:d for d in patch['region_decisions']}
    if len(decisions)!=len(patch['region_decisions']) or decisions.keys()!=allowed.keys():raise ValueError('INCOMPLETE_LOWERING: every dirty region needs an explicit disposition')
    for key,owned in allowed.items():
        updated=bool(paths & owned)
        if (decisions[key]['status']=='UPDATED')!=updated:raise ValueError('Region disposition contradicts actual patch: '+key)
    if not paths and any(c['change_type']!='OVERRIDE_CHANGE' for c in changeset['changes']):raise ValueError('EMPTY_EXECUTION_PATCH')
    return paths
