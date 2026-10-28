# blender-previs-layout 使用说明手册

本手册保留旧执行器操作说明。当前公开版本为 1.9.0；流程授权、模型、审阅格式与交接门禁以 SKILL.md 为准。同版已明确的授权不重复询问。文中历史 benchmarks 未随公开包分发，快速开始请用 README.md 的匿名示例。

## V1.2 新增的必经环节

流程为：剧情分析 → 全场逐角色路线与关键站位设计 → 示意图及行动表 → 使用者确认该版本 → 选择普通叙事或 Combat & Dynamic Motion Layout 路径 → 制作 → 审看修改 → 交付。普通文戏/叙事调度流程保持原样；打戏路径在同一全场确认之后增加动作阶段、支撑、质心、道具和接触检查。

起点确认不能替代全场确认。每个角色都要说明入场、停留、移动、关键反应、离画去向和最终位置，包含桥上桥下、山前山后、朝向及可见性。交付路线总图、关键节点图、逐角色行动表；复杂地势另配侧视或真实场景机位图。等待使用者确认期间不制作依赖该方案的 Layout 动画。

使用 `templates/story-blocking-plan.json` 记录方案，运行：

```powershell
python scripts/review_blocking.py story-blocking-plan.json --output blocking-review
python scripts/review_blocking.py story-blocking-plan.json --check-approval blocking-decision.json
```

第一条命令输出 SVG 总图、节点图、分段路线图、CSV 行动表和 HTML 审阅页。图示是坐标草图，需补真实场景的地标、遮挡和高度关系检查。第二条仅检查已记录的用户确认是否覆盖全场且对应当前方案，不会自动批准；确认语句需来自实际对话。待确认、仅首镜确认或方案更改时返回非成功状态。

确认记录采用 `templates/blocking-decision.json`，填写实际回复、来源、时间及方案 SHA256。若路线、关键站位、离场去向改变，更新受影响图示再确认；已确认且内容未变的同一完整方案无需重复询问。下文通用脚本和已有场景分支都遵循此流程，低层脚本本身不能替代人为确认。

二次修改时分别登记删镜、裁短、变速、画面裁切和空间重排；不要把整片乘同一速度。A/B 仅在需要比较明确变体时制作；默认已无手臂。道具、身体摆动与头部动作按本轮要求处理，并重构无法用所选几何体表达的手部特写。详见 `references/director-reedit.md`、`references/narrative-variants.md` 和山地案例 2026-09-11 复盘。

## 先选对执行路径

- **从零做简化预演**：使用本手册第 3–9 节的通用 manifest 和 build_previs.py。它逐镜生成并拼接，整场连续状态需要另外明确编排。
- **已有场景继续制作整场 Layout**：保留已确认场景、角色和光向，在版本副本上制作全局动画；按第 13 节操作。不要对已有工程执行通用 FULL_BUILD。
- **只要角色资产、剧情分析或首镜站位**：完成所要求阶段。进入整场前需要完整路线与关键站位图示确认；同一全场方案已有明确确认时直接继续。

## 1. 这个 Skill 做什么

`blender-previs-layout` 用低模环境、彩色角色代理和可编辑 Blender 场景，把故事、分镜、镜头表和角色/场景参考整理成可审看的 layout/previs 视频。

它优先解决五件事：

1. 谁在什么位置，空间关系是否清楚。
2. 谁先行动，动作因果和节奏是否清楚。
3. 摄影机看谁，镜头运动是否有动机。
4. 前景、中景、背景和遮挡关系是否成立。
5. 多镜头之间的位置、朝向和动作状态是否连续。

它用于前期布局和导演审看，不替代最终建模、绑定、表演动画、布料、特效或声音制作。

## 2. 运行环境

- 当前验证环境为 Blender 5.2、Python 3.13；其他版本需检查 API 兼容性。
- ffmpeg 和 ffprobe，用于视频打包与技术检查。
- 工具脚本使用 Blender headless + `bpy`。用户指定 MCP/UI 操作时遵循该要求；自动脚本不依赖专用 GUI 插件。

如果程序不在 PATH，可以设置环境变量：

```powershell
$env:BLENDER_EXECUTABLE = 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
$env:FFMPEG_EXECUTABLE = 'C:\Program Files\EVCapture\ffmpeg.exe'
```

## 3. 最小输入

输入是一个 JSON 项目清单，至少包含：

```json
{
  "project_id": "MY_PROJECT",
  "fps": 24,
  "resolution": [1280, 720],
  "scene": {"id": "COURTYARD", "elements": []},
  "characters": [
    {"id": "HERO", "display_name": "主角", "height": 1.7,
     "proxy_type": "HUMAN", "color": [0.1, 0.4, 0.9],
     "position": [0, 0, 0], "pose": "STAND"}
  ],
  "shots": [
    {"id": "SH001", "frames": 96, "actions": [],
     "camera": {"movement": "STATIC", "lens": 35,
      "start": {"location": [5, 5, 3], "target": [0, 0, 1]}}}
  ]
}
```

可直接复制和修改的模板在 `templates/project-manifest.json`。场景元素模板在 `templates/scene-manifest.json`，镜头计划参考在 `templates/shot-plan.json`。

## 4. 从参考资料到输入

Codex 负责把自然语言、故事、镜头表、分镜和参考图整理成上述 JSON。输入来源的优先级是：

1. 故事、镜头表和明确的导演意见：决定时序、动作和意图。
2. 分镜和关键帧：决定构图、景别、屏幕方向和镜头变化。
3. 场景参考：决定地标、尺度、入口、出口、遮挡和层次。
4. 角色参考：决定身份、色彩、轮廓、比例和代理类型。

按字段处理来源冲突：新版文字表可以决定剪辑顺序、动作和对白，旧 PDF 仍可提供匹配的构图。镜号不能代替内容匹配。导演的场景标注优先于此前推断的起点/路线。焦距、路速和场景适配身高必须标为估算。缺少的信息按 AUTO 填安全默认值；有证据时 INFER；确实影响导演意图且无法判断时 ASK。已有确认持续有效。

## 5. 代理类型和动作

支持的 `proxy_type`：`HUMAN`、`HUMANOID`、`BIPED_CREATURE`、`QUADRUPED`、`GENERIC_CREATURE`、`CORPSE`。

常用动作原语：

- 姿态：`STAND`、`CROUCH`、`KNEEL`、`BOW`、`SIT`、`LIE`、`CORPSE`。
- 起落：`RISE_FROM_KNEEL`、`RISE_FROM_CROUCH`、`STAND_FROM_SIT`、`FALL`。
- 移动：`MOVE_TO`、`WALK`、`RUN`、`APPROACH`、`RETREAT`、`FOLLOW`。
- 转向：`TURN_LEFT`、`TURN_RIGHT`、`TURN_TO_TARGET`。
- 视线和手势：`LOOK_UP`、`LOOK_DOWN`、`LOOK_LEFT`、`LOOK_RIGHT`、`LOOK_AT_TARGET`、`REACH`、`POINT`。
- 保持：`HOLD`。

每个动作需要 `character`、`primitive`、`start`、`end`；移动动作还需要 `to` 或 `target`。所有动作必须落在镜头帧范围内。通用 FOLLOW 只取目标初始位置，不能自动持续追随。四/五件式角色已由模式预设构建；源片级身体趋势、攀爬接触、道具交接和石块冻结反转需要项目专用动画，不能只填写一个动作名字就视为支持。

## 6. 基本命令

在 Skill 目录执行：

```powershell
python scripts/build_previs.py path/to/project-manifest.json `
  --output out --mode FULL_BUILD
```

只构建一个镜头：

```powershell
python scripts/build_previs.py path/to/project-manifest.json `
  --output out --mode SHOT_BUILD --shot SH001
```

只生成 `.blend`，暂不渲染视频：

```powershell
python scripts/build_previs.py path/to/project-manifest.json `
  --output out --mode FULL_BUILD --build-only
```

需要确定重建时加 `--force`。多个镜头会分别生成，再自动拼成 sequence 视频。

## 7. 增量模式

| 模式 | 用途 |
|---|---|
| `FULL_BUILD` | 清空并重建环境、角色、动作、相机和视频 |
| `SHOT_BUILD` | 指定镜头的完整重建 |
| `CAMERA_ONLY` | 只重建相机路径 |
| `BLOCKING_ONLY` | 重建角色阻挡和相机 |
| `MOTION_ONLY` | 重建角色动作和相机 |
| `OVERRIDE_PATCH` | 根据导演覆盖自动选择受影响的增量范围 |
| `RENDER_ONLY` | 使用已有 `.blend` 重新渲染和打包 |

通用运行时根据版本和规范化计划生成 fingerprint；它没有覆盖所有脚本和手动修改的 .blend。脚本/场景变更后用 `--force` 并独立核验视频。只构建 .blend 不代表旧 MP4 也已更新。第 13 节的新渲染器另用场景/依赖/帧内容校验。

## 8. 导演覆盖

覆盖文件格式：

```json
{
  "version": "1.0",
  "overrides": [
    {"shot": "SH001", "target": "camera",
     "changes": {"lens": 40,
       "end": {"target": [1, -2, 1.1]}}},
    {"shot": "SH001", "target": "character:HERO",
     "changes": {"position": [0.5, 0, 0]}}
  ]
}
```

支持的 target：`shot`、`camera`、`character:<id>`、`action:<id>`、`environment:<id>`。

执行：

```powershell
python scripts/build_previs.py project.json --output out `
  --mode OVERRIDE_PATCH --shot SH001 `
  --overrides director-overrides.json
```

## 9. 输出物

每个镜头目录包含：

- `PREVIS.mp4`：干净审看视频。
- `PREVIS_DEBUG.mp4`：带镜头编号、动作 beat 和角色图例的视频。
- `CONTACT_SHEET.png`：首、中、尾画面缩略图。
- `<shot>-PREVIS-V1.blend`：可继续编辑的 Blender 场景。
- `README.md`：镜头时长、动作 beat 和已知限制。
- `_work/technical-check.json`：分辨率、帧率、帧数和时长检查。

项目根目录还会生成 `BUILD-SUMMARY.json`、`PREVIS-SEQUENCE.mp4` 和 `PREVIS-SEQUENCE-DEBUG.mp4`。

## 10. 推荐审看顺序

先看 `PREVIS.mp4`，确认空间、动作和镜头是否成立；再看 `PREVIS_DEBUG.mp4`，核对帧号和 beat；最后打开 `.blend` 或修改 manifest。不要先用细节掩盖站位、方向或节奏问题。

最低审看问题：谁在哪里？谁先动？动作是否有起因和结果？镜头为什么移动？下一镜头是否继承了上一镜头的状态？

## 11. 常见问题

**找不到 Blender 或 ffmpeg**  
设置 `BLENDER_EXECUTABLE`、`FFMPEG_EXECUTABLE`，或使用 `--blender`、`--ffmpeg`。

**镜头画面为空**  
检查相机的 `start.location`、`start.target` 与角色位置是否在同一空间范围；确认角色 id 拼写一致。

**动作没有出现**  
确认 `primitive`、`start`、`end` 正确，且动作角色 id 存在；先看 debug 视频的帧号和 beat。

**想修改一个镜头但不想全量重建**  
使用 `OVERRIDE_PATCH`，并限制 `--shot`。相机变化会选择 `CAMERA_ONLY`，角色或动作变化会选择动作/阻挡重建。

**需要清理临时 PNG 帧**  
运行：

```powershell
python scripts/cleanup_generated.py path/to/skill-or-output
```

它只清理 `_work/frames`、Python 字节码和 Blender `.blend1` 备份，不会删除 clean/debug 视频、`.blend`、contact sheet 或报告。

## 12. 已验证示例

项目内置：

- `benchmarks/DEMO-S13-SH13-26/regression-manifest.json`：历史 SH13-26 回归。
- `benchmarks/generalization/SH13-25-manifest.json`：跑入、下蹲和 PAN 的通用化检查。
- `benchmarks/generalization/director-overrides.json`：相机覆盖和缓存示例。

这些是 V1.0 历史验证，结果和限制见 `V1-VALIDATION-REPORT.md`、`SH13-26-REGRESSION-RESULT.md` 与 `GENERALIZATION-CHECK-RESULT.md`；不作为 V1.1 新工具的通过证明。

## 13. 已有场景与整场连续制作

先保存版本副本，填写 `templates/production-context.json`：资料版本、已确认范围、坐标/单位/朝向、主要角色，以及本轮反馈要改动和保留的字段。根据标注核对总览、首镜机位、共同起点、分支路线、全场关键节点和最终去向；给出位置/颜色图例并完成本手册开头的确认环节。

填写 `templates/sequence-plan.json`。数组顺序就是剪辑顺序，`edit_id` 唯一，`shot_id` 可以保留插镜和非顺序编号，`camera` 必须是工程里的真实摄影机名。时间换算采用 1 起算的包含首尾帧范围；秒数区间为左闭右开。路线点用场景单位，速度为标明依据的估算；同时转移的队伍分别使用共同时间窗口。

```powershell
python scripts/plan_sequence.py sequence-plan.json --output timeline.json
```

工具会拒绝非整帧时长、重复剪辑 ID 和不相接的路线；转移估算超时会写出结果并返回退出码 2。修改某镜时长后，由它重新推算后续时间；项目动画、相机、字幕也必须按新时间表同步。

在副本里用项目脚本完成持续动画与摄影机：角色出画后继续运动，望远镜/投射物保留状态，手臂和根部曲线分配各自写入区间。模板不会自动生成这些表演。先检查首/中/尾画面，再看交接、攀爬、转身、近景和切点的连续短片。

填写 `templates/render-job.json` 的真实路径、场景名和外部依赖。`mode: review` 渲染每镜首/中/尾，`review_scale` 控制抽帧尺寸；`mode: final` 渲染整个时间轴或指定连续帧段。

```powershell
blender -b approved-animated-copy.blend --python-exit-code 1 --python scripts/render_existing.py -- --job render-job.json
blender -b approved-animated-copy.blend --python-exit-code 1 --python scripts/render_existing.py -- --job final-render-job.json --start 1 --end 240
```

此工具仅渲染已经完成动画的场景，不保存/重建原工程，也不编码视频。它按时间表指定摄影机；`--start/--end` 仅用于 final 模式。只复用指纹、尺寸和 PNG 内容哈希全部吻合的帧。场景保存或依赖变化会保守地使所有旧帧失效；它不能自动判断某次手臂修改只影响哪几帧。外链库、纹理、缓存等依赖需明确列入 job，同一目录不要同时跑重叠帧段。

完成连续 PNG 帧后，用同一序列编码干净和审阅 MP4，字幕根据时间表生成。填写 `templates/delivery-spec.json`，独立核验两支视频和工程文件：

```powershell
python scripts/verify_delivery.py delivery-spec.json --output delivery-check.json --ffmpeg ffmpeg --ffprobe ffprobe
python scripts/verify_delivery.py delivery-spec.json --output revision-check.json --compare previous-check.json
```

校验包含分辨率、帧率、实际解码帧数、时长、声明的音轨有无、全视频致命解码错误和文件 SHA256。参数失败或旧报告文件不一致时退出码为 2，报告仍保存。只有字幕时设置 `audio: absent`，不宣称有配音。

报告区分技术通过、文件是否仍与旧记录一致、渲染来源证据、实际视觉检查范围和用户最终验收。这个工具不会自动证明视频来自某个 .blend，也不能代替导演审看。山地案例案例、返工与依据见 `references/case-study-production.md`。

## 14. 本地安装与验证

将压缩包中的整个 `blender-previs-layout` 文件夹放入 `$CODEX_HOME/skills`（默认 `C:/Users/<用户名>/.codex/skills`）。更新前保留旧版本备份，确保 `SKILL.md` 位于该文件夹顶层。重新开始任务以加载更新后的说明；必要时重启应用。

## 15. 打戏 / 运动戏（Combat & Dynamic Motion）

1.5升级仅整合进本模块，不新增第三种模块。默认优先级：**动作可读性 > 屏幕运动轨迹 > Timing/Spacing > Camera Choreography > Action/Reaction > 重量感 > 简化物理合理性 > 精细人体动作**。

先做ACTION_BEAT + RHYTHM_MAP（准备、加速、爆发、命中/擦过、余势、恢复；松—紧—爆—停—再爆），再设计连续角色/代理轨迹、环境尺度参照与Camera。使用 `templates/combat-performance-plan.json` 作设计记录。具体参数从Source/批准设计取得，不照搬新资料的城堡、人数、动作或秒数。

Camera加入Lead、Lag、Catch-up、Impact Reaction、Pull-back，按事件选择和衔接，不能始终机械跟随或锁死中心。完整规则集中在 `references/combat-dynamic-motion.md`。

CLEAN允许保留有动作语义的简单ACTION/WEAPON/VFX代理；纯装饰性复杂FX不保留。新增ACTION_READABILITY_GATE和SILENT_REVIEW：关闭音效和Camera Shake，以正常速度确认攻击双方、力向、快慢、轻重、命中/未命中和下一趋势均可读。逐Beat记PASS/FAIL/NOT_REVIEWED/NA，未审看不算通过。定向Impact Reaction属于基础Camera运动，与随机Shake分开。


**默认成片与模型规范（1.5）**：文戏使用图2五件式（球头、眼条、锥鼻、一个整体长方体身体、胸前方向条）；打戏/运动戏使用图1四件式（球头、上身长方体、单块下半身长方体、锥鼻）。两者主体默认都无常驻胳膊、手、独立腿脚；COMBAT_DYNAMIC可按动作窗口增加临时ACTION_PROXY，四件式主体保持不变。用户明确模型参考优先，否则直接采用对应默认。视频1/2认可的身体动势预演、B站Box作品观察、可复用运动模板和交付条件见 `references/layout-presentation-standard.md` 与 `references/combat-dynamic-motion.md`，原图及认可视频已随Skill保存。

Layout服务于大轨迹、头身趋势、相对关系、快慢节奏与Camera。打戏允许用临时长条Box/小球表达拳脚方向或命中；武器用WEAPON_PROXY，简化刀气/冲击波/爆炸/烟尘/碎片用VFX_MOTION_PROXY，均不追求最终效果。精细摆臂/人体仍交后期；Mixamo仅在明确要求时作为变体。输出可播放CLEAN MP4、DEBUG MP4、.blend、简短Review；有Source还原任务加同步对比MP4。只交分析或模型不算完成Layout动画。

当任务含有打斗、追逐、跑跳、腾空、武器、飞行物、冲击或大幅度动作时，选择这条独立路径。它仍然使用本手册开头的全场路线/站位确认，不会改变普通文戏 Layout 的输入和动作原语。

### 15.1 制作顺序

1. 读取Source剪辑、动作、空间，区分剪辑慢放、录屏暂停与实际动作时间；使用源秒数映射目标帧。
2. 先填写ACTION_BEAT和RHYTHM_MAP，明确准备、加速、爆发、命中/擦过、余势、恢复，以及整场速度和张力对照。
3. 按节奏设计共享角色/代理连续路线、环境尺度参照和Camera意图；加入全场路线/站位包，沿用既有确认流程。
4. 保留COMBAT_BOX_4主体；添加必要的临时ACTION_PROXY、简单WEAPON_PROXY和VFX_MOTION_PROXY，记录所有者、目标、可见窗口、释放、命中和终态。具体生命周期见模块规范。
5. 先确定Root/COM写入者，再实现上下身、头部、攻击代理和接收者的连续曲线；保留支撑、腾空、持有/释放、Follow Through、Recovery及跨Cut状态检查。
6. 实现事件驱动的Lead/Lag/Catch-up/Impact Reaction/Pull-back，并用实际评估的身体/代理范围检查构图。Camera与动画可以迭代，不退回始终机械跟随。
7. 以正常速度执行ACTION_READABILITY_GATE及关闭声音/Shake的SILENT_REVIEW；不通过先修可读性。再做支撑间隙、穿模、旋转连续和代理端点等技术检查。
8. 从同版动画交付CLEAN、DEBUG及必要的Source同步对比，完整解码并报告审看范围、Gate结论和未解决问题。

### 15.2 打戏白模和质心检查

均匀长方体的质心是几何中心；如果道具参与质量估计，明确是角色质心还是角色+道具组合质心。不要使用底面原点沿弹道旋转，也不要在倾斜/缩放后固定使用 `H/2` 放置。支撑时建议让最低角/边落在实际地面附近，并保留支撑见证点。落地顺序必须是接触、压缩、一次回弹、回稳，不能把空中姿态直接吸到地上。

### 15.3 避坑规则

- 不用奇偶帧旋转、随机逐帧摆动或全程正弦呼吸制造“流畅”。
- 不在角色尚未入画前把它预先放到揭示点，不在切镜时重置路线或速度。
- 不让释放后的飞行物继续跟随手，不在接触点瞬移武器。
- 不用固定高度、固定原点或当前最低顶点替代真实支撑计算。
- 不用镜头抖动、速度坡道或闪光掩盖动作因果不清。
- 选定无四肢白模时，不在字幕或报告中声称存在五指、脚步或未见的接触结果。

### 15.4 能力边界

本模块目前可复用的是节拍拆解、低模方向表达、体型差异、支撑/质心布局、抛物线近似、道具状态、连续动作通道、接触/回稳检查和切镜后评估相机。认可视频的呈现层级现已成为默认目标；每个新案例仍须分别审看运镜匹配、快慢节奏、重量差和Recovery，报告实际不足。技术 PASS 和历史认可都不等于当前成片已验收。

调用示例：“使用 $blender-previs-layout，基于已确认的场景完成整场 Layout。保留当前站位、路线、角色颜色与光向，按最新文字表的剪辑顺序，先编译全局时间表，再制作连续表演，输出 24fps 干净版、审阅版和可编辑工程。”

维护者可运行 `python -m unittest discover -s tests -p 'test_*.py' -v`；带 Blender 的六帧实测运行 `python tests/smoke_existing_scene.py --blender <Blender路径> --output <独立检查目录>`。这些验证覆盖时间、校验和渲染复用，不能证明任意项目的动作美术质量。
