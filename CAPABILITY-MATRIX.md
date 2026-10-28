# Capability matrix · public 1.9.0

Public packaging note: the registry below includes historical development evidence. Private benchmark fixtures and approval records are not distributed; these rows are not a claim that the public tests reproduce every historical result. Current entry and behavior are defined by SKILL.md; see PUBLIC-DISTRIBUTION.md for scope.

Development snapshot: 1.7.0-SYSTEM-V2. The independent stage registry is [capabilities/production-v2.json](capabilities/production-v2.json), covering historical rows and new interfaces. A schema or synthetic PASS never means LIMITED/STABLE/VERIFIED production capability. Runtime values describe only the stated scope; all new production capabilities remain INTERFACE_ONLY.

Historical rows below retain exact ratings/conditions. Sprint006/007 and Lighting Compatibility Guard remain EXPERIMENTAL. Accepted perception/control/support/momentum/intensity/takeoff/contact remain LIMITED. NOT_REASSESSED is not a downgrade or an invented YES. No new human/director/downstream approval was obtained.

| Capability | Maturity | SPEC_DEFINED | RUNTIME_IMPLEMENTED | PROJECT_TESTED | NATIVE_VALIDATED | DIRECTOR_APPROVED | DOWNSTREAM_VALIDATED | Runtime scope |
|---|---|---|---|---|---|---|---|---|
| PRODUCTION_ROUTE | INTERFACE_ONLY | YES | YES | NO | NO | NO | NO | Explicit routes/primary owner and no-sidecar fallback; no semantic text classification |
| PRODUCTION_SCENE_STATE | INTERFACE_ONLY | YES | NO | NO | NO | NO | NO | Schema and structural validator; no native snapshot extractor |
| REVISION_DEPENDENCY | INTERFACE_ONLY | YES | PARTIAL | NO | NO | NO | NO | Read-only transitive query; no automatic patch or completed audit |
| SCENE_DIRECTOR | INTERFACE_ONLY | YES | NO | NO | NO | NO | NO | Objectives/beats/shot decisions contract only |
| NARRATIVE_DIRECTOR | INTERFACE_ONLY | YES | NO | NO | NO | NO | NO | Behavior and reaction/decision/hold contract only |
| CAMERA_SEMANTIC_COMPILER | INTERFACE_ONLY | YES | PARTIAL | NO | NO | NO | NO | Explicit constraint packet and subset validation; no prose solver or lowering |
| COMPOSITION_CONTRACT | INTERFACE_ONLY | YES | NO | NO | NO | NO | NO | Screen-space contract; native solver/validator not added |
| IDENTITY_PROXY_V2 | INTERFACE_ONLY | YES | NO | NO | NO | NO | NO | Proportion/anchor schema+validator; no mesh generation |
| SIMPLE_HAND_PROXY | INTERFACE_ONLY | YES | NO | NO | NO | NO | NO | Simple anchor relations only |
| PHYSICAL_BEHAVIOR_PROFILE | INTERFACE_ONLY | YES | NO | NO | NO | NO | NO | Relative profiles validated; no parameter mapping |
| LOCOMOTION_PROFILES | INTERFACE_ONLY | YES | PARTIAL | NO | NO | NO | NO | HUMAN references existing Sprint008 only; other runtime absent |
| MOTION_DECISION_LAYER | INTERFACE_ONLY | YES | NO | NO | NO | NO | NO | Intent vocabulary only; no autonomous action decision |
| PROP_INTERACTION_PROFILE | INTERFACE_ONLY | YES | NO | NO | NO | NO | NO | Constraints and schema; existing control remains separate |
| KINEMATIC_IMPACT_RESPONSE | INTERFACE_ONLY | YES | NO | NO | NO | NO | NO | Authored candidate validation; no response solver |
| VFX_PREVIS | INTERFACE_ONLY | YES | NO | NO | NO | NO | NO | Typed semantic/geometry/light interface; no new effects runtime |
| LIGHTING_CONTEXT | INTERFACE_ONLY | YES | NO | NO | NO | NO | NO | Preflight contract and scoped authorization routing only |
| SCENE_BUILD_UPGRADE | INTERFACE_ONLY | YES | NO | NO | NO | NO | NO | Five production scopes; old scene builders unchanged |
| DELIVERY_MANIFEST | INTERFACE_ONLY | YES | PARTIAL | NO | NO | NO | NO | Hash and declared-version compiler; no native render provenance inference |
| AI_VIDEO_HANDOFF | INTERFACE_ONLY | YES | PARTIAL | NO | NO | NO | NO | Data packaging/cut-version checks; no provider execution |
| PRODUCTION_PLAN_VS_ACTUAL | INTERFACE_ONLY | YES | NO | NO | NO | NO | NO | Scene comparison interface; old S3 checker unchanged |

---

## Historical accepted matrix — verbatim, status vocabulary below applies to history

# CAPABILITY MATRIX · 1.7.0 基线 / S3 附加层

状态仅使用 VERIFIED、LIMITED、EXPERIMENTAL、NOT_IMPLEMENTED。VERIFIED 必须按该行条件解读；失败案例不作正例证据。历史画面审查与本轮技术复跑分开。

| Capability | Module | Status | Evidence | Conditions | Known Limits | Last Verified Version |
|---|---|---|---|---|---|---|
| NARRATIVE_BOX_5 与 COMBAT_BOX_4 默认结构 | BOTH | VERIFIED | 原有 smoke_box_presets.py 本轮 PASS | 默认参数与受测三种尺寸 | 显式旧项目变体不自动改成默认模型 | 1.7.0 |
| 文戏 manifest 解析、现有动作构建、保存 | NARRATIVE | VERIFIED | NAR-SH13-26 fresh build + saved-blend-open-audit | 现有七角色/144帧基线 | 本轮未重新审片；不是任意文本导演成熟证明 | 1.7.0 |
| CSP/1.0 解析、共同 Builder、保存、评估导出 | COMBAT_DYNAMIC | VERIFIED | CDR-003/004 重建共892帧，误差0 | 已显式采样的动作/Camera/几何 | 不自动从动作名称求轨迹 | 1.7.0 |
| 单 Projectile 跨镜身份与轨迹连续 | COMBAT_DYNAMIC | VERIFIED | CDR-003 同一球、8镜重建；S35 Native ID/Owner登记、错误Owner/未脱离检出 | 显式完整轨迹与生命周期；Native登记证据检查为LIMITED技术扩充 | 任意复杂多 Projectile 相互作用未验证 | 1.7.0 |
| 已登记木条群持续ID与同剑取回 | COMBAT_DYNAMIC | VERIFIED | CDR-004 15镜重建 | 指定12条木条/持久剑与明确采样 | 仅此冻结群体案例；不是通用群体解算 | 1.7.0 |
| 同一次腾空跨Cut、身体/头部状态保持 | COMBAT_DYNAMIC | VERIFIED | CDR-003/004 world/state/continuity逐值比较 | 原批准简化角色、明确pose tracks | 无精细人体接触/步态认证 | 1.7.0 |
| 已有Camera执行数据与镜头Cut保真 | COMBAT_DYNAMIC | VERIFIED | CDR-003/004 Camera/lens/screen零差异 | 原始Camera采样与Cut固定 | 不证明自动选择机位/节奏正确 | 1.7.0 |
| 现有武器/语义VFX代理生命周期重放 | COMBAT_DYNAMIC | VERIFIED | 两正式CSP全部proxy_lifecycles与tracks比较 | 冻结生命周期、可见区间、ownership | 雪林扩散后完整露人Recovery未认证 | 1.7.0 |
| 既有场景渲染续跑与文件新鲜度 | BOTH | VERIFIED | 既有6帧 smoke_existing_scene 四分支 PASS | 原有固定微型回归场景 | 仅技术文件保护，不是画面艺术通过 | 1.7.0 |
| Clean/Debug/Blend历史交付链 | BOTH | VERIFIED | 既有正式MP4与工程指纹；历史V1.7结果 | 已有批准案例/冻结产物 | 本轮只重建动画，未重渲整片 | 1.7.0（历史渲染+本轮指纹） |
| AG校验与两正式案例CSP语义编译等价 | COMBAT_DYNAMIC | VERIFIED | 26新增测试；2正式Graph迁移；fresh Builder数据比较 | 显式绑定执行sidecar | 不从意图自主生成运动；V02批准范围见S0-S1-CLOSEOUT-REPORT.md | 1.7.0 + S1 AG/1.0 |
| 纯文字自主设计成熟整场打戏 | COMBAT_DYNAMIC | EXPERIMENTAL | 候选自评与明确Director Fail并存 | Codex逐案编写方案/轨迹 | V02已获限定范围批准；不代表通用成熟，不作VERIFIED | 未获通用验证 |
| Camera意图/节奏的自主导演选择 | COMBAT_DYNAMIC | LIMITED | 参考重建已验证；自由设计缺独立成功集 | 已给参考/明确分镜时更可约束 | 不保证所有Lead/Lag/Catch-up等状态的自主调度 | 1.7.0证据边界 |
| 接触、重量、Recovery判断 | COMBAT_DYNAMIC | LIMITED | 正式回归场景与既有文字审查 | 简化白盒与显式接触链 | 无成熟生物力学；雪林片尾被特效遮挡 | 1.7.0证据边界 |
| 通用文戏跨镜连续与复杂互动 | NARRATIVE | LIMITED | 通用Builder每镜重置；existing-scene辅助流程 | 需要显式共享场景或继承状态 | 拼接不自动产生连续性 | 1.7.0证据边界 |
| Seedance动作/空间/镜头控制收益 | DOWNSTREAM | EXPERIMENTAL | 有下游用途规范，无正式A/B实验 | 可作为参考输入 | 没有DOWNSTREAM_VALIDATED结论 | 未验证 |
| 自动视频跟踪/3D运动恢复 | COMBAT_DYNAMIC | NOT_IMPLEMENTED | 当前源片手动分析+显式采样 | 不适用 | 不是自动求解器 | 不适用 |
| AG→NARRATIVE执行 lowering | NARRATIVE | NOT_IMPLEMENTED | Compiler明确拒绝 | 本轮只冻结旧文戏链 | Schema可表达不等于执行已实现 | 不适用 |
| AG Partial Recompile | COMBAT_DYNAMIC | LIMITED | TEST A/B/C、零无关变化、原Builder重建与重开 | 显式依赖/所有权索引、固定拓扑、作者提供局部lowering | 非自动动作生成；仅三项技术修改题 | 1.7.0 + S2 |
| AG Override LOCKED通道保护 | COMBAT_DYNAMIC | LIMITED | CDR-003人工Camera跨重建0误差；故意冲突正确拒绝 | 明确登记执行快照、工程指纹和保护selector | 非任意Rig/约束通用锁；不自动发现手改 | 1.7.0 + S2 |
| Repair Feasibility Preview | COMBAT_DYNAMIC | LIMITED | S45 F1/F2；R1 Lens提前检出F203–207出画；三候选隔离测量、431对象保护指纹 | 指定Camera配方、原S3.5阈值、有限六项耦合 | 不选优、不授权；任意参数与未登记意图不保证；遮挡为估计 | 1.7.0 + S4.5 |
| Motion Boundary Validation | COMBAT_DYNAMIC | LIMITED | S45 F3/F4；R4 C1/C2 FAIL、Root A FAIL / B PASS、事件授权测试 | 显式fps/尺度/边界及守护采样；TECHNICAL_DEFAULT相对阈值 | 非解析连续时间保证；无证据C0不判PASS；Jerk无普遍硬门槛 | 1.7.0 + S4.5 |
| Human-approved Repair Loop | COMBAT_DYNAMIC | LIMITED | S4五份真实用户Decision、原S2局部合并、五工程重建/重开/Trace、SHA收据；R1 NOT_FIXED、R2–R5 FIXED | 指定五类故障、明确scope、作者提供单轮lowering；162测试及零无关变化 | 不保证修复成功；R1出画失败；R4边界速度不作光滑认证；不是自主修复 | 1.7.0 + S4 |
| Execution Primitive Runtime | COMBAT_DYNAMIC | LIMITED | S51 六个原 Builder fixture，225 测试，Native Trace / C0/C1 / 重开一致 | 显式参数、统一时间、固定通道；仅技术 fixture | Runtime本体只接显式Primitive；作者映射见S5.2行；非任意动作/复杂 Rig | 1.7.0 + S5.1 |
| Motion Primitive Kernel | COMBAT_DYNAMIC | LIMITED | 六个通用 Motion、独立轨迹/Owner、Recovery、组合与拒绝测试 | 合同可满足的路径/速度参数；C1 不通过则拒绝 | 尖角不自动修平；C2 记录且有 WARNING；非武术动作库 | 1.7.0 + S5.1 |
| Camera Primitive Kernel | COMBAT_DYNAMIC | LIMITED | 六个 Camera Primitive；S3.5 原 Hold/Lag/Catch-up/Reframe 检查 | 已知目标轨迹、投影模型、显式构图目标 | 非摄影艺术选择；任意父链/遮挡/多主体需另验 | 1.7.0 + S5.1 |
| Author Event → Primitive Lowering | COMBAT_DYNAMIC | LIMITED | S52 固定9类规则、5个Native链、缺信息/ATTACK拒绝、267测试；State Chain/C0/C1 | 明确机器可读数量、完整入口/目标/时序及来源 | 非任意自然语言；ATTACK等不支持；ENTER/EXIT本轮为单元证据 | 1.7.0 + S5.2 |
| Camera Intent → Primitive Lowering | COMBAT_DYNAMIC | LIMITED | S52 六类规则测试，FOLLOW→CATCH_UP Native Checker PASS | 明确行为/profile/主体/关系和批准入口状态；复用S51 | 不推导艺术机位；裸HOLD/缺目标停下；其余映射无新增Native剧情 | 1.7.0 + S5.2 |
| Prop Control Continuity | BOTH | LIMITED | Sprint003 两个 Native 原型 + 两个 Benchmark 道具专项；357 测试，CDR 数值零差异 | 显式事件、代理控制点、接触 dwell、平移保持、release/place；CSP 单一时间轴 | 无 IK/支撑/动量；控制权 transfer 只有单元证据；完整 Benchmark 仍 FAIL | 1.7.0-AUTODEV-S003 |
| Support Contact | BOTH | LIMITED | AUTODEV S004: 3 Native prototypes + 2 support slices; 379 tests; CDR numeric equality | CSP support samples, transition IDs, finite cuboid contacts, proxy body support and controller dependency | No IK, gait, momentum, force/COM solver or landing; LOST_SUPPORT unit-only | 1.7.0-AUTODEV-S004 |
| Automatic Repair | BOTH | NOT_IMPLEMENTED | S2明确排除 | 不适用 | 不自动重设计动作/Camera/节奏 | 不适用 |
| Plan-vs-Actual Checker | COMBAT_DYNAMIC | LIMITED | S3/S35三既有案例、八项破坏检出、Hold校准、Native证据与充分性分级 | 明确可测声明、Mesh代理、逐帧运行数据 | 非像素精确/生物力学/艺术评分；缺Native Owner/未知意图不判PASS；严重裁边仅WARNING；不做自动修复 | 1.7.0 + S3.5 |
| Blender人工改动自动回写Author Graph | BOTH | NOT_IMPLEMENTED | 本轮采用显式登记策略 | 仅显式抽取已知Camera通道 | 不自动理解任意关键帧/导演意图 | 不适用 |

V02新增证据：USER_APPROVED TEXT-ONLY COMBAT CANDIDATE，仅限9镜结构、构图/机位景别、主运动方向、Timing/Cut/节奏转译。纯文字自主成熟打戏仍为EXPERIMENTAL。

S4工程Gate PASS / LIMITED：五个用户批准技术Repair各执行一次，R1 NOT_FIXED、R2–R5 FIXED；失败保留并停止，不自动重试。详见S4-FINAL-REPORT.md。Automatic Repair仍NOT_IMPLEMENTED。

S4.5 PASS / LIMITED：新增只读预览和边界诊断，R4历史几何FIXED保持、Motion Quality另报FAIL；未执行新Repair。详见S45-FINAL-REPORT.md。

S5.2 PASS / LIMITED：五个真实 Lowering 链、两个不执行的负向样例；267 项回归 PASS，C0/C1 PASS、C2 WARNING 保留。Builder / AG / S51 内核及正式 Benchmark 指纹保持。等待人工审核，未进入 S5.3。


S5.3 集成试验：ENGINEERING FAIL，INTEGRATION_PILOT_ONLY，非正向Benchmark。新文戏首遍Event READY 2/8、Combat 1/9，均仅静止建立事件；C1拒绝主要运动，动态LOOK/Camera/Recovery受依赖阻塞。未升级任何能力状态。275测试PASS仅代表旧回归未退化，不能替代连续场景成功。证据见 S53-FINAL-REPORT.md、S53-PILOT-GAP-MATRIX.md。S5.2末尾“未进入S5.3”为当时停止点的历史记录。


S5.3R（2026-09-20）：合同稳定化专项证据 LIMITED。显式起停语义、near-zero包络、时间对齐和Evaluation DAG恢复原Pilot基础运动；不提升为通用VERIFIED。N Auto 6/8，Narrative Technical仍FAIL（B转身/发现与5项屏幕方向）；C Auto6/9，Combat Foundation PASS / LIMITED，完整Combat仍FAIL / UNSUPPORTED GAP，B_LOOK角速度仍失败。已执行片段C0/C1通过，C2 WARNING/FAIL保留。290测试PASS，11个S51/S52既有fixture执行采样逐值一致。原Benchmark与S53失败证据不变。参见S53R-FINAL-REPORT.md。Automatic Repair仍NOT_IMPLEMENTED，纯文字成熟导演仍EXPERIMENTAL；不新增ATTACK/BLOCK能力。

S5.3R2（2026-09-20）：Orientation / Attention / Screen-Space Preflight 为 LIMITED 技术证据。Narrative R2 支持事件 8/8 自动 Lower，Head→Body attention split、5项屏幕合同修订、C0/C1 和 Angular C0/C1 通过；Combat 支持事件 6/9 自动 Lower，Approach/Dodge/Pursue/Exit/Recovery通过，B_NOTICE保留 angular C1 failure，ATTACK/BLOCK仍UNSUPPORTED。R2 Pilot-only，未加入正式 Benchmark；Builder 与 AG Schema 未修改，项目专用运动代码 0%。Plan-vs-Actual、Dynamic Look、Screen Direction 仍 LIMITED，不升级为通用 VERIFIED。


AUTODEV Sprint 001（2026-09-21）：Screen Direction Preflight 防误通过已按技术微原型验证，LIMITED。HOLD_REGION 要求显式区域并复用原S3.5 Checker；径向方向、缺采样、出画中心证据不足返回NOT_REVIEWED。285原测试+23新测试=308项本轮实跑PASS；CDR-003/004 fresh build/reopen/render数值零差异；S51六项、S52五执行+两拒绝fixture通过。Builder、AG、Motion/Camera Runtime及既有Benchmark未修改。AUTODEV基础设施与代码候选ACCEPT；LAST_BUS/RUNAWAY_CART只提供名称、缺剧本验收，尚未执行，整个Sprint未宣告完整PASS。历史S53R2部分字面量fixture结果不作新正向证据。Automatic Repair仍NOT_IMPLEMENTED；本轮开发缺陷修复不等于动画自动修复。证据位于工作区 AUTODEV/sprint_001/SPRINT_001_REPORT.md。


Sprint 001闭合补记：用户后续提供两组1.0完整定义，STOP D已解除。LAST_BUS与RUNAWAY_CART均已用冻结Runtime真实执行、保存重开、Trace、低清Preview；Runtime PASS而完整Benchmark均FAIL，作为负向Baseline保留，不是正向成熟证据。文戏暴露移动察觉/道具接管/坐姿支撑缺口；运动戏暴露抓取控制/支撑/动量传递/尾声释放缺口。新能力评级不变。整体自主研发工程闭环完成，Screen Direction Preflight候选ACCEPT / LIMITED。


AUTODEV Sprint 002（2026-09-21）：PERCEPTION_REACTION_CAUSALITY 从缺失可执行触发接口提升为 LIMITED。显式作者触发 / 无遮挡上下文下的世界距离与朝向锥条件，经已求值目标证据解析首次察觉，再派生延迟和带引用的响应窗口；复用 S51 与既有 CSP causal_links。两个微原型及 LAST_BUS / RUNAWAY_CART 因果专项实测 PASS。完整 Benchmark 均仍 FAIL；道具、抓取、支撑、动量与导演艺术质量未通过本轮验证。308 旧测试 +25 新测试=333 PASS；CDR-003/004 7,932,404 数值零差异。仅新因果编译/验证器与旧 Narrative 的 opt-in S51 位置适配；Geometry Builder、Motion/Camera Kernel、AG/CSP Schema、Sprint001 Screen Preflight 均不变。三个有根因证据的修复后停止，非生产 Automatic Repair。版本仍1.7.0；详见工作区 AUTODEV/sprint_002/SPRINT_002_REPORT.md。


AUTODEV Sprint 003（2026-09-21）：PROP_CONTROL_CONTINUITY ACCEPT / LIMITED。FREE / CONTACT_PENDING / CONTROLLED / RELEASING / PLACED 落入既有 CSP object state，接触和失败不授予 controller；显式接管、释放、放置及跨技术 Cut 状态通过 Native 验证。333 旧测试 +24 新测试=357 PASS，CDR-003/004 7,932,404 数值零差异。Builder 只新增可选离散 custom-property 状态回写/读取，未改几何和旧 TRS；CSP 验证器允许现有 baked scene_asset 的 Narrative replay，不提供新 Narrative actor lowering。Perception / Reaction 与 Screen Preflight 保持。两个完整 Benchmark 仍 FAIL，首次追车尝试没有接触，动量/支撑/票/门/尾声掉箱未解决。正式版本1.7.0，未进入 Sprint004。


AUTODEV Sprint004（2026-09-21）：SUPPORT_CONTACT ACCEPT / LIMITED，仅限简化代理的可解析支撑状态、表面接触、显式承重转移、对象控制的身体支撑依赖。三个原型与 LAST_BUS / RUNAWAY_CART 身体支撑专项通过；357旧测试+22新测试=379 PASS，CDR-003/004 7,932,404数值零差异。Prop Control、Perception / Reaction保持。完整Benchmark仍FAIL，导演质量待审。坐姿为压缩代理；绿色支撑连接不是解剖腿、足底锁定或IK，权重不是受力解算。Builder仅新增可选离散metadata持久化，几何/运动/Camera核心及AG不变。正式版本1.7.0，未进入Sprint005。


### AUTODEV Sprint005 — MOMENTUM_TRANSFER

ACCEPT / LIMITED, development snapshot `1.7.0-AUTODEV-S005`; formal version remains 1.7.0. Three native prototypes plus two benchmark slices, 403 tests (379 previous + 24 new), CDR-003/004 7,932,404 values zero difference. Supports explicit contact-caused velocity ramp, controlled co-deceleration, residual motion and root recovery through existing RECOVERY_PROFILE. Requires S003 control and S004 support evidence. No physical momentum conservation, mass/friction, IK, gait, falling, landing, Attack/Block or downstream generation. Full benchmarks remain FAIL; director quality PENDING_DIRECTOR_REVIEW. Builder, AG and motion/camera kernels unchanged.


### AUTODEV Sprint006 — CONTACT_RESPONSE_READABILITY

ACCEPT / EXPERIMENTAL, development snapshot `1.7.0-AUTODEV-S006`; formal version 1.7.0. Optional CSP phase contract, native contact witness projection/occlusion, visible causal interval and result displacement. Three micro diagnostic gates PASS; LAST_BUS objective slice PASS; RUNAWAY_CART first failure and second control/response visual slices FAIL. 429 tests (403 old + 26 new); CDR native regression zero difference. Technical default thresholds lack independent human calibration. No Camera Director, IK, collision/dynamics or combat contact. Full benchmarks remain FAIL; human readability PENDING_DIRECTOR_REVIEW.


### AUTODEV Sprint007 — CONTACT_WITNESS_CALIBRATION

ACCEPT / EXPERIMENTAL; formal version 1.7.0, snapshot 1.7.0-AUTODEV-S007. Isolated OFAT study: 44 native Blender previews, mechanical positive/negative discrimination, frozen-motion verification and blind R1–R5 packet. Human review PENDING; CONTACT_RESPONSE_READABILITY remains EXPERIMENTAL. Existing thresholds unchanged; no human-calibrated envelope. 447 tests PASS; CDR-003/004 7,932,404 values zero difference. No formal Camera, Builder, AG or motion kernel changes.


### AUTODEV Sprint008 — MOTION_INTENSITY_ACTION_TREND

ACCEPT / LIMITED, snapshot `1.7.0-AUTODEV-S008`, formal version 1.7.0 unchanged. Explicit relative speed profiles and global-frame phases reuse S51; ordinary body pitch/roll trends, fixed-Camera native evidence and six trend diagnostics. 13 prototype clips, Cart intensity slice PASS and Last Bus unchanged protection PASS. Raw Cart C2 FAIL/WARNING retained; C0/C1 pass existing S53R authored-start semantics. 474 tests PASS; CDR-003/004 7,932,404 values zero difference. Human/director recognition PENDING; full benchmarks remain FAIL. S006/S007 stay EXPERIMENTAL; contact witness refinement deferred by user; no new gait/IK/physics/Camera or downstream generation.


## Sprint008 lighting compatibility addendum (2026-09-26)

Read-only `scripts/lighting_compatibility.py` compares native global-frame states; see [contract](references/LIGHTING-COMPATIBILITY.md). It does not create lighting, change motion/Camera, or authorize a plan. No Lighting Previs requirement/presence: NOT_APPLICABLE with no additional confirmation. Changed dynamic geometry/motion invalidates prior test review; protected lights/exposure/Camera changes require review. Missing evidence stays NOT_REVIEWED.

Guard maturity: EXPERIMENTAL. Existing Door/Night project tests are scoped state-compatibility evidence, not proof of a general Lighting Previs runtime. Sprint008 motion remains LIMITED; Sprint006/007 readability remains EXPERIMENTAL. Version remains 1.7.0. Regression: 488 tests PASS; CDR003/004 7,932,404 numeric values, zero difference. Human/director approval is not inferred.


## Sprint009R — support release clearance (2026-09-26)

TAKEOFF_LAND_TRAJECTORY: ACCEPT / LIMITED, opt-in. Formal version remains 1.7.0; development snapshot 1.7.0-AUTODEV-S009R. Load [support release clearance](references/SUPPORT-RELEASE-CLEARANCE.md) for explicit standing/running jump or passive edge departure. The rejected S009 candidate was not restored unchanged. Passive Drop now requires native body-clearance preflight and saved/reopened geometry verification; support weight zero alone is insufficient. Scope: fixed box witnesses, planar supports, linear translation; unresolved geometry stays NOT_REVIEWED. Changed landing timing/target requires author approval.

Evidence: 3 clearance micros; original Drop and Benchmark Drop repaired under explicit user-approved retiming; active jump protection; 535 tests PASS; CDR003/004 7,932,404 values zero difference. C0/C1 PASS; C2 FAIL retained. No Builder/AG/motion-kernel/Camera-kernel changes. Contact readability/calibration remain EXPERIMENTAL. Human review PENDING; no combat, IK or physical simulation claim.


## AUTODEV Sprint010 — ATTACK_BLOCK_CONTACT_INTENT

ACCEPT / LIMITED; formal version 1.7.0, snapshot 1.7.0-AUTODEV-S010. Load [Combat intent](references/COMBAT-INTENT.md) for explicit simplified one-to-one attack/block/evade/hit/miss contracts. Existing AG automatic ATTACK/BLOCK mappings remain unsupported. Fixed-axis committed proxy routes compose existing perception, control, support, momentum and intensity primitives; no kernel changes. Four native micros and a 15-second three-beat benchmark pass scoped mechanical gates. 567 tests PASS (535 old + 32 new); CDR003/004 7,932,404 values zero difference. C0/C1 PASS; C2 FAIL retained. Human comprehension/director quality PENDING. Sprint006/007 remain EXPERIMENTAL. No full-combat, IK, physics, Camera intelligence, Lighting, VFX or downstream video-generation claim.


## 1.8.0 local upgrade overlay — 2026-10-11

Historical rows and failures above are unchanged. New evidence lives in the local upgrade receipt.

| Capability | Current evidence/status | Limitation |
|---|---|---|
| Story-first directing | Workflow and local-case rules; two independent text-origin toy fixtures | Codex-authored, not NLP/animation compiler; no blind artistic generalization pass |
| Explicit camera/Cut adapter | Native saved/reopened fixtures, evaluated matrices and cut IDs | Fixed focal per shot, new unparented cameras, complete plan only |
| Path/aim/time separation | Promoted independent Python tests and native straight/static samples | Arcs require intent review; fixed position does not imply good framing |
| Persistent revision dependencies | Independent tests for local/global/persistent/reset/captions | Declared dependencies, not complete automatic Blender graph analysis |
| Finite repair loop | Persistent single-writer ledger; rename cannot reset limit | Execution orchestration still agent-owned |
| Encoded evidence | Actual 480p MP4 decode, scheduled extraction and hashes | Extraction is not full-speed viewing or director approval |
| Combat/contacts/hand detail | Existing accepted core preserved; strict CDR regression | Toy bypass is not a contact-fight acceptance; detailed hand/gait/expression remain LIMITED |
| AI handoff | Existing contract plus practical evidence mapping | No Seedance generation or transfer-quality acceptance |

## 1.8.1 directing and review guidance — 2026-10-28

| Addition | Status | Boundary |
|---|---|---|
| Story/photography decision methods | Agent guidance with source/page trace | No autonomous runtime, lens optimizer, automatic focus or emotional-quality certification |
| Adaptable shot tables and review presentation | Workflow and optional human-readable templates | No new compositor/template renderer or schema fields; use existing tools with explicit parameters |
| New-project review delivery recommendation | Documentation default; existing project agreements preserved | Same-frame and actual-media validation still required; not evidence of a newly rendered film |

Runtime, adapters, schemas, tests and benchmarks retain their prior capability status. Source study and documentation checks do not convert historical failures, NOT_REVIEWED results or pending director/downstream acceptance into PASS.


## 1.9.0 ACTION-EXPRESSION — explicit opt-in runtime

| Capability | Maturity | Implemented scope | Evidence and limits |
|---|---|---|---|
| ACTION_EXPRESSION_TRAVEL | EXPERIMENTAL | Grounded linear / cubic Bézier route, authored speed weights + global frames, explicit scale, tangent/fixed facing, independent Box pose channels | New numeric tests and fixed/follow/turn native micro-cases; no autonomous semantic calibration, gait, flight or general character physics |
| ACTION_EXPRESSION_IMPACT | EXPERIMENTAL | Named source/contact, arbitrary horizontal direction, stationary receiver rise/coast/brake, independently timed body channels | Light/strong contact-point micro-cases; authored response speed, no mass/friction solver, exact mesh collision or full fight approval |
| ACTION_EXPRESSION_REVIEW | EXPERIMENTAL | World/body-normalized/image/landmark/scale measurements, cut exclusion, explicit contact witness, guarded rejoining CSP pose patch | Measurements are not artistic PASS. Native save/reopen and encoded delivery tested; normal-speed director approval remains pending |

1.8.1 photography/review methods, final goal/authority/handoff and all legacy scripts/schemas remain unchanged. Short authored speed envelopes preserve raw S45 C1/C2 failures; exact scalar knot continuity is separate evidence, not a relabeling of the old checker. Old automatic Physical Profile / Kinematic Impact Response interface ratings remain as recorded. Full text-to-combat maturity and downstream AI benefit are not promoted.
