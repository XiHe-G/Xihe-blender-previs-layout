# ACTUAL-TRACE/1.0

Schema：runtime/actual-trace.schema.json。输入为已有.blend与测量binding；不从CSP执行采样复制Actual。支持COMBAT_BOX_4、NARRATIVE_BOX_5及武器/Projectile/Proxy的既有Mesh或Mesh组，按显式对象列表采样，不依赖Rig风格名。成熟复杂约束/Rig没有通用验证。

容器：graph_id、measurement_binding_sha256、source_blend文件指纹、timebase、sampling、methods、frames。methods包含本轮exporter/projection/motion/timebase代码指纹。source文件导出前后校验，Exporter不保存输入工程。

逐帧字段：shot_id、frame、time、entities、camera_transform、camera_lens、camera_motion、pairwise_distance、event_state。实体记录entity_world_state、screen_bounds/center/height_ratio/width_ratio、visibility、occlusion_ratio、世界/屏幕motion_vector与speed、proxy_state、ownership_state、实际对象名/identity_token、exists。缺失对象显式exists=false。

屏幕坐标原点为左下，u向右、v向上；世界距离单位米，速度米/秒，镜头lens毫米、转角度。

原生Timeline Camera marker决定实际Shot/Camera；不是把Plan镜头表当执行结果。每帧读取evaluated dependency graph，Camera父变换也在world matrix中。世界速度用相邻全局帧；屏幕速度在Cut处置null，避免把换机位当成主体瞬移。Camera记录位置、旋转、lens及连续镜头内位移/转角。

投影计算实际Mesh顶点及跨越近/远裁面的边，不使用3D bbox冒充可见像素框。记录projected_bounds、clipped_bounds、visible_fraction_estimate、投影状态。screen_height_ratio是投影矩形高度；可从clipped_bounds审计裁剪后高度。矩形包含空白和被遮挡区域，面积比例是ESTIMATED，不是像素覆盖率。部分出画、完全出画、相机后方和跨近裁面均有原生bpy测试。

遮挡采用最多17个可投影顶点到Camera的射线，跳过hide_render物体；标签VISIBLE/PARTIAL/MOSTLY_OCCLUDED/HIDDEN始终ESTIMATED。没有有效样本则occlusion_ratio=null，相关可见性不能PASS。不是透明材质/毛发/体积/运动模糊的像素精确解法；render collection/复杂可见性配置需额外审查。

几何对：BVH三角形相交、闭合体包含检查及顶点到另一表面的最近距离估计。接触记clearance=0，非接触给正距离；不计算穿透深度。共面重合表面通过近零距离识别。非凸/开放网格、极细边对边及帧间高速穿越存在误差/漏检风险。没有subframe swept collision；只能证明所采帧的代理几何关系。

screen_center_distance与screen_bounds_gap_estimate分开。大球部分出画时，中心距不能代替可见边缘关系；Near Miss可明确选择bounds_gap指标，同时独立要求世界几何净空。

Owner的registered_owner只记录作者提供的来源关系；native_owner仅来自场景s3_owner_id属性。旧案例没有native属性则Owner为NOT_REVIEWED。owner_relative从实际世界位置计算，可用于检验Release后是否仍黏在指定Owner。release_time是注册事件时刻，并非Exporter自动发现的释放；缺失保留null。event_state明确标REGISTERED_WINDOW_ONLY_NOT_PHASE_DETECTION。

命令：`blender --factory-startup -b --python-exit-code 1 --python scripts/actual_trace_exporter.py -- --blend LAYOUT.blend --binding MEASUREMENT-BINDING.json --output ACTUAL-TRACE.json.gz`。本轮三例按原30fps完整逐帧采样，共1328帧，无采样降帧。
