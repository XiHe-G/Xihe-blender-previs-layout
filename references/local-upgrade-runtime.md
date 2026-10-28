# 1.8 执行接口与迁移

新增通用模块在 scripts/director_camera；原 combat/narrative 核心及冻结 Benchmark 保留。新入口是明确的摄影计划执行器，不是能自动生成完整角色动画的编译器。Codex 依 [导演制作流程](director-production-workflow.md) 作设计，场景与动作通过既有生产路径执行，再用这些工具检查和落实相机。

## 可执行命令

下例用本机配置的 python、blender、ffmpeg，不包含制作电脑固定路径。把 <skill>、项目文件和输出替换为实际路径，始终新建候选输出。

```text
python "<skill>/scripts/director_workflow.py" plan.json --output plan_review.json
python "<skill>/scripts/director_workflow.py" plan.json --changes changes.json --output revision_scope.json
blender --factory-startup --disable-autoexec -b baseline.blend --python-exit-code 1 --python "<skill>/scripts/execute_director_cameras.py" -- --plan plan.json --output candidate.blend --evidence native.json
python "<skill>/scripts/review_encoded.py" plan.json CLEAN.mp4 --output encoded_review --ffmpeg "<ffmpeg>" --native native.json
```

示例：examples/director_workflow/dialogue_plan.json 与 brief.txt。例子只展示独立文字任务的相机合同，不能当真实项目机位库。既有场景必须先确认它的完整帧区间与 plan 相同；部分修改任务应由完整镜表复制未改摄影视图，再只重渲染受影响区间，或使用项目已有局部适配器。

DIRECTOR_PLAN/1 使用整数 [start,end)；末帧 end−1，时长(end−start)/fps。每镜唯一 camera.id；普通返打可复制同一个机位参数但用独立 camera identity。字段 purpose、first_focus、start_read、end_read、cut_reason、source、events 和 motion_nodes 由导演作者填写。Native adapter 创建新摄影机、替换完整时间轴 camera markers、保留非相机marker，保存原绑定证据；不会清场、改人物/道具/灯光。

当前位置、瞄准、时间曲线通过 motion 显式定义；BEAT 曲线允许分段节拍。固定机位不漂移。STATIC_HOLD 的 waypoint 也不得暗中摇动。固定镜 native 判定需要朝向样本；缺少朝向时只保留兼容的平移status，并明确 scope=TRANSLATION_ONLY、orientation_status=NOT_REVIEWED；不能引用这个status宣称全相机静止通过。DIRECTOR_PLAN adapter 当前只支持每镜固定焦距，无旧rig自动迁移；FOLLOW_WITH_LAG 的几何辅助有实现，但新Native adapter尚未支持，提前拒绝。变焦、复杂跟随、角色动画走原有明确授权的项目执行器，附实际trace，不能伪报新接口已支持。

依赖：纯计划／依赖／预算工具仅Python标准库；Blender适配器需要bpy；视频抽帧需要FFmpeg；video_review 中图像数值辅助需要numpy（可选）。当前原生验证环境是Windows + Blender5.2；其他系统安装包可搬运，未宣称跨系统原生测试。

## 证据边界

声明与哈希一致只证明绑定，没有证明渲染过程。要保存渲染命令、原工程hash、输出hash、实际trace、媒体解码与逐帧镜表。仍用原 verify_delivery 做真实媒体QA。审阅图片索引中的 source_frame 才是原时间轴帧号，导出 frame_00001.png 是抽帧序号，不能混淆。

持久化修正预算调用 workflow.reserve_attempt；复用调用 verify_reuse；渲染范围调用 invalidation。它们是可调用辅助，需要制作执行者传入可靠来源、事件、依赖和状态；不存在全自动扫描全工程语义关系的声明。

## Reproduce isolated integration fixtures

```text
blender --factory-startup --disable-autoexec -b --python-exit-code 1 --python "<skill>/examples/director_workflow/build_fixtures.py" -- --output "<new test directory>" --render
```

This command creates two new toy scenes from authored text briefs. Never pass a production .blend; the fixture intentionally resets only its fresh test process. It checks proxy forward direction against its partner, protects all pre-existing fixture objects across camera application, saves/reopens, then optionally renders 144 frames per scene. These are same-author integration samples, not blind tests or artistic/combat capability acceptance.

For isolated headless tests prefer --factory-startup --disable-autoexec so personal startup add-ons do not run. Production assets that require add-ons need explicit dependency preflight; do not disable a required rig dependency and silently continue. facing_relation accepts an evaluated world-forward vector plus origin/target; it reports geometric direction only, not eye gaze or acting.
