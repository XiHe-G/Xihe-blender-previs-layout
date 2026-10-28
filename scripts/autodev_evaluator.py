"""Receipts record observed files and explicit checks; no quality-score shortcut."""
from pathlib import Path
import json
from autodev_guard import digest,now

REQUIRED=('Blocking','Spatial Correctness','Continuity','Timing','Camera Execution','Runtime Stability')
DIMENSIONS=REQUIRED+('Motion','Physics','Camera Intent','Composition','Action Readability','AI Layout Readability')

def previs_gate(dimensions,applicable=('Motion',)):
    required=REQUIRED+tuple(applicable)
    return 'LAYOUT_READY' if all(dimensions.get(d)=='PASS' for d in required) else 'NOT_READY'

def receipt(run_id,benchmark_id,group,skill_revision,blender_version,inputs,outputs,checks,command_record):
    if group not in ('baseline','candidate','no_skill'):raise ValueError('INVALID_GROUP')
    if command_record.get('returncode')!=0:raise ValueError('COMMAND_NOT_SUCCESSFUL')
    if not checks:raise ValueError('NO_VALIDATOR_EVIDENCE')
    reports={str(p):json.loads(Path(p).read_text(encoding='utf-8')) for p in checks}
    good=all(r.get('status')=='PASS' for r in reports.values())
    return {'run_id':run_id,'benchmark_id':benchmark_id,'group':group,'skill_revision':skill_revision,
            'agent_version':'not exposed by runtime','blender_version':blender_version,'timestamp':now(),
            'evidence_state':'VERIFIED' if good else 'OBSERVED','command':command_record,
            'inputs':{str(p):digest(p) for p in inputs},'outputs':{str(p):digest(p) for p in outputs},
            'validator_reports':{str(p):digest(p) for p in checks},'validator_pass':good,
            'director_review':'PENDING_DIRECTOR_REVIEW','downstream_video':'NOT_EXECUTED'}

def authority_conflicts(facts):
    owners={};conflicts=[]
    for fact in facts:
        key=(fact['scope'],fact['field']);old=owners.get(key)
        if old and (old['owner']!=fact['owner'] or old['value']!=fact['value']):conflicts.append({'scope':key[0],'field':key[1],'facts':[old,fact]})
        owners[key]=fact
    return conflicts
