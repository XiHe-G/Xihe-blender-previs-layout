# Identity Proxy V2 and simple hand proxy

Status: INTERFACE_ONLY; schema/validator only. No new mesh generator. CORE_PROXY remains NARRATIVE_BOX_5 or COMBAT_BOX_4. Add IDENTITY_ANCHORS derived from character sheet and height chart, with source provenance and uncertainty. Do not replace the accepted core or silently switch to articulated rigs.

Identity combines color, relative height, head width/height and head/body ratio, shoulder/torso width, body volume, head silhouette and signature anchors (hair/ear/horn/hat/tail/prop/shoulder/back). Color alone is insufficient. Values are authored normalized proportions, not automatic image measurements. Native readability and cross-shot recognition require review at intended output size.

Optional SIMPLE_HAND_PROXY is a sphere or small box with LEFT/RIGHT, GRIP/CONTACT/POINT, a referenced prop grip/contact target and simple anchor position. It communicates what is held, touched or pointed at. It does not create fingers, palm anatomy or complex IK. Prop attachment semantics remain separate from geometry.

V2 defaults to no full legs. Movement uses Root Translation + Body Trend + Support State. The validator rejects full_legs=true in this contract. Explicit legacy articulated variants retain their existing behavior (including existing QUADRUPED legacy defaults); this opt-in contract does not migrate or rewrite them. Leg research requires separately scoped evidence of director/downstream benefit.
