# Batch 81 计划：Director 严格项目导入/导出

> 状态：`COMPLETED`。
>
> 日期：2026-08-29。

## 1. 为什么现在做

Batch 67 已完成严格 `DirectorProjectDocumentV1` codec，Batch 74/80 已建立
browser-local persistence、generation guard 和 tombstone cleanup。当前用户仍只能
依赖同一浏览器的 owner-scoped storage 恢复项目，无法主动备份、迁移到另一个
Director source node 或把一个可验证的 authored project 交给另一个 agent。

这不是把文件功能当成新的孤立按钮，而是把已有 authority 连接为一个安全工作流：

```text
current Director state
  -> portable V1 document
  -> strict JSON export

selected file
  -> parse
  -> strict decode/normalize
  -> rebind to current owner/project
  -> validate complete replacement
  -> update registry + local persistence
  -> one Director history entry
  -> restore R3F runtime projection
```

## 2. 证据边界与 clone 决策

### 2.1 已有事实

1. `createDirectorProjectDocumentV1` 已把 authored scene、objects、groups、timeline、
   paths、camera relations、stable resource references 和 capture descriptors 映射
   到 V1 document；
2. `encodeDirectorProjectDocument` 已执行 normalize 后 JSON 编码；
3. `decodeDirectorProjectDocument` 已执行 exact-key、schema、number、ID 和 reference
   校验；
4. `restoreDirectorProjectRuntimeSnapshotV1` 已把 portable document 恢复成 R3F
   runtime projection；
5. Director store 的 project-local history 已支持 semantic replacement 的
   before/after document；
6. Browser-local persistence 只应保存 stable document，不保存 runtime/media bytes。

### 2.2 未知与决策

当前没有足够 LibTV authenticated source evidence 证明原站的文件扩展名、JSON
schema、owner rebind、导入确认、history 语义、错误文案或下载命名。因此以下均
是 `CLONE_DECISION`：

| 问题 | 决策 |
|---|---|
| 文件格式 | 直接导出严格 `DirectorProjectDocumentV1` JSON，不增加未验证的 wrapper |
| 导入目标 | 只能替换当前已打开 Director project，文件 identity 不覆盖当前 owner |
| 导入 history | 成功替换计一条 Director semantic history；失败/no-op 为零条 |
| capture bytes | 不随导入/导出复制；import 后没有本地 archive 的 descriptor 不显示为可用截图 |
| local resources | 只保留 stable descriptor；不存在的本地 materialization 不伪造为已加载 |
| runtime/UI | selection、playhead、view mode、panel、phone vcam、gesture 清空/默认化 |
| error handling | parse/decode/rebind/commit 任一失败都 zero-partial |
| persistence failure | 当前状态保留为 session-only，沿用既有 storage boundary |

## 3. 实施切片

### Slice A：portable identity rebinding

- [x] 增加一个不改变 authored entity IDs 的 V1 document owner/project rebind helper；
- [x] helper 先 normalize 输入，再只替换 document-level `projectId`、`owner`；
- [x] 保持 camera/group/track/path/keyframe/anchor/resource 内部引用稳定；
- [x] 禁止通过 import 恢复 source owner、generation、session 或 tombstoned project。

### Slice B：store import/export authority

- [x] 暴露当前 active project 的严格 export string；
- [x] 暴露 `unknown -> DirectorCommandResult` 的严格 import action；
- [x] import 前完成 decode、rebind、normalize 和 active-session guard；
- [x] commit 前完成 registry update，成功替换时保留 before/after 供 undo/redo；
- [x] 清理 capture archive/active capture、phone runtime、clipboard 和 active gesture；
- [x] persistence write failure 不回滚 session state，不伪造 durable success。

### Slice C：Director UI workflow

- [x] 在 Director header 增加 icon-only export/import controls；
- [x] export 通过 browser download 写 JSON，不写截图或额外 storage；
- [x] import 使用 file input，接受 `.json`/`application/json`；
- [x] 显示成功/失败的短反馈，保留 `aria-label`、`title` 和 disabled/busy boundary；
- [x] 导入成功后 UI 显示当前 project 已恢复，且撤销可恢复旧 project。

### Slice D：focused verifier and governance

- [x] pure codec/rebind/zero-partial/history corpus；
- [x] fresh BrowserContext 下载并重新导入到同一/不同 source owner；
- [x] malformed/future/unknown/dangling/non-finite/data-URL 文件拒绝；
- [x] import success、undo/redo、capture/runtime/UI exclusion、owner rebind；
- [x] import/export 不改变 ordinary graph/history，zero diagnostics；
- [x] 更新 current verifier manifest、fixture、traceability、decision、coverage、
  Big Picture、Agent Task Map 和 Harness；
- [x] 运行 Batch 59、67-81 current gate、`npm run check`、`npm run docs:check`、
  `git diff --check`；
- [x] commit/push，确认 `master == origin/master`、工作区干净、仅保留主 worktree。

## 4. Fixture

```text
source owner A -> project A -> authored character/prop/camera/group/tracks/path
source owner B -> project B -> independent current session
portable export(A) -> JSON file -> import into B
```

必须覆盖：

1. A 导出后 JSON 不含 `data:`/`blob:` capture/resource bytes；
2. B 导入后保留 authored entity IDs 和内部引用，但 owner/project 使用 B；
3. B 的旧 project 可 undo 恢复，redo 再次得到 imported document；
4. malformed/future/unknown/dangling/non-finite 文件在 import 前零部分变更；
5. capture archive、selection、playhead、phone runtime、clipboard 不跨文件转移；
6. ordinary canvas graph nodes/edges/history 不因 Director import 变化；
7. 重新加载 B 时恢复的是 B 的 owner-scoped imported document，而不是 A；
8. tombstoned current owner、无 active session 和 persistence failure 均有明确 reject/
   session-only 边界。

## 5. 停止条件

只有以下全部满足才标记 `DIRECTOR_IMPORT_EXPORT_FOCUSED_PASS`：

- pure rebind/import corpus 通过；
- export 文件可下载且可被 fresh BrowserContext 重新选择；
- strict rejection 对 malformed/future/reference/resource-byte 输入 zero-partial；
- success/undo/redo 只产生一条 Director history，不污染 ordinary graph；
- imported owner/project/session authority 正确，runtime/UI transient 不泄漏；
- persistence failure 保持 session-only，tombstone 不可被 import 复活；
- current Director gates、全量检查和文档检查通过；
- closeout commit 已 push，主工作区干净。
