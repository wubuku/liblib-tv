# Batch 99：快捷键帮助面板对齐 2026-09-05 源站

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-09-05。
>
> 上一批 checkpoint：Batch 98（`batch/98-add-node-panel-source`）。

本批把快捷键帮助面板四栏文案对齐 2026-09-05 源站审计，并同步刷新
`LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md` 的源站快照列。**不新增任何运行时
快捷键 handler**——`⌘G/⌘L/⌘Enter/⌘F` 等运行时行为仍按 crosswalk 现状，
属后续独立批次。

## 导航

- [PLAN.md](PLAN.md)：范围、证据边界与不包含项。
- [runtime-audit.json](runtime-audit.json)：结构化运行时证据。

## 证据边界

| 标签 | 本批含义 |
|---|---|
| `SOURCE_FACT` | 创作栏 9 项与顺序、文本键帽、⌘ 图标键帽、suffix 文案、删除位于其他栏、画布节点搜索 `⌘F` |
| `CLONE_DECISION` | 删除的 `Delete` keycap、移除 `重做（Windows）` 行 |
| `SOURCE_UNKNOWN` | 删除源站 keycap、其他栏更深条目、Windows 变体、弹窗精确几何 |

## 实施结果

- 创作栏：成组 `⌘G`、合并分镜组 `⌘⌥G`、解组 `⌘⇧G`、连线 `⌘L`、复制节点和连线
  `⌘D`、生成 `⌘Enter`、新建节点 `Tab`、节点复制 `Option+拖动节点`、创建副本
  `⌘Option+拖动`；移除 clone 自行放入的 `删除`。
- 其他栏：撤销 `⌘Z`、重做 `⌘⇧Z`、画布节点搜索 `⌘F`、删除 `Delete`；移除
  `重做（Windows）`。
- crosswalk 受影响行的源站快照/clone 帮助列已按 2026-09-05 复核刷新，
  「clone 实际处理/结论」列不变（运行时未改）；新增 `画布节点搜索`
  `SOURCE_ONLY` 行并记录 Windows 重做的移除。

## 完成定义

1. `verify-liblib-batch99.py` 30 checks、`0/0/0` diagnostics 通过。
2. 相邻 `verify-liblib-batch11.py`、`verify-liblib-batch62.py` 通过。
3. `npm run check`、`npm run docs:check` 通过。
4. 特性分支 commit/push。

通过结果只证明 clone-owned 帮助面板展示合同；帮助文案与运行时 chord 的
差异（如 `⌘G` vs 现行 `G` handler）已由 crosswalk 显式记录，不在本批闭合。
