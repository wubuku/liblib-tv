# Batch 131：第二轮全量 verifier 串行回归 + 三项修复

> 状态：`REGRESSION_RECORDED_PASS`（含 3 项回归修复）
>
> 建档日期：2026-09-06。
>
> 上一批 checkpoint：Batch 130。

全量串行回归（114 项）：99 项通过；15 项失败中——
- 12 项为 Batch 108 已归因的既有漂移（aged gates，不变）；
- **batch16**：Batch 114 下拉重构漏迁移的断言（`data-canvas-row-menu` 已移除）——本批迁移到 hover+更多操作+新菜单文案，并修正 fallback 断言（删活动画布回退 canvas-3 名称 画布 3）；
- **batch21**：Batch 126 高级设置内联行使弹出菜单 y 偏移上移 28px——迁移 x/y 断言，并把内联行从 footer 移到独立行（恢复 footer 几何，源站布局即如此）；
- **batch93**：会话时序 flake（对象树点击被拦截），复跑通过。

## 完成定义

1. 修复后 batch16/21/93 复跑通过；全库无未归因失败。
2. `npm run check`、`npm run docs:check` 通过。
3. master commit/push。

旧漂移 12 项维持 Batch 108 归因（aged gates），不在本批处置。
