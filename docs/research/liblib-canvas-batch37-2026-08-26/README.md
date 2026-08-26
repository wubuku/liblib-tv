# Batch 37：导演台运动轨迹与速度曲线第一条纵切

> 状态：已完成。主实现、专项 Playwright、截图台账、跨批回归、稳定文档、
> `npm run check` 和提交推送均已闭环。

## Read Order

1. [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)：当前 LibTV chunk 中的路径、
   轨迹、朝向与速度曲线命令合同。
2. [`PLAN.md`](PLAN.md)：价值排序、状态边界、实施顺序和验收标准。
3. [`DIRECTOR_MOTION_PATH.spec.md`](DIRECTOR_MOTION_PATH.spec.md)：路径采样、
   R3F 可视化、曲线编辑器和 selectors 合同。
4. [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：本批截图的一次性识图台账。
5. [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：实施、验证、提交和接力记录。
6. [`../liblib-canvas-batch36-2026-08-26/README.md`](../liblib-canvas-batch36-2026-08-26/README.md)：
   已完成的 typed timeline、关键帧和 playback 基线。

## Batch Goal

```text
selected transform/camera track
  -> 创建运动轨迹
  -> 直线 / 圆环 / 矩形路径
  -> visible R3F trajectory
  -> scrub/playback path sampling
  -> optional orient-to-path
  -> track speed curve
  -> functional Bezier editor and presets
```

## Evidence Discipline

- **LibTV source fact:** 当前线上 chunk 直接包含创建/绘制运动轨迹、三种预设路径、
  铅笔/钢笔路径、启用/删除曲线、沿路径朝向、曲线编辑器、线性/平滑/缓入/
  缓出/缓入缓出和贝塞尔调整等命令。
- **Existing replication fact:** 固定的 `storyai-3d-director-desk` 上游没有
  timeline、motion path 或 speed curve，本批没有可直接搬运的路径实现。
- **Clone decision:** 本批先实现三种有明确 source label 的预设路径、真实 R3F
  轨迹采样和 track-level speed curve。路径尺寸、控制点、颜色和曲线 preset
  数值是可替换 calibration，不冒充原站运行时测量。

## Scope Boundary

本批不实现铅笔/钢笔自由绘制、Bezier path anchor type/handle 编辑、路径
position/rotation/scale offset Inspector、pose/group track、动画视频导出或手机
虚拟机位。它们保留为后续批次，不以 disabled 假控件冒充完成。

## Completion

- Plan: `baf0db9`
- Implementation: `e4d7ecf`
- Focused verification: `f7a9b64`
- Stable documentation: `2493653`
- Finalization: recorded in the next documentation-only commit
