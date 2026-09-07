# Batch 182 — batch75 超时根因闭环（零代码改动复活）

## 结论

batch75 的 `wait_for_function` 30s 超时是 **Batch 181 已修复的持久化回归
的下游症状**——本批通过可证伪实验确立因果，零代码改动即复活 batch75。
老化名单进一步降至 **10**。

## 根因链

1. Batch 96 收紧 director 文档校验（shot→camera/capture 引用存在性）。
2. `documentForPersistence` 剥离非持久 capture 时未剪枝
   `shots[].captureIds` → 保存的文档在 load 重校验时 REJECTED
   （Batch 181 定性为真回归并修复）。
3. batch75 的 reload-boundary 场景等待 `documentRestored`，恢复链路被
   上述 REJECTED 卡死 → 等待 30s 超时。

## 可证伪实验

- `git show fce8467^:src/lib/directorProjectPersistence.ts` 还原修复 →
  batch75 精确复现 `TimeoutError: Page.wait_for_function: Timeout
  30000ms exceeded`；
- 恢复修复（`git checkout fce8467 --`）+ typecheck 通过 → batch75 全绿
  （pure 12 场景 + browser clipboard/persistence/reload 全过，
  `documentRestored: true`）。

## 验收

- batch75 PASS；batch72 / batch74 复跑 PASS（确认 Batch 181 修复稳定）。
- Director 89-96 与画布 21-180 全量回归绿。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。
- 无源站采样（纯 clone 验证器诊断），源站画布保持 0 残留。
- 老化名单动态：12 → batch49 自愈（181）→ batch75 复活（本批）→
  **剩余 10**：batch6/9/40/41/44/46/48/51（历史合同）。
