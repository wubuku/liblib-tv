# Open Canvas 上游研究

> 研究对象：[`ZeroLu/open-canvas`](https://github.com/ZeroLu/open-canvas/)
> 及其官网 [`open-canvas.cyberbara.com/zh`](https://open-canvas.cyberbara.com/zh)。
> 本目录只记录研究，不代表已经授权将其能力编码进 LibTV 克隆。

## 研究锚点

| 项目 | 值 |
|---|---|
| 上游远端 | `https://github.com/ZeroLu/open-canvas.git` |
| 分支 | `main` |
| 锁定提交 | `cf3a906bb8c35bb940d3267497e7f394b8f42582` |
| 上游目录 | [`research/upstream/open-canvas`](../../../research/upstream/open-canvas) |
| 引入方式 | git submodule |
| 当前项目分支 | `master` |
| 观察日期 | 2026-08-26 |
| 实施边界 | 研究和报告；等待用户明确授权后才编码 |

## Read Order

1. [`PLAN.md`](PLAN.md)：研究问题、方法、范围和交付物。
2. [`REPORT.md`](REPORT.md)：面向项目决策的完整结论。
3. [`SOURCE_ANALYSIS.md`](SOURCE_ANALYSIS.md)：固定版本的目录、模块和源码证据。
4. [`RUNTIME_AUDIT.md`](RUNTIME_AUDIT.md)：官网落地页和托管应用入口的只读核对。
5. [`EVIDENCE_MATRIX.md`](EVIDENCE_MATRIX.md)：OC claim ID、证据级别、可证明范围和待验证问题。
6. [`IMPLEMENTATION_IMPLICATIONS.md`](IMPLEMENTATION_IMPLICATIONS.md)：与当前 LibTV/FrameOS 克隆的映射、收益、风险和待授权队列。
7. [`ITERATION_LOG.md`](ITERATION_LOG.md)：研究报告版本和维护历史。

## 当前结论摘要

`open-canvas` 的高价值不在于复刻 LibTV 的具体视觉皮肤，而在于它把“可见节点画布”做成了一套可运行、可导入导出、可本地持久化、可替换 provider 的工作流内核。其核心边界如下：

- React Flow 负责空间交互，Zustand 负责画布文档与保存/冲突状态。
- 图模型只允许 `note`、`text`、`image`、`video`、`audio` 五类节点，边经过方向归一化和 DAG 校验。
- 节点执行先解析上游引用，再生成 task descriptor，服务端记录 run，前端对异步任务轮询。
- provider 是 BYOK 适配层：Cyberbara、OpenRouter、Replicate；媒体上传另有 Cyberbara/S3-compatible storage。
- local-first 不是纯浏览器 demo：默认使用文件 JSON，Cloudflare 运行时切换到 KV，并保留 API 路由、revision 和 conflict 语义。
- 官网当前应用入口首先要求配置 provider Key；没有 Key 时仍可读到产品骨架，但不能把“可生成”误判为无需后端配置的能力。

本次研究不修改 `src/`、不修改上游 submodule 内容、不执行生成或上传、不创建官网画布。
