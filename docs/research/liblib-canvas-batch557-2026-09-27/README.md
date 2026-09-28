# Batch 557 — 摄像机轨道行「ⓘ 绘制轨迹」affordance

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。源站证据：batch 552
> （截图 48）——时间线轨道行 1「主机位」右侧带「ⓘ绘制轨迹」affordance。

## 合同

- camera 轨道行（无绑定 motion path）右侧渲染
  `data-director-track-draw-trail`（Info 图标 + 绘制轨迹，span
  role=button——避免源站行内 button 嵌套 button 的 hydration 警告）；
- 点击 → `selectTimelineTrack(track.id)` + 打开与控制簇「创建运动轨迹」
  同一运动路径菜单（togglePathMenu）；
- 已绑定 motion path 的行显示既有 Route 绑定图标（不变）；
- 非 camera 轨道行不渲染该 affordance。

## 内容

- `src/components/director/DirectorTimeline.tsx`（camera 行 affordance）；
- `scripts/verify-liblib-batch557.py`（5 检查：affordance 可见、菜单
  打开、ESC 关闭）；
- 回归：batch 70/553/556 全绿（引导气泡与轨道行共存）；typecheck 净；
  lint 0 error。
- `runtime-audit.json`：本目录。
