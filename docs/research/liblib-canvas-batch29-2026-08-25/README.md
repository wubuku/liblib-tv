# Batch 29：视频首帧、尾帧与当前帧截取

> 状态：规划中。当前线上 bundle 证据、clone 缺口、工作流规格和实施计划已落档。

## 批次前缺口

当前 clone 的 ready-video 工具条在 `画面编辑` 后直接进入下载区：

- 缺少 `截取首帧 / 截取尾帧 / 截取当前帧` 工具组；
- 播放栏缺少 camera 快捷入口及 hover 菜单；
- 无法从视频创建 image resource node；
- 没有 source-to-image edge、截取时点 metadata 或重复截取避让；
- 当前图片节点无法区分普通图片与视频帧结果。

2026-08-25 当前线上 bundle 已覆盖入口顺序、菜单视觉参数、截取时点、
命名、图片节点创建、连接方向和初始位置。本批据此实现一条可验证的
representative workflow。

## 本批范围

- 在 ready-video 顶部工具条增加三项 frame-capture menu；
- 在视频播放栏增加 camera 当前帧快捷入口和同组三项 hover menu；
- 新增 source-backed image graph transaction；
- 保存 kind、时点、name、alt、source 和 edge metadata；
- 首个结果使用 source right `+100` world units、同 Y；
- 重复截取使用确定性的 clone 碰撞避让；
- 截取后保留 source selection，使工具条可继续使用；
- 一次 undo/redo 回退或恢复单个 image + edge；
- 补专项 Playwright、截图台账、跨批回归和工程门禁。

## 阅读顺序

1. [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)
2. [`PLAN.md`](PLAN.md)
3. [`FRAME_CAPTURE_WORKFLOW.spec.md`](FRAME_CAPTURE_WORKFLOW.spec.md)
4. [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)
5. [`IMPLEMENTATION.md`](IMPLEMENTATION.md)

## 原型边界

clone 当前只有本地 poster，没有真实视频 URL 和 `<video>` 解码资源。本批
因此使用 source poster 作为代表性 frame bitmap，不声称真实 seek、canvas
绘制、PNG 上传或异步 resource replacement 已实现。源站真实媒体流程及其
timeout 只作为背景证据记录。
