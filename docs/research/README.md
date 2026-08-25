# Research Index

> 原站事实、组件规格、截图台账、原始 JSON、批次计划和实施历史的统一入口。

## How To Read

1. Start with the route-specific overview.
2. Search for an existing `SCREENSHOT_ANALYSIS.md` before opening a screenshot.
3. Read a component spec before modifying its source.
4. Treat raw JSON as evidence, not as a current runtime contract by itself.
5. Keep source fact, inference and clone decision separate.

## Route Research

### LibTV

- [`liblib-live-2026-08-25/`](liblib-live-2026-08-25/README.md)：登录态原站总体审计、节点/边/面板 JSON 和差距排序。
- [`liblib-seedance-2.5-2026-08-25/`](liblib-seedance-2.5-2026-08-25/README.md)：Seedance 2.5 能力背景、原站复核、证据图和实现历史。
- [`components/`](components/)：LibTV 组件规格，包括节点、面板、工具条和对话框。

### FrameOS

- [`frameos/`](frameos/README.md)：FrameOS 原站抽取、视觉 token、行为、组件清单、运行手册和原始 JSON。
- [`frameos/IMPLEMENTATION.md`](frameos/IMPLEMENTATION.md)：设计决策与已知 prototype 边界。
- [`frameos/RUNBOOK.md`](frameos/RUNBOOK.md)：调试、扩展和浏览器诊断路径。

## Batch History

| Batch | Focus | Entry |
|---|---|---|
| 3 | command history, context menu, keyboard shortcuts | [`liblib-canvas-batch3-2026-08-25/`](liblib-canvas-batch3-2026-08-25/) |
| 4 | grouping and multi-selection | [`liblib-canvas-batch4-2026-08-25/`](liblib-canvas-batch4-2026-08-25/) |
| 5 | movement transactions and selection copy | [`liblib-canvas-batch5-2026-08-25/`](liblib-canvas-batch5-2026-08-25/) |
| 6 | marquee selection and navigation gestures | [`liblib-canvas-batch6-2026-08-25/`](liblib-canvas-batch6-2026-08-25/) |
| 7 | source-like organize topology and confirmation | [`liblib-canvas-batch7-2026-08-25/`](liblib-canvas-batch7-2026-08-25/) |
| 8 | video group parent-child hierarchy | [`liblib-canvas-batch8-2026-08-25/`](liblib-canvas-batch8-2026-08-25/) |
| 9 | selected-node floating UI anchor geometry | [`liblib-canvas-batch9-2026-08-25/`](liblib-canvas-batch9-2026-08-25/) |
| 10 | image editor five-state matrix | [`liblib-canvas-batch10-2026-08-25/`](liblib-canvas-batch10-2026-08-25/) |
| 11 | top-level overlay exclusivity and lifecycle | [`liblib-canvas-batch11-2026-08-25/`](liblib-canvas-batch11-2026-08-25/) |
| 12 | asset manager canvas/assets tabs and local media selection | [`liblib-canvas-batch12-2026-08-25/`](liblib-canvas-batch12-2026-08-25/) |
| 13 | storyboard mode data binding and key-elements/storyboard layout | [`liblib-canvas-batch13-2026-08-25/`](liblib-canvas-batch13-2026-08-25/) |
| 14 | Agent drawer and share panel source-shaped structure and local feedback | [`liblib-canvas-batch14-2026-08-25/`](liblib-canvas-batch14-2026-08-25/) |
| 15 | add-node source-shaped entries, audio renderer and material submenu | [`liblib-canvas-batch15-2026-08-25/`](liblib-canvas-batch15-2026-08-25/) |
| 16 | project metadata and multi-canvas navigation lifecycle | [`liblib-canvas-batch16-2026-08-25/`](liblib-canvas-batch16-2026-08-25/) |
| 17 | asset drawer project/canvas context, hierarchy and local browse controls | [`liblib-canvas-batch17-2026-08-25/`](liblib-canvas-batch17-2026-08-25/) |
| 18 | source-shaped zoom menu commands and unified overlay lifecycle | [`liblib-canvas-batch18-2026-08-25/`](liblib-canvas-batch18-2026-08-25/) |

Each batch directory normally contains `README.md`, `PLAN.md` and `IMPLEMENTATION.md`; additional `*.spec.md`, JSON and screenshot analysis files are the detailed contract.

## Stable Cross-Cutting Research

- [`BEHAVIORS.md`](BEHAVIORS.md)：whole-app interaction map.
- [`PAGE_TOPOLOGY.md`](PAGE_TOPOLOGY.md)：page layout and z-index map.
- [`DESIGN_TOKENS.md`](DESIGN_TOKENS.md)：visual tokens.
- [`COMPONENT_INVENTORY.md`](COMPONENT_INVENTORY.md)：current component catalog.
- [`INSPECTION_GUIDE.md`](INSPECTION_GUIDE.md)：live-site extraction workflow and screenshot ledger rule.

## Evidence Assets

- Raw structured audits live beside the relevant research directory.
- Original and clone screenshots live in [`../design-references/`](../design-references/).
- Screenshot interpretation is recorded in the nearest batch `SCREENSHOT_ANALYSIS.md`.
- A screenshot filename containing `final` is not proof that it still matches the current source.
