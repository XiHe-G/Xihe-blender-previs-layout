# S5.1 Execution Primitive Runtime

正式 Skill 仍为 **1.7.0**。V1.8 是研发名称。本层只接受显式执行参数，六个 fixture 是技术验收，不是新导演 Benchmark。

```text
EXECUTION-PRIMITIVE/1.0 + global timebase + declared read tracks
  → schema / channel ownership / dependency checks
  → six motion kernels + six camera kernels
  → sampled entry/exit contracts + unchanged S4.5 boundary validator
  → PRIMITIVE-EXECUTION-FRAGMENT/1.0
  → fresh-fixture CSP merger (reject failed C0/C1, conflicts, stale payload)
  → ordinary CSP/1.0 → original combat_sequence_builder.py
  → save → reopen → Actual Trace → existing S3.5 measurements
```

没有 Author Event→Primitive 选择，没有 AG 字段变化，没有新的导演对象。`entry_from` 是执行片段之间的显式合同引用；它不是作者事件推导。已有项目/LOCKED 内容必须走 S2，本合并器只接收声明为 fresh 的技术初始化 CSP。

模块边界：

| 文件 | 职责 |
|---|---|
| primitive_sampler.py | 纯数值向量/四元数、路径、积分速度曲线、确定性读取；只调用既有 timebase 转换 |
| motion_primitives.py | 6 个参数化运动工具，无 bpy |
| camera_primitives.py | 6 个摄影机执行工具；直接导入 S3.5 Hold profiles / checker |
| primitive_channel_registry.py | 显式 READS、READ_CHANNELS、WRITES 与三种组合权限 |
| primitive_runtime.py | 协议验证、读依赖排序、合同、边界报告、诊断、SHA |
| primitive_fragment_merger.py | 按通道输出普通 CSP 样本；拒绝冲突、坏合同和陈旧 payload |
| tests/primitive_fixtures.py | 参数与静态 COMBAT_BOX_4 场景配置；无运动实现 |
| tests/run_s51_fixtures.py | 原 Builder、重开逐值对比、Native metadata、原 Checker 与边界验收 |

Runtime 不访问 Blender、随机源、当前时间或隐式 Scene。相同描述、时间基准与读轨迹生成相同 JSON 数值及规范 SHA。环境/代码升级后的跨版本位级一致性不作保证；交付另外冻结实现文件 SHA。

正式 Builder、CSP 语义、AG/1.0、S3.5 profile、S4.5 阈值及正式 Benchmark 全部保留。S5.1 停止于技术 Runtime；进入 S5.2 需要下一轮人工审核。
