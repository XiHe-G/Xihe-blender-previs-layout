# Prop control continuity — LIMITED development contract

`prop_control.compile_control` composes explicitly authored control transitions into existing CSP/1.0 `action_beats`, dense `object_tracks[].state.prop_control`, and `continuity_states.ownership`. It returns a new package. No Author Graph object class or parallel timeline is added.

States: FREE, CONTACT_PENDING, CONTROLLED, RELEASING, PLACED. Events: CONTACT, ACQUIRE, FAIL, RELEASE, PLACE, FREE, TRANSFER. Contact never grants control. ACQUIRE references a matching contact event and requires a continuous contact dwell; TRANSFER additionally names the previous controller. FAIL leaves the object free. RELEASE removes the controller immediately. PLACE requires an explicit support plane and native mesh-bottom verification. FREE after RELEASE is a distinct terminal state; current release continuation is explicitly HOLD_WORLD, not free-flight physics.

Bindings identify prop, actor, sampled control-point object, handle offset, contact radius, minimum contact frames, maximum actor reach, maximum prop speed, numeric position tolerance and placement tolerance. Values belong to the scene scale and authored contract; no benchmark names enter the runtime. Contact uses a proxy point, not anatomical hand IK. Translation anchoring preserves the acquisition world position and follows pre-evaluated driver samples. Rotation and force transmission are outside this version. Optional rigid members keep their relative translation. Existing S51 primitives produce motion samples.

The Builder only adds discrete custom-property keyframes (`previs_prop_control_index` and a state registry); existing transforms, geometry and interpolation stay unchanged. `prop_control_native.native_control` reads the saved/reopened state. Native controller, prop and handle positions must be observed, not inferred from names. Static owner metadata means provenance and is separate from current active controller.

`validate_control` replays transitions, checks contact dwell, controller changes, release legality, proxy reach, transform continuity, stable placement and cut snapshots. Missing native control evidence cannot PASS. A read-only native validation must use saved/reopened Blender evidence. New sessions begin FREE; an initially held object must provide an explicit initial acquisition sequence rather than silently naming a controller.

Old CSPs without this optional state remain unchanged. Fresh NARRATIVE actor lowering is not added: only an existing baked simple-geometry `scene_asset` can be replayed as NARRATIVE CSP; fresh actors remain the established COMBAT_BOX_4 path. Unsupported rig/constraint geometry remains rejected.

No momentum transfer, full support solver, IK, grasp-force simulation, automatic director repair, or artistic quality claim. Native tested transfer is not yet covered by a dedicated Blender scene; transition transfer currently has unit evidence only.
