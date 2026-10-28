"""Pure transactional CSP merge with unchanged-region and LOCKED protection.

All inputs are validated before returning any updated package. Builder is not
involved in partial compilation; it receives an ordinary complete CSP/1.0.
"""
import argparse
from copy import deepcopy
from s2_common import digest,put,get,read,write,projection,unchanged_report
from execution_patch_validator import validate_patch
from override_guard import verify_registry,resolve_registry,protect,finish_registry
from combat_sequence_package import validate as validate_csp,read_package
from author_graph_to_csp import write_package

def validate_lock_scopes(graph,binding,csp,registry):
    authors={o['override_id']:o for o in graph['overrides']}
    registered={o['override_id']:o for o in registry['overrides']}
    for id,o in authors.items():
        if o['status']=='LOCKED' and id not in registered:raise ValueError('UNREGISTERED_LOCK: '+id)
    for lock in registry['overrides']:
        if lock['override_id'] not in authors:raise ValueError('Override registry absent from author graph')
        for key in ('scope','target','channel','owner','status'):
            if lock[key]!=authors[lock['override_id']][key]:raise ValueError('Override graph/registry mismatch: '+key)
        if lock['scope']=='SHOT' and lock['channel'] in ('camera_transform','lens'):
            shotid=binding['shot_ids'].get(lock['target'])
            s=next((s for s in csp['shot_plan'] if s['id']==shotid),None)
            if s is None:raise ValueError('Unknown protected shot')
            expected=[dict(section='camera_tracks',target=s['camera_id'],channel=lock['channel'],frame_range=[s['first_frame'],s['end_frame_exclusive']-1])]
            if lock['channel']=='camera_transform':
                for parent in lock['source']['parent_chain']:
                    if parent in csp['object_tracks']:
                        expected.append(dict(section='world_tracks',target=parent,channel='camera_transform',frame_range=[s['first_frame'],s['end_frame_exclusive']-1]))
            if set(projection(csp,expected))!=set(projection(csp,lock['protections'])):raise ValueError('Incomplete/wrong Camera lock selector')

def check_author_execution(graph,csp,binding):
    beats={b['event_id']:b for b in csp['action_beats']}
    for e in graph['events']:
        if e['event_id'] not in binding['event_ids']:continue
        b=beats[binding['event_ids'][e['event_id']]]
        if b['interval_s']!=[e['start'],e['end']]:raise ValueError('LOWERING_TIME_MISMATCH '+e['event_id'])
        peak=b.get('phases',{}).get('PEAK',{}).get('interval_s',[e['start']])[0]
        if peak!=e['peak']:raise ValueError('LOWERING_PEAK_MISMATCH '+e['event_id'])

def merge(base,patch,graph,updated_graph,changeset,binding,scope,registry,resolution=None):
    paths=validate_patch(base,patch,graph,updated_graph,changeset,binding,scope,registry,resolution)
    verify_registry(registry,base);validate_lock_scopes(graph,binding,base,registry)
    active,replacements=resolve_registry(registry,resolution,patch['patch_id'])
    protect(active,base,paths,patch['patch_id'],[] if changeset.get('execution_repair') else changeset['changes'])
    result=deepcopy(base)
    for op in patch['execution_payload']:put(result,op['path'],op['new_value'])
    errors=validate_csp(result)
    if errors:raise ValueError('MERGED_CSP_INVALID: '+'; '.join(errors))
    check_author_execution(updated_graph,result,binding)
    protected=finish_registry(active,replacements,result)
    validate_lock_scopes(updated_graph,binding,result,protected)
    regression=unchanged_report(base,result,scope['allowed_paths'])
    if regression['status']!='PASS':raise ValueError('UNCHANGED_REGION_REGRESSION')
    # Require a direct spatial request to change an owned motion/execution leaf.
    for c in changeset['changes']:
        if c['change_type']=='EVENT_SPATIAL_CHANGE':
            from s2_common import selector_paths,TRACK_SECTIONS
            owned={p for r in scope['affected_execution_channels'] if r['owner']==c['target'] and r['section'] in TRACK_SECTIONS for p in selector_paths(base,r)}
            if not paths & owned:raise ValueError('SPATIAL_CHANGE_NOT_LOWERED')
    next_binding=deepcopy(binding);next_binding['graph_sha256']=digest(updated_graph);next_binding['csp_sha256']=digest(result)
    receipt=dict(status='PASS',patch_id=patch['patch_id'],base_csp_sha256=digest(base),updated_csp_sha256=digest(result),
                 author_graph_sha256=digest(updated_graph),binding_sha256=digest(next_binding),unchanged_region=regression,
                 changed_paths=sorted(paths),manual_motion_generation=False,
                 override_states={x['override_id']:x['status'] for x in protected['overrides']})
    return result,next_binding,protected,receipt

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    for flag in ['csp','patch','graph','updated-graph','changeset','binding','scope','registry','output']:ap.add_argument('--'+flag,required=True)
    ap.add_argument('--resolution');a=ap.parse_args()
    result,binding,registry,receipt=merge(read_package(a.csp),read(a.patch),read(a.graph),read(a.updated_graph),read(a.changeset),read(a.binding),read(a.scope),read(a.registry),read(a.resolution) if a.resolution else None)
    from pathlib import Path
    out=Path(a.output)
    if out.exists():raise ValueError('Use a new output directory; no input overwrite')
    out.mkdir(parents=True)
    write_package(out/'UPDATED.csp.json.gz',result);write(out/'UPDATED-BINDING.json',binding);write(out/'UPDATED-OVERRIDES.json',registry)
    write(out/'UPDATED-GRAPH.json',read(a.updated_graph));write(out/'UNCHANGED-REGION-REPORT.json',receipt['unchanged_region']);write(out/'MERGE-RECEIPT.json',receipt)
    print('PARTIAL_MERGE_PASS; ordinary CSP ready for unchanged Builder')
