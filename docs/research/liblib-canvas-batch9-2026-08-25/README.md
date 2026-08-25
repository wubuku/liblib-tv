# LibTV 画布 Batch 9：选中节点双浮层锚定

> 建档日期：2026-08-25
> 状态：计划、实施、专项验证、跨批回归和完整工程检查已完成
> 目标：以保存的原站 DOM 几何为基准，审计并加固图片/视频节点选中后浮层的节点锚定、反缩放和生命周期。

## 为什么做这一批

图片节点选中后同时出现上方工具条和下方编辑面板。用户已经明确指出旧 clone 曾把两个浮层放乱；该体验又是画布生成工作流中最显眼、最高频的反馈之一。

Batch 8 把失败视频改成视频组的真实 child 后，还需要确认节点内生成面板在 parent drag、child drag、pan 和 zoom 下仍严格跟随 child，而不是错误参考 parent 或浏览器视口。

## 文档导航

- [`PLAN.md`](PLAN.md)：缺口、价值、范围和验收标准
- [`FLOATING_UI_ANCHOR.spec.md`](FLOATING_UI_ANCHOR.spec.md)：原站证据、几何公式和行为合同
- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：本批原站/clone 截图的详细识图记录与复用边界
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：测量、实施、验证、提交和接力记录

## 证据入口

- `docs/research/liblib-live-2026-08-25/image-node-state-audit.json`
- `docs/research/liblib-seedance-2.5-2026-08-25/live-audit.json`
- `docs/research/components/ImageEditPanel.spec.md`
- `docs/design-references/liblib-original-image-selected-2026-08-25.png`
- `docs/design-references/liblib-original-seedance-video-selected-2026-08-25.png`

## 证据边界

原站节点、工具条和编辑面板的屏幕矩形、无视口夹取行为、DOM class 与控件文案是直接事实。锚定公式由这些直接几何反推；专项测试选择哪些节点、拖动多少像素和容差范围属于 clone 的回归验证设计。

## 本批结果

- 图片顶部工具条校准为原站测得的 `900.5x49`；
- 图片和视频的节点内底部面板从实际 `15 * zoom` 间距修正为 `16 * zoom`；
- `929x874` 整理态实测图片和视频面板中心误差均为 `0px`；
- 面板屏幕尺寸在 `28%` / `38%` 下保持 `660x274`；
- 靠左图片的工具条与面板仍允许 `x < 0`，没有加入原站不存在的视口夹取；
- 视频 child drag、pan 和 zoom 时面板持续跟随；
- parent drag 会切换选择到 parent，因此面板卸载；重新选择 child 后在新绝对位置准确重建；
- 多选时所有单节点大型浮层隐藏；
- Batch 4-Batch 9 与 `npm run check` 全部通过。

关键提交：

```text
466333f docs: plan LibTV floating UI anchor batch
c0d7e72 fix: align LibTV selected node overlays
ddc985b docs: persist screenshot recognition findings
```
