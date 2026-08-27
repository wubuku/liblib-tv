# Batch 67 计划：Director Project Document V1

> 状态：`COMPLETE`。
>
> 日期：2026-08-27。
>
> 风险等级：中。实现纯数据边界和 verifier，不接 storage、不迁移 Director UI
> command，不修改两个 submodule。

## 1. 背景与决策

Batch 66 的静态审计确认，Director 当前有丰富的 R3F、对象树、Inspector、typed
timeline、姿态、运动路径、预设运镜、视频导出和手机虚拟运镜能力，但 authoring
状态仍由单例 `directorStore` 持有：

- `openSession(sourceNodeId)` 只更新 source ID，scene/objects/timeline/captures
  会跨 node 保留；
- `timeline.currentTime`、播放采样和 authored `objects` 当前存在运行时耦合；
- capture data URL、selection、panel、phone recorder 和 graph return 不适合作为
  portable project；
- 没有 schema version、严格 decode、invalid/future/reference corpus 或 zero-partial
  contract。

本批选择 `STORY-I01` 的第一代码 slice：先建立独立 document codec，再决定后续
project registry 和 store migration。这样可以尽早验证字段边界，同时避免把整个
3,800 行 store 一次性重写。

## 2. 价值排序

| 工作包 | 用户价值 | 风险降低 | 本批决策 |
|---|---:|---:|---|
| V1 portable authored document | 5 | 5 | 实施 |
| strict decode / normalize | 5 | 5 | 实施 |
| deterministic round-trip | 4 | 5 | 实施 |
| invalid/future/reference corpus | 5 | 5 | 实施 |
| current state snapshot adapter | 4 | 4 | 实施，显式输入类型 |
| project registry/open-switch persistence | 5 | 5 | 延后到 codec 稳定 |
| Director command/history/delete | 5 | 5 | 延后到下一批 |
| real mesh/panorama/multi-camera | 4 | 4 | 延后 |
| LibTV source-exact UI calibration | 4 | 2 | 没有新 source evidence 时不做 |

## 3. V1 文档形状

顶层字段白名单：

```text
schemaVersion
projectId
owner
scene
objects
groups
activeCameraId
timeline
outputPreferences
resourceRefs
captureDescriptors
```

owner 至少包含：

```text
route: "libtv"
canvasId: string
sourceNodeId: string
```

document 只保存 authored semantic state：

- scene 名称、颜色和 ground/grid；
- object identity、kind、primitive、颜色、可见/锁定、transform；
- character rig；
- camera 参数和 relation；
- group identity、成员和 crowd；
- active camera identity；
- timeline duration、loop、autoKeyframe、typed tracks 和 motion paths；
- output aspect ratio；
- stable resource references；
- 不包含媒体 bytes 的 capture descriptors。

## 4. Strictness Contract

`decodeDirectorProjectDocument(input: unknown)` 必须：

1. 只接受 object，不接受 `null`、array 或 primitive；
2. 严格检查每一层的字段白名单，未知字段直接 reject；
3. 只接受 `schemaVersion === 1`，未来版本返回明确错误；
4. 检查非空 ID、ID 唯一性、finite number、tuple 长度和 tuple finite；
5. 检查 object/group/track/path/keyframe/camera 之间的引用闭包；
6. 检查 camera object 才能有 camera payload，character 才能有 rig；
7. 检查 `activeCameraId` 指向 camera object；
8. 检查 track kind 与 object/group 关系、motion path 与 track/object 关系；
9. 检查所有捕获 descriptor 和 resource ref 的 ID 唯一性；
10. 失败时返回零 partial：不能返回看似成功的局部 document。

normalize 必须创建新的深层对象和稳定数组排序/字段形状；不得修改输入对象。
encode 只接受已经通过 normalize 的 V1 document，并输出 JSON-safe value/string。

## 5. 当前 store adapter 边界

adapter 的输入使用显式 `DirectorProjectSnapshotInput`，不得为了读取 private
`DirectorState` 而导出整个 store state。adapter 必须：

- 接受 caller 提供的 `projectId` 和 owner；
- 复制 scene、objects、groups、active camera、timeline semantic fields；
- 将 `DirectorCapture[]` 转为没有 `dataUrl` 的 capture descriptors；
- 接受显式 `resourceRefs`，默认空数组；
- 将 current sampled `objects` 视为 baseline snapshot，并在文档中注明这是过渡
  语义，不声称已经解决 authored/runtime 分离；
- 排除 selection、playback、UI、phone runtime 和 graph projection。

本批不在 `setTimelineTime` / `advanceTimeline` 中改写 store 语义。若 verifier 暴露
sampled values 被错误当作 authored document 的问题，只记录为下一批 blocker。

## 6. 实施顺序

### Slice A：计划与边界 checkpoint

- 创建本目录四份文档；
- 记录不重做截图识别的理由；
- 运行 `docs:check` 与 `git diff --check`；
- commit/push 保护上下文。

### Slice B：纯类型与 codec

- 新增 `src/lib/directorProjectDocument.ts`；
- 使用 `import type` 复用 Director 类型；
- 实现类型、创建、normalize、strict decode、encode 和 snapshot adapter；
- 不使用 `any`，不引入运行时循环依赖。

### Slice C：contract verifier

- 新增 `scripts/verify-liblib-batch67.py`；
- 以 Node/TypeScript 可执行的方式验证 codec，或使用临时编译产物；
- 覆盖 valid round-trip、malformed、future、unknown、duplicate、dangling、
  non-finite、zero-partial 和 excluded runtime fields；
- verifier 不启动 browser，不生成截图，不修改 localStorage 或 graph。

### Slice D：治理同步与收口

- 更新 `LIBTV-VR-024` current manifest；
- 更新 fixture catalog、verification ledger、traceability、decision register、
  Big Picture、Agent Task Map 和 component coverage；
- 更新本目录 `IMPLEMENTATION.md`；
- 运行 docs/typecheck/check 与专项 verifier；
- commit/push 后确认工作区干净。

## 7. 验收标准

代码：

- [ ] `DirectorProjectDocumentV1` 有封闭的顶层和嵌套字段；
- [ ] valid fixture 可以 normalize -> encode -> decode -> stable encode；
- [ ] malformed/future/unknown/duplicate/dangling/non-finite 输入全部 reject；
- [ ] reject 不返回 partial document；
- [ ] document 不含 data URL、selection、runtime、UI 或 Three.js 引用；
- [ ] snapshot adapter 不修改输入 state；
- [ ] `npm run typecheck` 和 `npm run check` 通过。

文档：

- [ ] 新模块、verifier、fixture 和稳定合同可从 Hub 发现；
- [ ] `IMPLEMENTATION.md` 记录真实命令、结果、warning 和未完成项；
- [ ] 历史 verifier pass 不被升级为当前全量 pass；
- [ ] 截图识别成本记录保持零重复，除非出现新的视觉问题。

## 8. 停止条件

以下任一情况出现时，本批不继续扩展到 registry/history/asset：

- V1 字段需要猜测 LibTV source persistence 语义；
- 需要移动 submodule pointer；
- 需要将 `File`、`Blob`、object URL 或 Three.js runtime 写进 document；
- codec 只能通过 cast 或 `any` 绕过 strict validation；
- current verifier 无法区分 document failure 与 Director runtime failure；
- 其他开发者代码 WIP 与本批文件冲突且无法在不覆盖的情况下继续。

## 9. 当前进度

| 工作项 | 状态 | 记录 |
|---|---|---|
| 计划、边界、截图成本 checkpoint | `DONE` | `e56f2e6` |
| V1 schema / strict codec / snapshot adapter | `DONE` | `src/lib/directorProjectDocument.ts` |
| valid + invalid/future/reference corpus | `DONE` | `scripts/verify-liblib-batch67.mjs` |
| Batch 67 Python verifier entry | `DONE` | `scripts/verify-liblib-batch67.py` |
| focused typecheck/lint/verifier | `PASS` | 17 个 rejection case + round-trip/isolation/order |
| 稳定索引与治理台账 | `DONE` | Hub、authority、fixture、manifest、traceability、coverage 已同步 |
| full `npm run check` 与 Batch 59 smoke | `PASS` | 9 条既有 lint warning；typecheck/build/smoke 通过 |

## 10. 收口

Batch 67 按既定边界完成，没有接入 registry、storage、history/delete，也没有移动
Open Canvas 或 StoryAI submodule。下一批应实施 `DIR-PROJECT-I02` 的 owner registry
与 session lifecycle，继续使用本批 document 作为 project payload。
