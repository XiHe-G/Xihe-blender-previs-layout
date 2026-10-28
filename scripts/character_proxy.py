"""Simple hierarchical proxy builders and baked blocking-grade performance."""

from __future__ import annotations

import math
from typing import Any

import bpy
from mathutils import Matrix, Vector

import motion_builder


V = Vector


def _material(name: str, color: list[float], roughness: float = 0.82):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.diffuse_color = (*color[:3], 1.0)
    material.use_nodes = True
    node = material.node_tree.nodes.get("Principled BSDF")
    node.inputs["Base Color"].default_value = (*color[:3], 1.0)
    node.inputs["Roughness"].default_value = roughness
    return material


def _link(object_, name: str, collection, material=None):
    object_.name = name
    for old in list(object_.users_collection):
        old.objects.unlink(object_)
    collection.objects.link(object_)
    if material and object_.type == "MESH":
        object_.data.materials.clear(); object_.data.materials.append(material)
    return object_


def _sphere(name, collection, material, segments=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=6)
    return _link(bpy.context.object, name, collection, material)


def _segment_mesh(name, collection, material):
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=1.0, radius2=0.86, depth=1.0)
    return _link(bpy.context.object, name, collection, material)


def _empty(name, collection):
    object_ = bpy.data.objects.new(name, None); collection.objects.link(object_)
    object_.empty_display_size = 0.12
    return object_


def _matrix(location, rotation=None, scale=None):
    return Matrix.LocRotScale(V(location), rotation or Matrix.Identity(3).to_quaternion(), V(scale or (1, 1, 1)))


def _place_world(object_, world_matrix: Matrix, frame: int | None = None):
    if object_.parent:
        local = object_.parent.matrix_world.inverted() @ world_matrix
    else:
        local = world_matrix
    location, rotation, scale = local.decompose()
    object_.rotation_mode = "QUATERNION"
    object_.location = location; object_.rotation_quaternion = rotation; object_.scale = scale
    if frame is not None:
        object_.keyframe_insert("location", frame=frame)
        object_.keyframe_insert("rotation_quaternion", frame=frame)
        object_.keyframe_insert("scale", frame=frame)
    bpy.context.view_layer.update()


def _segment_matrix(a, b, radius):
    a, b = V(a), V(b); delta = b - a
    return _matrix((a + b) * 0.5, delta.to_track_quat("Z", "Y"), (radius, radius, delta.length))


def _ik(a, b, first, second, pole):
    a, b, pole = V(a), V(b), V(pole)
    delta = b - a; distance = max(0.0001, delta.length); direction = delta.normalized()
    reach = min(first + second - 0.0001, max(abs(first - second) + 0.0001, distance))
    along = (first * first - second * second + reach * reach) / (2 * reach)
    height = math.sqrt(max(0.0, first * first - along * along))
    pole = pole - direction * pole.dot(direction)
    if pole.length < 0.0001:
        pole = V((1, 0, 0))
    return a + direction * along + pole.normalized() * height


def _blend(a, b, t):
    if isinstance(a, Vector):
        return a.lerp(b, t)
    return a * (1.0 - t) + b * t


def _pose(h: float, name: str) -> dict[str, Any]:
    name = name.upper()
    data = {
        "pelvis": V((0, 0, h * 0.52)), "neck": V((0, 0, h * 0.84)), "head": V((0, 0.015 * h, h * 0.93)),
        "foot_L": V((-h * .085, .015 * h, h * .045)), "foot_R": V((h * .085, -.015 * h, h * .045)),
        "wrist_L": V((-h * .255, .025 * h, h * .48)), "wrist_R": V((h * .255, .025 * h, h * .48)),
        "lean": 0.0, "head_pitch": 0.0,
    }
    if name == "CROUCH":
        data.update(pelvis=V((0, 0, h * .39)), neck=V((0, h * .07, h * .67)), head=V((0, h * .10, h * .77)), lean=15.0,
                    wrist_L=V((-h*.28,h*.11,h*.40)), wrist_R=V((h*.28,h*.11,h*.40)))
    elif name == "KNEEL":
        data.update(pelvis=V((0,-h*.025,h*.31)), neck=V((0,h*.015,h*.60)), head=V((0,h*.035,h*.70)),
                    foot_L=V((-h*.09,-h*.18,h*.04)), foot_R=V((h*.09,-h*.18,h*.04)),
                    wrist_L=V((-h*.25,h*.17,h*.31)), wrist_R=V((h*.25,h*.17,h*.31)), lean=8.0)
    elif name == "BOW":
        data.update(pelvis=V((0,-h*.025,h*.29)), neck=V((0,h*.25,h*.34)), head=V((0,h*.37,h*.27)),
                    foot_L=V((-h*.09,-h*.18,h*.04)), foot_R=V((h*.09,-h*.18,h*.04)),
                    wrist_L=V((-h*.18,h*.39,h*.045)), wrist_R=V((h*.18,h*.39,h*.045)), lean=84.0, head_pitch=58.0)
    elif name == "SIT":
        data.update(pelvis=V((0,0,h*.33)), neck=V((0,0,h*.64)), head=V((0,.01*h,h*.74)),
                    foot_L=V((-h*.1,h*.32,h*.045)), foot_R=V((h*.1,h*.32,h*.045)))
    elif name in {"LIE", "CORPSE"}:
        data.update(pelvis=V((0,-h*.08,h*.13)), neck=V((0,h*.25,h*.14)), head=V((0,h*.41,h*.145)),
                    foot_L=V((-h*.18,-h*.45,h*.045)), foot_R=V((h*.22,-h*.42,h*.045)),
                    wrist_L=V((-h*.32,h*.18,h*.045)), wrist_R=V((h*.29,h*.25,h*.045)), lean=88.0)
    return data


def _pose_blend(h, a, b, t):
    first, second = _pose(h, a), _pose(h, b)
    return {key: _blend(first[key], second[key], t) for key in first}


def _rise_pose(h: float, progress: float, source_pose: str) -> dict[str, Any]:
    # Explicit support, plant, weight transfer, extension and settle poses.
    keys = [
        (0.0, _pose(h, "BOW" if source_pose == "BOW" else "KNEEL")),
        (.22, _pose_blend(h, source_pose, "CROUCH", .24)),
        (.46, _pose_blend(h, "KNEEL", "CROUCH", .72)),
        (.72, _pose_blend(h, "CROUCH", "STAND", .67)),
        (1.0, _pose(h, "STAND")),
    ]
    for (a, first), (b, second) in zip(keys, keys[1:]):
        if progress <= b:
            t = motion_builder.smooth((progress - a) / max(.001, b - a))
            data = {key: _blend(first[key], second[key], t) for key in first}
            if .20 < progress < .53:
                # Plant left foot first; right hand remains a visible support.
                data["foot_L"].y += h * .24 * motion_builder.smooth((progress-.20)/.33)
                data["foot_L"].z += h * .07 * math.sin(math.pi * motion_builder.clamp((progress-.18)/.24))
                data["wrist_R"].z = min(data["wrist_R"].z, h * (.07 + .28 * motion_builder.smooth((progress-.33)/.35)))
            if .52 < progress < .82:
                data["foot_R"].y += h * .15 * motion_builder.smooth((progress-.52)/.30)
                data["foot_R"].z += h * .055 * math.sin(math.pi * motion_builder.clamp((progress-.52)/.30))
            return data
    return keys[-1][1]


class BipedRig:
    def __init__(self, character: dict[str, Any], collection):
        self.character = character; self.h = float(character["height"]); self.id = character["id"]
        color = list(character["color"]); self.body_mat = _material("MAT_" + self.id, color)
        self.joint_mat = _material("MAT_" + self.id + "_JOINT", [max(.02, value*.43) for value in color])
        self.face_mat = _material("MAT_DIRECTION", [.92,.94,.88]); self.dark_mat = _material("MAT_EYES", [.012,.018,.025])
        self.root = _empty("CHAR_" + self.id, collection); self.root["character_id"] = self.id
        self.root["display_name"] = character["display_name"]; self.root["proxy_type"] = character["proxy_type"]
        self.root["height"] = self.h
        self.parts: dict[str, Any] = {}
        def add(key, kind="sphere", material=None, parent=None):
            object_ = (_sphere if kind == "sphere" else _segment_mesh)(self.id+"__"+key, collection, material or self.body_mat)
            # Visible parts stay below the character root. Parenting scaled
            # segment meshes to other non-uniformly scaled meshes introduces
            # shear on Blender evaluation and turns limbs into long spikes.
            # The root still gives every proxy one movable hierarchy while the
            # baked part transforms remain stable at every frame.
            object_.parent = self.root; object_.matrix_parent_inverse = Matrix.Identity(4)
            object_["character_id"] = self.id; object_["proxy_part"] = key
            self.parts[key] = object_; return object_
        pelvis=add("PELVIS"); torso=add("TORSO", parent=pelvis); head=add("HEAD", parent=torso)
        add("NOSE", material=self.face_mat, parent=head); add("EYE_L", material=self.dark_mat, parent=head); add("EYE_R", material=self.dark_mat, parent=head)
        add("CHEST_DIRECTION", material=self.face_mat, parent=torso)
        for side in ("L", "R"):
            thigh=add("THIGH_"+side,"segment",parent=pelvis); shin=add("SHIN_"+side,"segment",parent=thigh)
            add("FOOT_"+side,parent=shin)
            upper=add("UPPER_ARM_"+side,"segment",parent=torso); fore=add("FOREARM_"+side,"segment",parent=upper)
            add("HAND_"+side,parent=fore)
            for joint,parent in [("HIP_"+side,pelvis),("KNEE_"+side,thigh),("ANKLE_"+side,shin),("SHOULDER_"+side,torso),("ELBOW_"+side,upper),("WRIST_"+side,fore)]:
                add(joint,material=self.joint_mat,parent=parent)
        if character["proxy_type"].upper() in {"BIPED_CREATURE", "GENERIC_CREATURE"}:
            for side in ("L","R"):
                bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=.1, radius2=0, depth=.25)
                ear=_link(bpy.context.object,self.id+"__EAR_"+side,collection,self.body_mat); ear.parent=self.root; ear.matrix_parent_inverse=Matrix.Identity(4); self.parts["EAR_"+side]=ear
            tail=add("TAIL_BASE","segment",parent=pelvis); add("TAIL_TIP","segment",material=self.face_mat,parent=tail)

    def _world(self, local, root_matrix):
        return root_matrix @ V(local)

    def apply(self, state: dict[str, Any], frame: int):
        h=self.h; motion=state.get("motion","HOLD"); progress=float(state.get("progress",1))
        if motion in {"RISE_FROM_KNEEL","RISE_FROM_CROUCH","STAND_FROM_SIT"}:
            data=_rise_pose(h,progress,state.get("from_pose","KNEEL"))
        elif state.get("to_pose"):
            data=_pose_blend(h,state.get("from_pose","STAND"),state["to_pose"],motion_builder.smooth(progress))
        else:
            data=_pose(h,state.get("pose","STAND"))
        if motion in motion_builder.MOVE_PRIMITIVES:
            cycles=max(1.0, float(state.get("cycles",2.0))); phase=progress*math.tau*cycles
            stride=h*(.19 if state.get("gait")=="RUN" else .12)
            for side,offset in [("L",0),("R",math.pi)]:
                wave=math.sin(phase+offset); data["foot_"+side].y += stride*wave
                data["foot_"+side].z += h*(.085 if state.get("gait")=="RUN" else .045)*max(0.0,wave)
                data["wrist_"+side].y -= stride*.75*wave
            data["pelvis"].z += h*.015*abs(math.sin(phase))
        if motion in {"TURN_LEFT","TURN_RIGHT","TURN_TO_TARGET"} and progress < 1:
            first=math.sin(math.pi*motion_builder.clamp(progress*2)); second=math.sin(math.pi*motion_builder.clamp((progress-.5)*2))
            data["foot_L"].z += h*.055*max(0,first); data["foot_R"].z += h*.055*max(0,second)
            data["pelvis"].x += h*.025*(first-second)
        if state.get("reach",0):
            data["wrist_R"] = V((h*.12,h*(.28+.24*state["reach"]),h*(.63+.08*state["reach"])))
        root_rot=Matrix.Rotation(math.radians(state["yaw"]),4,"Z")
        root_matrix=Matrix.Translation(V(state["position"])) @ root_rot
        _place_world(self.root,root_matrix,frame)
        torso_pitch=float(data.get("lean",0))+float(state.get("lean",0))
        torso_rot=root_rot.to_3x3() @ Matrix.Rotation(math.radians(-torso_pitch),3,"X")
        head_rot=root_rot.to_3x3() @ Matrix.Rotation(math.radians(state.get("head_yaw",0)),3,"Z") @ Matrix.Rotation(math.radians(-(data.get("head_pitch",0)+state.get("head_pitch",0))),3,"X")
        def wp(key): return self._world(data[key],root_matrix)
        pelvis=wp("pelvis"); neck=wp("neck"); head=wp("head")
        hscale=h/1.7
        placements={
            "PELVIS":_matrix(pelvis,root_rot.to_quaternion(),(.205*hscale,.14*hscale,.12*hscale)),
            "TORSO":_matrix((pelvis+neck)*.5,torso_rot.to_quaternion(),(.23*hscale,.145*hscale,max(.15,(neck-pelvis).length*.52))),
            "HEAD":_matrix(head,head_rot.to_quaternion(),((.19 if self.character["proxy_type"].upper() in {"BIPED_CREATURE","GENERIC_CREATURE"} else .145)*hscale,.135*hscale,.175*hscale)),
            "NOSE":_matrix(head+head_rot@V((0,.145*hscale,-.01)),head_rot.to_quaternion(),(.06*hscale,.075*hscale,.045*hscale)),
            "CHEST_DIRECTION":_matrix((pelvis+neck)*.5+torso_rot@V((0,.145*hscale,.025*hscale)),torso_rot.to_quaternion(),(.09*hscale,.018*hscale,.22*hscale)),
        }
        for side,sign in [("L",-1),("R",1)]:
            placements["EYE_"+side]=_matrix(head+head_rot@V((sign*.075*hscale,.118*hscale,.052*hscale)),head_rot.to_quaternion(),(.025*hscale,)*3)
            hip=pelvis+root_rot.to_3x3()@V((sign*h*.075,0,0)); ankle=wp("foot_"+side)
            knee=_ik(hip,ankle,h*.235,h*.235,root_rot.to_3x3()@V((0,1,.08)))
            shoulder=neck+torso_rot@V((sign*h*.14,0,-h*.035)); wrist=wp("wrist_"+side)
            elbow=_ik(shoulder,wrist,h*.175,h*.165,torso_rot@V((sign*.5,.65,-.12)))
            for key,point,radius in [("HIP_"+side,hip,.05),("KNEE_"+side,knee,.046),("ANKLE_"+side,ankle,.038),("SHOULDER_"+side,shoulder,.05),("ELBOW_"+side,elbow,.04),("WRIST_"+side,wrist,.032)]:
                placements[key]=_matrix(point,scale=(radius*hscale,)*3)
            for key,a,b,radius in [("THIGH_"+side,hip,knee,.052),("SHIN_"+side,knee,ankle,.043),("UPPER_ARM_"+side,shoulder,elbow,.042),("FOREARM_"+side,elbow,wrist,.035)]:
                placements[key]=_segment_matrix(a,b,radius*hscale)
            foot_rot=root_rot.to_3x3(); placements["FOOT_"+side]=_matrix(ankle+foot_rot@V((0,.065*hscale,-.025*hscale)),foot_rot.to_quaternion(),(.06*hscale,.14*hscale,.045*hscale))
            placements["HAND_"+side]=_matrix(wrist,scale=(.045*hscale,.035*hscale,.055*hscale))
        if "EAR_L" in self.parts:
            for side,sign in [("L",-1),("R",1)]:
                placements["EAR_"+side]=_matrix(head+head_rot@V((sign*.105*hscale,0,.20*hscale)),head_rot.to_quaternion(),(hscale,hscale,hscale))
            tail_a=pelvis+root_rot.to_3x3()@V((0,-.10*hscale,0)); tail_b=pelvis+root_rot.to_3x3()@V((.14*hscale,-.48*hscale,-.18*hscale)); tail_c=pelvis+root_rot.to_3x3()@V((.22*hscale,-.72*hscale,-.22*hscale))
            placements["TAIL_BASE"]=_segment_matrix(tail_a,tail_b,.085*hscale); placements["TAIL_TIP"]=_segment_matrix(tail_b,tail_c,.065*hscale)
        for key in ["PELVIS","TORSO","HEAD","NOSE","EYE_L","EYE_R","CHEST_DIRECTION","HIP_L","THIGH_L","KNEE_L","SHIN_L","ANKLE_L","FOOT_L","HIP_R","THIGH_R","KNEE_R","SHIN_R","ANKLE_R","FOOT_R","SHOULDER_L","UPPER_ARM_L","ELBOW_L","FOREARM_L","WRIST_L","HAND_L","SHOULDER_R","UPPER_ARM_R","ELBOW_R","FOREARM_R","WRIST_R","HAND_R","EAR_L","EAR_R","TAIL_BASE","TAIL_TIP"]:
            if key in self.parts and key in placements:
                _place_world(self.parts[key],placements[key],frame)


class BoxRig:
    """Approved box presets; source-matched motion is authored via sampled states.

    Local +Y faces forward (generic runtime convention), +Z is up. All control
    empties have unit scale; only leaf meshes are scaled. No implicit gait loop.
    position is a bottom-root path. For COM flight supply root_is_com=True and
    grounded=False; the evaluated mesh centroid then follows position exactly.
    """
    def __init__(self, character, collection):
        self.character = character
        self.id = character['id']; self.h = float(character['height'])
        self.style = character['proxy_style']
        self.combat = self.style == 'COMBAT_BOX_4'
        self.root = _empty('CHAR_' + self.id, collection)
        self.root['character_id'] = self.id
        self.root['height'] = self.h
        self.root['proxy_style'] = self.style
        self.root['forward_axis'] = '+Y'
        self.parts = {}; self.controls = {}
        self.mat = _material('MAT_' + self.id, list(character['color']))
        self.face = _material('MAT_BOX_DIRECTION', [.94, .86, .62])
        for key in ['LOWER_CTRL', 'BODY_CTRL', 'HEAD_CTRL']:
            o = _empty(self.id + '__' + key, collection)
            o.parent = self.root if key == 'LOWER_CTRL' else self.controls['LOWER_CTRL' if key == 'BODY_CTRL' else 'BODY_CTRL']
            self.controls[key] = o
        def add(key, parent, shape='cube', material=None):
            if shape == 'sphere':
                bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1)
            elif shape == 'cone':
                bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=1, radius2=0, depth=2)
            else:
                bpy.ops.mesh.primitive_cube_add(size=2)
            o = _link(bpy.context.object, self.id + '__' + key, collection, material or self.mat)
            o.parent = self.controls[parent]; o['proxy_part'] = key
            o['character_id'] = self.id; self.parts[key] = o
            if shape == 'sphere':
                for face in o.data.polygons: face.use_smooth = True
            return o
        if self.combat: add('LOWER', 'LOWER_CTRL')
        add('UPPER' if self.combat else 'BODY', 'BODY_CTRL')
        add('HEAD', 'HEAD_CTRL', 'sphere')
        add('NOSE', 'HEAD_CTRL', 'cone', self.face)
        if not self.combat:
            add('EYE_BAR', 'HEAD_CTRL', material=self.face)
            add('CHEST_DIRECTION', 'BODY_CTRL', material=self.face)

    def apply(self, state, frame):
        h = self.h
        def pose_value(pose):
            return {'CROUCH': (.72, 24), 'KNEEL': (.58, 12), 'SIT': (.60, 4),
                    'BOW': (1, 55), 'LIE': (1, 90), 'CORPSE': (1, 90)}.get(pose, (1, 0))
        compress, pitch = pose_value(state.get('pose', 'STAND'))
        if state.get('to_pose'):
            a = pose_value(state.get('from_pose', 'STAND')); b = pose_value(state['to_pose'])
            u = motion_builder.smooth(state.get('progress', 1))
            compress, pitch = [motion_builder.lerp(x, y, u) for x, y in zip(a, b)]
        compress = float(state.get('compression', compress))
        if compress <= 0: raise ValueError('Box compression must be positive')
        # Basic pose lean is an alternative to pose pitch, not an additive bow.
        pitch = float(state.get('body_pitch', pitch if pitch else state.get('lean', 0)))
        width = h * float(self.character.get('width_ratio', .25 if self.combat else .23))
        depth = h * float(self.character.get('depth_ratio', .18))
        r = h * float(self.character.get('head_radius_ratio', .085))
        body_h = h - 2*r - h*.015
        lower_h = body_h * float(self.character.get('lower_fraction', .46)) * compress if self.combat else 0
        upper_h = body_h * compress - lower_h
        self.root.location = state['position']; self.root.rotation_mode = 'XYZ'
        self.root.rotation_euler = tuple(math.radians(x) for x in
            (state.get('root_pitch', 0), state.get('root_roll', 0), state.get('yaw', 0)))
        lo, bo, he = [self.controls[k] for k in ['LOWER_CTRL', 'BODY_CTRL', 'HEAD_CTRL']]
        lo.location = (0, 0, 0)
        lo.rotation_euler = (math.radians(-state.get('lower_pitch', 0)), math.radians(state.get('lower_roll', 0)), 0)
        bo.location = (0, 0, lower_h)
        bo.rotation_euler = (math.radians(-pitch), math.radians(state.get('body_roll', 0)), math.radians(state.get('body_yaw', 0)))
        he.location = (0, 0, upper_h + h*.015 + r)
        he.rotation_euler = (math.radians(-state.get('head_pitch', 0)), 0, math.radians(state.get('head_yaw', 0)))
        def place(key, pos, scale, rotation=(0,0,0)):
            o = self.parts[key]; o.location = pos; o.scale = scale; o.rotation_euler = rotation
        if self.combat:
            place('LOWER', (0,0,lower_h/2), (width*.46,depth*.47,lower_h/2))
        place('UPPER' if self.combat else 'BODY', (0,0,upper_h/2), (width/2,depth/2,upper_h/2))
        place('HEAD', (0,0,0), (r,r,r))
        place('NOSE', (0,r*1.08,-r*.15), (r*.25,r*.25,r*.42), (-math.pi/2,0,0))
        if not self.combat:
            place('EYE_BAR', (0,r*.89,r*.3), (r*.78,r*.13,r*.14))
            place('CHEST_DIRECTION', (0,depth*.53,upper_h*.72), (width*.29,depth*.05,h*.021))
        bpy.context.view_layer.update()
        if state.get('root_is_com', False):
            if state.get('grounded', True): raise ValueError('COM flight requires grounded=False')
            # Volume-weighted mesh-box centroid is the declared mass proxy.
            total = 0.; center = V((0,0,0))
            for o in self.parts.values():
                volume = o.dimensions.x*o.dimensions.y*o.dimensions.z
                center += o.matrix_world.translation*volume; total += volume
            self.root.location += V(state['position']) - center/total
        elif state.get('grounded', True):
            zmin = min((o.matrix_world @ V(c)).z for o in self.parts.values() for c in o.bound_box)
            self.root.location.z += float(state['position'][2]) - zmin
        bpy.context.view_layer.update()
        for o in [self.root, *self.controls.values(), *self.parts.values()]:
            for channel in ['location','rotation_euler','scale']:
                o.keyframe_insert(channel, frame=frame)


class QuadrupedRig:
    def __init__(self, character, collection):
        self.character=character; self.id=character["id"]; self.h=float(character["height"])
        material=_material("MAT_"+self.id,list(character["color"])); face=_material("MAT_DIRECTION",[.92,.94,.88])
        self.root=_empty("CHAR_"+self.id,collection); self.root["character_id"]=self.id; self.root["height"]=self.h; self.parts={}
        def add(key,kind="sphere",mat_=material,parent=None):
            o=(_sphere if kind=="sphere" else _segment_mesh)(self.id+"__"+key,collection,mat_); o.parent=self.root; o.matrix_parent_inverse=Matrix.Identity(4); self.parts[key]=o; return o
        body=add("BODY"); head=add("HEAD",parent=body); add("NOSE",mat_=face,parent=head)
        for leg in ["FL","FR","BL","BR"]: add("LEG_"+leg,"segment",parent=body)
        add("TAIL","segment",parent=body)
    def apply(self,state,frame):
        h=self.h; root_rot=Matrix.Rotation(math.radians(state["yaw"]),4,"Z"); root_matrix=Matrix.Translation(V(state["position"]))@root_rot
        _place_world(self.root,root_matrix,frame); rot=root_rot.to_3x3(); gait=state.get("motion") in motion_builder.MOVE_PRIMITIVES; phase=state.get("progress",0)*math.tau*2
        body=V(state["position"])+rot@V((0,0,h*.48)); head=body+rot@V((0,h*.42,h*.08))
        placements={"BODY":_matrix(body,rot.to_quaternion(),(h*.29,h*.45,h*.22)),"HEAD":_matrix(head,rot.to_quaternion(),(h*.22,h*.24,h*.21)),"NOSE":_matrix(head+rot@V((0,h*.23,-h*.03)),rot.to_quaternion(),(h*.1,h*.12,h*.07))}
        for index,leg in enumerate(["FL","FR","BL","BR"]):
            side=-1 if leg.endswith("L") else 1; front=1 if leg.startswith("F") else -1
            top=body+rot@V((side*h*.19,front*h*.24,-h*.12)); wave=math.sin(phase+(index%2)*math.pi) if gait else 0
            foot=V(state["position"])+rot@V((side*h*.20,front*h*(.30+.13*wave),h*(.04+.05*max(0,wave))))
            placements["LEG_"+leg]=_segment_matrix(top,foot,h*.055)
        placements["TAIL"]=_segment_matrix(body+rot@V((0,-h*.35,0)),body+rot@V((h*.12,-h*.75,h*.1)),h*.07)
        for key,value in placements.items(): _place_world(self.parts[key],value,frame)


def clear_character_collection():
    collection=bpy.data.collections.get("PREVIS_CHARACTERS")
    if collection:
        for object_ in list(collection.objects): bpy.data.objects.remove(object_,do_unlink=True)
        bpy.data.collections.remove(collection)


def build_characters(plan: dict[str, Any]):
    clear_character_collection()
    collection=bpy.data.collections.new("PREVIS_CHARACTERS"); bpy.context.scene.collection.children.link(collection)
    characters={item["id"]:item for item in plan["characters"]}
    rigs=[]
    for character in plan["characters"]:
        kind=character["proxy_type"].upper()
        from shot_builder import resolve_proxy_style
        character = dict(character)
        character['proxy_style'] = resolve_proxy_style(character, plan.get('layout_mode', 'NARRATIVE'))
        if character['proxy_style'] in {'NARRATIVE_BOX_5', 'COMBAT_BOX_4'}:
            rig = BoxRig(character, collection)
        else:
            rig=QuadrupedRig(character,collection) if kind=="QUADRUPED" else BipedRig(character,collection)
        rigs.append(rig)
    scene=bpy.context.scene
    for frame in range(1,int(plan["frames"])+1):
        scene.frame_set(frame)
        for rig in rigs:
            state=motion_builder.sample_state(rig.character,plan["actions"],frame,characters)
            rig.apply(state,frame)
    for action in bpy.data.actions:
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for point in curve.keyframe_points: point.interpolation="LINEAR"
    return rigs
