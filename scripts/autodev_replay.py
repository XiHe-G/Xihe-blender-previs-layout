"""Replay one declarative evaluation in a fresh directory, never in-place.

Configs are trusted local command specifications, not instructions imported from references.
"""
import argparse,json,hashlib
from pathlib import Path
from autodev_guard import ExecutionGuard,digest,now
from autodev_evaluator import receipt

def replay(config,group,output):
    if group not in ('baseline','candidate'):raise ValueError('INVALID_GROUP')
    skill=Path(config['skills'][group]).resolve();out=Path(output).resolve()
    if out.exists():raise ValueError('FRESH_OUTPUT_REQUIRED')
    if out.is_relative_to(skill):raise ValueError('OUTPUT_MUST_BE_OUTSIDE_SKILL')
    inputs={str(Path(p).resolve()):v for p,v in config['input_hashes'].items()}
    if any(digest(p)!=v for p,v in inputs.items()):raise ValueError('INPUT_REVISION_MISMATCH')
    sources={str(Path(p).relative_to(skill)):digest(p) for p in sorted(skill.rglob('*.py')) if '__pycache__' not in p.parts}
    revision=hashlib.sha256(json.dumps(sources,sort_keys=True).encode()).hexdigest()
    out.mkdir(parents=True);run_id=config['benchmark_id']+'_'+out.name
    g=ExecutionGuard(out/'jobs',run_id)
    def expand(s):return s.replace('{output}',str(out)).replace('{skill}',str(skill))
    for step in config['steps']:
        record=g.run(step['id'],[expand(s) for s in step['argv']],out,step['mutation'],timeout=step.get('timeout',1800))
        if record.get('returncode')!=0:raise RuntimeError('JOB_FAILED_OR_UNCERTAIN: '+step['id'])
    if any(digest(p)!=v for p,v in inputs.items()):raise RuntimeError('INPUT_MUTATED')
    current={str(Path(p).relative_to(skill)):digest(p) for p in sorted(skill.rglob('*.py')) if '__pycache__' not in p.parts}
    if sources!=current:raise RuntimeError('SKILL_CHANGED_DURING_REPLAY')
    reports=[out/p for p in config['reports']];outputs=[out/p for p in config['outputs']]
    r=receipt(run_id,config['benchmark_id'],group,revision,config['blender_version'],inputs,outputs,reports,record)
    r['source_files']=sources;r['configuration']=config;r['completed']=now()
    (out/'EVAL-RECEIPT.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
    if not r['validator_pass']:raise RuntimeError('VALIDATOR_FAIL')
    g.verify(record['command_id'],outputs,reports[0])
    return r

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('config');ap.add_argument('--group',choices=['baseline','candidate'],required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
    r=replay(json.loads(Path(a.config).read_text()),a.group,a.output);print(r['evidence_state'])
