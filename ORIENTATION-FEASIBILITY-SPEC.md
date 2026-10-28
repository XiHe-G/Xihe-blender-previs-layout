# Orientation Feasibility

The budget uses shortest quaternion angle, available duration, declared maximum angular speed, optional angular acceleration, and zero entry/exit angular velocity. The easing peak is `1.875 * delta / duration`; exceeding the declared limit returns `INFEASIBLE_DURATION`. Duration is never silently extended.
