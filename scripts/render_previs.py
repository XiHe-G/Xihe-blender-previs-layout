"""Blender-side build/patch/render entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy

SCRIPT_DIR=Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path: sys.path.insert(0,str(SCRIPT_DIR))

import camera_builder, character_proxy, scene_builder


def arguments():
    argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    parser=argparse.ArgumentParser(); parser.add_argument("--plan",type=Path,required=True); parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--mode",required=True); parser.add_argument("--render",action="store_true")
    return parser.parse_args(argv)


def main():
    args=arguments(); plan=json.loads(args.plan.read_text(encoding="utf-8-sig")); output=args.output.resolve(); output.mkdir(parents=True,exist_ok=True)
    full=args.mode in {"FULL_BUILD","SHOT_BUILD"} or len(bpy.data.objects)==0
    if full: bpy.ops.wm.read_factory_settings(use_empty=True)
    scene_builder.configure_scene(plan)
    if full: scene_builder.build_environment(plan)
    if full or args.mode in {"BLOCKING_ONLY","MOTION_ONLY","OVERRIDE_PATCH"}: character_proxy.build_characters(plan)
    if full or args.mode in {"CAMERA_ONLY","BLOCKING_ONLY","MOTION_ONLY","OVERRIDE_PATCH"}: camera_builder.build_camera(plan)
    scene=bpy.context.scene; scene.timeline_markers.clear()
    for action in plan["actions"]: scene.timeline_markers.new(f"{action['character']} / {action['primitive']}",frame=int(action["start"]))
    scene.frame_set(1)
    blend=output/(plan["shot_id"]+"-PREVIS-V1.blend"); bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    if args.render:
        frames=output/"_work"/"frames"; frames.mkdir(parents=True,exist_ok=True)
        for old in frames.glob("F*.png"): old.unlink()
        scene.render.filepath=str(frames/"F"); bpy.ops.render.render(animation=True)
    print("PREVIS_RESULT",json.dumps({"blend":str(blend),"rendered":args.render,"frames":plan["frames"]}))


if __name__=="__main__": main()

