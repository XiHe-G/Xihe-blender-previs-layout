# Motion Primitive Kernel

仅以下六种。Root/对象运动是可采样轨迹，不生成脚步、武术招式或人体姿态库。

| Primitive | 参数和执行职责 | 输出/限制 |
|---|---|---|
| MOVE_PROFILE | end_position；可指定 start_position、entry_velocity / start_velocity、exit_velocity / end_velocity、peak_velocity、path_type、timing_profile | 从入口到出口；边界速度与路径切线不一致则拒绝 |
| ORIENT_TO | ROOT/BODY/HEAD/WEAPON；WORLD_DIRECTION/WORLD_POINT/ENTITY；target / target_entity / target_point；lead_delay、max_angular_speed、SNAP/SMOOTH/LEAD/LAG | 默认平滑、四元数限速；Body/Head 转换为父控制空间；非根父链需显式 parent_orientation_track |
| APPROACH_TARGET | target_entity/target_point、desired_distance、arrival_time、approach_direction、entry/exit velocity | MOVE 与平滑朝向组成；停在指定距离，不移动到目标中心；目标未来位置必须来自显式轨迹 |
| OFFSET_PATH | base_primitive 或 base_path、方向/距离、peak_time、return_mode | 五次平滑权重；RETURN_TO_BASE 归零，KEEP_OFFSET 保持，TRANSITION_TO_NEW_PATH 需显式 new_path |
| ATTACH_DETACH | owner、attachment_transform.position、detach_time/velocity/direction、inherit_owner_velocity、可选 release_ramp_duration / reattach_time | Owner socket 的位置/方向参与计算；显式释放继承；ATTACHED→DETACHING→FREE；可验证位置吻合的 REATTACHED |
| RECOVERY_PROFILE | entry/exit velocity、duration、displacement_limit、direction_retention、可选 orientation_recovery | 积分减速，方向保持约束与总位移约束；可写 Body Orientation，不发明复杂人体表演 |

MOVE 路径：LINEAR（两个端点）、BEZIER_SIMPLE（四控制点、固定 512 段弧长近似）、POLYLINE。Polyline 的尖角不是光滑曲线：原 C1 检查会拒绝不满足合同的拐角；不偷偷平滑，也不自动混合任意轨迹。

Timing：CONSTANT、EASE_IN、EASE_OUT、EASE_IN_OUT、ACCEL_CRUISE_DECEL、CUSTOM_NORMALIZED_CURVE。Ease 是 spacing，不冒充物理。ACCEL_CRUISE_DECEL 使用首尾各 25% 的平滑速度坡段和中间巡航，依据距离、时长、入口/出口速度解巡航峰值；不相容的显式 peak 会拒绝。自定义归一化曲线使用单调 Hermite，端点 0/1，时间严格递增；不是可随意过冲的速度数据。

释放可选 ramp 明确控制自由段获得额外速度的过程；未提供 ramp 的瞬时速度变化必须通过原边界合同或具有事件授权。Native owner property 保留**来源 Owner 身份**，物理状态 FREE 单列 ownership_samples；不是释放后仍绑定的证据。Program `entity_ids` 必须和 primitive 的 native_entity/native_owner 注册吻合。

边界状态中的数值是采样/显式合同值。Blender 使用既有 LINEAR F-curves，因此 C0 是同一节点连接，C1/C2 是有限差分质量检测，不宣称连续时间解析 C1/C2。只有技术 fixture 已验证；不可达参数、尖角、过短窗口会被拒绝而非自动修复。
