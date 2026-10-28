# Repair Candidate Impact Graph · 有限耦合表

每个图记录target_observable、directly_modified_channels、potentially_affected_observables、protected_observables、known_couplings、effective_protected_channels及table_sha256。耦合是可能影响，不等于该结果必然失败；原S3.5复核决定实际测量。World Motion不因Camera重构图自动获得修改权限。

| 策略 | PRIMARY_EFFECT | SECONDARY_EFFECTS | PROTECTED_CHANNELS | COMMON_FAILURE_MODES |
|---|---|---|---|---|
| LENS_CHANGE | SHOT_SIZE | SCREEN_POSITION, VISIBILITY, CLIPPING, OCCLUSION, SCREEN_DIRECTION, CONTACT, NEAR_MISS, CAMERA_STATE | world_motion, pose, camera_transform, cut_timing, identity | Off-axis subject magnified outside frame; Other subjects cropped; Zoom violates Hold |
| CAMERA_DOLLY | SHOT_SIZE | SCREEN_POSITION, VISIBILITY, CLIPPING, OCCLUSION, SCREEN_DIRECTION, CONTACT, NEAR_MISS, CAMERA_STATE, PERSPECTIVE | world_motion, pose, lens, cut_timing, identity | Parallax / occlusion change; Near-plane clipping; Moving camera violates Hold |
| CAMERA_REFRAME | SCREEN_POSITION | SHOT_SIZE, VISIBILITY, CLIPPING, OCCLUSION, SCREEN_DIRECTION, CONTACT, NEAR_MISS, CAMERA_STATE | world_motion, pose, lens, cut_timing, identity | Other subject leaves frame; Temporal pan violates Hold |
| RESTORE_CAMERA_ANCHOR | CAMERA_STATE | SHOT_SIZE, SCREEN_POSITION, VISIBILITY, CLIPPING, OCCLUSION, SCREEN_DIRECTION, CONTACT, NEAR_MISS | world_motion, pose, lens, cut_timing, identity | Anchor incompatible with moved subjects |
| PROJECTILE_LOCAL_OFFSET | CONTACT, NEAR_MISS | PROJECTILE_CONTINUITY, SCREEN_DIRECTION, VISIBILITY, OCCLUSION, MOTION_BOUNDARY | camera_transform, lens, character_world_motion, pose, cut_timing, identity, visibility_keys | Velocity / acceleration break at patch edges; New contact or teleport |
| RECOVERY_SPEED_SAMPLES | RECOVERY | ACTION_PHASE, CONTACT, NEAR_MISS, SCREEN_POSITION, VISIBILITY, MOTION_BOUNDARY | camera_transform, lens, pose, weapon, projectile, cut_timing, identity | Abrupt stop or acceleration at entry; Recovery endpoint drift |

Lens不改变几何深度排序；它改变视场、裁边及视觉深度感。Dolly改变视点和视差。Compound候选的有效保护通道为组成项保护集合扣除明确直接修改通道；它的人工审批仍需同时覆盖两种修改。没有获选候选、评分排名或自动执行字段。
