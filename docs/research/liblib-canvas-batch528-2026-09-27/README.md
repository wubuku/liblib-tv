# Batch 528 — 脚本生成器入口跟随接线

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。第五/八轮源站采样
> （liblib-source-exploration-2026-09-25 NOTES §11 + round-8）观察到：
> 单击「剧本生成分镜脚本」等尝试入口仅选中/跟随节点（顶部出现
> 「正在跟随/取消ESC」横幅），未展开任何子流程。本批把 batch 105 的
> FollowBanner（此前仅暴露状态、无触发方）与 batch 116 的
> ScriptGeneratorNode 尝试入口接通。

## 行为合同

- 单击尝试入口 → 入口 `aria-pressed=true` + 顶部跟随横幅可见
  （`aria-hidden=false`，文案「正在跟随」），无任何前景面板打开
  （与源站「仅选中/跟随，未展开子流程」一致）；
- 横幅「取消」→ 跟随结束，入口高亮同步清除（高亮 = 跟随态的派生值，
  `activeAttempt = isFollowingSession ? attempt : null`，避免 effect 级联
  setState）；
- 再次单击入口后按 `Escape` → 同样结束跟随（page.tsx keydown 的 Escape
  分支优先于清空选区处理跟随态）；
- 提示词本地草稿不受跟随往返影响；不触发任何生成（GVLM 仅为卡面徽标）。

## 内容

- `scripts/verify-liblib-batch528.py`（4 场景 14 检查）；
- `src/components/nodes/ScriptGeneratorNode.tsx`：入口点击
  `setFollowingSession`，高亮派生自跟随态；
- `src/app/page.tsx`：keydown Escape 分支先退出跟随态；
- 回归：batch 116 verifier 15/15 仍绿（入口点击新增的横幅副作用不破坏
  其 aria-pressed 合同）；`npm run check` 0 error。
- `runtime-audit.json`：本目录。
