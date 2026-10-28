# Dynamic Target Resolution

版本 1.7.0；S5.3R 修复阶段，非 S5.4。INTEGRATION_PILOT_ONLY / SELF_REVIEW。

ORIENT_TO通过sample_track读取每个采样时刻目标的已求值位置和actor位置，不取初始/终点常量。沿用LEAD/LAG时间偏移、局部方向转换与max_angular_speed。S51原动态取样算法没有复制到Lowering；新调度让合法目标轨迹先存在。

通过技术fixture：移动目标LOOK quaternion确实随时间改变；Camera FOLLOW对动态subject实际位移超过2m；同一原Runtime生成。原文戏A_NOTICE/A_LOOK_BACK已执行且Native rotation与Fragment一致。观察不等于“视线艺术正确”：SMOOTH有获取过程，大角度和快速近身掠过仍可能不可行。

大角度TURN的EASE_IN_OUT_ROTATION使用现有quintic曲线，零角速度入口/出口；若曲线请求超max速度，返回INFEASIBLE_DURATION，不再靠限速追赶到未完成的终点。0→135°/4s专项PASS；同角度0.2s拒绝。

冻结文戏B_ESTABLISH为180°/1.8s、180°/s上限；quintic峰速187.5°/s，原时长不可行，未偷偷延长。Combat B_NOTICE的采样max rate step约0.41378 rad/s/sample超过原0.1，因此仍未执行。没有修改此阈值。不能宣称所有动态LOOK已稳定。
