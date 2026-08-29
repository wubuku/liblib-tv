# Batch 92 计划：Director 本地资源生命周期与 session lease 收口

> 状态：`PLANNED`
>
> 建档日期：2026-08-29。
>
> 上一批 checkpoint：`738504e`。

## 1. 背景与高价值问题

Batch 82 已建立 Director 本地 OBJ/FBX 的 descriptor、attempt、状态和有限
Three.js materialization 路径，但它仍有几个可靠性缺口：

- descriptor 对 data URL、MIME、size 和 lastModified 的运行时校验不够严格；
- `ready/failed/canceled` 的 error 组合没有由状态机约束；
- local model resource 的 lease 只有计数，没有 session/generation 身份；
- 清理资源时若仍有 runtime lease，第一次 release 会被拒绝，但没有 deferred
  release 标记，可能留下不可达 descriptor；
- parse 失败/取消后的 lease 释放依赖 component unmount，终态完成后不够及时；
- portable Director project 仍必须与 `File`、`Blob`、data URL、`Object3D` 和
  运行时 lease 完全隔离。

这些是 clone reliability 问题，不是新增 LibTV 原站 source-exact 结论。

## 2. 本批排序

| 优先级 | Slice | 价值 | 风险 |
|---|---|---|---|
| P0 | descriptor strict validation + byte budget | 防止坏 data URL、错误 metadata 和超大 local payload 进入 catalog | 低 |
| P0 | terminal status/error invariant | 防止失败被标为成功或成功带着旧错误 | 低 |
| P0 | owner-scoped materialization lease | 防止跨 session 或重复 cleanup 误释放 | 中 |
| P0 | deferred release + terminal lease cleanup | 解决删除/卸载/失败交错时的孤儿资源 | 中 |
| P1 | materializer boundary hardening | 让 direct caller 也遵守 byte/abort/mesh 合同 | 低 |
| P1 | pure + fresh-page verifier and current-gate integration | 将上述合同变成持续门禁 | 低 |

## 3. 实施决策

### 3.1 资源边界

- `DirectorLocalResourceDescriptorV1` 仍是 session-local serializable metadata；
  `locatorClass` 继续为 `SESSION_DATA_URL`，不称为 durable asset。
- 本地模型默认最大 decoded payload 为 25 MiB；缺失 `sizeBytes` 时只接受能被
  可靠估算的 data URL，明确超预算或 malformed payload 直接拒绝。
- `mimeType`、`lastModified` 和 file name 在进入 descriptor 前做有限的类型、
  空值和有限数值校验。
- `Object3D`、`File`、`Blob`、原始 data URL 和 parsed bytes 不进入 portable
  project document、Director history 或 persistence envelope。

### 3.2 状态与 lease

- 状态继续使用 `idle/loading/ready/failed/canceled/released`；
  `ready` 只能有 `error=null`，`failed/canceled` 必须有对应 failure reason，
  `loading` 必须有 active request。
- 每个 materialization lease 带 session/generation/lease ID；错误 session 或
  重复释放不得改变当前状态。
- release request 在 lease 尚未归零时先标记 deferred；最后一个 lease 释放时
  自动收口为 `released` 并使 active request 失效。
- failed/canceled 终态不继续持有成功 materialization lease；ready 资源由
  runtime object 持有，直到 loader unmount 或资源被安全清理。

### 3.3 证据边界

| 内容 | 证据等级 |
|---|---|
| 当前 clone local model catalog、loader、resource map | `CLONE_STATIC_FACT` |
| 本批 descriptor/lease/release 规则 | `CLONE_DECISION` |
| StoryAI 或 Open Canvas 的 resource layering | `UPSTREAM_INSPIRATION` |
| LibTV 原站 Director loader、session lease、资源协议 | `SOURCE_UNKNOWN` |

不把本批结果描述成 LibTV 原站行为，也不把有限 OBJ/FBX parser 描述成生产级
asset pipeline。

## 4. 验收矩阵

| 场景 | 预期 |
|---|---|
| valid descriptor | accepted，decoded size/metadata 在预算内 |
| malformed/empty/oversized data URL | rejected，zero catalog mutation |
| invalid MIME/size/lastModified | rejected，zero mutation |
| loading | active request 与 owner/lease 一致 |
| ready | error 清空，旧失败信息不残留 |
| failed/canceled | 明确 reason，不能伪造 ready |
| stale request/owner | rejected，zero current mutation |
| wrong/double lease release | rejected/no-op |
| release with active lease | deferred，active request 失效 |
| final lease release | exactly once 进入 released |
| runtime parse failure | proxy/object state 保留，UI 可 retry |
| portable export | 不含 File/Blob/data URL/Object3D/lease runtime |
| browser diagnostics | console/page/request error 均为 0 |

## 5. 预定文件与治理同步

实现预计触及：

- `src/lib/directorLocalResourceLifecycle.ts`
- `src/lib/directorLocalModelMaterializer.ts`
- `src/store/directorStore.ts`
- `src/components/director/DirectorViewport.tsx`
- `scripts/verify-liblib-batch92.mjs`
- `scripts/verify-liblib-batch92.py`

文档预计新增/更新：

- 本目录 `README.md`、`IMPLEMENTATION.md`、`runtime-audit.json`；
- `docs/research/README.md`；
- `docs/research/VERIFICATION_LEDGER.md`；
- `docs/research/LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md`；
- `docs/research/LIBTV_FIXTURE_CATALOG.md`、`docs/research/TRACEABILITY_MATRIX.md`
  或相关治理入口（仅在确有对应条目时更新）；
- `docs/HARNESS.md`、`docs/AGENT_TASK_MAP.md`、`docs/BIG_PICTURE.md`。

## 6. 停止条件

Batch 92 以专项 verifier、Batch 82 与当前 Director gates、`npm run check`、
`npm run docs:check`、`python3 scripts/verify-docs.py` 和 `git diff --check`
全部通过为完成标准。Batch 92 完成后立即建立 checkpoint；随后实施 Batch 93
最终跨批/移动端回归。Batch 93 完成后按用户指示停止，不启动 Batch 94。
