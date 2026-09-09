# Batch 262 — UI 层去选重选验证收敛 + 维护集稳定性确认

> 状态：`VERIFIED`（batch 255 放弃的几何重选路径在本批闭环；维护集
> 37 脚本全绿；无代码变更）。

## UI 层验证（`ui-reselect.png`）

Batch 255 曾因预设节点屏幕重叠放弃几何重选断言。本批以 clone 暴露的
`window.__libtv_store.removeNode` 先移除预设视频节点（消除重叠），
随后完整 UI 路径全绿：

1. 添加面板 → 新视频节点（自动选中，data-id 捕获）；
2. 提交 首帧生成视频 芯片（selected）；
3. 顶右空白处点击 → **取消选中确认**；
4. 按 data-id **几何重选**（无 force）→ 选中恢复；
5. **芯片保持已提交**（aria-pressed=true）+ 首帧槽仍在——与源站
   持久态（batch 254）一致。

## 维护集稳定性

37 项验证脚本全绿；`npm run check` 0 errors（8 warnings 基线）；
docs check 通过（823 文件）；源站画布 0 残留。

## 后续候选

- OmniHuman 音频路径（BLOCKED_AUTOMATION——需素材库拖拽或人工）；
- Style Video / Kling3.0 动作迁移（BLOCKED_AUTOMATION）；
- 素材库门后内容（需用户授权承诺书）。
