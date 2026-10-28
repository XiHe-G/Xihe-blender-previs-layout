"""Previs motion grammar: compile action beats into continuous sampled states."""

from __future__ import annotations

import math
from copy import deepcopy
from typing import Any


POSE_PRIMITIVES = {
    "STAND": "STAND",
    "CROUCH": "CROUCH",
    "KNEEL": "KNEEL",
    "BOW": "BOW",
    "SIT": "SIT",
    "LIE": "LIE",
    "CORPSE": "CORPSE",
}
MOVE_PRIMITIVES = {"MOVE_TO", "WALK", "RUN", "APPROACH", "RETREAT", "FOLLOW"}


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def smooth(value: float) -> float:
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def lerp(a: float, b: float, amount: float) -> float:
    return float(a) * (1.0 - amount) + float(b) * amount


def lerp_vec(a: list[float], b: list[float], amount: float) -> list[float]:
    return [lerp(x, y, amount) for x, y in zip(a, b)]


def angle_delta(a: float, b: float) -> float:
    return (float(b) - float(a) + 180.0) % 360.0 - 180.0


def lerp_angle(a: float, b: float, amount: float) -> float:
    return (float(a) + angle_delta(a, b) * amount) % 360.0


def yaw_to(source: list[float], target: list[float]) -> float:
    dx, dy = float(target[0]) - float(source[0]), float(target[1]) - float(source[1])
    return math.degrees(math.atan2(-dx, dy)) % 360.0


def _target_position(action: dict[str, Any], characters: dict[str, dict[str, Any]]) -> list[float]:
    target = action.get("target")
    if isinstance(target, str):
        return list(characters[target]["position"])
    if isinstance(target, list):
        return [float(value) for value in target]
    if isinstance(action.get("to"), list):
        return [float(value) for value in action["to"]]
    raise ValueError(f"Action {action.get('id')} requires target or to")


def base_state(character: dict[str, Any]) -> dict[str, Any]:
    pose = str(character.get("pose", "STAND")).upper()
    return {
        "position": [float(value) for value in character.get("position", [0, 0, 0])],
        "yaw": float(character.get("facing", 0.0)),
        "pose": pose,
        "head_pitch": 58.0 if pose == "BOW" else 0.0,
        "head_yaw": 0.0,
        "lean": 82.0 if pose == "BOW" else 12.0 if pose == "CROUCH" else 0.0,
        "reach": 0.0,
        "motion": "HOLD",
        "progress": 1.0,
        "phase": "END",
    }


def _phase(progress: float) -> str:
    if progress <= 0.08:
        return "START"
    if progress <= 0.22:
        return "ANTICIPATION"
    if progress <= 0.72:
        return "ACTION"
    if progress <= 0.9:
        return "TRANSITION"
    if progress < 1.0:
        return "SETTLE"
    return "END"


def _finish(state: dict[str, Any], action: dict[str, Any], characters: dict[str, dict[str, Any]]) -> dict[str, Any]:
    result = deepcopy(state)
    primitive = action["primitive"]
    if primitive in POSE_PRIMITIVES:
        result["pose"] = POSE_PRIMITIVES[primitive]
    elif primitive in {"RISE_FROM_KNEEL", "RISE_FROM_CROUCH", "STAND_FROM_SIT"}:
        result["pose"] = "STAND"; result["lean"] = 0.0; result["head_pitch"] = 0.0
    elif primitive == "FALL":
        result["pose"] = "LIE"
    elif primitive in MOVE_PRIMITIVES:
        target = _target_position(action, characters)
        if primitive == "APPROACH" and isinstance(action.get("target"), str):
            distance = float(action.get("distance", 1.0))
            target_yaw = yaw_to(result["position"], target)
            target = [target[0] + math.sin(math.radians(target_yaw)) * distance,
                      target[1] - math.cos(math.radians(target_yaw)) * distance,
                      target[2]]
        elif primitive == "RETREAT":
            direction = [result["position"][i] - target[i] for i in range(3)]
            length = math.hypot(direction[0], direction[1]) or 1.0
            distance = float(action.get("distance", 1.5))
            target = [result["position"][0] + direction[0] / length * distance,
                      result["position"][1] + direction[1] / length * distance,
                      result["position"][2]]
        result["yaw"] = yaw_to(result["position"], target)
        result["position"] = target
    elif primitive in {"TURN_LEFT", "TURN_RIGHT", "TURN_TO_TARGET"}:
        if primitive == "TURN_TO_TARGET":
            result["yaw"] = yaw_to(result["position"], _target_position(action, characters))
        else:
            sign = 1.0 if primitive == "TURN_LEFT" else -1.0
            result["yaw"] = (result["yaw"] + sign * float(action.get("degrees", 90.0))) % 360.0
    elif primitive in {"LOOK_UP", "HEAD_RAISE"}:
        result["head_pitch"] = float(action.get("degrees", -8.0))
    elif primitive == "LOOK_DOWN":
        result["head_pitch"] = float(action.get("degrees", 28.0))
    elif primitive in {"LOOK_LEFT", "LOOK_RIGHT"}:
        sign = 1.0 if primitive == "LOOK_LEFT" else -1.0
        result["head_yaw"] = sign * float(action.get("degrees", 35.0))
    elif primitive in {"LOOK_AT_TARGET"}:
        result["head_yaw"] = angle_delta(result["yaw"], yaw_to(result["position"], _target_position(action, characters)))
    elif primitive in {"REACH", "POINT"}:
        result["reach"] = 1.0
    result.update({"motion": primitive, "progress": 1.0, "phase": "END"})
    return result


def _active(state: dict[str, Any], action: dict[str, Any], progress: float, characters: dict[str, dict[str, Any]]) -> dict[str, Any]:
    result = deepcopy(state)
    primitive = action["primitive"]
    eased = smooth(progress)
    result.update({
        "motion": primitive,
        "progress": progress,
        "phase": _phase(progress),
        "from_pose": state["pose"],
    })
    if primitive in POSE_PRIMITIVES:
        result["to_pose"] = POSE_PRIMITIVES[primitive]
    elif primitive in {"RISE_FROM_KNEEL", "RISE_FROM_CROUCH", "STAND_FROM_SIT"}:
        result["to_pose"] = "STAND"
        result["lean"] = lerp(state.get("lean", 0.0), 0.0, eased)
        result["head_pitch"] = lerp(state.get("head_pitch", 0.0), 0.0, eased)
    elif primitive == "FALL":
        result["to_pose"] = "LIE"
    elif primitive in MOVE_PRIMITIVES:
        target = _finish(state, action, characters)
        result["position"] = lerp_vec(state["position"], target["position"], eased)
        result["yaw"] = lerp_angle(state["yaw"], target["yaw"], min(1.0, progress * 3.0))
        result["gait"] = "RUN" if primitive == "RUN" else "WALK"
    elif primitive in {"TURN_LEFT", "TURN_RIGHT", "TURN_TO_TARGET"}:
        target = _finish(state, action, characters)
        result["yaw"] = lerp_angle(state["yaw"], target["yaw"], eased)
    elif primitive in {"LOOK_UP", "HEAD_RAISE", "LOOK_DOWN", "LOOK_LEFT", "LOOK_RIGHT", "LOOK_AT_TARGET"}:
        target = _finish(state, action, characters)
        result["head_pitch"] = lerp(state.get("head_pitch", 0.0), target.get("head_pitch", 0.0), eased)
        result["head_yaw"] = lerp(state.get("head_yaw", 0.0), target.get("head_yaw", 0.0), eased)
    elif primitive in {"REACH", "POINT"}:
        result["reach"] = eased
    return result


def sample_state(character: dict[str, Any], actions: list[dict[str, Any]], frame: int,
                 characters: dict[str, dict[str, Any]]) -> dict[str, Any]:
    state = base_state(character)
    relevant = sorted((action for action in actions if action["character"] == character["id"]), key=lambda item: (item["start"], item["end"]))
    for action in relevant:
        if frame < action["start"]:
            break
        if frame >= action["end"]:
            state = _finish(state, action, characters)
            continue
        duration = max(1, action["end"] - action["start"])
        progress = (frame - action["start"]) / duration
        result = _active(state, action, progress, characters)
        if action.get("causal_execution") is not None:
            from perception_reaction import narrative_location
            return narrative_location(action, frame, result)
        return result
    return state


def active_beat(actions: list[dict[str, Any]], frame: int) -> str:
    active = [action for action in actions if action["start"] <= frame <= action["end"]]
    if not active:
        return "HOLD"
    meaningful = [action for action in active if action["primitive"] not in {"HOLD", "CORPSE"}]
    if not meaningful:
        return "HOLD"
    return " + ".join(str(action.get("label") or action["primitive"]) for action in meaningful)
