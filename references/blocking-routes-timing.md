# Blocking, routes and time

## Read the actual place

Register a director's annotation using multiple visible scene landmarks and camera/overview views. A plausible rock platform is not evidence for the marked rock seam. Record the shared starting cluster, observer, handoff neighbor, waiting group, screen direction and cover. Show a labeled top view plus the intended camera view. Keep source facts, confirmed choices and proposed coordinates/lenses separate.

If a group must travel to an ambush, do not initialize it at the destination just because it is offscreen. Track the shared route until the branching point, then each group's distinct branch and endpoint. Preserve character IDs and color IDs.

## Budget movement

Measure 3D polyline lengths in documented scene units. A route estimate is sum(length / assumed speed), plus pauses and settling. Distinguish level movement from climbs. Record both departure and required reveal time. Simultaneous groups each get that same global window; feasibility uses the slowest group's arrival, not the sum of group travel times. Do not confuse each group's travel time with the sum of shots that show it.

Use timing as an estimate, not proof of contact or physically possible motion. Inspect slopes, support, crowd spacing and actual animation. Ask for a material unresolved directorial choice; routine estimates may be labeled and advanced within authorized scope.

## Compile a stable edit

Use templates/sequence-plan.json and scripts/plan_sequence.py. Array order is edit order. Give each segment a unique edit_id independent of its source shot_id; preserve inserts, reused source IDs and out-of-order numbering. Frame ranges are inclusive, start at 1; time intervals are half-open [start_s, end_s), with start_s = (start_frame - 1) / fps. Durations must resolve exactly to whole frames.

When changing a duration, retain unrelated durations and regenerate all downstream absolute times, camera cuts, action events, route deadlines, captions and SRT. Do not independently hand-edit several copies of the time table.

MountainCase example: 43 edit segments, including 11-1b and 11-33 → 11-35 → 11-34. Four duration changes added 12 seconds: 132.5 → 144.5 seconds at 24 fps (3180 → 3468 frames). Departure at 33 seconds and reveal at 63 seconds created a shared 30-second travel window. These are case data, not default timing.
