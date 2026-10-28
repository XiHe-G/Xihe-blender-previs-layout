# Prop interaction profile

Status: INTERFACE_ONLY. Contract/state constraints and validator exist; no attachment animator, rigid-body or hand IK runtime added. Continue using accepted Prop Control Continuity with explicit current CSP events.

Record prop type, relative mass, size, COM offset in prop-local space, carry/grip mode, named contact points, attachment point, orientation constraint, reach, support function, motion lag and interaction rules. Control and support references must resolve to existing states; transform parenting alone does not establish grasp, weight, support or release.

| Mode/example | Authoring requirements |
|---|---|
| HAND_HELD | Named hand/grip, ownership and release |
| PALM_SUPPORTED / bowl | Palm contact plus UPRIGHT orientation |
| BACK_MOUNTED / basket | Back contact, explicit rear COM offset in declared prop coordinates |
| SHOULDER_CARRIED | Shoulder contact, orientation and load |
| TWO_HAND_HELD | Separate left/right grip points |
| GROUND_SUPPORTING / staff or cane | Hand grip + ground support contact, vertical/diagonal constraint |
| WEAPON / sword | Grip, weapon axis, reach and intended threat route |
| CONTAINER | Carrier relation, upright/contents constraint as appropriate |

Changing weapon geometry does not automatically revise reach, threat route or contact timing. Record these dependencies before edits. Validator currently enforces palm/ground/back/two-hand/weapon minimal conditions and dimensions; author/native review still owns range, COM direction, release timing and actual contact. No simulated lag or true COM solving is claimed.
