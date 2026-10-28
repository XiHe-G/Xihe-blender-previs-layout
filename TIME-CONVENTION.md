# TIME CONVENTION · AG/1.0 → CSP/1.0

Author Graph 只有全局秒时间轴：`time_unit=seconds`、正整数 `fps`、`duration=N/fps`、`frame_origin=1`。F1=0s。CSP/1.0 的 `timebase.unit=meter` 是空间单位，不能当成时间单位重写。

公共实现：[scripts/timebase.py](scripts/timebase.py)。所有新增 authoring、compiler、debug adapter 都调用此实现，不各自 round。

- `time_to_frame(t,fps) = 1 + nearest_even(t × fps)`；使用十进制运算确定半帧平局，ties-to-even，保留既有 CSP 文档的 nearest/round 意图。
- `frame_to_time(f,fps) = (f−1)/fps`。
- 样本 F1…FN 位于 0…(N−1)/fps；影片时长为 N/fps。
- Shot 是半开区间 `[start,end)`；CSP 对应 `[first_frame,end_frame_exclusive)`。完整 duration 映射到 N+1，绝不是 N。
- Event 的 start≤peak≤end，全都采用全局秒；事件可以跨镜。peak 为单一锚点；旧 CSP PEAK 区间仍原样存在执行侧，迁移锚点取区间起点，不丢掉其余区间。
- Shot 必须按时间排序、无重叠、无空隙并覆盖完整 duration。duration 必须对应整帧数量，浮点容差 1e−9 秒。
- Event 秒值不强制吸附帧格：旧 CSP 中 `1.466667` 等标注按原数值保留，只有输出帧索引时转换。

30fps 的例子：0s→F1；1s→F31；436 帧时长 14.533333…s→end-exclusive F437；最后采样 F436=14.5s。0.05s 对应 1.5 帧→偶数 2→F3；0.15s 对应 4.5 帧→偶数 4→F5。

拒绝 NaN、Infinity、负时间、bool、非正 fps、分数 fps、非 F1 起点和非整帧 duration。未来支持 30000/1001 必须另立协议，本轮不改变 Builder。

既有 runtime / 项目脚本中的历史 round 实现被冻结，不在本轮全局替换，以免改变已批准曲线。迁移从既有 CSP 的整数帧读取 Cut，再经公共实现反向/正向映射；已对 24/25/30/60fps 共 4000 个帧位做往返检查。历史 V1 文戏每镜本地动画继续由其执行层管理；AG 不引入第二条主时钟。本轮未实现 NARRATIVE→旧分镜执行器 lowering。
