# Batch 33 Implementation Log

> 状态：实现、专项浏览器验证、跨批回归、工程门禁和提交推送均已完成。

## Planned Protection Points

1. source evidence、截图台账、缺口排序和 graph spec；
2. store transaction、renderer 和 generation panel handoff；
3. focused Playwright、clone screenshot ledger 和零浏览器错误检查；
4. 跨批回归、工程/文档门禁、最终 handoff 和 commit/push。

## Implementation Result

- 新增 `LongVideoProcessStage`、`LongVideoProcessInput` 和
  `LongVideoProcessMetadata`，将请求形状与 stage metadata 固化在
  `canvasStore` 类型边界中。
- 新增 `canvasStore.createLongVideoProcess`。一次调用创建 12 个节点和
  22 条边，节点按 material / shot / candidate / assembly / final 分层；
  material 与 shot 多对多，shot 进入两批 candidate，candidate 汇聚到
  assembly，再连接 final。
- 新增 `LongVideoProcessNode` renderer，并注册到 LibTV route。候选和最终
  节点保持等待态，局部图片只作为可辨识的 clone preview。
- `VideoGenerationPanel` 长视频提交接入 source video，加入短暂 disabled/
  spinner 状态；`查看过程` 改为画布过程说明，不再显示旧的面板四步图。
- 长视频 request metadata 包括 prompt、model、ratio、resolution、duration、
  audio、credits、reference count、source 和 process ID。
- 重复提交按整批 graph bounds 纵向避让；source selection 保留；一次提交、
  一次 undo/redo 对应整个过程图。

## Verification Result

- `python3 scripts/verify-liblib-batch33.py` 通过。
- 专项覆盖普通模式不建长视频图、`300s / 14700`、过程说明、提交 busy、
  12 节点、22 条边、五类 stage、metadata、等待态、多对多拓扑、重复避让、
  atomic undo/redo、多选隐藏、`390x844` 裁切和零 console/page errors。
- 跨批以下脚本均通过：Batch 9、15、21、26、27、28、29、30、31、32、33。
- 截图识别已写入 [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)，只对
  Batch 33 contact sheet 做一次视觉检查；之后不重复识别同一整图。
- `npm run docs:check` 通过：245 个 Markdown、576 个本地目标。
- `npm run check` 通过：0 error，保留 9 条既有 warning。
- `git diff --check` 通过。

## Commit Protection

计划保护提交：`3fcab38 docs: plan long video process graph batch`。

实现保护提交：本轮收口提交后回填。

## Interruption Handoff

下一批最高优先级是“导演台”UI/UX 复刻。用户已指定开源项目
`https://github.com/jiguang132/storyai-3d-director-desk.git` 作为研究源；
Batch 34 将先以 git submodule 引入，再做许可证、目录、运行入口、领域模型、
3D/画布交互和可复用 UI 的代码考古。不要把开源实现直接当作 LibTV 原站事实，
也不要在未完成证据审计前把它接入当前运行时代码。
