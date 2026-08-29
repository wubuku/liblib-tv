# Batch 96 实施记录：Director 多机位与 Shot 工作流

> 状态：`IN_PROGRESS`
>
> 实施日期：2026-08-29。

## 1. 计划 checkpoint

计划文档已在 `36ed905` 之后落档。代码、验证和治理结果将在本文件持续更新。

## 2. 实施记录

### 2.1 Document / runtime

待完成。

### 2.2 Store / lifecycle

待完成。

### 2.3 UI / responsive

待完成。

## 3. 验证记录

待完成。截图识别策略为不新增截图；验证优先使用 DOM、store snapshot、导出
JSON、纯函数和 WebGL nonblank 检查。

## 4. 剩余风险

- LibTV 原站的 Director shot schema、时段语义和视觉布局仍为 `SOURCE_UNKNOWN`；
- capture bytes 仍是 session memory sidecar，不能宣称 durable media storage；
- 真实相机/镜头渲染和 cloud project sync 不在本批范围。

