# S2 Partial Recompile 架构

正式版本 **1.7.0**；V1.8 是研发阶段名称。AG/1.0 六集合、CSP/1.0 与 Builder 运动行为不变。S0/S1 已获 `S0_S1_APPROVED_CLOSEOUT`。

数据链：批准的 AG + 批准的执行绑定 + CHANGESET + OVERRIDE REGISTRY → Change Analyzer → 显式依赖闭包 → AFFECTED SCOPE → 作者提供局部 execution lowering → EXECUTION PATCH → 校验/合并/锁保护 → 普通 CSP → 原 Builder → 区域回归。

## 协议与职责

| 文件/模块 | 职责 |
|---|---|
| changeset.schema.json / change_analyzer.py | 校验目标、旧值、基图指纹；追踪直接修改和显式因果闭包 |
| execution_state.py | 为已批准 CSP 添加执行所有权索引；CLEAN / DIRTY / STALE / LOCKED |
| execution-patch.schema.json / execution_patch_validator.py | 仅标量替换补丁；重新计算 scope，拒绝越界、过期、未声明写入 |
| execution_patch_merger.py | 事务式合并，现有 CSP 校验、作者时序核对、无关区域逐值比较 |
| override_guard.py / override-resolution.schema.json | 登记手改快照；LOCKED 拒绝写入；显式授权 resolution |
| s2_common.py | 规范化指纹、JSON pointer、有限执行 selector、逐叶比较 |

这些协议是编译辅助数据，不是第七类作者对象。AG schema 未修改。`S2-EXECUTION-BINDING/1.0` 与 CSP/AG 分开保存，包含全图/执行指纹、事件与镜头旧 ID 的完整双射、regions 和 provenance。region 包含 region_id、owner、section、target、channel，以及 track 的闭区间 frame_range；可用 entities 明确受影响实体。

S1 的执行 sidecar 先通过原编译合同解码，再由 `execution_state.from_s1()` 加入作者明确提供的 region 索引。已有 binding 不因意图改动而被直接重用；未跟踪修改或基包漂移得到 STALE。索引必须先经审核，不能由补丁临时扩大。S2 更新后的外部 binding 是当前编译依据；Graph 中旧 S1 execution 引用保留为来源，不重写为可绕过校验的新 sidecar。

## 闭包与范围

以 DEPENDENCY 的 depends_on → event_id、EVENT.source_event → 当前事件进行传递闭包，每条边记录原因/condition。条件文本用于解释，不由程序猜测布尔值；保守包含全部显式下游。多个直接根排序后遍历，scope 指纹跨进程确定。没有依赖的前段 Projectile 不因时间接近而加入。受影响镜头由明确 region 与 Cut 相交标注，镜头标注不会扩大可写路径。

本轮 A/B 的响应 region 是已批准的 F43–F96 局部采样窗口，包含修改所需提前余量；多个事件可以共享窗口。闭包最小，执行窗口有明示的保守边界，未宣称能逐帧推导数学最小范围。缺少受影响事件/镜头的所有权索引时拒绝局部更新。作者逐个 dirty region 声明 UPDATED 或 REVALIDATED_UNCHANGED 并给原因；后者不是系统自行把旧数据当新数据。

## 执行与状态

CLEAN：当前 AG/CSP 与绑定一致。DIRTY：已跟踪 Changeset 可映射到局部 region。STALE：未知修改、拓扑/结构变化或指纹失配，需要重新提供完整 lowering。LOCKED：人工保护的通道；它可与其他区域 DIRTY 同时存在。成功合并生成新的 CSP、Graph、Binding、Registry 与 receipt。

Partial 指作者层分析和执行数据的局部替换。Builder 仍读取完整普通 CSP 并完整重建，没有引入 Blender 增量构建器。原 Builder、默认角色结构、导演/Camera 规则、正式案例动画均未修改。

## 边界

第一版固定拓扑/采样数量，仅替换已有标量叶子。新实体、增删样本、改依赖结构、任意重排镜头不在此局部合同内。时间继续使用现有 timebase.py，不另立时钟。依赖传播只找范围，不生成动作。空间意图的普遍满足性不是本层求解问题；本轮用明确提供的 lowering 和专项结果断言验证 +1m。

人工 Blender 修改必须显式抽取相关执行值、登记源工程指纹和 LOCKED 投影。工具不会理解任意人工关键帧，也不会反推完整导演意图。Camera 父链必须显式检查，绑定中的父对象通道也要受保护；本轮真实案例 Camera 无父对象。约束驱动、驱动器及复杂 Rig 没有通用认证。

技术回归检查范围/指纹/锁/数据结果；没有视觉自动修复、Plan-vs-Actual 语义检查或新导演能力。S2 PASS 后停止，S3 需另行审核启动。
