# Batch 32：深度动作捕捉参考工作流

> 状态：已完成并推送。目标是把原站 bundle 已确认、但 clone 原先缺失的
> “深度动作捕捉”推进到可审查的参数、校验、提交和 pending graph 原型闭环。

本批继续遵守“先证据、再规格、再实现、再验证”的顺序。现有证据能够确认
能力语义、关键文案、参数校验提示和派生节点命名，但没有保存完整的登录态
深度动作捕捉 DOM 截图或精确矩形。因此本批不把入口位置、面板尺寸、真实
深度图媒体或后端任务状态写成原站事实。

## Read Order

1. [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)：当前 HTML/bundle 字符串和
   历史研究中已确认的深度动作捕捉证据边界。
2. [`PLAN.md`](PLAN.md)：缺口排序、clone-only 决策和验收标准。
3. [`DEPTH_MOTION_WORKFLOW.spec.md`](DEPTH_MOTION_WORKFLOW.spec.md)：组件、
   参数、校验、graph handoff 和稳定选择器。
4. [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：本批截图台账；识图前
   先读它，避免重复识别。
5. [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：实施、回归、门禁和接力记录。

## Scope

- ready video 上的“深度动作捕捉”入口；
- 深度信息用途说明；
- 清晰度选择和源视频时长约束反馈；
- 确认提取、短暂忙状态和可观察错误状态；
- 一个 source-linked pending reference node；
- request-shaped metadata、direct edge、重复输出避让和 atomic history；
- 桌面/移动端自然裁切、稳定 selector 和专项 Playwright。

## Boundary

本批不实现真实深度图提取、视频解码、上传、任务 ID、计费、轮询或后端
资源替换。`{maxMin}`、`{maxSec}` 等未取得具体值的源站占位符不擅自填成
固定产品限制；clone 测试态只使用本地可审查 fixture，并显式标注为测试设施。
