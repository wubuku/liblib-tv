# Batch 35：真实 R3F 导演台第一条纵切

> 状态：已完成并验证。现有无行为的“导演台”节点已改为可进入、可编辑、
> 可截图并可原子回到 React Flow 的真实 R3F 工作区。

## Read Order

1. [`PLAN.md`](PLAN.md)：价值排序、证据边界、实施顺序和验收标准。
2. [`DIRECTOR_WORKSPACE.spec.md`](DIRECTOR_WORKSPACE.spec.md)：工作区、状态、
   交互、截图与回流合同。
3. [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：本批 clone 截图的一次性
   识图台账。
4. [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：实施、验证、提交和中断接力记录。
5. [`../liblib-canvas-batch34-2026-08-26/README.md`](../liblib-canvas-batch34-2026-08-26/README.md)：
   原站证据、既有复刻代码考古和可移植性边界。

## Batch Goal

完成一条端到端用户路径：

```text
React Flow 导演台节点
  -> 全屏三栏导演工作区
  -> 真实 R3F 场景和机位
  -> 对象树 / 视口 / Inspector 同步
  -> 画幅框内 helper-free 截图
  -> 图片节点与来源连线
  -> 关闭并恢复原画布上下文
```

## Evidence Discipline

- **LibTV source fact**：导演台用于搭建 3D 场景并截图作为构图参考；当前 bundle
  还证明动画时间轴、路径、机位轨道和动画输出等更大能力面。
- **Existing replication fact**：固定上游仓库已经用 Three.js/R3F 实现静态
  3D 导演台、树/视口/属性联动、机位视角、画幅和截图回流。
- **Clone decision**：本批在当前 Next.js/React Flow 应用中实现独立、
  lazy-loaded R3F island；具体颜色、尺寸和初始场景是可验证的 prototype
  calibration，不冒充尚未量取的原站像素事实。

## Scope Boundary

本批包括真实 WebGL 场景、基本物体与机位编辑、截图回流和响应式工作区。
动画时间轴、关键帧、运动路径、手机运镜、外部模型库和动画视频回流留给后续批次。

## Protected Commits

- Plan: `47bc0f4`
- Main implementation: `3661cca`
- Verification/finalization: see [`IMPLEMENTATION.md`](IMPLEMENTATION.md)
