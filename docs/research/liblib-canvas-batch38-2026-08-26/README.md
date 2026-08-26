# Batch 38：导演台自由路径创作与锚点编辑

> 状态：计划与证据边界已落档；实施、专项 Playwright 和稳定文档待完成。

## Read Order

1. [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)：当前 LibTV chunk、既有登录态
   证据和上游复刻的事实边界。
2. [`PLAN.md`](PLAN.md)：价值排序、实施纵切、selectors 和验收矩阵。
3. [`DIRECTOR_PATH_AUTHORING.spec.md`](DIRECTOR_PATH_AUTHORING.spec.md)：
   serializable anchor、自由绘制、Bezier 控制柄和 R3F 交互合同。
4. [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：本批截图识别台账；
   生成截图后只识别一次。
5. [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：提交、验证和中断接力记录。

## Batch Goal

```text
selected transform/camera track
  -> 自由绘制
  -> 铅笔路径 drag / 钢笔路径 point-and-drag
  -> serializable anchors + optional Bezier handles
  -> select/move/insert/delete anchor
  -> 顶点 / 对称 / 非对称
  -> live R3F curve + existing scrub/playback/capture pipeline
```

## Evidence Discipline

- **LibTV source fact:** 当前线上 chunk 明确包含 `正在绘制曲线`、`自由绘制`、
  `铅笔路径`、`钢笔路径`、`锚点类型`、`顶点`、`对称`、`非对称`，并把
  自由路径置于现有“创建路径 -> 播放预览 -> 导出到画布”的导演台流程中。
- **Existing replication fact:** 固定的
  `research/upstream/storyai-3d-director-desk` 没有 timeline、motion path、
  path anchor 或 Bezier path editor，可借鉴的是 R3F/TransformControls 和
  store mutation 边界，不是路径实现。
- **Clone decision:** 本批使用水平绘制平面、pointer-up 完成铅笔路径、
  显式完成钢笔路径、每段 12 次 Bezier 细分、路径 Inspector 位置和按钮布局。
  这些是可替换 calibration，不冒充原站运行时测量。

## Scope Boundary

本批不实现路径整体 position/rotation/scale offset、路径 undo/redo/persistence、
属性曲线、动画视频导出、手机虚拟机位或原站未测量的精确 3D hit area。

