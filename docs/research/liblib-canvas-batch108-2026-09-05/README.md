# Batch 108：普通画布对齐系列跨批回归（Batch 97-107）

> 状态：`REGRESSION_RECORDED_PASS`（含 12 项既有漂移归因）
>
> 建档日期：2026-09-05。
>
> 上一批 checkpoint：Batch 107（`batch/107-skill-headline-rotation`）。

照 Batch 93 模式，对 Batch 97-107 普通画布对齐系列执行全量 verifier 串行
回归，并对失败项做基线归因。

## 结果总览

- 串行队列 101 项（`scripts/verify-liblib-batch*.py` 全量）：**81 项通过**。
- 首轮 20 项失败中，12 项为环境问题（后台 shell 缺 nvm PATH，`node` 子进程
  不可达）；带 PATH 复跑后 batch65、67-73、76 全部通过。
- 剩余 12 项（batch 6、9、40、41、44、46、48、49、51、72、74、75）在基线
  提交 `86673b6`（Batch 96 收口点）上**同样失败**——归因为**既有漂移**，
  非 Batch 97-107 引入。

## 既有漂移清单（归因证据）

| verifier | 现象 | 基线 `86673b6` | 判定 |
|---|---|---|---|
| batch6 | 空白框选矩形不出现 | exit=1 | `HISTORICAL`：Batch 77 已将空白拖拽改为 no-op，marquee 断言被取代（AGENTS.md 有记录） |
| batch9 / batch51 | 图片工具条实测 `1092.5 x 900.5` | exit=1 | 旧几何断言漂移，属 `LIBTV-VR-001` 替换队列 |
| batch40 / 41 / 44 / 46 / 48 / 49 | Director 早期浏览器 gate 断言失败 | exit=1 | 已被 Batch 59、67-96 current gates 取代的旧 gate |
| batch72 / 74 / 75 | `.mjs` 子验证器/等待超时失败 | exit=1 | 早期 Director pure/浏览器 gate 漂移，已被后续批次取代 |

处理建议（不在本批执行）：按
[`../LIBTV_VERIFIER_REPLACEMENT_MAP.md`](../LIBTV_VERIFIER_REPLACEMENT_MAP.md)
把这 12 项标为 `HISTORICAL_CONTRACT` 或排入退役/重写队列。

## 当前有效 gates 结论

- 全部 Batch 97-107 专项 verifier：通过。
- 普通画布受影响面（batch11/12/13/14/15/17/23/24/25/26/62/64/65）：通过。
- Director current gates（batch59、67-76 中除 72/74/75 既有漂移外、82/92-96
  中的本轮复跑项）：通过。
- `npm run check`、`npm run docs:check`：通过。

## 完成定义

1. 串行回归与基线归因记录于 [runtime-audit.json](runtime-audit.json)。
2. 无 Batch 97-107 引入的回归。
3. 治理文档更新；特性分支 commit/push。
