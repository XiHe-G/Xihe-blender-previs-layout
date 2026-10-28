"""Independent text-origin integration fixtures, not an EP03 coordinate replay."""
import sys,json,math
from pathlib import Path
import argparse
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True,type=Path);ap.add_argument('--render',action='store_true');args=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
R=args.output.resolve();R.mkdir(parents=True,exist_ok=False);(R/'fixtures').mkdir();(R/'evidence').mkdir()
S=Path(__file__).resolve().parents[2];sys.path.insert(0,str(S/'scripts'))
import bpy
if bpy.data.filepath:raise ValueError("Run this NEW_SCENE fixture without an input Blend; never reset a production file")
from mathutils import Vector
from execute_director_cameras import execute
from director_camera.native import curves
from director_camera.workflow import file_sha
from director_camera.review_contracts import facing_relation

def box(name,loc,scale,color):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.color=(*color,1);return o
def person(name,pos,color):
    root=bpy.data.objects.new(name,None);bpy.context.scene.collection.objects.link(root);root.location=pos
    body=box(name+'_body',(0,0,.65),(.48,.35,1.3),color)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=.24,location=(0,0,1.55));head=bpy.context.object;head.name=name+'_head';head.color=(*color,1)
    eyes=box(name+'_eyes',(0,-.224,1.58),(.3,.04,.055),(.05,.05,.05))
    chest=box(name+'_chest',(0,-.184,1.1),(.22,.035,.06),(.7,.7,.7))
    bpy.ops.mesh.primitive_cone_add(vertices=8,radius1=.07,radius2=0,depth=.16,location=(0,-.3,1.51),rotation=(math.pi/2,0,0));nose=bpy.context.object;nose.name=name+'_nose';nose.color=(*color,1)
    for o in [body,head,eyes,chest,nose]:o.parent=root
    return root
def motion(kind,a,b,aim0,aim1=None,**kw):return dict(kind=kind,start=a,end=b,aim_start=aim0,aim_end=aim1 or aim0,**kw)
def shot(sid,start,end,lens,m,purpose,focus,enter,leave,eventframe):
    return dict(id=sid,start=start,end=end,purpose=purpose,first_focus=focus,start_read=enter,end_read=leave,cut_reason='new information or reaction',source='independent authored text brief',events=[dict(id=sid+'_beat',frame=eventframe,observable=leave)],camera=dict(id='NEW_'+sid,lens_mm=lens,motion=m,movement_reason='maintain action and reaction readability'))
def sample(names):
    out=[];sc=bpy.context.scene
    for f in range(1,145):
        sc.frame_set(f);out.append([f,[[n,[list(row) for row in bpy.data.objects[n].matrix_world]] for n in names]])
    return out
results=[]
for variant in ['dialogue','threat']:
    out=R/'fixtures'/variant;out.mkdir(exist_ok=False)
    bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene;sc.frame_start=1;sc.frame_end=144;sc.render.fps=24
    sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=854;sc.render.resolution_y=480;sc.render.resolution_percentage=100
    sc.display.shading.light='STUDIO';sc.display.shading.color_type='OBJECT';sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True
    sc.world=bpy.data.worlds.new('NeutralWorld');box('support',(0,0,-.15),(8,7,.3),(.22,.24,.28))
    box('back_wall',(0,2.8,1.4),(8,.2,2.8),(.28,.30,.34))
    a=person('Courier',(-.9,0,0),(.25,.52,.62));b=person('Keeper',(.9,0,0),(.65,.42,.23));a.rotation_euler.z=math.pi/2;b.rotation_euler.z=-math.pi/2
    bpy.context.view_layer.update()
    for actor,target in [(a,b),(b,a)]:
        forward=actor.matrix_world.to_3x3()@Vector((0,-1,0));direction=(target.location-actor.location).normalized()
        assert facing_relation(tuple(forward),tuple(actor.location),tuple(target.location),1)["status"]=="WITHIN_REQUESTED_CONE","local proxy front must face the other actor"
    for o in [a,b]:o.keyframe_insert('location',frame=1);o.keyframe_insert('rotation_euler',frame=1)
    if variant=='dialogue':
        brief='Courier asks the Keeper for passage. Keeper hesitates, looks away, then returns attention. Courier notices the decision. Three shots: relationship, response, recognition. Quiet holds are intentional.'
        b.keyframe_insert('rotation_euler',frame=55);b.rotation_euler.z=-.9;b.keyframe_insert('rotation_euler',frame=78);b.keyframe_insert('rotation_euler',frame=90);b.rotation_euler.z=-math.pi/2;b.keyframe_insert('rotation_euler',frame=104)
        shots=[shot('relation',1,49,40,motion('STATIC_HOLD',[0,-5,1.55],[0,-5,1.55],[0,0,1.15]),'establish request','both','shared space','keeper hears',30),shot('answer',49,105,58,motion('STATIC_HOLD',[-.4,-3,1.55],[-.4,-3,1.55],[.9,0,1.45]),'read hesitation','Keeper','listening','returns gaze',78),shot('recognition',105,145,58,motion('STRAIGHT_TRANSLATION',[.25,-3.4,1.5],[.1,-3.05,1.5],[-.9,0,1.4],[-.9,0,1.4],curve='EASE_IN_OUT'),'read response','Courier','waiting','recognition',125)]
    else:
        brief='Keeper blocks the lane with a horizontal bar already held across it. Courier notices the barrier, moves sideways around its end, then settles beyond it. The camera holds the relationship, tracks on a straight line, and cuts to the result. No fake impact or decorative VFX.'
        bar=box('barrier',(.35,0,1),(1.8,.12,.12),(.65,.6,.4))
        a.keyframe_insert('location',frame=30);a.location=(-.9,-1.4,0);a.keyframe_insert('location',frame=66);a.location=(1.8,-1.4,0);a.keyframe_insert('location',frame=112);a.keyframe_insert('location',frame=144)
        shots=[shot('notice',1,49,36,motion('STATIC_HOLD',[0,-5,1.9],[0,-5,1.9],[0,0,.9]),'establish blocked lane','Courier and barrier','lane','lateral choice',30),shot('evade',49,113,40,motion('STRAIGHT_TRANSLATION',[-.9,-5,1.55],[1.8,-5,1.55],[-.9,0,1],[1.8,0,1],curve='EASE_IN_OUT'),'show bypass','Courier','outside bar end','passes lane',85),shot('result',113,145,40,motion('STATIC_HOLD',[0,-5.5,2],[0,-5.5,2],[.9,-.7,1]),'show regained space','both','separated','settled',130)]
    for o in [a,b]:
        if o.animation_data:
            for fc in curves(o.animation_data.action):
                for key in fc.keyframe_points:key.interpolation='LINEAR'
    plan=dict(schema='DIRECTOR_PLAN/1',fps=24,start=1,end=145,frame_convention='HALF_OPEN',shots=shots)
    (out/'BRIEF.txt').write_text(brief,encoding='utf-8');(out/'plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
    names=[o.name for o in sc.objects];before=sample(names)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'BASELINE.blend'))
    execute(plan,out/'LAYOUT.blend',out/'NATIVE.json')
    assert sample(names)==before,'camera adapter altered protected scene'
    bpy.ops.wm.open_mainfile(filepath=str(out/'LAYOUT.blend'));assert sample(names)==before,'reopened scene mismatch'
    sc=bpy.context.scene;sc.render.image_settings.file_format='PNG';sc.render.filepath=str(out/'frames'/'frame_');(out/'frames').mkdir()
    if args.render:bpy.ops.render.render(animation=True)
    results.append(dict(case=variant,frames=144,protected_scene='STRICT_EQUAL',saved_reopen='PASS',blend_sha256=file_sha(out/'LAYOUT.blend'),artistic='PENDING_REVIEW'))
(R/'evidence/FIXTURES.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print('NATIVE_FIXTURES_PASS')
