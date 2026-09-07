# Batch 162 — 视频面板移动端（390×844）断点核查

## 结论（397px 增高后无移动端回归）

390×844 实测（Batch 161 增高后）：

- 页面无横向溢出（scrollWidth 390 == innerWidth 390，延续 batch21 契约：
  面板超出视口由画布裁切，页面不滚动）。
- 面板垂直方向完整落在视口内（bottom 641 < 844）。
- 提示词 textarea 95px 完好（与桌面端一致）。
- 面板 660px 宽自 x=456 起 —— 右侧超出视口被裁切，为既有既接受行为。

## 实施（验证器加固，无产品代码变更）

`verify-liblib-batch161.py` 扩展 mobile 阶段（390×844）：无页面溢出 /
面板高度 397 / 提示词完好 / 垂直可见 / 截图存档
`docs/design-references/liblib-clone-batch162-video-panel-mobile-390-2026-09-07.png`。

## 验收

- `verify-liblib-batch161.py`：10 checks（桌面 4 + 移动 6）。
- `npm run check`：0 errors、8 warnings（既有基线）。
