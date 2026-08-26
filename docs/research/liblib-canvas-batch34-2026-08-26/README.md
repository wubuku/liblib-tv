# Batch 34：导演台既有复刻代码考古与可借鉴 UX

> 状态：研究与验证已完成；本批先研究 `storyai-3d-director-desk`，再决定
> LibTV 画布原型中哪些导演台体验值得复刻。

用户指定的研究源：

```text
https://github.com/jiguang132/storyai-3d-director-desk.git
```

本批的研究对象是一次已有的 LibTV 导演台复刻/实现样本。公开 README 使用
通用的“3D 导演台”描述，但固定源码从初始公开提交开始就包含
`LibTV-style procedural body types`、`node_director_*` 会话、画布全景输入和
截图回流协议。它不是 LibTV 原站源码，仍须把上游实现与原站事实分开。

## Read Order

1. [`PLAN.md`](PLAN.md)：目标、价值排序、证据纪律和验收标准。
2. [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)：远程页面事实、固定 commit、许可证
   和实际构建/测试结果。
3. [`LIBTV_DIRECTOR_EVIDENCE.md`](LIBTV_DIRECTOR_EVIDENCE.md)：原站导演台、
   动画时间轴、运动路径和输出回画布的当前证据。
4. [`CODE_ARCHAEOLOGY.md`](CODE_ARCHAEOLOGY.md)：固定子模块版本后的目录、依赖、
   组件、状态和数据流。
5. [`UPSTREAM_SCREENSHOT_ANALYSIS.md`](UPSTREAM_SCREENSHOT_ANALYSIS.md)：七张
   上游截图的一次性识图台账。
6. [`REPLICATION_REFERENCE_MATRIX.md`](REPLICATION_REFERENCE_MATRIX.md)：原站事实、
   既有复刻和当前 clone 决策的三方对照。
7. [`BORROWABLE_UX.md`](BORROWABLE_UX.md)：面向 LibTV 画布的可借鉴交互。
8. [`PORTABILITY_MATRIX.md`](PORTABILITY_MATRIX.md)：上游能力到当前架构的适配成本
   和不可直接移植边界。
9. [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：研究实施、验证、提交和中断接力记录。

## Scope

- 将上游仓库作为 `research/upstream/storyai-3d-director-desk` git submodule
  引入并固定可复现版本；
- 读取许可证、README、构建入口、目录、依赖和核心源码；
- 梳理场景、角色、群演、模型、机位、灯光、全景、镜头、截图和工程持久化；
- 评估 3D 视窗、对象树、属性面板、镜头管理和快捷操作对 LibTV 的借鉴价值；
- 对照当前 LibTV 的时间轴、运动路径、动画导出和手机运镜能力；
- 形成以既有 R3F 复刻为实现基础的下一批计划，但本批不修改产品运行时代码。

## Boundary

本批不声称：

- 上游项目的每一个功能都适合接入 React Flow 画布；
- 上游项目已经覆盖当前 LibTV 的完整导演台；
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
- Replication-classification correction `ca1c9b0` is pushed to `origin/master`.
- The implementation recommendation is now to use the existing R3F replication
  as the static 3D desk baseline, then source-calibrate it and add the missing
  LibTV timeline, motion-path and animation-return layers.
