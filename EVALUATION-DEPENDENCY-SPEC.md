# Evaluation Dependency

版本 1.7.0；S5.3R 修复阶段，非 S5.4。INTEGRATION_PILOT_ONLY / SELF_REVIEW。

lowering_scheduler.py建立编译层DAG，区别CAUSAL/CAUSAL_SOURCE、EVALUATED_TARGET、STATE_CHAIN、ORIENTATION_STATE_CHAIN及CAMERA_SUBJECT。它们是编译关系，不是AG新增作者对象。

先完成目标与自身Root轨迹，再处理LOOK/TURN；已结束且停稳的目标可延续实际出口状态，不退回初始位置。相同旋转通道前序失败也阻塞后序，不默默使用neutral入口掩盖失败。状态链仍验证显式入口冲突。

调度确定性拓扑排序；环返回EVALUATION_CYCLE，无递归自动重试。Camera阶段等待subject运动结果后再求值。依赖失败返回BLOCKED_BY_UPSTREAM并列出producer，不再伪装成作者缺参数。

原S52并非完全没有目标依赖：本次把隐含排序变成可审计输出，补齐自身运动、结束目标、旋转通道和级联分类。若上游被拒绝，调度器不会凭空创建运动。

本轮恢复链：C_ENTER→A_NOTICE/A_LOOK_BACK/Camera；A_APPROACH→A_PURSUE→A_RECOVERY；B_DODGE→B_EXIT。B_NOTICE在Combat解除上游阻塞后暴露自身角速度失败，必须记为新Primary，不能记作成功的Cascade Resolution。
