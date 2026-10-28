# AUTHOR-INPUT-REQUEST/1.0

A request contains request_version, plan_id, graph_id, event_id, status, missing, known, valid_unresolved_choices, question, automatic_dialogue=false, automatic_execution=false and provenance. Files may contain a list of independently schema-valid packets when a graph has multiple unresolved plans.

NEEDS_AUTHOR_INPUT means required facts, reliable evidence, evaluated read tracks or a safe entry are missing. AMBIGUOUS means multiple unresolved meanings/choices remain (for example two legal dodge directions or dolly versus lens). UNSUPPORTED means no safe rule exists, notably ATTACK. Constraint and override conflicts are separately identified.

Packets do not ask a live conversation question or restart the compiler. No valid unresolved choice is selected automatically. The caller must obtain a separate authored revision before trying again. The present S52 acceptance run contains a deliberately missing dodge direction and unsupported attack; neither produces PRIMITIVES, CSP, Blend or a Builder invocation.

CLI: `python scripts/event_lowering.py --graph AUTHOR-GRAPH.json --context EXECUTION-CONTEXT.json --output NEW_DIRECTORY`. Output is review data and, only for fully validated READY plans, S51 primitives/fragments. A new output directory is required to avoid leaving stale CSP/Blend artifacts beside a later unresolved result.
