# Batch 40：导演台动画视频导出与画布回流

> 状态：已完成。真实浏览器录制、可播放视频回流、专项 Playwright、截图
> 台账、Batch 35-40 跨批回归、稳定文档和提交推送均已闭环。

## Read Order

1. [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)：当前 LibTV 导出词条、引导
   文案、上游缺口和证据边界。
2. [`PLAN.md`](PLAN.md)：价值排序、实现步骤、selectors 和验收矩阵。
3. [`DIRECTOR_ANIMATION_EXPORT.spec.md`](DIRECTOR_ANIMATION_EXPORT.spec.md)：
   浏览器录制、时间轴驱动、错误状态和画布事务合同。
4. [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：本批截图的一次性识图
   台账，生成截图前也保留为接力入口。
5. [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：提交、验证和中断接力记录。
6. [`MATURITY_ASSESSMENT.md`](MATURITY_ASSESSMENT.md)：核心导演工作流成熟度、
   剩余源站能力和下一批决策边界。

## Batch Goal

```text
source-backed export settings
  -> deterministic full-timeline playback
  -> cropped WebGL canvas recording
  -> real browser-playable video blob
  -> atomic video node + source edge transaction
  -> one-step canvas undo/redo
```

## Evidence Discipline

- **LibTV source fact:** 当前 canvas locale 直接包含导出设置、时长、比例、
  录制、成功、失败、只读、登录、上传和节点创建失败词条；引导文案明确要求
  预览后点击“导出视频到画布”继续编辑。
- **Runtime limit:** 尚未从登录态运行界面量到导出面板的精确几何、时长范围、
  编码格式、帧率、码率和上传 API；这些不能写成源站事实。
- **Existing replication fact:** 固定上游子模块没有动画时间轴、运动路径或
  视频导出实现，不能提供这一层的运行时合同。
- **Clone decision:** 以浏览器 `captureStream` + `MediaRecorder` 录制裁切后的
  R3F WebGL 画面，使用浏览器支持的 WebM 编码，并直接把 session-local blob
  URL 回写为可播放视频节点。后端上传和 MP4 转码保持明确未复刻。

## Scope Boundary

本批不实现 LibTV 账号/只读权限体系、远端上传、持久化媒体存储、MP4 转码、
音轨、服务端渲染、后台导出队列或导出取消。blob URL 只保证当前页面会话内
可播放。

## Completion

- Plan: `7a2ffab`
- Main implementation: `3065e92`
- Focused verification: `e085e63`
- Stable documentation/finalization: recorded by the next documentation-only
  commit
