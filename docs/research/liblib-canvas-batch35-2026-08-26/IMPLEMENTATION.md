# Batch 35 Implementation Log

> 状态：计划保护点准备提交；产品代码尚未修改。

## Planned Protection Points

1. 计划、规格、selectors 与验收矩阵；
2. 依赖、director schema/store、入口和 R3F 工作区；
3. helper-free capture、React Flow return transaction 和 undo/redo；
4. Playwright、WebGL 像素检查、截图台账和跨批回归；
5. 实施收口、接力说明和下一批计划。

## Pre-Implementation Audit

- 当前 `ScriptExecutionNode` 是无行为脚本步骤卡，不符合已确认的导演台产品边界。
- `AssetManagerPanel` 将该节点标为“脚本生成器”，属于同一处错误脑补。
- 当前页面是 Client Component，符合 Next.js 16 在 client boundary 内使用
  `next/dynamic(..., { ssr: false })` 的要求。
- React Flow 和 R3F 可在同一路由共存；通过 full-screen island 隔离 pointer、
  renderer 和 state ownership。
- React 19.2.4 与计划安装的 R3F 9 / Drei 10 / Three 0.185 版本范围兼容。
- 现有 22 张历史截图二进制变化不是本批工作，所有提交必须排除。

## Implementation Result

Pending.

## Verification Result

Pending.

## Commit Protection

- Batch 35 plan protection: pending.
- Batch 35 implementation protection: pending.
- Batch 35 verification/finalization: pending.

## Interruption Handoff

如在计划保护点后中断，从 [`PLAN.md`](PLAN.md) 第 4 节开始。先安装依赖，再按
`directorStore -> canvas return transaction -> dynamic workspace -> browser
verification` 顺序推进；不要把历史截图变化带入提交。

