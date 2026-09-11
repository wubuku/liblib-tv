# Batch 339 — AGED_GATE 家族处置定案：维持历史归档，不现代化（`LEDGER_RECORDED`）

> 状态：对残余 13 个失败验证器完成逐项再确认与处置定案，台账写入
> [`LIBTV_VERIFIER_REPLACEMENT_MAP.md`](../LIBTV_VERIFIER_REPLACEMENT_MAP.md)
> §5.z3。无产品代码变更。

## 调查摘要

- **源站恢复探测**：模型菜单仍失效，BLOCKED_SOURCE 维持；
- **batch 89 深查**（唯一本轮深挖项）：移动端关闭按钮在打开后可见
  （390×584、display block、无 inert/aria-hidden），但点击前被新式
  移动面板生命周期（焦点收纳/自动关闭，后期批次行为）卸载——
  batch 89 时代「点击覆盖层关闭」合同已被取代。桌面段合同不受影响。
  **处置：AGED_GATE 维持**，替代物为移动面板生命周期所属的现行批次；
- 其余 12 项（6/29/39/40/41/44/46/48/49/57/61/64）维持 batch 335
  归因：29 已由 Batch 338 修复转绿；6/40/41/44/46/48/49 为
  AGED_GATE；57/61/64 为 ownership-managed slice。

## 决策

**不对 13 项做现代化改写**：其替代物（Batch 59/67-96 current gates
与 ownership slices）均已存在且全绿；重写死合同无复刻价值。台账
§5.z3 固化该处置与证据链（sweep 逐项结果 + 89 插桩记录）。

## 验收

- docs check 通过；无产品代码变更（维护集 45 项态势不变，全绿）；
- 源站画布 0 残留。

## 后续候选

- 源站恢复后 BLOCKED_SOURCE 补采（三项）并替换故事板
  CLONE_DECISION；
- 图片栏 对话/展开 行为采样（待源站恢复）；
- 新表面随源站更新巡检。
