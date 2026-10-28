# Camera Intent Lowering

SHOT_INTENT.camera_behavior_intent uses the existing evidence envelope and an explicit JSON semantic vocabulary. Transforms/lens entry state live in the separate approved execution context, not in Shot Intent. No camera position is chosen for artistic reasons.

| Behavior | Primitive | Required quantities |
|---|---|---|
| HOLD | CAM_HOLD | Explicit LOCKED_HOLD / COMPOSITION_HOLD / SOFT_HOLD, subject, entry camera and readable target state |
| REFRAME | CAM_REFRAME | Subject, normalized rectangle [xmin,ymin,xmax,ymax], duration, rotation/translation limits |
| FOLLOW | CAM_FOLLOW | Subject, screen anchor, tracking strength, lag, distance or evaluable entry relation |
| LEAD_LAG | CAM_LEAD_LAG | Explicit lead distance, lag seconds, scalar screen bias and transition duration |
| PUSH_PULL | CAM_PUSH_PULL | Explicit PUSH/PULL, travel distance and time; fixed lens |
| CATCH_UP | CAM_CATCH_UP | Subject, explicit entry lag, tracking strength, catch-up and settle fractions |

Bare historical HOLD remains NEEDS_AUTHOR_INPUT in this safe subset; S52 does not silently upgrade it to LOCKED_HOLD. Historical calibration may be supplied as explicit sourced author evidence in a future adapter. “Tighter” without a dolly/lens decision is AMBIGUOUS. Lens-changing lowering is UNSUPPORTED in this first subset.

start/end semantic quantities may explicitly narrow a behavior window within its Shot time range. Otherwise the Shot interval is used, with end-exclusive timeline termination mapped through the existing timebase to the last available sample; provenance distinguishes explicit bounds from this sampling derivation. Adjacent camera windows inherit actual camera velocity, orientation, lens and tracking relationship. No private time conversion exists.

Distance inherited from approved camera/subject entry is labelled DERIVED_FROM_ENTRY_STATE. Holding an approved orientation is an explicit execution-context policy. Follow/Lead/Catch-up are never introduced merely because the subject moves quickly. Missing evaluated target tracks stop before runtime; initial entity position alone is not treated as an indefinitely static trajectory.

Generated curves come exclusively from S51 camera_primitives.py. HOLD semantics import the existing S3.5 policy there. Native L5 uses the existing CAMERA_STATE and SCREEN_POSITION checks. Other camera mappings have unit-level rule coverage and inherit S51's runtime tests; they have not each been promoted to a new native S52 director benchmark.
