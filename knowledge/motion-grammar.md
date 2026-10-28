# Motion Grammar

Supported primitives are intentionally small and composable: `STAND`, `CROUCH`, `KNEEL`, `BOW`, `SIT`, `LIE`, `CORPSE`, `RISE_FROM_KNEEL`, `RISE_FROM_CROUCH`, `STAND_FROM_SIT`, `FALL`, `MOVE_TO`, `WALK`, `RUN`, `APPROACH`, `RETREAT`, `FOLLOW`, `TURN_LEFT`, `TURN_RIGHT`, `TURN_TO_TARGET`, `LOOK_UP`, `LOOK_DOWN`, `LOOK_LEFT`, `LOOK_RIGHT`, `LOOK_AT_TARGET`, `REACH`, `POINT`, and `HOLD`.

Movement changes position and yaw continuously. Pose changes interpolate through visible weight transfer. `APPROACH` stops at a target distance; `RETREAT` moves away from a target; `FOLLOW` is available for a future actor-relative path. Keep action ids unique and within shot frames.

## Dynamic action grammar

Dynamic layout extends the small primitive set with a phase contract rather than a long list of fighting verbs: `ANTICIPATE → IMPULSE → TRAVEL → READ/HOLD → CONTACT → RECOIL/RECOVER`. Each phase records its actor, interval, support, center-of-mass witness, facing and prop state. Head/aim may lead the body, while the lower body establishes or receives support before force transfers upward. Airborne paths can use a documented ballistic approximation in action time; editorial slow motion does not rewrite gravity. Grounded and contact intervals are checked separately from free flight.

Use persistent prop states `HELD → RELEASE → FLIGHT → NEAR_MISS/CONTACT → ENDPOINT`. A generic `FOLLOW` or `TURN_TO_TARGET` entry does not create a weapon exchange, projectile path or physical contact; those require explicit project animation and review frames.
