# Batch 69 实施与验证记录

> 状态：`COMPLETE / AUTHORED_RUNTIME_FOCUSED_PASS`。
>
> 日期：2026-08-27。
>
> 代码 checkpoint：`985e33a`；文档与 verifier 收口提交见本仓库后续 git log。

## 1. 本批决策

Batch 68 已解决 Director 按 `route + canvasId + sourceNodeId` 的 project/session
隔离，但 snapshot 仍读取混合的 `state.objects`。本批采用最小双层模型：

```text
authoredObjects
  = DirectorProjectDocumentV1 的 portable authored baseline

objects
  = derive(authoredObjects, timeline, motionPaths, currentTime, groups)
  = 当前 R3F / Inspector 可见 runtime projection
```

`objects` 保留为兼容 selector，不改名为 `runtimeObjects`，避免破坏已有 Director
组件和历史 verifier。StoryAI/Open Canvas 只提供状态分层的工程启发，不被当作
LibTV source-exact 证据。

## 2. 代码实施

`src/store/directorStore.ts` 完成以下迁移：

- state 初始化、project restore 和 project snapshot 增加 `authoredObjects`；
- snapshot/close/switch 只把 authored objects 写入 V1 document；
- `setTimelineTime`、播放、keyframe selection、speed curve、camera preset 和
  motion path 全部从 authored baseline 重新派生 runtime；
- character pose、Inspector transform/camera、group transform 写 authored layer；
  auto-keyframe 开启且已有对应 track 时同步当前时间的 keyframe；
- crowd/model-library add、local model removal 和 phone take import 同步维护
  authored/runtime 两层；
- phone live pose/elevation/recording preview 继续只更新 runtime objects；
- restore 先恢复 authored document，再以存储的 timeline 语义在当前 runtime 中派生。

这次没有扩大到 Director command/history、reference-aware delete、async result
freshness、browser persistence、真实资源加载或 LibTV source-exact Director UI。

## 3. Verifier

新增：

```text
scripts/verify-liblib-batch69.mjs
scripts/verify-liblib-batch69.py
docs/research/liblib-canvas-batch69-2026-08-27/runtime-audit.json
```

纯 verifier 静态确认：

- `authoredObjects` 可发现、初始化和用于 snapshot；
- runtime projection helper 存在；
- timeline/path projection 不再以 `state.objects` 作为采样输入；
- 两个 phone preview runtime-only writer 仍存在。

Playwright verifier 使用 `DIRECT_STORE_DRIVEN` Director fixture，在新页面中创建两个
Director source nodes，并覆盖：

| 场景 | 结果 |
|---|---|
| 多次 seek、keyframe selection、speed curve、motion path、camera preset | `PASS` |
| playback/advance/stop 后 authored fingerprint 稳定 | `PASS` |
| object transform、camera FOV/target、pose control authoring | `PASS` |
| close/reopen 后 authored baseline 恢复 | `PASS` |
| V1 runtime reset：reopen playhead 回到 `0` | `PASS` |
| owner A/B project 隔离 | `PASS` |
| 普通 graph/history 不变 | `PASS` |
| console/page/request error | `0` |
| screenshot artifact | `0` |

运行命令：

```bash
node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON \
  --experimental-strip-types scripts/verify-liblib-batch69.mjs
LIBLIB_BASE_URL=http://localhost:3001 python3 scripts/verify-liblib-batch69.py
```

最近一次结果已写入 [`runtime-audit.json`](runtime-audit.json)。浏览器使用
`localhost:3001`，因为 Next 16.2.1 在当前配置下对 `127.0.0.1` 的开发资源有
origin 限制；本批没有截图识别，也没有修改 `docs/design-references/`。

## 4. 最终回归与门禁

2026-08-27 收口运行：

| Gate | 结果 |
|---|---|
| `python3 scripts/verify-liblib-batch67.py` | `PASS`：V1 codec 17 个 rejection cases 与 round-trip |
| `LIBLIB_BASE_URL=http://localhost:3001 python3 scripts/verify-liblib-batch68.py` | `PASS`：owner/session/generation、A/B/cross-canvas 与 graph isolation |
| `LIBLIB_BASE_URL=http://localhost:3001 python3 scripts/verify-liblib-batch69.py` | `PASS`：authored/runtime、authoring restore、owner/graph isolation；zero errors/screenshots |
| `LIBLIB_BASE_URL=http://localhost:3001 python3 scripts/verify-liblib-batch59.py` | `PASS`：asset library、scene insertion、Inspector/WebGL 与 mobile bounds |
| `npm run docs:check` | `PASS`：555 个 Markdown 文件、3283 个本地目标 |
| `npm run check` | `PASS`：lint、typecheck、Next 16.2.1 production build；仅既有 9 条 lint warning |

`runtime-audit.json` 不记录 timestamp-derived project ID，重复运行不会因临时
identity 产生无意义 diff。

## 5. 实施历史

| 节点 | 结果 |
|---|---|
| `09ffdf1` | Batch 69 authored/runtime 计划 checkpoint |
| `985e33a` | `directorStore` 双层 authority 核心代码 checkpoint，已 push |
| 2026-08-27 | pure verifier 首次通过 |
| 2026-08-27 | browser 首次失败：错误断言 restore 保留 currentTime |
| 2026-08-27 | 修正为 V1 既定 time-zero restore 后 browser verifier 通过 |
| 2026-08-27 | Batch 67/68/69/59、docs check 与 `npm run check` 全部通过 |
| 收口 | 文档、manifest、fixtures、coverage、traceability 和 verifier 提交见 git log |

## 6. 仍然开放的后续合同

本批完成的是 `LIBTV-VR-024` 的 authored/runtime slice，不是 Director 完整成熟度
结论。后续优先级仍是：

1. command result、gesture transaction 和 Director 独立 undo/redo；
2. object/group/camera/path 的 reference-aware delete 与 zero-partial repair；
3. async capture/export 的 owner + generation freshness；
4. durable project persistence 与真实 mesh/panorama resource lifecycle；
5. 重新取得 LibTV authenticated Director 证据后校准 source-exact UI/UX。
