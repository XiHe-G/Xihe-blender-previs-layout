# Director Override

An override is a deliberate production decision expressed as a target and a patch. Targets can be `environment:<id>`, `character:<id>`, `action:<id>`, `camera`, or `shot`. Examples include moving a character, changing a proxy color, changing a camera lens, replacing a camera target, or retiming an action.

Apply overrides before normalization so they are included in the fingerprint and review package. The patched plan is the source of truth for that build. Use `OVERRIDE_PATCH` for an incremental rebuild; the runtime selects environment, camera, motion, or render-only work from the affected scopes.
