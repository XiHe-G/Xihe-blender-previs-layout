# Minimal Author Graph · AG/1.0

适用范围：V1.8 FOUNDATION BUILD 的 S1；正式 Skill 基线仍为 1.7.0。数据链为 INPUT → DIRECTOR PLAN → AUTHOR GRAPH → CSP/1.0 → CURRENT BUILDER。

Author Graph 记录角色/物体身份、镜头为何存在、事件、设计约束、因果依赖与人工覆盖记录。它不生成成熟打戏，不包含逐帧对象矩阵、Camera XYZ、lens 样本或最终关键帧。

## 六种核心集合

| 集合 | 必需字段 | 语义 |
|---|---|---|
| ENTITY / entities | id,type,module,owner,role,persistent_state | character / weapon / projectile / prop / environment；VFX 几何可用 prop + role，未增设第七类 |
| SHOT_INTENT / shot_intents | shot_id,time_range,primary_information,subjects,shot_size_intent,screen_direction_intent,camera_behavior_intent,required_visibility,handoff_to_next | time_range 全局秒；subjects 表示事件相关主体，required_visibility 才是明确必须看见；未知可为空数组，不能把投影包围盒当可见性证据 |
| EVENT / events | event_id,event_type,actor,targets,start,peak,end,world_intent,screen_intent,result,source_event | actor/targets 均为稳定 Entity ID 数组，允许多人共同事件；CONTACT 必须有双方；source_event 可空 |
| CONSTRAINT / constraints | constraint_id,scope,targets,requirement,provenance | 设计要求及作用域，不能装最终关键帧；S1 校验引用/作用域，不证明画面满足要求 |
| DEPENDENCY / dependencies | event_id,depends_on,condition | 被依赖事件→当前事件；无额外时间字段。因果条件可以跨越镜头；禁止环和重复边 |
| OVERRIDE / overrides | override_id,scope,target,channel,owner,reason,status | 状态 LOCKED / PROPOSED / RELEASED；S1 为结构保留位；S2 通过独立 Registry 执行通道保护，无自动 Blender 手工回写 |

容器元数据仅有 schema_version、graph_id、origin、module、entry_mode、timebase、execution。这些是协议/打包信息，不是第七种导演对象。JSON Schema 关闭未定义属性；新增动作类型通过同一个 EVENT 的 event_type 扩展，不新增逐动作 Schema。

必备类型：MOVE、LOOK、TURN、ENTER、EXIT、RELEASE、PROJECTILE_TRAVEL、DODGE、TAKEOFF、LAND、ATTACK、BLOCK、CONTACT、NEAR_MISS、FOLLOW_THROUGH、RECOVERY、VFX_TRIGGER、ATTENTION_HANDOFF。名称只描述事件；写 ATTACK 不会自动生成攻击曲线。

## 稳定 ID 与证据

CHAR_xxx、PROP_xxx、WPN_xxx、PROJ_xxx、SHOT_xxx、EVT_xxx、CST_xxx、OVR_xxx。后缀限 ASCII 字母数字下划线，全图唯一。Entity 类型必须匹配前缀。同一对象或事件跨 Cut 保持 ID；Shot 只是不同观察窗口。与旧 CSP 命名通过 execution binding 显式映射，既有 Blender 对象名、旧事件名和 Cut marker 不重命名。

意图值统一为 `{value,status,source}`，status 仅为 AUTHORED / SOURCE / INFERRED / UNKNOWN。UNKNOWN 时 value=null。SOURCE 表示文件明确记录的语义，不等于 source video 真实三维测量。INFERRED 不等于用户确认。origin 为 AUTHORED / MIGRATION / DEBUG。DEBUG graph 被生产 Compiler 明确拒绝。

Debug adapter 仅复制明确的 CSP summary/outcome/causal_links；缺失的景别、情绪、世界意图和 handoff 不补写。按旧名称识别 Projectile 仅记 INFERRED；不根据轨迹发明因果。本轮三个 MIGRATION 文件经显式逐例类型/别名映射整理，保留未知意图；没有重导演。

## 作者层与执行层边界

Graph 保存“是什么、为什么、何时、依赖谁”。执行侧保存“如何以既有对象/曲线实现”。`execution={path,sha256}` 指向独立 `AG-CSP-BINDING/1.0` gzip JSON，密集数据不进入 Graph。

执行 binding 含：

- `execution`：原 CSP 中除 shot_plan/action_beats/causal_links 外的内容，包括世界/姿态/Camera 采样、screen_targets、武器/VFX 生命周期、continuity、geometry 引用、review 等。
- `shots`：author_id、CSP 原 ID / camera_id 模板、原 interval/summary 是否存在；Compiler 从 Graph 生成帧边界、interval 与 summary。
- `events`：author_id、旧 event_id / owner / target / phase / breakdown 模板；Compiler 从 Graph 生成 interval、outcome 并核对 peak/参与者。
- `dependencies`：两个稳定事件 ID 和旧因果执行参数模板；Compiler 从 Graph 的事件绑定生成 cause_event/reaction_event，原 trigger/response/anticipation 保留。
- `entity_aliases` / `entity_groups`：明确对应旧对象名、复合参与者、物体群；Compiler 校验角色类型、Owner、持续状态、覆盖范围。
- `lifecycle_event_bindings`：每个 Proxy 绑定唯一现有源事件，Compiler 校验 CSP event_id；VFX 时刻属于该绑定的执行 lowering，不另写独立 VFX 脚本时钟。
- `author_sha256` 与 `source_csp`：绑定精确作者内容和原始 CSP 证据；源 Approval 只记录，不自动提升。

Compiler 不是“读取旧 CSP 然后原样返回”：执行包里不允许重复存放三个待生成集合，必须完整覆盖 Graph ID。旧 CSP 是兼容性比较对照，正式 compile 无需读取 source_csp 原文件。输出仍是原 Builder 接受的 CSP/1.0；不增加 CSP 字段或更改其语义。唯一允许的文件定位差异是将相同 SHA-256 的 geometry 路径解析为输出可用的绝对路径。

## 编辑与失效

首次创建 Graph 时，作者同时提供显式执行 lowering；本轮迁移复用旧批准执行数据。修改 Graph 的事件、时序、参与者、约束或意图后，旧 binding 会得到 `STALE_EXECUTION_BINDING`，不能悄悄重放旧动作。由作者完整重写/核对执行数据并重新绑定后才能再次编译。仅重算指纹不代表画面正确或用户批准；Compiler 的结构检查不替代导演审核。

S1 本身不自动传播时间编辑到曲线。S2 通过独立 Changeset、依赖闭包与作者提供的局部 lowering 更新执行绑定，见 [S2 架构](../S2-ARCHITECTURE.md)。Override 不进入 Builder；活动 LOCKED 必须走 S2 Registry/guarded merger，旧 S1 full compiler 明确拒绝绕过保护。S1 author_sha256 仍不包含 override；S2 binding 则绑定完整 Graph 指纹。没有 Automatic Repair 或 Plan-vs-Actual。Graph、binding 与 CSP 一起交付便于追踪；从 CSP 单独回读不能完美恢复导演意图。

## 验证和运行

安装 authoring/requirements.txt 所列的 `jsonschema==4.26.0` 到任务 Python 环境；旧 Builder 不新增此依赖。CLI 从 Skill 根目录运行：

```powershell
python scripts/author_graph_validator.py <your-project>/author-graph.json
python scripts/author_graph_to_csp.py <your-project>/author-graph.json --output out/sequence.csp.json.gz
blender --factory-startup -b --python-exit-code 1 --python scripts/combat_sequence_builder.py -- out/sequence.csp.json.gz --output out/new-build
python scripts/csp_to_author_graph_debug.py out/sequence.csp.json.gz --output out/debug-graph.json
```

这里的命令需要自己的 Author Graph、匹配的 execution binding 与 geometry。公开包中的历史 Graph 仅用于结构阅读，未分发对应生产数据；不能直接编译成动画。时间映射见 [TIME-CONVENTION.md](../TIME-CONVENTION.md)。

Schema 可以表达 NARRATIVE 语义；本轮 Compiler 明确拒绝未实现的 NARRATIVE lowering。旧文戏构建链独立回归，不将 Schema 可表达夸大为已有编译能力。
