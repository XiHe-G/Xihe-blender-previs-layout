# 动作表达：速度、受击与画面反馈 · 1.9.0

用于 COMBAT_DYNAMIC 的奔跑、突进、急停、平面转向、受击退移与身体反应。目标是让简化 Box 在正常速度下读得出方向、强弱、先后与恢复，不发展成完整步态或人体物理解算。视频参考可选，文字也可设计。已批准镜头和动作保留其意图，只改授权通道。

## 先判断问题在哪一层

- 距离／时间：记录场景单位、人物身高、路线长度、运动窗口、峰值速度和每秒跨越多少个身高。`RUN / BURST / 仙侠` 都不是数值校准。路程、时长、速度目标冲突时列出可调整项，不偷偷拉长动作或整体加速成片。
- Timing / Spacing：把准备、爆发、持续、制动、恢复分开分配；不要求每次动作都走完固定阶段。安静段与爆发段产生反差；下一招可以接续余势，不强制每招回待机。
- 身体：Root、下身、上身、头部允许不同响应时间；先读施力与重心，再加必要的压低、倾斜、转体、回弹。脚步细节不在默认范围。
- 摄影：角色居中跟拍时，结合地面／地标掠过、前后景视差、尺度变化判断速度；镜头远近、运动方向和跟随程度要与路线一起设计。不为证明“快”强制出画，不用震屏、音效和遮挡主体的效果补救动作。

## 执行入口与实际能力

`scripts/action_expression.py` 是新增的显式作者工具，复用未修改的 S51 速度积分与现有 BoxRig / CSP Builder。不是自然语言导演解算器，不改变旧 S008 / S010 行为。

| 入口 | 输入与输出 | 边界 |
|---|---|---|
| `compile_travel(spec, timebase)` | 平面直线或三次 Bézier 路线、全局帧速度权重、单位／身高、分通道姿态 → 逐帧位置／朝向／姿态与速度报告 | 路线和时间固定后推导实际速度；可用 `peak_speed_range_hps` 拒绝不符意图的方案；不把路径变长以假造速度 |
| `compile_impact(spec, timebase, source_rows)` | 攻击来源／接触事件、水平施力方向、接收方反应速度、起效／滑移／制动窗口、姿态曲线 → 受击后位移与恢复 | 接收方初始静止；来源点必须运动且身份匹配；偏转须有作者理由。不是质量、摩擦、碰撞、平衡或击飞求解器 |
| `full_track(compiled, total_frames)` | 为新候选生成完整同一时间轴 | 只在静止入口／出口补持态；非零速度边界需要连续后继，不自动急停 |
| `patch_csp(...)` | 明确允许角色、锁定通道、能接回原轨迹的局部修改 | 保护入口／出口与边缘速度；不修改摄影、其他角色、道具；使旧审阅结果失效。已登记 LOCKED 仍走 S2；不替代附件／接触／支撑依赖审计 |

`response_kind` 的 RECOIL / SLIDE / BRACED / DEFLECT 是作者意图标签，不自带物理公式。反应差别必须落实在位移、速度、方向、起效时间和身体曲线中。攻击方的阻停／余势／反弹也要在自己的轨迹中明确设计，不凭接收方一条曲线宣称完整碰撞成立。

方向使用世界坐标；角色正面沿运行时局部 +Y，yaw 单位为度。`body_height` 与路线坐标同单位，`meters_per_unit` 显式换算。水平平面可以位于不同 Z，但斜坡、腾空和落地仍使用已有 takeoff/landing、支撑或项目明确采样流程，不投影回地面。复杂多人战术、空中连击、完整人体碰撞不在本次新增能力内。

## 可执行示例

读取 [位移示例](../templates/action-expression-travel.json) 或 [受击示例](../templates/action-expression-impact.json)，替换角色、路线、帧数、尺度和意图。示例数字只用于校准比较，不是题材标准。命令在 skill 根目录运行，沿用现有 Python/jsonschema 环境：

```powershell
python scripts/action_expression.py templates/action-expression-travel.json --output out/move-v001.json
python scripts/action_expression.py templates/action-expression-impact.json --output out/impact-v001.json
```

生成结果的 `rows` 可以写入新 CSP 的 `actor_pose_tracks[actor]`；需要完整静止前后段时调用 `full_track`。同一 CSP 内保留所有角色／道具身份、时间轴、切镜与生命周期，然后使用既有 `combat_sequence_builder.py`，不建立第二套场景 Builder。已有带动画工程继续使用版本副本与项目适配器；禁止直接送到 reset builder。输出文件已存在时工具拒绝覆盖。

姿态通过 `pose_channels` 各自定义帧和值。支持上身 pitch/roll/yaw、下身 pitch/roll、头部 pitch/yaw、compression；每条曲线覆盖整个动作窗口，各通道可错开峰值。缺省通道不凭空生成手脚。身高、身份、常驻 Mesh 数保持原规则。

## 快速动作与连续性诊断

缺省 `boundary_policy: LEGACY_STRICT` 保留旧 C1 失败即拒绝。新设计中有意的短促加速，可显式使用 `AUTHORED_SPEED_ENVELOPE` 并填写来源／意图。此方式仍使用原 S51 光滑速度积分，核对段间位置与速度的精确衔接；**原 S45 的 C1/C2 失败与警告全部保存在 `kernel_evidence`，不改成 PASS，也不降低旧阈值**。

标量曲线解析连续不等于投影后的身体、转向、接触、剪辑已经通过。新路径仍需原生逐帧检查：找位置跳变、意外加速、路线尖点、转向翻转、穿地、穿透、错误接触和缺失恢复。对高加速度诊断说明它对应哪个作者阶段；无法解释或原生证据不符就修正。旧工程的连续性合同不因新工具而失效；这个实验入口不获通用生产 PASS。

## 两种观察视角与证据

先检查正常速度的固定机位或稳定空间参照，再检查最终镜头；已有固定镜头任务无需额外设计正式摄影。不是要求每个交付都增加视频版本，而是在有疑问的动作窗口提供足够证据。

`scripts/action_readability.py::measure_readability` 同时报告世界速度、米／秒、身高／秒、主体画面速度、可见地标的画面运动、主体尺度变化、全身在画内的采样比例。跨 Cut 的样本不算运动；缺失地标不填零或假 PASS。它只给测量值，**不能自动判定有冲击力或导演通过**。UV 数值按画幅归一化，不跨不同画幅直接当像素速度比较。

接触使用 `contact_evidence` 检查保存并重开的 Blender 控制点／目标区域；缺原生证据为 NOT_REVIEWED。它不是网格扫掠碰撞，更不意味着后续没有穿透。查看碰撞前、接触、反应起效、最大退移和恢复，且检查攻击方是否有对应结果。

原生读回可使用 `action_expression_native.py` 和 [绑定示例](../templates/action-expression-native-job.json)。替换 root、Mesh、地标、接触对象及采样区间；脚本读取实际 FPS 与镜头标记，使用依赖图求值，恢复原帧和 Camera，不保存或更改动画：

```powershell
blender -b candidate.blend --python scripts/action_expression_native.py -- --job native-job.json --output out/native-v001.json
```

原生检查脚本本身仅依赖 Blender 与现有脚本；表达编译仍沿用现有 jsonschema 依赖。不要在项目内临时安装或替换 Blender 的 Python 包来掩盖版本不匹配。

针对当前目标选择可区分的对照：同路程不同爆发时间、同来袭不同承受／反馈、同动作固定与跟拍。按项目意图选择范围，不建立通用“越快越好、退得越远越好”的评分。静音并关闭 Shake 后，人物与空间关系仍须成立。技术、原生、视觉抽查、正常速度观感与用户批准分别记录。

## Blender 操作习惯与吸收来源

从 arjun988/blender-skills 的 MCP / animation / physics / QA 中吸收：先读取对象、单位、FPS、活动摄影机、动画数据和约束；小步修改并回读；先验证低成本动作，再处理效果。使用 headless bpy 或 MCP 取决于任务，二者不是动画质量等级。检查实际 evaluated transforms 与保存重开结果，不仅检查写入的关键帧。

不引入整套游戏资产流程、强制 NLA、强制参考视频、固定30fps、固定攻击帧数、默认复杂骨骼或“永远平滑／禁止线性”的规则。逐帧正确的间距可用线性插值重放；盲目给所有动作缓入缓出会抹去爆发差异。物理模拟优先用于确实需要的道具／环境后果，人物导演反馈先用可控轨迹；不把整个角色变成被动刚体。

来源固定到 [8f778d2](https://github.com/arjun988/blender-skills/tree/8f778d2405a214b508d4c7d80742be8e43acdd52)，MIT；本次为概念取舍与本地新实现，未复制第三方执行代码。既有摄影／审阅升级与定稿后交接门禁保持。
