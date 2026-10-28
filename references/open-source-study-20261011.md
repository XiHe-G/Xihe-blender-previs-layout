# 开源研究与取舍 · 2026-10-11

围绕文字导演、摄影路径、切镜、调度、可读代理、验证和AI交付检索。以下12个相关仓库完成有界筛选，并按本地痛点选择性读取文档或代码；这不是“GitHub所有项目”穷尽检索，也没有声称看完仓库引用的所有视频。保留 commit、原文快照及失败请求，避免只凭README功能表判断成熟度。

没有下载运行外部仓库脚本，没有安装外部插件，也没有把第三方源码或模型复制进正式Skill。新增代码是本地已有候选的迁移和独立实现；吸收的是经过取舍的组织方法。许可证不明确的项目只作研究参考。

## [Wanrd0Geri/seedance-previz](https://github.com/Wanrd0Geri/seedance-previz/tree/4228d05168e99a2e54567fb86d92629502f79181)

- 固定版本：`4228d05168e99a2e54567fb86d92629502f79181`。
- 许可证记录：未找到明确许可证；不复制代码。
- 阅读层级：SKILL、camera-moves、export-verify、check_export及局部库实现。
- 取舍：借鉴镜头控制与最终编码证据、交付卡分离。拒绝强制运动、默认多层抖动、隐藏对手换取单人构图、清理历史版本和固定平台秒数。

## [AcademySoftwareFoundation/OpenTimelineIO](https://github.com/AcademySoftwareFoundation/OpenTimelineIO/tree/00c22fa3a64256d8d3dcafbc7276492185dd970d)

- 固定版本：`00c22fa3a64256d8d3dcafbc7276492185dd970d`。
- 许可证记录：Apache-2.0。
- 阅读层级：README、帧范围与时间轴文档、示例。
- 取舍：吸收精确帧范围和剪辑来源映射，新增接口采用明确半开区间。没有安装OTIO或声称实现了OTIO工程互通。

## [wonderunit/storyboarder](https://github.com/wonderunit/storyboarder/tree/8b81a25c71d5f7ca46e8d5b8e3d4f7b3968f95c2)

- 固定版本：`8b81a25c71d5f7ca46e8d5b8e3d4f7b3968f95c2`。
- 许可证记录：build/license_en.txt 为自定义条款；不直接归类MIT。
- 阅读层级：README、许可证、FCPX导出代码；未完整运行应用。
- 取舍：借鉴快速调度迭代与镜头身份/时长绑定。没有引入应用、模型库或整个导出器。

## [wonderunit/shot-generator-models](https://github.com/wonderunit/shot-generator-models/tree/8195e380179561c04bcd1b5ed4a772c305245dff)

- 固定版本：`8195e380179561c04bcd1b5ed4a772c305245dff`。
- 许可证记录：MIT。
- 阅读层级：README/元数据。
- 取舍：参考可读轮廓、身高比例服务调度的分工；没有导入资产，也不替换用户已确认的箱体代理。

## [tin2tin/Blender_Screenwriter](https://github.com/tin2tin/Blender_Screenwriter/tree/ff4543bd3cf0ede45672fbe1a11f39f299c9a5f3)

- 固定版本：`ff4543bd3cf0ede45672fbe1a11f39f299c9a5f3`。
- 许可证记录：此次未充分核定；不复制。
- 阅读层级：README与部分入口源码；一个目标源码路径404。
- 取舍：剧本文本与剪辑条目关联有用，但关键词绑定不等于导演设计。作为流程参照，不新增运行依赖。

## [arazcreates/CineKit](https://github.com/arazcreates/CineKit/tree/4fda86f1acb0b994f81ad658ca7d078e1152078f)

- 固定版本：`4fda86f1acb0b994f81ad658ca7d078e1152078f`。
- 许可证记录：GPL-3.0-or-later。
- 阅读层级：README、shots.py；另存rig/camera源码待深入。
- 取舍：借鉴镜头管理与原生标记绑定，独立实现本地adapter。不给每镜自动换曝光/Look，不复制GPL代码进入当前模块。

## [koosoli/OpenShotDesigner](https://github.com/koosoli/OpenShotDesigner/tree/3f1a595d7f7d36c0a40fa75bec027098df43bd2d)

- 固定版本：`3f1a595d7f7d36c0a40fa75bec027098df43bd2d`。
- 许可证记录：GPL-3.0-or-later（读取LICENSE）。
- 阅读层级：README和许可证。
- 取舍：借鉴剧本、场地图与分镜共享稳定身份；不导入桌面工具、账户流程或完整代码。

## [arjun988/blender-skills](https://github.com/arjun988/blender-skills/tree/8f778d2405a214b508d4c7d80742be8e43acdd52)

- 固定版本：`8f778d2405a214b508d4c7d80742be8e43acdd52`。
- 许可证记录：MIT。
- 阅读层级：camera-cinematography SKILL。
- 取舍：保留意图→摄影→画面检查的简洁顺序，感光面与焦距联合记录。镜头焦段不能当电影感配方，默认Track To不适合所有横移。

## [scenario-labs/skills](https://github.com/scenario-labs/skills/tree/f6f8ab71aa1f1e8322624869a173c1024aa875b8)

- 固定版本：`f6f8ab71aa1f1e8322624869a173c1024aa875b8`。
- 许可证记录：MIT。
- 阅读层级：previs-storyboard SKILL；未验证其全部引用教学视频。
- 取舍：信息节点先于镜头、切后注意力与共享场景/摄影分工值得参考。不采用通用固定每拍时长、将完整Layout全改静帧或未经授权的角色漂浮/缩放/换物作弊。

## [HiAPIAI/awesome-ai-video-workflows](https://github.com/HiAPIAI/awesome-ai-video-workflows/tree/ad5deeef59029a24db393f10ca44fcf8371a5f2b)

- 固定版本：`ad5deeef59029a24db393f10ca44fcf8371a5f2b`。
- 许可证记录：MIT。
- 阅读层级：Blender engine README.source.md；未运行引擎。
- 取舍：文字由Codex编写合同，执行器核验而非宣称NLP导演；一次改变一类变量，编解码证据绑定。暂不引入Node引擎与其风格模板。

## [DevMartinese/threejs-previz](https://github.com/DevMartinese/threejs-previz/tree/615b05622c5267ceb5c127c43c32e1bd87ebe8cf)

- 固定版本：`615b05622c5267ceb5c127c43c32e1bd87ebe8cf`。
- 许可证记录：MIT。
- 阅读层级：README/架构概览；未运行Remotion。
- 取舍：可借鉴按帧确定性、动作与摄影独立求值及检查再渲染。测量不能替代看画面；不迁移至Three.js，避免第二套运行栈。

## [wassermanproductions/blockout](https://github.com/wassermanproductions/blockout/tree/3f2d0564fd575f70fc28e9bfaa7e94b05e3955d9)

- 固定版本：`3f2d0564fd575f70fc28e9bfaa7e94b05e3955d9`。
- 许可证记录：Apache-2.0。
- 阅读层级：设计文档前半与README；设计目标不当成已验证功能。
- 取舍：借鉴场景拥有共享调度、镜头拥有摄影和时间，明确位置/朝向/到达/停顿节点。其自动步态与大量预设不作为本Skill已具备能力。

## 未采用与研究限制

blender/blender-studio-tools 与 Chebifier/Blender-MCP 本次请求404，没有当作已调查实现；godot-open-rpg与当前目标不匹配，排除。部分下载源码仅存档未逐行审计；不把下载量当学习成果。第三方Seedance时长、模型能力或观看量不作为当前平台事实。原生功能主张以本地Blender与媒体证据为准，艺术效果仍需正常速度审片。

## 本地落地关联

| 研究方向 | 本次可检查的落地 |
|---|---|
| 文字→明确导演决定→执行 | director-production-workflow；workflow.validate_plan 与独立文字fixture |
| 摄影、瞄准、时间曲线分离 | 本地director_camera.motion/native；不是直接移植外部噪声/样条库 |
| 切镜与帧范围 | execute_director_cameras、validate_cuts；原生marker和每帧有效Camera证据 |
| 最终编码证据 | review_encoded，帧事件清单、源帧映射、媒体hash；不冒充完整观看 |
| 共享场景调度与独立摄影 | 同一Blend中生成候选Camera；原有对象矩阵保护和保存重开测试 |
| 交付可追溯性 | 增量依赖、复用receipt、CLEAN/REVIEW区分、AI交付约束分层 |
