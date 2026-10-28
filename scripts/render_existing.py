"""Render an already animated .blend without saving or rebuilding the source."""
from __future__ import annotations
import argparse
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from production_io import read_json, write_json, resolve_path, sha256, png_size, render_fingerprint, reusable_frame


def main():
    import bpy
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job", required=True, type=Path)
    parser.add_argument("--start", type=int, help="Final rendering only; inclusive")
    parser.add_argument("--end", type=int, help="Final rendering only; inclusive")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    job_path = args.job.resolve()
    job = read_json(job_path)
    base = job_path.parent
    blend = resolve_path(base, job["blend"])
    if Path(bpy.data.filepath).resolve() != blend:
        raise ValueError("Opened .blend does not match job.blend")
    timeline_path = resolve_path(base, job["timeline"])
    timeline = read_json(timeline_path)
    scene = bpy.data.scenes.get(job["scene"])
    if scene is None:
        raise ValueError("Named scene does not exist")
    fps = scene.render.fps / scene.render.fps_base
    if not math.isclose(fps, timeline["fps"], rel_tol=0, abs_tol=1e-6):
        raise ValueError("Scene fps differs from compiled timeline")
    shots = timeline["shots"]
    cursor, cameras = 1, {}
    for shot in shots:
        if shot["start_frame"] != cursor or shot["end_frame"] < cursor:
            raise ValueError("Timeline must be contiguous and ordered from frame 1")
        camera = scene.objects.get(shot["camera"])
        if camera is None or camera.type != "CAMERA":
            raise ValueError(f"Missing camera: {shot['camera']}")
        for frame in range(cursor, shot["end_frame"] + 1):
            cameras[frame] = camera
        cursor = shot["end_frame"] + 1
    if cursor - 1 != timeline["total_frames"]:
        raise ValueError("Timeline frame total differs from shot coverage")
    if scene.frame_start > 1 or scene.frame_end < cursor - 1:
        raise ValueError("Scene frame range does not cover timeline")
    mode = job.get("mode", "review")
    if mode not in {"review", "final"}:
        raise ValueError("mode must be review or final")
    if mode == "review":
        if args.start is not None or args.end is not None:
            raise ValueError("Use mode final for a bounded range")
        frames = sorted({f for s in shots for f in
                         (s["start_frame"], (s["start_frame"] + s["end_frame"]) // 2, s["end_frame"])})
        scale = float(job.get("review_scale", 0.5))
        if not 0 < scale <= 1:
            raise ValueError("review_scale must be in (0, 1]")
    else:
        first = args.start if args.start is not None else 1
        last = args.end if args.end is not None else timeline["total_frames"]
        if not 1 <= first <= last <= timeline["total_frames"]:
            raise ValueError("Invalid final frame range")
        frames, scale = list(range(first, last + 1)), 1
    resolution = job["resolution"]
    if len(resolution) != 2 or any(not isinstance(n, int) or isinstance(n, bool) or n < 4 for n in resolution):
        raise ValueError("resolution must contain two positive pixel integers >= 4")
    dimensions = [max(4, int(n * scale)) for n in resolution]
    output = resolve_path(base, job["output_dir"]) / mode
    dependencies = [resolve_path(base, p) for p in job.get("dependencies", [])]
    fingerprint = render_fingerprint(job, [blend, timeline_path, Path(__file__),
                                          Path(__file__).with_name("production_io.py"), *dependencies])
    output.mkdir(parents=True, exist_ok=True)
    scene.render.resolution_x, scene.render.resolution_y = dimensions
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.use_file_extension = True
    scene.render.use_sequencer = False
    # Prevent camera markers from overriding explicit per-edit camera selection.
    for marker in scene.timeline_markers:
        if marker.camera:
            marker.camera = None
    rendered = reused = 0
    for frame in frames:
        path = output / f"frame_{frame:06d}.png"
        if job.get("resume", True) and reusable_frame(path, fingerprint, dimensions):
            reused += 1
            continue
        scene.frame_set(frame)
        scene.camera = cameras[frame]
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True, scene=scene.name)
        actual = png_size(path)
        if actual != dimensions:
            raise ValueError(f"Unexpected PNG dimensions at frame {frame}: {actual}")
        write_json(path.with_suffix(".receipt.json"), {
            "frame": frame, "camera": cameras[frame].name, "fingerprint": fingerprint,
            "dimensions": actual, "sha256": sha256(path)})
        rendered += 1
    if render_fingerprint(job, [blend, timeline_path, Path(__file__),
                               Path(__file__).with_name("production_io.py"), *dependencies]) != fingerprint:
        raise RuntimeError("Source or dependency changed during rendering; rerun against a stable revision")
    report = {"source_blend": str(blend), "source_sha256": sha256(blend),
              "fingerprint": fingerprint, "mode": mode, "frames": frames,
              "rendered": rendered, "reused": reused, "dimensions": dimensions,
              "external_dependencies": [str(p) for p in dependencies],
              "source_saved": False}
    report_path = output / f"render_{frames[0]:06d}_{frames[-1]:06d}.json"
    write_json(report_path, report)
    print(f"Rendered {rendered}, reused {reused}; report: {report_path}")


if __name__ == "__main__":
    main()
