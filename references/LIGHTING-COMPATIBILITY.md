# Lighting compatibility guard (S008 companion validation)

Opt-in read-only diagnostic; not Lighting Previs design or construction. No sidecar/lighting requirement in a grayscale scene: NOT_APPLICABLE and continue the existing pipeline without a confirmation gate. An explicit lighting request with missing native/authority evidence: NOT_REVIEWED, never a fabricated PASS.

`lighting_compatibility.evaluate(before, after, context)` compares full sampled global-frame light matrices/parameters, world/material nodes, fixed exposure/color management, cameras, non-light transforms and evaluated geometry. Native fixture adapter lives in the S008 audit package; it is not a universal scene adapter. Pure comparison code cannot authenticate user approval: `plan_approval_ref` must point to an actual scoped confirmation record supplied by the caller.

Changes affecting motion/geometry conservatively invalidate prior lighting test review: LIGHTING_REVIEW_INVALIDATED + REVIEW_REQUIRED with frames, subjects, lamps and regions when supplied. A confirmed unchanged plan can remain valid when only timing changes; old Test Approval cannot carry over automatically. Protected light/Camera/exposure changes or evidenced intent conflicts require plan review. Missing fields or time coverage yield NOT_REVIEWED. No lighting, motion, door or Camera writes are permitted by this interface.

Where Lighting Previs is requested, retain the six-plan mechanism: Lighting Intent, Key Light, Fill / Practical Lights, Spatial Lighting, Character Lighting, Dynamic Lighting. Actual user confirmation of that plan version precedes formal lighting construction. Existing confirmed unchanged scope is reused without asking again. Test confirmation is distinct. No confirmation is inferred from documents, silence or numeric validation.

Scene-native compatibility evidence does not prove artistic lighting/readability, rays do not measure final radiometry, and preserved light state does not prove every possible Dynamic Lighting intent. Ray witnesses under fixed lights/world/materials can support geometric causality, with limits recorded. Project Door/Night examples and general Lighting module maturity remain separate.

Motion intensity must come from Actor Root displacement, not flicker, exposure animation, light switching or global color changes. Grey Workbench preview does not claim Lighting Previs. This guard adds no automatic lamps, Camera Intelligence, rigid-body system or downstream video generation.


SYSTEM-V2 clarification: an actual scoped instruction to light directly from a named reference is direct authorization for that construction scope; preserve the source message/reference and do not ask again. This does not fabricate test approval. Context planning/navigation is in lighting-context.md; this guard remains EXPERIMENTAL and read-only.
