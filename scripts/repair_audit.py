"""Immutable file receipts; raw artifact SHA256 plus cross-stage semantic hashes."""
import hashlib
from pathlib import Path
from s2_common import read,write,digest

REQUIRED=['original_graph','original_csp','original_blend','original_trace','original_report','proposal','human_decision','changeset','affected_scope','execution_patch','new_csp','new_blend','new_trace','new_report','result','unchanged_region']
def filehash(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def receipt(paths,proposal,decision,changeset,scope,result):
    if set(REQUIRED)-set(paths):raise ValueError('INCOMPLETE_REPAIR_AUDIT')
    if decision['proposal_sha256']!=digest(proposal) or changeset['execution_repair']['decision_id']!=decision['decision_id'] or scope['changeset_sha256']!=digest(changeset):raise ValueError('BROKEN_REPAIR_PROVENANCE_CHAIN')
    for key,value in [('proposal',proposal),('human_decision',decision),('changeset',changeset),('affected_scope',scope),('result',result)]:
        if digest(read(paths[key]))!=digest(value):raise ValueError('REPAIR_RECEIPT_INPUT_MISMATCH: '+key)
    from combat_sequence_package import read_package
    graph=read(paths['original_graph']);base=read_package(paths['original_csp']);trace=read_package(paths['new_trace']);report=read(paths['new_report']);patch=read(paths['execution_patch'])
    if digest(graph)!=changeset['base_graph_sha256'] or digest(base)!=scope['base_csp_sha256'] or patch['changeset_sha256']!=digest(changeset) or patch['affected_scope_sha256']!=digest(scope):raise ValueError('REPAIR_EXECUTION_CHAIN_MISMATCH')
    if report['trace_sha256']!=digest(trace) or trace['source_blend']['sha256']!=filehash(paths['new_blend']):raise ValueError('REPAIR_TRACE_CHAIN_MISMATCH')
    if digest(read(paths['original_report']))!=proposal['source_checker_result']['report_sha256']:raise ValueError('REPAIR_ORIGINAL_REPORT_MISMATCH')
    entries={k:dict(path=str(Path(v).resolve()),sha256=filehash(v),bytes=Path(v).stat().st_size) for k,v in paths.items()}
    return dict(schema_version='REPAIR-RECEIPT/1.0',proposal_id=proposal['proposal_id'],decision_id=decision['decision_id'],result=result['status'],artifacts=entries,chain=dict(proposal_sha256=digest(proposal),decision_sha256=digest(decision),changeset_sha256=digest(changeset),scope_sha256=digest(scope)),automatic_approval=False,automatic_retry=False)
def verify(receipt):
    for key,a in receipt['artifacts'].items():
        if filehash(a['path'])!=a['sha256']:raise ValueError('REPAIR_ARTIFACT_HASH_MISMATCH: '+key)
    return True

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--verify',required=True);a=ap.parse_args();verify(read(a.verify));print('REPAIR_RECEIPT_HASHES_PASS')
