# Batch 37 Source Evidence

## 1. Fresh Extraction

Observation date: 2026-08-26.

The same current LibTV chunk used by Batch 36 was fetched and decoded again:

```text
https://liblibai-web-static.liblib.cloud/liblibtv_online/static/_next/static/chunks/0_o2gxip5splz.js
```

| Artifact | Size | SHA-256 |
|---|---:|---|
| compressed response | `113458` bytes | `ca7be6208e2c16a57f718398f14b3fcb389daf5760644551558aa67d1976f492` |
| decoded JavaScript | `343745` bytes | `58ea14cd8358885f35147986fdafe6a2c7391b6111fd1e6e02283668d1bae277` |

The hashes match Batch 36. The minified source remains outside the repository;
this document preserves the extracted product vocabulary and nearby guide copy.

## 2. Direct Motion-Path Commands

Exact current locale values:

```text
创建运动轨迹
绘制轨迹
运动轨迹
新增路径
正在绘制曲线
启用曲线
删除曲线
自由绘制
铅笔路径
钢笔路径
直线路径
矩形路径
圆环路径
绑定对象沿路径朝向
已开启沿路径朝向，Y 轴旋转由运动轨迹控制
```

The path property vocabulary also contains:

```text
名称
锚点类型
顶点
对称
非对称
位置
旋转
缩放
重置
重置偏移
```

This proves that the source path model is editable and richer than a passive
polyline. It does not reveal current runtime geometry, path dimensions or exact
Bezier handle behavior.

## 3. Direct Speed-Curve Commands

Exact current locale values:

```text
设置曲线
曲线编辑器
返回时间线
选择一个轨道后编辑速度曲线
线性
平滑
缓入
缓出
缓入缓出
调整贝塞尔曲线
贝塞尔曲线参数
```

`选择一个轨道后编辑速度曲线` establishes track selection as the curve-editor
context. The preset names and explicit Bezier adjustment support a functional
curve editor rather than a decorative graph.

## 4. Direct Guided Workflow

The current source guide is explicit about the end-to-end interaction order:

```text
请选择一个角色或者摄像机后，可新建轨道
点击创建路径，弹出选项面板
点击圆环/直线/矩形创建路径，或用铅笔/钢笔工具绘制想要路径
路径绘制后点击播放，可预览动画
预览动画效果已确认，点击“导出视频到画布”，可以在画布内，进行后续编辑
```

This is the strongest Batch 37 evidence. It proves that preset path creation,
playback preview and later animation export belong to one director workflow.

## 5. Auto-Path Naming

The source contains typed fallback names:

```text
机位自动帧轨迹
道具自动帧轨迹
角色自动帧轨迹
```

Batch 37 may therefore name clone-created paths by object kind. Exact source
numbering, uniqueness rules and persistence remain unresolved.

## 6. Existing Replication Boundary

The fixed upstream submodule at
`research/upstream/storyai-3d-director-desk` contains no timeline, motion-path
or speed-curve runtime. Searches for path/trajectory/curve only find unrelated
Canvas 2D drawing helpers and camera orientation tests. Batch 37 is a new
source-backed extension over the Batch 35/36 R3F implementation.

## 7. Runtime Questions Still Open

- Exact path menu placement and whether it is toolbar- or track-relative.
- Whether the curve editor replaces, expands or overlays the timeline.
- Default path dimensions and coordinate plane.
- Whether preset paths create keyframes automatically.
- Exact curve preset control points.
- How path anchors and symmetric/asymmetric handles are manipulated in 3D.
- Whether camera paths can use orient-to-path while follow/look-at is active.

All corresponding Batch 37 choices must remain labeled clone calibration.
