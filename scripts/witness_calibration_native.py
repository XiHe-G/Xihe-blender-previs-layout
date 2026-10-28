"""Isolated fixed-condition renderer. No camera optimization or source mutation."""
import json,gzip,math,hashlib,copy
from pathlib import Path
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(v,indent=2),encoding='utf8')
def run(spec,out):
 import bpy
 from mathutils import Vector
 from bpy_extras.object_utils import world_to_camera_view
 from contact_readability import evaluate
 from contact_readability_native import measure
 from prop_control_native import native_control
 from witness_calibration import resolve_direction,calibration_diagnostics
 out=Path(out);out.mkdir(parents=True);src=Path(spec['source_dir']);p=read(src/'CSP.json');c=next(c for c in read(src/'RESOLVED-CONTRACTS.json') if c['id']==spec['contract']);before={k:sha(src/k) for k in spec['source_hashes']};assert before==spec['source_hashes']
 # Direction is inherited from accepted author/execution evidence, never an axis default.
 oldsrc=Path(read(src/'CASE.json')['source_dir']);momentum=read(oldsrc/'MOMENTUM-RESOLVED.json')
 if c['outcome']=='CONTROLLED':direction=resolve_direction(momentum)
 else:
  a,b=c['result_window'];rows=p['object_tracks'][c['receiver']];direction=resolve_direction(positions=[rows[a-1]['state']['location'],rows[b-1]['state']['location']])
 if direction['status']!='RESOLVED':write(out/'MECHANICAL.json',{'status':'NOT_REVIEWED','reason':'Unreliable direction'});return
 c=copy.deepcopy(c);c['expected_response_direction']=direction['value'];c['provenance']='CALIBRATION explicit inherited direction; no underlying action change'
 bpy.ops.wm.open_mainfile(filepath=str(src/'LAYOUT.blend'));sc=bpy.context.scene;sc.timeline_markers.clear();start,end=spec['window'];cause=c['cause_window'][0]
 sc.frame_set(cause);bpy.context.view_layer.update();actor=bpy.data.objects[c['actor_root']];prop=bpy.data.objects[c['prop']];point=bpy.data.objects[c['contact_object']]
 force=Vector(direction['value']);force.z=0
 if force.length<1e-8:force=Vector((0,1,0))
 force.normalize();side=Vector((force.y,-force.x,0));relation=spec['relation'];toward={'SIDE':side,'THREE_QUARTER_FRONT':(side+force).normalized(),'THREE_QUARTER_REAR':(side-force).normalized(),'FRONT':force,'REAR':-force}[relation]
 center=(actor.matrix_world.translation+prop.matrix_world.translation)/2;center.z=1.1
 distance={'WIDE':15.,'MEDIUM_WIDE':9.,'MEDIUM':6.,'MEDIUM_CLOSE':4.}[spec['scale']]
 data=bpy.data.cameras.new('CALIBRATION_VIEW');cam=bpy.data.objects.new('CALIBRATION_VIEW',data);sc.collection.objects.link(cam);cam.location=center+toward*distance+Vector((0,0,spec.get('elevation',1.2)));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();data.lens=40;sc.camera=cam
 added=[]
 def cube(name,color):
  bpy.ops.mesh.primitive_cube_add(size=1);o=bpy.context.object;o.name=name;m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);o.data.materials.append(m);added.append(o);return o
 helper=None
 if spec['witness']!='POINT_ONLY':helper=cube('CALIBRATION_WITNESS',(.9,.55,.12))
 if spec['occlusion']!='CLEAR':
  wall=cube('CALIBRATION_OCCLUDER',(.35,.35,.35));wall.location=(point.matrix_world.translation+cam.location)/2;wall.rotation_euler=cam.rotation_euler;wall.scale=(.25,1.8,.1) if spec['occlusion']=='PARTIAL_OCCLUSION' else (15,15,.1)
 body=next((bpy.data.objects[n] for n in c['actor_meshes'] if 'UPPER' in n or n.endswith('__BODY')),bpy.data.objects[c['actor_meshes'][0]])
 with gzip.open(src/'NATIVE-MATRICES.json.gz','rt',encoding='utf8') as f:frozen={r['frame']:r['values'] for r in json.load(f)}
 original_names=list(p['object_tracks']);exceptions={body.name} if spec['body']!='BODY_NEUTRAL' else set();frames=[];snapshots=[];count=0;maxerr=0;controls=[]
 # Complete original metadata and matrix reference is read before any presentation change at each frame.
 for f in range(1,p['timebase']['frames']+1):
  sc.frame_set(f);bpy.context.view_layer.update();original={n:list(v for row in bpy.data.objects[n].matrix_world for v in row) for n in original_names};metadata={n:{k:str(v) for k,v in bpy.data.objects[n].items() if k.startswith('previs_')} for n in original_names}
  if body.name in exceptions:
   desired=force if spec['body']=='BODY_ALIGNED_WITH_FORCE' else -force;body.rotation_mode='QUATERNION';body.rotation_quaternion=Vector((0,1,0)).rotation_difference(desired);body.keyframe_insert('rotation_quaternion',frame=f)
  exposed=cause<=f<cause+spec['exposure'];point.hide_render=not exposed;point.keyframe_insert('hide_render',frame=f)
  if helper:
   origin=body.matrix_world.translation+Vector((0,0,.2));target=point.matrix_world.translation
   if spec['witness']=='POINT_PLUS_BODY_RESPONSE':
    # A body-linked directional contour, derived from existing recipient motion, not an arm/pose solver.
    rows=p['object_tracks'][c['actor_root']];v=Vector(rows[min(f,len(rows)-1)]['state']['location'])-Vector(rows[max(0,f-2)]['state']['location']);target=origin+Vector((0,0,.5))+(v.normalized()*.25 if v.length>1e-6 else Vector((0,0,0)))
   delta=target-origin;helper.location=(origin+target)/2;helper.rotation_mode='QUATERNION';helper.rotation_quaternion=delta.to_track_quat('Z','Y') if delta.length>1e-6 else (1,0,0,0);helper.scale=(.055,.055,max(.01,delta.length));helper.hide_render=not exposed
   for key in ('location','rotation_quaternion','scale','hide_render'):helper.keyframe_insert(key,frame=f)
  bpy.context.view_layer.update()
  for n,vs in frozen[f].items():
   if n not in exceptions:count+=16;maxerr=max(maxerr,max(abs(a-b) for a,b in zip(vs,[v for row in bpy.data.objects[n].matrix_world for v in row])))
   assert metadata[n]=={k:str(v) for k,v in bpy.data.objects[n].items() if k.startswith('previs_')},('state changed',n,f)
  control=native_control(prop)
  if c['outcome']=='FAILED' and start<=f<=end:assert not control.get('controller'),('failed attempt acquired control',f)
  controls.append({'frame':f,'controller':control.get('controller') if control else None})
  first=min(ph['frames'][0] for ph in c['phases'].values() if ph.get('frames'));last=max(ph['frames'][1] for ph in c['phases'].values() if ph.get('frames'))
  if first<=f<=last:frames.append(measure(sc,cam,c))
  if start<=f<=end:snapshots.append((f,{n:[v for row in bpy.data.objects[n].matrix_world for v in row] for n in original_names}))
 assert maxerr==0
 sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=480;sc.render.resolution_y=270;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.display.shading.color_type='MATERIAL';sc.display.render_aa='8';sc.camera=cam
 bpy.ops.wm.save_as_mainfile(filepath=str(out/'LAYOUT.blend'));bpy.ops.wm.open_mainfile(filepath=str(out/'LAYOUT.blend'));sc=bpy.context.scene;cam=bpy.data.objects['CALIBRATION_VIEW']
 for f,reference in snapshots:
  sc.frame_set(f);bpy.context.view_layer.update()
  assert all(reference[n]==[v for row in bpy.data.objects[n].matrix_world for v in row] for n in original_names),('reopen changed',f)
 # Recompute actual measurement from reopened scene, not earlier planned snapshots.
 observed=[]
 for r in frames:
  sc.frame_set(r['frame']);bpy.context.view_layer.update();observed.append(measure(sc,cam,c))
 report=evaluate(p,c,observed);sc.frame_set(cause);a=world_to_camera_view(sc,cam,center);b=world_to_camera_view(sc,cam,center+force);axis=((a.x-b.x)**2+(a.y-b.y)**2)**.5*distance
 extra={'axis_projection_ratio':axis,'cause_result_gap_frames':max(0,c['result_window'][0]-c['cause_window'][1])}
 write(out/'SPEC.json',spec);write(out/'RESOLVED-CONTRACT.json',c);write(out/'MECHANICAL.json',report);write(out/'CALIBRATION-DIAGNOSTICS.json',calibration_diagnostics(spec,report,extra));write(out/'PROVENANCE.json',{'motion_source':str(src/'LAYOUT.blend'),'contact_source':str(src/'CSP.json')+' '+c['cause_ref'],'direction_source':direction,'camera_source':'EXPLICIT_TEST_MATRIX fixed transform','threshold_source':'UNCHANGED_S006_TECHNICAL_DEFAULT','review_source':'NONE / PENDING_HUMAN_REVIEW'})
 write(out/'INVARIANTS.json',{'status':'PASS','values_compared':count,'max_error':maxerr,'explicit_body_yaw_exception':list(exceptions),'witness_visibility_exception':c['contact_object'],'control_support_momentum_metadata_exact':True,'saved_reopened':True,'source_hashes':before})
 write(out/'CAMERA-OBSERVATION.json',{'position':list(cam.location),'rotation':list(cam.rotation_euler),'lens':cam.data.lens,'scale_label':spec['scale'],'mechanical':report,'human_review':'PENDING_HUMAN_REVIEW','not_written_to_benchmark':True})
 with gzip.open(out/'TRACE.json.gz','wt',encoding='utf8') as f:json.dump(observed,f)
 write(out/'CONTROL-TRACE.json',controls);images=out/'frames';images.mkdir()
 for index,f in enumerate(range(start,end+1),1):sc.frame_set(f);sc.camera=cam;sc.render.filepath=str(images/f'{index:04d}.png');bpy.ops.render.render(write_still=True)
 assert all(sha(src/k)==h for k,h in before.items())
 print(spec['id'],report['status'],flush=True)
