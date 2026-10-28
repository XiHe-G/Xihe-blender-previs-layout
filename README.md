# Blender Previs Layout

用于 Codex 的 Blender Layout / Previs 技能，当前版本 **1.9.0 · ACTION-EXPRESSION**。

从剧情、文字分镜、场景与角色参考制作连续、可审阅、可局部修改的预演。以简化 Box 角色表达空间调度、镜头、节拍、速度与受力反馈，服务最终 Layout 和经确认的下游参考。

## 主要能力

- 剧情意图 → 全场调度 → 摄影／切镜 → 连续预演 → 局部修改与版本交付。
- 文戏五件式、运动戏四件式角色；保持身份、尺度、镜外状态和跨镜连续。
- 可适配的镜表和审阅版式，以及基于故事目的的摄影决策。
- 新增显式路线、速度曲线、受击退移／制动与分通道身体响应。此入口仍为 **EXPERIMENTAL**，不等于自动编排完整打戏或人体物理解算。
- 原生轨迹回读、接触／支撑／镜头检查；数值通过与正常速度观感、导演批准分开。

完整行为入口：[SKILL.md](SKILL.md)；能力边界：[CAPABILITY-MATRIX.md](CAPABILITY-MATRIX.md)；[动作表达](references/action-expression.md)；[摄影](references/cinematography-for-layout.md)；[审阅](references/adaptive-layout-review.md)。

## 安装

下载仓库，将整个目录命名为 `blender-previs-layout`，放入你的 Codex skills 目录，保证 `SKILL.md` 位于该目录根部。已有同名技能时先备份，避免覆盖自己的项目配置。也可以把本仓库交给技能安装器安装。

需要能运行 Python 的 Codex 环境。数值编译使用 Python 3.12 与 `jsonschema`；原生场景脚本通过 Blender 自带 Python 执行。本次公开整理沿用 Blender 5.2 作为验证环境，其他版本需按实际接口验证。视频编码／媒体检查需要 FFmpeg 和 FFprobe。部分可选审计路径使用 NumPy。

在独立虚拟环境安装 `requirements.txt` 中的依赖；不要把系统 Python 的二进制依赖直接复制到 Blender 的不同版本 Python 中。

## 快速开始

在 Codex 中：

> 使用 $blender-previs-layout，依据我的剧本和参考制作 Layout。先明确全场空间、角色路线与关键节拍，再执行已确认的镜头；保留可编辑工程与正常速度预览。

参数编译示例（在仓库根目录运行，输出路径必须尚不存在）：

```sh
python scripts/action_expression.py templates/action-expression-travel.json --output out/travel-v001.json
python scripts/action_expression.py templates/action-expression-impact.json --output out/impact-v001.json
```

上述命令生成动作数据，不直接生成整场动画。原生构建与回读方式见 [动作表达](references/action-expression.md)。匿名三镜头场景可使用：

```sh
blender --factory-startup --disable-autoexec -b --python-exit-code 1 --python examples/director_workflow/build_fixtures.py -- --output out/director-demo --render
```

这是生成新示例的命令；已有工程请按 [已有场景流程](references/existing-scene-production.md) 在副本上修改。

## 验证与分发范围

```sh
python scripts/run_public_tests.py
```

公开测试覆盖动作表达与导演／摄影合同。历史项目素材及完整集成基准没有随仓库发布，不能据此宣称所有旧基准可在新机器直接重放。详见 [公开分发说明](PUBLIC-DISTRIBUTION.md)。

本版本保留原先的最终定稿交接门禁：用户明确确认具体版本定稿并交付同版 Layout 后，才生成下游视频交接卡。
