# Batch 27 Implementation Log

> 状态：计划完成，核心实现待开始。

## 1. Planned Files

- `src/components/SubtitleErasePanel.tsx`
- `src/components/VideoProcessingToolbar.tsx`
- `src/components/nodes/VideoNode.tsx`
- `src/store/canvasStore.ts`
- `scripts/verify-liblib-batch27.py`

## 2. Planned Protection Points

1. source evidence、plan 和 specs；
2. core UI/store implementation；
3. focused Playwright + screenshot ledger；
4. cross-batch regression + final handoff。

## 3. Verification Pending

- focused Batch 27 Playwright
- Batch 9、21、23、25、26、27 regression
- `npm run check`
- `npm run docs:check`
- `git diff --check`

完成后必须把实际结果、修复过程、截图结论和 commit IDs 写回本文件。
