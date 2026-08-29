# Batch 85：Director 对象树选择与 CRUD 可发现性

> 状态：`COMPLETED` / `RECORDED_PASS`。
>
> 建档日期：2026-08-29。

本批把既有的 Director 单选、Shift 多选、分组选择、复制和删除命令集中到
对象树 selection action bar，降低操作发现成本。

## 入口

- [PLAN.md](PLAN.md)：范围、合同和验收标准。
- [IMPLEMENTATION.md](IMPLEMENTATION.md)：实施、验证和证据边界。
- [runtime-audit.json](runtime-audit.json)：fresh-page Playwright 结构化结果。
- [`DirectorObjectTree.tsx`](../../../src/components/director/DirectorObjectTree.tsx)：对象树和选择操作面板。

## 证据边界

- `CLONE_FACT`：当前 clone 已有 selection/group/copy/delete store actions。
- `CLONE_DECISION`：使用 selection action bar 作为 clone-owned 的统一发现入口。
- `SOURCE_UNKNOWN`：LibTV 原站 Director 是否有相同 selection bar、文案、快捷键和布局。
