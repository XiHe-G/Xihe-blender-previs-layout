# Director Preflight / 1.0

Preflight checks time feasibility, orientation budget, evaluated-target trackability, screen-space direction, and camera/subject compatibility before Builder execution. It reports `FEASIBLE`, `INFEASIBLE_DURATION`, `INFEASIBLE_TRACKING`, `SCREEN_SPACE_CONFLICT`, or `NEEDS_AUTHOR_INPUT` and never edits the production graph.

Plan provenance is explicit: `USER_LOCKED`, `SOURCE_LOCKED`, `DIRECTOR_GENERATED`, or `TECHNICAL_DEFAULT`. This pilot permits one `DIRECTOR-REVISION-PROPOSAL` for Director-generated plans only.
