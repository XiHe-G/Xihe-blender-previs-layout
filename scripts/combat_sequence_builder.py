"""Shared COMBAT_DYNAMIC assembly backend. Source and text use identical data.

blender --factory-startup -b --python-exit-code 1 --python this.py -- package.json.gz --output out [--render]
No source analysis, automatic choreography, rigs, mocap, or scene-specific logic.
"""
import argparse, gzip, hashlib, json, sys
from pathlib import Path
import bpy
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0, str(Path(__file__).parent))
from combat_sequence_package import read_package, validate

def dump(path, value):
    path=Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    data=json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()
    path.write_bytes(gzip.compress(data, mtime=0) if path.suffix=='.gz' else data)

def state(o):
    d={'location':list(o.location), 'rotation_mode':o.rotation_mode,
       'rotation':list(o.rotation_quaternion if o.rotation_mode=='QUATERNION' else o.rotation_euler),
       'scale':list(o.scale), 'hide_render':o.hide_render, 'hide_viewport':o.hide_viewport}
    if o.type=='CAMERA': d['lens']=o.data.lens
    if 'previs_prop_control_index' in o:
        from prop_control_native import native_control
        d['prop_control']=native_control(o)
    if 'previs_support_index' in o:
        from support_contact_native import native_support
        d['support_contact']=native_support(o)
    return d

def apply(o,d,f=None):
    if 'support_contact' in d:
        from support_contact_native import apply_support
        apply_support(o,d['support_contact'],f)
    if 'prop_control' in d:
        from prop_control_native import apply_control
        apply_control(o,d['prop_control'],f)
    o.rotation_mode=d['rotation_mode']; o.location=d['location'];o.scale=d['scale']
    rotation='rotation_quaternion' if o.rotation_mode=='QUATERNION' else 'rotation_euler'
    setattr(o,rotation,d['rotation']);o.hide_render=d['hide_render'];o.hide_viewport=d['hide_viewport']
    if f is not None:
        for a in ('location',rotation,'scale','hide_render','hide_viewport'):o.keyframe_insert(a,frame=f)
    if 'lens' in d:
        o.data.lens=d['lens']
        if f is not None:o.data.keyframe_insert('lens',frame=f)

def fresh_assets(p):
    from character_proxy import BoxRig
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    sc=bpy.context.scene; sc.render.engine='BLENDER_WORKBENCH'
    sc.render.resolution_x=p['render']['width'];sc.render.resolution_y=p['render']['height'];sc.render.resolution_percentage=100
    sc.world.color=(.32,.36,.42);sc.display.shading.color_type='MATERIAL';sc.display.shading.background_type='WORLD'
    sc.view_settings.view_transform='Standard';sc.view_settings.look='None'
    rigs={}
    for a in p.get('actor_assets',[]):
        c=bpy.data.collections.new(a['id']);sc.collection.children.link(c)
        spec=dict(a['spec']);spec['proxy_style']='COMBAT_BOX_4'
        rigs[a['id']]=BoxRig(spec,c)
    for a in p.get('primitive_assets',[]):
        kind=a['type']
        if kind=='CUBE':bpy.ops.mesh.primitive_cube_add(size=1)
        elif kind=='SPHERE':bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=1)
        elif kind=='CAMERA':bpy.ops.object.camera_add()
        elif kind=='EMPTY':bpy.ops.object.empty_add()
        else:raise ValueError('Unsupported primitive '+kind+'; bake simple geometry to asset scene')
        o=bpy.context.object;o.name=a['id']
        if 'color' in a and o.type=='MESH':
            m=bpy.data.materials.new(a['id']);m.diffuse_color=(*a['color'][:3],1);o.data.materials.append(m)
        if 'state' in a:apply(o,a['state'])
    return rigs

def flatten(m):return [x for row in m for x in row]

def world_matrix(o):
    # Hidden viewport objects can keep stale dependency-graph matrix_world.
    # This backend rejects constraints/modifiers: compose authored TRS directly.
    r=o.rotation_quaternion if o.rotation_mode=='QUATERNION' else o.rotation_euler.to_quaternion()
    basis=Matrix.LocRotScale(o.location,r,o.scale)
    return world_matrix(o.parent)@o.matrix_parent_inverse@basis if o.parent else basis

def capture(p):
    sc=bpy.context.scene;fps=p['timebase']['fps'];rows=[]
    names=p.get('regression_objects',list(p['object_tracks']))
    for f in range(1,p['timebase']['frames']+1):
        sc.frame_set(f)
        sh=next(s for s in p['shot_plan'] if s['first_frame']<=f<s['end_frame_exclusive'])
        sc.camera=bpy.data.objects[sh['camera_id']];bpy.context.view_layer.update()
        row={'frame':f,'time_s':(f-1)/fps,'shot_id':sh['id'],'camera_id':sc.camera.name,'lens':sc.camera.data.lens,'objects':{},'screen':{}}
        for n in names:
            o=bpy.data.objects[n]
            row['objects'][n]={'world':flatten(world_matrix(o)),'state':state(o)}
        for a in p.get('actors',[]):
            points=[]
            for n in a['meshes']:
                o=bpy.data.objects[n]
                points.extend(world_to_camera_view(sc,sc.camera,world_matrix(o)@Vector(v)) for v in o.bound_box)
            xmin,xmax=min(v.x for v in points),max(v.x for v in points)
            ymin,ymax=min(v.y for v in points),max(v.y for v in points)
            row['screen'][a['id']]={'center_uv':[(xmin+xmax)/2,(ymin+ymax)/2],
                'bbox_uv':[xmin,ymin,xmax,ymax],'size_uv':[xmax-xmin,ymax-ymin],
                'depth_range':[min(v.z for v in points),max(v.z for v in points)],
                'occlusion':'projected bounds only; human visual review required'}
        rows.append(row)
    return rows

def build(p, package_path, out, render=False, identity_manifest=None):
    errors=validate(p)
    if errors:raise ValueError('\n'.join(errors))
    out=Path(out)
    if out.exists() and any(out.iterdir()):raise ValueError('Use a new empty output directory; cached frames are forbidden')
    out.mkdir(parents=True,exist_ok=True)
    asset=p.get('scene_asset')
    if asset:
        ap=(Path(package_path).parent/asset['path']).resolve()
        if hashlib.sha256(ap.read_bytes()).hexdigest()!=asset['sha256']:raise ValueError('Scene asset hash mismatch')
        bpy.ops.wm.open_mainfile(filepath=str(ap));rigs={}
    else:rigs=fresh_assets(p)
    sc=bpy.context.scene
    if any(o.type=='ARMATURE' or o.constraints or o.modifiers for o in sc.objects):
        raise ValueError('CSP simple-geometry backend rejects armatures, constraints and modifiers; bake geometry first')
    for o in sc.objects:
        if o.rotation_mode not in ('XYZ','QUATERNION') or any(abs(v)>1e-8 for v in (*o.delta_location,*o.delta_rotation_euler)) or any(abs(v-1)>1e-8 for v in o.delta_scale) or tuple(o.delta_rotation_quaternion)!=(1.,0.,0.,0.):
            raise ValueError('Bake unsupported rotation mode/delta transforms first: '+o.name)
        if o.type=='MESH' and o.data.shape_keys:raise ValueError('Shape keys are outside this simple proxy backend: '+o.name)
    # Remove every animation source. The package alone drives all new keyframes.
    for blocks in (bpy.data.objects,bpy.data.cameras,bpy.data.curves,bpy.data.meshes,bpy.data.materials,bpy.data.worlds,bpy.data.scenes):
        for block in blocks:block.animation_data_clear()
    sc.timeline_markers.clear();sc.frame_start=1;sc.frame_end=p['timebase']['frames'];sc.render.fps=p['timebase']['fps'];sc.render.fps_base=1
    for n,samples in p['object_tracks'].items():
        o=bpy.data.objects.get(n)
        if o is None:raise ValueError('Missing object '+n)
        for sample in samples:apply(o,sample['state'],sample['frame'])
    for n,samples in p.get('actor_pose_tracks',{}).items():
        if n not in rigs:raise ValueError('actor_pose_tracks requires matching COMBAT_BOX_4 actor asset')
        for sample in samples:rigs[n].apply(sample['state'],sample['frame'])
    for action in bpy.data.actions:
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in bag.fcurves:
                        for k in fc.keyframe_points:k.interpolation='CONSTANT' if 'hide_' in fc.data_path or fc.data_path in ('["previs_prop_control_index"]','["previs_support_index"]') else 'LINEAR'
    for shot in p['shot_plan']:
        marker=sc.timeline_markers.new(shot['id'],frame=shot['first_frame']);marker.camera=bpy.data.objects[shot['camera_id']]
    sc['CSP_version']=p['schema_version'];sc['CSP_entry_mode']=p['entry_mode'];sc['CSP_case']=p['sequence_id']
    fingerprint={'package_sha256':hashlib.sha256(Path(package_path).read_bytes()).hexdigest(),
        'builder_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'asset':asset,
        'blender_version':bpy.app.version_string,'frames':sc.frame_end,'fps':sc.render.fps}
    if identity_manifest is not None:
        from runtime_identity import instrument
        if identity_manifest.get('source_csp_sha256')!=fingerprint['package_sha256']:raise ValueError('STALE_IDENTITY_MANIFEST_CSP')
        fingerprint['runtime_identity']=instrument(sc,identity_manifest)
    dump(out/'build_manifest.json',fingerprint)
    dump(out/'evaluated.json.gz',capture(p))
    sc.frame_set(1);sc.camera=bpy.data.objects[p['shot_plan'][0]['camera_id']]
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'LAYOUT.blend'))
    if render:
        frames=out/'frames';frames.mkdir();sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGB'
        sc.render.filepath=str(frames/'frame_');bpy.ops.render.render(animation=True)
    return fingerprint

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('package');ap.add_argument('--output',required=True);ap.add_argument('--render',action='store_true');ap.add_argument('--identity-manifest')
    args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);build(read_package(args.package),args.package,args.output,args.render,read_package(args.identity_manifest) if args.identity_manifest else None)
