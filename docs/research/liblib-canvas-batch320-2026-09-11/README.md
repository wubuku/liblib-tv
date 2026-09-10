# Batch 320 — Style Video 禁用态数值确证：非音频单一因素（源站 2026-09-11）

> 状态：`BLOCKED_AUTOMATION` 维持（禁用条件未完全识别；无代码变更）。
>
> 证据：`StyleVideo.png`、`sample-log.json`（row opacity = 0.5）。

## 记录

- 全新会话（干净画布，仅首帧图片附挂、无音频素材）下 Style Video 行
  **opacity = 0.5（禁用态数值确证）**——排除音频单一因素；
- 禁用条件为模型自身的素材/模式要求（Style Video 为风格图生视频，
  可能需风格参考图而非首帧图），具体条件未识别 `SOURCE_UNKNOWN`；
- Kling3.0 动作迁移 行本轮不在视口（滚动定位后丢失），维持
  BLOCKED_AUTOMATION。

## 模型覆盖率最终状态

35 模型中 **33 项已有费率/数据点**。Style Video 与 Kling3.0 动作迁移
维持 BLOCKED_AUTOMATION（禁用条件未识别，需人工采样或源站条件文档）。

## 验收

- docs check 通过；源站画布 **0 残留**；无代码变更。
