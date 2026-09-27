# Batch 547 — 摄像机面板「切换机位」下拉

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。源站采样（截图
> 47-director-rightclick-tree.png）：摄像机面板字段顺序 名称 →
> **切换机位**（机位1）→ 位置 → …；切换机位切换当前活动机位。

## 合同

- 摄像机属性面板（selected.kind === "camera"）在「名称」下方渲染
  「切换机位」select（`data-director-camera-switch`）；
- 选项列出场景内全部 camera 对象（机位名）；选中项 = 当前绑定 shot；
- 切换 → `selectShot(shot.id)`：更新 `activeCameraId` + `activeShotId`
  （store 既有机制）；**不改 viewMode**——视角由顶部分段控件独立管理
  （与源站行为一致：面板内切换机位不强制跳机位视角）；
- 无绑定 shot 的机位选项 disabled；非 camera 对象面板不渲染该控件；
- batch 536/540/541/546 全部合同保持。

## 内容

- `src/components/director/DirectorInspector.tsx`（selectShot 引入 +
  切换机位 select）；
- `scripts/verify-liblib-batch547.py`（8 检查：双机位选项、切换更新
  activeCameraId、viewMode 不变、往返切换）；
- 回归：batch 70/536 全绿；typecheck 净；lint 0 error。
- `runtime-audit.json`：本目录。
