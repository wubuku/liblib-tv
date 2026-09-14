# Batch 510 — VR-018 §13：LIBTV-FIX-LOCAL-COMMAND-FEEDBACK-01 runtime

> 状态：`PURE_RUNTIME_RECORDED_PASS`（commit 本批）。确定性纯模块
> fixture（`src/lib/libtvCommandFeedbackFixture.ts`）：fake clock、
> announcement 队列（owner/dedupe/stale/burst/上限）、A/B 画布与
> attempt 台账、graph/history/selection/viewport 快照、feedback ledger、
> reset 与 §13.3 不变量断言；§13.2 全 15 场景绿。视觉几何（scene 14）
> 按 message-bound 数据策略覆盖，像素几何仍由 browser 验证器承载；
> route isolation（scene 15）由验证器静态检查（模块代码无 FrameOS
> 引用）+ owner 级断言共同承载。

## 内容

- `src/lib/libtvCommandFeedbackFixture.ts`：fixture 世界 + 场景 runner；
- `src/app/page.tsx`：window 暴露（dev-only，含对称 cleanup）；
- `scripts/verify-liblib-batch510.py`：15 场景 + 静态隔离检查；
- 合同 §18.1 审计修订（差距收敛为 connection 反馈一项）+
  FIXTURE_CATALOG 状态升级；
- `runtime-audit.json`：本目录。

## 实施中修正的建模错误

- `settleOperation` 曾无条件覆盖 superseded/orphaned 状态（复活本应
  抑制的尝试）→ 改为仅在 running 时落终态；
- retry 曾只使 running 尝试失效 → 改为使同一 operation 的全部先前
  尝试失效（failed 后迟到的 completed 必须按 attempt-stale 抑制）；
- 公告去重键含渲染文本（failed 与迟到 completed 是不同公告；完全
  相同事件的回放才是 duplicate）。
