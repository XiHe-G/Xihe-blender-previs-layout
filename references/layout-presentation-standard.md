# 两类 Layout 的默认呈现规范 · 1.7.0

本公开版保留既有模型与表现原则，并提供由运行时代码重新生成的匿名模型图。顶层仍只有NARRATIVE和COMBAT_DYNAMIC。它规定默认造型和预演视频的表现目标；不把示例角色身份、人数、场景、时长、镜头数量和具体动作移植到所有项目。

## 选择与优先级

使用者本轮明确模型要求/参考图 > 本项目已批准模型与变体 > 以下默认。新项目未指定时直接采用对应默认，无须为了确认默认造型再询问。已有场景的模型变更须在版本副本上进行。混合文戏与运动戏按主要用途选定一套角色，跨镜保持；不得切镜时自动换模型。

2026-10-28 补充：[可适配制作与审阅规范](adaptive-layout-review.md) 吸收新的项目资料。角色识别、跨镜复用、可选胸腰截幅标记和画面可读性可以迁移；示例项目角色色／无眼睛／无尾巴等属于项目预设，不替换此处通用模型。胸腰标记如被采用，应随真实体块转动与坐姿变化，不得为机位移动标线。审阅格式和下方交付建议已同步更新，既有项目的明确约定优先。

| 项目 | 文戏 / NARRATIVE | 打戏、运动戏 / COMBAT_DYNAMIC |
|---|---|---|
| 默认预设 | NARRATIVE_BOX_5 | COMBAT_BOX_4 |
| 视觉依据 | [图2](../assets/approved-layout-style/narrative-model.png) | [图1](../assets/approved-layout-style/combat-model.png) |
| 常驻主体 Mesh | 球头、横向眼条、锥鼻、一个长方体身体、胸前朝向条，共5件 | 球头、长方体上身、一个长方体下半身、锥鼻，共4件 |
| 身体构成 | 一个整体长方体代表躯干与四肢，不分腰腿 | 上下两块能相对倾斜、压低、扭转，不分左右腿 |
| 默认排除 | 胳膊、手、手指、独立腿脚、服装和精细五官 | 常驻胳膊/手/独立腿脚、复杂关节链、骨骼肌肉细节；动作窗口内可用临时ACTION_PROXY |
| 主要通道 | ROOT路线/转向、BODY姿态、HEAD_CTRL视线/反应 | ROOT/COM轨迹、LOWER支撑/制动、UPPER动势/回弹、HEAD朝向/滞后 |
| 成片重点 | 站位、视线、意图、关系、走停、信息与情绪节拍 | 大轨迹、重心与朝向趋势、双方因果、重量差、速度层次、机位与切镜 |

打开对应模型图后再建模。保持球头与方形身体的轮廓，避免胶囊人、圆柱人、火柴人、复杂机器人等替代默认。每角色一个身份色；白模指几何简化，不要求全白。模型图的具体名字和米数是案例信息，不是通用角色设定。根据新参考保持相对身高、肩宽、胸腔厚度、上下块比例和头身比，重量差不能只改整体缩放。

Root置于底部中心；头部及朝向标记可独立转向。使用无缩放 Empty 控制层，避免非均匀缩放的 Mesh 父子层级产生剪切。公开模型图和通用运行时使用 +Z 向上、yaw=0 朝 +Y；导入正面为 -Y 的其他资产时显式转换，不混用朝向。

**默认服务于 Seedance 等后续生成的布局与动势控制。** NARRATIVE维持原有五件式与表演规范。COMBAT_DYNAMIC的精细手部、摆臂和最终效果留给下游，但动作方向、命中和武器/特效时空关系要在Layout读懂：允许按动作临时生成ACTION_PROXY，武器使用WEAPON_PROXY，效果使用VFX_MOTION_PROXY。它们不替换四件式主体，不构成第三模块，也不需要为每次临时代理再确认。完整关节人/Mixamo仍只在明确要求时启用，动作库不能让库内节拍覆盖Source。

COMBAT_DYNAMIC默认优先级：**动作可读性 > 屏幕运动轨迹 > Timing/Spacing > Camera Choreography > Action/Reaction > 重量感 > 简化物理合理性 > 精细人体动作**。制作顺序、代理生命周期、环境尺度、Lead/Lag/Catch-up/Hold/Impact Reaction/Pull-back/Settle、ACTION_READABILITY_GATE及SILENT_REVIEW集中定义在[现有打戏/运动戏模块](combat-dynamic-motion.md)，打戏任务必须读取。

### COMBAT_DYNAMIC 导演前置检查 · 1.7

仅以下五项作为默认执行的**条件式检查**，不是默认必须发生的动作。两种入口均在细化ACTION_BEAT / RHYTHM_MAP、路线与Camera之前使用：有Source时检验可见因果并标注未知；纯文字时设计因果与选择理由。检查结果写入项目导演Plan，记录候选ID、关联事件、触发条件、采用/不适用/保留未知及理由，再进入原有CSP与同一Builder。不增加审批层，不为满足检查而修改Source或生成新动作。

| 检查 | IF：适用条件 | THEN：导演前置检查 | EXCEPTION：反例与边界 |
|---|---|---|---|
| **CAND01 · 反应交叠** | 对手已承诺防守方向，或支撑/余势暴露可利用空档 | 检查接收者能否在对手余势结束前开始反应；将触发、反应起点及未完成动作写入因果链。有意等待须有剧情或动作读数理由 | 未获得威胁信息、尚无通路、主动对峙或Source明确等待时，允许等待；不能强制所有动作交叠，更不能把未观察到的反击补成事实 |
| **CAND05 · 危险体积与通路** | 攻击、障碍或支撑变化要求角色选择下一路线 | 先标危险范围/扫掠方向、支撑和可用净空，再比较横向、高度、距离或原位防御如何改变攻防关系；用世界路线与屏幕读数验证选择 | 站定格挡、承受冲击或空间无出口可成立；不能预设每击必跳/必闪。仅有屏幕运动时，世界危险体积是待证推断 |
| **CAND08 · 注意力交接** | 画面重点在角色、武器、Projectile、目标或环境后果之间转移 | 保存归属、运动方向、接收端与未完成事件；用屏幕位置/大小、Camera目标和跨镜状态确认观众能接续同一因果 | 近距同框已能读懂时保持同框，不强迫追Projectile或切镜；悬念可暂隐接收端，但须记录未知与后续揭示条件，不伪造明确目标 |
| **CAND11 · 环境约束** | 环境承担支撑、边界、危险、出口、遮挡或距离/速度参照 | 在路线和Camera设计前记录哪些几何改变通路或运动读数；检查移除它是否损失支撑、净空、距离、遮挡或方位信息，保留必要白盒 | 空旷场面不强塞障碍；只提供速度/尺度参照而不改变路线也可保留。无运动读数贡献的装饰不能代替动作质量 |
| **CAND13 · 生命周期适用性** | 武器、飞行物或VFX跨事件、出画或延续至片尾 | 逐阶段区分适用、不适用、不可见及片尾未完成；保留同一对象/事件、所有权、已知轨迹与终态。持有、REST、余摆和继续扩散都可作为合法终态 | 不为填满生命周期强制持续道具消失、爆炸或每镜重生；出画不等于消失，亮起不等于命中，未知阶段不补假事实。精确接触/扩张动力学仍未由此检查认证 |

**CAND13的数据兼容约定**：导演证据可使用 `OFFSCREEN / OPEN_END` 标签；它们不是CSP/1.0运行时阶段枚举。现有阶段仍只用 `APPLIES / NA`：已知适用阶段保留全局区间，确实不适用者填写NA原因；不可见与片尾未完成记在导演Plan/现有provenance说明、生命周期终态及连续性证据中。片尾继续使用 `CONTINUES_BEYOND_CLIP` 的既有终态约定。未知时保留不确定性，不凭空填阶段，也不把不可见机械转为NA。无需新增必填字段、修改schema或Builder。

CAND06（Recovery）、CAND09（语义VFX）只补充既有能力证据；其余候选与Pattern维持参考库，不升级默认规则。证据、反例及未验证边界见[导演研究整合证据](combat-directing-integration.md)。五项检查只作用于COMBAT_DYNAMIC；NARRATIVE、COMBAT_BOX_4和已有八项验收保持原状。

### COMBAT_DYNAMIC 的共用制作数据包

打戏有Source时提取、只有剧情/文字分镜时自主设计同一个 [COMBAT SEQUENCE PACKAGE](combat-sequence-package.md)：Shot Plan、Action Beats、Rhythm Map、角色世界轨迹/上下身姿态/头部朝向、屏幕中心与占比/层次/遮挡、Action/Reaction因果、武器道具轨迹、代理生命周期、Camera Choreography、跨镜Continuity State。之后统一使用 `combat_sequence_builder.py`，不得建立两套互不兼容的还原/原创Builder。视频参考只是检验方法，最终能力仍须服务纯文字自主编排。

正式回归登记见 [两个回归案例](combat-regressions.md)。它们的场景、角色人数、造型例外、镜头数量、时长和具体动作只属于测试资产。默认角色仍是COMBAT_BOX_4；不新增顶层模块，不引入完整人体绑定、Rigify、动捕或复杂模型。文戏规范及运行时保持原状。

准备、压低、加速、峰值、命中/擦过、余势和恢复不能缩成起止Pose。每镜保存屏幕关键状态，每个跨Cut动作/武器/飞行物使用同一事件和对象ID。生命周期按Spawn、Build、Travel、Impact、Expansion、Dissipation记录适用阶段；长期持有道具、未命中和片尾未完成的扩散明确写NA或延续状态，不能捏造消失。

验收正式采用ACTION_READABILITY、CUT_CONTINUITY、TIMING_SPACING、CAMERA_CHOREOGRAPHY、VFX_LIFECYCLE、RECOVERY、SILENT_REVIEW、FILE_RENDER_QA。逐Beat/切点附时间码；静音且Shake关闭后须可读。几何代理可保留语义，但不得提前遮住关键动作。数字一致性不替代视觉判断，已认可案例不等于所有新能力都经过验证。

### 建模入口与动画边界

通用manifest设置 `layout_mode: NARRATIVE` 或 `COMBAT_DYNAMIC`，`proxy_style: AUTO`；角色级 `proxy_style` 可显式覆盖为 `NARRATIVE_BOX_5`、`COMBAT_BOX_4` 或 `ARTICULATED`。未给模式的旧manifest按文戏处理，因此需要重现旧有四肢版本时显式填 `ARTICULATED`。四足类是明确拓扑例外；AUTO保留其四足代理，不把人形模型强套给动物。

`character_proxy.BoxRig` 构建4/5件模型。比例参数为 `width_ratio`、`depth_ratio`、`head_radius_ratio`、`lower_fraction`（运动戏上下身分界）。项目动画可逐采样调用 `apply(state, frame)`，输入 `position`、`yaw`、`body_pitch/body_roll/body_yaw`、`lower_pitch/lower_roll`、`head_pitch/head_yaw`、`compression`。默认位置是底部Root且按该位置Z所在平面补偿贴地；复杂地形必须由项目支撑解算提供准确位置。腾空关闭 `grounded`；若轨迹描述的是质心，另设 `root_is_com: true`，实现使用几何包围体积加权中心近似，不声称人体物理质心。

这些字段是BoxRig采样接口，不是给通用action随意添加字段就会自动生效。通用动作只覆盖基本走停/转头/身体姿态；真实Source匹配的冲刺、跳跃、近身攻防与Recovery必须由项目脚本显式采样。无手模型的通用REACH/POINT仍会报错；COMBAT_DYNAMIC可由项目脚本将其语义实现为独立临时ACTION_PROXY事件，配合身体/头部，或按用户明确要求选择关节模型。不要静默丢掉动作或给manifest填未知字段冒充实现。

## 可迁移的动态呈现原则

原始项目视频及屏幕录制未分发。以下是方法总结，不声称公开包附带原片或已验证所有动作。

1. 位置、身体长轴、上下身与头部朝向共同解释前冲、闪避、腾空和受力，避免直立方块匀速滑行。
2. 准备、爆发、制动和恢复按剧情分配时间；不把某段参考片的秒数照搬成固定模板。
3. 地面、门洞、树干、坡面和前景提供尺度、遮挡及速度参照，复杂背景不是质量保证。
4. 近大远小、斜向构图、主体出入画及景别变化只在已授权意图内使用。动作可读窗口优先于炫目的镜头与效果。
5. 用鼻锥、头部和上下身角度保持朝向可辨；临时动作／武器代理提供力向与空间关系。不能据轮廓猜测隐藏接触，更不能用特效掩盖未成立的碰撞。

公开模型图由 `examples/director_workflow/render_proxy_reference.py` 生成，图中 +Y 为默认运行时正面。它们用于说明几何层级，不是正式角色设定或动作验收证据。

## 成片交付与通过条件

当任务是“制作/优化 Layout 动画”，按请求或项目已约定的组合交付可播放视频与可编辑工程。新项目没有交付约定时，建议 **CLEAN MP4 + DIRECTOR_REVIEW MP4（文件名可用 REVIEW）+ 可编辑.blend／必要资产 + 简短镜表与修改记录**；DEBUG 按技术诊断需要提供，已有 CLEAN＋DEBUG 约定继续沿用。有可读取Source视频且要求还原／对比时，增加按秒同步的 **SOURCE/LAYOUT 对比MP4**。列数、像素布局、画幅、fps和命名按 [审阅规范](adaptive-layout-review.md) 适配；仅资料分析、资产、Skill编辑任务按其本身范围交付，不凭空制作剧情片。分析表、模型图、脚本和.blend都不能代替已承诺的视频。

DIRECTOR_REVIEW：完整原始镜头画幅与常驻本镜说明、必要技术信息、独立对白相结合，跟随切点更新；保持与CLEAN同镜号、同帧数和同节奏。文字在目标播放尺寸可读；可以按项目改变信息区布局，不能靠裁边、拉伸或遮挡主体塞进模板。它与下述DEBUG用途不同。

CLEAN：NARRATIVE保持现有简洁交付规则。COMBAT_DYNAMIC允许保留有动作语义的ACTION_PROXY、WEAPON_PROXY与VFX_MOTION_PROXY，包括Projectile、Slash Arc、Impact、Shockwave、Explosion、烟尘和Debris；不加入纯装饰性复杂FX、调试路径线、文字遮挡或控制器。旧版“纯角色+Camera”标准在打戏中升级为“Box角色+环境+语义代理+Camera”：关闭音效和Camera Shake后仍须读懂攻击关系、力向、速度差、重量差、命中点/未命中以及下一步趋势。

DEBUG：与CLEAN同时间轴、同机位和动作，增加角色ID、源/目标时间码、阶段、ROOT/COM路径、身体/头部朝向与Camera路径。无手脚模型不生成虚假的Hand/Foot骨骼路径；临时代理端点可显示ACTION_PROXY_PATH，并标记Beat、所有者、出现/释放/命中/消失。只有明确的完整肢体变体才显示真实Hand/Foot路径。相机路径可放在独立俯视小窗，避免画外相机路径根本看不到。

同步对比：先标记源唯一动作段、重复尾段、剪辑重映射和源fps，按秒采样对齐，不复制源Frame Number；列明源/目标fps、起点和帧约定。变速须有明确依据，不为“更爽”全局加速。

审看真实连续片段和成片，检查镜头切点前后、最密集动作段、落地/脱离后的完整Recovery。报告模型合规、轨迹与朝向、跨Cut连续、轻重差、动作因果、Camera、快慢对比、Recovery、文件新鲜度及实际审看范围；COMBAT_DYNAMIC附ACTION_READABILITY_GATE与SILENT_REVIEW逐Beat结论，未审看不标PASS。无腿版的“跑动自然”指前倾、起伏、重心与速度趋势成立，不声称验证了真实交替支撑脚或摆臂。
