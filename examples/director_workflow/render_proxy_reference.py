"""Render anonymous reference sheets from the distributed BoxRig, in a new scene."""
from pathlib import Path
import sys
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from character_proxy import BoxRig

if bpy.data.filepath:
    raise ValueError('Run without an input .blend; this script creates new reference scenes.')
dest = ROOT / 'assets' / 'approved-layout-style'
dest.mkdir(parents=True, exist_ok=True)
for stem, style, color in [('narrative', 'NARRATIVE_BOX_5', [.16,.56,.68]), ('combat', 'COMBAT_BOX_4', [.75,.28,.38])]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.world = bpy.data.worlds.new('NeutralWorld')
    for i, yaw in enumerate([0, 50, 140]):
        rig = BoxRig(dict(id=f'ACTOR_{i+1}', height=2, proxy_style=style, color=color), sc.collection)
        rig.apply(dict(position=[(i-1)*1.6,0,0],yaw=yaw), 1)
    bpy.ops.mesh.primitive_plane_add(size=200, location=[0,0,-.01])
    floor=bpy.context.object; floor.name='Ground'; floor.color=(.14,.17,.22,1)
    bpy.ops.object.camera_add(location=[0,8,4])
    cam=bpy.context.object; cam.name='ReferenceCamera'
    cam.rotation_euler=(Vector([0,0,1])-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.type='ORTHO'; cam.data.ortho_scale=6.2; sc.camera=cam
    sc.render.engine='BLENDER_WORKBENCH'
    sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL'
    sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True
    sc.display.shading.background_type='WORLD';sc.world.color=(.1,.12,.16)
    sc.render.resolution_x=1100;sc.render.resolution_y=550;sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG';sc.render.film_transparent=False
    sc.render.filepath=str(dest / f'{stem}-model.png')
    sc.frame_set(1);bpy.ops.render.render(write_still=True)
