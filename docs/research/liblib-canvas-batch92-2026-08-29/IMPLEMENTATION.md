# Batch 92 实施与验证记录

> 状态：`FOCUSED_RUNTIME_RECORDED_PASS`
>
> 日期：2026-08-29。

## 1. 实施范围

本批承接 Batch 82 的 Director local model materialization，处理本地资源在
session、异步 request、runtime object 和删除清理之间的生命周期边界：

- descriptor 严格校验 data URL、扩展名、MIME、`sizeBytes`、`lastModified`
  和解码后 25 MiB 上限；
- `idle/loading/ready/failed/canceled/released` 状态约束与终态错误一致性；
- request completion 必须匹配 request ID 和创建时的 owner；
- lease 具名化，带 `ownerKey`、`projectId`、`sessionId`、`generation` 和
  `leaseId`；
- 删除或清理时若仍有 lease，先记录 `releaseRequested`，最后一个 lease
  释放后才进入 `released`；
- stale ready completion 释放 lease，并 dispose 已解析但未被接收的
  `Object3D`；
- loader 跨 session/unmount 时使用创建 lease 时保存的旧 owner 释放资源；
- portable Director project 继续排除 `File`、`Blob`、data URL、`Object3D`
  和 runtime lease。

## 2. 关键实现结果

### 2.1 Descriptor 与 materializer

`createDirectorLocalResourceDescriptor` 现在拒绝 malformed/empty data URL、
不支持的扩展名、非安全整数 metadata、metadata 与 decoded bytes 不一致以及
超过 `25 * 1024 * 1024` bytes 的 local payload。materializer 在解析前再次
执行 decoded-byte budget guard，因此 direct caller 不能绕过 descriptor 层的
上限。

### 2.2 Owner-scoped lease

`startLocalModelResourceLoad` 在当前 Director active project/session 下同时
创建 request 和 lease。`settle`、`cancel`、`release` 均要求 owner 与当前
request/lease 一致；错误 owner 或重复 lease release 不改变当前资源状态。

### 2.3 Deferred release

`releaseLocalModelResource` 不再在仍有 runtime lease 时直接丢弃资源记录，而是
标记 deferred release。最后一个匹配 owner 的 lease 释放时，资源才进入
`released`，lease 数组清空且 active request 失效。删除 local library item
同时移除目录项和 authored/runtime 对象引用，但不会越过活动 lease 强制释放。

## 3. Verifier 与修正

专项 pure/source verifier：

```bash
node --experimental-strip-types scripts/verify-liblib-batch92.mjs
```

结果覆盖 strict descriptor/byte budget、owner-scoped request/lease、错误 owner
零 mutation、terminal invariant、deferred/final release、released resource
reactivation、retry 和 materializer budget guard，全部通过。

专项 fresh-page Playwright verifier：

```bash
LIBLIB_BASE_URL=http://localhost:4317 \
  python3 scripts/verify-liblib-batch92.py
```

结果覆盖 ready resource lease、deferred release、删除引用清理、最终 release、
released 无 lease 和 `0 / 0 / 0` browser diagnostics，全部通过。结构化结果见
[`runtime-audit.json`](runtime-audit.json)。

Batch 82 历史 verifier：

```bash
LIBLIB_BASE_URL=http://localhost:4317 \
  python3 scripts/verify-liblib-batch82.py
```

Batch 82 原脚本最初等待 `attempt === 1`，但当前 React/R3F loader 生命周期允许
在同一 mounted resource 上发生重入，最终合法 attempt 可能为 1 或更高。脚本
已收紧为合同要求的 `attempt >= 1`，并补齐 cancel 后显式匹配 owner/lease 的
最终 release；没有放宽资源状态或删除无效断言。适配后通过，browser
diagnostics 为 `0 / 0 / 0`。

TypeScript 与 diff whitespace 检查：

```bash
npm run typecheck
git diff --check
```

均通过。

## 4. 证据边界

| 主张 | 等级 |
|---|---|
| 当前 clone 有 owner-scoped Director local resource lifecycle | `CLONE_STATIC_FACT` + `RECORDED_RUNTIME` |
| 25 MiB decoded-byte budget、deferred release 和 terminal invariant | `CLONE_DECISION` + `RECORDED_RUNTIME` |
| 有限 OBJ/FBX materialization 能解析复杂生产模型 | `SOURCE_UNKNOWN` / `NOT_ESTABLISHED` |
| LibTV 原站使用相同 loader、lease、session protocol 或 persistence | `SOURCE_UNKNOWN` |

本批不证明 LibTV 原站 Director 的资源协议、真实 provider、远程持久化、生产
级 cache、复杂 FBX/纹理依赖或 ordinary canvas media ingress。`SESSION_DATA_URL`
仍是 clone-owned session-local locator，不是 durable cloud asset。

## 5. 后续入口

Batch 93 只做最终跨批、桌面/移动端、治理文档和全量门禁收口；完成后按当前
用户指示停止，不自动开始 Batch 94。

