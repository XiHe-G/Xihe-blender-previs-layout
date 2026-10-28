# EXECUTION-PRIMITIVE/1.0

执行协议，不能表达“选择哪个导演动作”。Schema 位于 `authoring/execution-primitive.schema.json`；它同时验证单个 primitive 和显式 program envelope。

单体必填：`primitive_version`, `primitive_id`（PRIM_ 前缀）, `primitive_type`, `actor`, `subjects`, `start_time`, `end_time`, `entry_state`, `parameters`, `exit_requirements`, `continuity_contract`, `provenance`。只允许 6 Motion + 6 Camera 类型。单体不允许未知顶层字段；类型相关参数由 schema 和数值检查共同验证。

Program：`program_version=EXECUTION-PRIMITIVE/1.0`, `timebase`, `primitives[]`, `composition[]`；可含显式 `read_tracks`、`entity_ids` 和只可收紧的 `seam_tolerance`。读依赖缺失/循环会拒绝。使用 `entry_from` 时，前片段实际出口成为后片段入口，原请求 SHA 仍保留。与同对象相关的轨迹读者等待其窗口内全部显式运动写者完成。

时间继续使用 `timebase.py`：全局秒、整数 fps、F1=0；采样覆盖 primitive 起止点，起止必须在原帧网格。CSP 的 duration 是片长，最后可执行样本是 F_N=(N−1)/fps，不能把 duration 本身当成最后一帧。没有第二套 round。路径/位置/速度分别使用 m、m/s；角速度参数使用 °/s，诊断用 rad/s；四元数为 Blender wxyz。

ENTRY/EXIT 至少记录 position、velocity、movement_direction、orientation、angular_velocity、ownership_state、support_state；Camera 另外记录 lens、subject_screen_position、subject_screen_size、camera velocity（actual 中由 velocity 表示）。入口位置/速度和显式出口要求都检查；不可达的峰值、时长/位移冲突、错切线、限幅越界直接拒绝，不改目标。默认求得的速度/峰值记录 DERIVED。

连续性：`C0_REQUIRED=true`, `C1_REQUIREMENT=REQUIRED|AUTHORIZED_DISCONTINUITY`, `C2_POLICY=RECORD|PREFERRED`。S4.5 数值阈值保持原文件。孤立片段使用明确的入口/出口常速延续守护样本；组合后的 Native Trace 用真正相邻采样重验。孤立分析不是全序列证明。

授权不连续必须带原 S4.5 接受的有来源、事件、主体、时间窗、导数范围和 SHA 的证据。只写 AUTHORIZED_DISCONTINUITY 字符串不能绕过检查；这是既有边界权限验证，不是 Author Event→Primitive lowering。

Fragment schema：`authoring/primitive-execution-fragment.schema.json`，可验证单体及 composite envelope。包含 affected_entity、time_range、world_samples、pose_samples、ownership_samples、metadata、实际 entry/exit、channel ownership、continuity_report。BODY/HEAD 姿态样本明确列出。`execution_sha256` 绑定执行样本、所有权、通道、合同与边界；pose mirror 必须与主采样一致。

PRIMITIVE-DIAGNOSTIC 包含原参数、derived 参数、entry/exit actual、boundary、通道、警告和 sample count。技术默认值与投影估计明确标注，不是导演批准的艺术标准。
