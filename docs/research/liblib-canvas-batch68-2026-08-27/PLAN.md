# Batch 68 计划：Director Owner Registry And Session Lifecycle

> 状态：`PLANNED`。
>
> 日期：2026-08-27。
>
> 风险等级：高。会修改 Director store/session authority 与页面 owner bridge，但不
> 修改两个 submodule，不接 storage，不实现 history/delete。

## 1. 为什么是这一批

Open Canvas 和 StoryAI 的评估结论一致：当前 Director 的可见能力已经足够丰富，
最高价值短板是可靠性，而不是继续加面板。Batch 67 已建立 portable V1 codec，
但当前 `openSession(sourceNodeId)` 仍只替换 source ID：

```text
surface owner = canvasId + sourceNodeId
authoring owner = singleton store + current sourceNodeId
```

这会使 node A 的 scene、objects、timeline 和 captures 在打开 node B 时继续出现。
Batch 68 实施 `DIR-PROJECT-I02`，先关闭这个 P0 串场问题，再进入 authored/runtime
split 和 Director history/delete。

## 2. 采纳与拒绝

| 研究输入 | 本批采纳 | 本批拒绝 |
|---|---|---|
| StoryAI | versioned project、scoped owner、project/runtime 分权 | 上游 JSON shape、浅 cast、UI snapshot、data URL persistence |
| Open Canvas | stable document owner、registry、hydrate/switch generation、stale guard | route/list UI、autosave/conflict、provider/storage 实现 |
| LibTV clone | 保留现有 R3F island、`uiStore` surface owner、Batch 67 codec | 继续把 `sourceNodeId` 单字段当 project identity |

上述研究输入不证明 LibTV 原站使用相同 schema、storage 或 UI。

## 3. 已确定的工程决策

### 3.1 Owner 与 key

```ts
interface DirectorProjectOwnerV1 {
  route: "libtv";
  canvasId: string;
  sourceNodeId: string;
}
```

- owner key 由结构化 tuple canonical encode 产生，不用可碰撞的手写分隔字符串；
- project ID 独立生成，不由 canvas/node display ID 推导；
- 相同 owner 复用 project ID；新 owner 永不复用其他 project ID；
- copied source node 在没有显式 remap contract 前采用“新 owner、新默认 project”
  的安全 reset policy，不共享原 project。

### 3.2 Registry 与 session

第一版只使用内存 registry：

```text
owner key
  -> projectId
  -> current DirectorProjectDocumentV1
  -> lifecycle ACTIVE | CLOSED | TOMBSTONED
  -> generation
  -> memory-only capture/resource sidecar
```

- portable document 是 Batch 67 V1；
- current capture `dataUrl/sentNodeId` 只放 memory-only sidecar，不进入 codec、
  history 或未来 persistence；
- local model library 继续是现有全局 resource catalog，本批不伪装成 project
  resource lifecycle；
- close 保存当前 project snapshot、取消 runtime、保留 CLOSED record；
- reopen 创建新 session ID 并递增 generation；
- same owner + same active session 为 no-op，不重置用户状态。

### 3.3 Session UI reset

切换到不同 owner 时：

- selection 按目标 document 中可解析 ID 重建；
- view/transform mode、thirds、panel、capture selection、timeline playhead/zoom、
  editor selection、path draft 和 phone recording 使用明确默认值；
- playback/capture/draft/phone runtime 全部停止；
- 不把旧 owner 的 session UI 套到目标 project。

同 owner 的 active no-op 不执行上述 reset。

### 3.4 Known boundary

当前 `objects` 仍混合 authored baseline 与 sampled projection。Batch 68 必须：

- 不宣称 `DIR-PROJECT-I03` 已完成；
- switch/restore 后以 deterministic non-playing baseline 重建可见 runtime；
- verifier 记录 seek 后 document 仍是已知风险，不能把 owner isolation pass 升级为
  authored stability pass；
- 若 integration 必须通过猜测 authored 值才能工作，停止扩张并将该部分移到
  Batch 69 authored/runtime split。

## 4. 实施切片

### Slice 0：主工作区与 worktree 安全清理

- 计划 checkpoint commit/push；
- 审计 `git worktree list --porcelain`、`.git/worktrees` 和
  `.claude/worktrees`；
- 对每个其他 worktree 检查 status、HEAD、相对 `master` 独有提交和 patch-id；
- 仅在 WIP/提交已被 `master` 吸收或为空时移除；
- 保持 `master` 主工作区干净，后续不创建 worktree。

### Slice A：纯 registry 与 identity

候选新增：

```text
src/lib/directorProjectRegistry.ts
```

职责：

- canonical owner key；
- project/session ID 与 generation；
- create/open/focus/switch/close/tombstone typed result；
- detached document 与 memory-only sidecar；
- deterministic clock/ID dependency，供 pure verifier 使用；
- invalid/stale/noop 为 zero partial。

### Slice B：document -> store restore adapter

在 Batch 67 codec 附近增加显式 reverse adapter：

- V1 scene/object/group/camera/timeline/output -> Director store authored fields；
- motion path points 等派生值重新计算，不写进 document；
- selection、playback、panel、phone、capture runtime 使用 session defaults；
- resource/capture sidecar 与 document 明确分开；
- strict decode failure 不替换 live store。

### Slice C：Director store/session authority

- `openSession` 输入完整 owner；
- 增加 current `projectId/sessionId/generation/ownerKey/lifecycle`；
- switch 前 snapshot current project，原子 restore/create target；
- 增加 owner-aware close；
- 不包装现有全部 mutation action，不新增 history；
- 暂不把 registry 写入 localStorage。

### Slice D：页面与 UI owner bridge

- `DirectorDesk` 接收 `canvasId + sourceNodeId`；
- workspace DOM 暴露 project/session/generation diagnostics；
- close 与 owner reconciliation 调用 owner-aware session close；
- source node 删除导致 active owner invalid 时关闭 session；
- source duplicate/new canvas owner 首次打开得到独立默认 project；
- 保持现有普通 graph selection、capture return 和 foreground shortcut 行为。

### Slice E：`LIBTV-VR-024` owner/session verifier

新增 Batch 68 pure/store verifier 与 focused browser scenario，至少覆盖：

```text
open A -> edit A -> open B -> B is default
edit B -> reopen A -> A restored
same owner open -> no-op
canvas A/source X != canvas B/source X
close/reopen -> project stable, session/generation fresh
new duplicated owner -> distinct default project ID
active source delete -> workspace closes, record not rebound
runtime/session fields do not bleed
invalid/stale request -> zero partial
ordinary graph count/history isolation
```

继续运行 Batch 67 pure codec 与 Batch 59 browser smoke。

### Slice F：治理与收口

- 更新 authority contract、current manifest、fixture catalog、verification ledger、
  traceability、decision register、Big Picture、Agent Task Map 和 coverage matrix；
- 运行专项 verifier、跨批 smoke、`npm run docs:check`、`npm run check`；
- 记录 warning、known boundary、commit/push 和下一批建议。

## 5. 验收标准

代码：

- [ ] owner key 对 route/canvas/source 三元组无碰撞；
- [ ] A/B source 和 A/B canvas 的 project ID/document/capture sidecar 不串场；
- [ ] reopen 同 owner 保持 project ID 与 authored document；
- [ ] session ID 与 generation 在 reopen/switch 后更新；
- [ ] same active owner open 是 no-op；
- [ ] close/switch 停止 playback/capture/path draft/phone recording；
- [ ] invalid/future document zero replacement；
- [ ] duplicate owner 不共享原 project；
- [ ] 普通 canvas graph/history 不因 open/switch/close 改变；
- [ ] TypeScript strict，无 `any`。

验证：

- [ ] Batch 68 pure/store verifier；
- [ ] Batch 68 Playwright focused verifier；
- [ ] Batch 67 pure codec；
- [ ] Batch 59 current Director smoke；
- [ ] `npm run docs:check`；
- [ ] `npm run check`；
- [ ] `git diff --check`；
- [ ] submodule pointers 未变化。

治理：

- [ ] 计划 checkpoint 后所有其他 worktree 已安全审计和移除；
- [ ] 关键进展及时 commit/push；
- [ ] 工作区最终干净且 `master...origin/master` 同步；
- [ ] 未把 Open Canvas/StoryAI 方法写成 LibTV source fact；
- [ ] 未把 owner isolation pass 写成 authored/runtime split pass。

## 6. 停止条件

出现以下任一情况时停止扩大本批范围：

- 其他 worktree 存在未吸收 WIP 或独有提交，不能安全移除；
- reverse adapter 需要猜测未来 schema 或 LibTV source persistence；
- owner isolation 必须先重写全部 85 个 action；
- 必须引入 browser storage、cloud/backend 或移动 submodule pointer；
- current capture/resource 只能通过写入 portable data URL 才能保存；
- sampled/authored 混写使 owner registry 无法在不损坏 document 的情况下工作；
- 需要删除或覆盖其他开发者未提交内容。

## 7. 下一批候选

Batch 68 完成后优先评估：

1. `DIR-PROJECT-I03` authored/runtime projection split；
2. typed Director command result + project-local undo/redo；
3. reference-aware object/camera delete；
4. 真实 asset/panorama slice；
5. 获得新 authenticated LibTV 证据后再做 UI/UX calibration。
