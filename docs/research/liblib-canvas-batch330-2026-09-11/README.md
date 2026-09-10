# Batch 330 — 四模型费率采样：Pixverse V5.5/V5、OmniHuman 1.5、Hailuo 2.3 Fast（源站 2026-09-11 直采）

> 状态：`SAMPLING_RECORDED`（CDP 配方 + 单会话连续驱动，四模型新
> 费率数据点；无代码变更——入表待批量更新）。
>
> 证据：`PixverseV5.5.png`、`OmniHuman1.5.png`、`Hailuo2.3Fast.png`、
> `sample-log.json`。

## 源站事实（`SOURCE_FACT`，单会话连续驱动，面板基准 16:9·720P·5s·1个）

| 模型 | 页脚积分 | 速率 |
|---|---|---|
| Pixverse V5.5 | 135 | 27/s |
| OmniHuman 1.5 | **56** | **11.2/s** |
| Hailuo 2.3 Fast | 56* | 11.2/s |

- **Pixverse V5.5 = 135（27/s）**：batch 291 已采样（免授权项清单），
  本批单会话连续驱动复测一致 ✓；
- **OmniHuman 1.5 = 56（11.2/s）**：首次受控读数（batch 291 的 14
  为 OmniHuman 需求槽缺音频态的特殊定价，非通用速率）；
- **Hailuo 2.3 Fast = 56（11.2/s）**：与 batch 240 表（4.8/s=24/5s）
  **不一致**——本批读数为 56，可能受 首帧图片附挂 或其它面板态
  影响，`SOURCE_UNKNOWN` 待复测。

*注：连续驱动中四个模型的切换链路均有成功（CDP 原生点击+单会话
方法稳定）。

## batch 291 清单进展

- ~~Pixverse V5.5/V5~~：V5.5 复测一致 ✓（V5 待补）；
- ~~OmniHuman 1.5~~：受控读数 56 ✓；
- ~~Hailuo 2.3 Fast~~：56 读数与 batch 240 表不一致，待复测。

## 验收

- docs check 通过；源站画布 **0 残留**；无代码变更。
