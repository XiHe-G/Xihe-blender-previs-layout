# S4 Human-approved Repair Loop — PASS / LIMITED — one human-approved round

正式版本1.7.0。八类Checker不扩展，AG/1.0六类对象不扩展，Builder代码与运动行为不改。本阶段不是Automatic Repair。

路径：原Graph/执行/Trace/Checker → 只读Repair Proposal → 用户选择与批准 → REPAIR-DECISION/1.0 → CHANGESET/1.0 → 原S2 analyze/依赖闭包 → 作者提供局部lowering → 原S2 sparse patch merge/Override Guard → 普通CSP Builder → 保存并重开Blend → 原S3.5 Trace/Checker → Repair Result + SHA审计。

新脚本：repair_proposal_generator.py、repair_to_changeset.py、repair_result_validator.py、repair_audit.py。原S2只增加受批准Repair envelope约束的执行重生成兼容入口，没有复制依赖闭包、Patch合并或锁保护实现。

必要兼容：普通S2 Changeset仍要求old_value != new_value。Repair不能改导演目标，因此可选execution_repair.mode=RELOWER_UNCHANGED_PLAN保存提案、Decision及其ID，允许在现有SHOT_INTENT_CHANGE/EVENT_SPATIAL_CHANGE分派下请求重新生成同一个作者值。此时old_value严格等于new_value，Graph逐值不变。不是把导演目标改成Actual；不是伪造作者设计变化。Patch同时受S2真实范围和人工允许范围约束。这个辅助执行协议不增加AG顶层对象。

S2依赖闭包可能包含更多下游Event。每个脏region都须UPDATED或REVALIDATED_UNCHANGED；Proposal估计与真实S2范围有差异时WARNING，不扩大Decision权限。修复绑定由UPDATED-BINDING明确携带，新CSP/绑定是本轮执行权威；历史S1 sidecar不能被当成本轮执行结果。

实验目录examples/s4/R1..R5保存原始快照、提案与审核HTML；工作区foundation-v18-s4保存检查与后续执行结果。tests/run_s4_repairs.py只接受已记录的真实用户Decision文件；先校验五项Decision，再一次性按所选策略运行作者提供的技术lowering。禁止自动选优/批准/多轮重试。

五份真实用户Decision已记录并各消费一次：R1 NOT_FIXED；R2–R5 FIXED。五例均经过S2、Builder保存/重开和S3.5重检，保护区零差异；162项测试PASS。闭环工程Gate为PASS / LIMITED，不表示五项修复全成功。执行器以排他创建的Decision消费文件阻止同一Decision重放；失败后不自动改参数或选择其它策略。详见S4-FINAL-REPORT.md。
