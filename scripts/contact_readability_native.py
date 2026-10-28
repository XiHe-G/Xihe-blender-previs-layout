"""Read-only native camera evidence. Reuses S3 projection and ray sampling."""
from actual_trace_exporter import geometry,sample_occlusion
from screen_projection import project_mesh,summarize_projection
from prop_control_native import native_control
def measure(scene,camera,c):
 import bpy
 from bpy_extras.object_utils import world_to_camera_view
 dep=bpy.context.evaluated_depsgraph_get()
 def view(names):
  objects=[bpy.data.objects[n] for n in names];visible=[o for o in objects if not o.hide_render]
  g=geometry(visible,dep);s=summarize_projection(project_mesh(scene,camera,g[0],g[2]));s.update(sample_occlusion(scene,dep,camera,g[0],{o.name for o in visible}));return s
 root=bpy.data.objects[c['receiver']];q=world_to_camera_view(scene,camera,root.matrix_world.translation);state=native_control(bpy.data.objects[c['prop']])
 from mathutils import Vector
 gap=(bpy.data.objects[c['contact_object']].matrix_world.translation-(bpy.data.objects[c['prop']].matrix_world.translation+Vector(c['handle_offset']))).length
 return {'frame':scene.frame_current,'actor':view(c['actor_meshes']),'prop':view([c['prop']]),'contact':view([c['contact_object']]),'contact_gap':gap,'contact_radius':c['contact_radius'],'receiver_world':list(root.matrix_world.translation),'receiver_screen':list(q[:2]) if camera.data.clip_start<=q.z<=camera.data.clip_end else None,'controller':None if state is None else state.get('controller') or '', 'camera':camera.name,'method':'REUSED_S3_EVALUATED_MESH_PROJECTION_AND_ESTIMATED_CAMERA_RAYS'}
