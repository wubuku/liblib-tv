# Batch 438 — VGP §7.2 host resize reconciliation（resize anchor 中心保持）

> 状态：`IMPLEMENTATION_RECORDED`（viewport 合同 §7.2 声明政策的
> runtime 实现；clone-only 默认，无源站依赖；心跳批次）。
>
> 证据：`runtime-audit.json`、
> `docs/design-references/liblib-clone-batch438-resize-anchor-1200-2026-09-13.png`、
> `scripts/verify-liblib-batch438.py`。

## 变更（src/app/page.tsx）

ResizeObserver 观察 React Flow host；host 尺寸变更（非断点翻转）时按
合同 §7.2 中心保持政策调和视口：

```text
oldCenterFlow = (oldHost.center - live.x/y) / zoom
nextViewport  = newHost.center - oldCenterFlow * zoom  （zoom 不变）
```

- **仅 stable（用户自有）所有权**适用：bootstrap 阶段（batch 65 响应式
  预设权威域）记 skip（`resize-anchor-not-applicable`）；
- **断点翻转委托**：`max-width:768px` 翻转时跳过（
  `breakpoint-flip-delegated`），交还 batch 65 响应式 effect 处理，
  避免双权威竞争；
- 每次裁决入 `__libtv_viewport_owner_log`（declared reasons 扩展：
  `resize-anchor` / `resize-anchor-not-applicable` /
  `breakpoint-flip-delegated`）；提交即写 live（`setViewport`）与
  stable（store viewport），zoom 百分比经既有 live 投影路径更新。

## 验收（verify-liblib-batch438.py，SCRIPT_RECORDED_PASS）

- **bootstrap_resize_skipped**：用户交互前 resize 不调和、skip 有日志、
  所有权仍 bootstrap；
- **resize_anchor_center_preserved**：滚轮纵移获得 stable 所有权后，
  host 929×874 → 1360×940，zoom 不变（<0.01），旧 host 中心的 flow 点
  落在新 host 中心（偏差 <2px），日志有 `resize-anchor` 提交；
- **stored_viewport_survives_switch**：调和后视口跨画布切换往返保持；
- console/pageerror/requestfailed 为 0；无溢出。

## 后续

VGP 合同 runtime 余项：full live/stable endpoint phase（§6.3
逐帧 live + 单稳定端点压缩）。多画布 lifecycle（VR-017）runtime 至此
仅剩该 VGP 域余项。
