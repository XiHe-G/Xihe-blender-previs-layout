# Existing-scene production

Use this path when the user supplies a Blender scene or approves a previous blocking version.

## Scope and baseline

Record the requested stage, source file hash, scene name, shot range, fps, world scale, axes, character forward direction and primary actors in production-context.json. Save production to a new .blend; preserve earlier deliverables. Retain cameras/scenes required by the user. Reopen the saved file in a separate Blender process to verify they actually persisted; use persistent datablock users when needed.

For asset-only requests, deliver the proxy library/individual assets and legend. For analysis-only requests, deliver source conflicts and story beats. Before full animation, prepare whole-story routes and key-node position diagrams for every character and obtain user confirmation of that version. The checkpoint is required by the user in V1.2; see story-blocking-confirmation.md. Existing approval of the same complete plan persists, but approval of only opening positions does not cover unplanned retreats or endings.

## Architecture

Use project-specific scene preparation, actor/prop motion, camera and rendering modules as needed. A single scene contains the continuous story timeline. Actor roots, limbs and props keep state while offscreen; camera cuts change visibility, not world state. Camera markers or explicit camera names map each edit segment to an existing camera.

The generic build_previs.py resets generated scenes and normalizes each shot independently. Do not use it to continue an approved .blend. The new render_existing.py is a renderer only: supply a scene with animation already authored. It never saves the source scene.

## Revision handling

Record feedback verbatim or faithfully paraphrased, its marked image/source, old assumption, replacement and affected scope. Invalidate dependent route, timing, camera, actor/prop animation, subtitle and render outputs. Preserve approved fields outside that dependency set. A blocking-only revision may need camera and timing changes without rebuilding character assets.

World conversion is project-specific: document source units, handedness and reference landmarks before importing transforms. Validate height ratios in a camera view and overview; do not claim a view-matched whitebox is exact reconstruction.
