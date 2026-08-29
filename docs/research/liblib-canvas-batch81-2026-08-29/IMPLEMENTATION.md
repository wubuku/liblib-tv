# Batch 81 实施与验证记录

> 状态：`SCRIPT_RECORDED_PASS`。
>
> 建档日期：2026-08-29。

## 1. 实施历史

本文件按顺序记录 Batch 81 的决策、代码变更、专项验证和保护性
checkpoint。计划阶段不把导入/导出写成已实现能力；本文件在 closeout 后记录
实际结果。

## 2. 预期代码边界

- `src/lib/directorProjectDocument.ts`：portable document identity rebind；
- `src/store/directorStore.ts`：strict export/import authority、session guard、
  history and persistence boundary；
- `src/components/director/DirectorDesk.tsx`：browser download/file selection；
- `scripts/verify-liblib-batch81.mjs`：pure contract corpus；
- `scripts/verify-liblib-batch81.py`：fresh BrowserContext workflow。

## 3. 实施结果

| Slice | Result |
|---|---|
| portable identity rebinding | `PASS`；strict normalize 后仅替换 document-level `projectId` 与 `owner`，内部 object/group/camera/track/path 引用保持稳定 |
| store import/export authority | `PASS`；active-session guard、strict decode、zero-partial、capture sidecar 清除、one-entry history、undo/redo 和同文档 `NOOP` |
| Director UI workflow | `PASS`；JSON download、`.json`/`application/json` file input、busy disabled boundary、aria/title 和成功/失败 feedback |
| ordinary route isolation | `PASS`；ordinary graph nodes/edges/history 未因 Director import/export 改变 |

## 4. 验证台账

| Gate | 状态 | 说明 |
|---|---|---|
| pure import/export/rebind | `PASS` | `node --experimental-strip-types scripts/verify-liblib-batch81.mjs` |
| fresh browser download/import | `PASS` | `LIBLIB_BASE_URL=http://localhost:4317 python3 scripts/verify-liblib-batch81.py` |
| Batch 59、67-81 current gate | `PASS` | serial run；全部专项脚本通过，zero browser diagnostics |
| `npm run check` | `PASS` | Batch 81 closeout 后执行 |
| `npm run docs:check` | `PASS` | Batch 81 closeout 后执行 |
| `git diff --check` | `PASS` | Batch 81 closeout 后执行 |

## 5. Closeout checkpoint

本批专项和跨批验证均使用固定开发端口 `4317`。Batch 59、67–81 的脚本顺序
运行通过；Batch 81 `runtime-audit.json` 保留本批最新结果，Batch 69–80 的
dated runtime audit 恢复为其原始记录。最终 `npm run check`、`npm run docs:check`
和 `git diff --check` 通过后提交并推送本批。

Closeout 已完成：三项项目门禁均通过，以下回归台账记录了本批 HEAD、端口、
脚本序列、诊断和工作区状态：
[`current-gate-regression.json`](current-gate-regression.json)。

## 6. 证据边界

本批不会新增 LibTV 原站 source-exact 结论。文件格式、identity rebind、导入
history、capture byte 排除、session-only failure 和 UI controls 都是 clone-owned
决策；原站是否存在相同能力保持 `SOURCE_UNKNOWN`，除非后续取得新的只读证据。
