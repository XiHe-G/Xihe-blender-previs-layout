# Camera semantic compiler and composition contract

Status: INTERFACE_ONLY. `compile_camera` packages explicit authored constraints and native-check requirements. It does not parse arbitrary director prose, choose lens/trajectory, solve composition, lower into Camera Kernel or validate pixels. Existing Camera Kernel remains unchanged.

All recipes require start/end framing, position path, height/rotation/target/lens behavior, screen objective, foreground relationship, allowed compensation and forbidden transforms. Path vectors use **camera-start local coordinates: X right, Y forward, Z up**, meters; native adaptation to world coordinates must preserve this convention. Timing stays referenced to the existing shot; no new spline/time source is introduced. A sampled contract is not a guarantee of between-sample curve behavior.

| Recipe | Required meaning and native checks |
|---|---|
| OTS_RELATION | Head/shoulder foreground, relation and depth; not generic waist occlusion |
| LATERAL_REVEAL_FROM_SHOULDER | Start behind head/shoulder; lateral X motion, fixed height/Y, no waist rise/orbit; Pan only when explicitly allowed; reveal named target |
| DIAGONAL_PULLBACK | Single monotonic diagonal backward segment, no dogleg or orbit; meet end composition |
| FOLLOW_THEN_STOP | Follow window, explicit stopping event and terminal camera velocity |
| STATIC_REACTION | Fixed position, rotation and lens; reaction stays visible |
| PUSH_IN_FOR_REALIZATION | Motivated trigger, approach target and end occupancy |
| COMPOSITION_PRESERVE_REFRAME | Re-solve world position only within authorized channels; preserve screen contract |
| SCREEN_DIRECTION_TRACK | Maintain selected screen direction over frames and cuts |
| FOREGROUND_WIPE | Specify occluder, crossing interval and reveal target |
| AXIS_CROSS_AUTHORIZED | Scoped actual authorization, transition and orientation cues |

The current validator enforces reveal geometry/prohibitions, single-segment pullback, static transforms, axis authorization presence, nonconflicting compensation, positive lens and normalized screen ratios. The other recipes produce checklists only; temporal and screen-space assertions require existing native evidence or future adapters. An authorization string must be checked against actual user history.

Composition contract includes subject occupancy, headroom, lead room, foreground relation, screen left/right, depth, background landmark, camera height, lens, perspective compression and ground relation. CAMERA_WORLD_LOCK protects transform channels; COMPOSITION_LOCK protects screen relationships and may permit world re-solving. Neither grants permission to change a protected channel. For 'positions changed but composition stays', preserve actor scale, side, head/shoulder framing, foreground occlusion and background landmarks; check native projection through time. Transform equality alone cannot prove composition.
