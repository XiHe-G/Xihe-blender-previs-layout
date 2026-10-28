# Scene Director and narrative directing contract

Status: INTERFACE_ONLY. Formal decision contract and schema exist; no autonomous director runtime, shot-count optimizer or general prose-to-AG compiler is implemented.

Scene Director output is SCENE_OBJECTIVE, CHARACTER_OBJECTIVES, BEAT_MAP, BLOCKING_PLAN, SHOT_FUNCTION_MAP, RHYTHM_MAP and CONTINUITY_HANDOFF. `scene-director-plan` references existing authoring times instead of creating timings independently. Each beat names what happens, each participant's objective, what is perceived, what changes, who has initiative and the result. Every shot-function record states purpose, viewer priority, new information, relationship change, motivation for cutting in and reason to end.

Narrative behavior uses Objective → Trigger → Perception → Reaction → Decision → Action → Listener/Opponent feedback → Relation change → Endpoint. Do not replace a discovery with an unmotivated walk. Dialogue duration is not shot duration: allow reaction holds, listener shots, decision pauses and silence beats. Their timing references remain in the existing sequence/CSP source. Merging and splitting are proposals only under design permission; confirmed storyboards must be executed as approved unless current scoped direction changes them.

Choose a story-motivated motion intent from SLOW / WALK / FAST_WALK / RUN / SPRINT / BURST / FLY / CHASE / RETREAT / LUNGE / DODGE. No default WALK for all beats. Physical profile then informs author-selected speed/acceleration/stopping/turn response. That mapping remains NOT_IMPLEMENTED_RUNTIME; explicit Sprint008 parameters use the existing path.

Whole-scene objectives precede isolated pretty shots. Training should verify whether reaction, decision and resulting spatial relationship remain legible across the actual edit. A complete form or passing validator does not establish directing quality.

For story-owned viewpoint, audience knowledge/reveal timing, in-frame staging versus coverage, lens/distance/depth choices and motivated motion, read [cinematography for layout](cinematography-for-layout.md). Keep those decisions in existing narrative notes and shot-function fields; optional [visual intent notes](../templates/visual-intent-note.md) are not a new schema. Use reference images by named properties, then test the actual action and edit. These are authoring methods, not a new automatic director or focus controller.
