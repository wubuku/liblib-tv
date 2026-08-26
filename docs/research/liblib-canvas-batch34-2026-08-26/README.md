# Batch 34：导演台上游代码考古与可借鉴 UX

> 状态：研究与验证已完成；本批先研究 `storyai-3d-director-desk`，再决定
> LibTV 画布原型中哪些导演台体验值得复刻。

用户指定的研究源：

```text
https://github.com/jiguang132/storyai-3d-director-desk.git
```

本批的研究对象是一个独立的浏览器 3D 导演台 demo。它不是 LibTV 原站，
也不是当前 clone 的既有代码。所有结论都必须标注来源类别，不能把上游
README 或源码中的能力直接写成 LibTV 原站事实。

## Read Order

1. [`PLAN.md`](PLAN.md)：目标、价值排序、证据纪律和验收标准。
2. [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)：远程页面事实、固定 commit、许可证
   和实际构建/测试结果。
3. [`CODE_ARCHAEOLOGY.md`](CODE_ARCHAEOLOGY.md)：固定子模块版本后的目录、依赖、
   组件、状态和数据流。
4. [`BORROWABLE_UX.md`](BORROWABLE_UX.md)：面向 LibTV 画布的可借鉴交互。
5. [`PORTABILITY_MATRIX.md`](PORTABILITY_MATRIX.md)：上游能力到当前架构的适配成本
   和不可直接移植边界。
6. [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：研究实施、验证、提交和中断接力记录。

## Scope

- 将上游仓库作为 `research/upstream/storyai-3d-director-desk` git submodule
  引入并固定可复现版本；
- 读取许可证、README、构建入口、目录、依赖和核心源码；
- 梳理场景、角色、群演、模型、机位、灯光、全景、镜头、截图和工程持久化；
- 评估 3D 视窗、对象树、属性面板、镜头管理和快捷操作对 LibTV 的借鉴价值；
- 形成下一批实现计划，但本批不把上游源码复制进 `src/`。

## Boundary

本批不声称：

- LibTV 原站已经存在完整 3D 导演台；
- 上游项目的每一个功能都适合接入 React Flow 画布；
- 上游内置模型、贴图和示例资源具有可复用或可再分发许可；
- 仅凭 README 就能确认所有运行时交互。

## Verified Snapshot

- Submodule fixed at `8c8bd361790be4d37158a7430365e65546e358fe`.
- `npm ci` passed and the submodule working tree is clean.
- `npm run build` passed with external model-thumbnail and chunk-size warnings.
- `npm test` passed `304/312`; the 8 failures are recorded in
  [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md).
- Parent `npm run docs:check`, `git diff --check` and `npm run check` passed.
- Batch 34 research commit `e1d20ef` is pushed to `origin/master`.
- The implementation recommendation remains a LibTV-specific 2D director
  workspace first: shot tree, selection-driven inspector, framed preview and
  capture history. Full 3D staging is a separate architecture decision.
