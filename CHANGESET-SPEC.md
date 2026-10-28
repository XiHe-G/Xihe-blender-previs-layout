# CHANGESET/1.0

Schema：`authoring/changeset.schema.json`。入口：`scripts/change_analyzer.py`。

必需：changeset_version、changeset_id、base_graph_id、base_graph_sha256、author、reason、changes。每个 change：change_id、change_type、target、channel、old_value、new_value、requested_by、provenance。版本值为 CHANGESET/1.0。

| 类型 | target | channel |
|---|---|---|
| EVENT_TIMING_CHANGE | EVT_xxx | start / peak / end / time_range；time_range 为 [start,peak,end] |
| EVENT_SPATIAL_CHANGE | EVT_xxx | world_intent / screen_intent，保留 AG 意图结构 |
| SHOT_INTENT_CHANGE | SHOT_xxx | primary_information、shot_size_intent、screen_direction_intent、camera_behavior_intent、required_visibility、handoff_to_next |
| OVERRIDE_CHANGE | OVR_xxx | status；LOCKED 的释放必须另有显式 resolution |

全局秒，帧映射继承 TIME-CONVENTION.md。旧值必须与基图逐值一致；未知目标、重复写入、无操作、非法时间/引用、基图指纹失配均拒绝。不接受新作者集合或修改依赖拓扑。

AFFECTED-SCOPE/1.0 输出 directly_changed、dependent_events、affected_events、affected_entities、affected_shots、affected_execution_channels、protected_overrides、unaffected_shots、unaffected_entities。另含 dependency_trace、region_ids、allowed_paths 与全部基准指纹，供审计与拒绝过期 patch。scope 由合并器重新计算，不能靠手改 scope 扩大写权限。

SHA-256 的协议含义：UTF-8、JSON 键排序、无空白分隔、ensure_ascii=false、禁止 NaN/Infinity；对解析后的数据计算，不对 gzip 容器字节计算。工程文件/源产物另用文件字节 SHA-256。不同用途的指纹不能互换。

示例见 examples/s2/timing-edit/CHANGESET.json；用户只修改 EVT_BLOCK 的时间三元组，依赖下游变更由作者在 UPDATED-GRAPH 和局部 lowering 中明确提供。分析器自身不改动作。

运行：`python scripts/change_analyzer.py --graph BASE-GRAPH.json --changeset CHANGESET.json --binding BASE-BINDING.json --csp BASE.csp.json.gz --registry OVERRIDE-REGISTRY.json --output AFFECTED-SCOPE.json`。
