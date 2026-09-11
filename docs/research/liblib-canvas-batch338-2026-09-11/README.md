# Batch 338 — 播放器截帧悬停菜单不可点击缺陷修复（`PRODUCT_FIX`）

> 状态：修复 clone 视频节点播放器「截取当前帧」悬停菜单的真实产品
> 缺陷（菜单项被 react-flow pane 遮挡，真实用户无法点中）；
> batch 29 验证器从 TimeoutError 恢复全绿。源站恢复探测：仍失效。

## 源站状态

恢复探测（goto + 20s 水合 + 触发器三次开合）：
`RECOVERY: still-broken`——BLOCKED_SOURCE 三项（Hailuo 系条件分解、
480P 档批量、Style Video 费率）维持阻塞。

## 产品缺陷与修复（`PRODUCT_FIX`）

**缺陷链**（batch 29 验证器 run_player_menu_action 的 TimeoutError 插桩定位）：

1. `PlayerFrameCaptureMenu` 的菜单为节点内 `absolute bottom-full`
   定位，几何上溢出节点盒；
2. 溢出部分落入 react-flow pane 层——菜单项中心的 elementFromPoint
   命中 `DIV.react-flow__pane`（插桩直证），点击落在 pane 上；
3. wrapper 的 `onMouseLeave` 在指针离开相机按钮几何边界时立即关闭
   菜单——双重原因导致菜单项永远无法点击。

**修复**：

- 菜单改为 `createPortal` 挂载到 body + `position: fixed` 对齐相机
  按钮（右缘对齐、菜单底贴合按钮顶，零间距保持 batch 29 几何合同），
  逃出节点 stacking context；
- wrapper `onMouseLeave` 检查 `relatedTarget`：指针移入 Portal 菜单
  内则保持开启；菜单自身 `onMouseEnter`/`onMouseLeave` 管理悬停态。

## 验收

- `verify-liblib-batch29.py` 全绿（TimeoutError → passed；含触发相对
  几何、截取元数据、重复截取避免等全量合同）；
- 维护集 45 项（42 基线 + 332/334/336）全绿——VideoNode 变更无回归；
- `npm run check` 0 errors（8 warnings 基线）；docs check 通过
  （897 Markdown）。

## 后续候选

- 其余 12 项 AGED_GATE/历史合同失败维持归档（低优先现代化）；
- 源站恢复后 BLOCKED_SOURCE 补采；
- 图片栏 对话/展开 目标行为采样。
