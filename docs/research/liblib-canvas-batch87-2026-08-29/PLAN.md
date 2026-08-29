# Batch 87 计划：Director undo/redo 后的 selection authority 一致性

> 状态：`COMPLETED` / `RECORDED_PASS`。
>
> 建档日期：2026-08-29。
>
> 本批是当前五批连续迭代中的第四批。目标是修复 Director 文档恢复与当前
> UI selection 混用造成的可发现性和上下文一致性问题。

## 1. 背景与证据

Batch 86 的 fresh-page 验证观察到：Director undo/redo 会重新投影恢复后的
对象和时间线，但 `restoreDirectorProjectState` 当前会默认选择首个角色或首个
对象。可持久化 `DirectorProjectDocumentV1` 明确不包含 selection、viewport
panel、playhead 和其他运行时 UI 状态，因此该默认策略不应被复用于 undo/redo。

受影响的 clone-owned surface：

- 对象树的 selected row 与 selection count；
- Inspector 当前对象/分组属性；
- Viewport 变换目标上下文与 TransformControls；
- Timeline 当前 track/path/keyframe；
- undo/redo 后的键盘命令和锁定目标反馈。

已有合同：

- `LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md`：Director history 只保存
  portable document before/after；
- Batch 69：`authoredObjects` 是 authoring baseline，`objects` 是 runtime
  projection；
- Batch 70/71：one-entry history、undo/redo、gesture cleanup；
- Batch 84–86：锁定目标、selection/CRUD、变换目标上下文；
- `directorProjectDocument.ts`：schema V1 不允许增加未声明的 UI selection 字段。

## 2. Clone-owned 决策

| 恢复场景 | selection 策略 |
|---|---|
| 首次打开/重开项目 | 使用现有确定性默认选择：首个角色，否则首个对象 |
| undo/redo 文档恢复 | 保留恢复前当前 selection；只保留恢复后仍存在且语义有效的对象/分组 |
| 当前对象被删除后 undo | 若当前选择已为空或失效，选择恢复文档中的首个存活角色，否则首个对象 |
| 分组失效 | 清除失效 group，按其仍存活成员降级为对象多选 |
| timeline track/path/keyframe 失效 | 保留仍存在的选择；失效项清空，不指向恢复文档中无关的首项 |
| scene/selection-only mutation | 不产生 Director document history；既有 selection 直接保留 |

该策略只描述 clone 的 UI authority，不宣称 LibTV 原站 Director 的 exact
undo selection policy。source-exact 结论仍为 `SOURCE_UNKNOWN`。

## 3. 实施范围

纳入：

- 提取可测试的 Director selection repair helper；
- 让文档恢复支持明确的 `default` / `preserve-and-repair` policy；
- 将 undo/redo 使用 preserve-and-repair，保持 import/open 的默认语义；
- 在恢复后重新校验 object/group/timeline selection 与 runtime projection；
- 增加 Batch 87 pure/source verifier 和 fresh-page Playwright verifier；
- 更新 current verifier manifest、verification ledger、Harness、research index
  和 component coverage；
- 记录运行时观察、证据边界和回归结果。

不纳入：

- 把 selection、viewport 或 playhead 写进 Director V1 文档；
- 改变普通 LibTV React Flow、FrameOS 或 Director history 的项目边界；
- 改变 delete planner 的 closure、locked target policy 或 gesture coalescing；
- 推断 LibTV 原站 Director exact DOM/CSS、快捷键或 selection policy；
- 新增截图；已有识图记录不能回答本批 clone-owned store contract 问题。

## 4. 验收标准

- undo/redo 变换后，当前对象仍同时出现在对象树、Inspector、Viewport context
  和 TransformControls 目标中；
- undo/redo 后 timeline 只保留仍存在的 track/path/keyframe，不跳到无关首项；
- 删除后 undo/redo 的失效 selection 被清理，且至少有确定性的合法回退；
- 无选择、多选、分组和锁定目标的 Batch 84–86 语义不回归；
- 项目打开/重开仍保持原有默认选择和 history continuity；
- Director document fingerprint 不因 selection-only 修复改变；
- pure verifier、fresh-page Playwright、current-gate、`npm run check`、
  `npm run docs:check`、`python3 scripts/verify-docs.py` 和 `git diff --check`
  全部通过，浏览器 diagnostics 为 `0 / 0 / 0`；
- 本批代码与文档在单独 checkpoint commit 中 push，工作区恢复干净。

## 5. 执行步骤

- [x] 阅读 Batch 70/84/85/86 与 Director document/history 实现；
- [x] 记录 selection 不属于 portable document 的事实和恢复策略；
- [x] 实施 selection repair helper 与恢复 policy；
- [x] 新增并运行 Batch 87 pure/source verifier；
- [x] 新增并运行 Batch 87 fresh-page Playwright verifier；
- [x] 运行 Batch 59、67–87 current-gate 回归；
- [x] 更新台账、manifest、Harness、索引和实施记录；
- [x] 运行全量检查并 commit/push。
