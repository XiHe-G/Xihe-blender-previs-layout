# Combat & Dynamic Motion · 1.7.0

现有 COMBAT_DYNAMIC 模块内的动作表达升级，适用于打斗、追逐、跑跳、腾空、武器、飞行物和冲击。不是第三种顶层模块，不替换 NARRATIVE，不把四件式白模变成复杂火柴人。默认角色、认可视频与新参考证据见 [呈现规范](layout-presentation-standard.md)。

## 默认优先级与工作顺序

**动作可读性 > 屏幕运动轨迹 > Timing/Spacing > Camera Choreography > Action/Reaction > 重量感 > 简化物理合理性 > 精细人体动作。**

优先级用于取舍制作精力：先保证观众看懂，再解决更细的物理和人体表现。它不允许瞬移、无缘由反重力、假命中或跨Cut重置。可用经过设计的夸张距离、停顿和速度差，但必须维持方向、因果与连续性；还原任务由Source控制，原创任务由已批准设计控制。

读取参考或剧情/文字分镜 → **ACTION_BEAT + RHYTHM_MAP** → 连续角色/代理轨迹与环境尺度参照 → Camera意图与运动方案 → 合并全场路线/站位图示确认 → 完整 **COMBAT SEQUENCE PACKAGE** → 同一Builder动画实现与预览 → **八项验收（包含ACTION_READABILITY与SILENT_REVIEW）** → 修订及成片交付。

沿用现有全场路线确认及同版已批准方案，不增加额外审批层。先设计动作/节奏再设计路线与Camera；实现阶段可迭代镜头与动画，但不能为弥补镜头失败而随意改Source节奏。普通文戏工作流不套用此节奏设计门槛。

制作前执行[呈现规范中的五项条件式导演检查](layout-presentation-standard.md)：CAND01、CAND05、CAND08、CAND11、CAND13。记录适用条件、例外与未知，之后沿用以下动作/节奏和CSP流程；这是导演前置检查，不改变Builder。

## 1. 先读Source，再定义动作与节奏

从剪辑、动作、空间三层读取：切点/变速，准备/加速/爆发/命中/余势/恢复，世界方向/屏幕方向/遮挡/Camera。视频动作优先于解释性文字；隐藏角色或接触记为不确定，不编造输赢。区别动画停顿与录屏暂停/缓冲/重复段；不要仅凭重复画面推断表演Hold。

记录源秒数、PTS或时间码、有效唯一动作段、目标fps和帧起点。无变速时 `frame = frame_start + round((source_time - source_in) * output_fps)`；变速使用显式分段映射。不得跨fps复制Source Frame Number。明确半开区间及最后一帧采样约定，避免重复切点帧。

制作前填写 [combat-performance-plan.json](../templates/combat-performance-plan.json)，它是项目动画的设计契约，不会被通用 build_previs 自动执行。

### ACTION_BEAT：逐动作设计

| 字段 | 必须回答 |
|---|---|
| id / actor / target | 谁发动、指向谁或哪块环境，哪个事件触发下一反应？ |
| phase_times | 准备 Preparation、加速 Acceleration、爆发 Burst、命中 Hit、余势 Follow Through、恢复 Recovery，各自源/输出秒区间；未命中写 Near Miss，不适用阶段写null及原因，禁止捏造命中 |
| intent / silhouette | 观众应读到什么；身体长轴、头部朝向、压低/拉长/转体如何表达？ |
| world_path / screen_path | 起点、弧线、拐点、终点、进出画边、屏幕占比；Root与COM谁拥有轨迹？ |
| timing_spacing | 哪里短停、拉开帧间距离、最快、减速；如何避免全程匀速或每个动作等长？ |
| contact / reaction | 命中点、受力方向、接收者响应延迟、击飞/阻挡/擦过、双方余势和下一步趋势 |
| proxies | ACTION_PROXY / WEAPON_PROXY / VFX_MOTION_PROXY的所有者、语义、出现/消失、释放/命中/扩散事件 |
| support / environment | 起跳和落地支撑、掠过参照、遮挡物、击飞距离参照；身体/代理净空 |
| camera_intent | 为此动作服务的Lead/Lag/Catch-up/Impact Reaction/Pull-back或其他Source支持的运动 |
| uncertainty | 哪些是Source事实、导演选择、估计或看不清的部分？ |

### RHYTHM_MAP：整场设计

用事件驱动的 **松—紧—爆—停—再爆** 描述紧张度，而非固定五镜或固定秒数。记录每段区间、张力/速度级别、主导主体、ACTION_BEAT关联、视觉重点、进入/退出触发，以及快/慢/停的对照关系。“停”可以是读动作/蓄势/冲击强调的短窗，不等于所有物体冻结；接收者、碎片或Camera可继续保留余势。Source不存在的再次爆发不强加进去。

先画速度和空间节拍：蓄势的短距离 → 爆发的快速大位移 → 接触后方向改变 → 放开空间 → 恢复到新平衡。不要全局加速来制造爽感。密集变化区增加Root/上下身/头/代理Breakdown；30fps下2–3帧一次可作为起点，命中/释放/切点视需要逐帧检查，稳定区可以稀疏。逐帧烘焙不等于已设计出动作。

## 2. 四件式主体 + 三类语义代理

**COMBAT_BOX_4常驻主体始终是球头 + 上身Box + 单块下身Box + 朝向锥鼻。** 保留稳定ID、身份色、身高、肩宽/厚度、上下身比例、前向轴、无缩放控制层和独立Root/COM、LOWER、UPPER、HEAD通道。四件是主体Mesh数，不是整场总物件数。不要为了增加表达层而调用ARTICULATED或Mixamo替换主体。

| proxy_role | 简单几何与语义 | 生命周期与边界 |
|---|---|---|
| ACTION_PROXY | 长条Box表达出拳、踢击或手臂的方向/扫掠范围；小球表达拳头、施力端或命中位置 | 只在对应动作窗口启用，结束隐藏/回收；用目标、方向、弧线和速度驱动，不制作常驻肩肘腕/髋膝踝关节链 |
| WEAPON_PROXY | 简单Box、杆、锥、Plane或Curve表达剑/刀/枪/棍的长度、朝向、尖端与扫掠范围 | 依据剧情持有→准备→挥动/释放→飞行/碰撞→回收/落地；可跨多个Beat持有，不跟ACTION_PROXY一起无条件消失 |
| VFX_MOTION_PROXY | 球体/简单球簇=元气弹、Impact、Explosion或烟尘；圆环=Shockwave；Curve/Plane=刀气/Slash Arc；Cube Cluster=Debris | 只控制出现时间、起点、方向、速度、扩张、衰减和消失；不做最终流体、火焰、粒子、复杂材质或装饰层叠 |

三类是COMBAT_DYNAMIC内部对象职责，不是新增layout_mode或proxy_style。临时代理已由本规范授权按动作需要使用，不必再逐个询问是否能加手臂；常驻完整肢体/精细人体仍需要使用者明确要求。非必要不生成，不能每个动作都塞满全部代理。

每个代理登记 `id, proxy_role, semantic, beat_id, owner_id, target_id, geometry, space, visible_interval_s, release_s, contact_s, endpoint, clean_visible`。允许只有环境为target；空目标/看不清的目标要记uncertainty。开始前和结束后同时关闭渲染与视口可见性；可见性用阶梯切换，位置/方向/尺度按语义连续变化，防止零尺度或插值导致一闪而过。

命名/集合可用 `ACTION_PROXY/<id>`、`WEAPON_PROXY/<id>`、`VFX_MOTION_PROXY/<id>`；通过自定义属性关联Beat和所有者。控制器、测量标记、调试路径单独放在DEBUG集合。命中小球必须绑定明确事件，不能伪装成角色持续长出的手。

持有时在owner/body或ACTION_PROXY空间；释放前后保持同一世界变换，随后独立沿世界轨迹运动。一个持续存在的武器/Projectile保留同一ID，不在每个Cut重新生成。刀气和武器可分离，但要有清楚的Release。冲击波从确认的起点扩张，爆炸/烟尘留出命中与受力方向的可见窗口，碎片速度和扩散方向服务于力量读懂而非随机遮屏。

## 3. 连续运动、重量与简化支撑

保留已验证的支撑几何、COM近似、弹道、道具所有权、连续旋转和跨Cut检查。地面阶段按实际变换后的下身角/边接触支撑面，不能固定用H/2代替。腾空明确起跳/着地与Root/COM拥有者；使用抛物线近似时记录重力、端点、动作时间与剪辑时间映射。它是布局近似，不是生物力学认证。

LIGHT / AGILE通过低位切换、较短恢复、快速变向和紧贴对方的空间移动表达。HEAVY / POWER通过较大蓄力、同样可以很快的爆发、较大Follow Through及较长恢复表达，不能简单变成慢速角色。体型差由身高、宽厚和上下身比例共同实现。

共享事件链：A接近 → B身体/攻击代理扫入空间 → A压低/绕行 → B余势继续并转向追击 → A利用空间重新定位。双方上一步速度/旋转影响下一步，不拼接独立攻击Pose。临时拳/刀代理要由身体准备、转动或位移支持，不能角色Freeze只动代理。落地遵循支撑→吸收→恢复；脱离保留制动→上身前冲→回正→头部收稳。

Near Miss有净空；Hit有目标区域、时刻、方向和接收者响应。允许为读懂做简化或夸张，但必须标记设计选择。隐藏命中不凭VFX推断结果。保持四元数半球/旋转连续、离画后轨迹、Cut前后世界位置、速度、腾空阶段、身体方向和代理状态。

## 4. 环境是运动尺度参照

按动作至少安排能读懂距离/高度/纵深的参照，而非空背景匀速漂浮：地面表达支撑与投影距离；墙体/门洞表达越过、穿行和擦过；树干/前景遮挡形成视差与高速掠过；平台/落差表达跳跃高度与落地；纵深层次表达击飞距离。使用Source场景或已批准设计，不自动添加城堡、固定角色数量或额外障碍。

前景短时遮挡可以增强速度，关键命中点和攻击者/接收者不能持续被挡。环境/相机/主体三者相对运动必须一致，不用移动整个背景假装完成世界路径。简模环境足够，建模复杂度服从动作可读性。

## 5. Camera Choreography

先依据Beat/Rhythm及屏幕轨迹决定镜头意图，再用已评估角色/代理包围范围验证实际机位、aim、距离和lens。每段记录触发事件、开始/结束秒、目标/前视点、延迟或提前量、最大偏移、速度变化、构图余量及退出/接续方式。

| 逻辑 | 行为与用途 | 防止误用 |
|---|---|---|
| Lead | Camera/构图预留下一运动方向或目标空间，让观众先读到将去哪里 | 不提前泄露不该出现的对象，不固定看向瞬时Root中心 |
| Lag | 主体先起动，Camera延迟响应，产生相对屏幕位移 | 延迟应有限，不丢失攻击关系或关键命中 |
| Catch-up | Lag后有目的地加速追赶，随后减速重新建立构图 | 不瞬移、不恒定追赶导致主体永远跑不出来 |
| Hold | 保持机位或构图张力，允许主体在画内移动/离开中心 | 不把稳定区误加速，也不把技术停帧当节奏 |
| Settle | 追赶/冲击反应后逐渐消除平移和旋转残余速度，落在下一构图 | 不瞬间停住或尾部重复复制静帧 |
| Impact Reaction | 接触后一次有方向的退让、偏转或短暂响应，然后恢复 | 这是可设计的相机运动，不等同随机高频Shake；静音审看时Shake归零，基础反应仍须可读 |
| Pull-back | 接触/击飞/大范围爆发后后撤或扩大景别，展示路径、距离和环境尺度 | 不用纯变焦假装实际后撤；变化方式须匹配Source/已批准意图 |

这些是按事件选用的运动逻辑，不要求每镜全用。Camera保持独立控制，禁止始终机械Parent角色、始终锁死中央或每击必抖。还原任务匹配Source高度、角度、距离、屏幕占比、方向、速度变化与切点；新逻辑不得覆盖已有Source。原创任务用已批准设计选择提前/滞后，参数按场面调整，无固定万能值。

## 6. ACTION_READABILITY_GATE 与 SILENT_REVIEW

这是视觉验收，不是脚本自评或新增用户审批。先完成设计版Gate，再在低成本连续预览与最终成片中执行；未通过先修关系、Timing/Spacing、Camera或必要语义代理，不能靠加细节/音效/Shake掩盖。

**SILENT_REVIEW条件**：音效/配乐静音，所有Camera Shake控制强度为0；仅保留Box主体、环境、ACTION_PROXY、WEAPON_PROXY、VFX_MOTION_PROXY和基础Camera运动。保留有语义的Lead/Lag/Impact Reaction，不强行变成固定机位。不要靠字幕解释动作。

正常速度首次观看必须能直接回答：
1. 谁攻击谁，或主体正在躲避/越过什么？
2. 力量从哪里来、朝哪里去？
3. 准备、爆发、停顿、追击之间速度差是否明显？
4. 轻重角色的体量、余势和恢复差是否成立？
5. 命中点/时刻在哪里；若未命中，擦过距离是否可读？
6. 接收者如何反应，下一步运动趋势是什么？

无目标攻击、单人跑跳等适用性不同的Beat可记N/A，但须说明原因，并验证障碍/支撑/落地方向，不凭空加对手或命中。静音正常速度看不懂而暂停/慢放才能看懂，Gate不通过；慢放仅用于定位问题。逐Beat登记 `PASS / FAIL / NOT_REVIEWED / NA`、证据时间码、问题、修正及复看结论。任一适用关键项FAIL或未审看都不得称已通过。

检查命中前/命中/后连续帧、释放、Near Pass、落地、切点、主体进出画和Recovery尾部；同步检查穿模、支撑缝隙、旋转跳变、代理生命周期、过曝遮挡与Camera构图。工程检查和历史认可不能代替本次视觉判断。

## 7. CLEAN / DEBUG交付

COMBAT_DYNAMIC的CLEAN允许保留承担动作语义的ACTION_PROXY、简单武器、Projectile、Slash Arc、Impact、Shockwave、Explosion、烟尘与Debris。它们属于动作表达，不因叫FX就删掉；纯装饰性复杂FX、控制器、轨迹测量线、调试文字不进入CLEAN。删除某代理若不影响动作理解或明确Source内容，应重新判断它是否必要。夸张代理也不能持续盖住命中与反应。

DEBUG与CLEAN共享同版动作、Camera和时间轴，另显示Beat/Phase、Rhythm、所有者、Root/COM与Camera路径、代理释放/命中/消失及必要端点路径。临时拳/踢击端点标成ACTION_PROXY_PATH，不能标称真实Hand/Foot骨骼路径。相机路径可以俯视小窗呈现。

沿用CLEAN MP4、DEBUG MP4、可编辑.blend、短Review；Source还原任务增加按秒同步对比。Review附Gate和Silent Review结果、实际审看范围、尚存的不确定项与文件新鲜度。未完成的审看必须明示，技术PASS不是艺术通过。禁止意外黑尾、异常停帧、重复尾段及被裁掉的Recovery。

## 8. 统一 COMBAT SEQUENCE PACKAGE 与正式回归

必须读取 [CSP/1.0 共用数据包与八项验收](combat-sequence-package.md)。有参考视频时从Source提取，只有剧情/文字分镜时由Skill设计；两入口共用Shot Plan、Action Beats、Rhythm Map、角色世界/屏幕轨迹、上下身与头部、因果链、武器/道具/VFX生命周期、Camera状态及跨镜Continuity State，然后进入同一个 `combat_sequence_builder.py`。

同一腾空、攻击、受击、飞行物或Recovery在Cut前后保留event_id；同一武器/飞行物保留object_id与所有权。每镜保存中心UV、画面占比、纵深、屏幕运动方向和主要遮挡，近景额外看头朝向、武器尖端和命中点。Camera除了机位，还记录Lead/Lag/Catch-up/Hold/Impact Reaction/Pull-back/Settle的触发、延迟、加减速和退出状态。

正式八项为 **ACTION_READABILITY、CUT_CONTINUITY、TIMING_SPACING、CAMERA_CHOREOGRAPHY、VFX_LIFECYCLE、RECOVERY、SILENT_REVIEW、FILE_RENDER_QA**。ACTION_READABILITY承接既有ACTION_READABILITY_GATE；旧名称可以保留为项目显示名，不另增顶层模块。详细通过条件、适用性和证据格式见共用数据包文档。可见失败不得用NA绕开；片段开始前或结尾后的未知状态必须明示。

两个回归案例及本次运行证据见 [combat-regressions.md](combat-regressions.md)。回归数据是测试夹具，不是新任务场景模板；禁止从中继承雪林/室内、演员数量、镜头数、时长或动作顺序。候选改动只有在两个案例完整重建/渲染且适用检查通过后才合入；失败先修，不覆盖Golden来消除差异。

## 实现边界

BoxRig、原有支撑/质心/弹道与文戏基础原语保持不变。新增的CSP校验器与共用Builder负责消费明确轨迹/姿态/Camera/可见性样本，生成同一全局时间轴的可编辑工程和新帧；不自动读懂剧情，不自动从视频反求三维，不因为填了Lead或Attack就产生合格动画。Agent必须先设计/提取阶段和Breakdown，并完成视觉复核。

源片入口可以从已批准工程抽取状态注册回归；文字入口用同一BoxRig或简单几何资产编写同种采样包。资产文件中的原动画会被清除，再从包重建；不允许复制旧视频充当新结果。通用无手REACH/POINT的限制继续有效，临时ACTION_PROXY登记为独立几何事件，不静默切成ARTICULATED。任何未支持的绑定、变形或数据通道须明确报错或先烘焙为已支持的简单几何表达。


## 1.9：把动作意图落实到可测轨迹

速度与碰撞反馈薄弱时，使用 [动作表达执行与检查](action-expression.md)：先确定世界位移／时长／身高尺度，再设计爆发、制动、双方反应及身体错时，不先添加强震屏或特效。新增可选编译器生成原有 CSP pose tracks，保持同一 Builder、身份与全局时间轴；旧行为不变。固定参照视角与最终摄影共同检查速度感，跟拍居中不能仅凭角色屏幕速度为零判失败。新工具仍是显式作者输入和实验验证范围，不等于任意文本生成成熟打戏。
