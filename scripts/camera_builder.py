"""Build a continuous camera path from shot intent and subject targets."""

from __future__ import annotations

import math
from typing import Any

import bpy
from mathutils import Vector

import motion_builder


V=Vector


def clear_camera():
    collection=bpy.data.collections.get("PREVIS_CAMERA")
    if collection:
        for object_ in list(collection.objects): bpy.data.objects.remove(object_,do_unlink=True)
        bpy.data.collections.remove(collection)


def _character_point(character_id: str, frame: int, height_ratio=.62):
    object_=bpy.data.objects.get("CHAR_"+character_id)
    if object_ is None: raise ValueError(f"Camera target character missing: {character_id}")
    height=float(object_.get("height",1.7))
    return object_.matrix_world.translation+V((0,0,height*height_ratio))


def _resolve_target(value,frame,default=None):
    if isinstance(value,str): return _character_point(value,frame)
    if isinstance(value,list): return V(value)
    return V(default or (0,0,.8))


def _lerp_vec(a,b,t): return V(a).lerp(V(b),t)


def build_camera(plan: dict[str,Any]):
    clear_camera(); collection=bpy.data.collections.new("PREVIS_CAMERA"); bpy.context.scene.collection.children.link(collection)
    config=plan.get("camera",{}); data=bpy.data.cameras.new("CAM_"+plan["shot_id"]+"_DATA")
    data.lens=float(config.get("lens",35)); data.sensor_width=float(config.get("sensor_width",36)); data.dof.use_dof=False; data.clip_end=500
    camera=bpy.data.objects.new("CAM_"+plan["shot_id"],data); collection.objects.link(camera); bpy.context.scene.camera=camera
    movement=str(config.get("movement","STATIC")).upper(); start=config.get("start",{}); end=config.get("end",start)
    start_loc=V(start.get("location",[6,7,3])); end_loc=V(end.get("location",start_loc))
    frames=int(plan["frames"]); subject=config.get("subject"); start_subject=None
    scene=bpy.context.scene
    for frame in range(1,frames+1):
        scene.frame_set(frame); t=motion_builder.smooth((frame-1)/max(1,frames-1))
        location=_lerp_vec(start_loc,end_loc,t)
        if movement=="FOLLOW" and subject:
            current=bpy.data.objects["CHAR_"+subject].matrix_world.translation.copy()
            if start_subject is None: start_subject=current.copy()
            location+=current-start_subject
        elif movement=="ARC":
            target=_resolve_target(config.get("target",subject),frame,start.get("target",[0,0,.8])); offset=start_loc-target
            angle=math.radians(float(config.get("arc_degrees",45))*t); ca,sa=math.cos(angle),math.sin(angle)
            location=target+V((offset.x*ca-offset.y*sa,offset.x*sa+offset.y*ca,offset.z+float(config.get("height_delta",0))*t))
        elif movement in {"STATIC","PAN","TILT"}: location=start_loc.copy()
        if movement=="HANDHELD_APPROX":
            amount=float(config.get("handheld_amount",.025)); location+=V((math.sin(frame*.73),math.sin(frame*.51+1.1),math.sin(frame*.37+.4)))*amount
        target_start=start.get("target",config.get("target",subject)); target_end=end.get("target",target_start)
        target=_resolve_target(target_start,frame,[0,0,.8]).lerp(_resolve_target(target_end,frame,[0,0,.8]),t)
        if movement=="FOLLOW" and subject and not start.get("target"):
            target=_character_point(subject,frame,float(config.get("target_height",.62)))
        camera.location=location; camera.rotation_mode="QUATERNION"; camera.rotation_quaternion=(target-location).to_track_quat("-Z","Y")
        camera.keyframe_insert("location",frame=frame); camera.keyframe_insert("rotation_quaternion",frame=frame)
    for action in bpy.data.actions:
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for point in curve.keyframe_points: point.interpolation="LINEAR"
    camera["movement_intent"]=movement; camera["subject"]=str(subject or "GROUP"); return camera

