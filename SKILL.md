---
name: blender-previs-layout
description: Create and revise narrative and dynamic-motion Blender layout/previs from scripts, shot tables, optional storyboards, character and scene references, or existing scenes. Route scene building, confirmed-shot execution, local revision, Lighting Previs and delivery without restarting direction. Produce continuous reviewable layout, not final character animation; reference video is optional for study or reconstruction.
---

# Blender Previs Layout · 1.9.0

Local release: **1.9.0-ACTION-EXPRESSION** (2026-10-28). Retains the 1.8.1 photography/review upgrade and adds an opt-in [action expression runtime](references/action-expression.md) for explicit grounded routes, short speed envelopes, directed recoil/slide and staggered Box body response. This path is EXPERIMENTAL with native micro-case evidence, not automatic fight choreography or a physics solver; old runtime kernels and acceptance gates remain unchanged. Read [director production workflow](references/director-production-workflow.md) for story-first authoring, [cinematography for layout](references/cinematography-for-layout.md) for visual decisions, and [adaptive review](references/adaptive-layout-review.md) when preparing shot tables or review outputs. Existing [camera/cut execution](references/camera-cut-execution.md), [revision loop](references/revision-and-review-loop.md) and [runtime commands](references/local-upgrade-runtime.md) remain the execution paths. [Capability status](CAPABILITY-MATRIX.md) retains historical limits and accepted kernels.

## Goal and abstraction

Script / text shots + optional storyboard, character references/height chart, scene references, director requirements or Blender project → Scene/Sequence analysis → shootable space → Lighting Context when requested → identity/physical profiles → whole-scene blocking → shots/Camera → motion/action/props/combat/narrative → optional VFX → Lighting validation → continuous layout → scene validation → local revision → versioned delivery → AI-readable downstream reference. Video is optional study/reconstruction/benchmark input, never a production prerequisite.

Layout controls world/screen position, facing/gaze, routes, relative speed and acceleration, body/action trend, takeoff/landing, attack/block/contact intent, support/momentum/prop relationships, VFX scope/timing, Camera, spatial lighting, beats and inherited states. It does not default to gait, detailed arms/legs/fingers, complex IK, mocap, final VFX/lighting or character animation. Keep NARRATIVE_BOX_5 / COMBAT_BOX_4; V2 identity anchors/simple hands are optional interfaces, no default full legs. Read the presentation standard and matching model image before creating characters.

## Task router

Choose explicit primary owner and only needed companion routes. Director reasoning and evidence rules apply to all production. The new camera adapter is used only when its explicit contract fits; otherwise use the established project adapter and equivalent checks. No mandatory Physical/Lighting/VFX schema migration.

| Route | Scope |
|---|---|
| DESIGN_FROM_STORY | Propose directing, full-story routes and shots |
| EXECUTE_CONFIRMED_STORYBOARD | Execute approved intent; no unauthorized restructuring |
| REVISE_EXISTING_LAYOUT | Local changes plus transitive dependency audit |
| BUILD_SCENE | Reference matching / shootable space / reverse coverage / simplification / local edit |
| LIGHTING_PREVIS | Context, authorized lamps and validation |
| OUTPUT_PACKAGE | Requested versions, shots and segments |
| DOWNSTREAM_PREP | AI control/reference package only after explicit final approval and delivery of that exact final layout |

Read [routing](references/production-routing.md). Export, local edit and confirmed-shot execution do not automatically restart full directing.

## Production workflow

1. Establish field-level authority, scope, existing approvals and source versions. Register stable scene/landmark/character/prop IDs. Preserve offscreen actors.
2. For newly designed layout: scene objectives/beats → full-character routes and key-node diagrams, including endings/entrances/exits/heights → authorization check → execution. Honor a project-specific diagram-first review requirement; explicit autonomous candidate authoring may proceed within unlocked choices. Combat adds ACTION_BEAT/RHYTHM_MAP before routes and cameras.
   Define whose experience the scene follows and when the audience should learn each key fact. Translate the emotional turn into visible blocking, framing or attention changes. Compare in-frame staging, cuts and camera movement only where a real choice matters; no fixed coverage pattern or mandatory new form.
3. Establish shootable space and optional Lighting Context before Camera design. Use semantic Camera/composition constraints and explicit motion intent. Automatic physical-profile-to-animation lowering remains unimplemented. For authored grounded motion, use [action expression](references/action-expression.md) when its route/time/response contract fits; otherwise use accepted explicit primitives or the project adapter.
4. Execute through [existing production paths](references/production-execution.md). Combat uses AG/CSP and one global timeline. Generic primitive shots reset separately and do not create cross-cut continuity by concatenation. Preserve approved existing scenes on versioned copies; never send them to a reset builder.
5. For fast motion or weak impact feedback, resolve route distance, time, body scale, phase spacing, source/receiver consequences and body-channel offsets before adding effects. Measure world motion and image context together; a centered tracking shot can convey speed through environment flow. Use normal-speed fixed/context views and the actual shot where needed, without adding a mandatory delivery format.
   Preview continuous clips and cut-adjacent states. Preserve existing motion/contact/readability gates. Lighting validates after layout, without rewriting Camera/Motion/Blocking. Technical, native, visual and director judgments are separate.
   Judge camera distance, perspective, lens, aspect ratio and needed depth/focus together. Check attention, reveal timing and reaction at playback speed; a cinematic technique or parameter is not proof of its intended emotional effect.
6. Revisions record source version, allowed/protected channels and dependency closure; use guarded S2 merge for registered LOCKED channels. Check affected handoffs and protected channels before versioned output.

## Authority and confirmation

Read [field authority](knowledge/input-source-authority.md). Script owns story/action, confirmed storyboard Camera/composition, floor/top view topology, scene reference appearance/context, character sheet identity/proportions and height chart relative heights. Current explicit user direction overrides only its addressed scope. An environment image never silently overrides approved blocking/Camera. Record unresolved conflicts and estimates.

Keep the whole-story route/position review when the active project requests it. Explicit autonomous directing authorizes candidate choices within scope; it does not fabricate approval of those choices. Ask only for material unresolved creative/source conflicts, locked changes or missing required authorization, after making the choices concrete. Reuse all prior scoped approvals and continue independent authorized work. General silence, a still or technical PASS does not approve new protected routes. Pure output/caption changes do not reopen blocking.

When Lighting is requested, preserve plan confirmation and distinct test review. Explicit instruction to light directly from a named reference authorizes that scope. No Lighting request means no extra Lighting gate. Schema authorization records must match actual user evidence. Confirmed storyboard merge/split requires design permission.

## Stop and output rules

Stop dependent work for unresolved major directing/authority choices, unavailable evidence required for acceptance, unsupported lowering or protected-channel conflicts; continue independent authorized work. Do not silently substitute unsupported actions or claim unknown evidence as PASS. AUTODEV follows its scoped checkpoint/repair policy and must not rewrite stable kernels to satisfy an interface.

Deliver the requested playable layout and editable project, not merely a plan, unless scope is asset/interface/analysis only. Honor requested output combinations and established project defaults. For a new project without an output convention, prefer CLEAN, DIRECTOR_REVIEW, editable project/assets and concise shot/revision notes; DEBUG is for needed diagnostics. Review format is adaptable: preserve shot semantics, complete picture, synchronized timing and readable text, without fixing column count, pixel layout, fps or aspect ratio. Use common source/revision fingerprints and existing media freshness checks; a manifest compiler only checks declared bindings and hashes. Downstream may add detail but cannot freely change key Camera, Blocking, Screen Direction, Cut or Beat result. No AI video execution is implied.

## Final layout → aigc-video handoff gate

用户明确确认当前版本定稿，并且已交付该版本最终修改好的 layout 后，才生成给 `aigc-video` 的交接卡。顺序固定为：现有制作／审阅／修改流程 → 用户明确确认具体版本定稿 → 交付最终可播放 layout 和可编辑 .blend → 核验同版 CLEAN 参考视频 → 生成并交付交接卡。可在同一轮按此顺序完成，无需重复询问已取得的同版确认。

“继续”“先导出看看”、分镜／路线确认、技术 PASS、自主制作授权和沉默都不是最终定稿确认。定稿前可以按原流程输出审阅版与技术资料，但不得生成交接卡、填好的 AI_VIDEO_HANDOFF 或调用交接编译器。OUTPUT_PACKAGE 不自动等于 DOWNSTREAM_PREP；用户提前索要交接时说明还缺哪项定稿或最终交付证据，继续已授权的 layout 工作。

Read [AI handoff](references/downstream-handoff.md) for the gated procedure and [card template](templates/aigc-video-handoff-card.md) only when the gate is satisfied. Bind approval, final delivery and handoff to the same version and shot scope. A later layout change invalidates the old approval/handoff for the new version; preserve historical deliveries, finish the existing revision loop, obtain final confirmation for the changed version and deliver it before regenerating its card. This is an agent workflow gate; existing low-level compilers do not establish user approval.

## References — load by active task

- [Story-to-photography decisions](references/cinematography-for-layout.md) for new direction or camera diagnosis; optional [visual intent note](templates/visual-intent-note.md). Confirmed shots retain their approved intent.
- [Adaptive shot tables and review](references/adaptive-layout-review.md) for production/review/delivery; optional [review working sheet](templates/layout-review-plan.md). [Source study](references/source-study-20261028.md) records provenance and exclusions; do not load raw books or all references by default.
- [Execution and preserved commands](references/production-execution.md), [presentation](references/layout-presentation-standard.md), [existing scenes](references/existing-scene-production.md), [blocking confirmation](references/story-blocking-confirmation.md).
- [Scene state](references/production-scene-state.md), [revisions](references/production-revision.md), [Scene/Narrative Director](references/scene-director.md).
- [Action expression / speed / impact feedback](references/action-expression.md) for COMBAT_DYNAMIC motion design or weak speed/weight diagnosis; executable [travel](templates/action-expression-travel.json) and [response](templates/action-expression-impact.json) examples are editable calibration cases, not genre presets.
- [Camera semantics and composition](references/camera-semantic-compiler.md), [Identity V2 / simple hands](references/identity-proxy-v2.md), [physical / locomotion / impact](references/physical-behavior-profile.md), [props](references/prop-interaction-profile.md).
- [Lighting Context](references/lighting-context.md), [existing Lighting guard](references/LIGHTING-COMPATIBILITY.md), [VFX](references/vfx-previs.md).
- [Output/versioning](references/output-versioning.md), [AI handoff](references/downstream-handoff.md), [scene Plan-vs-Actual interface](references/production-plan-actual.md).
- [Contract API and examples](references/production-contract-api.md), [accepted modules and research index](references/research-index.md). Historical Sprints are loaded only when relevant.

- [Local production lessons](references/production-lessons-20260915-20261011.md), [selective open-source research](references/open-source-study-20261011.md).
