# Revision-bound rendering and delivery

## Preflight and render

Save and reopen the animated scene before rendering. Confirm intended scene, camera coverage, fps, global frame range and persistent objects. Review representative shot frames and continuous problem intervals at low resolution before committing to all frames.

render_existing.py reads render-job.json and a compiled timeline. It preserves the source file, reads the exact existing camera names in the timeline, renders review samples or an explicit final range, and writes PNG receipts. It does not generate animation or encode MP4s.

A render fingerprint includes the source .blend, timeline, job settings, renderer code and explicitly listed external dependencies. List external libraries, textures, caches and linked files used by the scene; there is no automatic Blender dependency discovery. A frame is reusable only if its receipt has the current fingerprint, dimensions and content hash. A mere existing filename is insufficient. Do not run overlapping ranges in the same output directory concurrently.

The conservative fingerprint invalidates all frames after any scene save. For partial rerenders, use explicit object/channel/frame dependency evidence and a project-managed render manifest; the helper does not infer unaffected frames. Never combine arbitrary old and new frames just to finish faster.

Encode only a verified contiguous frame sequence at the agreed fps. Export clean and readable review versions from the same sequence; keep dialogue SRT synchronized with the compiled timeline.

## Independent checks

verify_delivery.py probes every listed movie, counts decoded frames and runs a fatal-error full decode. It checks resolution, fps, duration, frame count and declared audio presence. It hashes all listed artifacts and can compare an earlier report using --compare. Inspect clean and review versions equally.

Record four separate claims:
1. technical_status: files decode and match specified media parameters;
2. freshness_status: current file hashes match the supplied earlier report, mismatch, or not compared;
3. provenance: whether a render receipt/manifest links the scene and movies (a file list by itself does not prove this);
4. visual_review and user_acceptance: actual review scope and actual user response.

Never infer final acceptance from approval of opening positions or from numeric PASS. Never claim full visual playback based only on contact sheets. If the scene hash differs but movies still match, retain the discrepancy and historical report; do not refresh the old hash as if it established provenance.

Deliver the editable .blend, clean MP4, review MP4, timeline/shot table, captions if applicable, technical report and concise README with version, known limits and review status. Do not add a voiced-audio claim when only subtitles exist.
