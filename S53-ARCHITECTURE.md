# S5.3 Architecture

正式版本：1.7.0。INTEGRATION_PILOT_ONLY；SELF_REVIEW，非 USER_APPROVED。

执行链：新故事 → 冻结 Director Plan → AG/1.0 → 原 S52 Lowering → 请求/显式补充/模拟决定 → 原 S51 Primitive Runtime → 原 Fragment Merger → CSP/1.0 → 原 Builder → 保存/重开 → Native Trace → 原 S35 Checker / S45 Boundary → 诊断影片、自审与 Gap。

完整图非 READY；为保留现场证据，只把已有 READY、Boundary PASS 的片段放入显式诊断子集。完整图、拒绝片段和全部未解决 Event 不删除。此子集不是完整图编译成功，也不是绕过 C1 去执行拒绝片段。静态入口资产和缺失动作在影片中保持可见。

Narrative 使用 NARRATIVE_BOX_5 静态资产（原 BoxRig，建立入口姿态后清除动画）；Combat 使用 COMBAT_BOX_4。原 Builder 的 scene_asset + 普通 object_tracks 接口可执行这些对象。CSP 的既有 layout_mode=COMBAT_DYNAMIC 只是该入口的协议要求，不能据此宣称一般 AG→NARRATIVE 执行已实现。没有改 Builder 或角色结构。

参数/场景/渲染/测量编排位于 staging/tooling；没有运动函数、Camera 曲线或直接项目关键帧实现。沿用 S52 测试辅助的 JSON 构造器，部分 graph/source 命名保留 S52 前缀；故事、角色路线和图是新建的，不是拿旧 fixture 充当 Pilot。

所有原算法保持原 SHA，包括 Lowering、Primitive、Builder、AG Schema、Checker、Boundary。恢复建议只读生成；无 Decision/Changeset/Patch 执行。C2 记录，C1 不过则拒绝。

局限：当前完整运动链被拒绝，安全子集只提供静态诊断片。1×静音播放两遍是在浏览器完整播放并间隔取帧核查，不冒充人类持续视觉审片。相关时刻与结束状态保存于 PLAYBACK-REVIEW-EVIDENCE.json。
