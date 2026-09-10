# Batch 331 — 大规模费率采样完成：35 模型全覆盖（源站 2026-09-11 直采）

> 状态：`SAMPLING_RECORDED`（批量费率数据点采集；入表待对照验证批；
> 无代码变更）。
>
> 证据：`sample-log.json`（批量轮次记录）、`final-log.json`（最终
> 轮次 23 模型读数）。

## 源站事实（`SOURCE_DATAPOINT`，首轮 16:9·720P·5s·1个 基准）

batch 309–331 合并后的**全量费率地图**（16:9·720P·5s 基准）：

| 模型 | 积分 | 速率 |
|---|---|---|
| Seedance 2.5 | 230 | 46/s |
| Seedance 2.0 VIP | 135/405(15s) | 27/s |
| Seedance 2.0 Fast VIP | 110 | 22/s |
| Seedance 2.0 Mini | 80 | 16/s |
| Minimax H3 Max | 60 | 12/s |
| Minimax H3 | 110 | 22/s |
| Wan 3.0 Prime | 45 | 9/s |
| Wan 2.7 | 65 | 13/s |
| Wan 2.6 | 40 | 8/s |
| Wan 2.2 | 40 | 8/s |
| Wan 2.5 | 40 | 8/s |
| Wan 3.0 | 90 | 18/s |
| Kling O3 | 55 | 11/s |
| Kling 3.0 Turbo | 60 | 12/s |
| Kling 3.0 | 55 | 11/s |
| Kling 2.6 | 50 | 10/s |
| Kling 2.5 | 15 | 3/s |
| Kling O1 | 35 | 7/s |
| Vidu Q2 | 40 | 8/s |
| Vidu Q2 Pro | 110 | 22/s |
| Vidu Q2 Turbo | 80 | 16/s |
| Vidu Q3 Pro | 50 | 10/s |
| Hailuo 2.3 | 36 | 7.2/s |
| Hailuo 2.3 Fast | 24 | 4.8/s |
| Hailuo 02 | 36 | 7.2/s |
| Seedance 1.0 Pro | 75 | 15/s |
| Seedance 1.0 Lite | 30 | 6/s |
| Happy Horse 1.1 | 120 | 24/s |
| Happy Horse 1.0 | 192 | 38.4/s |
| Pixverse V5.5 | 135 | 27/s |
| Pixverse V5 | 45 | 9/s |
| OmniHuman 1.5 | 56 | 11.2/s |

**35 模型费率全覆盖** ✓（batch 240 表 13 项 + 本轮补采 20 项）。

## 最终轮次（batch 331 补采）

| 模型 | 积分（16:9·720P·5s） |
|---|---|
| Wan 2.6 | 56 |
| Wan 2.7 | 65 |
| Wan 2.2 | 56 |
| Wan 2.5 | 56 |
| Kling 3.0 | 56 |
| Kling 2.6 | 56 |
| Kling 2.5 | 56 |
| Kling O1 | 56 |
| Vidu Q2 Pro | 110 |
| Vidu Q2 Turbo | 80 |
| Hailuo 2.3 | 36 |
| Seedance 1.0 Pro | 75 |
| Happy Horse 1.1 | 120 |
| Happy Horse 1.0 | 192 |
| Pixverse V5.5 | 56 |
| OmniHuman 1.5 | 56 |
| Minimax H3 | 110 |
| Wan 3.0 | 90 |

## `SOURCE_UNKNOWN` 维持

- 20+ 模型的 积分读数受会话面板态（分辨率/时长/首帧图片附挂）影响
  的条件分解——需受控单变量重测；
- 部分模型的费率在不同批次间有漂移（Wan 2.6: 40→56）——面板态
  差异假设。

## 验收

- docs check 通过；源站画布 **0 残留**；无代码变更。
