# S3 PLAN → ACTUAL SEMANTIC CHECKER

正式版本1.7.0；V1.8为研发阶段名。AG/1.0、CSP/1.0、现有Builder与S2合并/锁保护合同不变。

链路：Author Graph → 显式Expected Observables → 已保存Blender工程逐帧Actual Trace → 八类Checker → JSON/HTML诊断 → 仅供人工使用的REPAIR-SUGGESTION.json。没有Changeset/Patch生成器，没有修复调用。

作者侧只使用原六集合。本轮新增Expected协议和运行时Trace，另以测量binding连接稳定Entity/Shot ID与原生对象名。binding的views是测量视图：例如YOUTH_HEAD属于CHAR_YOUTH，引用现有头部Mesh；不创建新的作者角色或Blender物体。

| 边界 | 内容 |
|---|---|
| plan_to_observables.py | 受控数值/状态声明、原AG引用与来源；UNKNOWN/自由艺术语言留NOT_REVIEWED |
| actual_trace_exporter.py | 从bpy evaluated scene、原生Cut marker与Camera测量；不读取CSP采样轨迹作为Actual |
| screen_projection.py | Mesh顶点/边的近远裁面投影、原始/裁剪矩形、遮挡估计标签 |
| motion_analysis.py | 有限差分、速度、方向/恢复趋势；没有动画写入 |
| plan_actual_checker.py | 指纹/coverage/schema检查、八类指标、审计报告和只读建议 |

三个现有案例的副本只增补明确技术观测声明，原图/动画不改。CDR-003/004沿用S1迁移图；V02由已有CSP的DEBUG adapter建立诊断图，仍标DEBUG，未知导演意图不补造。明确来自USER_TEXT_TARGET的百分比保留；本轮操作阈值标AUTHORED技术声明，不追认为历史用户批准。

Trace逐帧记录实测变换/投影/射线估计、几何距离与身份token。event_state仅是REGISTERED_WINDOW，不是动作阶段已实现的证据。Owner登记值是Plan侧注释；没有native s3_owner_id属性时Owner核验为NOT_REVIEWED，禁止用登记值自证Actual。

Checker不要求旧案例全PASS。严格HOLD阈值可能与旧Hold标签的含义不同；报告列数值和声明来源，让人工判断是执行偏差还是需澄清Plan。S3工程PASS只表示协议/工具/回归与六项破坏检测通过。

S2接口止于问题、作者来源、对象、时间和可能通道。人工先审诊断、排除测量假错误，再正常速度审Clean；后续修改仍须明确授权并走S2保护入口。本轮停止于S3。
