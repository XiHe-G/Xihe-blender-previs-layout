# Combat intent / 1.0 — opt-in, LIMITED

Owner: `scripts/combat_intent.py` (CSP contract/diagnostics) and `scripts/combat_intent_compiler.py` (composition). Formal version 1.7.0. Development S010.

Use only for explicitly authored one-to-one simplified proxy combat. This does not enable arbitrary ATTACK/BLOCK AG auto-lowering. Existing unsupported mappings are unchanged. No VFX, tactics, exact collision physics, IK, or automatic Camera design.

`compile_intents(csp, plan)` returns ordinary CSP plus primitive/fragment evidence. All frames use the original global timebase. Plan contains actor/weapon identities, finite contact anchors, fixed threat direction, per-beat cue, result, relative intensity and timing. Existing perception, prop control, support, momentum, intensity and RECOVERY_PROFILE are reused. Weapon controller remains the attacker through Block and Hit. Fixtures may supply parameters and static geometry, never their own motion interpolation.

V0.1 executable geometry scope is a straight committed +X attack with a fixed horizontal bar proxy, target region, ground support and lateral evade. Other directions are rejected. Route endpoint is authored before commit; it never follows a moving defender. Contact is the native weapon endpoint versus declared target/defense region, not exact swept weapon-body collision. All tolerances are TECHNICAL_DEFAULT, not human safety/perception standards.

State projection includes NEUTRAL, PREPARE_ATTACK, ATTACK_COMMIT, DEFEND_PREPARE, BLOCK_ATTEMPT, EVADE_ATTEMPT, CONTACT/NEAR_MISS, result and RECOVERY. Initiative records attacker/defender/neutral; a change is emitted only when a subsequent authored beat names a different attacker. The compiler does not select tactics.

Source cue → S002 explicit perception → reaction delay → defense. S003 acquisition establishes weapon control before attack; touching the defense region does not transfer ownership. S004 verifies grounded support. Block/Hit use S005 sourced momentum consequences and recovery. S008 relative profiles feed S51 primitives. Repositioning must wait for the full momentum recovery window. A short constant-velocity contact handoff preserves the finite-difference S005 input contract.

`validate(csp, contract, observed)` requires saved/reopened native evidence plus independent perception/control/support/boundary dependencies. Missing evidence is NOT_REVIEWED, never PASS. Reject missing threat, anticipatory defense without authority, Block/Hit without contact, Evade remaining in route, Miss with contact, unsourced response, illegal tracking, ownership change and missing recovery. Ordinary contact never implies Hit; no contact never implies Evade.

Native C0/C1 and raw C2 are reported separately. C2 FAIL remains visible. Mechanical PASS is not independent human comprehension or director approval. Sprint006/007 remain EXPERIMENTAL. Review CLEAN first, then DEBUG; downstream video generation remains disabled.
