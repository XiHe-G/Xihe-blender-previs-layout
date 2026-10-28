# Production scene state

Status: INTERFACE_ONLY; structural validation implemented. `scene-state` is a registry and boundary snapshot over Author Graph + CSP + existing continuity. Its `ag_ref`, `csp_ref`, `continuity_ref` point to existing shot/event identities. It owns no FPS, cut list, keyframes or second timeline. Generic narrative scenes use their existing sequence continuity source; AG/CSP adapters remain explicit and do not imply new AG→narrative lowering.

The typed template records scene/sequence/shot IDs, world axes and units, stable landmark IDs and coordinates, entrances/exits, walkable and height bands, foreground/middle/background, key occluders, support surfaces, light zones and persistent props. DOOR_A and WINDOW_NORTH remain distinct even when screen-left changes. Existing shot order comes from the authoring source, never lexical shot-number sorting.

Register the complete scene cast before snapshot generation. Every boundary preserves identity, world position, screen relationship, facing, gaze, height profile, body orientation, prop control, support, motion phase, action trend, combat state, lighting zone and terminal state. Invisible actors retain world/action state and next entrance dependency (`NONE` means no further entrance). A character absent from screen is not absent from the world. New arrivals must already be represented offscreen; removal at death/exit is expressed as terminal state, not deletion.

Validator rejects duplicate IDs, dangling landmarks, inconsistent cast, unknown props/support/light zones and bad height ranges. Source-reference existence and native positions require project adapters/evidence; an unresolved reference is NOT_REVIEWED, not a validated scene. No automatic native snapshot extractor was added.
