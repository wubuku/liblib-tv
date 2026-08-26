# Batch 39：导演台路径整体变换与重置

> 状态：已完成。主实现、专项 Playwright、截图台账、Batch 35-39
> 跨批回归、稳定文档、`npm run check` 和提交推送均已闭环。

## Read Order

1. [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)：当前 LibTV transform/reset
   文案、跨 chunk 搜索结果和上游群组变换参考。
2. [`PLAN.md`](PLAN.md)：价值排序、状态边界、selectors 和验收矩阵。
3. [`DIRECTOR_PATH_TRANSFORM.spec.md`](DIRECTOR_PATH_TRANSFORM.spec.md)：
   固定 pivot、可逆路径变换、两类重置和 R3F 编辑合同。
4. [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：本批截图的一次性识图
   台账。
5. [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：提交、验证和中断接力记录。

## Batch Goal

```text
editable local anchors
  -> fixed path pivot
  -> path position / rotation / scale offset
  -> transformed world anchors + derived points
  -> existing playback/orient/capture pipeline
  -> 重置偏移 or 重置 creation snapshot
```

## Evidence Discipline

- **LibTV source fact:** 当前 locale 直接提供
  `directorMotionPathPosition / Rotation / Scale / Reset / ResetOffset`。
- **Runtime limit:** 对当前页面 108 个脚本做明文键名搜索后，只有 locale
  chunk 命中；没有获得原站 pivot、欧拉顺序、数值范围或两类重置行为。
- **Existing replication fact:** 固定上游包含围绕群组锚点应用缩放、X/Y/Z
  旋转和平移的 serializable store 算法，可借鉴数学边界，但不是 LibTV
  路径实现。
- **Clone decision:** 本批使用创建时固定质心 pivot、X→Y→Z 欧拉旋转、
  正比例缩放、`重置偏移` 清空 transform、`重置` 恢复创建快照并清空
  transform。它们必须保留为 calibration。

## Scope Boundary

本批不实现路径整体 TransformControls、负缩放、pivot 移动、路径 history/
persistence、属性曲线、动画视频导出或手机虚拟机位。

## Completion

- Plan: `42f1a3c`
- Main implementation: `21f5c01`
- Focused verification: `8d521cb`
- Stable documentation/finalization: recorded by the next documentation-only
  commit
