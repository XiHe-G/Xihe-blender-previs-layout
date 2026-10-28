# S4.5 · Repair Feasibility + Motion Boundary Validation

正式Skill 1.7.0；S4.5是V1.8研发阶段。新增两个只读辅助层，AG/1.0的六类数据、CSP、原Builder和八类S3.5 Checker均未修改。

建议流程：Checker FAIL → 原Repair Proposal → 指定候选的PREVIEW_ONLY → Impact Graph / Constraint Collision → 人工Decision → 现有S2 → 原Builder → S3.5复查 → Boundary Validation → 分维度Repair Assessment。

Preview不是Decision，也不生成Changeset/Patch。独立JSON以Proposal、原CSP、Expected和Checker结果的SHA绑定；未来人工Decision可在既有authority.source/director_note引用Preview报告。此轮没有改写S4执行器强制消费Preview，也没有生成新的Decision。

模块：repair_impact_graph.py保存六项有限耦合；repair_feasibility.py负责风险摘要、保护值冲突和原Checker调用；motion_boundary_validator.py负责相对运动边界与独立结果维度；s45_protocol.py离线验证五份辅助Schema。没有新的作者层顶级对象或第九类导演Checker。

F1/F2用R1 BEFORE工程，在内存中评估三个预先写明的静态Camera配方。Lens先运行低成本投影数学，再用原bpy exporter测量三候选的遮挡、屏幕关系和全片Expected。没有save_mainfile、Builder调用或CSP输出。每个产物和目录标记PREVIEW_ONLY；Trace外层明确source_blend只是输入，并非候选已保存工程。

F3只读S4 R4已有AFTER Blend/Trace。F4是100帧数值技术fixture，不是角色表演、新动画Primitive或导演Benchmark。初始Preview后发现隐藏对象求值缓存不能作为运动证据，故以同一配方补测原生曲线保护；没有调整参数或按结果搜索。最终权威数据在PREVIEW_ONLY/r1-verified、boundary-verified；早期诊断保留为工程过程记录。

停止边界：所有输出均为诊断；没有S2 merge、自动平滑、扩大窗口、自动选胜者、自动批准或第二次正式Repair。S4所有Decision消费记录和收据保持原SHA。
