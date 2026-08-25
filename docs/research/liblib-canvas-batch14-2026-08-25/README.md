# Batch 14：Agent 与分享面板的原站结构复刻

> 日期：2026-08-25
> 范围：LibTV 顶部分享菜单与右侧 Agent 抽屉。
> 目标：用已保存的原站截图校准高频命令面的结构、文案和本地交互状态。

## 当前缺口

- Agent 标题、工具栏、Skill 推荐区和输入区与原站截图差异明显。
- 当前 Agent 只有 3 个静态文字卡，缺少原站 2×2 图片 Skill 卡、换一批和浏览器通知提示。
- 当前输入区没有受控状态，发送按钮是死按钮。
- 分享面板的尺寸接近原站，但标题、说明文案和两个命令均是 clone-only 占位。

## 证据

- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：一次性识别已保存的 Agent/share 原站截图。
- [`../liblib-live-2026-08-25/README.md`](../liblib-live-2026-08-25/README.md)：原站 340px Agent 抽屉、360px 分享面板和证据边界。
- [`../liblib-canvas-batch11-2026-08-25/`](../liblib-canvas-batch11-2026-08-25/)：顶层 overlay 互斥与生命周期。

## 边界

- 只复刻前端结构和可验证本地状态，不发送 Agent 任务、不发布作品、不生成真实分享链接。
- 推荐 Skill 使用当前项目已有本地图片作为缩略图；不声称这些图片就是原站推荐服务返回的素材。
- 不改变 `uiStore` overlay 互斥规则，不混入 FrameOS Agent。

## 导航

- [`PLAN.md`](PLAN.md)
- [`AGENT_SHARE.spec.md`](AGENT_SHARE.spec.md)
- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)

