# S2 Override Protection

AG/1.0 OVERRIDE 保持原字段与 PROPOSED / LOCKED / RELEASED。执行保护通过独立 OVERRIDE-REGISTRY/1.0；登记时复制 override、添加 protections、source、protected_sha256。source 保存版本、来源、理由和工程 blend_sha256，TEST C 同时保存实际对象、帧区间和手改回执。

LOCKED 在 Changeset 检查与 Patch 合并时生效。命中保护路径或被锁作者通道返回 **OVERRIDE_CONFLICT**，必须带 override、target、channel、patch；不静默忽略，不覆盖，不自动解锁。基 CSP 的保护投影已漂移则 LOCKED_BASE_DIVERGED。

SHOT camera_transform 保护完整镜头帧范围的 location / rotation / rotation_mode / scale。登记源必须提供已检查 parent_chain（无父对象为 []）；CSP 中可动画父对象同范围的变换也必须纳入保护，否则拒绝不完整锁。lens 独立通道，只有显式登记才受镜头焦距锁保护。Entity/其他关键通道通过显式 protections 选择器登记；本轮完整 native 证据针对 SHOT Camera，其他复杂情形不宣称普遍验证。

OVERRIDE-RESOLUTION/1.0 必需 resolution_version、resolution_id、base_registry_sha256、patch_id、resolutions。每项 override_id、decision 以及 authorization（requested_by、source、quote、reason）。协议可审计输入，不是身份认证系统；调用者必须保存真实用户授权，不能编造 quote。

| decision | 行为 |
|---|---|
| KEEP_LOCKED | 保持锁，冲突仍拒绝 |
| RELEASE | 此次明确授权解除锁，AG 状态同步为 RELEASED |
| REPLACE_LOCK | 按此次授权改动后重新捕获受保护执行值并继续 LOCKED |

resolution 绑定确切 registry 指纹和 patch ID，不能重复套用到另一版本。单独 OVERRIDE_CHANGE 请求 RELEASED 不能自我授权。真实 TEST C 没有释放锁；RELEASE/REPLACE_LOCK 只在独立合成单元测试中验证。

人工流程：复制批准工程 → 用 Blender bpy 明确修改指定通道并保存 MANUAL-EDIT.blend → 显式采样这些 Camera 执行值成为新 base CSP → 保存工程指纹并注册锁 → 对无关事件做局部补丁 → 原 Builder 重建 → 将 Camera 本地变换和 world matrix 与人工工程逐帧比较并重开工程。没有自动反推 Graph，没有任意工程手改自动发现。

带活动 LOCKED 的 Graph 不能绕过 S2 直接运行旧 S1 full compiler，返回 OVERRIDE_REGISTRY_REQUIRED。旧测试中“LOCKED 仅结构可忽略”的断言已升级为必须拒绝此路径。Builder 无锁逻辑、行为未改；直接在系统外提交任意 CSP 给 Builder 不属于 S2 的受保护入口。

限制：人工执行快照/所有权索引仍需正确登记；父链、约束/driver/复杂 Rig 的完整影响关系依赖显式资料。没有 Blender ↔ AG 双向编辑，也不自动识别未登记修改。
