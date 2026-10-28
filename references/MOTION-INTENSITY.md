# Motion intensity and action trend (S008)

## Director-approved abstraction policy · 2026-09-23

Layout communicates who/where/facing, world and screen direction, route, relative speed, acceleration/deceleration, rhythm, intent/trend, success/failure, control, support, motion consequence and key states. It does not require precise gait, arms/fingers, detailed center-of-mass animation, mocap, precise fighting technique or complex IK. These may be completed downstream under layout constraints; no downstream generation is implied or tested.

BODY_CONTACT_WITNESS_REFINEMENT is deferred by explicit user decision. Contact Response Readability and Contact Witness Calibration remain EXPERIMENTAL; neither is removed or promoted.

## Owner and interface

`scripts/motion_intensity.py` is an opt-in execution compiler and diagnostic, not a new motion kernel, autonomous author-event selector or Camera system. It calls existing S51 RECOVERY_PROFILE as a generic smooth velocity interpolator (as Momentum already does), and emits normal primitive fragments/CSP poses. No AG changes. All frame/time conversion uses existing timebase.

`compile_profile(spec, timebase)` accepts id, actor, intensity_class, trend, start_position, direction, facing_yaw, phase knots, body_trend and provenance. Knots have absolute global frame, nonnegative scalar speed and phase. Output contains ordinary primitives/fragments plus MOTION_INTENSITY_PROFILE data: class, entry/target/exit speed, per-phase durations, total displacement and source. Speed direction remains separate from facing. Phases: PREPARE, ACCELERATE, CRUISE, BURST, DECELERATE, STOP, RECOVER. No requirement to use all phases.

Classes SLOW/WALK/FAST_WALK/RUN/SPRINT/BURST are director-relative labels. There is no universal m/s lookup. Authors supply scale, durations and speeds. `validate_ladder` compares explicitly selected same-context observations; do not compare class labels across differently scaled projects as absolute truth.

`apply_body_trend` writes existing actor body_pitch/body_roll proportional to normalized generated speed. It is a simple torso trend, not gait, physical balance, IK or contact proof. Existing motion/control/support semantics have priority.

`redistribute_path` is an explicitly scoped candidate-copy adapter: named actor objects and phase windows, unchanged path endpoints, time and Camera, peak derived from remaining arc length. It changes only location samples inside the supplied scope. It is not automatically selected or inserted in legacy scenes. Reject locked work; registered override edits still require S2. Native support, contact/control and consequence validation is mandatory after re-spacing. Nonlinear terrain/curved paths are not certified by this limited experiment.

## Validation and limits

Mechanical diagnostics: SPEED_CLASS_NOT_SEPARATED, ACCELERATION_NOT_VISIBLE, BURST_WITHOUT_SPEED_GAIN, DECELERATION_NOT_VISIBLE, HARD_STOP_TOO_SOFT, ACTION_TREND_MISMATCH. Root speed and projected center speed are sampled; missing target/facing/screen evidence cannot PASS. Screen center is not an occlusion/visibility certificate. Technical relative ratios (1.2 speed-class separation, 1.5 gain and hard-stop comparison) are assumptions, not independent perceptual calibration.

APPROACH/CHASE/LUNGE need a target relation and forward motion; DODGE requires lateral motion relative to facing; RETREAT requires backward motion; HARD_STOP needs a normal-stop comparator. PULL/PUSH/TURN_AND_GO/STOP_AND_REACT/RECOVER are accepted declarative labels, but their dedicated trend diagnosis is NOT_REVIEWED in this version. Prior recovery/control modules remain responsible for their existing contracts.

Boundary evaluation reuses unchanged S45 and S53R authored-start semantics. Keep raw relative dimensions and C2 records; genuine jumps must still fail. C0/C1 passing does not erase a C2 warning/failure or certify physical motion.

Evidence: AUTODEV Sprint008 technical prototypes and benchmark slices, fixed Camera; no human/director approval inferred from mechanical PASS. Full benchmark failures and pending director review remain visible. Narrative inputs are untouched unless explicitly opted into a new profile.
