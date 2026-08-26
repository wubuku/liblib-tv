# Batch 54：图片元素编辑空态

> 状态：实施中（2026-08-26）。本批复刻当前 LibTV selected image 的
> `元素编辑`空 authoring state，不创建有效 edit record，不提交生成任务。

## 目标

```text
selected image + standard toolbar + generation panel
  -> click 元素编辑
  -> dedicated 272x44 toolbar
  -> node-local edit stage + mask/guide
  -> 400x50 empty record panel
  -> Escape / close
  -> same selected image + standard double overlay
```

## 文档入口

- [`PLAN.md`](PLAN.md)：价值、范围、实施步骤和验收门；
- [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)：源站事实、推断和 clone 决策；
- [`../components/ImageElementEditMode.spec.md`](../components/ImageElementEditMode.spec.md)：
  状态、DOM、几何和生命周期合同；
- `IMPLEMENTATION.md`：实施后补充代码、验证和提交历史；
- `SCREENSHOT_ANALYSIS.md`：本地截图生成后补充唯一识图记录；
- `runtime-audit.json`：专项 Playwright 生成的 desktop/mobile 结构化测量。

## 明确边界

- 只支持单个已选图片的空元素编辑态；
- `点选`默认 active，`点选 / 框选 / 画笔`只切换本地空态视觉；
- 空态撤销和生成不可用；
- 不创建 edit record，不上传、不生成、不创建派生节点；
- 不修改 nodes、edges、selection、Prompt、viewport 或 graph history；
- 不修改旋转、图层分离、下载、FrameOS、Director 或真实 provider。

