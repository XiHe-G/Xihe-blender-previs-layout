# EXECUTION-PATCH/1.0

Schema：`authoring/execution-patch.schema.json`。校验：execution_patch_validator.py；合并：execution_patch_merger.py。

必需：patch_version、patch_id、base_csp_sha256、author_graph_sha256（UPDATED-GRAPH）、changeset_sha256、affected_scope_sha256、execution_binding_sha256、override_registry_sha256、modified_sections、execution_payload、region_decisions、provenance。

execution_payload 是稀疏列表：每项 section、path（JSON pointer）、old_value、new_value。只替换既有标量，拒绝容器、整序列副本、无变化数据、重复路径、类型不符、过期旧值。modified_sections 必须等于实际写入集合。

可选的执行 section：world_tracks、pose_tracks、camera_tracks、weapon_tracks、projectile_tracks、visibility、proxy_lifecycles、shot_execution、event_execution、camera_choreography、continuity、screen_targets、causal_links。这些是旧 CSP 数据的选择器，不改变 CSP 字段语义。track 仍位于旧 object_tracks / actor_pose_tracks；frame_range 是原 CSP 帧号的闭区间。镜头 end_frame_exclusive 保留原有半开语义。

world/camera/weapon/projectile track 可选择 location、rotation、scale、camera_transform 或 lens 等现有通道；visibility 只选隐藏标志，pose 选原姿态状态。record section 只允许既有时刻/phase/breakdown/结果及已规定执行字段，不允许改 ID、ownership 或资产。详细可写路径由 s2_common.selector_paths 与批准索引唯一决定。

每个 dirty region 必须有 region_decisions：region_id、status=UPDATED 或 REVALIDATED_UNCHANGED、reason；实际补丁必须与 disposition 相符。未改但仍有效的依赖区不能静默跳过。空执行补丁仅用于纯 OVERRIDE_CHANGE。

合并顺序：协议/所有输入指纹 → 重算 scope → 校验请求与 UPDATED-GRAPH → 校验每条写入 → 验证锁投影与完整范围 → 显式 resolution → OVERRIDE_CONFLICT 检查 → 在内存副本写入 → 原 CSP validator → AG/CSP 事件 start/peak/end 一致 → 无关区域精确相等 → 新 binding/receipt。任何失败不返回变更包，CLI 只写新的输出目录。

`UNCHANGED-REGION-REPORT.json` 遍历 CSP 全部非 affected 标量，覆盖 Cut/身份/世界姿态/Camera/武器Projectile/visibility/lifecycle/continuity及其余数据，容差为0。Blender 评估另用旧回归容差1e-5；本轮实际最大误差0。

运行：`python scripts/execution_patch_merger.py --csp BASE.csp.json.gz --patch EXECUTION-PATCH.json --graph BASE-GRAPH.json --updated-graph UPDATED-GRAPH.json --changeset CHANGESET.json --binding BASE-BINDING.json --scope AFFECTED-SCOPE.json --registry OVERRIDE-REGISTRY.json --output new-output`。锁释放另传 `--resolution OVERRIDE-RESOLUTION.json`。输出普通 CSP，再交给原 combat_sequence_builder.py。

不从 BLOCK 名称生成姿态，不替代作者给出的 lowering。改变空间意图必须至少改实际所属 motion leaf；通用视觉/语义正确性不在合并器内自动推断。TEST A/B 提供独立专项断言确认具体时间/距离，而不是接受“看起来差不多”。
