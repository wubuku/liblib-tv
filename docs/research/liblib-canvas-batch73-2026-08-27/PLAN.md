# Batch 73 计划：Director Async Result Authority

> 状态：`IN_PROGRESS / ASYNC_AUTHORITY_FOCUSED_PASS_PENDING`。
>
> 日期：2026-08-27。
>
> 上游 checkpoint：`5ff6485`。

## 1. 目标

在 Director 现有 project/session authority 上补齐最小 async result ingress：

1. typed operation descriptor、owner snapshot、attempt 和 result/version identity；
2. current owner、project、session、generation、source fingerprint freshness 检查；
3. retry 抢占旧 attempt；
4. terminal duplicate/out-of-order completion 的零 mutation disposition；
5. 资源 producer -> graph result 的一次性 transfer/release 规则；
6. 视频导出完成结果在普通 canvas projection 前经过 authority；
7. phone take 的本地完成结果可使用同一 identity contract；
8. pure fixture、fresh-page export/capture 入口验证和现有 Batch 67-72 回归。

## 2. 实现切片

### Slice A：pure authority

- [ ] 新增 `src/lib/directorAsyncAuthority.ts`；
- [ ] `DirectorAsyncOperationDescriptorV1` 冻结 owner、session、generation、
  source fingerprint 和请求 fingerprint；
- [ ] `DirectorAsyncResultEnvelopeV1` 区分 operation、attempt、result 和
  result version；
- [ ] `begin`、`reconcile`、`snapshot` 以及 stable reason/disposition；
- [ ] operation 的新 attempt 自动让旧 attempt stale；
- [ ] terminal duplicate 为 `duplicate-noop`，invalid/stale 不写 registry。

### Slice B：resource ownership

- [ ] producer resource 只能被一个 accepted result transfer；
- [ ] stale/reject/commit failure 只能 release 一次；
- [ ] transfer/release 重复调用返回明确的 zero-mutation disposition；
- [ ] 不把 Blob/File/Object URL 放进 Director portable document。

### Slice C：Director integration

- [ ] 导出 request 携带 captured async owner/attempt/source fingerprint；
- [ ] browser result envelope 在 `createDirectorAnimationExport` 前 reconcile；
- [ ] stale/duplicate 导出不创建普通 canvas node；
- [ ] accepted graph projection 后才保留 video URL；
- [ ] capture / phone 的 authority adapter 先提供稳定入口，不接远端。

### Slice D：focused verifier

- [ ] pure current apply；
- [ ] owner/session/generation stale；
- [ ] source fingerprint drift；
- [ ] retry old attempt race；
- [ ] duplicate terminal delivery；
- [ ] progress 不产生 terminal duplicate；
- [ ] resource transfer/release exactly once；
- [ ] export graph projection stale guard；
- [ ] ordinary canvas graph/history isolation；
- [ ] console/page/request error 为零，截图写入为零。

### Slice E：治理与回归

- [ ] 更新 current verifier manifest、fixture catalog、coverage、traceability；
- [ ] 更新 verification ledger、HARNESS、Big Picture、Agent Task Map、decision register；
- [ ] 更新 async / Director 合同状态和 CHANGELOG；
- [ ] 运行 Batch 67-73 focused gates；
- [ ] 运行 `npm run docs:check`、`git diff --check`、`npm run check`；
- [ ] 记录实施结果、commit/push 并确认主工作区干净。

## 3. Fixture

纯 authority fixture 使用稳定别名：

```text
C1 / S1@V1
  -> O_EXPORT
  -> A1
  -> X1 / X1v1

retry:
  O_EXPORT
  -> A2

resource:
  U1 owned by A1
```

browser fixture 使用 fresh Director owner，导出结果通过真实 R3F canvas recorder
路径产生，但不调用网络 provider。普通 canvas graph/history 在操作前后记录
baseline，验证 stale/duplicate 不产生节点、边、selection 或 history residue。

## 4. 验收停止条件

只有全部满足才标记 `ASYNC_AUTHORITY_FOCUSED_PASS`：

- operation descriptor 不从 late-read active owner 生成；
- current/stale/duplicate/invalid 有稳定可检查的 disposition；
- 旧 attempt 不能覆盖 retry attempt；
- source fingerprint drift 不能覆写当前 Director project；
- duplicate completion 不重复 graph、resource 或 selection effect；
- resource transfer/release exactly once；
- export stale/reject 时 video URL 被释放；
- accepted export 只向 ordinary canvas 写入一次 graph history；
- phone/capture adapter 不破坏 Director project history；
- Batch 67-73、docs check、`npm run check` 全部通过；
- 文档明确记录 clone-owned 决策、LibTV source unknown 和后续边界；
- `master` 与 `origin/master` 同步且工作区干净。

## 5. 暂不解决

- 普通 canvas 所有 delayed creator 的统一 operation migration；
- remote run/poll/cancel/retry transport；
- durable async result envelope persistence；
- result superseded/history UI；
- 真实资源 loader、跨项目 lease/reachability；
- LibTV source-exact Director async UI/API。
