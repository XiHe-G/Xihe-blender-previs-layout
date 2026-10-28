# Whole-story blocking confirmation

This stage preserves the diagram-first workflow requested for applicable projects. The current user's authorization takes precedence: explicit autonomous candidate direction permits routine unlocked staging choices without a new approval at every node. Still prepare the spatial plan and record AUTONOMOUS_CANDIDATE with its real authorization; never forge an APPROVED design record. When diagram-first review is requested, use the confirmation process below. Its purpose is to expose important spatial choices before expensive production.

## Design from story and ending

Read the story beats and ending composition first. Work backward from required final relationships, then trace each actor forward from their source-backed start. Identify the beats where a position, facing, visibility, formation, height, prop ownership or relationship changes. The node count follows the story; do not impose a fixed six-node formula.

For every actor, including minor actors and actors offscreen:
- starting location and intention;
- path/corridor through each relevant node, intermediate turn or waiting point;
- facing / eye target and relation to other actors;
- level and support (bridge, road, ledge, room, stairs), with feet-level elevation where known;
- visible, intentionally occluded, or out of camera, with actual offscreen location;
- final location and departure direction, including who stays;
- time window, order or provisional time, and source/estimate status.

A group line can simplify the drawing but cannot replace the individual actor rows. HOLD is explicit. Hiding a mesh is not a substitute for a spatially valid retreat. Validate common paths, branches, crossing traffic and different elevations in the scene.

## Review package

Produce these before requesting confirmation:
1. Whole-scene route overview with landmarks, axis/view direction, arrows, actor IDs/colors, start/end and height levels.
2. Key-node position diagrams, using a consistent map framing. Add a side/elevation view or representative camera view when a top view cannot explain bridge-over-road or mountain occlusion.
3. Per-character node/action table with intention, movement/stay, facing, visibility, endpoints and time/order.
4. Short decisions and unresolved assumptions list; identify which drawing/version is being confirmed.

Use actual scene overview imagery when available. Coordinate-only diagrams are useful drafts but do not prove terrain clearance, camera visibility or that a marked place was correctly recognized. Read each generated diagram before showing it. Split crowded routes into stage/character panels, enlarge labels, and provide detail views instead of forcing many overlapping labels into one image.

scripts/review_blocking.py can validate actor/node coverage, generate editable SVG maps, CSV and an HTML review page, and check a recorded approval against the exact plan hash. Its map omits terrain unless separately supplied; add scene-context views for production. It does not make narrative decisions or verify that an approval quote is authentic. The agent must confirm the quote against the conversation.

## Confirmation and revisions

State the version, decisions to confirm and any material estimates. When scoped confirmation is required, ask the user to confirm the route/position package; do not start dependent animation while waiting. When autonomous candidate authoring is explicitly authorized, record that scope and proceed without claiming the design itself was approved. Record the real response in a separate decision file using templates/blocking-decision.json, with plan_sha256, scope and message/source. Do not provide a tool that auto-approves its own output.

If the same complete plan already has explicit approval, reuse it. If only an opening still was approved, add the missing full-story nodes for confirmation. If a plan changes, its old fingerprint is stale: generate the changed diagrams and recheck the active authorization; request confirmation of protected or approval-gated routes/positions. Do not reinterpret a vague earlier “continue” as approval of a newly inferred ending.

Layout, camera, timing, captions and render products consume the confirmed plan revision. Technical checks and final aesthetic acceptance are separate.

## MountainCase lesson

Opening V2 correctly confirmed the common rock seam and two paths onto the bridge, but did not lock the whole retreat and ending. The later director review showed eight rats escaping toward the foreground when they should leave via the two bridge ends into the western mountain backs. Rat One must stay on the bridge. The final over-shoulder relationship also required the two humans farther along the road, so their confrontation/departure path and related cameras changed together.

The expanded stage would show those later nodes before the first whole layout. The case diagrams in the manual are retrospective teaching examples; they are not evidence that this full-stage approval existed during the original production.
