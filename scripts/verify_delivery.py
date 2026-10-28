"""Probe/decode each movie and independently compare artifact revision hashes."""
from __future__ import annotations
import argparse
import json
import math
import subprocess
from fractions import Fraction
from pathlib import Path
from production_io import read_json, write_json, resolve_path, sha256, compare_files


def media_errors(probe, expected):
    errors = []
    videos = [s for s in probe.get("streams", []) if s.get("codec_type") == "video"]
    audios = [s for s in probe.get("streams", []) if s.get("codec_type") == "audio"]
    if len(videos) != 1:
        return ["Expected exactly one video stream"]
    video = videos[0]
    if [video.get("width"), video.get("height")] != expected["resolution"]:
        errors.append("resolution mismatch")
    for name in ("avg_frame_rate", "r_frame_rate"):
        try:
            actual = float(Fraction(video.get(name, "0")))
            if not math.isclose(actual, expected["fps"], abs_tol=1e-5, rel_tol=0):
                errors.append(name + " mismatch")
        except (ValueError, ZeroDivisionError):
            errors.append(name + " unavailable")
    try:
        if int(video["nb_read_frames"]) != expected["total_frames"]:
            errors.append("decoded frame count mismatch")
    except (KeyError, ValueError, TypeError):
        errors.append("decoded frame count unavailable")
    try:
        duration = float(video.get("duration", probe.get("format", {}).get("duration")))
        if not math.isfinite(duration) or abs(duration - expected["total_frames"] / expected["fps"]) > 1 / expected["fps"] + 1e-6:
            errors.append("duration mismatch")
    except (TypeError, ValueError):
        errors.append("duration unavailable")
    requirement = expected.get("audio", "unspecified")
    if requirement not in {"present", "absent", "unspecified"}:
        errors.append("invalid expected audio policy")
    elif requirement == "present" and not audios:
        errors.append("expected audio track absent")
    elif requirement == "absent" and audios:
        errors.append("unexpected audio track")
    return errors


def verify(spec_path, ffmpeg, ffprobe, previous_path=None):
    spec_path = Path(spec_path).resolve()
    spec = read_json(spec_path)
    base = spec_path.parent
    if not spec.get("videos") or float(spec["fps"]) <= 0 or int(spec["total_frames"]) <= 0:
        raise ValueError("Specify videos, positive fps and positive total_frames")
    files, checks, failures = [], [], []
    seen = set()
    for item in [*spec["videos"], *spec.get("artifacts", [])]:
        path = resolve_path(base, item["path"])
        if path in seen:
            continue
        seen.add(path)
        if not path.is_file():
            failures.append(f"Missing file: {path}")
            files.append({"path": str(path), "sha256": None, "bytes": None})
        else:
            files.append({"path": str(path), "sha256": sha256(path), "bytes": path.stat().st_size})
    for item in spec["videos"]:
        path = resolve_path(base, item["path"])
        errors, probe = [], {}
        if path.is_file():
            try:
                result = subprocess.run([ffprobe, "-v", "error", "-count_frames", "-show_streams",
                                         "-show_format", "-of", "json", str(path)],
                                        capture_output=True, text=True, encoding="utf-8", errors="replace")
                if result.returncode or result.stderr.strip():
                    errors.append("ffprobe reported error: " + result.stderr.strip()[:1200])
                else:
                    probe = json.loads(result.stdout)
                    errors.extend(media_errors(probe, {**spec, **item}))
                decoded = subprocess.run([ffmpeg, "-hide_banner", "-v", "error", "-xerror",
                                          "-i", str(path), "-map", "0:v:0", "-f", "null", "-"],
                                         capture_output=True, text=True, encoding="utf-8", errors="replace")
                if decoded.returncode or decoded.stderr.strip():
                    errors.append("full decode error: " + decoded.stderr.strip()[:1200])
            except (OSError, ValueError) as exc:
                errors.append(str(exc))
        else:
            errors.append("video missing")
        checks.append({"path": str(path), "status": "failed" if errors else "passed",
                       "errors": errors, "probe": probe})
        failures.extend(f"{path.name}: {e}" for e in errors)
    comparisons = compare_files(files, read_json(previous_path)) if previous_path else []
    freshness = ("mismatch" if any(c["status"] == "mismatch" for c in comparisons) else
                 "incomplete" if any(c["status"] == "not_in_previous" for c in comparisons) else
                 "match" if comparisons else "not_compared")
    return {"technical_status": "failed" if failures else "passed",
            "freshness_status": freshness, "errors": failures, "files": files,
            "comparisons": comparisons, "video_checks": checks,
            "provenance": {"status": "not_independently_verified",
                           "declared_evidence": spec.get("provenance", "not supplied")},
            "visual_review": spec.get("visual_review", "not recorded"),
            "user_acceptance": spec.get("user_acceptance", "not recorded")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--compare", type=Path)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    args = parser.parse_args()
    result = verify(args.spec, args.ffmpeg, args.ffprobe, args.compare)
    write_json(args.output, result)
    print(f"technical={result['technical_status']}; freshness={result['freshness_status']}")
    raise SystemExit(0 if result["technical_status"] == "passed" and result["freshness_status"] not in {"mismatch", "incomplete"} else 2)


if __name__ == "__main__":
    main()
