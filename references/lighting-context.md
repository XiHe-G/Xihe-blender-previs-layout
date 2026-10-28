# Lighting architecture: preflight context + post-layout validation

New Context status: INTERFACE_ONLY. Existing Lighting Compatibility Guard stays EXPERIMENTAL; see LIGHTING-COMPATIBILITY.md for its sole runtime authority. Do not duplicate or replace that comparator.

After scene space exists and before formal Camera design, when Lighting is requested, establish Lighting Intent, Key Direction, Ambient, Practical Lights, Color Relationship, Intensity Relationship, Spatial Light Zones, Character Light Expectation and Dynamic Lighting Events. Propose these from script/scene reference/director requirements; record inferred choices explicitly. Ordinary grey tasks without Lighting continue unchanged, no extra gate.

For creative choices, use [cinematography for layout](cinematography-for-layout.md): define what the viewer should read, how motivated light and foreground/subject/background relationships support it, and which properties a reference contributes. Identity colors and emotional palette serve different functions. Genre conventions, warm/cool associations and high/low-key styles are options, not automatic mappings. Validate light-zone changes and the sequence, not only attractive stills; a lighting ratio requires an explicit measurement definition. This guidance adds no new Lighting executor or approval stage.

Actual lamp construction retains existing plan confirmation and distinct test confirmation. The user's explicit 'directly light according to this reference' is scoped DIRECT_REFERENCE authorization for that task; record actual message/reference/scope instead of asking again. PLAN_APPROVAL records actual approved version. Neither a schema enum nor an arbitrary source string proves user approval; match trusted conversation evidence. Existing unchanged approval persists.

After layout validate world-fixed lights, no camera-carried lamps, real door/window occlusion, actors crossing light zones, changed lit side on turns, multi-source relationships, fixed exposure/color management and cross-shot continuity. Record frame/source evidence, not just planned labels. Geometry/motion changes invalidate affected lighting test evidence under the existing guard.

Lighting cannot change Camera/Motion/Blocking outside a formal authorized revision. NEUTRAL_LIGHTING_LAYOUT and identity-color presentation are separate requested variants. VFX light events bind explicitly; a low-poly flame cannot serve as evidence of character illumination. Scene reference may suggest light context but cannot override approved camera/blocking.
