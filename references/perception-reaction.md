# Perception / Reaction causal binding — LIMITED

Use the opt-in compilation owner `scripts/perception_reaction.py` plus `perception_response_lowering.py` when an existing response must depend on a perceivable world event. LOOK is orientation; it does not imply NOTICE. NOTICE is an authored recognition rule; it does not automatically imply movement.

`PERCEPTION-REACTION/1.0` is a compilation binding, not a seventh AG collection or new animation timeline. Required: binding_id, actor, target, source_event {event_id,frame}, perception_event ID, fps, global frame window, trigger, reaction_delay_frames, response_steps [{event_id,kind,duration_frames}], provenance. Optional execution_end_frame, immediate_reaction_authorized, locked_channels and measurement_onset_allowance_frames. Reference IDs must stay consistent in resolution, native evidence and response execution. On an existing locked project, use existing S2 ownership/override checks; this fresh-output interface must not bypass them.

Triggers:
- EXPLICIT_AUTHOR_TRIGGER: frame and author_reason required; frame must follow source. This proves author cue authority, not visual detection.
- SPATIAL_VISUAL_TRIGGER: max_distance and half_cone_deg against evaluated world position/local +Y facing; optional min_target_speed. A declared unoccluded_context is required. Camera visibility is NOT actor perception. Required actor LOS, missing entity/trajectory, unknown geometry or missing samples yield NOT_REVIEWED. This mode is a world-proxy estimate, not cognitive/occlusion simulation.

No implicit delay defaults. Delay is authored integer frames or explicitly authorized immediate reaction; caller must record profile/derivation if used. Detection scans after source for the first eligible global sample. Missing earlier samples prevent claiming a first detection. Non-triggering conditions produce UNTRIGGERED and no program. Out-of-window response and locks block generation.

Source < perception <= reaction < first response, except an explicitly authorized immediate response can equal reaction. Response steps inherit each previous endpoint; references and timing both validate. Response templates call existing S51 MOVE/RECOVERY/ORIENT; no new motion algorithm. A constant pre-response MOVE can be truncated at the detected response boundary with inherited position/velocity. Other truncations are not supported.

Evidence stages: compiled resolution PLANNED; real command EXECUTED; saved/reopened native samples OBSERVED; recomputed trigger plus independently measured response onset and dependency validation VERIFIED. Registered event windows never count as observed changes. Event metadata cannot prove subjective noticing; VERIFIED applies to this bounded declared model.

Project to existing CSP action_beats and causal_links through attach_csp. No CSP schema or Combat CSP Builder change; the opt-in legacy Narrative adapter is described below. AG sources/constraints/dependencies can supply the binding; automatic natural-language extraction is not provided. Legacy Narrative optionally accepts CAUSAL-LOCATION/1.0 on a movement action, with dense S51 samples and SHA. Untagged actions retain the old path. Endpoint/coverage and C0/C1 must pass before publishing; the adapter is not an arbitrary raw animation importer.

Always re-evaluate native geometry. Native onset has a declared small measurement allowance because sampled zero-derivative starts may remain below numeric precision for several frames; this does not shorten the authored delay or authorize early response. Failed source/trigger/identity/delay/dependency/onset validation cannot PASS. A successful causal gate never approves prop control, contact, support, momentum transfer, director quality or downstream video.


Sprint002 evidence: two micro prototypes plus two baseline reruns, 333 tests and frozen CDR-003/004 rebuild/reopen equality. Accepted only as LIMITED offline causal compilation. The runtime still executes ordinary baked CSP; this is not real-time cognition or a general reactive simulation.

State handoff follows channel ownership: orientation-only output cannot overwrite a translation writer's velocity. Native position imports must retain existing proxy grounding transforms; do not replace an evaluated target with authored initial coordinates. `native_position_track` imports the measured root and reuses the common timebase/derivative helper.

`verify_response_stationarity` distinguishes pre-response root stationarity from the motion anchor of a declared grounded proxy during an authorized turn. Anchor = measured root XY + evaluated mesh-bottom Z; raw root drift remains in the report. Missing anchor evidence is NOT_REVIEWED. This is a measurement convention, not a new support runtime or proof of contact physics. Never use it for airborne motion.

Use the common `lower(...)` API with evaluated pre-response tracks and explicit response templates; inspect `status` before using the returned program. Only READY emits a program. Compile fragments into the existing CSP and remeasure after Builder/save/reopen. Legacy Narrative uses the opt-in location adapter; it does not gain a new full narrative CSP implementation. No existing AG, CSP, Camera or motion-kernel schema/contract was replaced.
