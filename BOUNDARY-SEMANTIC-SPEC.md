# Boundary Semantic

版本 1.7.0；S5.3R 修复阶段，非 S5.4。INTEGRATION_PILOT_ONLY / SELF_REVIEW。

CONTINUOUS / CONTINUOUS_TRANSITION：默认原S45相对C1规则，零起停语义不适用于非零边界。

AUTHORED_START：实际entry velocity为0或近零，必须有可见采样加速窗口；禁止第一移动帧骤达高速。

AUTHORED_STOP：对称检查出口，必须有减速窗口。不是最后一帧强制设零。

SMOOTH_OFFSET：分别检查start→peak、peak→end的偏移分量包络；RETURN_TO_BASE入口/出口偏移为0，偏移导数为0；KEEP_OFFSET保留位置但终端导数为0。TRANSITION_TO_NEW_PATH继续旧合同，不借起停语义豁免显式非零速度转换。

IMPACT / CUT_RESET / TELEPORT：继续使用原S45授权声明、Graph SHA、Event、subject和导数范围；单独字符串不是豁免凭据。UNINTENDED_DISCONTINUITY由失败代码表示，不能自动转成授权。

Native复验使用实际对象采样和全局时间轴内的真实guard；只有时间轴外使用明确入口/出口延拓。native seam和runtime angular都保留。C0必须有原线性执行/单侧极限证据，不能由起停语义制造。C2 WARNING/FAIL不清除，本阶段只记录。

所称C1仍是离散采样质量合同，不是所有子帧的解析可微证明。普通连续运动旧profile数值完全不变；新包络只用于显式启用的作者起停/平滑Offset。请勿将该有限合同描述成通用物理保证。
