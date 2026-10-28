# Support release clearance — S009R

Owner: `support_release_clearance.py`, used by opt-in `takeoff_land.py`. One CSP global frame timeline. No Builder, AG, motion or Camera kernel change.

Support weight zero is semantic release, not geometry clearance. Passive departure needs a valid actor/surface transition, zero support weight, **full named body witness** outside the native finite support volume, and a conservative outgoing sweep. Center clearance never suffices. Preserve semantic unload time separately from geometric release; between them, `SUPPORT_LOSS` is pending clearance, not AIRBORNE.

`SUPPORT-RELEASE-CLEARANCE/1.0`: actor, support_surface, native support_region bounds, body_clearance_proxy, direction, release_candidate_frame, minimum_clearance, evidence_source, transition_event, mode and interpolation proof. Results record first_valid_clear_frame, center/body clearance, support weight, transition authority and interval sweep bounds. Technical tolerance remains `.015` meters; not human perception or universal collision tolerance.

V0.1 proof is restricted to axis-aligned planar support and fixed-orientation, fixed-size box witnesses under linear translation. Endpoint AABB union conservatively contains every intermediate translated box. It may reject safe diagonal paths; it is not general collision physics. Rotating/deforming/unresolved witnesses are NOT_REVIEWED, never guessed. Native evaluated geometry uses existing `support_contact_native.bounds`; no parallel bounds definition.

Passive DROP compile requires measured native local witness bounds and immutable platform evidence. Prediction blocks premature release. After the unchanged Builder saves/reopens the scene, `validate_air` also requires actual per-frame `clearance_bounds` and actual `support_region`; planned bounds do not replace native verification. Metadata-only results are NOT_REVIEWED. Run existing support and boundary validators as well.

Active vertical push-off differs: contact at the release frame is legal, the first outgoing sample must clear upward without penetrating the support. Do not apply passive horizontal edge clearance to a standing jump.

Clearance frame changes are proposals. If original endpoint/timing cannot hold, return TRAJECTORY_RETIMING_REQUIRED and obtain director authority before changing the target or total duration. Do not shrink the actor, move the platform/Camera or loosen thresholds.

Errors: SUPPORT_RELEASE_BEFORE_BODY_CLEAR, CENTER_CLEAR_BUT_BODY_OVERLAP, SWEPT_EDGE_INTERSECTION, AIRBORNE_WHILE_INTERSECTING_SUPPORT, CLEARANCE_PROXY_UNRESOLVED, SUPPORT_RELEASE_GEOMETRY_CONFLICT.

Maturity maximum LIMITED for this narrow box/plane domain. No IK, rigid bodies, character controller, force/mass solver or combat claim. C2 warnings/failures remain visible. Lighting absent: NOT_APPLICABLE; no new confirmation gate.
