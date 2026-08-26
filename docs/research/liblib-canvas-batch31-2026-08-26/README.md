# Batch 31：主体消除、主体修改与主体替换标注工作流

> 状态：计划中。目标是把 Batch 30 留下的三项主体编辑从“15 秒限制反馈”
> 推进到可操作的标注、校验、提交和 pending graph 原型闭环。

本批继续使用当前 LibTV bundle 中已经保存的 `usePictureEditStore` 证据，
不重新识别 Batch 30 contact sheet。重点不是编造真实视频处理，而是把原站
已经确认的编辑器状态机变成开发者和 agents 可重复验证的画布交互：

```text
主体消除 / 修改 / 替换
  -> 选择标注工具
  -> 在视频画面标记主体
  -> 根据模式填写描述或替换图来源
  -> 校验通过
  -> 分析中
  -> pending 主体编辑视频 + source edge
```

## Read Order

1. [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)：Bundle 中已确认的 store、工具、
   mark 字段、模式校验和文案。
2. [`PLAN.md`](PLAN.md)：缺口排序、范围、clone-only 决策和验收标准。
3. [`PICTURE_EDIT_WORKFLOW.spec.md`](PICTURE_EDIT_WORKFLOW.spec.md)：组件、状态、
   标注几何、提交和 metadata contract。
4. [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：本批截图识别台账；先读
   文字记录，再决定是否需要查看新截图。
5. [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：实现历史、专项验证、回归和接力。

## Scope

- 三种主体编辑模式共享一个标注编辑器；
- `点选 / 框选 / 画笔 / 橡皮` 工具；
- normalized mark 几何、选中、移动、框选缩放和画笔轨迹；
- remove / modify / replace 的模式化提交校验；
- modify 的逐标记描述；
- replace 的本地上传/历史图库选择反馈和逐标记绑定；
- reset、撤销/重做、取消和 `Escape`；
- `分析中` 状态与 pending video graph handoff；
- request-shaped metadata、source edge、重复输出避让、atomic undo/redo；
- 专项 Playwright、截图 ledger、跨批回归和工程门禁。

## Boundary

本批不实现真实视频 seek、对象识别、分割 mask、文件上传、历史图库 API、
透明视频、模型任务、计费或轮询。候选名称、替换图入口和输出状态必须标注
为本地 prototype 行为。
