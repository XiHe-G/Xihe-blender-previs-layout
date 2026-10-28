# Camera, light and review

For every shot review start/middle/end views in narrative order. Then inspect continuous clips for close interactions, route transitions, fast gestures and cuts. Check focal actor visibility, face/nose/eye direction, headroom, body crop, screen direction, prop silhouette and foreground/background separation.

An observation POV must originate from the approved observer area with plausible eye height and sightline. A generic visibility/raycast pass can succeed at the wrong place. Validate it against the approved map.

For near foreground occlusion, try camera position/height, aim and lens before near clipping. A large clip_start can erase needed geometry or performers; only use it as a shot-specific fallback, record the reason and inspect all frames of that camera. Do not adopt MountainCase's 610 mm lens or 3.4 m clipping distance as defaults.

Preserve the approved sun direction and basic lit/shadowed planes. Modest fill can make colored block actors readable without replacing the source light. Benchmark a few representative frames with the installed render engines; choose settings based on measured time and adequate readability. A case's Eevee timing does not guarantee another scene's speed.

Keep labels off critical action. Size legends for the actual cast; use multiple columns/pages when eleven actors do not fit a short fixed strip. Clean and review versions share imagery and timing. Dialogue captions are prompts, not synthesized speech; describe the actual audio track.
