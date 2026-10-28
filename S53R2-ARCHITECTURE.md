# S5.3R2 Architecture

S5.3R2 inserts a read-only feasibility path between the frozen Director Plan and AG lowering:

`DIRECTOR PLAN -> DIRECTOR-PREFLIGHT/1.0 -> one explicit Director revision (pilot-only) -> AG/1.0 copy -> event lowering -> S5.1 Primitive Runtime -> screen trajectory preview -> CSP -> existing Builder -> Actual Trace -> S3.5 Checker`.

The revision is limited to execution feasibility. It preserves shot count and boundaries, event order, character goals, entry/exit directions, and the fact that ATTACK/BLOCK are unsupported. The original S5.3 and S5.3R inputs remain immutable.

Orientation uses existing `ORIENT_TO` primitives with explicit channel plans: `HEAD_ONLY`, `HEAD_LEAD_BODY_FOLLOW`, and `BODY_ROOT_TURN`. Screen direction is evaluated after camera projection with S3 projection math. No repair loop is invoked.
