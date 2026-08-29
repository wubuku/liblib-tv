# Batch 80 计划：Director Durable Tombstone 与安全资源清理

> 状态：`DURABLE_TOMBSTONE_FOCUSED_PASS`。
>
> 日期：2026-08-28。

## 1. 为什么现在做

Batch 76 已能把不可达 Director owner 标记为 memory-only tombstone，但
browser-local persistence 仍保留可恢复 document。这样刷新后，registry 虽然
重建，旧 document 仍可能被读取；而 transient capture 和 local model descriptor
也缺少与 owner 生命周期一致的清理门槛。

Batch 79 又让 Director document 能随 whole-project duplicate 复制，因此删除
生命周期必须明确区分：

```text
owner unreachable
  -> registry tombstone
  -> durable tombstone attempt
  -> success: block reload + clear transient project state + release unshared locals
  -> failure: keep session-only state/resources and report non-durable result
```

## 2. 证据边界与 clone 决策

当前没有足够的 LibTV authenticated source evidence 证明原站使用 localStorage、
同一 tombstone envelope、同一恢复阻断、capture bytes 清理或本地模型 descriptor
回收。因此本批的 schema、reason、cleanup 顺序和资源策略全部标记为：
`CLONE_DECISION` / `CLONE_FACT`，不能写成 LibTV source fact。

采用以下保守决策：

1. persistence envelope 增加严格的 `lifecycle: "TOMBSTONED"` 形态；
2. load 遇到合法 tombstone 返回 `PROJECT_TOMBSTONED`；
3. save 不得覆盖 tombstone，避免旧 session 或晚到保存复活 document；
4. tombstone 幂等；generation 更高的 document 不能被更低 generation 删除；
5. tombstone 写失败保留旧 document 与 local resource，状态为 `SESSION_ONLY`；
6. durable cleanup 后删除 store history/capture archive，并清空 registry transient
   capture sidecar；
7. local resource 只有在其他 live owner 或 session-only owner 都不引用时才释放；
8. graph history 与 Director semantic history 分层，reconciliation 不增加
   Director history。

## 3. 实施切片

### Slice A：storage authority

- [x] 增加 strict tombstone envelope；
- [x] load 识别合法 tombstone；
- [x] tombstone 写入、幂等、generation guard；
- [x] save-after-tombstone 拒绝 resurrection；
- [x] storage unavailable/write failure 显式返回。

### Slice B：registry/store cleanup

- [x] active/inactive owner reconciliation 统一尝试 durable tombstone；
- [x] durable 成功后清理 project history 与 capture archive；
- [x] 清空 tombstoned registry 的 transient capture sidecar；
- [x] 只释放不再被其他 live/session-only project 引用的 local descriptor；
- [x] active shell/session/runtime cleanup 保持 Batch 76 的两阶段顺序。

### Slice C：focused verifier

- [x] pure strict round-trip、malformed、stale、idempotent、failure corpus；
- [x] fresh-page active owner delete；
- [x] fresh-page inactive owner delete；
- [x] reload reopen rejection；
- [x] shared/unshared local resource retention/release；
- [x] graph history、Director history、capture sidecar 和 diagnostics assertions。

### Slice D：governance/closeout

- [x] 更新 current verifier manifest、fixture、traceability、decision、coverage、
  Big Picture、Agent Task Map 和 Harness；
- [x] 运行 Batch 59、67-80 current gate；
- [x] 运行 `npm run check`、`npm run docs:check`、`git diff --check`；
- [x] commit/push，确认 `master == origin/master`、工作区干净、仅保留主 worktree。

## 4. Fixture

```text
canvas A:
  source A -> active Director project PA -> local resource R -> capture bytes
  source B -> closed Director project PB -> same local resource R
```

场景：

1. 删除 active source A：PA durable tombstone、shell/session 清理，R 因 PB 引用
   仍保留；
2. 删除 inactive source B：PB durable tombstone，R 无引用后释放；
3. reload 后 A/B 都不能 reopen；
4. malformed tombstone 不被当成合法 durable marker；
5. write failure 不覆盖旧 document、不释放资源。

## 5. 停止条件

只有以下条件全部满足，才将本批标记为 focused pass：

- pure verifier 通过全部 tombstone/storage contract；
- fresh BrowserContext 通过 active/inactive/reload/resource 场景；
- active shell teardown 不出现 R3F/页面错误；
- capture bytes、history、resource release 与 durable success 条件一致；
- ordinary graph history 不被 Director cleanup 污染；
- current Director gates、全量检查和文档检查通过；
- closeout commit 已 push，主工作区干净。
