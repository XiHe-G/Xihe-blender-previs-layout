"""Production entry point for full, per-shot and incremental Blender previs builds."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR=Path(__file__).resolve().parent; SKILL_DIR=SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path: sys.path.insert(0,str(SCRIPT_DIR))
if str(SKILL_DIR/"adapters") not in sys.path: sys.path.insert(0,str(SKILL_DIR/"adapters"))

import blender_headless_adapter as adapter
import director_override, package_review, sequence_builder, shot_builder
from common import BUILD_MODES, VERSION, load_json, stable_hash, write_json


def arguments():
    parser=argparse.ArgumentParser(description="Build director-readable Blender Layout/Previs")
    parser.add_argument("manifest",type=Path); parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--mode",choices=sorted(BUILD_MODES),default="FULL_BUILD"); parser.add_argument("--shot",action="append")
    parser.add_argument("--overrides",type=Path); parser.add_argument("--blender",type=Path); parser.add_argument("--ffmpeg",type=Path)
    parser.add_argument("--build-only",action="store_true"); parser.add_argument("--force",action="store_true")
    return parser.parse_args()


def _effective_override_mode(affected: set[str]) -> str:
    if "environment" in affected: return "SHOT_BUILD"
    if affected=={"camera"}: return "CAMERA_ONLY"
    if "characters" in affected: return "MOTION_ONLY"
    return "RENDER_ONLY"


def main():
    args=arguments(); project=load_json(args.manifest.resolve()); overrides=load_json(args.overrides.resolve()) if args.overrides else None
    project,affected=director_override.apply_overrides(project,overrides); shot_builder.validate_project(project)
    requested=args.shot or [str(item["id"]) for item in project["shots"]]
    if args.mode=="SHOT_BUILD" and not args.shot: raise ValueError("SHOT_BUILD requires --shot")
    output_root=args.output.resolve()/project["project_id"]; output_root.mkdir(parents=True,exist_ok=True)
    blender=adapter.find_blender(args.blender); ffmpeg=adapter.find_ffmpeg(args.ffmpeg); ffprobe=adapter.find_ffprobe(ffmpeg)
    shot_dirs=[]; summary={"version":VERSION,"project_id":project["project_id"],"requested_mode":args.mode,"shots":[]}
    for shot_id in requested:
        plan=shot_builder.normalize_shot(project,shot_id); shot_dir=output_root/shot_id; work=shot_dir/"_work"; work.mkdir(parents=True,exist_ok=True)
        plan_path=work/"shot-plan.json"; write_json(plan_path,plan); fingerprint=stable_hash({"version":VERSION,"plan":plan})
        cache_path=work/"build-cache.json"; old=load_json(cache_path) if cache_path.exists() else {}; blend=shot_dir/(shot_id+"-PREVIS-V1.blend")
        clean=shot_dir/"PREVIS.mp4"; mode=args.mode
        if mode=="OVERRIDE_PATCH": mode=_effective_override_mode(affected.get(shot_id,affected.get("*",set())))
        render=not args.build_only
        can_skip=not args.force and args.mode in {"FULL_BUILD","SHOT_BUILD","OVERRIDE_PATCH"} and old.get("fingerprint")==fingerprint and blend.exists() and (not render or clean.exists())
        if can_skip:
            status="CACHE_HIT"
        else:
            if mode not in {"FULL_BUILD","SHOT_BUILD"} and not blend.exists(): mode="SHOT_BUILD"
            result=adapter.run_blender(blender,SKILL_DIR/"scripts"/"render_previs.py",plan_path,shot_dir,mode,render,blend if blend.exists() and mode not in {"FULL_BUILD","SHOT_BUILD"} else None)
            (work/"blender.log").write_text(result.stdout,encoding="utf-8"); status="BUILT"
            if render: package_review.package_shot(plan,shot_dir,ffmpeg,ffprobe)
            write_json(cache_path,{"fingerprint":fingerprint,"mode":mode,"version":VERSION})
        shot_dirs.append(shot_dir); summary["shots"].append({"shot_id":shot_id,"status":status,"mode":mode,"directory":str(shot_dir)})
    if not args.build_only: summary["sequence"]=sequence_builder.assemble(project["project_id"],shot_dirs,output_root,ffmpeg)
    write_json(output_root/"BUILD-SUMMARY.json",summary)
    print(f"Blender Previs Layout {VERSION}: {output_root}")
    for row in summary["shots"]: print(f"  {row['shot_id']}: {row['status']} ({row['mode']})")


if __name__=="__main__": main()
