# Production task router

Status: INTERFACE_ONLY production orchestration; Python routing/validation implemented, no Blender executor dispatch. Use `production_v2.route(task)` or CLI `route`. Inputs are explicit task facts, not a natural-language classifier. A compound task has exactly one named primary owner in its route set; secondary routes supply only their requested scope.

| Route | Primary responsibility | Read / action |
|---|---|---|
| DESIGN_FROM_STORY | Autonomous proposal within granted design scope | Scene Director → route diagrams → confirmed blocking → existing execution |
| EXECUTE_CONFIRMED_STORYBOARD | Preserve approved shots, composition and intent | Import authority, resolve missing execution parameters; no re-edit |
| REVISE_EXISTING_LAYOUT | Local feedback and dependency audit | Revision record → guarded S2 patch where applicable → affected validation |
| BUILD_SCENE | Shootable geometry | Select REFERENCE_MATCH / FULL_SHOOTABLE_SPACE / REVERSE_COVERAGE / STRUCTURAL_SIMPLIFICATION / LOCAL_REVISION |
| LIGHTING_PREVIS | Context, lamps and lighting validation | Existing plan/test mechanism, protect Camera/Motion/Blocking |
| OUTPUT_PACKAGE | Version-bound rendering/export | Existing saved-scene renderer and delivery verification |
| DOWNSTREAM_PREP | Package control/reference data after explicit final approval AND delivery of that exact final layout | Read downstream-handoff.md; do not create cards or compile populated handoff contracts before both conditions hold; no AI video invocation |

No sidecar: `route(None)` returns LEGACY with no additional confirmation. Empty or malformed opted-in contracts are errors, not fallback. Do not force old projects to migrate. No Physical/Lighting/VFX input is required for ordinary grey layout. A lighting request adds only the existing scoped Lighting gate. Confirmed storyboard reconstruction requires explicit redesign authority before shot merge/split; a version-specific prior approval remains valid.

Scene construction prioritizes topology, proportions, height, entrances, paths, occlusion, support, reverse coverage and camera-accessible volume. A reference-matched facade alone does not establish a full shootable room. Structural simplification preserves approved landmarks and blocking. Scope selection is currently author-directed; it does not dispatch a new mesh generator.

1.8.1 reading routes: DESIGN_FROM_STORY uses [cinematography for layout](cinematography-for-layout.md); EXECUTE_CONFIRMED_STORYBOARD uses only the portions needed to realize approved intent; REVISE_EXISTING_LAYOUT uses it for the diagnosed camera/directing issue. OUTPUT_PACKAGE uses [adaptive review](adaptive-layout-review.md) without reopening direction. BUILD_SCENE may use its character/space guidance; LIGHTING_PREVIS retains its existing scope and approvals. No new schema fields or mandatory worksheets are introduced.
