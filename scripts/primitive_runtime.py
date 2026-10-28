"""EXECUTION-PRIMITIVE/1.0 -> deterministic fragments; never touches Blender or AG."""
import copy
import json
import math
from pathlib import Path
from primitive_sampler import *
from primitive_channel_registry import channels,validate_composition,MOTION,CAMERA
from motion_primitives import make_motion
from camera_primitives import make_camera
from motion_boundary_validator import validate_boundary

def validate_primitive(p):
    import jsonschema
    schema=json.loads((Path(__file__).resolve().parents[1]/'authoring'/'execution-primitive.schema.json').read_text())
    jsonschema.validate(p,schema)
    if p['end_time']<=p['start_time']:raise ValueError('INVALID_TIME_RANGE')
    if norm(p['entry_state']['orientation'])<1e-8:raise ValueError('INVALID_QUATERNION')
    # JSON serialization rejects nonfinite values even where parameters are extensible.
    sha(p)

def boundary(rows,p,fps):
    """Boundary evaluation includes real sampled interval and contract-extrapolated guards.

    Guards are explicit constant-velocity continuation assumptions, never hidden scene data.
    They are replaced by neighboring fragments for composed execution validation.
    """
    lo,hi=rows[0]['frame'],rows[-1]['frame'];a=rows[0];b=rows[-1]
    # S4.5 needs positive global guard frames: pad the observation clock only when origin has no past.
    shift=max(0,5-lo)
    samples=[{'frame':r['frame']+shift,'position':r['position']} for r in rows]
    for k in range(1,5):
        samples.append({'frame':lo-k+shift,'position':sub(a['position'],mul(a['velocity'],k/fps))})
        samples.append({'frame':hi+k+shift,'position':add(b['position'],mul(b['velocity'],k/fps))})
    samples.sort(key=lambda r:r['frame'])
    profile='PROJECTILE_CONTINUITY_PROFILE' if 'PROJECTILE_TRANSFORM' in channels(p)['WRITES'] else 'CHARACTER_ROOT_CONTINUITY_PROFILE'
    authority=p['provenance'].get('boundary_authority',{})
    if authority and shift:raise ValueError('AUTHORIZATION_REQUIRES_ORIGINAL_GLOBAL_GUARD_TIME')
    if p['continuity_contract']['C1_REQUIREMENT']=='AUTHORIZED_DISCONTINUITY' and not authority:raise ValueError('AUTHORIZED_DISCONTINUITY_REQUIRES_EVIDENCE')
    result=validate_boundary(samples,[lo+shift,hi+shift],fps,profile,p['actor'],interpolation_evidence={'kind':'AUTHORED_CONTINUOUS_PIECEWISE_LINEAR'},authorized=authority.get('declarations'),graph=authority.get('graph'),boundary_semantic={'rows':rows,'primitive':p} if p['provenance'].get('boundary_semantics')=='AUTHORED_ENVELOPE/1.0' else None)
    result['guard_evidence']='EXPLICIT_ENTRY_EXIT_CONSTANT_VELOCITY_CONTINUATION';result['observation_frame_shift']=shift
    result['contract']=p['continuity_contract']
    return result

def compile_primitive(p,timebase,reads=None):
    validate_primitive(p);reads=reads or {};fps=timebase['fps'];fs=list(frames(p['start_time'],p['end_time'],fps))
    if len(fs)<3:raise ValueError('INSUFFICIENT_PRIMITIVE_SAMPLES')
    if timebase.get('frame_origin',1)!=1 or timebase.get('time_unit','seconds')!='seconds':raise ValueError('TIMEBASE_CONFLICT')
    if p['end_time']>timebase['duration']:raise ValueError('OUTSIDE_DURATION')
    fn=make_motion if p['primitive_type'] in MOTION else make_camera
    rows,derived=fn(p,[frame_to_time(f,fps) for f in fs],reads)
    for i,r in enumerate(rows):
        r['frame']=fs[i];r['orientation']=qnorm(r['orientation'])
        if i:
            if dot(rows[i-1]['orientation'],r['orientation'])<0:r['orientation']=mul(r['orientation'],-1)
        r['angular_velocity']=0. if not i else qangle(rows[i-1]['orientation'],r['orientation'])*fps
    def state(r):
        return dict(position=r['position'],velocity=r['velocity'],movement_direction=unit(r['velocity']),orientation=r['orientation'],angular_velocity=r['angular_velocity'],ownership_state=r.get('ownership_state',p['entry_state']['ownership_state']),support_state=p['entry_state'].get('support_state','UNSPECIFIED'),**({k:r[k] for k in ('lens','subject_screen_position','subject_screen_size')} if p['primitive_type'] in CAMERA else {}))
    a,b=state(rows[0]),state(rows[-1]);warnings=[];tol=p.get('contract_tolerance',1e-5)
    for key,value in p['exit_requirements'].items():
        if key not in b:raise ValueError('UNKNOWN_EXIT_REQUIREMENT '+key)
        error=qangle(b[key],value) if key=='orientation' else norm(sub(b[key],value)) if isinstance(value,list) else abs(b[key]-value) if isinstance(value,(float,int)) else 0 if b[key]==value else 1
        if error>tol:raise ValueError('EXIT_CONTRACT_MISMATCH '+key)
    if norm(sub(a['position'],p['entry_state']['position']))>tol and p['primitive_type'] not in ('ORIENT_TO','OFFSET_PATH'):raise ValueError('ENTRY_POSITION_MISMATCH')
    if any(c in channels(p)['WRITES'] for c in ('ROOT_LOCATION','PROJECTILE_TRANSFORM','CAMERA_LOCATION')) and norm(sub(a['velocity'],p['entry_state']['velocity']))>tol:raise ValueError('ENTRY_VELOCITY_MISMATCH')
    report=boundary(rows,p,fps)
    rotation_channels=[c for c in channels(p)['WRITES'] if 'ROTATION' in c or 'TRANSFORM' in c]
    if rotation_channels:
        rates=[r['angular_velocity'] for r in rows];limit=p['parameters'].get('max_angular_speed');initial_rate=rates[1];entry_error=abs(initial_rate-p['entry_state']['angular_velocity']);step=max(abs(y-x) for x,y in zip(rates,rates[1:]));c1='PASS' if entry_error<=.01 and step<=.1 and (limit is None or max(rates)<=math.radians(limit)+1e-6) else 'FAIL'
        c0='PASS' if qangle(rows[0]['orientation'],p['entry_state']['orientation'])<=tol else 'FAIL'
        report['angular_contract']={'unit':'radians/second','entry':initial_rate,'exit':rates[-1],'peak':max(rates),'max_rate_step':step,'max_angular_speed_deg':limit,'C0':c0,'C1':c1,'basis':'quaternion hemisphere + sampled entry rate / rate-step checks','technical_defaults':{'source':'TECHNICAL_DEFAULT S51 angular-only contract; S45 translation policy unchanged','entry_rate_tolerance':.01,'max_rate_step':.1}}
        if p['parameters'].get('orientation_mode')=='SNAP' and p['parameters'].get('snap_authorized') and p['continuity_contract']['C1_REQUIREMENT']=='AUTHORIZED_DISCONTINUITY':
            jump_frames=[rows[i]['frame'] for i in range(1,len(rows)) if abs(rates[i]-rates[i-1])>.1]
            declarations=report['authorized_discontinuities']
            if all(any('C1' in d['derivatives'] and d['frame_range'][0]<=frame<=d['frame_range'][1] for d in declarations) for frame in jump_frames):
                report['angular_contract'].update(raw_C1=c1,C1='PASS',basis='EXPLICIT_SNAP_AND_SCOPED_S45_AUTHORIZATION');c1='PASS'
        for dim,status in [('C0',c0),('C1',c1)]:
            if status=='FAIL':report['dimensions'][dim]='FAIL';report['status']='FAIL'
    if report['dimensions']['C1']!='PASS':warnings.append('S45_C1_CONTRACT_NOT_SATISFIED')
    fragment=dict(fragment_version='PRIMITIVE-EXECUTION-FRAGMENT/1.0',primitive_id=p['primitive_id'],primitive_sha256=sha(p),affected_entity=p['actor'],time_range=[p['start_time'],p['end_time']],timebase=copy.deepcopy(timebase),channel_ownership=channels(p),world_samples=rows,pose_samples=[],ownership_samples=[{'frame':r['frame'],'state':r['ownership_state'],'owner':r.get('owner')} for r in rows if 'ownership_state' in r],metadata={'primitive_type':p['primitive_type'],'parameters_source':'EXPLICIT','derived_parameters':derived,'native_identity':p.get('native_identity',{}),'sample_interpolation':'LINEAR','boundary_policy':'S45 unchanged'},entry_state_actual=a,exit_state_actual=b,continuity_report=report)
    diagnostic=dict(requested_parameters=p['parameters'],derived_parameters=derived,entry_actual=a,exit_actual=b,boundary_result=report['dimensions'],channel_ownership=channels(p),warnings=warnings,execution_sample_count=len(rows))
    if p['primitive_type']=='ATTACH_DETACH':
        fragment['metadata']['native_identity']=dict(p.get('native_identity',{}))
        if not fragment['metadata']['native_identity'].get('previs_entity_id') or not fragment['metadata']['native_identity'].get('previs_owner_id'):raise ValueError('ATTACH_NATIVE_IDENTITY_REQUIRED')
    fragment['pose_samples']=[{'frame':r['frame'],'channel':ch,'orientation':r['orientation']} for ch in channels(p)['WRITES'] if ch in ('BODY_ROTATION','HEAD_ROTATION') for r in rows]
    fragment['execution_sha256']=sha({k:fragment[k] for k in ('world_samples','ownership_samples','channel_ownership','entry_state_actual','exit_state_actual','continuity_report')})
    import jsonschema
    jsonschema.validate(fragment,json.loads((Path(__file__).resolve().parents[1]/'authoring'/'primitive-execution-fragment.schema.json').read_text()))
    return fragment,diagnostic

def compile_program(program):
    import jsonschema
    jsonschema.validate(program,json.loads((Path(__file__).resolve().parents[1]/'authoring'/'execution-primitive.schema.json').read_text()))
    ps=program['primitives'];ops=program.get('composition',[]);validate_composition(ps,ops)
    for p in ps:
        if p['primitive_type']=='ATTACH_DETACH':
            ids=program.get('entity_ids',{})
            native=p.get('native_identity',{})
            if ids.get(p['actor'])!=native.get('previs_entity_id') or ids.get(p['parameters']['owner'])!=native.get('previs_owner_id'):raise ValueError('NATIVE_OWNER_REGISTRY_MISMATCH')
    pending=list(ps);fragments=[];diagnostics={};reads=copy.deepcopy(program.get('read_tracks',{}))
    while pending:
        progressed=False
        for p in pending[:]:
            needed=channels(p)['READS']
            if any(n not in reads for n in needed):continue
            # Consumers observe all explicitly scheduled writers in their read window.
            entities=[n for n in needed if any(x['actor']==n for x in ps)]
            if p['primitive_type']=='ORIENT_TO':entities.append(p['actor'])
            if any(x is not p and x['actor'] in entities and any(c in channels(x)['WRITES'] for c in ('ROOT_LOCATION','PROJECTILE_TRANSFORM')) and x['start_time']<=p['end_time'] and x['end_time']>=p['start_time'] for x in pending):continue
            resolved=copy.deepcopy(p)
            if p['parameters'].get('entry_from'):
                parent=next(f for f in fragments if f['primitive_id']==p['parameters']['entry_from'])
                resolved['entry_state']=copy.deepcopy(parent['exit_state_actual'])
                resolved['entry_state']['camera_velocity']=resolved['entry_state']['velocity']
            f,d=compile_primitive(resolved,program['timebase'],reads)
            f['metadata']['unresolved_description_sha256']=sha(p)
            fragments.append(f);diagnostics[p['primitive_id']]=d
            reads[p['primitive_id']]=f['world_samples']
            if any(c in f['channel_ownership']['WRITES'] for c in ('ROOT_LOCATION','PROJECTILE_TRANSFORM')):
                old={r['frame']:r for r in reads.get(p['actor'],[]) if 'frame' in r};old.update({r['frame']:r for r in f['world_samples']});reads[p['actor']]=[old[k] for k in sorted(old)]
            pending.remove(p);progressed=True
        if not progressed:raise ValueError('MISSING_OR_CYCLIC_PRIMITIVE_READS '+','.join(p['primitive_id'] for p in pending))
    # Shared endpoints must agree, not last writer wins.
    byid={f['primitive_id']:f for f in fragments}
    for op in ops:
        if op['type']!='SEQUENTIAL':continue
        a,b=[byid[x] for x in op['members']]
        if abs(a['time_range'][1]-b['time_range'][0])>1e-9:raise ValueError('SEQUENCE_TIME_GAP')
        common=set(a['channel_ownership']['WRITES'])&set(b['channel_ownership']['WRITES'])
        for channel in common:
            fields=['position','velocity'] if 'LOCATION' in channel or 'TRANSFORM' in channel else ['orientation','angular_velocity'] if 'ROTATION' in channel else ['lens'] if channel=='CAMERA_LENS' else []
            for key in fields:
                av,bv=a['exit_state_actual'][key],b['entry_state_actual'][key]
                err=abs(av-bv) if isinstance(av,(int,float)) else qangle(av,bv) if key=='orientation' else norm(sub(av,bv))
                if err>program.get('seam_tolerance',.005):raise ValueError('SEQUENTIAL_CONTRACT_MISMATCH '+channel+' '+key)
    return {'fragment_version':'PRIMITIVE-EXECUTION-FRAGMENT/1.0','program_sha256':sha(program),'fragments':fragments,'composition':ops},diagnostics

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('--output',required=True);args=ap.parse_args()
    result,diag=compile_program(json.loads(Path(args.input).read_text()));out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    (out/'EXECUTION-FRAGMENT.json').write_text(json.dumps(result,indent=2,allow_nan=False));(out/'PRIMITIVE-DIAGNOSTIC.json').write_text(json.dumps(diag,indent=2,allow_nan=False))
