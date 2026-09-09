# Batch 292 — 键盘快捷键全量对照（源站 2026-09-10 直采）

> 状态：`SAMPLING_RECORDED`（macOS ⌘ 系快捷键行为确证；无代码变更）。
>
> 证据：`shortcuts-log.json`（Ctrl 系探测，全 inert）、`meta-log.json`、
> `meta-final.json`（⌘ 系探测）。

## 源站事实（`SOURCE_FACT`）

| 快捷键 | 行为 | 证据 |
|---|---|---|
| **⌘A 全选** | 未生效（sel 1→1，未全选——与预期不符，仅选中节点保持） | meta-log |
| **⌘C / ⌘V 复制粘贴** | **生效**：粘贴 +1 节点（1→2） | meta-log |
| **⌘Z 撤销** | **生效**：撤销粘贴（2→1） | meta-log |
| Delete / Backspace 删除 | 生效（历批次复认） | 各批次清理路径 |
| Escape 关面板 | 生效（batch 289 弹层关闭） | batch 289 |

- Ctrl 系（Ctrl+A/C/V/Z）在 macOS 源站**全部 inert**——快捷键为 ⌘ 系；
- ⌘A 未全选为意外观察（sel 保持 1）——可能需 pane 焦点或功能缺失，
  记 `SOURCE_UNKNOWN`。

## Clone 对照

- clone 的 undo/redo（batch 33 合同）/删除/Escape/粘贴合同与 ⌘ 系
  行为一致 ✓；
- clone ⌘A 全选行为：合同存在与否待查（未在本批范围）。

## 验收

- docs check 通过；源站画布 **0 残留**；无代码变更。
