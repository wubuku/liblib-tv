# LibTV Seedance 2.5 画布能力研究

本目录记录 LibTV 近期 Seedance 2.5 相关能力在画布中的呈现，以及本克隆的规划、原站验证和实施历史。

## 阅读顺序

1. [`BACKGROUND.md`](BACKGROUND.md)：外部调研中提炼出的 LibTV 能力背景、共性产品模式和证据边界。
2. [`PLAN.md`](PLAN.md)：实施前的能力清单、缺口、价值排序、范围与验收标准。
3. [`LIVE_AUDIT.md`](LIVE_AUDIT.md)：登录原站后的逐项验证记录和证据等级。
4. [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：实现完成后的文件、状态机、交互与验证记录；其中 2026-08-25 是历史 clone 快照，当前差距以总矩阵和组件合同为准。
5. [`live-audit.json`](live-audit.json) 与 [`live-script-string-evidence.json`](live-script-string-evidence.json)：当前原站结构化数据和静态字符串证据。
6. [`evidence/`](evidence/)：第三方文章中的 LibTV UI 截图，只作为功能线索和视觉证据。
7. [`LIBTV_FEATURE_GAP_MATRIX.md`](LIBTV_FEATURE_GAP_MATRIX.md)：以“LibTV 有什么”为中心的能力呈现、clone 缺口、价值排序和授权闸门总矩阵。
8. [`LIBTV_VERIFICATION_COVERAGE.md`](LIBTV_VERIFICATION_COVERAGE.md)：现有回归脚本对当前源站合同的覆盖、历史断言和授权后测试队列。
9. [`NEXT_RESEARCH_PLAN.md`](NEXT_RESEARCH_PLAN.md)：已批准的研究-only 执行顺序、安全边界、产出和验收标准。
10. [`LIBTV_UI_STATE_HIERARCHY.md`](LIBTV_UI_STATE_HIERARCHY.md)：节点、双浮层、active tool、预览、任务和 graph mutation 的状态层级与转换合同。

同日的当前项目原站复核仍在 [`../liblib-live-2026-08-25/`](../liblib-live-2026-08-25/)；图片节点逐状态审计属于两组研究的交叉证据。

## 证据边界

- 输入文档是第三方调研，不是 LibTV 官方规格。
- 本目录只采用其中关于“LibTV 有什么、界面如何呈现”的内容，不采用其对另一个项目的实现展望。
- 文章陈述与截图观察会在 `LIVE_AUDIT.md` 中分开记录；能在当前登录原站复现的事实优先级最高。
- 30 秒、4 秒片段、最多 5 段、300 秒和积分数字都是采样时产品表现，不写成模型或后端的永久契约。
