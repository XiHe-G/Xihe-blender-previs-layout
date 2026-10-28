"""Apply natural-language-derived Director Override records to a project manifest."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from common import deep_merge


def _find(items: list[dict[str, Any]], key: str, value: str) -> dict[str, Any]:
    for item in items:
        if str(item.get(key)) == value:
            return item
    raise ValueError(f"Director Override target not found: {key}={value}")


def apply_overrides(project: dict[str, Any], payload: dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, set[str]]]:
    """Return a patched copy and per-shot rebuild scopes.

    Supported targets are ``shot``, ``camera``, ``character:ID``,
    ``action:ID`` and ``environment:ID``. The user never needs to edit this
    representation; the calling Codex instance translates natural-language
    notes into these small records.
    """

    result = deepcopy(project)
    affected: dict[str, set[str]] = {}
    if not payload:
        return result, affected
    for record in payload.get("overrides", []):
        shot_id = str(record.get("shot", "*"))
        target = str(record["target"])
        changes = dict(record.get("changes", {}))
        scopes = affected.setdefault(shot_id, set())
        if target.startswith("environment:"):
            element_id = target.split(":", 1)[1]
            element = _find(result.setdefault("scene", {}).setdefault("elements", []), "id", element_id)
            element.update(deep_merge(element, changes))
            scopes.add("environment")
            continue
        if shot_id == "*":
            raise ValueError(f"Override target {target!r} requires a shot id")
        shot = _find(result.get("shots", []), "id", shot_id)
        if target == "shot":
            shot.update(deep_merge(shot, changes)); scopes.update({"characters", "camera"})
        elif target == "camera":
            shot["camera"] = deep_merge(shot.get("camera", {}), changes); scopes.add("camera")
        elif target.startswith("character:"):
            character_id = target.split(":", 1)[1]
            blocking = shot.setdefault("blocking", [])
            entry = next((item for item in blocking if item.get("character") == character_id), None)
            if entry is None:
                entry = {"character": character_id}; blocking.append(entry)
            entry.update(deep_merge(entry, changes)); scopes.update({"characters", "camera"})
        elif target.startswith("action:"):
            action_id = target.split(":", 1)[1]
            action = _find(shot.setdefault("actions", []), "id", action_id)
            action.update(deep_merge(action, changes)); scopes.update({"characters", "camera"})
        else:
            raise ValueError(f"Unsupported Director Override target: {target}")
    return result, affected

