# S3.5 Checker Calibration + Evidence Coverage

正式版本 1.7.0；V1.8 为研发名称。S3.5 保留八类 Checker，AG/1.0 六核心集合和 CSP/1.0 执行语义不变。

数据链：既有 AG + 明确来源的校准声明 → Expected Observable → 已保存 Blender Scene 的 Actual Trace → 数据充分性 gate → 八类测量 → 来源/置信度限定 → JSON/HTML 诊断。没有 Changeset、Patch 或自动修复调用。

`checker_calibration.py` 集中 HOLD profile、明显违背 HOLD 的技术边界、证据资格判断。`plan_to_observables.py` 校验完整的来源字段；旧 S3 无校准字段的协议仍可读取，归档文件保持原样。新 S35 Observable 全部带 requirement_source、confidence、behavior_profile、tolerance_profile；报告保留 measurement_status 和最终 status，不隐藏被降级的测量异常。

Runtime Identity 使用独立、CSP 指纹绑定的登记文件。Builder 仅新增可选 `--identity-manifest` 参数，写六个对象 Custom Properties；未提供时不猜身份。身份文件不属于 AG 第七类数据，也不影响 CSP 运动求值。读取到 Native 属性之后，Checker 检查登记身份与计划一致、跨 Cut 持续以及 Owner-local 相对运动。

三个正式案例在 examples/s35 独立副本重建。A–F 复用冻结的 S3 破坏动画副本，G/H 是技术负例。原 Benchmark、S3 归档和 S2 代码不修改。测试详情见 S35-FINAL-REPORT.md。
