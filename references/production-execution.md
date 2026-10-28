# Existing execution paths — preserved 1.7.0

All commands and inline file paths are relative to the skill root. This is an execution reference, not an instruction to restart design for a revision or export. SYSTEM-V2 source authority and scoped output selection take precedence over historical defaults.

## Two layout modes and default characters

Read `references/layout-presentation-standard.md` and open its matching model image before creating characters. **NARRATIVE / 文戏** defaults to Image 2: sphere head, eye bar, cone nose, one body cuboid and chest-facing bar (5 meshes). **COMBAT_DYNAMIC / 打戏、运动戏** defaults to Image 1: sphere head, upper cuboid, single lower cuboid and cone nose (4 meshes). Neither default has permanent articulated limbs. COMBAT_DYNAMIC can add event-scoped ACTION_PROXY, geometric WEAPON_PROXY and VFX_MOTION_PROXY while keeping COMBAT_BOX_4 intact; these are internal expression layers, not a third layout mode. Explicit user references and approved project models override the defaults; complex articulated/Mixamo replacements still require explicit direction.

The primary product is a playable layout movie controlling space, trajectory, body/head trends, shot rhythm and cameras for downstream production, including Seedance. Fine hand/strike animation is downstream unless explicitly requested. The legacy default delivery is CLEAN MP4, DEBUG MP4, editable .blend and short review; source-matched benchmark tasks also deliver synchronized SOURCE/LAYOUT MP4. Explicit current output requests override this default; render only their selected combinations. Do not stop at analysis, poses, a character sheet or an unrendered scene. Asset-only and skill-edit tasks keep their requested scope.


## 1.9 explicit action expression

When authoring grounded speed changes or collision consequences, read [action expression](action-expression.md). `action_expression.py` compiles explicit route/time envelopes and directed receiver responses into existing Box pose tracks; `action_readability.py` measures both world and image motion. Reuse the CSP Builder and one global timeline. The new path does not change S008/S010, infer arbitrary ATTACK/BLOCK, compute physics, add limbs, or certify a complete fight. Fixed/curved routes, short acceleration, source/contact evidence, recoil/slide, staggered body response and integration limits are documented there. Existing-scene edits retain their established adapter and scoped revision protection.

## Choose the execution path

For **COMBAT_DYNAMIC**, both video-reference reconstruction and story/text design first produce the same [COMBAT SEQUENCE PACKAGE](../references/combat-sequence-package.md), then use `scripts/combat_sequence_builder.py` on one global timeline. The fresh primitive per-shot reset pipeline below remains available for its existing narrative scope; do not use its concatenation as combat continuity.

- **Fresh primitive previs:** use the generic manifest and commands below. Full builds reset the generated scene; each shot is built separately. Concatenation does not create cross-shot actor or prop continuity.
- **Approved existing scene / continuous sequence:** preserve the scene, named objects, identity colors, approved blocking and light direction. Work on a versioned copy; use project-specific animation scripts, one global timeline and camera cuts. Read `references/existing-scene-production.md`. Never feed an approved scene into the generic reset builder.
- Respect the requested MCP/UI method when specified. Otherwise headless `bpy` is appropriate for repeatable builds and rendering. If viewport rendering crashes, save/recover and try Solid display; do not change scene lighting merely to repair the viewport.


## Production decisions

1. Record source ownership by field and distinguish source facts, director-confirmed choices and estimates. New annotated scene views can revoke previous position inferences. Read `knowledge/input-source-authority.md`.
2. Register annotations against scene landmarks and prepare the full-story route/position package, not just an opening still. Include initial, transition, reveal, response, retreat and ending nodes as the story requires. Do not pre-position an offscreen group at its future destination. Obtain the confirmation described above before animation.
3. For relocation or climbing, validate the shared origin, branch routes, distances, speeds and concurrent travel window. Recalculate dependent times without rewriting unrelated shot durations. Read `references/blocking-routes-timing.md`.
4. Keep the supplied edit order, including inserts and non-monotonic shot numbers. Use one frame convention and update all downstream absolute times after a duration edit. Track offscreen actors and persistent props on the same timeline.
5. Apply the two default proxy presets above unless the user specifies another model. NARRATIVE retains its minimal construction. In COMBAT_DYNAMIC, use temporary ACTION_PROXY for strike direction/contact, simple WEAPON_PROXY and VFX_MOTION_PROXY for event semantics; do not replace the four-part body with a permanent limb rig. Keep the body contributing to the action and disclose the abstraction. Read `references/proxy-and-prop-performance.md`, `references/narrative-variants.md` and `references/combat-dynamic-motion.md`.
6. Inspect body/head transforms, support, interaction distances and prop states as well as roots and cameras; inspect local limbs only in an explicitly articulated variant. Read `references/motion-continuity.md` before baking or repairing motion.
7. Review shot samples and continuous clips before full rendering. Fix framing and occlusion using camera position, aim and lens first. Preserve approved light direction. Read `references/camera-light-review.md`.
8. Bind rendered frames and checks to the exact scene/dependency revision. Verify both clean and review movies. Report technical validity, file freshness, visual review and user acceptance separately. Read `references/render-delivery.md`.
9. For director-edited video, distinguish deletions, trims, speed changes, crop/reframing and rewritten actions. Map old and new time explicitly, then rebuild native animation. Read `references/director-reedit.md` and `references/case-study-revision.md`.


## Combat & Dynamic Motion (independent layout module)

Use this section when the requested layout contains a fight, chase, run, jump, fall, airborne exchange, weapon action, projectile, impact, or similarly large movement. It is a layout/previs method, not a final-animation or stunt-simulation system. It is intentionally independent from the ordinary narrative primitives so a normal dialogue layout keeps its existing behavior.

**Default priorities:** Action Readability > Screen-space Motion Trajectory > Timing/Spacing > Camera Choreography > Action/Reaction > Weight > Simplified Physical Plausibility > Detailed Human Motion. This prioritizes production effort, not permission to break continuity or invent source outcomes.

Read `references/combat-dynamic-motion.md` for this module's complete contract and use `templates/combat-performance-plan.json` for project planning. Use [CSP/1.0](../references/combat-sequence-package.md) as the common execution package and `scripts/combat_sequence_builder.py` as its shared assembly backend. The planning template alone does not generate animation.

### Dynamic-motion production sequence

1. **Source or text → ACTION_BEAT + RHYTHM_MAP → COMBAT SEQUENCE PACKAGE.** Inspect edit/action/space, separate recording pauses from performed holds, and map seconds to output frames. Plan each action's preparation, compression, acceleration, peak, hit/near miss, follow-through and recovery, plus whole-scene relaxation/tension/burst/pause/re-burst. Do this before continuous trajectories and Camera. No fixed scene, cast count, action order or duration is inherited from a study clip.
2. **Routes, environment and camera intent.** Design shared actor/COM and proxy paths from the beats, including offscreen motion and next-event momentum. Ground, walls, doorways, trees, platforms and foreground occlusion establish distance, height and speed. Add camera intent and reuse the existing full-story route/position confirmation; no extra approval gate is introduced.
3. **Four-part body plus semantic proxies.** Preserve COMBAT_BOX_4 (sphere head, upper/lower Box, cone nose), identity and mass differences. ACTION_PROXY is temporary Box/sphere strike or contact geometry; WEAPON_PROXY is simple weapon geometry; VFX_MOTION_PROXY uses spheres, rings, curves, planes or cube clusters to express timing, direction, speed, expansion and disappearance. Track event, owner/target, geometry, visible interval, coordinate space, release/contact and endpoint; hide inactive proxies in viewport and render. Never silently switch to ARTICULATED.
4. **Continuous body/action/reaction pass.** Sample root/lower/upper/head and proxy paths densely where direction or speed changes. Preserve support/COM, airborne events, ownership and cross-cut continuity. Let momentum carry into the next response and retain full recovery. A temporary arm proxy does not justify freezing the torso. Simplified mass/support and ballistic checks remain available without making fine biomechanics the first priority.
5. **Camera Choreography.** Choose event-driven Lead, Lag, Catch-up, Hold, Impact Reaction, Pull-back and Settle where source or approved design supports them. Define trigger, time window, anticipation/delay, speed, framing and exit state. Camera stays independent; avoid constant center locking or mechanical parenting. Evaluate actual animated bounds and cut-adjacent frames. Directed Impact Reaction is distinct from optional high-frequency Shake.
6. **ACTION_READABILITY_GATE + SILENT_REVIEW.** At design review, continuous preview and final delivery, judge whether who attacks whom, force direction, speed/weight contrast, contact/near miss and next movement are immediately readable. Mute sound and set Camera Shake to zero, retaining bodies, environment, semantic proxies and base Camera. Slow motion may diagnose but cannot rescue a normal-speed FAIL. Record PASS/FAIL/NOT_REVIEWED/NA with timecoded evidence; repair failed applicable criteria before calling the layout ready.
7. **Clean/debug delivery.** COMBAT_DYNAMIC CLEAN retains action-bearing temporary proxies, weapons, Projectile, Slash Arc, Impact, Shockwave, Explosion, dust and Debris; decorative complex FX and debug overlays remain excluded. DEBUG adds beat/rhythm, owner/lifecycle and root/COM/Camera/proxy paths. Call temporary endpoint paths ACTION_PROXY_PATH, not anatomical hand/foot paths. Export the same verified animation to both movies and include gate results, actual review scope and remaining uncertainty.

8. **Eight gates and regression.** Apply ACTION_READABILITY, CUT_CONTINUITY, TIMING_SPACING, CAMERA_CHOREOGRAPHY, VFX_LIFECYCLE, RECOVERY, SILENT_REVIEW and FILE_RENDER_QA with timecoded evidence. Preserve stable event/object IDs, per-shot screen-space targets and complete applicable proxy lifecycles. Rebuild both registered [combat regression fixtures](../references/combat-regressions.md) through the candidate builder before merging changes. Numerical compatibility, visual/source fidelity and untested capabilities are distinct conclusions.

### Current capability status

CSP/1.0 adds executable shared assembly, structural validation, dense evaluated world/screen evidence and hash-bound regression comparison. The two fixture rebuilds test preservation of approved choreography, not general automatic video-to-3D solving or mature autonomous text-to-fight design. See the regression record for coverage and limitations.

The reusable baseline now covers dynamic beat tables, low-model direction-first proxies, cast proportion differences, center-of-mass/support annotations, ballistic layout approximations, persistent weapon/projectile states, continuous pose channels, contact/recovery checks, and cut-aware camera review. These are layout capabilities, not a claim of final animation quality.

The user-approved presentation baseline is now documented with two local example movies and the Box reference in `references/layout-presentation-standard.md`. Use their body-trend abstraction, trajectory readability and camera/space relationships as the baseline, upgraded by the 2026-09-16 study and user-directed semantic proxy, rhythm and silent-readability contract. NARRATIVE and the proven four-part body builder remain unchanged. Approval of presentation is not certification of source fidelity or mature biomechanics. Assess camera match, tempo, weight and recovery per new case, report actual limitations, and continue improving them without substituting shake or technical PASS labels.


## Generic primitive pipeline

1. Complete the confirmed full-story blocking package, then normalize the generic manifest with `scripts/shot_builder.py`.
2. Build environment primitives and proxy rigs with `scene_builder.py` and `character_proxy.py`.
3. Compile action beats into continuous sampled states with `motion_builder.py`.
4. Build a camera path within each shot with `camera_builder.py`; assemble separate shots with `sequence_builder.py`. Explicitly author inherited boundary states when continuity is required.
5. Run Blender headless through `adapters/blender_headless_adapter.py`. The runtime uses `bpy` for scene generation and animation; no GUI add-on is required.
6. Package clean and debug MP4s, a contact sheet, a technical check, and a director-facing README with `package_review.py`.


## Commands

From this skill directory:

The production commands below follow the confirmed diagram stage. They are low-level utilities, not an automatic substitute for user confirmation.

```powershell
python scripts/build_previs.py path/to/project-manifest.json --output out --mode FULL_BUILD
python scripts/build_previs.py path/to/project-manifest.json --output out --mode SHOT_BUILD --shot SH13-26
python scripts/build_previs.py path/to/project-manifest.json --output out --mode OVERRIDE_PATCH --shot SH13-26 --overrides path/to/director-overrides.json
```

Use `--build-only` for a `.blend` without MP4 packaging, `--force` to bypass the fingerprint cache, and `--blender`/`--ffmpeg` when executables are not on PATH. Incremental modes are `CAMERA_ONLY`, `BLOCKING_ONLY`, `MOTION_ONLY`, `OVERRIDE_PATCH`, and `RENDER_ONLY`; they reuse the existing V1 `.blend` when present.

The generic cache keys version and normalized plans; it is not sufficient evidence that videos match edited scripts or a manually saved scene. After those edits use `--force`, then verify delivery independently. A `.blend`-only build is not a new movie delivery.

Existing-scene helpers (templates are illustrative and must be filled with actual paths/object names):

```powershell
python scripts/plan_sequence.py sequence-plan.json --output timeline.json
blender -b approved-animated-copy.blend --python-exit-code 1 --python scripts/render_existing.py -- --job render-job.json
python scripts/verify_delivery.py delivery-spec.json --output delivery-check.json --ffmpeg ffmpeg --ffprobe ffprobe
```

These helpers compile timing, render an already animated scene and verify media. They do not generate bespoke character performances, infer camera objects, or transfer the MountainCase scene automatically. See `USER-MANUAL.zh-CN.md` and `templates/production-context.json`.


## 1.8 explicit camera execution

For an existing shared scene and a complete fixed-lens DIRECTOR_PLAN/1, use [the new camera-only adapter](local-upgrade-runtime.md). It preserves the input file and creates distinct shot cameras/markers in a new saved output. For actor animation, unsupported rigs/zoom or partial production adapters, keep the established execution path and apply equivalent evaluated-camera, cut and encoded-video checks. Do not route a confirmed scene into a reset builder.
