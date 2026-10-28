# Execution State Chain

An entity's initial author evidence states position, velocity, heading_degrees and at_time. Ownership/support may be explicit; missing neutral angular velocity/support use labelled technical defaults. State is transferred by entity ID and channel, never by creating a new per-shot entity.

Position/velocity come from the most recent available movement fragment at the next event's start. At an exact prior endpoint the source is PREVIOUS_EXIT_STATE / CONTINUITY_INHERITANCE. Concurrent orthogonal LOOK reads the moving actor's evaluated state with DEPENDENCY provenance. Rotation channels retain their own exits; root rotation is inherited by later root movement. Neutral local HEAD/BODY entries are recorded defaults, not a claim of recovered acting intent.

Explicit source_event/dependency order is topologically sorted. Known target/owner motion read dependencies are also resolved before runtime. Failed prerequisites prevent dependent execution. Missing tracks, gaps without an authored state, static recovery entries and conflicts between explicit next entry and inherited exit stop rather than overwrite.

STATE_CONFLICT maps to BLOCKED_BY_CONSTRAINT with validation FAIL. S52 does not generate a reset or infer impact authority. Explicit discontinuities remain subject to the existing S4.5 authorization mechanism; this conservative lowering subset requests input instead of synthesizing a discontinuous connection, including SNAP. Declaring an event name alone never bypasses C1.

Channel ownership reuses S51 channels and three operators: sequential shared endpoints, orthogonal concurrent channels, explicit base+offset addition. Overlapping writers conflict. Same global timebase is used throughout. All ready fragments run the unchanged S4.5 C0/C1 test; any failure prevents CSP. Native composed positions and reopened orientations are measured again. C2 is reported independently and is not silently repaired.

Constraint preview supports explicit world bounds, speed bounds and normalized screen regions using existing projection/region definitions. Projection is geometric center evidence, not pixel-exact visibility or occlusion. A dynamic-camera constraint requiring evaluated camera evidence, or another subject without an evaluated preview, stops rather than passing on a stale static camera. Unknown/unconfirmed constraints request author input. Relevant LOCKED overrides stop before runtime; unknown lock channels fail closed.
