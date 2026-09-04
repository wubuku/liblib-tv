# Batch 101：生成历史面板对齐 2026-09-05 源站

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-09-05。
>
> 上一批 checkpoint：Batch 100（`batch/100-empty-canvas-state`）。

本批把生成历史模态对齐 2026-09-05 源站：标题、缩略图尺寸 slider、本画布
chip、图片/视频/音频计数 tab、所有评级下拉、空态文案，以及底部工具条入口
更名（历史记录 → 生成历史）。全部为本地状态，不接历史数据服务。

## 导航

- [PLAN.md](PLAN.md)：范围、证据边界与不包含项。
- [runtime-audit.json](runtime-audit.json)：结构化运行时证据。

## 证据边界

| 标签 | 本批含义 |
|---|---|
| `SOURCE_FACT` | 标题 `生成历史`、slider 尺寸控制、本画布 chip、三 tab+计数、所有评级/时间倒序/批量操作、`暂无历史记录`、底部工具条入口命名 |
| `CLONE_DECISION` | slider 取值范围、评级菜单选项（所有评级/已收藏）与 favorites 本地过滤、计数沿用本地 mock |
| `SOURCE_UNKNOWN` | 评级菜单真实选项、本画布筛选完整行为、历史项非空态源站样式 |

## 实施结果

- `HistoryPanel`：标题/aria 改为 `生成历史`（`primary:history` overlay id 不变）；
  +/− 步进改为两端网格图标 + range slider（本地 zoom 50–150）。
- 筛选行：本画布 chip（`aria-pressed`）+ `图片 3 / 视频 0 / 音频 0` 计数 tab；
  右侧 `所有评级` 本地下拉（`已收藏` 按既有 favorites 过滤）+ 时间倒序 + 批量操作。
- 空 tab 文案统一 `暂无历史记录`；收藏为空的图片 tab 也落入空态文案。
- `LeftSidebar` 底部工具条入口 `历史记录` → `生成历史`（同位置同 action，
  overlay 机制不变，batch11/62 复跑通过）。

## 完成定义

1. `verify-liblib-batch101.py` 20 checks、`0/0/0` diagnostics 通过。
2. 相邻 `verify-liblib-batch11.py`、`verify-liblib-batch62.py` 通过。
3. `npm run check`、`npm run docs:check` 通过。
4. 特性分支 commit/push。

通过结果只证明 clone-owned 生成历史展示合同；真实历史数据、评级后端与
非空态源站样式仍是 `SOURCE_UNKNOWN`。
