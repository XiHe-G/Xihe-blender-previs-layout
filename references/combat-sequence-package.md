# COMBAT SEQUENCE PACKAGE · CSP/1.0

This is the common intermediate representation inside COMBAT_DYNAMIC. It is not a third layout mode. NARRATIVE keeps its current builders, models and approval workflow.

## Two inputs, one production path

**SOURCE:** inspect the full unique action segment, actual PTS/timebase, edits and event changes; extract observable screen states and annotate inferred world paths/camera/hidden actions with confidence. A prose synopsis does not override visible source. An approved Blender reconstruction can be sampled into the same package for regression; this is not automatic video tracking.

**TEXT:** turn the plot and storyboard into explicit causes, initiative changes, action beats, rhythm, support/space and camera intent. Design the world/screen states and breakdowns yourself. Allocate preparation and recovery before filling burst intervals. Do not copy a fixture's stage, cast, cut count, duration or choreography. Record authorial choices as DESIGN, not SOURCE_MEASURED. Retain the existing route-confirmation policy and actual user authorizations.

Both inputs then use:

`Shot Plan + Action Beats + Rhythm Map → continuous routes/poses/proxies + screen targets + camera dynamics + continuity states → validate package → combat_sequence_builder.py → editable .blend + fresh frames → Clean/Debug/optional Sync → eight gates`.

The builder never branches on SOURCE versus TEXT. It consumes authored/sampled state tracks. It does not interpret the word ATTACK, infer unseen actions, solve combat, or automatically make timing good. Changes belong in the package and its authoring code; do not create a second text-only renderer or replay an old movie as a new build.

Before authoring either entry, apply the five conditional COMBAT_DYNAMIC director checks in [the presentation standard](layout-presentation-standard.md). Keep their decisions in the director plan and existing provenance/causality/screen/continuity records. OFFSCREEN and OPEN_END are evidence labels, not new phase enum values; CSP/1.0, required fields and the shared Builder are unchanged.

## Package fields and units

Use JSON or gzip-compressed JSON, `schema_version: CSP/1.0`, `layout_mode: COMBAT_DYNAMIC`, `entry_mode: SOURCE|TEXT`. Seconds are the design authority. `frame = 1 + round(seconds * fps)` is the default mapping; record deliberate alternative rounding. Samples 1…N correspond to 0…(N−1)/fps; encoded duration is N/fps. Store PTS/time-remap separately for nonuniform source media. No global speed-up without instruction.

| Field | Required content |
|---|---|
| `timebase`, `provenance` | FPS, frame count/origin, time origin, units, up/forward axes, source/crop/unique interval or design ownership; confidence and unresolved observations |
| `shot_plan` | Persistent shot ID, contiguous first frame and exclusive end, camera ID, seconds, action/relationship summary, dominant subject and framing intent |
| `action_beats` | Global event ID, owner/target, interval, outcome; PREPARE, COMPRESS, ACCELERATE, PEAK, CONTACT, FOLLOW_THROUGH, RECOVERY with APPLIES intervals or NA reasons; breakdown seconds and sample policy |
| `rhythm_map` | Scene-wide relax/tension/burst/hold/re-burst windows, dominant action, relative intensity, breathing space; never a fixed rhythm copied from a fixture |
| `actors`, tracks | Identity/color/proportion/style; root world route and velocity, support/airborne status; LOWER/UPPER compression/tilt/twist, head facing and delay; explicit endpoints only for visible proxies |
| `screen_targets` | Per shot and meaningful time: subject center UV, width/height or bbox UV, depth order, travel direction, main occluders, visible intent, margins; source measurement/design/approved baseline must be distinguished |
| `causal_links` | Cause/response event IDs, trigger/response times, anticipation if any, contact/near-miss point, incoming tangent/normal, response direction and strength rules; link receiver, prop and environment response |
| `proxy_lifecycles` | Stable object ID, role, owner/target, attachment/coordinate space, path/endpoints, visibility episodes, six lifecycle stages, end state; event IDs survive cuts |
| `camera_choreography` | States, trigger, target/lead point, anticipation/delay, entry/exit speed, acceleration/deceleration, aim/lens/roll, framing, transition/settle; actual camera samples are required |
| `continuity_states` | Each cut's previous/next samples, same active event IDs, phase, root/pose/head, velocity/rotation trend, support, weapon ownership, projectile and VFX age/visibility, camera state; intentional discontinuity needs source/edit evidence |
| `review_gates` | Eight named gates, PASS/FAIL/NOT_REVIEWED/NA, timecoded evidence, scope, fix/review result and artifact hash |

Do not store only a pair of Action Poses. Add breakdowns at release, contact, reversal, takeoff, apex, landing absorption, weapon sweep and camera response changes. Dense sections commonly need 1–3 output-frame samples; this is a diagnostic starting point, not a fixed cadence. Stable regions can be sparse. Inspect interpolated motion between samples; add samples until trajectories and changes in speed read correctly. Baking every frame cannot repair an originally poor design.

For closeups prioritize head facing, weapon tip, contact point and near-pass clearance over root centering. UV uses bottom-left origin; an offscreen center or bbox is a valid observation, not automatically a framing failure. Projected bounds do not measure true occlusion: manually annotate foreground, behind-camera/partly cropped states and readable windows. Compare within each shot; a cut changes projection even when world continuity is exact.

## Runtime contract

`scripts/combat_sequence_package.py` checks structure, coverage, event references, lifecycle applicability and numeric sanity; its `STRUCTURAL_PASS` is not a visual PASS.

`scripts/combat_sequence_builder.py` is the shared Blender 5.2 assembly backend. Fresh assets can use `actor_assets` (existing COMBAT_BOX_4 BoxRig), `primitive_assets` (CUBE/SPHERE/EMPTY/CAMERA) and `actor_pose_tracks`. More elaborate simple mesh/curve sets can come from an approved `scene_asset` `.blend` with a SHA256. The latter is an asset container, not an animation shortcut: the builder clears scene/object/data animation and rebuilds all motion from package tracks. It rejects armatures, constraints and modifiers rather than silently changing their meaning. Static asset parent transforms, mesh materials and render settings are retained.

`object_tracks` map object names to ordered `{frame, state}` samples. State contains `location`, `rotation_mode` (XYZ or QUATERNION), `rotation`, `scale`, `hide_render`, `hide_viewport`, and camera `lens` when applicable. Transform samples are local to the declared asset hierarchy; evaluated world matrices provide the world-path evidence. Unwrap Euler turns or keep quaternion hemispheres continuous before baking. Visibility uses constant keys; dense transforms use linear interpolation. Supply first and last samples even for holds. Static untracked asset objects retain their declared state.

`actor_pose_tracks` map actor asset IDs to `{frame,state}` using the existing `BoxRig.apply` interface: position, grounded, yaw, body_pitch/body_roll/body_yaw, lower_pitch/lower_roll, head_pitch/head_yaw and compression. COM paths must explicitly set root_is_com. Bone/hand animation is not implied. Keep all Empty scales at one. Never animate the same actor both through low-level object tracks and actor pose tracks.

The executable example `scripts/combat_text_example.py` writes a small TEXT package with a body trend, projectile and camera cut, then feeds the same builder. It verifies the interface, not autonomous dramatic fight quality. Replace its designed samples with the new approved sequence; it is not a mandatory scene or action template.

```powershell
python scripts/combat_sequence_package.py project/sequence.csp.json
blender --factory-startup -b -t 6 --python-exit-code 1 --python scripts/combat_sequence_builder.py -- project/sequence.csp.json --output project/build-v001 --render
```

Output directories must be new/empty. The build records package, builder and asset hashes, Blender version, evaluated world/screen samples, editable LAYOUT.blend and optional fresh PNG frames. Package Clean and Debug from those same frames and state revision. The existing packaging tools or a project wrapper may add overlays; they must not retime or silently rebuild independent animation. Scene assets can preserve an explicitly approved simple-body variant, without changing the default.

## Causality, proxies and camera

Treat an action as a dependency graph. One event owns release/contact; weapon tangent, receiver displacement/rotation, debris launch direction and impact expansion derive from that event. Energy/strength is a relative layout parameter, not a claim of physical simulation. Distinguish HIT, BLOCK, NEAR_MISS and ENVIRONMENT_HIT. A dodge cannot receive a fake hit flash, and debris cannot start before its cause unless pre-existing motion is documented. Follow-through and recovery can continue in a linked subsequent event; do not reset because a beat or shot changed.

Every proxy explicitly accounts for **Spawn → Build → Travel → Impact → Expansion → Dissipation**. Not all stages apply: a carried sword persists; a near miss has no impact; an impulse-born ring has no charging stage. Record NA and why. A persistent object may have multiple visible episodes with different event IDs; hide/show is not a new object or owner. When source ends during expansion, record CONTINUES_BEYOND_CLIP and uncertainty instead of inventing an in-shot fade or claiming dissipation was tested. Opaque geometry must not cover the initiating contact before it is legible.

Camera states are **Lead, Lag, Catch-up, Hold, Impact Reaction, Pull-back, Settle**. Use only motivated states. Specify their windows and transitions, target offsets, delay, and speed profile; a label alone does nothing. Hold can keep tension while a subject leaves center; Settle removes residual camera velocity after a response. Lead/Lag may affect framing without translating the camera. Match acceleration and response timing as well as lens and position; distinguish measured delays from qualitative classification. Never parent the camera mechanically to a character or add automatic shake at each hit.

Environment remains a scale/occlusion instrument: ground, walls, columns, trees, tabletop, doors/windows, steps and platforms explain support, parallax, height and travel. Use only the elements needed for the new scene. No fixture scenery is a default asset requirement.

## Eight acceptance gates and regression policy

| Gate | Evidence required |
|---|---|
| ACTION_READABILITY | Normal-speed muted Clean: attacker/receiver or obstacle, force direction, hit/near miss and next trend immediately readable |
| CUT_CONTINUITY | Every cut, at least before/after plus adjacent samples: event/owner/support/pose, weapon/projectile and VFX phase continuous; inherited momentum retained |
| TIMING_SPACING | Preparation, compression, acceleration, peak, contact, follow-through/recovery; identify undesired uniform movement or abrupt stops; preserve intended holds |
| CAMERA_CHOREOGRAPHY | Screen targets plus camera speed/acceleration/lag/catch-up/hold/settle; no unmotivated center lock, orbit or lens jump |
| VFX_LIFECYCLE | Per-object visibility and path, release/contact/expansion/end; valid NA, no accidental pops/residuals, no early key-action occlusion |
| RECOVERY | High-speed exit, impact, landing or recoil includes braking/absorption, body return and final settling; hidden/unobserved tail explicitly not certified |
| SILENT_REVIEW | Sound muted and shake zero, Box/environment/weapon/proxies/base camera alone convey the fight; captions and slow motion cannot rescue failure |
| FILE_RENDER_QA | Current hash-bound fresh renders, exact duration/frame count, no black tail, accidental freeze, repeated tail, cache reuse, missing frames or decorative obstruction |

Use PASS/FAIL/NOT_REVIEWED/NA per applicable event and gate. NA must identify a genuinely untested or inapplicable subcriterion; it cannot hide a visible failure. Report regression compatibility separately from source fidelity, user acceptance and new capability coverage.

The official fixtures and their case-only values are in [combat-regressions.md](combat-regressions.md). Rebuild BOTH through the candidate shared builder, compare evaluated actor/body/head/weapon/proxy/camera states over the full timeline, re-render full sequences and inspect movies/cut neighborhoods. A failure blocks merging the candidate change; fix and rerun affected checks, then ensure both fixture fingerprints still match the final candidate. Never approve a candidate merely because the baseline itself was previously accepted. Do not replace baseline files just to erase a regression.
