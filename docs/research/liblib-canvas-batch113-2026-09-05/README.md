# Batch 113：角色卡片条均匀间距

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-09-05。
>
> 上一批 checkpoint：Batch 112（`batch/112-character-filter-panel`）。

源站补采样截图（`../liblib-live-2026-09-05/original-character-library-modal.png`）
显示角色卡片条为均匀 ~19px 间距；clone 曾对第 3/4 位卡片附加 `ml-[6px]`
（clone 历史残留）。本批移除该 hack，卡片条统一 `gap-[19px]` 节奏。

## 证据边界

| 标签 | 本批含义 |
|---|---|
| `SOURCE_FACT` | 卡片条均匀间距节奏（截图观察） |
| `CLONE_DECISION` | 移除位次特判，保留 19px gap |
| `SOURCE_UNKNOWN` | 源站精确像素值（截图粗读） |

## 验证

- `verify-liblib-batch113.py`：前 6 张卡片 x 轴间距一致、`0/0/0` diagnostics。
- 相邻 batch111 通过；`npm run check`、`npm run docs:check` 通过。
- 特性分支 commit/push。
