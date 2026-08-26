# Batch 36：导演台动画时间轴第一条纵切

> 状态：已完成、验证并形成可接力记录。当前结果是在 Batch 35 的真实 R3F
> 工作区中加入 source-backed、可播放、可编辑并能确定性驱动场景的
> typed timeline。

## Read Order

1. [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)：2026-08-26 当前线上 HTML/chunk
   重新提取的时间轴术语和证据边界。
2. [`PLAN.md`](PLAN.md)：价值排序、范围、实施顺序和验收标准。
3. [`DIRECTOR_TIMELINE.spec.md`](DIRECTOR_TIMELINE.spec.md)：timeline state、
   interpolation、交互、响应式与 selectors 合同。
4. [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：本批截图的一次性识图台账。
5. [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：实施、验证、提交和接力记录。
6. [`../liblib-canvas-batch35-2026-08-26/README.md`](../liblib-canvas-batch35-2026-08-26/README.md)：
   已完成的 R3F 工作区与画布回流基线。

## Batch Goal

```text
Director object/camera
  -> typed timeline track
  -> add/select/delete keyframes
  -> scrub or playback
  -> deterministic interpolation
  -> live R3F scene/camera update
  -> optional auto-keyframe from Inspector or gizmo commit
```

## Evidence Discipline

- **LibTV source fact:** 当前线上 chunk 直接包含动画时间轴、播放头、播放/暂停、
  循环、缩放、新建轨道、上一/下一关键帧、typed keyframes、曲线和动画回画布
  等产品合同。
- **Existing replication fact:** 固定上游导演台复刻没有时间轴，本批不能把其
  静态工作区当成当前 LibTV 的完整能力面。
- **Clone decision:** 首批只让现有 character/prop/camera schema 可真实采样；
  8 秒 duration、轨道高度、像素密度和默认关键帧是本批可替换 calibration。

## Scope Boundary

本批不做曲线编辑器、运动路径、姿态/SAM 骨骼、分组动画、动画录制与视频回流。
这些能力有 source contract，但需要后续批次先补对应 runtime model，不能只画
一组无行为控件。
