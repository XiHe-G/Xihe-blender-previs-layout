"""Changeset application and explicit dependency closure; no motion regeneration."""
import argparse
from copy import deepcopy
from s2_common import digest,schema_check,selector_paths,read,write
from author_graph_validator import require_valid
from override_guard import verify_registry,protect

EVENT_FIELDS={'EVENT_TIMING_CHANGE':{'start','peak','end','time_range'},'EVENT_SPATIAL_CHANGE':{'world_intent','screen_intent'}}
SHOT_FIELDS={'primary_information','shot_size_intent','screen_direction_intent','camera_behavior_intent','required_visibility','handoff_to_next'}

def apply_changeset(graph,changeset):
    schema_check(changeset,'changeset.schema.json');require_valid(graph)
    if changeset['base_graph_id']!=graph['graph_id'] or changeset['base_graph_sha256']!=digest(graph):raise ValueError('BASE_GRAPH_HASH_MISMATCH')
    repair=changeset.get('execution_repair')
    if repair:
        from repair_to_changeset import validate_relower
        validate_relower(graph,changeset)
    g=deepcopy(graph);ids=set();writes=set()
    for c in changeset['changes']:
        if c['change_id'] in ids or (c['target'],c['channel']) in writes:raise ValueError('Duplicate change/overlapping author write')
        ids.add(c['change_id']);writes.add((c['target'],c['channel']))
        kind=c['change_type'];field=c['channel']
        table,key=('events','event_id') if kind in EVENT_FIELDS else ('shot_intents','shot_id') if kind=='SHOT_INTENT_CHANGE' else ('overrides','override_id')
        allowed=EVENT_FIELDS[kind] if kind in EVENT_FIELDS else SHOT_FIELDS if kind=='SHOT_INTENT_CHANGE' else {'status'}
        if field not in allowed:raise ValueError('Unsupported change channel: '+field)
        matches=[v for v in g[table] if v[key]==c['target']]
        if len(matches)!=1:raise ValueError('INVALID_TARGET: '+c['target'])
        row=matches[0];old=[row[k] for k in ('start','peak','end')] if field=='time_range' else row[field]
        if digest(old)!=digest(c['old_value']):raise ValueError('STALE_OLD_VALUE: '+c['change_id'])
        if digest(old)==digest(c['new_value']) and not repair:raise ValueError('NO_OP_CHANGE: '+c['change_id'])
        if field=='time_range':
            if not isinstance(c['new_value'],list) or len(c['new_value'])!=3:raise ValueError('time_range requires start/peak/end')
            for k,v in zip(('start','peak','end'),c['new_value']):row[k]=v
        else:row[field]=deepcopy(c['new_value'])
    require_valid(g);return g

def analyze(graph,changeset,binding,csp,registry,*,enforce_locks=True):
    changed=apply_changeset(graph,changeset)
    if binding['binding_version']!='S2-EXECUTION-BINDING/1.0':raise ValueError('Unsupported execution binding')
    if binding['graph_sha256']!=digest(graph) or binding['csp_sha256']!=digest(csp):raise ValueError('STALE_EXECUTION_BINDING')
    verify_registry(registry,csp)
    events={e['event_id']:e for e in graph['events']};adj={k:[] for k in events}
    for d in graph['dependencies']:adj[d['depends_on']].append((d['event_id'],'DEPENDENCY',d['condition']))
    for e in graph['events']:
        if e['source_event']:adj[e['source_event']].append((e['event_id'],'SOURCE_EVENT',None))
    direct=list(dict.fromkeys(c['target'] for c in changeset['changes']));closure=set(k for k in direct if k in events)
    queue=sorted(closure);edges=[]
    while queue:
        parent=queue.pop(0)
        for child,kind,condition in adj[parent]:
            edges.append(dict(cause=parent,effect=child,edge_type=kind,condition=condition))
            if child not in closure:closure.add(child);queue.append(child)
    owners=closure|set(direct);regions=[r for r in binding['regions'] if r['owner'] in owners]
    if any(x in closure and not any(r['owner']==x for r in regions) for x in closure):raise ValueError('STALE: missing execution ownership for affected event')
    if any(c['change_type']=='SHOT_INTENT_CHANGE' and not any(r['owner']==c['target'] for r in regions) for c in changeset['changes']):raise ValueError('STALE: missing shot execution ownership')
    paths=sorted({p for r in regions for p in selector_paths(csp,r)})
    shots=set(c['target'] for c in changeset['changes'] if c['change_type']=='SHOT_INTENT_CHANGE')
    for r in regions:
        if 'frame_range' in r:
            for s in csp['shot_plan']:
                if r['frame_range'][0]<s['end_frame_exclusive'] and r['frame_range'][1]>=s['first_frame']:
                    shots.update(k for k,v in binding['shot_ids'].items() if v==s['id'])
        elif r['section'] in ('shot_execution','camera_choreography','screen_targets'):
            shots.update(k for k,v in binding['shot_ids'].items() if v==r['target'])
    entities=set()
    for r in regions:
        if 'entities' in r:entities.update(r['entities'])
        elif r['owner'] in events:entities.update(events[r['owner']]['actor']+events[r['owner']]['targets'])
    protected=[l['override_id'] for l in registry['overrides'] if l['status']=='LOCKED']
    if enforce_locks:protect(registry,csp,[],changeset['changeset_id'],[] if changeset.get('execution_repair') else changeset['changes'])
    scope=dict(scope_version='AFFECTED-SCOPE/1.0',base_graph_sha256=digest(graph),request_graph_sha256=digest(changed),base_csp_sha256=digest(csp),
        changeset_sha256=digest(changeset),execution_binding_sha256=digest(binding),override_registry_sha256=digest(registry),
        directly_changed=direct,dependent_events=sorted(closure-set(direct)),affected_events=sorted(closure),affected_entities=sorted(entities),
        affected_shots=sorted(shots),affected_execution_channels=deepcopy(regions),region_ids=[r['region_id'] for r in regions],allowed_paths=paths,
        protected_overrides=protected,unaffected_shots=sorted(set(binding['shot_ids'])-shots),
        unaffected_entities=sorted({e['id'] for e in graph['entities']}-entities),dependency_trace=edges,
        policy='Explicit dependency/source_event closure plus approved execution ownership; shot intersection only labels observations, never expands writable paths')
    return scope,changed

if __name__=='__main__':
    from combat_sequence_package import read_package
    ap=argparse.ArgumentParser()
    for flag in ['graph','changeset','binding','csp','registry','output']:ap.add_argument('--'+flag,required=True)
    a=ap.parse_args();scope,g=analyze(read(a.graph),read(a.changeset),read(a.binding),read_package(a.csp),read(a.registry));write(a.output,scope)
    print('AFFECTED_SCOPE',len(scope['region_ids']),'regions; execution still DIRTY until explicitly lowered')
