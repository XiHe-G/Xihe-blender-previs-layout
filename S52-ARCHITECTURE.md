# S5.2 Architecture

Release version remains 1.7.0; this is an additive development stage. AG/1.0, the S5.1 runtime, CSP semantics, Builder, S3.5 checker and S4.5 thresholds are immutable dependencies.

Pipeline: authored AG evidence + explicit execution context → fixed event/camera registry → EVENT-LOWERING-PLAN/1.0 → HIGH/MEDIUM READY only → S5.1 compile_program → existing boundary validation and constraint preview → fragment → existing primitive_fragment_merger → ordinary CSP → original Builder → reopen / Actual Trace / existing checker.

The implementation selects named tools, translates quantities, composes channels and transfers state. It contains no position integration, curve generator, pose solver, camera controller or bpy writes. Technical fixture code contains only author JSON construction, static initialization, assertions and tool calls. This is not arbitrary prose interpretation or automatic choreography.

AG/1.0 evidence.value already accepts strings. S52 uses an explicitly authored JSON object encoded in this existing string, with evidence.status/source intact. This is a bounded, machine-readable author vocabulary for destination, timing, threat direction, gaze target, stability and camera relationship. No primitive_type, primitive_parameters or execution samples are added to AG. Ordinary prose is not guessed; it produces an input request. Entry camera transforms and runtime object aliases remain in the separate EXECUTION-CONTEXT.json, with a hash in the lowering report.

The public lower_graph(graph, context) returns (report, program, bundle, requests). program/bundle are None if any selected plan is unresolved, blocked or fails validation. Successful prefix calculations are diagnostic only; they do not authorize a partial scene build. The command-line entry emits plans, requests and READY fragments; it never invokes Blender. Only the native acceptance runner calls the original Builder after builder_allowed=true.

All five positive technical graphs use the same lower_graph entry. L6 and unsupported ATTACK emit only reports and never invoke the runtime or Builder. This is a full-program technical lowering path; it does not bypass S2 for production edits. Existing approved CSP cannot be overwritten through the fresh-fixture merger.

Authority: explicit author quantities → scoped constraints → previous evaluated exits/entity facts → explicitly permitted derivation. Contradictions stop. LOCKED overrides are checked before runtime, including unknown relevant lock channels which fail closed. Unparsed constraints stop. No requirement is relaxed to improve coverage.

Reproduce (Blender bundled Python; add scripts/tests and existing foundation-v18/.deps to PYTHONPATH): `python -m unittest discover -s <skill>/tests -p test_*.py`; separately `python -m unittest test_combat_sequence_package`. Native: `blender -b --factory-startup --python-exit-code 1 --python <skill>/tests/run_s52_fixtures.py -- --output <new-empty-directory>`. Factory startup avoids user preferences/add-ons changing standard material nodes; Builder code is unchanged.
