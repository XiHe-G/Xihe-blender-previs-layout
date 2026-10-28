# TIME ALIGNMENT POLICY /1.0

版本 1.7.0；S5.3R 修复阶段，非 S5.4。INTEGRATION_PILOT_ONLY / SELF_REVIEW。

必须在Execution Context声明策略；没有设置不偷偷量化。原严格OFF_GRID旧入口保持。NEAREST_FRAME沿用timebase.py的Decimal ROUND_HALF_EVEN；FLOOR_FRAME/CEIL_FRAME也集中在timebase.py实现。SUBFRAME_IF_SUPPORTED在当前CSP整数采样后端返回SUBFRAME_UNSUPPORTED_BY_CSP_SAMPLING，不假装支持。

作者时间不修改。编译副本保存author_time、execution_frame、execution_time、quantization_error、policy、tie_rule、max_time_quantization_error和来源。两Pilot容差显式为半帧1/60s。4.25×30=127.5，ties-to-even→128，F1=0，所以F129，execution_time=4.2666666667s，误差+0.0166666667s。

超过容差返回NEEDS_AUTHOR_INPUT。不同作者时刻量化到同帧时，保守返回TIME_ORDER_COLLISION；不默默合并先后。相同原时刻允许共享执行帧。该保守检查也可能拒绝本来不相关的近时刻，当前LIMITED。

原AG磁盘内容和语义SHA不变；执行图SHA与原图SHA分列。参数Provenance明确execution time来自TIME_ALIGNMENT而非作者显式写入的新数字。4.25s虽然量化合法，B_NOTICE仍会因B_ESTABLISH失败而BLOCKED_BY_UPSTREAM；对齐成功不是动作成功。
