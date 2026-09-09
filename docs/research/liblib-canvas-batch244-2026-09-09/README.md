# Batch 244 — 首帧参考槽「销毁」按钮复刻（源站 2026-09-09 截图落地）

> 状态：`IMPLEMENTED`（batch 241 截图事实 → 实施 → 15 checks 验收 → 33 项回归绿）。
>
> 源站证据：`../liblib-canvas-batch241-2026-09-09/m-HappyHorse1.1.png`
> （槽悬停「销毁」）——本批无新增源站采样。

## 复刻范围辨析

- **参考槽「销毁」按钮**：实施。视觉源站忠实（槽悬停出现深色 销毁
  覆层）；点击行为（移除自动创建的图片节点与连线、清除尝试芯片、面板
  回到建议态）为 `CLONE_DECISION`——源站点击行为未采样，取
  `createFirstFrameReference` 的逆操作语义。
- **首帧态紧凑页脚（单 pill）**：**deferred**——紧凑页脚仅在 Happy Horse
  系（模式 首帧）截图中出现，而 2.5 的首帧态（batch 237 a1）为完整药丸行；
  属模型/模式相关变体，模式分布未采样全，不具备受控实施条件。

## 实施

1. `canvasStore.destroyFirstFrameReference(videoNodeId)`：找到视频节点的
   入边图片节点，单事务移除该节点与连线；保持视频节点选中；单条历史
   记录；无入边图片节点时为无操作。
2. `VideoGenerationPanel` 首帧槽：容器加 `group`；`onDestroyFirstFrame`
   存在时渲染悬停覆层按钮 `data-video-firstframe-destroy`（销毁，黑色
   70% 覆层、hover 显示）。
3. `VideoNode` 接线：销毁点击 → `destroyFirstFrameReference(id)` +
   `setAttempt(null)`（面板回到建议态）。

## 验收

- `verify-liblib-batch244.py`：**15 checks**（提交后 +1 节点 +1 边；槽
  存在；销毁按钮 DOM/文案/悬停可见；点击后节点与边回滚、芯片清除、槽
  消失、textarea 回归；重击芯片可重建参考——销毁后守卫放行）。
- 回归绿：21 / 22 / 26 / 33 / 100 / 111 / 128 / 141 / 145 / 146 / 149 /
  151 / 155 / 160 / 165 / 166 / 172 / 173 / 174 / 175 / 176 / 177 / 178 /
  189 / 191 / 213 / 215 / 218 / 236 / 237 / 238 / 239 / 240（33 项）。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。

## 不证明 / 后续候选

- 源站「销毁」点击的确切行为（是否同时清除提示词/回切模式）未采样；
- 紧凑页脚的模型/模式分布（需 Happy Horse 系及其它 首帧 态模型的
  对照采样）；
- OmniHuman 1.5 模式名与芯片上下文、Style Video / 动作迁移
  （BLOCKED_AUTOMATION）。
