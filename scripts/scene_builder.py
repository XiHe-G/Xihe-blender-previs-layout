"""Build only the environment forms that establish performance and camera space."""

from __future__ import annotations

import math
from typing import Any

import bpy
from mathutils import Vector


def _material(name: str, color: list[float]):
    material=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.diffuse_color=(*color[:3],1); material.use_nodes=True
    node=material.node_tree.nodes.get("Principled BSDF")
    node.inputs["Base Color"].default_value=(*color[:3],1); node.inputs["Roughness"].default_value=.88
    return material


def _link(object_,name,collection,material):
    object_.name=name
    for old in list(object_.users_collection): old.objects.unlink(object_)
    collection.objects.link(object_)
    object_.data.materials.clear(); object_.data.materials.append(material)
    object_["previs_environment"]=True
    return object_


def _cube(name,location,dimensions,rotation,collection,material):
    bpy.ops.mesh.primitive_cube_add(size=1,location=location,rotation=tuple(math.radians(float(v)) for v in rotation))
    object_=_link(bpy.context.object,name,collection,material); object_.scale=dimensions
    return object_


def _cylinder(name,location,dimensions,rotation,collection,material,vertices=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=1,depth=1,location=location,rotation=tuple(math.radians(float(v)) for v in rotation))
    object_=_link(bpy.context.object,name,collection,material); object_.scale=(dimensions[0]/2,dimensions[1]/2,dimensions[2])
    return object_


def _build_gate(element,collection,material):
    x,y,z=[float(v) for v in element["location"]]; w,d,h=[float(v) for v in element["dimensions"]]
    opening=float(element.get("opening_width",w*.48)); pillar=(w-opening)/2
    _cube(element["id"]+"_LEFT",(x-(opening+pillar)/2,y,z+h/2),(pillar,d,h),(0,0,0),collection,material)
    _cube(element["id"]+"_RIGHT",(x+(opening+pillar)/2,y,z+h/2),(pillar,d,h),(0,0,0),collection,material)
    _cube(element["id"]+"_LINTEL",(x,y,z+h-.16),(w,d*1.2,.32),(0,0,0),collection,material)
    roof=_material("MAT_GATE_ROOF",element.get("accent_color",[.12,.15,.17]))
    _cube(element["id"]+"_ROOF",(x,y,z+h+.08),(w*1.1,d*1.55,.22),(0,0,0),collection,roof)


def _build_grid(element,collection,material):
    x,y,z=[float(v) for v in element.get("location",[0,0,.003])]; w,d=[float(v) for v in element.get("dimensions",[20,20])[:2]]
    spacing=float(element.get("spacing",2)); thickness=float(element.get("thickness",.018))
    ix=math.floor(w/spacing/2); iy=math.floor(d/spacing/2)
    for i in range(-ix,ix+1): _cube(f"{element['id']}_X_{i}",(x+i*spacing,y,z),(thickness,d,.008),(0,0,0),collection,material)
    for i in range(-iy,iy+1): _cube(f"{element['id']}_Y_{i}",(x,y+i*spacing,z),(w,thickness,.008),(0,0,0),collection,material)


def _build_stairs(element,collection,material):
    x,y,z=[float(v) for v in element["location"]]; w,d,h=[float(v) for v in element["dimensions"]]; count=int(element.get("steps",8))
    for index in range(count):
        depth=d/count; height=h*(index+1)/count
        _cube(f"{element['id']}_{index+1:02}",(x,y-d/2+depth*(index+.5),z+height/2),(w,depth,height),(0,0,0),collection,material)


def _build_bridge(element,collection,material):
    x,y,z=[float(v) for v in element["location"]]; w,d,h=[float(v) for v in element["dimensions"]]
    _cube(element["id"]+"_DECK",(x,y,z),(w,d,h),(0,0,float(element.get("yaw",0))),collection,material)
    rail=_material("MAT_BRIDGE_RAIL",element.get("accent_color",[.68,.7,.7])); count=int(element.get("posts",8))
    for side in (-1,1):
        _cube(f"{element['id']}_RAIL_{side}",(x+side*w*.47,y,z+h*.72),(.07,d,h*.08),(0,0,0),collection,rail)
        for index in range(count+1):
            yy=y-d/2+d*index/count
            _cube(f"{element['id']}_POST_{side}_{index}",(x+side*w*.47,yy,z+h*.38),(.075,.075,h*.76),(0,0,0),collection,rail)


def clear_environment():
    collection=bpy.data.collections.get("PREVIS_ENVIRONMENT")
    if collection:
        for object_ in list(collection.objects): bpy.data.objects.remove(object_,do_unlink=True)
        bpy.data.collections.remove(collection)


def build_environment(plan: dict[str,Any]):
    clear_environment(); collection=bpy.data.collections.new("PREVIS_ENVIRONMENT"); bpy.context.scene.collection.children.link(collection)
    for element in plan["scene"].get("elements",[]):
        kind=str(element.get("type","CUBE")).upper(); material=_material("MAT_ENV_"+element["id"],element.get("color",[.38,.40,.41]))
        if kind=="GATE": _build_gate(element,collection,material)
        elif kind=="GRID": _build_grid(element,collection,material)
        elif kind=="STAIRS": _build_stairs(element,collection,material)
        elif kind=="BRIDGE": _build_bridge(element,collection,material)
        elif kind=="CYLINDER": _cylinder(element["id"],element.get("location",[0,0,0]),element.get("dimensions",[1,1,1]),element.get("rotation",[0,0,0]),collection,material)
        else: _cube(element["id"],element.get("location",[0,0,0]),element.get("dimensions",[1,1,1]),element.get("rotation",[0,0,0]),collection,material)
    return collection


def configure_scene(plan: dict[str,Any]):
    scene=bpy.context.scene; width,height=plan["resolution"]
    scene.render.engine="BLENDER_EEVEE"; scene.render.resolution_x=int(width); scene.render.resolution_y=int(height); scene.render.resolution_percentage=100
    scene.render.fps=int(plan["fps"]); scene.render.fps_base=1; scene.frame_start=1; scene.frame_end=int(plan["frames"])
    scene.render.image_settings.file_format="PNG"; scene.render.image_settings.color_mode="RGB"; scene.render.image_settings.color_depth="8"
    # Blender 5.2 exposes the AgX view transform names with an `AgX -` prefix.
    # Keep a small fallback so the runtime also works on older Blender builds.
    try:
        scene.view_settings.look="AgX - Medium High Contrast"
    except TypeError:
        scene.view_settings.look="Medium High Contrast"
    scene.world=bpy.data.worlds.get("PREVIS_WORLD") or bpy.data.worlds.new("PREVIS_WORLD"); scene.world.use_nodes=True
    scene.world.node_tree.nodes["Background"].inputs[0].default_value=(*plan["scene"].get("world_color",[.23,.29,.36]),1)
    scene.world.node_tree.nodes["Background"].inputs[1].default_value=float(plan["scene"].get("world_strength",.45))
    for old in list(bpy.data.collections):
        if old.name=="PREVIS_LIGHTS":
            for object_ in list(old.objects): bpy.data.objects.remove(object_,do_unlink=True)
            bpy.data.collections.remove(old)
    lights=bpy.data.collections.new("PREVIS_LIGHTS"); scene.collection.children.link(lights)
    sun_data=bpy.data.lights.new("PREVIS_SUN","SUN"); sun_data.energy=2.1; sun_data.angle=.22
    sun=bpy.data.objects.new("PREVIS_SUN",sun_data); lights.objects.link(sun); sun.rotation_euler=(math.radians(27),math.radians(-18),math.radians(-32))
    area_data=bpy.data.lights.new("PREVIS_FILL","AREA"); area_data.energy=1300; area_data.shape="DISK"; area_data.size=9
    area=bpy.data.objects.new("PREVIS_FILL",area_data); lights.objects.link(area); area.location=(6,5,10); area.rotation_euler=(Vector((0,-4,.7))-area.location).to_track_quat("-Z","Y").to_euler()
    scene["previs_version"]="1.0"; scene["project_id"]=plan["project_id"]; scene["shot_id"]=plan["shot_id"]
