"""Encode clean/debug videos, contact sheet and a short director-facing README."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import motion_builder
from common import write_json


def _run(command: list[str]) -> None:
    result=subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if result.returncode:
        detail=result.stderr.decode("utf-8",errors="replace")
        raise RuntimeError("ffmpeg packaging failed:\n"+detail)


def _ass_time(seconds: float) -> str:
    return f"{int(seconds)//3600}:{int(seconds)//60%60:02}:{int(seconds)%60:02}.{int(seconds%1*100):02}"


def _ass_color(rgb: list[float]) -> str:
    values=[max(0,min(255,round(float(value)*255))) for value in rgb[:3]]
    return f"{values[2]:02X}{values[1]:02X}{values[0]:02X}"


def _probe(ffprobe: Path, video: Path) -> dict[str, Any]:
    raw=subprocess.check_output([str(ffprobe),"-v","error","-select_streams","v:0","-count_frames",
        "-show_entries","stream=width,height,r_frame_rate,nb_read_frames,duration","-of","json",str(video)])
    return json.loads(raw)["streams"][0]


def package_shot(plan: dict[str,Any], shot_dir: Path, ffmpeg: Path, ffprobe: Path) -> dict[str,Any]:
    work=shot_dir/"_work"; frames=work/"frames"; fps=int(plan["fps"]); count=int(plan["frames"])
    clean=shot_dir/"PREVIS.mp4"; debug=shot_dir/"PREVIS_DEBUG.mp4"; contact=shot_dir/"CONTACT_SHEET.png"
    _run([str(ffmpeg),"-hide_banner","-loglevel","error","-y","-framerate",str(fps),"-start_number","1","-i",str(frames/"F%04d.png"),
          "-frames:v",str(count),"-c:v","libx264","-preset","medium","-crf","17","-pix_fmt","yuv420p","-movflags","+faststart",str(clean)])
    width,height=plan["resolution"]; debug_height=int(height)+96
    ass="""[Script Info]
ScriptType: v4.00+
ScaledBorderAndShadow: yes
PlayResX: %s
PlayResY: %s
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Microsoft YaHei,22,&H00F4F5F7,&H00FFFFFF,&H00211811,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""%(width,debug_height)
    def event(a,b,text):
        nonlocal ass; ass+=f"Dialogue: 0,{_ass_time(a)},{_ass_time(b)},Default,,0,0,0,,{text}\n"
    duration=count/fps; event(0,duration,r"{\pos(22,10)\fs22}"+plan["shot_id"]+" · PREVIS V1")
    for frame in range(1,count+1):
        a=(frame-1)/fps; b=frame/fps; beat=motion_builder.active_beat(plan["actions"],frame)
        event(a,b,r"{\pos(380,10)\fs20}"+beat); event(a,b,r"{\pos("+str(width-150)+r",10)\fs19}"+f"F{frame:03} / {count}")
    step=max(150,int(width/max(1,len(plan["characters"]))))
    for index,character in enumerate(plan["characters"]):
        x=20+index*step; color=_ass_color(character["color"])
        event(0,duration,"{\\pos("+str(x)+","+str(debug_height-30)+")\\fs18\\c&H"+color+"&}● "+character["display_name"])
    ass_path=work/"debug.ass"; ass_path.write_text(ass,encoding="utf-8-sig")
    ass_filter=ass_path.as_posix().replace(":",r"\:")
    _run([str(ffmpeg),"-hide_banner","-loglevel","error","-y","-i",str(clean),"-vf",f"pad={width}:{debug_height}:0:48:color=0x111b29,ass=filename='{ass_filter}'",
          "-frames:v",str(count),"-c:v","libx264","-preset","medium","-crf","17","-pix_fmt","yuv420p","-movflags","+faststart",str(debug)])
    samples=sorted(set(round(index*(count-1)/5) for index in range(6)))
    select="+".join(f"eq(n\\,{value})" for value in samples)
    thumb_w=max(320,int(width/3)); thumb_h=max(180,int(height/3))
    _run([str(ffmpeg),"-hide_banner","-loglevel","error","-y","-i",str(clean),"-vf",f"select='{select}',scale={thumb_w}:{thumb_h},tile=3x2:padding=4:margin=4",
          "-frames:v","1",str(contact)])
    clean_info=_probe(ffprobe,clean); debug_info=_probe(ffprobe,debug)
    expected_rate=f"{fps}/1"; expected_duration=count/fps
    if int(clean_info["nb_read_frames"])!=count or clean_info["r_frame_rate"]!=expected_rate or abs(float(clean_info["duration"])-expected_duration)>.01:
        raise RuntimeError(f"Clean video verification failed: {clean_info}")
    readme=shot_dir/"README.md"
    limitations=plan.get("notes") or ["Blocking-grade proxy motion; refine contacts and secondary motion after director review."]
    readme.write_text(
        f"# {plan['shot_id']} · Blender Previs Layout V1\n\n"
        f"{count/fps:.2f} seconds, {fps} fps, {width}×{height}. Clean video, debug video, editable Blender scene and contact sheet are the review package.\n\n"
        "## Action beats\n\n"+"\n".join(f"- F{a['start']:03}–F{a['end']:03}: {a.get('label') or a['character']+' '+a['primitive']}" for a in plan["actions"])+
        "\n\n## Known limitations\n\n"+"\n".join(f"- {item}" for item in limitations)+"\n",
        encoding="utf-8")
    report={"status":"PASS","shot_id":plan["shot_id"],"clean":clean_info,"debug":debug_info,"files":{"clean":str(clean),"debug":str(debug),"blend":str(shot_dir/(plan["shot_id"]+"-PREVIS-V1.blend")),"contact_sheet":str(contact)}}
    write_json(work/"technical-check.json",report); return report
