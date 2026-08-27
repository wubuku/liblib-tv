# Batch 66 Director Reliability Evidence Matrix

> 状态：`CURRENT_EVIDENCE_BOUNDARY`。
>
> 日期：2026-08-27。
>
> 用途：让后续 agent 能区分“看到的事实”和“建议采用的工程合同”。

## 1. Clone 静态事实

| ID | 级别 | 主张 | 证据 | 不可推出 |
|---|---|---|---|---|
| `B66-CLONE-001` | `CLONE_STATIC_FACT` | Director store 是单个全局 Zustand instance | [`directorStore.ts`](../../../src/store/directorStore.ts) | 所有 Director node 共享项目是产品决策 |
| `B66-CLONE-002` | `CLONE_STATIC_FACT` | `openSession` 只替换 `sourceNodeId`，保留 scene、objects、groups、timeline、captures 和 local library | `directorStore.ts` 的 `openSession` | reopen 是按 node 正确恢复 |
| `B66-CLONE-003` | `CLONE_STATIC_FACT` | store 声明 19 个状态字段和 85 个 action | `DirectorState` interface | action 数量等于功能质量 |
| `B66-CLONE-004` | `CLONE_STATIC_FACT` | 没有 project ID、schema version、owner generation、strict decoder 或 migration | `directorStore.ts` 全文件检索 | refresh/duplicate/import 可以可靠工作 |
| `B66-CLONE-005` | `CLONE_STATIC_FACT` | `uiStore` 单独持有 Director 的 canvas/node surface owner | [`uiStore.ts`](../../../src/store/uiStore.ts) | authoring document 也按该 owner 隔离 |
| `B66-CLONE-006` | `CLONE_STATIC_FACT` | page reconciliation 会在切 canvas 或 source node 消失时关闭 Director surface | [`page.tsx`](../../../src/app/page.tsx) | close 同时 flush/cancel/delete project/resource |
| `B66-CLONE-007` | `CLONE_STATIC_FACT` | capture/export graph action 在调用时读取 `canvasStore.activeCanvasId` | [`canvasStore.ts`](../../../src/store/canvasStore.ts) | async result 拥有 immutable destination |
| `B66-CLONE-008` | `CLONE_STATIC_FACT` | screenshot/video result 各自给普通 graph push 一步 history | `createDirectorCapture`、`createDirectorAnimationExport` | Director 内部已有 domain history |
| `B66-CLONE-009` | `CLONE_STATIC_FACT` | timeline seek/playback 使用 sampled timeline 值重写 `objects` | `setTimelineTime`、`advanceTimeline`、`applyTimelineAtTime` | `objects` 是纯 authored baseline |
| `B66-CLONE-010` | `CLONE_STATIC_FACT` | 当前没有 Director undo、redo、copy/paste、通用 object delete 或 camera delete action | `DirectorState` 与 components 检索 | 背景 Ctrl/Cmd+Z guard 等于 Director undo |
| `B66-CLONE-011` | `CLONE_STATIC_FACT` | object TransformControls mouse-up 会执行 9 次字段更新和一次 keyframe record | [`DirectorViewport.tsx`](../../../src/components/director/DirectorViewport.tsx) | 一个 drag 已是一个 history entry |
| `B66-CLONE-012` | `CLONE_STATIC_FACT` | Inspector number、pose slider和 curve handle 在 change/pointermove 阶段直接 mutation | [`DirectorInspector.tsx`](../../../src/components/director/DirectorInspector.tsx)、[`DirectorCurveEditor.tsx`](../../../src/components/director/DirectorCurveEditor.tsx) | naive snapshot history 不会爆栈 |
| `B66-CLONE-013` | `CLONE_STATIC_FACT` | free path draft 每个 pointer event 更新 store，finish 才生成正式 path | `DirectorViewport.tsx`、`directorStore.ts` | draft 应进入 portable document/history |
| `B66-CLONE-014` | `CLONE_STATIC_FACT` | local asset 删除会删实例、tracks、paths和部分 selection | `removeLocalModelLibraryItem` | camera relation、resource lease 和全部引用已修复 |
| `B66-CLONE-015` | `CLONE_STATIC_FACT` | track 删除会删绑定 path，path 删除会 detach track，anchor 删除保留至少 2 点 | timeline/path actions | 已有通用 reference-aware delete planner |
| `B66-CLONE-016` | `CLONE_STATIC_FACT` | local model catalog 使用单一全局 localStorage key并保存 data URL | `DIRECTOR_LOCAL_MODEL_LIBRARY_STORAGE_KEY` | 它是 durable、quota-safe、按 project 隔离的 asset store |
| `B66-CLONE-017` | `CLONE_STATIC_FACT` | capture 记录 `cameraId` 与 `sentNodeId`，phone state 记录 imported camera/track IDs | `DirectorCapture`、`DirectorPhoneVcamState` | 删除 camera/track/result 时引用会自动修复 |
| `B66-CLONE-018` | `CLONE_STATIC_FACT` | 动态 object/group/track/path/keyframe ID 多处依赖 `Date.now()` | `directorStore.ts` | import/duplicate/fixture 下不会碰撞 |

## 2. 固定 StoryAI 上游事实

| ID | 级别 | 主张 | 证据 | 不可推出 |
|---|---|---|---|---|
| `B66-UP-001` | `UPSTREAM_FACT` | 上游有 `DirectorProject.version = 1`，分开 scene/assets/objects/cameras | [`directorProject.ts`](../../../research/upstream/storyai-3d-director-desk/src/editor/schema/directorProject.ts) | 当前 clone 应照抄 schema |
| `B66-UP-002` | `UPSTREAM_FACT` | 上游可按 scope ID 使用不同 localStorage key 打开 scene | [`directorStore.ts`](../../../research/upstream/storyai-3d-director-desk/src/editor/store/directorStore.ts) | localStorage 是当前 clone 最终 persistence |
| `B66-UP-003` | `UPSTREAM_FACT` | 上游有 `commitMutation`、undo batch、80-entry undo stack | 同上 | 上游已支持 redo 或完全正确的 gesture semantics |
| `B66-UP-004` | `UPSTREAM_FACT` | 上游 copy/paste 会 remap对象/相机并处理 target reference | 同上 | 它覆盖当前 timeline/group/path/phone 引用 |
| `B66-UP-005` | `UPSTREAM_FACT` | 上游删除 asset/object 时修复 camera target、linked camera、active camera 与 asset refs | 同上 | 该 delete closure 可直接复制到 clone |
| `B66-UP-006` | `UPSTREAM_FACT` | 上游 persistence snapshot 包含 UI state | `extractPersistedDirectorState` | UI state 应进入 portable document |
| `B66-UP-007` | `UPSTREAM_FACT` | 上游 shape guard 只检查少量顶层字段，JSON import 使用 cast | `isDirectorProjectShape`、`importProjectJson.ts` | 上游 import 是 strict decode |
| `B66-UP-008` | `UPSTREAM_FACT` | 上游把 local model/data URL 写浏览器 storage，并吞掉 quota error | persistence helpers | 当前 clone 应复制相同资源策略 |
| `B66-UP-009` | `UPSTREAM_FACT` | 上游有 undo 但没有 redo action | `DirectorActions`、store implementation | 上游 history 是完整目标状态 |

## 3. 历史验证事实

| ID | 级别 | 主张 | 证据 | 不可推出 |
|---|---|---|---|---|
| `B66-HIST-001` | `HISTORICAL_RECORDED_PASS` | Batch 35-50、59 共 17 个 Director verifier 有历史实现记录 | [`VERIFICATION_LEDGER.md`](../VERIFICATION_LEDGER.md)、`scripts/verify-liblib-batch*.py` | 17 个脚本在当前 HEAD 全部通过 |
| `B66-HIST-002` | `HISTORICAL_RECORDED_PASS` | 历史 verifier 覆盖 workspace、timeline、path、export、phone、pose、camera、group、capture、asset和 responsive | 各 batch `IMPLEMENTATION.md` 与 verifier | 已覆盖 project/session/history/delete authority |
| `B66-HIST-003` | `HISTORICAL_RECORDED_PASS` | 多数 verifier 会覆盖 tracked historical screenshots | 17 个脚本中的 screenshot path | 可无副作用并行运行 |
| `B66-HIST-004` | `HISTORICAL_RECORDED_PASS` | Batch 40 执行真实 MediaRecorder export，Batch 48 改 localStorage，Batch 59 写 runtime audit | 对应 verifier | 三者适合作为每次低成本 smoke |
| `B66-CURRENT-001` | `CURRENT_CLONE_RECORDED_PASS` | 2026-08-27 在 fresh Next dev server、`localhost:3001` 上重跑 Batch 59，desktop/mobile WebGL、asset search/preview/add、graph isolation、bounds 和 diagnostics 通过 | [`LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md`](../LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md)、Batch 59 runtime audit | 其余 16 个脚本当前 HEAD 全部通过，或 project/history/delete authority 已实现 |
| `B66-ENV-001` | `ENVIRONMENT_FACT` | 同一 dev server 使用 `127.0.0.1:3001` 时 Next 16 dev-origin policy 阻止客户端资源，入口可见但 click 未生效 | Next dev log 与失败 traceback | Director 产品入口本身回归 |

## 4. 本批建议

| ID | 级别 | 建议 | 支撑 | 解除/验收 |
|---|---|---|---|---|
| `B66-REC-001` | `RECOMMENDATION` | 建立 clone-owned `DirectorProjectDocumentV1` | `B66-CLONE-001..004/009`、`B66-UP-001` | strict decode/migration/round-trip tests |
| `B66-REC-002` | `RECOMMENDATION` | owner 至少含 route/canvas/source/project/generation | `B66-CLONE-005..007`、Open Canvas owner/convergence研究 | open/switch/close/delete/duplicate fixture |
| `B66-REC-003` | `RECOMMENDATION` | authored objects 与 timeline sampled projection 分离 | `B66-CLONE-009` | seek/playback 后 project snapshot不漂移 |
| `B66-REC-004` | `RECOMMENDATION` | project/session/runtime/resource 四层分开 | `B66-CLONE-002/009/013/016`、`B66-UP-006/008` | schema 字段归属表和 serializer allowlist |
| `B66-REC-005` | `RECOMMENDATION` | command 返回 committed/noop/rejected/stale 与 stable reason | `B66-CLONE-010..015`、Open Canvas transaction研究 | pure command tests |
| `B66-REC-006` | `RECOMMENDATION` | one completed gesture -> one history entry；Director history有 past/future | `B66-CLONE-011..013`、`B66-UP-003/009` | drag/input/slider/curve/path verifier |
| `B66-REC-007` | `RECOMMENDATION` | object/camera delete 先生成 full reference-repair plan再一次 commit | `B66-CLONE-014/015/017`、`B66-UP-004/005` | integrity checker + delete matrix tests |
| `B66-REC-008` | `RECOMMENDATION` | graph result history 与 Director history保持独立 | `B66-CLONE-008` | undo route和graph count assertions |
| `B66-REC-009` | `RECOMMENDATION` | async result commit 比较 immutable owner/generation/source existence | `B66-CLONE-006/007` | canvas switch/delete during pending fixture |
| `B66-REC-010` | `RECOMMENDATION` | 先建 current verifier manifest，再把历史脚本升级或降级 | `B66-HIST-001..004` | current smoke/full入口和artifact cleanup |
| `B66-REC-011` | `RECOMMENDATION` | 第一代码 slice只实现 schema/owner registry，不同时实现 history/delete | audit blast radius | focused unit + one runtime smoke |

## 5. 当前未知

| ID | 级别 | 问题 | 解除条件 |
|---|---|---|---|
| `B66-UNK-001` | `UNKNOWN` | LibTV 原站 Director 是否按 canvas/node/project 持久化 | authenticated source UI/bundle evidence |
| `B66-UNK-002` | `UNKNOWN` | LibTV 原站 undo/redo 覆盖哪些 Director command | authenticated shortcut/control/runtime evidence |
| `B66-UNK-003` | `UNKNOWN` | 删除最后一个 camera 的产品语义 | source evidence 或明确 clone product decision |
| `B66-UNK-004` | `UNKNOWN` | source node 删除后 Director project 应 cascade、tombstone还是保留 | source/product decision |
| `B66-UNK-005` | `UNKNOWN` | capture/export graph result 与 Director project 的 durable 双向关系 | source/product/resource evidence |
| `B66-UNK-006` | `UNKNOWN` | project persistence 最终使用 localStorage、IndexedDB还是 backend | prototype scope与产品决定 |
| `B66-UNK-007` | `UNKNOWN` | exact LibTV Director shell、timeline、asset和camera UI/UX | 新的 authenticated source fixture |

## 6. 使用规则

后续文档和代码评审引用本矩阵时：

1. 不得把 `UPSTREAM_FACT` 改写成 `LIBTV_SOURCE_FACT`；
2. 不得把 `HISTORICAL_RECORDED_PASS` 改写成 current pass；
3. `RECOMMENDATION` 进入代码前必须有独立 batch、fixture 和 verifier；
4. 新 source evidence 只能新增 dated claim，不静默覆盖本批未知项；
5. 任何 current verifier 运行都必须记录 artifact cleanup 和工作区前后状态。
