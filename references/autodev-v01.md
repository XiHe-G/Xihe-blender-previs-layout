# AUTODEV V0.1 development protocol

This is a bounded Skill-development workflow, not automatic animation repair.
User scope controls target and iteration budget. Keep the NARRATIVE / COMBAT_DYNAMIC routes, optional references, CSP execution and simplified proxies.

1. Before formal changes, create a full recoverable snapshot and verify every file hash; record version, environment, working tree and run ID outside the Skill.
2. Audit code and evidence separately. Source presence, schema expressiveness, old reports and file existence do not prove fresh runtime verification.
3. Select one small capability; write a falsifiable hypothesis and acceptance contract before changing its owning module. Prototype in isolation, then promote only after real validation.
4. Use `scripts/autodev_guard.py` for mutation commands. Persist command/run IDs, argv, expected mutation and state. A timeout remains UNCERTAIN even if time passes. Inspect process completion, scene objects, cameras and keys before reconciliation; never blindly replay. The inspection record must refer to an actual independently read report.
5. Use `scripts/autodev_evaluator.py` to hash actual inputs/outputs and validator reports for baseline/candidate receipts. VERIFIED is scoped to named validators, not a claim about artistic quality. Review remains PENDING_DIRECTOR_REVIEW until actually conducted.
6. Test unit → CSP → Blender build → saved-scene reopen/numeric capture → low-resolution preview. Preserve failed attempts and exactly identify measurement-window corrections. Never tune accepted thresholds to hide failures.
7. Keep a per-run rule registry, per-field authority table, stop policy, benchmark and regression registry. Conflicting owners for the same scope/field stop dependent work. Do not invent an absent benchmark script or approved result.
8. Bounded repair requires a new evidence-backed diagnosis each attempt. Maximum three attempts unless the user sets a stricter bound. Accept only improvements without regressions; restore only recorded owned changes if rejected. Never restore over unrelated user edits.

Screen preflight contract: `screen_trajectory_preflight.classify_direction` delegates supported full-sample direction measurement to the existing S3.5 checker. HOLD_REGION needs an explicit normalized region. TOWARD_CENTER / AWAY_FROM_CENTER remain NOT_REVIEWED. Center-only projection is not mesh visibility, occlusion, pixel truth or downstream AI effectiveness. Projection supports the documented perspective 36mm, 16:9, no-shift model; use native trace for other cameras. This API is opt-in; it does not silently insert itself into every existing Builder call.

Do not promote capability merely because a test passes once. Do not use a total Layout Quality score. A layout gate needs blocking, spatial, continuity, timing, camera execution, runtime stability and applicable motion/physics evidence; missing evidence is NOT_READY.
