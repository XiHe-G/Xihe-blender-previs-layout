"""Assemble one or more per-shot videos into a review sequence."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def _concat_file(paths: list[Path], target: Path):
    lines=[]
    for path in paths:
        safe=path.resolve().as_posix().replace("'","'\\''")
        lines.append(f"file '{safe}'")
    target.write_text("\n".join(lines)+"\n",encoding="utf-8")


def assemble(project_id: str, shot_dirs: list[Path], output_root: Path, ffmpeg: Path):
    if not shot_dirs: return {}
    work=output_root/"_work"; work.mkdir(parents=True,exist_ok=True)
    outputs={}
    for source_name,target_name in [("PREVIS.mp4","PREVIS-SEQUENCE.mp4"),("PREVIS_DEBUG.mp4","PREVIS-SEQUENCE-DEBUG.mp4")]:
        sources=[path/source_name for path in shot_dirs]; target=output_root/target_name
        if len(sources)==1: shutil.copyfile(sources[0],target)
        else:
            listing=work/(source_name+".txt"); _concat_file(sources,listing)
            subprocess.run([str(ffmpeg),"-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(listing),"-c","copy",str(target)],check=True)
        outputs[target_name]=str(target)
    return outputs

