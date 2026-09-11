# Batch 351 — batch 64 专项现代化完成（`VERIFIER_FIXED`）

> 状态：六子流程整体验证器按 320px 面板架构重推完成，
> **三连跑确定性全绿**；台账 §5.z3 更新（64 → 已修复转绿）。
> 无产品代码变更（全部为验证器合同迁移）。源站恢复探测：
> `RECOVERY: still-broken`。

## 现代化内容（batch 350 分诊的四类之④架构级联）

1. **面板宽度迁移 ×3**：240 → 320（batch 298 面板 flex 架构现行）——
   桌面 toolbar toggle viewport 偏移 -120 → -160；mobile viewport
   偏移 -120 → -160；mobile host 宽 150 → 70（390 − 320）；
2. **stale-canvas-guard 竞态确定性化**：布局计划在两帧 rAF 后提交，
   旧写法「dispatch 开面板 → 另一次 evaluate 切画布」依赖竞态
   （320px 面板下 rAF 常先提交 → committed 优先于 skipped）——
   合并进同一 evaluate 使 canvas-changed skip 路径确定性触发；
3. **纯函数段（run_pure_helper）不动**：其 -120 期望对应合成输入
   （240+689 矩形），输入驱动的合同仍然正确；
4. acceptance 元数据 `expectedDrawerViewportDeltaX` 同步 -160。

## AGED_GATE 清算进度（batch 335 sweep 13 项 → 已清算 6 项）

29（338）、39（346）、40（347）、41（348）、46（349）、**64（351）**
已转绿；剩余 7 项维持归档：6（marquee 历史化）、44/48/49（同点同形
的 Director 旧合同）、57/61（ownership slices）、89（移动面板生命
周期取代）。

## 验收

- batch 64 三连跑全绿（exit=0 ×3）；
- 回归：19（资产面板共享）/202/334/336/337/341 全绿；
- `npm run check` 0 errors / 0 warnings；docs check 通过
  （910 Markdown）。

## 后续候选

- 源站恢复后 BLOCKED_SOURCE 补采与 CLONE_DECISION 替换；
- 剩余 7 项归档失败按需深查（低优先）。
