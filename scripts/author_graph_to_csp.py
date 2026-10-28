"""AG/1.0 -> unchanged CSP/1.0 via explicit, hash-bound execution lowering.

Authoring intent does not synthesize Blender curves. The execution sidecar owns
samples and CSP-only phase detail. It must be bound to the current graph; stale
lowerings are rejected. This is full compilation, not partial recompile/repair.
"""
import argparse
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
from author_graph_validator import require_valid
from combat_sequence_package import read_package, validate as validate_csp
from timebase import duration_frames, time_to_frame


def author_digest(graph):
    # Paths/hash are packaging metadata; overrides are reservations only in S1.
    payload={k:v for k,v in graph.items() if k not in ('execution','overrides')}
    return hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def write_package(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    data=json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
    path.write_bytes(gzip.compress(data,mtime=0) if path.suffix=='.gz' else data)


def compile_graph(graph, graph_path):
    require_valid(graph,for_compile=True)
    if any(o['status']=='LOCKED' for o in graph['overrides']):
        raise ValueError('OVERRIDE_REGISTRY_REQUIRED: active LOCKED channels must use the S2 guarded execution binding/merge route; S1 full compile cannot discard manual edits')
    if graph['module'] != 'COMBAT_DYNAMIC': raise ValueError('NARRATIVE lowering is not implemented in S1')
    ref=graph['execution']
    if not ref: raise ValueError('Explicit execution lowering required; intent alone is not animation')
    base=Path(graph_path).resolve().parent
    path=(base/ref['path']).resolve()
    if hashlib.sha256(path.read_bytes()).hexdigest()!=ref['sha256']: raise ValueError('Execution sidecar hash mismatch')
    binding=read_package(path)
    if binding.get('schema_version')!='AG-CSP-BINDING/1.0': raise ValueError('Unsupported execution binding')
    if binding.get('author_sha256')!=author_digest(graph):
        raise ValueError('STALE_EXECUTION_BINDING: author intent changed; explicitly re-author execution before compilation')
    p=deepcopy(binding['execution'])
    fps=graph['timebase']['fps'];n=duration_frames(graph['timebase']['duration'],fps)
    if (p['timebase']['fps'],p['timebase']['frames'])!=(fps,n): raise ValueError('Global duration/timebase differs from execution')
    if p['entry_mode']!=graph['entry_mode'] or p['sequence_id']!=graph['graph_id']: raise ValueError('Execution identity differs')
    if any(k in p for k in ('shot_plan','action_beats','causal_links')): raise ValueError('Generated fields must not be duplicated in execution payload')
    def index(records,key):
        result={r[key]:r for r in records}
        if len(result)!=len(records): raise ValueError('Duplicate execution binding')
        return result
    shots=index(binding['shots'],'author_id');events=index(binding['events'],'author_id')
    if set(shots)!={s['shot_id'] for s in graph['shot_intents']} or set(events)!={e['event_id'] for e in graph['events']}:
        raise ValueError('Incomplete author/execution binding coverage')
    aliases=binding['entity_aliases'];groups=binding.get('entity_groups',{})
    entities={e['id']:e for e in graph['entities']}
    if set(aliases.values()) != set(entities): raise ValueError('Entity binding coverage mismatch')
    def resolve(value):
        if value in aliases: return [aliases[value]]
        if value in groups: return groups[value]
        return list(dict.fromkeys(aliases[v.strip()] for v in value.split('/') if v.strip() in aliases))
    for actor in p['actors']:
        if actor['id'] not in aliases or entities[aliases[actor['id']]]['type']!='character':
            raise ValueError('Actor identity binding mismatch')
    for proxy in p['proxy_lifecycles']:
        entity=entities[aliases[proxy['id']]]
        if entity['owner']!=aliases.get(proxy.get('owner_id',proxy.get('owner'))):
            raise ValueError('Execution ownership mismatch: '+proxy['id'])
        if entity['persistent_state']['value']!=proxy['end_state']:
            raise ValueError('Persistent state binding mismatch: '+proxy['id'])
    lifecycle_bindings={x['proxy_id']:x['source_event'] for x in binding['lifecycle_event_bindings']}
    if len(lifecycle_bindings)!=len(binding['lifecycle_event_bindings']) or set(lifecycle_bindings)!={x['id'] for x in p['proxy_lifecycles']}:
        raise ValueError('VFX lifecycle event coverage mismatch')
    for proxy in p['proxy_lifecycles']:
        source=lifecycle_bindings[proxy['id']]
        if source not in events or events[source]['csp_template']['event_id']!=proxy['event_id']:
            raise ValueError('VFX lifecycle must bind to its source event')
    p['shot_plan']=[]
    for s in graph['shot_intents']:
        record=shots[s['shot_id']];out=deepcopy(record['csp_template'])
        out['first_frame']=time_to_frame(s['time_range'][0],fps)
        out['end_frame_exclusive']=time_to_frame(s['time_range'][1],fps)
        if record['has_interval_s']: out['interval_s']=list(s['time_range'])
        if record['has_summary']: out['summary']=s['primary_information']['value']
        p['shot_plan'].append(out)
    p['action_beats']=[]
    for e in graph['events']:
        out=deepcopy(events[e['event_id']]['csp_template'])
        if e['actor']!=resolve(out['owner']) or e['targets']!=resolve(out['target']):
            raise ValueError('Event participant binding mismatch: '+e['event_id'])
        out['interval_s']=[e['start'],e['end']]
        if events[e['event_id']]['has_outcome']: out['outcome']=e['result']['value']
        peak=out.get('phases',{}).get('PEAK',{}).get('interval_s',[e['start']])[0]
        if peak != e['peak']: raise ValueError('Event peak differs from execution phase')
        p['action_beats'].append(out)
    dependencies={(d['event_id'],d['depends_on']):d for d in graph['dependencies']}
    p['causal_links']=[]
    if len(binding['dependencies'])!=len(dependencies): raise ValueError('Dependency binding coverage mismatch')
    seen=set()
    for d in binding['dependencies']:
        pair=(d['event_id'],d['depends_on'])
        if pair not in dependencies or pair in seen: raise ValueError('Unbound/duplicate dependency')
        seen.add(pair);out=deepcopy(d['csp_template'])
        out['cause_event']=events[d['depends_on']]['csp_template']['event_id']
        out['reaction_event']=events[d['event_id']]['csp_template']['event_id']
        p['causal_links'].append(out)
    # Geometry location changes when the generated package moves; bytes are immutable.
    if p.get('scene_asset'):
        asset=(path.parent/p['scene_asset']['path']).resolve()
        if hashlib.sha256(asset.read_bytes()).hexdigest()!=p['scene_asset']['sha256']: raise ValueError('Scene asset hash mismatch')
        p['scene_asset']['path']=str(asset)
    errors=validate_csp(p)
    if errors: raise ValueError('Generated CSP invalid: '+'; '.join(errors))
    return p


def semantic_execution_equivalence(original, generated):
    """Compare all CSP content, with only relocation of hash-identical assets allowed.

    Dict ordering/JSON formatting are immaterial. Lists and numeric execution
    values are exact, stricter than tolerance-based evaluated Blender comparison.
    """
    a=deepcopy(original);b=deepcopy(generated)
    if a.get('scene_asset') and b.get('scene_asset'):
        a['scene_asset'].pop('path',None);b['scene_asset'].pop('path',None)
    differences=[]
    def compare(x,y,path):
        if isinstance(x,dict) and isinstance(y,dict):
            if x.keys()!=y.keys(): differences.append(path+'/keys')
            for k in x.keys() & y.keys(): compare(x[k],y[k],path+'/'+k)
        elif isinstance(x,list) and isinstance(y,list):
            if len(x)!=len(y): differences.append(path+'/length')
            for i,(u,v) in enumerate(zip(x,y)): compare(u,v,f'{path}/{i}')
        elif type(x) is bool or type(y) is bool:
            if type(x)!=type(y) or x!=y: differences.append(path)
        elif x!=y: differences.append(path)
    compare(a,b,'CSP')
    return dict(status='PASS' if not differences else 'FAIL',mismatch_count=len(differences),first_mismatches=differences[:30],
                coverage=['actors','ownership','shot/event timing','world/pose tracks','screen targets','weapon/projectile','camera execution','VFX lifecycle','continuity','all remaining CSP fields'])


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('graph');ap.add_argument('--output',required=True);args=ap.parse_args()
    src=Path(args.graph);dest=Path(args.output)
    if src.resolve()==dest.resolve(): raise ValueError('Do not overwrite the author graph')
    g=json.loads(src.read_text(encoding='utf-8'));p=compile_graph(g,src);write_package(dest,p)
    print(json.dumps({'status':'STRUCTURAL_PASS','output':str(dest),'author_sha256':author_digest(g),
        'override_status':'NO_ACTIVE_LOCKS; LOCKED graphs require the S2 guarded route'},ensure_ascii=False))
