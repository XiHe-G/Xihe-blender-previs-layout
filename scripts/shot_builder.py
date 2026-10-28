"""Normalize the compact production manifest into one self-contained shot plan."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


SUPPORTED_PROXY_TYPES = {"HUMAN", "HUMANOID", "QUADRUPED", "BIPED_CREATURE", "CORPSE", "GENERIC_CREATURE"}
LAYOUT_MODES = {"NARRATIVE", "COMBAT_DYNAMIC"}
PROXY_STYLES = {"AUTO", "NARRATIVE_BOX_5", "COMBAT_BOX_4", "ARTICULATED"}


def resolve_proxy_style(character, mode="NARRATIVE", default="AUTO"):
    style = str(character.get("proxy_style", "AUTO")).upper()
    if style == "AUTO":
        style = str(default).upper()
    if style not in PROXY_STYLES:
        raise ValueError(f"Unsupported proxy_style: {style}")
    if style == "AUTO":
        if character.get("proxy_type", "HUMAN").upper() == "QUADRUPED":
            return "ARTICULATED"
        return "COMBAT_BOX_4" if mode == "COMBAT_DYNAMIC" else "NARRATIVE_BOX_5"
    return style


def validate_project(project: dict[str, Any]) -> None:
    required = ["project_id", "scene", "characters", "shots"]
    missing = [key for key in required if key not in project]
    if missing:
        raise ValueError(f"Project manifest missing: {missing}")
    if not project["shots"]:
        raise ValueError("Project manifest has no shots")
    if str(project.get("layout_mode", "NARRATIVE")).upper() not in LAYOUT_MODES:
        raise ValueError("layout_mode must be NARRATIVE or COMBAT_DYNAMIC")
    if str(project.get("proxy_style", "AUTO")).upper() not in PROXY_STYLES:
        raise ValueError("Unsupported project proxy_style")
    ids = [str(item["id"]) for item in project["characters"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Character ids must be unique")
    for character in project["characters"]:
        kind = str(character.get("proxy_type", "HUMAN")).upper()
        if kind not in SUPPORTED_PROXY_TYPES:
            raise ValueError(f"Unsupported proxy type {kind} for {character['id']}")


def _resolve_facing(value: Any, source: list[float], characters: dict[str, dict[str, Any]]) -> float:
    if isinstance(value, (int, float)):
        return float(value) % 360.0
    if isinstance(value, dict) and value.get("target"):
        target = characters[str(value["target"])]["position"]
        import math
        dx, dy = float(target[0]) - float(source[0]), float(target[1]) - float(source[1])
        return math.degrees(math.atan2(-dx, dy)) % 360.0
    return 0.0


def normalize_shot(project: dict[str, Any], shot_id: str) -> dict[str, Any]:
    validate_project(project)
    shot = deepcopy(next(item for item in project["shots"] if str(item["id"]) == shot_id))
    mode = str(shot.get("layout_mode", project.get("layout_mode", "NARRATIVE"))).upper()
    if mode not in LAYOUT_MODES:
        raise ValueError(f"Unsupported layout_mode: {mode}")
    fps = int(shot.get("fps", project.get("fps", 24)))
    frames = int(shot.get("frames", round(float(shot.get("duration", 4.0)) * fps)))
    if fps <= 0 or frames <= 0:
        raise ValueError(f"Invalid timing for {shot_id}")
    characters = {str(item["id"]): deepcopy(item) for item in project["characters"]}
    for entry in shot.get("blocking", []):
        character_id = str(entry["character"])
        if character_id not in characters:
            raise ValueError(f"Shot {shot_id} refers to unknown character {character_id}")
        characters[character_id].update({key: deepcopy(value) for key, value in entry.items() if key != "character"})
    for character in characters.values():
        character.setdefault("display_name", character["id"])
        character.setdefault("height", 1.7)
        character.setdefault("proxy_type", "HUMAN")
        character.setdefault("color", [0.25, 0.55, 0.95])
        character.setdefault("position", [0.0, 0.0, 0.0])
        character.setdefault("pose", "STAND")
        character.setdefault("state", "ALIVE")
        character["proxy_style"] = resolve_proxy_style(character, mode, project.get("proxy_style", "AUTO"))
    for character in characters.values():
        character["facing"] = _resolve_facing(character.get("facing", 0.0), character["position"], characters)
    action_ids: set[str] = set()
    for index, action in enumerate(shot.setdefault("actions", []), start=1):
        action.setdefault("id", f"{shot_id}-A{index:02}")
        action["primitive"] = str(action["primitive"]).upper()
        action["start"] = int(action.get("start", 1))
        action["end"] = int(action.get("end", frames))
        if action["id"] in action_ids:
            raise ValueError(f"Duplicate action id: {action['id']}")
        action_ids.add(action["id"])
        if action.get("character") not in characters:
            raise ValueError(f"Action {action['id']} refers to unknown character")
        if not 1 <= action["start"] <= action["end"] <= frames:
            raise ValueError(f"Action {action['id']} falls outside shot timing")
        if action["primitive"] in {"REACH", "POINT"} and characters[action["character"]]["proxy_style"] != "ARTICULATED":
            raise ValueError(f"{action['id']}: REACH/POINT needs an explicit articulated override or a body/head reinterpretation; box proxies have no hands")
    resolution = shot.get("resolution", project.get("resolution", [1280, 720]))
    return {
        "version": "1.0",
        "project_id": str(project["project_id"]),
        "scene": deepcopy(project["scene"]),
        "shot_id": shot_id,
        "layout_mode": mode,
        "fps": fps,
        "frames": frames,
        "resolution": [int(resolution[0]), int(resolution[1])],
        "characters": list(characters.values()),
        "actions": shot["actions"],
        "camera": deepcopy(shot.get("camera", {})),
        "notes": deepcopy(shot.get("notes", [])),
    }
