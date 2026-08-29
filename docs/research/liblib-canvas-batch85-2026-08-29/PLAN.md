# Batch 85 计划：Director 对象树选择与 CRUD 可发现性

> 状态：`COMPLETED` / `RECORDED_PASS`。
>
> 建档日期：2026-08-29。
>
> 本批是连续五个 batch 中的第二个。目标是把已有的选择、多选、复制、删除、
> 打组和解组能力组织成一个可发现的对象树操作面板。

## 1. 背景与证据

当前 `DirectorObjectTree` 已有以下 clone 行为：

- 点击对象行进行单选；
- Shift 点击角色行切换 `selectedObjectIds`；
- 选择分组后选中全部成员；
- 顶部提供 `打组` / `解组`；
- 行内提供 visibility、lock 和 delete；
- DirectorDesk 键盘处理 `Cmd/Ctrl+C`、`Cmd/Ctrl+V`、Delete/Backspace。

缺口是这些动作没有共同的选择上下文：多选数量不可见，复制和删除只能靠键盘，
清除选择没有显式入口，用户需要猜测哪些命令针对当前选择。

已有 source/upstream 证据只支持对象树、group/multi-selection 的局部启发；
LibTV Director 的 source-exact 选择工具条和快捷键视觉仍是 `SOURCE_UNKNOWN`。

## 2. Clone-owned 合同

| 场景 | 规则 |
|---|---|
| 单选 | 选择一个对象时显示选择上下文和复制、删除、清除入口 |
| 多选 | Shift 角色选择产生多个对象时显示数量和批量动作入口 |
| 分组选择 | 选择分组时显示分组上下文；复制使用现有 group closure，删除使用既有解组策略 |
| 清除 | 清除选择不改 document/history，只清理选择和临时路径选择 |
| 复制 | 复用 `copyDirectorSelection`，结果继续由 Director typed feedback 投影 |
| 删除 | 单选/多选对象复用 `deleteDirectorEntity`，保持 reference-aware closure 和一条 history |
| 打组 | 继续只允许至少两个未分组角色，复用现有 `groupSelectedCharacters` |
| 解组 | 继续复用现有 `ungroupSelectedCharacters`，保留成员对象 |
| 锁定对象 | 选择、复制、删除和清除仍可用；属性/变换保护继续由 Batch 84 负责 |

## 3. 实施范围

纳入：

- 在对象树中增加稳定的 selection action bar；
- 显示当前选中对象/分组数量；
- 增加复制、删除、清除选择的 icon buttons、ARIA、tooltip；
- 让批量删除与现有 reference-aware delete command 一致；
- 为 selection bar 增加 pure/source 和 fresh-page verifier；
- 更新 current manifest、verification ledger、HARNESS、研究索引和组件覆盖矩阵。

不纳入：

- 改变 Director selection store 数据结构；
- 让 props/cameras 参与角色打组；
- 猜测 LibTV 原站 Director 的 exact DOM/CSS 或快捷键文案；
- 引入系统剪贴板、远端持久化或新的拖拽选择框；
- 改变普通 LibTV 画布、FrameOS 或 Batch 84 锁定语义。

## 4. 验收标准

- 有任意 Director selection 时，selection action bar 可发现；
- bar 能准确显示单选、多选和分组选择；
- 复制、删除、清除入口拥有稳定 selectors 和 ARIA；
- 清除选择不产生 history；
- 删除多对象保持现有 closure、选择修复和一条 history；
- 复制入口继续保持 project-scoped clipboard 语义；
- desktop/mobile 不溢出，浏览器 diagnostics 为零；
- 专项 verifier、`npm run check`、`npm run docs:check` 和文档检查通过；
- 本批结论区分 `CLONE_FACT`、`CLONE_DECISION` 与 `SOURCE_UNKNOWN`。

## 5. 实施与验证结果

本批已完成实施并通过：

```text
node --experimental-strip-types scripts/verify-liblib-batch85.mjs
LIBLIB_BASE_URL=http://localhost:4317 python3 scripts/verify-liblib-batch85.py
npm run lint -- --quiet
npm run typecheck
git diff --check
```

浏览器验证使用固定 `localhost:4317`，未产生截图，console/page/request
diagnostics 均为 0。结果见 [`IMPLEMENTATION.md`](IMPLEMENTATION.md) 和
[`runtime-audit.json`](runtime-audit.json)。

## 6. 预定文件

- `src/components/director/DirectorObjectTree.tsx`
- `scripts/verify-liblib-batch85.mjs`
- `scripts/verify-liblib-batch85.py`
- `docs/research/liblib-canvas-batch85-2026-08-29/*`
- current manifest、coverage、verification ledger、HARNESS 和研究索引，均已更新
