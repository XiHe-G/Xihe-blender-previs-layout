# Primitive Composition

通道注册：ROOT_LOCATION、ROOT_ROTATION、BODY_ROTATION、HEAD_ROTATION、WEAPON_TRANSFORM、PROJECTILE_TRANSFORM、ATTACHMENT_STATE、CAMERA_LOCATION、CAMERA_ROTATION、CAMERA_LENS。

每个 Primitive 声明 READS（对象/片段引用）、READ_CHANNELS 和 WRITES。编译前进行 ID 唯一、读依赖和写通道冲突检查。并行位置与 Body/Head 朝向可共享对象，但必须显式 ORTHOGONAL_CHANNEL；两个同时写 Root Location 的普通 Primitive 会 CONFLICT。

只允许三种组合：

1. **SEQUENTIAL**：A 结束时 B 开始。逐通道比较实际出口/入口，不能最后写入者覆盖。Camera 可使用 entry_from 明确取前片段状态；没有自动选择。
2. **ORTHOGONAL_CHANNEL**：同时写同一对象的不同通道，例如 Move + Body Orient。读者等待依赖轨迹完成。
3. **EXPLICIT_ADDITIVE_OFFSET**：明确 base primitive + OFFSET_PATH。只累加 offset，不替换主路线；普通两个 Root 曲线不能借此自动 blend。KEEP_OFFSET 的后续通道影响继续占用，不能静默影响另一 Recovery。

合并器验证 fragment schema、SHA、pose mirror、C0/C1；只合入 fresh 技术 CSP。它输出 actor_pose_tracks 和 object_tracks，Body/Head quaternion 转为既有 BoxRig 的局部欧拉字段。无新 Builder 分支、无 bpy 调用。

非写入通道保持初始化数据；世界位置在 primitive 外按明确入口/出口常速延续。顺序片段覆盖自己的时窗；外侧延续只属于最早/最晚的通道所有者。输出必须通过旧 CSP validator。既有项目、人工 LOCKED 或部分重编译仍由 S2 的 analyzer/patch/override/merge 审判，本入口不替代 S2。

Gate 包括组合后 Native Trace 的真正邻接采样。孤立片段边界报告不够证明组合安全。C2 记录，C0/C1 不符合合同则 fixture FAIL；不扩大 S4.5 阈值。
