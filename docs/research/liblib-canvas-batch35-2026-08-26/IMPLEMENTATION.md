# Batch 35 Implementation Log

> 状态：已完成、验证并形成可接力记录。

## Planned Protection Points

1. 计划、规格、selectors 与验收矩阵；
2. 依赖、director schema/store、入口和 R3F 工作区；
3. helper-free capture、React Flow return transaction 和 undo/redo；
4. Playwright、WebGL 像素检查、截图台账和跨批回归；
5. 实施收口、接力说明和下一批计划。

## Pre-Implementation Audit

- 当前 `ScriptExecutionNode` 是无行为脚本步骤卡，不符合已确认的导演台产品边界。
- `AssetManagerPanel` 将该节点标为“脚本生成器”，属于同一处错误脑补。
- 当前页面是 Client Component，符合 Next.js 16 在 client boundary 内使用
  `next/dynamic(..., { ssr: false })` 的要求。
- React Flow 和 R3F 可在同一路由共存；通过 full-screen island 隔离 pointer、
  renderer 和 state ownership。
- React 19.2.4 与计划安装的 R3F 9 / Drei 10 / Three 0.185 版本范围兼容。
- 现有 22 张历史截图二进制变化不是本批工作，所有提交必须排除。

## Implementation Result

- 安装 `three@0.185.1`、`@react-three/fiber@9.7.0`、
  `@react-three/drei@10.7.8` 和 `@types/three@0.185.4`。
- 新增独立 `directorStore`，保存 scene、objects、selection、active camera、
  view/transform/aspect mode 和 capture records；R3F runtime refs 不进入 store。
- `uiStore.activeDirectorNodeId` 管理 full-screen workspace lifecycle；当前
  React Flow 页面使用 `next/dynamic(..., { ssr: false })` 按需挂载工作区。
- 将原“脚本执行”步骤卡修正为 `3D导演台` 节点、已确认的 3D 构图说明和
  `进入导演台` 命令；Asset Manager 同步修正名称。
- 新增三栏工作区、语义对象树、选择驱动 Inspector、桌面 rails 和移动 drawers。
- 新增真实 R3F scene：程序化角色、咖啡桌、杯子、背景体块、地面、灯光、
  可见 camera rig、OrbitControls 和 TransformControls。
- 新增导演/机位视角、移动/旋转/缩放模式、三种画幅和九宫格。
- 新增 `preserveDrawingBuffer` capture pipeline；按可见画幅裁剪 WebGL bitmap，
  capture 时隐藏 grid、camera rig 和 TransformControls。
- 新增 `canvasStore.createDirectorCapture` 原子事务，将 PNG data URL 回流为
  image node + source edge + typed metadata，并进入现有 undo/redo history。
- `ImageNode` 暴露 director capture stable selectors，便于专项回归。
- 首次浏览器 smoke test 发现节点内 CTA 被 React Flow pointer lifecycle
  拦截；加入 `nodrag nopan nowheel` 和 pointer propagation guard 后，真实点击
  可以稳定打开工作区。
- 第一次 contact-sheet 识图发现 active camera rig 在自己的机位视角中遮挡
  画面；最终实现会在 camera view 隐藏 active rig，并缩小 director view 中
  的机位 authoring model。

## Verification Result

- `npm run typecheck` passed.
- `npm run build` passed.
- 初次 lint 只发现 R3F mutable Three.js camera 与 React immutability rule
  的边界冲突；已使用局部、带原因的 lint exception。重跑 lint 通过，保留
  仓库原有 9 条 warning。
- `python3 scripts/verify-liblib-batch35.py` passed. It covers real pointer entry,
  full-screen geometry, WebGL pixel variance, tree/Inspector synchronization,
  visibility and numeric edits, director/camera view switching, three aspect
  ratios, thirds, helper-free capture, canvas return, atomic undo/redo and
  `390x844` drawers/overflow.
- Final raw capture is `852x479`; visual inspection confirms no grid, gizmo,
  camera rig, frame, thirds or DOM chrome. Details are recorded in
  [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md).
- Cross-batch regression passed for Batch 9, 15, 21, 26, 27, 28, 29, 30,
  31, 32 and 33.
- `npm run check` passed with the repository's existing 9 lint warnings.
- `npm run docs:check` and `git diff --check` passed.

## Commit Protection

- Batch 35 plan protection: `47bc0f4`.
- Batch 35 main implementation protection: `3661cca`.
- Batch 35 verification/finalization: recorded by the next commit containing
  this log, the two browser-found fixes, verifier and screenshots.

## Interruption Handoff

Batch 35 已收口。后续从 Batch 36 的时间轴计划继续，优先建立 typed tracks、
playhead、关键帧、scrub/playback 和 R3F deterministic sampling，再进入运动
路径与动画输出。不要把回归脚本重写的 Batch 9/15/21/26-33 历史截图带入提交。
