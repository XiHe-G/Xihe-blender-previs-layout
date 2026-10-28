# Orientation Channel Plan / 1.0

The three supported plans are `HEAD_ONLY`, `HEAD_LEAD_BODY_FOLLOW`, and `BODY_ROOT_TURN`. A split plan writes `HEAD_ROTATION` first and `BODY_ROTATION` later using the same existing `ORIENT_TO` runtime. It does not add an AG object or a new primitive. Channel ownership is checked before execution.
