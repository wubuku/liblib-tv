# Batch 114：多画布下拉对齐 2026-09-06 丢弃式采样

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-09-06。
>
> 上一批 checkpoint：Batch 113。
>
> 源站证据：[`../liblib-canvas-sampling-2026-09-06/README.md`](../liblib-canvas-sampling-2026-09-06/README.md) §1。

本批把画布下拉对齐丢弃式项目采样：行结构改为「切换到画布 X」+ hover 门控
「更多操作」双按钮；行级菜单四项（在新窗口打开/重命名画布/复制画布/删除
画布）；删除确认框（此操作不可恢复）；副本命名 `{名称}副本{n}`；下拉按
创建时间倒序；删除活动画布回退到创建序相邻画布。

## 导航

- [PLAN.md](PLAN.md)：范围、证据边界与不包含项。
- [runtime-audit.json](runtime-audit.json)：结构化运行时证据。

## 证据边界

| 标签 | 本批含义 |
|---|---|
| `SOURCE_FACT` | 行结构、行级菜单四项、确认框文案、副本命名、最新在前排序 |
| `CLONE_DECISION` | 新窗口打开为 no-op、副本序号计算、删除 fallback 取创建序前一画布 |
| `SOURCE_UNKNOWN` | 副本再复制的命名、更多画布时的排序表现 |

## 实施结果

- `CanvasTabDropdown`：行双按钮重构（switch aria `切换到画布 X` + more aria
  `更多操作`），四项菜单，`data-canvas-delete-confirm` 确认框；创建时间倒序。
- `canvasStore.duplicateCanvas`：副本命名 `(副本)` → `{名称}副本{n}`；
  `removeCanvas` 删除活动画布回退到创建序相邻画布。
- `data-canvas-row`/`data-canvas-trigger` 保留（batch13/64/65 复跑通过）。

## 完成定义

1. `verify-liblib-batch114.py` 20 checks、`0/0/0` diagnostics 通过。
2. 相邻 `verify-liblib-batch13/64/65.py` 通过。
3. `npm run check`、`npm run docs:check` 通过。
4. master commit/push。

通过结果只证明 clone-owned 多画布下拉合同；在新窗口打开行为与副本再复制
命名仍是 `SOURCE_UNKNOWN`。
