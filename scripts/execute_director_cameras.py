"""Apply explicit DIRECTOR_PLAN/1 cameras to a COPY of an existing scene.

Camera-only adapter: actors, props, lighting, VFX and edit ranges outside the
declared complete plan are not redesigned. Saved output is never the input.
Run via blender -b input.blend --python-exit-code 1 --python this.py -- ...
"""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from director_camera.workflow import validate_plan,file_sha
from director_camera.native import apply_camera

def execute(plan, output, evidence):
    import bpy
    validate_plan(plan);sc=bpy.context.scene
    if any(s['camera']['motion']['kind']=='FOLLOW_WITH_LAG' for s in plan['shots']):
        raise ValueError('FOLLOW_WITH_LAG needs a separate evaluated following adapter')
    source=Path(bpy.data.filepath).resolve() if bpy.data.filepath else None
    output=Path(output).resolve();evidence=Path(evidence).resolve()
    if not source or output==source or output.exists() or evidence.exists() or evidence==output:
        raise ValueError('new output and evidence paths required; source must be saved')
    if sc.frame_start!=plan['start'] or sc.frame_end!=plan['end']-1 or abs(sc.render.fps/sc.render.fps_base-plan['fps'])>1e-8:
        raise ValueError('existing timeline is locked; plan must match')
    planned=[s['camera']['id'] for s in plan['shots']]
    if any(n in bpy.data.objects for n in planned):raise ValueError('new camera names required; preserve baseline camera actions')
    source_hash=file_sha(source);output.parent.mkdir(parents=True,exist_ok=True);evidence.parent.mkdir(parents=True,exist_ok=True)
    # Preserve the current camera-marker list as evidence, then replace bindings
    # only for the complete explicitly supplied timeline. Non-camera markers stay.
    old=[{'name':m.name,'frame':m.frame,'camera':m.camera.name} for m in sc.timeline_markers if m.camera]
    for sh in plan['shots']:
        item=sh['camera'];data=bpy.data.cameras.new(item['id']);cam=bpy.data.objects.new(item['id'],data);sc.collection.objects.link(cam)
        data.lens=item['lens_mm'];data.sensor_width=item.get('sensor_width_mm',36)
        apply_camera(cam,item['motion'],sh['start'],max(sh['start']+1,sh['end']-1))
    for marker in list(sc.timeline_markers):
        if marker.camera:sc.timeline_markers.remove(marker)
    for sh in plan['shots']:
        m=sc.timeline_markers.new(sh['id'],frame=sh['start']);m.camera=bpy.data.objects[sh['camera']['id']]
    sc.camera=bpy.data.objects[planned[0]];rows=[]
    from director_camera.editing import validate_cuts,motion_contract
    actual={};motion={s['id']:[] for s in plan['shots']};orient={s['id']:[] for s in plan['shots']}
    for sh in plan['shots']:
        for f in range(sh['start'],sh['end']):
            sc.frame_set(f);cam=sc.camera.evaluated_get(bpy.context.evaluated_depsgraph_get());mat=cam.matrix_world
            actual[f]=sc.camera.name;motion[sh['id']].append(list(mat.translation));orient[sh['id']].append(list(mat.to_quaternion()))
            rows.append({'frame':f,'shot':sh['id'],'camera':sc.camera.name,'position':list(mat.translation),'quaternion':list(mat.to_quaternion()),'lens_mm':cam.data.lens})
    shots=[dict(id=s['id'],start=s['start'],end=s['end']-1,camera=s['camera']['id']) for s in plan['shots']]
    cuts=validate_cuts(shots,[dict(frame=m.frame,camera=m.camera.name) for m in sc.timeline_markers if m.camera],actual)
    checks={s['id']:motion_contract(motion[s['id']],plan['fps'],s['camera']['motion']['kind'],orient[s['id']]) if len(motion[s['id']])>1 else {'status':'SINGLE_FRAME'} for s in plan['shots']}
    if cuts['status']!='PASS' or any(v['status']=='FAIL' for v in checks.values()):raise ValueError('evaluated camera QA failed; output not saved')
    sc.frame_set(plan['start']);bpy.ops.wm.save_as_mainfile(filepath=str(output),check_existing=False)
    evidence.write_text(json.dumps(dict(source_sha256=source_hash,blend_sha256=file_sha(output),old_markers=old,cuts=cuts,motion=checks,rows=rows,visual='NOT_REVIEWED',director='NOT_REVIEWED'),indent=2),encoding='utf-8')
    return rows

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--plan',required=True,type=Path);ap.add_argument('--output',required=True,type=Path);ap.add_argument('--evidence',required=True,type=Path)
    a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);execute(json.loads(a.plan.read_text(encoding='utf-8-sig')),a.output,a.evidence)
if __name__=='__main__':main()
