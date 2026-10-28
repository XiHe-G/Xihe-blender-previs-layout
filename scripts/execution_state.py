"""Explicit approved execution binding and CLEAN/DIRTY/STALE/LOCKED states."""
from copy import deepcopy
from s2_common import digest,selector_paths,projection
from author_graph_validator import require_valid
from combat_sequence_package import validate as validate_csp


def make_binding(graph,csp,regions,event_ids,shot_ids,*,provenance):
    require_valid(graph)
    errors=validate_csp(csp)
    if errors: raise ValueError('; '.join(errors))
    if graph['graph_id']!=csp['sequence_id']: raise ValueError('Binding sequence mismatch')
    if set(event_ids)!={e['event_id'] for e in graph['events']} or set(event_ids.values())!={e['event_id'] for e in csp['action_beats']} or len(set(event_ids.values()))!=len(event_ids):
        raise ValueError('Event binding must be a complete bijection')
    if set(shot_ids)!={s['shot_id'] for s in graph['shot_intents']} or set(shot_ids.values())!={s['id'] for s in csp['shot_plan']} or len(set(shot_ids.values()))!=len(shot_ids):
        raise ValueError('Shot binding must be a complete bijection')
    owners={x['event_id'] for x in graph['events']}|{x['shot_id'] for x in graph['shot_intents']}|{x['id'] for x in graph['entities']}
    ids=set()
    for region in regions:
        if region['owner'] not in owners: raise ValueError('Invalid region owner')
        if not set(region.get('entities',[])).issubset({e['id'] for e in graph['entities']}):raise ValueError('Unknown affected entity in execution index')
        if region['region_id'] in ids: raise ValueError('Duplicate region ID')
        ids.add(region['region_id']);selector_paths(csp,region)
    return dict(binding_version='S2-EXECUTION-BINDING/1.0',graph_sha256=digest(graph),csp_sha256=digest(csp),
                regions=deepcopy(regions),event_ids=event_ids,shot_ids=shot_ids,provenance=provenance)


def from_s1(graph,graph_path,regions,event_ids,shot_ids):
    from author_graph_to_csp import compile_graph
    csp=compile_graph(graph,graph_path)
    return csp,make_binding(graph,csp,regions,event_ids,shot_ids,provenance='Explicit S2 ownership index on validated S1 execution binding')


def assess(graph,csp,binding,scope=None,registry=None):
    if binding['csp_sha256']!=digest(csp): return dict(status='STALE',reason='CSP diverged from binding; register manual edits explicitly')
    matches=binding['graph_sha256']==digest(graph)
    if not matches and (not scope or scope.get('base_graph_sha256')!=binding['graph_sha256'] or scope.get('request_graph_sha256')!=digest(graph)):
        return dict(status='STALE',reason='Untracked graph change or dependency topology changed; full lowering required')
    dirty=set(scope.get('region_ids',[]) if scope else [])
    locked={p for lock in (registry or {}).get('overrides',[]) if lock['status']=='LOCKED' for p in projection(csp,lock['protections'])}
    states={}
    for r in binding['regions']:
        paths=set(selector_paths(csp,r))
        states[r['region_id']]='LOCKED' if paths & locked else 'DIRTY' if r['region_id'] in dirty else 'CLEAN'
    return dict(status='DIRTY' if dirty else 'CLEAN',regions=states,locked_channels=len(locked))
