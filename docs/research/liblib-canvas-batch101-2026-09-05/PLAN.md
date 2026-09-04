# Batch 101 Plan：生成历史面板对齐 2026-09-05 源站

> 状态：`PLANNED`
>
> 建档日期：2026-09-05。
>
> 上一批 checkpoint：Batch 100（`batch/100-empty-canvas-state`）。
>
> 源站证据：[`../liblib-live-2026-09-05/README.md`](../liblib-live-2026-09-05/README.md) §6（生成历史模态截图与结构）。

## 1. 范围

### 包含（仅展示层与本地状态，不接任何历史数据服务）

1. **标题**（`SOURCE_FACT`）：`历史资产` → `生成历史`（aria-label 同步；`data-liblib-overlay="primary:history"` 与 `isHistoryPanelOpen` 不变）。
2. **缩略图尺寸控制**（`SOURCE_FACT`+`CLONE_DECISION`）：源站为两端网格图标 + 连续 slider；clone 由 +/− 步进改为 range slider（沿用本地 zoom state，范围 50–150）。
3. **筛选行**（`SOURCE_FACT`）：新增「本画布」选中 chip（带图标）；tab 改为 `图片/视频/音频` + 计数徽标（沿用 clone 本地 mock：图 3/视频 0/音频 0；源站空画布为 0/0/0，计数语义一致——当前画布分类计数）。
4. **所有评级下拉**（`SOURCE_FACT` 按钮 + `CLONE_DECISION` 菜单）：新增按钮；点击展开本地小菜单（`所有评级` 选中 / `已收藏`），`已收藏` 按既有 favorites 本地过滤，不发明真实评级语义。
5. **空态文案**（`SOURCE_FACT`）：`暂无历史记录`（替换视频/音频 tab 的旧文案）。
6. 保留：时间倒序、批量操作、缩略图 hover 操作、`没有更多了`、模态形态与 backdrop。

### 不包含

- 真实历史任务/生成记录、远端数据、评级后端；
- 「本画布」之外的画布/项目筛选范围（源站仅见本画布 chip）；
- 生成历史与普通画布 graph 的任何写入。

## 2. 证据边界

| 标签 | 内容 |
|---|---|
| `SOURCE_FACT` | 标题 `生成历史`、slider 尺寸控制、本画布 chip、图片/视频/音频+计数、所有评级/时间倒序/批量操作、`暂无历史记录` |
| `CLONE_DECISION` | slider 取值范围、评级菜单选项与 favorites 过滤、计数沿用本地 mock 数据 |
| `SOURCE_UNKNOWN` | 评级菜单真实选项、本画布 chip 的完整筛选行为、历史项非空态的源站样式 |

## 3. 影响面与兼容

- 仅 `src/components/HistoryPanel.tsx`；
- batch11/62 只断言 overlay 开关（复跑确认）；无内容级历史断言。

## 4. 验证

- 新增 `scripts/verify-liblib-batch101.py`：desktop `1440x900`，断言标题、slider 行为（拖动改变缩略图尺寸）、本画布 chip、三 tab 计数、所有评级菜单与已收藏过滤、时间倒序/批量操作按钮、空态文案、Escape/关闭、零诊断。
- 复跑 `verify-liblib-batch11.py`、`verify-liblib-batch62.py`。
- `npm run check`、`npm run docs:check`。

## 5. 完成定义

1. 面板头部/筛选行/右控件与源站 2026-09-05 快照一致（除标注项）。
2. 评级菜单为本地过滤，零 graph 副作用。
3. 相邻 verifier 与全量检查通过；特性分支 commit/push。
