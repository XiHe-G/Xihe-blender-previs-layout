# Evidence Sufficiency / S35

每项报告都有 evidence_sufficiency。先检查采样覆盖、对象/几何/投影/必需射线证据，再进行测量，最后限制结论强度。旧 UNKNOWN 和纯艺术语句仍为 NOT_REVIEWED。

| Level | 最终结果规则 |
|---|---|
| ENOUGH | 数据与明确可测条件足够；可以 PASS/FAIL，仍只对记录条件成立 |
| PARTIAL | 通常最多 WARNING；只有已记录的独立强证据允许 FAIL |
| INSUFFICIENT | 必须 NOT_REVIEWED，不得因缺证据 FAIL |

强证据包括原生身份/Owner明确不符、身份重建、实测瞬移、完整 Owner-local 窗口未脱离、真实几何 Contact、明显大 Camera 运动。缺失 Owner、无注册源、采样缺帧不是错误证据。

SCREEN_DIRECTION 的依据固定为 PROJECTED_CENTER，不是 VISIBLE_PIXEL。射线不足不阻止有有效中心和 clipped bounds 的轨迹测量；完全出画或缺投影仍 NOT_REVIEWED。投影矩形中心已落出画框时仍给出方向数值，但证据为 PARTIAL / WARNING，防止严重裁边/近裁面放大造成假 FAIL。不存在可见像素方向的认证。

requirement_source 六值：USER_AUTHORED、DIRECTOR_AUTHORED、SOURCE_REFERENCE、HISTORICAL_LABEL、TECHNICAL_DEFAULT、INFERRED；confidence 为 HIGH/MEDIUM/LOW。来源与容差来源分别记录。任一使用默认阈值的结果显示 DEFAULT ASSUMPTION。INFERRED/LOW/HISTORICAL_LABEL 不因符合默认值获得强 PASS。

保留 measurement_status（测量对条件的结果）与 status（证据限定后的结论）。报告带 Author ID、对象、时间/帧、trace JSON pointer、Plan/Actual、源 Blend 指纹。严重程度与证据量分开；MINOR/INFO 的原规则仍可降为 WARNING。

限制：几何距离和遮挡为估计；30fps不检查帧间连续碰撞；注册标签不能独立证明真实导演意图；静态 Native 属性不是防篡改签名。
