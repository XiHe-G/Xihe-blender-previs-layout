# EXPECTED-OBSERVABLES/1.0

Schema：authoring/expected-observable.schema.json。容器包含schema_version、graph_id、graph_sha256、measurement_binding_sha256、observables、not_reviewed。

每项：observable_id、source_author_id、shot_id（跨镜为null）、time_window、type、subjects、expected_range、expected_state、tolerance、severity、provenance。时间为全局秒半开区间[start,end)，沿用timebase.py，F1=0。容差必须非负，量纲随指标：米/秒/度/毫米或归一化屏幕单位。

受控编译入口：AG CONSTRAINT.requirement字符串以`OBSERVABLE/1.0 `开头，后接JSON测量声明。原AG schema不扩展；混合Shot/Entity/Event引用使用原SEQUENCE scope。subjects引用测量view，其entity_id必须在constraint.targets；shot_id也须在targets。声明必须AUTHORED或SOURCE，INFERRED/UNKNOWN不自动接受。

例如：

```json
{"type":"SHOT_SIZE","subjects":["YOUTH_HEAD"],"shot_id":"SHOT_005","time_window":[6.733333333333333,8.533333333333333],"expected_range":[0.45,0.60],"expected_state":{"axis":"height"},"tolerance":0.002,"severity":"MAJOR"}
```

SHOT_INTENT中的精确受控词也可转换：shot_size_intent为XS/SMALL/MEDIUM/LARGE/EXTREME；screen_direction_intent中的明确位置LEFT/RIGHT/CENTER/UPPER/LOWER；camera_behavior_intent为HOLD。须有明确subject及default测量view。其他自然语言、艺术意图不猜数值。事件的时间/peak由显式技术约束引用，不把仅有ATTACK名称自动当完整测量合同。

尺寸分档是S3操作约定，非摄影行业通用认证：XS=[0,.10]、SMALL=[.10,.25]、MEDIUM=[.25,.45]、LARGE=[.45,.70]、EXTREME=[.70,1.50]。明确百分比优先。LEFT x=[0,.45]、RIGHT x=[.55,1]；其余区域或归一化[xmin,ymin,xmax,ymax]见Checker spec。不要求像素逐点一致。

类型共8家族，CONTACT/NEAR_MISS有两个type标签。expected_state仅保存对应测量参数；缺必要阈值返回NOT_REVIEWED，不能自行补一个能通过的标准。min_visible_fraction、max_occlusion可给出明确可见性/遮挡要求，不新增独立第九类Checker。

Expected包需与当前AG和binding逐值重编译一致；过期或手改容差绕过作者源将被拒绝。canonical SHA-256继承S2 JSON排序规范。测量声明不等于用户批准或视觉通过。

命令：`python scripts/plan_to_observables.py --graph AUTHOR-GRAPH.json --binding MEASUREMENT-BINDING.json --output EXPECTED-OBSERVABLES.json`。
