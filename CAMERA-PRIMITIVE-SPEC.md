# Camera Primitive Kernel

只生成普通 Camera CSP samples，不改变主体世界运动。默认 perspective、36mm sensor width、16:9（可显式 aspect_ratio）、固定 lens；投影是测量预估，Native mesh trace 才用于 fixture Gate。

| Primitive | 输入与行为 |
|---|---|
| CAM_HOLD | behavior_profile=LOCKED_HOLD / COMPOSITION_HOLD / SOFT_HOLD；直接导入 checker_calibration.PROFILES；固定、有限构图保持、轻微跟随 |
| CAM_REFRAME | subject/target、target_screen_region=[xmin,ymin,xmax,ymax]、max_rotation(°)、max_translation(m)；优先旋转，可显式 translation；不改 Subject |
| CAM_FOLLOW | target、follow_strength、lag、distance、screen_anchor、target_offset；带速度状态的临界阻尼追踪，不是直接拷贝固定 offset |
| CAM_LEAD_LAG | target、lead_distance（正领先/负落后）、lag_time、screen_bias、transition_duration；平滑进入显式领先/落后关系 |
| CAM_PUSH_PULL | mode=PUSH/PULL、distance_delta、profile、lens_policy；默认沿视线平移；仅 EXPLICIT_ZOOM 允许 exit_lens |
| CAM_CATCH_UP | target、entry_lag、follow_strength、catchup_start、settle_start；明确 entry lag→加速追赶→settle；可 entry_from 承接前片段 |

CAM_HOLD 预检实际调用既有 `camera_hold()`，不另建阈值。COMPOSITION_HOLD 使用有界平滑 translation 保持构图；超过原 world/composition 限制就拒绝。SOFT_HOLD 不是主动 Push 的许可。Native 验收使用同一 S3.5 Checker，包含屏幕关系、Camera 实际 transform、lens；默认阈值继续标 TECHNICAL_DEFAULT。

Camera 的入口/出口记录 position、orientation、lens、subject_screen_position、subject_screen_size、velocity、angular_velocity。显式顺序组合检查共享位置/速度、四元数/角速度及 lens 通道。惯性跟随在输入轨迹的边界按显式入口/出口速度延续，并用入口偏差平滑接入延迟轨迹，防止起步倒冲。

Translation 用未修改的 S4.5 C0/C1/C2 规则；新增 angular-only 检查记录四元数连接、入口角速差和每帧角速变化（技术默认 0.01 rad/s 入口差、0.1 rad/s 每帧变化）。这些没有替换或放宽 S4.5 的平移阈值。小角度插值仍按精确 slerp 限速。角速度/构图窗口无法满足时输出失败，不能自动修改参数。

限制：无 orbit、handheld、crane、shake；无摄影艺术评分；不保证任何目标路线都能同时满足 distance、screen anchor 和所有 Hold 限制。复杂 parent/roll、遮挡、多主体构图和任意 fps 的参数组合需要额外验证。相机不会自行选择类型或镜头。
