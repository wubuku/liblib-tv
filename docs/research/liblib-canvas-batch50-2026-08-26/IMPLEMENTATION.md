# Batch 50 实施记录

> 状态：已完成（2026-08-26）。本批收口为 clone-owned 的 Director
> workspace shell 有界成熟原型，不声明 LibTV source-exact。

## 保护上下文

- [`PLAN.md`](PLAN.md)：选择理由、范围、状态副作用和验收门；
- [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)：LibTV unknown、clone fact、
  upstream fact 分层；
- [`UPSTREAM_ARCHAEOLOGY.md`](UPSTREAM_ARCHAEOLOGY.md)：固定上游 shell/
  keyboard 结构；
- [`DIRECTOR_WORKSPACE_SHELL.spec.md`](DIRECTOR_WORKSPACE_SHELL.spec.md)：
  clone 行为契约；
- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：四态截图的单次视觉识别记录；
- [`MATURITY_ASSESSMENT.md`](MATURITY_ASSESSMENT.md)：成熟度和残余风险；
- 上一批 [`../liblib-canvas-batch49-2026-08-26/IMPLEMENTATION.md`](../liblib-canvas-batch49-2026-08-26/IMPLEMENTATION.md)：
  视口 gizmo 已收口，改动必须保持其 capture/path/phone guard。

## 进度

- [x] Batch 50 计划与证据边界
- [x] upstream shell/keyboard 代码考古
- [x] `viewportPanelsCollapsed` session-local state
- [x] Director toolbar 全屏/恢复侧栏 command
- [x] desktop shell geometry 与 mobile drawer recovery
- [x] workspace focus owner 与 page shortcut isolation
- [x] focused Playwright、截图台账和一次视觉识别
- [x] 跨批回归与 repository gates
- [ ] commit/push

## 实施决定

- 不使用 Browser Fullscreen API；
- 不把 UI collapse 写入普通 graph/history；
- 不为 source 未证实的 Director shortcut 创造新命令；
- 不修改 `docs/design-references/` 历史证据，新增截图只属于 Batch 50；
- 若 source evidence 仍不足，成熟度结论只写 clone-owned bounded contract。

## 实施内容

### Workspace shell

- `directorStore` 新增 typed `viewportPanelsCollapsed` 状态与 toggle/set action；
- Director viewport toolbar 提供 `全屏` / `恢复侧栏` icon-only command；
- desktop collapsed 状态隐藏左对象树和右 Inspector，并让 R3F viewport
  从 `x=220,width=932` 扩展为 `x=0,width=1440`；
- mobile 保留 tree/Inspector 互斥 drawer；从 collapsed 状态打开 drawer
  会先恢复侧栏可用状态；
- hidden rails 标记 `aria-hidden="true"`，workspace root 作为可查询的
  dialog/focus owner。

### Keyboard ownership

- page-level LibTV keyboard handler 在 Director active 时跳过普通画布快捷键；
- Director 内部 surface 继续按自身优先级处理 Escape；
- editable Inspector input 的 Delete/Backspace/Space/Tab 不会触发普通画布
  的删除、临时 pan 或 Add Node；
- collapse/restore 不修改 objects、selection、timeline、active camera、
  captures 或普通 graph/history。

## Focused Verification

已运行：

```bash
python3 scripts/verify-liblib-batch50.py
```

结果：

```text
Batch 50 director workspace shell verification passed.
```

专项脚本覆盖：

- desktop expanded/collapsed/restored 的 aside display、ARIA 和 viewport bounds；
- mobile tree/Inspector 互斥、Escape close、collapsed recovery 和无水平溢出；
- workspace `role="dialog"`、`aria-modal`、label 和 activeElement focus owner；
- collapse 前后 objects、selection、timeline、active camera、captures 不变；
- Director active 时 Tab/Space/Delete/Ctrl+Z 不穿透普通 LibTV page handler；
- Inspector editable target 的 Delete/Space/Tab 不触发普通画布行为；
- export panel -> workspace 的 Escape 分层关闭；
- main WebGL 非空、console/page/request 错误为零；
- desktop expanded/collapsed、mobile tree/collapsed 四态截图和 contact sheet。

一次性视觉识别的详细结果见 [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)；
后续 agent 不应重复识别同一批截图。

## Repository Gates

最终结果：

```text
Batch 50 focused Playwright: passed
Batch 35-50 serial regression: passed
npm run docs:check: passed (423 Markdown files, 1687 local targets)
npm run check: passed
  - lint: passed, 9 pre-existing warnings, 0 errors
  - typecheck: passed
  - build: passed
git diff --check: passed
```

`npm run build` 仍报告仓库上级存在多个 lockfile 的 Next.js workspace-root
warning；它没有影响编译、TypeScript 或静态页面生成结果。

## 接力

实施中断时先读本文件和 [`PLAN.md`](PLAN.md)，再查看当前
`DirectorDesk.tsx`、`DirectorViewport.tsx`、`directorStore.ts` 和
`src/app/page.tsx` 的对应 selector；不要重复识别 Batch 49 或 Batch 50
截图。最终成熟度边界见 [`MATURITY_ASSESSMENT.md`](MATURITY_ASSESSMENT.md)。
