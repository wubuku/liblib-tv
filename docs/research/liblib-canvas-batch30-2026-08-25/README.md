# Batch 30: Subject Edit Menu And Smart Matting

> 状态：核心实现与专项 Playwright 已完成，等待跨批回归与工程门禁。

本批纠正 ready-video 顶部工具条中无源站依据的 `画面编辑` 菜单，并复刻
当前线上已有完整闭环证据的 `智能抠像`：

```text
主体消除
├── 主体消除
├── 主体修改
├── 主体替换
└── 智能抠像
        └── source video -> pending matting video
```

## Read Order

1. [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)：当前 bundle 的菜单、校验、
   panel、request 和 graph 事实。
2. [`PLAN.md`](PLAN.md)：本批价值排序、范围和验收标准。
3. [`SMART_MATTING_WORKFLOW.spec.md`](SMART_MATTING_WORKFLOW.spec.md)：
   可实施与可测试的交互、状态和 metadata contract。
4. [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：专项 Playwright 截图
   的一次性识别台账。
5. [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：提交、验证和最终接力记录。

## Scope Boundary

- 本批实现：source-backed 四项菜单、hover 时序、30 秒主体编辑限制、
  智能抠像下方面板、pending video output、direct edge、history。
- 下一批实现：主体消除/修改/替换共用的全屏标注器，以及点选、框选、
  画笔、橡皮、候选对象、描述和替换图流程。
- 本批不声称执行真实视频抠像、算力计价或任务提交。
