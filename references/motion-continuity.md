# Motion continuity and repair

## Ground and climb paths

Raw downward ray hits on fragmented rock can alternate between surfaces every frame. Sample a route, identify the intended support surface, smooth position/height/tangent, then check foot/root clearance and transitions. Keep true steps and endpoints. Excessive smoothing can tunnel through a ledge; inspect the resulting path. Small support geometry is a proposed scene adjustment, not a substitute for correct motion or permission to redesign an approved landscape.

## One writer per channel and interval

Assign ownership for root, local limbs, hands and props. Rest-pose keys and climb keys must not interleave in the same local channel and time span. Before rebaking a patch, inspect all relevant actions, slots/channel bags and NLA influences in the installed Blender version. Remove only keys in the explicitly owned repair interval, preserve boundary poses, write the corrected curve, and evaluate the final dependency graph result.

For quaternion sequences normalize values and maintain a consistent hemisphere: if dot(previous, current) < 0, negate the current quaternion before inserting keys. Compare angular change using the absolute normalized dot product. Quaternion sign repair cannot fix actual pose discontinuity.

## Check the evaluated animation

Inspect root and camera translation/rotation, local limbs, hand markers, prop transforms and world-space contacts. Assess per-frame speed and angular change against the actor's scale, shot size and intended motion; do not import numerical thresholds from another production. Sample offscreen movement, cuts and every state change too.

A root/camera-only numeric PASS does not cover local limb corruption. Static first/middle/last images do not cover one-frame pops. For suspected intervals, render consecutive frames and a continuous clip, including the frame before and after the repair.

A bounded patch records object/channel names, frame range, cause, before/after measurements, preserved constraints and witness frames. Rerender affected frames and regenerate every video/review/subtitle product that depends on changed timing or imagery. If the source .blend changed, old frame receipts are conservatively stale unless a reviewed dependency map proves reuse.
