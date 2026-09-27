# Batch 540 — rail「添加机位」接通场景树同源动作

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。源站实证（batch 537 rail
> DOM 枚举）：rail「添加机位」为直接动作（点击无面板），与场景树
> 「新增机位」共享机位创建语义。本批把该动作接到
> `directorStore.addDirectorCamera`（场景树/Inspector 同一 action）。

## 合同

- rail add-camera 点击 → `addDirectorCamera()`：场景树新增「机位N」
  条目（与树按钮同源，连续点击递增）；
- 动作项不抢激活态——scene 保持激活（`aria-pressed` 不变），无任何
  flyout/modal 打开；
- batch 536 verifier 的「add-camera 激活态迁移」断言迁移至本合同
  （台账规则：记录合同更替——537 证实其为动作项而非面板项）。

## 内容

- `src/components/director/DirectorIconRail.tsx`（add-camera 分支）；
- `scripts/verify-liblib-batch540.py`（7 检查：树条目递增、无面板、
  激活态保持、树按钮同源）；
- `scripts/verify-liblib-batch536.py`（断言迁移）；
- 回归：batch 536/70 全绿；typecheck 净；lint 0 error。
- `runtime-audit.json`：本目录。
