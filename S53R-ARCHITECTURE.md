# S5.3R Architecture

版本 1.7.0；S5.3R 修复阶段，非 S5.4。INTEGRATION_PILOT_ONLY / SELF_REVIEW。

原输入指纹 → Primary/Cascade追踪 → 显式Execution Context → 时间对齐副本 → Evaluation DAG → 原Lowering规则 → S51 Primitive → 显式Boundary Semantic → 普通CSP → 原Builder → 保存/重开 → Trace/同一组S35 Observable → Native边界 → 正常速度自审。

启用设置：contract_policy=S53R/1.0，time_alignment_policy=NEAREST_FRAME，max_time_quantization_error=1/60s。没有该设置的历史输入继续走旧路径。新增编译协议状态 BLOCKED_BY_UPSTREAM；AG/1.0六类对象和Schema不变。

新增 scripts/boundary_semantics.py、lowering_scheduler.py；扩展 timebase.py、event_lowering.py、execution_state_chain.py、motion_primitives.py、primitive_runtime.py、motion_boundary_validator.py 和编译层的两份Schema。Builder、Fragment Merger、摄影规则、S35阈值均未改。旧S45 PROFILES、连续运动判定、Impact授权逻辑保持。

Start/Stop只选择有显式零入口/出口的合法运动包络检测；不是通过减小阈值消除原失败。旧相对C1结果另存 legacy_relative_dimensions，C2原样记录。Offset内核原来已是五次平滑函数，其导数无须重写。TURN原来已有quintic easing，但限速追赶会隐藏无法在原时限到达的问题；显式angular profile现在拒绝该情况。

完整图未READY时不交给Builder。独立记录已验证片段组成的可执行子集，保留完整图中的未解决Event。这次不是静态替代：Native位移数据证明C走4.20m、A离位3m及打戏两人移动。仍不能把部分恢复误报成完整场景通过。

两次正常速度审看以浏览器完整播放并间隔截图观察进行，不冒充人类全帧持续视觉判断。原来S53的文件、图、计划、视频均未覆盖。没有Repair Loop、项目轨迹函数、新Primitive或导演目标修订。
