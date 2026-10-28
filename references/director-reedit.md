# Director re-edit and second revisions

Preserve the original layout, its movies and the director's annotated/re-edited reference. Register each note by shot/content, original time, new time and affected field. A video with baked subtitles may contain outdated original timestamps; use measured edit boundaries for current timing.

Separate:
- whole-shot deletion;
- head/tail or internal trimming;
- speed change on a retained source interval;
- image crop/digital zoom versus a new native camera;
- changed actor action, route or final relationship.

A shorter shot is not necessarily a faster shot. Static frames cannot uniquely reveal which identical frames the director removed; label that mapping as estimated. Record source_in/source_out and approximate playback rate separately from output duration.

Round measured director cut boundaries to the target fps once, then derive adjacent shot durations. Do not independently round every duration and accumulate drift. Keep source order and inserted/deleted IDs. Map old narrative time to new edit time; a source seconds field must not be treated as new timeline seconds. Rebuild native 24 fps (or requested fps) keys; do not duplicate low-frame-rate images to claim native motion.

Recheck travel windows after deletions or trims. A shorter edit can compress or omit visible travel; it does not permit actors to teleport through geography. Keep explicit offscreen transit and validate the global state across cuts. Confirm changed routes/positions using the V1.2 diagram stage.

Changing the ending can require earlier staging changes. Trace dependencies backward: endpoint → departure path → confrontation point → relation shots / closeups → support height and light → render. Record which coordinates are an implementation choice, not source data.

Review first/middle/last samples and consecutive frames at retime boundaries. Keep height smoothing within continuous motion intervals; never smooth across unrelated old-time jumps or camera cuts. Preserve legitimate world continuity without averaging discontinuous edit-time samples. Disable motion blur when the edit mapping creates cross-cut trails that corrupt a reference image.

Deliver the change register, old/new time table, route/position confirmation record and variant-specific outputs. Mark final user acceptance separately from a completed render.
