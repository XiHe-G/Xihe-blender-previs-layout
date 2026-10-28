# EVENT-LOWERING-PLAN/1.0

The schema accepts an individual plan or a graph report containing plans. Required plan fields: lowering_version, plan_id, graph_id, event_id/type, lowering_status, input_evidence, required_inputs, resolved_inputs, derived_inputs, primitive_sequence, channel_plan, entry_state, exit_requirements, continuity_contract, dependencies, constraints, confidence, provenance and warnings. validation_status is separate from the six lowering statuses.

| Event | Fixed mapping | Minimum explicit evidence |
|---|---|---|
| MOVE | MOVE_PROFILE | Entry fact/exit, destination or explicit path, time, spacing and arrival velocity or permission to derive |
| ENTER | MOVE_PROFILE | Entry point consistent with current state, destination and movement requirements |
| EXIT | MOVE_PROFILE | Explicit exit point/path; no inferred screen side |
| LOOK | ORIENT_TO | One target direction/point/entity, angular speed; HEAD is recorded TECHNICAL_DEFAULT |
| TURN | ORIENT_TO | One target and angular speed; root/body/head level explicit or recorded root default |
| DODGE | MOVE_PROFILE + OFFSET_PATH | Threat direction, chosen direction, offset, base destination, start/peak/end, return policy and speed/spacing |
| RELEASE | ATTACH_DETACH | Stable object/owner, attached entry, release time, speed, direction, socket offset and owner-velocity fraction |
| PROJECTILE_TRAVEL | MOVE_PROFILE on PROJECTILE_TRANSFORM | Same FREE entity, route endpoint/time/speed contract |
| RECOVERY | RECOVERY_PROFILE | Immediately preceding moving exit, duration, displacement limit, arrival velocity or explicit stop/stable intent |

ATTACK, BLOCK, CONTACT, NEAR_MISS, FOLLOW_THROUGH, TAKEOFF, LAND, VFX_TRIGGER and ATTENTION_HANDOFF have no execution rule. A dependent CONTACT can supply an explicit target_point for travel without creating contact animation. Such a graph still cannot build as a complete new sequence while CONTACT remains unresolved.

Example evidence.value (a JSON string in the unchanged AG evidence envelope): `{"destination":[4,0,0],"spacing":"constant","arrival_velocity":[1,0,0]}`. Directions/positions use world coordinates, times global seconds, lengths metres. Supported spacing vocabulary: constant, accelerate_cruise_decelerate, ease_in, ease_out, ease_in_out. Path arrays map to existing POLYLINE; no unspecified curve is invented.

Each resolved value records value/source/derived_from/method/confidence. Sources are AUTHOR_EXPLICIT, CONSTRAINT, DEPENDENCY, PREVIOUS_EXIT_STATE, ENTITY_STATE, DERIVED, TECHNICAL_DEFAULT. Runtime-solved peak speed is copied into derived_inputs with S51_RUNTIME_PROFILE_SOLVE and its exact input lineage. Every primitive parameter also has fixed-registry translation provenance. Defaults lower confidence to MEDIUM, while INFERRED author quantities stop for confirmation.

RELEASE may derive direction from one explicitly dependent travel endpoint and the owner's evaluated release position plus declared socket offset. The method is DERIVED_FROM_DEPENDENCY. Speed is never invented. Multiple endpoints or multiple safe dodge directions produce AMBIGUOUS. Zero directions and malformed author vectors are not READY. Runtime limitations still apply; failed C0/C1 or unsupported representation prevents fragment publication.

Statuses: READY, NEEDS_AUTHOR_INPUT, AMBIGUOUS, UNSUPPORTED, BLOCKED_BY_CONSTRAINT, BLOCKED_BY_OVERRIDE. Only READY + HIGH/MEDIUM + validation PASS can publish execution. LOW never executes. STATE_CONFLICT and LOWERING_VALIDATION_FAIL are diagnostic codes, not extra status enum values.
