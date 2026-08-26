# Batch 38 Source Evidence

## 1. Current LibTV Artifact

Observation date: 2026-08-26.

The target canvas HTML was fetched again from:

```text
https://www.liblib.tv/canvas?spaceId=670983&projectId=5f2550d0036944e2b618f494276fa1dd
```

The response was `648317` bytes and referenced the same current locale chunk
used by Batches 36-37:

```text
https://liblibai-web-static.liblib.cloud/liblibtv_online/static/_next/static/chunks/0_o2gxip5splz.js
```

| Artifact | Size | SHA-256 |
|---|---:|---|
| gzip response | `113458` bytes | `ca7be6208e2c16a57f718398f14b3fcb389daf5760644551558aa67d1976f492` |
| decoded JavaScript | `343745` bytes | `58ea14cd8358885f35147986fdafe6a2c7391b6111fd1e6e02283668d1bae277` |

The hashes still match Batch 37, so this batch extends rather than replaces the
existing evidence baseline.

## 2. Direct Current Product Vocabulary

Exact current locale values:

```text
新增路径
正在绘制曲线
自由绘制
铅笔路径
钢笔路径
圆环路径
直线路径
矩形路径
名称
启用曲线
锚点类型
顶点
对称
非对称
位置
旋转
缩放
绑定对象沿路径朝向
重置
重置偏移
```

This directly proves:

- freehand and pen tools coexist with the three preset paths;
- a selected path has named, enabled and transform-related properties;
- anchors have at least vertex, symmetric and asymmetric semantics;
- the source data model is richer than the Batch 37 passive point array.

It does **not** prove exact pointer gestures, control-handle colors, hit radius,
Bezier subdivision, drawing plane, completion gesture or panel geometry.

## 3. Existing Guided Workflow

The current source guide retained from Batch 37 states:

```text
点击创建路径，弹出选项面板
点击圆环/直线/矩形创建路径，或用铅笔/钢笔工具绘制想要路径
路径绘制后点击播放，可预览动画
预览动画效果已确认，点击“导出视频到画布”，可以在画布内，进行后续编辑
```

Therefore pencil/pen output must enter the same real playback pipeline as preset
paths. A decorative drawing layer that does not drive scene sampling would not
satisfy the source workflow.

## 4. Prior Login-State Evidence

The current session's earlier login-state exploration directly established the
full-screen director workspace, timeline, track selection and path/curve product
surface. Batch 37 recorded that runtime evidence and its screenshot-cost ledger
under:

- `docs/research/liblib-canvas-batch37-2026-08-26/`
- `docs/research/liblib-canvas-batch35-2026-08-26/`

No Batch 38 source screenshot is claimed. The current automation pass could
reconfirm the online artifact and locale contract, but not recover a new
authenticated anchor-drag screenshot. Exact visual calibration remains open.

## 5. Existing Replication Boundary

The fixed upstream submodule at commit
`8c8bd361790be4d37158a7430365e65546e358fe` contains a real R3F viewport,
selection, TransformControls and serializable Zustand mutations. Static search
again found no timeline, motion path, trajectory, Bezier path or path-anchor
implementation.

Borrowable implementation facts:

- R3F owns runtime objects and hit testing;
- Zustand owns serializable authoring state;
- TransformControls commits completed drags back to the store;
- helper objects stay outside exported media.

The upstream does not supply source truth for pencil/pen interaction.

## 6. Clone Calibration Required

Batch 38 must label these choices as clone decisions:

- drawing on a horizontal plane at the bound object's current Y;
- pencil point decimation threshold;
- pen completion via explicit command or Enter;
- pen click-drag creating symmetric handles;
- 12 samples per curved segment;
- anchor/handle size, color and selected state;
- path Inspector placement and insert/delete/closed controls;
- one selected anchor and one selected handle at a time.

