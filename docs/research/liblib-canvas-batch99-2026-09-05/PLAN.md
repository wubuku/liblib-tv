# Batch 99 Plan：快捷键帮助面板对齐 2026-09-05 源站

> 状态：`PLANNED`
>
> 建档日期：2026-09-05。
>
> 上一批 checkpoint：Batch 98（`batch/98-add-node-panel-source`）。
>
> 源站证据：[`../liblib-live-2026-09-05/README.md`](../liblib-live-2026-09-05/README.md) §9（快捷键弹窗四栏全量 DOM + 截图；⌘ 为图标键帽，ARIA 无文本，截图确认存在）。

## 1. 范围

### 包含（仅帮助面板展示文案 + crosswalk 快照列，不改任何运行时监听）

1. **创作栏**（`SOURCE_FACT`，9 项）：成组 `⌘G`、合并分镜组 `⌘⌥G`、解组 `⌘⇧G`、连线 `⌘L`、复制节点和连线 `⌘D`、生成 `⌘Enter`、新建节点 `Tab`、节点复制 `Option + 拖动节点`、创建副本 `⌘Option + 拖动`。移除 clone 自行放入创作栏的 `删除`。
2. **其他栏**（`SOURCE_FACT` + 1 项 `CLONE_DECISION`）：撤销 `⌘Z`、重做 `⌘⇧Z`、画布节点搜索 `⌘F`、删除（位于其他栏；keycap 在源站被 Agent 抽屉遮挡，clone 取 `Delete`，`CLONE_DECISION`）。移除 `重做（Windows）ctrl Y`（源站该栏可观察序列为 撤销→重做→画布节点搜索→删除，无 Windows 行位置；如后续采样到再恢复）。
3. **缩放/移动画布栏**：不动（clone 已与源站一致）。
4. **crosswalk 文档**：刷新 `LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md` 受影响行的「源站快照/clone 帮助」列，并标注 2026-09-05 复核；「clone 实际处理/结论」列不变（运行时未改）。

### 不包含

- 任何新快捷键的运行时 handler（`⌘G`、`⌘L`、`⌘Enter`、`⌘F` 等运行时仍按 crosswalk 现状，属后续独立批次）；
- 弹窗几何调整（源站约 `1014x388` 为截图粗读值，clone 保持 `905x447`，待精确采样）；
- 空画布状态与快捷芯片（Batch 100 候选）。

## 2. 证据边界

| 标签 | 内容 |
|---|---|
| `SOURCE_FACT` | 四栏条目集合与顺序、文本键帽（⇧/⌥/G/L/D/Enter/Tab/F/V/H/Space/0/+/−）、⌘ 图标键帽、节点复制/创建副本的 suffix 文案、删除位于其他栏 |
| `CLONE_DECISION` | 删除的 `Delete` keycap 取值、移除 `重做（Windows）`、⌘ 渲染沿用 Command 图标 |
| `SOURCE_UNKNOWN` | 删除源站 keycap、其他栏删除以下是否有更多条目、Windows 变体是否存在、弹窗精确几何 |

## 3. 影响面与兼容

- `src/components/KeyboardShortcutsDialog.tsx` 仅 `sections` 数据；
- batch11/62 只断言弹窗 overlay 开关，不受影响（复跑确认）；
- `LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md` 行内快照列更新，不改变结论列。

## 4. 验证

- 新增 `scripts/verify-liblib-batch99.py`：desktop `1440x900`，断言四栏条目集合、关键键帽文本与每行 kbd 数量、删除位于其他栏、关闭行为、零诊断。
- 复跑 `verify-liblib-batch11.py`、`verify-liblib-batch62.py`。
- `npm run check`、`npm run docs:check`。

## 5. 完成定义

1. 面板四栏与源站 2026-09-05 快照一致（除标注 `CLONE_DECISION` 项）。
2. crosswalk 快照列与面板一致，结论列不变。
3. 相邻 verifier 与全量检查通过；特性分支 commit/push。
