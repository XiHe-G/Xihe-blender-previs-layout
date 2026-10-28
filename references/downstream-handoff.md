# AI video handoff contract

Status: INTERFACE_ONLY; explicit data packaging compiler implemented. No Seedance call, generation test or Seedance Plan-vs-Actual implemented.

AI_VIDEO_HANDOFF carries cuts, identity/reference mapping, world positions, screen direction, shot size, camera paths/lens, start/end states, motion trends/speed class, prop relations, combat results, VFX semantics, lighting changes, field-level source authority and downstream freedoms. Bind it to the delivery manifest and its exact fingerprint. Compiler checks layout version, shot order and cuts against that manifest; source content/native fidelity still requires external evidence.

Default permitted completion: limb action detail, expression, cloth, hair, action detail, final VFX and materials. Protected: key Camera, Blocking, Screen Direction, Cut and Beat result. A user override needs actual scoped source authorization; it is not implied by downstream model limitations. Keep explicit uncertainty when a layout does not encode a limb action or final effect appearance.

Reference video is optional learning/reconstruction/benchmark evidence, never a required production input. A comparison-only video must not be misregistered as supplied generation control. Describe exactly which layout/images/other references were actually handed downstream. Downstream benefit remains unvalidated until controlled real-project comparison.

## 定稿与交付门槛（适用于全部交接路径）

先在现有项目记录中核对：用户确认定稿的原话或消息引用、确认的 layout 版本与镜头范围、最终 .blend／可播放 layout 的实际文件和交付记录。确认和交付必须指向同一版本；无证据不得填成通过。只确认分镜、路线、测试或“先给我看”不满足门槛。用户已明确确认同版并要求最终交付时，先完成交付再生成卡，无需再问一次。

未满足时沿原制作／审阅／修改／输出路径推进，不创建预填交接卡或 AI_VIDEO_HANDOFF，不调用 compile_handoff。现有交接编译器只核对数据绑定，不能代替此门槛。所有交接入口（包括直接 DOWNSTREAM_PREP 和旧 JSON 模板）遵守本节。

## 定稿后交接步骤

1. **交付最终 layout。** 先提供已确认版本的可编辑 .blend 与可播放 layout 链接、版本及镜头范围；文件缺失、仍未完成最后修改或尚未交付时，停止交接步骤。
2. **准备参考视频。** 复用同版 CLEAN；若只有带字 REVIEW，按现有导出路径生成同版纯净参考。移除字幕、镜号、坐标轴、轨迹线和调试框，保留动作语义代理。不得为迁就下游擅自改代理结构、颜色、灯光、动作、切点或时长。核验解码、帧数、fps、分辨率、切点和来源，抽编码文件每镜起／中／落及关键事件、切点两侧画面。按当前平台实际限制检查可用性；不照抄外部仓库历史限制，不把取整秒数强加给已定稿时间轴。需要实质改动时回到现有修改与定稿流程。
3. **写交接卡。** 使用 [模板](../templates/aigc-video-handoff-card.md)，放在项目最终交付目录，文件名含版本。帧号／镜头／相机数据以最终工程和实际编码为准，逐镜描述实际可见内容，记录角色姿势、道具归属和跨切继承。对白、表情或四肢细节未被源资料确定时写“未定义／待下游补充”，不得当成已经拍到。
4. **交给 aigc-video。** 提供最终 CLEAN、交接卡及现有角色／场景参考的链接，说明下一环节用 `aigc-video` 按卡编写提示词。素材图N／视频N只按实际上传顺序绑定；未上传只列素材ID和路径，不伪造编号。layout skill 到此完成，不自动写最终提示词、上传平台或启动生成。后续用户要求写提示词时由 aigc-video 接管，读取它自己的白模流程（当前为 references/modes/whitebox-driven.md 与 references/seedance-operations.md）。

交接卡是上述 AI_VIDEO_HANDOFF 的人可读补充，不改变现有 JSON schema 或制作内核。若项目已经使用 JSON 合约，只在门槛满足后编译，并与卡共享 delivery fingerprint；旧项目无需迁移合约。新修改使旧卡对新版失效，重新确认并交付新版后才生成新版卡。

仅吸收 seedance-previz 的“导出参考视频 → 交接卡 → aigc-video”交接思路，不引入其场景构建、清理历史文件或默认渲染规则。参考：https://github.com/Wanrd0Geri/seedance-previz （4228d05168e99a2e54567fb86d92629502f79181），下游：https://github.com/Wanrd0Geri/aigc-video （efaac61de262aa20d4d41a0bb0a7bb37858ed590）。

## Practical 1.8 handoff

Bind CLEAN video, exact frame/cut table, actual lens/sensor, character IDs and reference ownership to one delivery receipt. Separate (1) exact constraints: cut order, camera trend, screen direction, action causality and event outcomes; (2) approximate proxy cues: body trend, contact intent, relative speed; (3) appearance references: character/scene/material; (4) unresolved details requiring later work. Missing hand/foot/contact evidence must not be described as accurate control. REVIEW is for people and is not silently supplied as CLEAN. Include first/last and key-event frames from actual encoding; mark extracted frame indices correctly. Check current platform limits only when a downstream request needs them; do not hardcode a repository's old duration/upload limits. No automatic upload or generation. Benefits to Seedance remain NOT_VALIDATED without controlled authorized downstream comparison.
