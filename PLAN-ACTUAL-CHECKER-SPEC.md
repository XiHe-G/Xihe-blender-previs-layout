# PLAN → ACTUAL Checker

只允许PASS、FAIL、WARNING、NOT_REVIEWED、NA。severity为CRITICAL/MAJOR/MINOR/INFO；明确失败在MINOR/INFO时作为WARNING。未知指标、缺样本、缺必要阈值、缺实际Owner证据不判PASS。显式applicable=false可记NA。

| 家族 | 检查/必要参数 |
|---|---|
| SHOT_SIZE | 逐帧height/width投影比例与expected_range；输出min/max/delta和失败帧；尺寸失败优先列明，比例符合但完全遮挡不得PASS |
| SCREEN_POSITION | 实际投影中心落在LEFT/RIGHT/CENTER/UPPER/LOWER或明确归一化区域；安全边界容差 |
| SCREEN_DIRECTION | 实际屏幕轨迹净位移、方向与coherence；LEFT_TO_RIGHT/RIGHT_TO_LEFT/UP/DOWN/DIAGONAL；跨Cut窗口NOT_REVIEWED |
| CONTACT / NEAR_MISS | 接触距离/相交；Near Miss要求整个活动窗口无接触、最接近时clearance在危险范围且有明确screen proximity；输出CONTACT/NEAR_MISS/SAFE_PASS、closest_time/frame/distance |
| PROJECTILE_CONTINUITY | 实际ID token、逐帧步长/速度上限、生命周期可见区间、terminal；有原生Owner才校验Owner，有release_time/relative trace才检查脱离；未知Owner整项NOT_REVIEWED，已知轨迹失败仍FAIL |
| ACTION_PHASE | ANTICIPATION/ACCELERATION的速度增加，PEAK速度峰值时间，CONTACT/NEAR_MISS复用几何检查，FOLLOW_THROUGH的速度/位移及可选转向趋势；无明显速度峰值不伪判PEAK |
| CAMERA_STATE | HOLD位移路径/转角/lens；FOLLOW相对距离与屏幕漂移；PUSH/PULL距离单调趋势且Camera必须确实移动；PAN/REFRAME转角；LAG/CATCH_UP相对目标屏幕误差变化 |
| RECOVERY | 起末分段速度比、末段位移收敛、max_step，可选姿态回正/速度跳变界限；不判断动作优美或生物力学 |

运行前重编Expected并核对完整AG/binding指纹；Trace做Schema、graph/timebase/measurement binding校验。每个window必须逐帧覆盖，缺帧/错时刻/错实际Shot不能空集PASS。未知自然语言单独输出NOT_REVIEWED，并保留作者来源。

报告每项含source_author_id、related_events、shot_id、severity、PLAN、ACTUAL、time_window、subjects、trace_pointer/frame/time证据。HOLD失败列出超过阈值的具体帧；不是仅给整段标题。HTML可按Shot/Event/Severity/结果筛选并展开完整证据，所有文本HTML转义，无外网依赖。JSON保存完整指纹与结果。

REPAIR-SUGGESTION.json仅含problem、source_author_id、affected_object、time_range、likely_channel、suggested_scope；action明确HUMAN_DIAGNOSIS_ONLY。不能自动成为Changeset/Execution Patch，不能绕过S2 Override。

本轮阈值是显式可审计的技术约定，不是通用艺术标准。例如HOLD使用0.02m、0.2度、0.05mm；快速Projectile使用粗5m/frame、150m/s跳位边界。较细瞬移可漏检，合法高速也可能在更紧阈值下报警。源Plan意图与操作阈值不一致时先人工澄清，不自动改镜头。

命令：`python scripts/plan_actual_checker.py --graph AUTHOR-GRAPH.json --expected EXPECTED-OBSERVABLES.json --trace ACTUAL-TRACE.json.gz --binding MEASUREMENT-BINDING.json --output report-dir`。

Python侧依赖沿用authoring/requirements.txt的jsonschema；Blender exporter只使用自带bpy/mathutils和标准库。正常速度Clean人工审片仍负责导演表现、节奏、力量感和审美；S3提供客观声明偏差定位，不替代用户判断。
