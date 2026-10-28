# Scene-level plan versus Blender actual

Status: INTERFACE_ONLY. `plan-vs-actual` defines SHOT_PLAN / BLENDER_ACTUAL evidence references and requested comparisons: shot count/order, world positions, screen direction, terminal states, Camera path, lens, Lighting Context and output version. No new scene-level evaluator is implemented. Template status is NOT_REVIEWED.

Keep the existing S3/S3.5 measurable intent and native evidence checkers. New adapters should join by stable scene/shot/actor IDs and one existing global frame source, preserve UNKNOWN/NOT_REVIEWED for incomplete evidence, and report numeric, visual and director judgments separately. Matching Camera transforms does not prove composition; matching a lighting plan does not prove illumination. Seedance actual extraction/comparison remains NOT_IMPLEMENTED_RUNTIME.
