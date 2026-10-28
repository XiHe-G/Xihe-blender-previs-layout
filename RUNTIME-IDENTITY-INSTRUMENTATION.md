# Runtime Identity Instrumentation /1.0

Builder 新增可选 `--identity-manifest <RUNTIME-IDENTITY.json>`。独立文件保存 graph_id、source_csp_sha256、registration_basis 与 objects{name: properties}。Builder 对 CSP 文件指纹校验；登记对象必须存在，Owner必须指向登记 Entity；先验证全部条目再写 metadata。过期或无效登记拒绝。

六个字符串 Custom Properties：previs_entity_id、previs_owner_id、previs_event_id、previs_projectile_id、previs_weapon_id、previs_role。字符组的 Root/组成Mesh共享实体ID；每件持久武器/Projectile使用原AG稳定ID。无唯一事件的角色使用空event字段，不能虚构事件。逻辑VFX组明确映射到现有组成员，不创建/改父子关系/改几何。

Exporter优先读取 previs_entity_id/previs_owner_id；保留 registered_entity_id供对照。identity_evidence与ownership_evidence为 NATIVE_OBJECT_PROPERTY、REGISTERED_BINDING、INFERRED 或 UNKNOWN。缺 Native 时记录 REGISTERED_METADATA_ONLY / WEAK_EVIDENCE，登记绑定不能假充 Actual Owner。

Native属性证明运行对象保留了已登记身份，不证明作者登记本身正确，更不是自主归属推理。Owner-root取自明确测量绑定；Owner-local位置采用其实际 evaluated matrix 的逆变换，能识别随旋转Owner一起运动但相对不变的Projectile。可测窗口和脱离阈值必须明确；Open End合法，不要求对象消失。

本轮改变Builder的范围仅为metadata可选入口/校验/保存。所有Transform、曲线、Visibility、Timing、角色结构、Camera和VFX语义不变。三个案例逐帧1,328帧、全部既有求值输出按0容差比较，原动画曲线签名不变；保存后重开逐值确认全部登记属性。证据：examples/s35/INSTRUMENTATION-REGRESSION.json，以及工作区 evidence/FINAL-BUILDER-REGRESSION.json。后者由含最终指纹校验代码的Builder重建。

使用方式：现有 Builder 命令追加 --identity-manifest；然后按原 Actual Trace exporter 参数读取保存的Blend。未提供身份文件的旧工作流保持原行为和弱证据回退。
