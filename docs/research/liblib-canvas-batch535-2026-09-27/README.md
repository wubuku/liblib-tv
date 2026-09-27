# Batch 535 — 导演台底部场景输入条

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。第二轮源站采样
> （liblib-source-exploration-2026-09-25 NOTES §8 + 截图
> 18-director-console-opened.png）：3D 导演台视口底部居中胶囊条——
> 左段三模式图标（光标/相机/手）+「+ 描述想要搭建的场景」输入 + ↑ 圆形
> 提交；左下另有 ? 帮助圆钮（交互未采样，本批不克隆）。

## 合同

- 挂载于导演台工作区视口内底部居中（`data-director-scene-prompt-bar`），
  双胶囊分段：模式段 + 输入段；
- 模式图标 光标/相机/手 可切换（`data-director-scene-mode`，
  aria-pressed 单选态，默认光标）；
- 输入维护本地草稿；↑ 提交（或 Enter）→ 本地确认回显
  「场景描述已记录（本地草稿）」（`data-director-scene-prompt-status`，
  2 秒淡出）——真实场景搭建为云端 AI 动作，clone 不触发任何生成、
  无网络请求（diagnostics:zero 覆盖）；
- 空输入时提交按钮禁用。

## 内容

- `src/components/director/DirectorScenePromptBar.tsx`（新组件）；
- `src/components/director/DirectorDesk.tsx`（视口 main 内挂载）；
- `scripts/verify-liblib-batch535.py`（8 检查：占位、三模式切换、
  草稿提交、本地回显）；
- 回归：batch 70（导演台工作区 + TransformControls 路径）绿；
  lint 0 error；typecheck 仅并行 WIP 错误。
- `runtime-audit.json`：本目录。
