"""Read evaluated Blender motion for explicit bindings. Never saves the scene.

blender -b candidate.blend --python scripts/action_expression_native.py --
  --job native-job.json --output new-native-report.json
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
from action_expression import contact_evidence
from action_readability import measure_readability


def inspect(job):
    scene=bpy.context.scene;original_frame=scene.frame_current;original_camera=scene.camera
    fps=scene.render.fps/scene.render.fps_base
    first=job.get('first_frame',scene.frame_start);last=job.get('last_frame',scene.frame_end)
    if not isinstance(first,int) or not isinstance(last,int) or not scene.frame_start<=first<last<=scene.frame_end:
        raise ValueError('INVALID_NATIVE_WINDOW')
    actors=job['actors'];names=[a['id'] for a in actors]
    if not names or len(names)!=len(set(names)):raise ValueError('INVALID_ACTOR_BINDINGS')
    required=[a['root'] for a in actors]+[n for a in actors for n in a['meshes']]+job.get('landmarks',[])
    required += [c[k] for c in job.get('contacts',[]) for k in ('source_object','target_object')]
    for name in required:
        if name not in bpy.data.objects:raise ValueError('MISSING_NATIVE_OBJECT '+name)
    markers=sorted((m.frame,m.name,m.camera) for m in scene.timeline_markers if m.camera)
    if len({f for f,_,_ in markers})!=len(markers):raise ValueError('AMBIGUOUS_CAMERA_CUT')
    traces={a['id']:[] for a in actors};witnesses={c['id']:[] for c in job.get('contacts',[])}
    try:
        for frame in range(first,last+1):
            scene.frame_set(frame)
            applicable=[m for m in markers if m[0]<=frame]
            shot=applicable[-1] if applicable else (scene.frame_start,'SCENE_CAMERA',original_camera)
            if shot[2] is None:raise ValueError('NO_CAMERA')
            scene.camera=shot[2];bpy.context.view_layer.update();depsgraph=bpy.context.evaluated_depsgraph_get()
            camera=scene.camera.evaluated_get(depsgraph)
            def evaluated(name):return bpy.data.objects[name].evaluated_get(depsgraph)
            landmarks={}
            for name in job.get('landmarks',[]):
                o=evaluated(name);uv=world_to_camera_view(scene,camera,o.matrix_world.translation)
                landmarks[name]=[uv.x,uv.y] if not o.hide_render and uv.z>0 and 0<=uv.x<=1 and 0<=uv.y<=1 else None
            for actor in actors:
                root=evaluated(actor['root']);parts=[evaluated(n) for n in actor['meshes']]
                if not parts or any(o.type!='MESH' for o in parts):raise ValueError('EXPLICIT_MESH_BINDINGS_REQUIRED')
                vertices=[o.matrix_world@Vector(v) for o in parts for v in o.bound_box]
                projected=[world_to_camera_view(scene,camera,v) for v in vertices]
                xmin=min(p.x for p in projected);xmax=max(p.x for p in projected)
                ymin=min(p.y for p in projected);ymax=max(p.y for p in projected)
                traces[actor['id']].append(dict(frame=frame,shot_id=shot[1],position=list(root.matrix_world.translation),
                    center_uv=[(xmin+xmax)/2,(ymin+ymax)/2],height_uv=ymax-ymin,
                    visible=not root.hide_render and all(not o.hide_render for o in parts) and all(p.z>0 for p in projected) and xmin>=0 and xmax<=1 and ymin>=0 and ymax<=1,
                    landmark_uv=landmarks))
            for c in job.get('contacts',[]):
                if frame==c['frame']:
                    points={k:list(evaluated(c[k+'_object']).matrix_world@Vector(c.get(k+'_local',[0,0,0]))) for k in ('source','target')}
                    witnesses[c['id']].append(dict(frame=frame,source_point=points['source'],target_point=points['target']))
        metrics={a['id']:measure_readability(traces[a['id']],fps,a['body_height'],job['meters_per_unit']) for a in actors}
        contacts={c['id']:contact_evidence(witnesses[c['id']],c['frame'],c['tolerance']) for c in job.get('contacts',[])}
        return dict(blender_version=bpy.app.version_string,source_blend=bpy.data.filepath,fps=fps,
                    window=[first,last],metrics=metrics,contacts=contacts,traces=traces,
                    scope='Evaluated bounds and control points; occlusion, mesh collision and artistic judgement not measured',
                    visual_review='NOT_REVIEWED',director_approval='PENDING')
    finally:
        scene.frame_set(original_frame);scene.camera=original_camera


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--job',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);out=Path(args.output)
    if out.exists():raise FileExistsError('Use a new report version')
    result=inspect(json.loads(Path(args.job).read_text(encoding='utf-8')))
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({'report':str(out),'actors':list(result['metrics']),'contacts':result['contacts']}))
