# Batch 53：图片空标注替换态

> 状态：已完成（2026-08-26）。本批把当前图片工具条的
> `标注` 入口推进为 source-backed 的空 authoring state，不实现绘制和真实保存、
> 远程任务或 graph mutation。

## 目标

```text
selected image + standard toolbar + generation panel
  -> click 标注
  -> dedicated 536x49 toolbar
  -> standard bottom panel removed
  -> DPR=2 canvas overlays the image node
  -> Escape / close
  -> same selected image + standard double overlay
```

## 文档入口

- [`PLAN.md`](PLAN.md)：缺口、证据、范围、实施和验收门；
- [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)：标注空态的已知源站合同；
- [`../components/ImageAnnotateMode.spec.md`](../components/ImageAnnotateMode.spec.md)：
  组件、状态和几何合同；
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：实施、验证、截图和提交结果；
- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：本批截图唯一识图记录；
- [`runtime-audit.json`](runtime-audit.json)：desktop/mobile rect 和状态记录。

## 明确边界

- 只支持单个已选图片的空标注态；
- 入口进入 active tool 后替换标准 toolbar，不叠加第三个浮层；
- canvas 只负责 source-shaped surface 和 DPR backing size；
- 本批不记录 stroke、不显示有效草稿、不执行真实保存；源站可见的 `保存` 控件保持 enabled；
- 不上传、不生成、不创建派生节点、不修改节点数据或 history；
- 不修改视频、FrameOS、Director、AutoLink 或真实 provider。

## 验证结果

- Batch 53 focused Playwright：通过；
- Batch 52、10、11 相邻回归：通过；
- code/runtime checkpoint：`7055776`；
- active image shortcut isolation fix：`8f468eb`；
- 完整结果见 `IMPLEMENTATION.md`。
