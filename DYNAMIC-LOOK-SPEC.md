# Dynamic Look

Entity targets are resolved from the evaluated trajectory DAG, not from an initial pose. Required angular velocity is sampled over the event window. Head lead and body follow can be evaluated as a channel split; if the sampled target cannot be followed under the declared angular limit, the event stays unresolved.
