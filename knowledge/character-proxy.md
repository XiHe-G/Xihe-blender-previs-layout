# Character Proxy

Read `../references/layout-presentation-standard.md` and its model images. Explicit references/approved project models win; otherwise NARRATIVE uses Image 2 / NARRATIVE_BOX_5 and COMBAT_DYNAMIC uses Image 1 / COMBAT_BOX_4. Neither default has permanent articulated limbs. COMBAT_DYNAMIC additionally supports temporary ACTION_PROXY, geometric WEAPON_PROXY and VFX_MOTION_PROXY as event objects; they are not new character presets or a third layout mode. The five-piece narrative model has ONE body cuboid plus head, eye bar, cone nose and chest marker. The four-piece combat model has upper/lower cuboids, head and cone nose. Do not confuse the two constructions.

Use a stable CHAR_<id> root, display name, color, scene-adapted height, width/depth proportions and documented forward axis. Separate body/head controls with unscaled Empty parents. Direction markers follow the appropriate body/head controller. Size, shoulder width and upper/lower proportions distinguish light/agile from heavy/power.

The generic runtime selects box presets by layout_mode and proxy_style; ARTICULATED is an explicit override. Quadruped proxy_type is an explicit nonhuman topology exception and retains the existing quadruped rig in AUTO; an explicit box preset can override it. Existing scene rigs are preserved, not reset through the generic builder. A model being low-poly does not authorize detailed fight animation or certify biomechanical quality.

For semantic proxy lifecycles, beat/rhythm design, camera logic and silent readability, read `../references/combat-dynamic-motion.md`. Keep the body meshes and BoxRig interface unchanged.
