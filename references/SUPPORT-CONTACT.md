# Support contact — LIMITED / opt-in

Load for sitting, standing, supported leaning/pushing and recovery support changes. Use `support_contact.compile_support` on baked ordinary CSP object samples. No AG object or parallel runtime timeline is added. Every actor frame carries a `state.support_contact`; cut snapshots are copied into existing `continuity_states.support`.

Declare body control/meshes and actual finite cuboid support surfaces. BASE proxy probes and connecting segments, SEAT body-bottom contact, and HAND control-point contacts are measured after save/reopen. Proxy support segments are bounded connectors, not anatomical legs, IK or locked foot plants. Do not claim running gait or physical weight distribution. Explicit weights are declared support responsibility, not solved forces.

Each state interval references an action-beat SUPPORT_TRANSITION. Sitting must pass through WEIGHT_SHIFT. Changing support sources requires an explicit stable contract; weight ramps may not jump more than the declared maximum per sample. Supported object action requires prior native Prop Control, valid hand contact and body base support. LOST_SUPPORT requires timely RECOVERY; it does not authorize airborne/landing motion.

Default technical tolerances (meter-scale box proxy): contact gap 0.015 m, body point step 0.15 m/frame at 30 fps, support projection margin 0.35 m, support responsibility step 0.15/sample, bounded support link 0.9 m. These are TECHNICAL_DEFAULT, not physical or director-approved universal thresholds. Bindings must state applicable scale/timebase. Finite support footprint and link endpoints are checked independently of labels.

`validate_support(csp, observed)` requires native properties plus evaluated geometry. Planned-only or missing native geometry is NOT_REVIEWED. Known invalid contact, unsupported force, floating/disconnected body, abrupt support/pose change and missing recovery FAIL. State PASS alone is not support PASS. Saved Builder hooks only persist/read discrete custom properties; ordinary TRS remains the sole movement executor.

Scope: simplified cuboid top surfaces and proxy control contacts. No arbitrary mesh collision, pressure/COM solver, momentum, IK, muscle, ragdoll, aerial or landing system. Hand support is proxy-level; anatomical grasp and whole-body force balance remain unverified. Full benchmark and director quality are separate gates.
