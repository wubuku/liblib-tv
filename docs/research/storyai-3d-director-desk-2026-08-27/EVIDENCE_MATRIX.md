# StoryAI / Director Evidence Matrix

> 目的：为 progress audit 和 roadmap 提供可反查的主张 ID。路径均相对于本目录。

## 1. 上游与 freshness

| ID | 级别 | 主张 | 证据 | 不可推出 |
|---|---|---|---|---|
| `STORY-UP-001` | `UPSTREAM_FACT` | 固定上游是 React 18 + Vite 6 + Three.js/R3F + Zustand 的 3D 导演台 | [`../../../research/upstream/storyai-3d-director-desk/package.json`](../../../research/upstream/storyai-3d-director-desk/package.json)、[`README.md`](../../../research/upstream/storyai-3d-director-desk/README.md) | LibTV 使用相同内部实现 |
| `STORY-UP-002` | `UPSTREAM_FACT` | 三栏 shell、对象树、selection-driven Inspector 和中央 R3F viewport 是上游核心 IA | `src/app/layout/DirectorDeskShell.tsx`、`src/editor/panels/*`、`src/editor/canvas/*` | 上游宽度/CSS 是 LibTV exact geometry |
| `STORY-UP-003` | `UPSTREAM_FACT` | 上游 project schema 包含 scene/assets/objects/cameras/panorama 和 version | `src/editor/schema/directorProject.ts` | 当前 clone 已有等价 schema/migration |
| `STORY-UP-004` | `UPSTREAM_FACT` | 上游 store 有 undo batch、copy/paste、delete、snapshot restore 和 scoped scene | `src/editor/store/directorStore.ts` | 这些行为天然适合直接复制 |
| `STORY-UP-005` | `UPSTREAM_FACT` | 上游有 project JSON、host bridge、capture bridge、local model 和 panorama loader | `src/editor/io/*`、`src/editor/loaders/*` | JSON parser 已严格验证；资源生命周期已生产化 |
| `STORY-UP-006` | `UPSTREAM_FACT` | 上游无 typed timeline、motion path、speed curve、video export 或 phone vcam | 固定源码全目录检索；[`../liblib-canvas-batch37-2026-08-26/SOURCE_EVIDENCE.md`](../liblib-canvas-batch37-2026-08-26/SOURCE_EVIDENCE.md) | LibTV 原站没有这些能力 |
| `STORY-UP-007` | `UPSTREAM_FACT` | 2026-08-27 上游 build 通过，test 为 304/312 | 本轮 `npm run build`、`npm test`；[`../liblib-canvas-batch34-2026-08-26/SOURCE_EVIDENCE.md`](../liblib-canvas-batch34-2026-08-26/SOURCE_EVIDENCE.md) | 上游是全绿参考实现 |
| `STORY-UP-008` | `REMOTE_FRESHNESS_FACT` | 远端 `main`/HEAD 仍是固定 SHA `8c8bd36` | 2026-08-27 `git ls-remote` | 未来不会变化 |

## 2. 当前 clone 静态事实

| ID | 级别 | 主张 | 证据 | 不可推出 |
|---|---|---|---|---|
| `STORY-CLONE-001` | `CLONE_STATIC_FACT` | Director 是 React Flow 入口外的 lazy-loaded 全屏 R3F island | [`../../../src/app/page.tsx`](../../../src/app/page.tsx)、[`../../../src/components/director/DirectorDesk.tsx`](../../../src/components/director/DirectorDesk.tsx) | 它是独立 route/iframe |
| `STORY-CLONE-002` | `CLONE_STATIC_FACT` | Director 有独立 `directorStore`，Three.js runtime refs 不进入 Zustand | [`../../../src/store/directorStore.ts`](../../../src/store/directorStore.ts)、[`../../../docs/ARCHITECTURE.md`](../../ARCHITECTURE.md) | store 已按 canvas/node 隔离 |
| `STORY-CLONE-003` | `CLONE_STATIC_FACT` | 当前实现有对象树、Inspector、viewport、timeline、curve、export 和 phone vcam surfaces | [`DirectorDesk.tsx`](../../../src/components/director/DirectorDesk.tsx) 及同目录组件 | 所有 surface 都 source-exact |
| `STORY-CLONE-004` | `CLONE_STATIC_FACT` | typed track union 覆盖 transform/camera/pose/group | `src/store/directorStore.ts` | 任意属性轨、音轨或完整 NLE |
| `STORY-CLONE-005` | `CLONE_STATIC_FACT` | motion path 覆盖预设、pencil/pen、anchor/handle、path transform 和 speed curve | `directorMotionMath.ts`、`DirectorTimeline.tsx`、`DirectorInspector.tsx` | source-exact path math/geometry |
| `STORY-CLONE-006` | `CLONE_STATIC_FACT` | screenshot 和 video result 通过 canvasStore transaction 回流普通画布 | `DirectorDesk.tsx`、`canvasStore.ts` | 后端上传或持久 media locator |
| `STORY-CLONE-007` | `CLONE_STATIC_FACT` | 资源库和本地模型可生成 serializable proxy object | `directorModelLibrary.ts`、`directorLocalModelImport.ts`、`DirectorViewport.tsx` | 真实 FBX/OBJ mesh 已解析/渲染 |
| `STORY-CLONE-008` | `CLONE_STATIC_FACT` | `openSession` 只更新 `sourceNodeId` 并保留全局 scene/objects/timeline | `directorStore.ts:1314` 起 | 不同 Director node 拥有独立 project |
| `STORY-CLONE-009` | `CLONE_STATIC_FACT` | clone 没有 project schema version/import/export/restore action | `directorStore.ts` 与 `src/components/director/` 全目录检索 | 页面刷新后项目可恢复 |
| `STORY-CLONE-010` | `CLONE_STATIC_FACT` | clone 没有 Director domain undo/redo/copy/paste/object delete action | `DirectorState` action surface 与 Director components 检索 | Batch 50 阻止背景 Ctrl+Z 等于 Director undo |
| `STORY-CLONE-011` | `CLONE_STATIC_FACT` | clone 场景设置只覆盖背景/地面颜色和 ground/grid 显隐 | `DirectorScene`、`DirectorInspector.tsx` | 全景、scene transform、ground height/opacity 已覆盖 |
| `STORY-CLONE-012` | `CLONE_STATIC_FACT` | clone 当前无 add-camera/add-primitive action，默认 fixture 提供单机位 | `DirectorState` action surface、default objects | 多机位 lifecycle 已完成 |
| `STORY-CLONE-013` | `CLONE_STATIC_FACT` | UI owner 记录 canvas/node，但 capture/export action 在执行时读取 active canvas | `uiStore.ts`、`page.tsx`、`canvasStore.ts` | 所有异步结果都有 immutable canvas owner |
| `STORY-CLONE-014` | `HISTORICAL_RECORDED_PASS` | Batch 35-50、59 各自有 focused verifier 和历史记录 | [`../VERIFICATION_LEDGER.md`](../VERIFICATION_LEDGER.md)、`scripts/verify-liblib-batch*.py` | 当前 HEAD 已一次性回归全部 17 个脚本 |
| `STORY-CLONE-015` | `CLONE_STATIC_FACT` | Director 当前约 13,563 行 TypeScript，20 个 component/utility 文件加 store | 2026-08-27 tracked-file inventory | 行数本身等于质量或 source parity |

## 3. 本轮运行事实

| ID | 级别 | 主张 | 2026-08-27 观察 | 边界 |
|---|---|---|---|---|
| `STORY-RUN-001` | `CLONE_RUNTIME_FACT` | 工作区可打开 | `role=dialog`、`aria-modal=true` | localhost prototype |
| `STORY-RUN-002` | `CLONE_RUNTIME_FACT` | WebGL 非空 | `932x656` canvas，`toDataURL` 长度 163,634 | 只证明本次 headless render 非空 |
| `STORY-RUN-003` | `CLONE_RUNTIME_FACT` | 三栏和时间线存在 | tree/viewport/Inspector/timeline 均 visible | desktop 1440x900 |
| `STORY-RUN-004` | `CLONE_RUNTIME_FACT` | 资源库主链可用 | 5 tabs、3 initial cards、1 preview；加入后 objects 5 -> 6 | proxy asset，不是真 mesh |
| `STORY-RUN-005` | `CLONE_RUNTIME_FACT` | 资源加入不改普通 graph | nodes/edges 保持 10/11 | 本次 add-to-scene 动作 |
| `STORY-RUN-006` | `CLONE_RUNTIME_FACT` | side panel collapse 可工作 | workspace collapsed flag 切到 true | 不证明全部 responsive/focus contract |
| `STORY-RUN-007` | `CLONE_RUNTIME_FACT` | 无 console/page error | 仅观察到 Three.Clock、PCFSoftShadowMap 弃用和 WebGL ReadPixels 性能 warning | 不等于完整回归无错误 |

## 4. 主要未知

| ID | 状态 | 问题 | 解除条件 |
|---|---|---|---|
| `STORY-UNK-001` | `UNKNOWN` | 当前 LibTV Director shell 的 exact DOM/CSS/geometry | authenticated、只读、多 viewport 运行证据 |
| `STORY-UNK-002` | `UNKNOWN` | LibTV 的 project persistence、undo 和 multi-shot 语义 | source UI/bundle evidence 或产品决策 |
| `STORY-UNK-003` | `UNKNOWN` | 真实模型/环境资产格式、license、上传和生命周期 | disposable fixture + asset/provider evidence |
| `STORY-UNK-004` | `UNKNOWN` | animation export 的远端编码、上传、恢复和失败语义 | disposable source fixture + 明确动作授权 |
| `STORY-UNK-005` | `UNKNOWN` | phone vcam 的真实 LAN/QR/WebRTC 协议 | 安全环境、协议证据和产品授权 |
