"""Read-only bpy measurement from a saved scene. Does not read execution tracks.

The measurement binding supplies names/author IDs, never sampled transforms.
Event labels are registered windows, explicitly NOT observed action phases.
"""
import argparse,hashlib,json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).parent))
from combat_sequence_package import read_package
from combat_sequence_builder import dump
from timebase import frame_to_time
from runtime_identity import identity
from screen_projection import project_mesh,summarize_projection,occlusion_label,bounds_gap
from motion_analysis import norm,distance,velocity,quaternion_angle

def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def filehash(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def geometry(objects,dep):
    verts=[];faces=[];edges=[]
    for obj in objects:
        if obj.type!='MESH':continue
        ev=obj.evaluated_get(dep);mesh=ev.to_mesh()
        try:
            off=len(verts);verts.extend(ev.matrix_world@v.co for v in mesh.vertices)
            faces.extend(tuple(off+i for i in p.vertices) for p in mesh.polygons)
            edges.extend(tuple(off+i for i in e.vertices) for e in mesh.edges)
        finally:ev.to_mesh_clear()
    return verts,faces,edges,BVHTree.FromPolygons(verts,faces) if faces else None

def inside(point,bvh):
    # Odd ray parity on closed proxy surfaces; edge ambiguity remains documented.
    direction=Vector((.9238795,.317,.211)).normalized();origin=point.copy();count=0
    for _ in range(128):
        hit=bvh.ray_cast(origin,direction)
        if hit[0] is None:return count%2==1
        count+=1;origin=hit[0]+direction*1e-5
    return None

def pair_measure(a,b):
    av,af,ae,at=a;bv,bf,be,bt=b
    if not at or not bt:return dict(geometry_clearance=None,contact=None,method='UNAVAILABLE')
    overlap=bool(at.overlap(bt))
    if not overlap:overlap=inside(av[0],bt) or inside(bv[0],at)
    nearest=min([bt.find_nearest(v)[3] for v in av]+[at.find_nearest(v)[3] for v in bv])
    overlap=bool(overlap or nearest<=1e-6)
    return dict(geometry_clearance=0. if overlap else nearest,contact=overlap,method='TRIANGLE_INTERSECTION_CONTAINMENT_AND_VERTEX_SURFACE_DISTANCE_ESTIMATED')

def sample_occlusion(scene,dep,camera,points,names):
    from bpy_extras.object_utils import world_to_camera_view
    samples=[]
    for p in points:
        q=world_to_camera_view(scene,camera,p)
        if camera.data.clip_start<=q.z<=camera.data.clip_end and 0<=q.x<=1 and 0<=q.y<=1:samples.append(p)
    if not samples:return occlusion_label(0,0)
    samples=[samples[i*(len(samples)-1)//min(16,len(samples)-1)] for i in range(min(17,len(samples)))] if len(samples)>1 else samples
    visible=0
    for point in samples:
        origin=camera.matrix_world.translation.copy()
        if camera.data.type=='ORTHO':
            v=camera.matrix_world.inverted()@point;v.z=0;origin=camera.matrix_world@v
        direction=(point-origin).normalized();limit=(point-origin).length+1e-4
        for _ in range(32):
            hit,loc,normal,index,obj,matrix=scene.ray_cast(dep,origin,direction,distance=limit)
            if not hit:visible+=1;break
            if obj.name in names:visible+=1;break
            if not obj.hide_render:break
            step=(loc-origin).length+1e-4;origin=loc+direction*1e-4;limit-=step
            if limit<=0:visible+=1;break
    return occlusion_label(visible,len(samples))

def export_trace(binding,blend_path,frame_range=None):
    scene=bpy.context.scene;fps=scene.render.fps/scene.render.fps_base
    if abs(fps-binding['timebase']['fps'])>1e-8:raise ValueError('TRACE_TIMEBASE_MISMATCH')
    if scene.frame_start!=1:raise ValueError('Unsupported native frame origin')
    lo,hi=frame_range or [scene.frame_start,scene.frame_end]
    rows=[];previous=None
    inverse={v:k for k,v in binding['shot_ids'].items()};markers=sorted((m.frame,m) for m in scene.timeline_markers if m.camera)
    if not markers:raise ValueError('NO_NATIVE_CAMERA_CUT_MARKERS')
    for frame in range(lo,hi+1):
        scene.frame_set(frame);bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get()
        eligible=[m for f,m in markers if f<=frame]
        if not eligible:raise ValueError('NO_ACTIVE_NATIVE_CUT')
        marker=eligible[-1];camera=marker.camera.evaluated_get(dep);shot=inverse.get(marker.name)
        if shot is None:raise ValueError('UNKNOWN_NATIVE_SHOT '+marker.name)
        time=frame_to_time(frame,int(fps));campos=list(camera.matrix_world.translation);camq=list(camera.matrix_world.to_quaternion())
        row=dict(shot_id=shot,frame=frame,time=time,entities={},pairwise_distance={},
          camera_transform=dict(object=camera.name,position=campos,quaternion=camq),camera_lens=camera.data.lens,
          camera_motion=None,event_state=[dict(event_id=e['event_id'],basis='REGISTERED_WINDOW_ONLY_NOT_PHASE_DETECTION') for e in binding.get('events',[]) if e['start']<=time<e['end']])
        if previous and previous['shot_id']==shot:
            dt=time-previous['time'];cp=previous['camera_transform'];row['camera_motion']=dict(translation=distance(campos,cp['position']),speed=distance(campos,cp['position'])/dt,rotation_deg=quaternion_angle(camq,cp['quaternion']))
        geo={}
        for id,spec in binding['views'].items():
            root=bpy.data.objects.get(spec['root']);objects=[bpy.data.objects[n] for n in spec['objects'] if n in bpy.data.objects]
            exists=root is not None and len(objects)==len(spec['objects'])
            entry=dict(entity_id=spec['entity_id'],exists=exists,object_ids=[o.name for o in objects],identity_token=[str(o.as_pointer()) for o in objects],
                entity_world_state=None,screen_bounds=None,screen_center=None,screen_height_ratio=None,screen_width_ratio=None,
                visibility='HIDDEN',occlusion_ratio=None,motion_vector_world=None,motion_vector_screen=None,speed_world=None,speed_screen=None,
                proxy_state=None,ownership_state=None)
            if not exists:row['entities'][id]=entry;continue
            ev=root.evaluated_get(dep);mat=ev.matrix_world;position=list(mat.translation);quat=list(mat.to_quaternion());axis=mat.to_quaternion()@Vector((0,0,1))
            entry['entity_world_state']=dict(position=position,quaternion=quat,scale=list(mat.to_scale()),tilt_deg=math.degrees(math.acos(max(-1,min(1,axis.z)))))
            visible_objects=[o for o in objects if not o.hide_render]
            # Retain actual geometry even when hidden; visibility remains separately explicit.
            geo[id]=geometry(objects,dep);points=project_mesh(scene,camera,geo[id][0],geo[id][2]);screen=summarize_projection(points)
            entry.update(screen_bounds=screen,screen_center=screen['screen_center'],screen_height_ratio=screen['screen_height_ratio'],screen_width_ratio=screen['screen_width_ratio'])
            occ=sample_occlusion(scene,dep,camera,geometry(visible_objects,dep)[0],{o.name for o in visible_objects}) if visible_objects and screen['clipped_bounds'] else occlusion_label(0,0)
            entry.update(visibility=occ['visibility'],occlusion_ratio=occ['occlusion_ratio'],occlusion=occ)
            entry['proxy_state']=dict(render_enabled=bool(visible_objects),hidden_objects=[o.name for o in objects if o.hide_render],native_parent=root.parent.name if root.parent else None)
            native=identity(root,spec);native_owner=native.pop('native_owner');entry.update(native)
            owner_root=bpy.data.objects.get(spec.get('owner_root',''))
            entry['ownership_state']=dict(native_owner=native_owner,registered_owner=spec.get('owner_id'),authority='NATIVE_OBJECT_PROPERTY' if native_owner else 'REGISTERED_METADATA_ONLY',
                evidence_strength='STRONG_REGISTRATION_EVIDENCE' if native_owner else 'WEAK_EVIDENCE',
                owner_local_position=list(owner_root.evaluated_get(dep).matrix_world.inverted_safe()@mat.translation) if owner_root else None,
                owner_distance=distance(position,list(owner_root.evaluated_get(dep).matrix_world.translation)) if owner_root else None,
                owner_relative=[position[i]-owner_root.evaluated_get(dep).matrix_world.translation[i] for i in range(3)] if owner_root else None)
            if previous and id in previous['entities'] and previous['entities'][id]['exists']:
                old=previous['entities'][id];dt=time-previous['time'];v=velocity(position,old['entity_world_state']['position'],dt)
                entry.update(motion_vector_world=v,speed_world=norm(v))
                if previous['shot_id']==shot and screen['screen_center'] and old['screen_center']:
                    v=velocity(screen['screen_center'],old['screen_center'],dt);entry.update(motion_vector_screen=v,speed_screen=norm(v))
            row['entities'][id]=entry
        for a,b in binding.get('pairs',[]):
            if a not in geo or b not in geo:continue
            result=pair_measure(geo[a],geo[b]);aa=row['entities'][a];bb=row['entities'][b]
            result['screen_center_distance']=distance(aa['screen_center'],bb['screen_center']) if aa['screen_center'] and bb['screen_center'] else None
            result['screen_bounds_gap_estimate']=bounds_gap(aa['screen_bounds']['clipped_bounds'],bb['screen_bounds']['clipped_bounds'])
            result['both_render_enabled']=aa['proxy_state']['render_enabled'] and bb['proxy_state']['render_enabled']
            row['pairwise_distance'][a+'|'+b]=result
        rows.append(row);previous=row
        if frame%100==0:print('TRACE_FRAME',frame,flush=True)
    return dict(schema_version='ACTUAL-TRACE/1.0',graph_id=binding['graph_id'],measurement_binding_sha256=digest(binding),
      source_blend=dict(path=str(Path(blend_path).resolve()),sha256=filehash(blend_path)),timebase=binding['timebase'],
      sampling=dict(mode='EVERY_FRAME',first_frame=lo,last_frame=hi,screen_motion_resets_at_cut=True),
      methods=dict(screen='EVALUATED_MESH_PROJECTED_RECT_ESTIMATE',occlusion='ESTIMATED_17_CAMERA_RAYS',geometry='BVH triangle intersections + containment; clearance vertex-to-surface estimate; no swept collision',implementation_sha256={name:filehash(Path(__file__).parent/name) for name in ['actual_trace_exporter.py','screen_projection.py','motion_analysis.py','timebase.py','runtime_identity.py']}),frames=rows)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--blend',required=True);ap.add_argument('--binding',required=True);ap.add_argument('--output',required=True);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
    before=filehash(a.blend);bpy.ops.wm.open_mainfile(filepath=str(Path(a.blend).resolve()))
    trace=export_trace(read_package(a.binding),a.blend);dump(a.output,trace)
    assert filehash(a.blend)==before,'SOURCE_BLEND_MUTATED'
    print('ACTUAL_TRACE_EXPORTED',len(trace['frames']),flush=True)
