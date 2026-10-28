"""JSON Schema + referential/time/causal checks; no visual or user approval."""
import argparse
import json
import math
from pathlib import Path
from jsonschema import Draft202012Validator
from timebase import duration_frames, time_to_frame

ROOT = Path(__file__).resolve().parents[1]
COLLECTIONS = {'entities': 'id', 'shot_intents': 'shot_id', 'events': 'event_id',
               'constraints': 'constraint_id', 'overrides': 'override_id'}


def validate(graph, *, for_compile=False):
    schema = json.loads((ROOT / 'authoring/author-graph.schema.json').read_text(encoding='utf-8'))
    errors = [f"schema/{'/'.join(map(str, e.absolute_path))}: {e.message}"
              for e in Draft202012Validator(schema).iter_errors(graph)]
    if errors:
        return errors
    def finite(x):
        if isinstance(x, float): return math.isfinite(x)
        if isinstance(x, dict): return all(finite(v) for v in x.values())
        if isinstance(x, list): return all(finite(v) for v in x)
        return True
    if not finite(graph): return ['Non-finite number']
    all_ids = []
    for key, field in COLLECTIONS.items(): all_ids += [v[field] for v in graph[key]]
    if len(set(all_ids)) != len(all_ids): errors.append('ID uniqueness violation')
    ids = set(all_ids)
    entities = {e['id']: e for e in graph['entities']}
    events = {e['event_id']: e for e in graph['events']}
    shots = {s['shot_id']: s for s in graph['shot_intents']}
    def refs(values, available, label):
        for v in values:
            if v not in available: errors.append(f'{label}: missing reference {v}')
    tb = graph['timebase']; fps = tb['fps']; duration = tb['duration']
    try: duration_frames(duration, fps)
    except ValueError as exc: errors.append(str(exc))
    for e in entities.values():
        prefix = {'character': 'CHAR_', 'weapon': 'WPN_', 'projectile': 'PROJ_',
                  'prop': 'PROP_', 'environment': 'PROP_'}[e['type']]
        if not e['id'].startswith(prefix): errors.append('Stable ID prefix/type mismatch: ' + e['id'])
        if e['module'] != graph['module']: errors.append('Entity module mismatch: ' + e['id'])
        if e['owner'] is not None:
            refs([e['owner']], entities, 'Owner')
            if e['owner'] == e['id']: errors.append('Self ownership: ' + e['id'])
        if e['type'] == 'projectile':
            owner = entities.get(e['owner'])
            if not owner or owner['type'] not in ('character', 'weapon', 'prop'):
                if not (graph['origin'] == 'DEBUG' and e['owner'] is None and not for_compile):
                    errors.append('Invalid projectile ownership: ' + e['id'])
    def cycle(adjacency, label):
        # Iterative Kahn traversal also handles graphs larger than Python's recursion limit.
        degrees = {k: 0 for k in adjacency}
        for children in adjacency.values():
            for v in children: degrees[v] += 1
        queue = [k for k, n in degrees.items() if n == 0]; visited = 0
        while queue:
            k = queue.pop(); visited += 1
            for v in adjacency[k]:
                degrees[v] -= 1
                if degrees[v] == 0: queue.append(v)
        if visited != len(adjacency): errors.append(label + ' cycle')
    ownership = {k: set() for k in entities}
    for e in entities.values():
        if e['owner'] in entities: ownership[e['id']].add(e['owner'])
    cycle(ownership, 'Ownership')
    cursor = 0.0
    for s in graph['shot_intents']:
        a, b = s['time_range']
        if not (0 <= a < b <= duration + 1e-9): errors.append('Invalid shot time: ' + s['shot_id'])
        if abs(a - cursor) > 1e-9: errors.append('Shot gap/overlap: ' + s['shot_id'])
        if time_to_frame(b, fps) <= time_to_frame(a, fps): errors.append('Shot collapses at frame rate')
        cursor = b
        refs(s['subjects'] + s['required_visibility'], entities, 'Shot entity')
        if s['handoff_to_next'] is not None: refs([s['handoff_to_next']], shots, 'Shot handoff')
    if abs(cursor - duration) > 1e-9: errors.append('Global duration / shot coverage mismatch')
    adjacency = {k: set() for k in events}
    for e in events.values():
        if not (0 <= e['start'] <= e['peak'] <= e['end'] <= duration + 1e-9):
            errors.append('Invalid event time: ' + e['event_id'])
        refs(e['actor'] + e['targets'], entities, 'Event entity')
        if for_compile and not e['actor']: errors.append('Unknown event actor: ' + e['event_id'])
        if e['event_type'] == 'CONTACT' and (not e['actor'] or not e['targets'] or not (set(e['targets']) - set(e['actor']))):
            errors.append('Contact requires two distinct participants: ' + e['event_id'])
        if e['source_event'] is not None:
            refs([e['source_event']], events, 'Source event')
            if e['source_event'] in events: adjacency[e['source_event']].add(e['event_id'])
    pairs = set()
    for d in graph['dependencies']:
        refs([d['event_id'], d['depends_on']], events, 'Dependency')
        pair = (d['event_id'], d['depends_on'])
        if pair in pairs: errors.append('Duplicate dependency')
        pairs.add(pair)
        if all(k in events for k in pair): adjacency[d['depends_on']].add(d['event_id'])
    cycle(adjacency, 'Dependency/source event')
    for c in graph['constraints']:
        refs(c['targets'], ids, 'Constraint')
        if c['scope'] != 'SEQUENCE': refs(c['targets'], {'ENTITY': entities, 'SHOT': shots, 'EVENT': events}[c['scope']], 'Constraint scope')
    for o in graph['overrides']:
        refs([o['target']], {'ENTITY': entities, 'SHOT': shots, 'EVENT': events, 'CONSTRAINT': {c['constraint_id'] for c in graph['constraints']}}[o['scope']], 'Override')
    if for_compile and graph['origin'] == 'DEBUG': errors.append('DEBUG graph is not a production authoring entry; curate explicitly')
    return errors


def require_valid(graph, **kwargs):
    errors = validate(graph, **kwargs)
    if errors: raise ValueError('\n'.join(errors))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('graph'); args = ap.parse_args()
    errors = validate(json.loads(Path(args.graph).read_text(encoding='utf-8')))
    print(json.dumps({'status': 'FAIL' if errors else 'STRUCTURAL_PASS', 'errors': errors}, ensure_ascii=False, indent=2))
    raise SystemExit(bool(errors))
