# MOTION-BOUNDARY/1.0

输入为世界位置逐帧采样、Patch闭区间[lo,hi]、fps、对象ID、对象profile、scene_scale、可选插值/两侧极限证据及显式Authorized Discontinuity。至少需要lo−4至hi+4。缺守护样本返回NOT_REVIEWED，不判失败。

边界为[lo−1,lo]和[hi,hi+1]，同时检查内部与退出后的下一段。v[f]=(p[f]−p[f−1])/dt；a[f]=(v[f]−v[f−1])/dt；j[f]=(a[f]−a[f−1])/dt。每段记录位置增量、前/内/后速度、前/边界/后加速度、方向角及jerk。Jerk只记录，无普遍硬阈值。

C0：显式两侧位置极限差超过scene_scale×1e−5为FAIL；经只读检查的原生LINEAR位置曲线、无Parent/Constraint可证明共享节点连续。只有采样但无此类证据时C0=NOT_REVIEWED。线性位置连续不等于速度连续。

C1/C2：这里是离散运动质量诊断，不声称数学意义的连续时间可导性。参考速度取Patch外入口/出口守护段速度中位数；参考加速度取外部加速度中位数，并设与参考速度/尺度关联的数值下限。速度下限=scene_scale×fps×1e−4；加速度下限=max(reference_speed×fps×0.05, scene_scale×fps²×1e−5)。不会因为高速Projectile绝对速度大就自动FAIL。

speed_ratio=(max(v_before,v_inside)+floor)/(min(...)+floor)；relative_velocity_change=|vector_inside−vector_before|/reference_speed；acceleration_spike_ratio=|a_boundary|/reference_acceleration。方向接近零速时不强猜角度。

| Profile | speed ratio WARNING / FAIL | relative vector WARNING / FAIL | direction degrees WARNING / FAIL | acceleration spike WARNING / FAIL |
|---|---:|---:|---:|---:|
| PROJECTILE_CONTINUITY_PROFILE | 2 / 4 | 0.6 / 2 | 45 / 100 | 4 / 10 |
| CHARACTER_ROOT_CONTINUITY_PROFILE | 1.8 / 3 | 0.5 / 1.5 | 45 / 90 | 4 / 10 |

所有这些是TECHNICAL_DEFAULT、MEDIUM置信，不是导演批准的普遍物理阈值。场景尺度作为输入，当前R4使用0.5世界单位、Root fixture使用1.0；它们是显式技术假设，整体单位缩放测试保持相同比例结论。超过阈值只报告，不修改采样。

AUTHORIZED_DISCONTINUITY是编译/验证伴随协议，不增加AG顶层对象。须包含graph_sha256、实际event_id、subject、frame_range、derivatives、USER_AUTHORED/DIRECTOR_AUTHORED来源及reason。对象必须是Event actor/target，帧窗必须在事件全局时间范围内，timebase必须匹配。CONTACT/IMPACT/LAND只豁免C1/C2；TELEPORT/CUT_RESET可明确豁免C0/C1/C2。没有声明或只是在Cut附近，均不自动豁免。

授权不删除测量：每条结果保留raw_status、实际值和授权Event，只将该导数/窗口的政策状态标记为PASS / AUTHORIZED_DISCONTINUITY。R4没有这样的依据，保持FAIL。技术授权fixture只验证协议，不是给历史Repair补批。

REPAIR-ASSESSMENT/1.1保留TARGET_RESULT、SIDE_EFFECT_RESULT、MOTION_QUALITY_RESULT三个独立维度；另存historical_result_sha256。目标FIXED而边界非PASS时overall可为FIXED_WITH_WARNING，但必须同时展示MOTION_QUALITY_RESULT=FAIL；它绝非整体质量通过。新副作用FAIL则REGRESSION_INTRODUCED。旧S4结果不改写。
