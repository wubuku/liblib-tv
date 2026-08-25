# Video Continuation Workflow

## Purpose

复刻当前 LibTV 就绪视频的 `智能续写` 两阶段画布工作流：

```text
source ready video
  -> continuation range selector
  -> confirm
  -> connected continuation target video
  -> continuation prompt
```

## Selector Contract

- screen size：`660x56`
- node-relative centered overlay
- node-to-selector gap：`8 * zoom`
- close：`32x32`
- timeline：flex remainder, `48px` high
- start/end handles：`16px`
- confirm：`32px` high
- initial range：`0-min(sourceDuration,30)`
- range duration：`4-30s`
- duration label：two decimals
- direct manipulation：start handle, end handle, region
- `Escape` and close cancel

Stable selectors:

- `[data-video-continuation-selector]`
- `[data-video-continuation-timeline]`
- `[data-video-continuation-start]`
- `[data-video-continuation-end]`
- `[data-video-continuation-region]`
- `[data-video-continuation-duration]`
- `[data-video-continuation-confirm]`
- `[data-video-continuation-close]`

## Graph Contract

Confirm creates one transaction:

- target type：`video`
- target status：`empty`
- target name：`续写 {sourceLabel}`
- target position：source right + `120` world units
- one source-to-target edge
- continuation metadata:
  - source node ID
  - source label
  - start/end seconds
  - edge ID
- selection moves to target

Undo removes target and edge together. Redo restores both.

## Target Prompt Contract

- normal `660x274` video generation panel
- source/range visible prefix
- placeholder：`请输入需要续写的内容`
- model：`2.5`
- mode：`全能参考`
- model/mode cannot be changed while continuation metadata exists
- `退出续写模式` keeps target but removes continuation metadata and its declared edge

## Prototype Boundary

No real video clipping, upload, compliance checks, task generation, credits or persistence. Static thumbnails and local graph state stand in for service-backed behavior.
