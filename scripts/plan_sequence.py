"""Compile ordered edits and concurrent route budgets; no Blender dependency."""
from __future__ import annotations
import argparse
import json
import math
from fractions import Fraction
from pathlib import Path


def number(value, label, positive=False):
    result = float(value)
    if not math.isfinite(result) or (result <= 0 if positive else result < 0):
        raise ValueError(f"{label} must be finite and {'positive' if positive else 'nonnegative'}")
    return result


def compile_plan(plan):
    fps = Fraction(str(plan["fps"]))
    if fps <= 0:
        raise ValueError("fps must be positive")
    shots, cursor, seen = [], 1, set()
    for item in plan["shots"]:
        edit_id = item["edit_id"]
        if not isinstance(edit_id, str) or not edit_id or edit_id in seen:
            raise ValueError(f"Missing/duplicate edit_id: {edit_id}")
        seen.add(edit_id)
        frames = Fraction(str(item["duration_s"])) * fps
        if frames.denominator != 1 or frames <= 0:
            raise ValueError(f"{edit_id}: duration must be a positive whole number of frames")
        frames = int(frames)
        shots.append({**item, "edit_order": len(shots) + 1, "start_frame": cursor,
                      "end_frame": cursor + frames - 1,
                      "start_s": float(Fraction(cursor - 1) / fps),
                      "end_s": float(Fraction(cursor + frames - 1) / fps)})
        cursor += frames
    if not shots:
        raise ValueError("At least one edit is required")
    routes = {}
    for route_id, route in plan.get("routes", {}).items():
        points = route["points"]
        if len(points) < 2 or any(len(p) != 3 for p in points):
            raise ValueError(f"{route_id}: at least two xyz points required")
        points = [[float(x) for x in p] for p in points]
        if not all(math.isfinite(x) for p in points for x in p):
            raise ValueError(f"{route_id}: invalid coordinates")
        length = sum(math.dist(a, b) for a, b in zip(points, points[1:]))
        speed = number(route["speed_units_s"], route_id + " speed", positive=True)
        routes[route_id] = {"length_units": length, "speed_units_s": speed,
                            "travel_s": length / speed, "points": points}
    groups, group_ids = [], set()
    for group in plan.get("movement_groups", []):
        group_id = group["id"]
        if group_id in group_ids:
            raise ValueError(f"Duplicate movement group: {group_id}")
        group_ids.add(group_id)
        selected = [routes[r] for r in group["route_ids"]]
        if not selected:
            raise ValueError(f"{group_id}: route_ids cannot be empty")
        for left, right in zip(selected, selected[1:]):
            if math.dist(left["points"][-1], right["points"][0]) > 1e-4:
                raise ValueError(f"{group_id}: route segments do not connect")
        depart = number(group["depart_s"], "departure")
        deadline = number(group["reveal_s"], "reveal")
        if deadline < depart:
            raise ValueError(f"{group_id}: reveal precedes departure")
        settle = number(group.get("settle_s", 0), "settle")
        travel = sum(r["travel_s"] for r in selected) + settle
        groups.append({**group, "length_units": sum(r["length_units"] for r in selected),
                       "travel_s": travel, "arrival_s": depart + travel,
                       "available_s": deadline - depart,
                       "slack_s": deadline - depart - travel,
                       "feasible_estimate": depart + travel <= deadline + 1e-8})
    return {"project_id": plan.get("project_id"), "fps": float(fps),
            "frame_start": 1, "frame_end": cursor - 1, "total_frames": cursor - 1,
            "duration_s": float(Fraction(cursor - 1) / fps),
            "time_convention": "inclusive frames; half-open seconds",
            "shots": shots, "routes": routes, "movement_groups": groups,
            "all_groups_feasible_estimate": all(g["feasible_estimate"] for g in groups)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = compile_plan(json.loads(args.plan.read_text(encoding="utf-8-sig")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(result['shots'])} edits; {result['total_frames']} frames; {result['duration_s']} seconds")
    if not result["all_groups_feasible_estimate"]:
        print("Route estimate exceeds one or more reveal deadlines.")
        raise SystemExit(2)


if __name__ == "__main__":
    main()
