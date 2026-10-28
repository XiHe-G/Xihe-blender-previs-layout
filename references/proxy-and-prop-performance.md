# Proxy identity and story performance

Follow explicit references first; otherwise use the two defaults in `layout-presentation-standard.md`. The narrative five-piece proxy uses a sphere head, cone nose, eye bar, body block and chest-facing marker. Keep a foot-level root, head control, consistent forward axis, distinct color ID and readable silhouette. Deliver a name/color/relative-height legend and distinguish scene-adapted height from source-canonical height. Do not force the generic articulated rig when no model is specified; the default is the mode-specific box model.

Prioritize main story actors. NARRATIVE keeps its existing minimal-parts policy. COMBAT_DYNAMIC may add a temporary Box arm/kick direction or sphere fist/contact as ACTION_PROXY, plus simple WEAPON_PROXY and VFX_MOTION_PROXY, following `combat-dynamic-motion.md`. This does not add a permanent limb rig or override COMBAT_BOX_4. Preserve body support, mass trend, persistent prop ownership and visible action/reaction; detailed articulated models still require explicit direction.

Use event/state tables for persistent props:
- Telescope: holder A → overlap/contact → holder B; preserve world transform during ownership changes.
- Projectile: held → release → travel → freeze → return/contact. Keep the same object across cuts.
- Encasing ball: enclosing → rolling/falling → settled → head emergence; maintain head/ball/ground relationships.
- Touch/command: approach → contact → recipient response → next gesture → effect response. A shoulder stop and later finger command should not all fire on one frame unless the story calls for it.

For each event record object IDs, owner, frame interval, attachment space, release transform, target and endpoint state. Inspect before/contact/after frames and a continuous short clip. Coordinates alone do not prove a hand touches a shoulder or a prop transfer reads clearly.
