# Batch 329（2026-10-01）：分组进入撤销历史（undo/redo 丢分组状态）

## 结论一句话

撤销历史快照只存 `{nodes, edges}`，而 `groups` 会被 `createGroup` / `ungroup` /
`removeNode`(Batch 328) 改动 —— 撤销只还原节点，**分组状态留在「动作之后」**。
最严重的一条：撤销「删除分组成员」时，**节点回来了但成员集没回来**，被恢复的节点
被静默踢出分组，且**不产生任何悬空引用、不报错**。已把 groups 纳入快照并让
成组/解组入栈。

## 这是 Batch 328 之后才暴露的缺陷

Batch 328 让 `removeNode` 开始改写 `groups`（`reconcileGroups`）。而历史快照不含
`groups` —— 于是**同一个动作**（删除成员）在「正向」被完整记录、在「撤销」只回滚了
一半。328 修好了一半，正好暴露出另一半。这也说明：数据结构变更后必须回头检查
**所有**依赖该数据的路径，而不是只看写入端。

## 运行时证据（修复前）

```
A_createGroup      : pastDepth 0 → 0   pushedToHistory: false   ← 成组不入栈
A_afterUndo        : groups 1                                ← 撤销无效
B_deleteMemberUndo : memberIdsAfterDelete [text-2]
                     nodeRestored 7
                     memberIdsAfterUndo   [text-2]            ← 节点回来了，成员集没回来
C_ungroup          : pushedToHistory: false                  ← 解组不入栈
```

B 最隐蔽：撤销后 `memberIds` 仍是 `[text-2]`，而 `text-1` 已经回到画布上。
它既不是悬空引用（节点确实存在），也不违反任何断言 —— 只是**悄悄不在组里了**。
用户表现为「撤销删除后，节点飘在组外面」。

## 修复

1. **快照类型纳入 `groups?`**（可选字段，旧快照按空数组处理，向后兼容）；
2. **新增 `pushHistorySnapshot(state)` 统一入口**，13 处入栈路径全部改用它。
   根因是这 13 处各自手写 `{nodes, edges}`，漏带 groups 只是迟早的事；
   集中到单一入口后，新增 action 不可能再漏；
3. **`createGroup` / `ungroup` 首次入历史栈**；
4. **undo/redo 还原 groups**，并过 `reconcileGroups` 兜底收敛
   （旧快照无 groups 时按「分组为空」处理，不会留下悬空成员）。

## 修复后（同一探针）

```
A_createGroup      : pastDepth 0 → 1   pushedToHistory: true
A_afterUndo        : groups 0                                 ← 撤销生效
B_deleteMemberUndo : memberIdsAfterUndo [text-1, text-2]      ← 成员集完整恢复
                     boxAfterUndo {33,5,737,319}              ← 分组盒还原
C_ungroup          : pushedToHistory: true, 撤销后 groups 1   ← 解组可撤销
```

## 验证器

`scripts/verify-frameos-batch329.py` — **23 项断言全 PASS，0 诊断**：

1. `createGroup` 入栈 + 撤销删除分组 + redo 恢复（成员与分组盒逐字比对）；
2. `ungroup` 入栈 + 撤销恢复分组；
3. **删除成员后撤销：节点恢复、成员集完整、分组盒还原、无悬空**（核心断言）；
4. redo 重放删除后的收敛状态；
5. 连撤 6 步不产生悬空成员；
6. **旧格式快照（无 groups 字段）不崩溃、不产生悬空**；
7. 控制台/页面错误为 0。

第 6 项特意伪造一条 Batch 329 之前的历史项（`{nodes, edges}` 无 groups），
确认 `reconcileGroups(prev.groups ?? [], prev.nodes)` 的兜底路径成立。

证据：`runtime-audit.json`（本目录）。
复现探针：`scripts/probe-frameos-batch329-group-undo.py`（只读，可重复运行）。

## 回归

- batch251（分组 59 项）PASS —— 该脚本此前**不**断言历史栈深度，故无冲突；
  本批扩大了入栈面（成组/解组现在会产生历史项），已复跑确认。
- 全量 `run-frameos-verifiers.sh` 见 checkpoint 记录。

## 顺延 / 候选

- 源站采样队列仍阻塞（见 `SOURCE_ACCESS_BLOCKED_2026-10-01.md`）。
- Batch 330 候选：`arrangeGroup` / `moveGroup` / `setGroupColor` / `renameGroup`
  仍不入历史栈 —— 成组解组已可撤销，但组内排列、拖拽、改色、改名撤销不了。
  需先确认源站是否把这些算作可撤销动作（**不可凭空发明**），或按纯克隆一致性
  补齐并明确标注为 clone-only 决策。
