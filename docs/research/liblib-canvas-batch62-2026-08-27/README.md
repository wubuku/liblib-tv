# Batch 62：Selection Command Snapshot 与单层 Escape

> 状态：`SCRIPT_RECORDED_PASS`。
>
> 建档日期：2026-08-27。
>
> 对应 backlog：`LIBTV-PAR-004/007/008/011`。
>
> 对应 fixture / verifier：`LIBTV-FIX-LOCAL-SELECTION-FOCUS-CONTEXT-01` /
> `LIBTV-VR-019` 的第一段 focused runtime slice。

## 目标

在 Batch 61 已建立 node/edge active-session owner 的基础上，先关闭当前 clone
中证据最充分、风险最可控的 selection/keyboard context 缺口：

```text
current active canvas + validated node/edge selection
  -> immutable command snapshot
  -> editable / IME / Director / active-tool / foreground-surface precedence
  -> one Escape closes one surface
  -> no foreground surface: clear selection + return focus to canvas root
```

本批不重新设计任何视觉，也不声称 LibTV 源站使用相同状态模型。它只建立普通
LibTV clone 的可验证 correctness floor，并保留现有源站已确认的图片双浮层、
edge effect、Director 隔离和 React Flow selection 行为。

## 证据边界

- Batch 61 已证明 node/edge session selection 与 current-snapshot routing；
- Batch 50 已证明 Director active 时普通 page shortcuts 被隔离；
- Batch 52/53/54/60 已证明 active image surface 的 capture-phase keyboard
  隔离与 owner cleanup；
- 既有静态审计直接证明当前 page Escape 会同时 `selectNode(null)` 与
  `closeAllPanels()`，editable guard 漏掉 `select`、ARIA textbox/searchbox/
  combobox 和 IME；
- LibTV 源站 mixed primary、Character/History focus trap、菜单焦点归还和
  Escape exact compound behavior 仍是 `SOURCE_UNKNOWN`。

## 接力入口

- [`PLAN.md`](PLAN.md)：实施切片、决策、fixture、回归与停止边界；
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：代码变更、验证结果、证据成本与未完成边界；
- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：截图复用与新识别闸门；
- [`../LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](../LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md)：
  长期 selection/focus/context authority；
- [`../LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](../LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md)：
  Batch 61 selection transport 前置。
