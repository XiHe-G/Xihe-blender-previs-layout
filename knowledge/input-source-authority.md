# Input Source Authority

Use source types for the decisions they are good at:

1. **Story, shot table, and explicit director notes:** timing, beat order, participants, intent, and overrides.
2. **Storyboard/keyframes:** composition, shot size, screen direction, staging, and motivated camera changes.
3. **Scene references:** architecture, landmarks, scale cues, entrances, exits, and depth layers.
4. **Character references:** identity cues, relative scale, proxy type, silhouette, and direction markers.

Resolve conflicts by field, not by declaring one whole document authoritative. Record the source version, original value, conflict, chosen value and reason. Latest explicit user/director instructions own the fields they address; preserve other approved fields. A newer shot table may own edit order, deleted dialogue and action beats while an older PDF still supplies composition. Match by content as well as IDs: inserts and reordered shot numbers can invalidate numeric page-to-shot joins.

Director-annotated scene images override inferred starting positions and paths. Register marks against actual scene landmarks before assigning coordinates. Route lengths, speeds, inferred lenses and scene-adapted heights remain estimates unless the user confirms them. Do not pass estimates off as original reference values.

AUTO fills safe presentation defaults, INFER uses stable evidence, and ASK is reserved for unresolved choices that materially alter blocking or camera meaning. Prior approval of the same complete plan remains valid. V1.2 separately requires the user-requested whole-story route/position diagram confirmation before layout; a general production request or opening-only approval does not cover newly inferred retreats and endings. See `references/story-blocking-confirmation.md`. Use `templates/production-context.json` and read `references/blocking-routes-timing.md` when spatial feedback changes timing.


## SYSTEM-V2 field refinements

Floor plans / top views own spatial topology when supplied; scene appearance references own architectural appearance and proposed Lighting Context. Character sheets own identity/proportions; height charts own relative height. A scene image never silently overrides confirmed blocking/Camera. Latest explicit instructions override only addressed fields. Optional video study/reconstruction owns observed motion only within that requested task; comparison-only video is not downstream generation input. Record these distinctions in production state and AI handoff.
