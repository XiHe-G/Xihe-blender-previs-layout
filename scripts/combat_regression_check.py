"""Compare evaluated CSP rerun with immutable baseline; no automatic visual PASS.
python this.py fixture_folder new_build_folder --output result.json
"""
import argparse,hashlib,json,math
from pathlib import Path
from combat_sequence_package import read_package,validate

def compare(base,actual,tolerance=1e-5):
    maximum=0.;issues=[];numbers=0
    def visit(a,b,path):
        nonlocal maximum,numbers
        if isinstance(a,bool) or isinstance(a,str) or a is None:
            if a!=b:issues.append(path)
        elif isinstance(a,(int,float)):
            if not isinstance(b,(int,float)) or not math.isfinite(b):issues.append(path);return
            delta=abs(a-b);maximum=max(maximum,delta);numbers+=1
            if delta>tolerance:issues.append(path)
        elif isinstance(a,list):
            if not isinstance(b,list) or len(a)!=len(b):issues.append(path+'/length');return
            for i,(x,y) in enumerate(zip(a,b)):visit(x,y,f'{path}/{i}')
        elif isinstance(a,dict):
            if not isinstance(b,dict) or a.keys()!=b.keys():issues.append(path+'/keys');return
            for k in a:visit(a[k],b[k],path+'/'+str(k))
    visit(base,actual,'timeline')
    return {'status':'PASS' if not issues else 'FAIL','max_absolute_numeric_error':maximum,'numeric_values_compared':numbers,'mismatch_count':len(issues),'first_mismatches':issues[:20],'tolerance':tolerance}

def check(fixture,build):
    fixture,build=Path(fixture),Path(build);p=read_package(fixture/'sequence.csp.json.gz')
    errors=validate(p);result=compare(read_package(fixture/'baseline-evaluated.json.gz'),read_package(build/'evaluated.json.gz'))
    manifest=read_package(build/'build_manifest.json')
    expected=hashlib.sha256((fixture/'sequence.csp.json.gz').read_bytes()).hexdigest()
    if expected!=manifest['package_sha256']:errors.append('Package fingerprint changed after build')
    script=Path(__file__).with_name('combat_sequence_builder.py')
    if hashlib.sha256(script.read_bytes()).hexdigest()!=manifest['builder_sha256']:errors.append('Builder changed after build')
    frames=list((build/'frames').glob('frame_*.png'))
    wanted=[f'frame_{i:04d}.png' for i in range(1,p['timebase']['frames']+1)]
    if sorted(f.name for f in frames)!=wanted:errors.append('Missing/unexpected rendered frames')
    result.update(sequence_id=p['sequence_id'],errors=errors,rendered_frames=len(frames),cut_count=len(p['continuity_states']),build_manifest=manifest,visual_gates='Separate timecoded review required; numeric equality is regression compatibility only')
    if errors:result['status']='FAIL'
    return result

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('fixture');a.add_argument('build');a.add_argument('--output',required=True);args=a.parse_args()
    result=check(args.fixture,args.build);Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(result['status']!='PASS')
