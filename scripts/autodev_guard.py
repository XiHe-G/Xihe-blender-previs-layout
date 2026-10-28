"""Single-writer persistent mutation guard. Timeout is uncertainty, not a retry."""
import json, os, subprocess, datetime, hashlib
from pathlib import Path

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

class ExecutionGuard:
    def __init__(self, directory, run_id):
        self.root=Path(directory);self.root.mkdir(parents=True,exist_ok=True)
        self.run_id=run_id;self.state=self.root/'execution-state.json';self.lock=self.root/'mutation.lock'
    def read(self):return json.loads(self.state.read_text()) if self.state.exists() else {'state':'CLEAN','commands':[]}
    def save(self,s):
        t=self.state.with_suffix('.tmp');t.write_text(json.dumps(s,indent=2),encoding='utf-8');os.replace(t,self.state)
    def run(self,command_id,argv,target,expected_mutation,timeout=1800):
        # File survives process death. Only explicit reconciliation can unlock uncertainty.
        fd=os.open(self.lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(fd)
        s=self.read()
        if s['state'] in ('MUTATING','UNCERTAIN') or any(c['command_id']==command_id for c in s['commands']):
            self.lock.unlink();raise RuntimeError('UNRECONCILED_OR_DUPLICATE_COMMAND')
        record={'command_id':command_id,'run_id':self.run_id,'argv':argv,'target_file':str(target),
                'expected_mutation':expected_mutation,'start_state':s['state'],'start':now(),'completion_state':'MUTATING'}
        s['commands'].append(record);s['state']='MUTATING';self.save(s)
        try:
            with (self.root/(command_id+'.log')).open('w',encoding='utf-8') as log:
                p=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT)
                record['pid']=p.pid;self.save(s)
                try:code=p.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    s['state']='UNCERTAIN';record['completion_state']='UNCERTAIN';record['timeout']=now();self.save(s)
                    return {'state':'UNCERTAIN','pid':p.pid}
            record['returncode']=code;record['end']=now()
            s['state']='CLEAN' if code==0 else 'FAILED';record['completion_state']=s['state'];self.save(s)
            self.lock.unlink()
            return dict(record)
        except Exception:
            s['state']='UNCERTAIN';record['completion_state']='UNCERTAIN';self.save(s);raise
    def verify(self,command_id,artifacts,validator_report):
        s=self.read()
        if s['state'] in ('MUTATING','UNCERTAIN'):raise RuntimeError('INSPECT_UNCERTAIN_JOB_FIRST')
        r=next(c for c in s['commands'] if c['command_id']==command_id)
        report=json.loads(Path(validator_report).read_text(encoding='utf-8'))
        if r.get('returncode')!=0 or report.get('status')!='PASS':raise ValueError('VALIDATION_NOT_PASS')
        r['files']={str(p):digest(p) for p in [*artifacts,validator_report]}
        r['completion_state']='VERIFIED';r['verified']=now();s['state']='VERIFIED';self.save(s)
    def reconcile(self,inspection_path):
        """Inspection must be independently collected after process exit, including scene audit.
        Never infer success just because a blend exists. No automatic replay API.
        """
        s=self.read();i=json.loads(Path(inspection_path).read_text())
        r=s['commands'][-1]
        if s['state'] not in ('UNCERTAIN','MUTATING'):raise ValueError('NOT_UNCERTAIN')
        if i.get('command_id')!=r['command_id'] or i.get('run_id')!=self.run_id or i.get('pid')!=r.get('pid'):raise ValueError('INSPECTION_ID_MISMATCH')
        if i.get('process_exited') is not True or i.get('scene_inspected') is not True or not i.get('objects_cameras_keyframes_report'):raise ValueError('INCOMPLETE_INSPECTION')
        outcome=i.get('outcome')
        if outcome not in ('SUCCESS','PARTIAL','FAILED'):raise ValueError('INVALID_OUTCOME')
        r['inspection_sha256']=digest(inspection_path);r['inspection_artifact_sha256']=digest(i['objects_cameras_keyframes_report'])
        r['completion_state']='CLEAN' if outcome=='SUCCESS' else 'FAILED';s['state']=r['completion_state'];self.save(s)
        if self.lock.exists():self.lock.unlink()

