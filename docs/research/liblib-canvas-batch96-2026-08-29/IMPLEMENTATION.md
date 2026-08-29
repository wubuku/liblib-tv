# Batch 96 实施记录：Director 多机位与 Shot 工作流

> 状态：`SCRIPT_RECORDED_PASS`
>
> 实施日期：2026-08-29。
>
> 计划 checkpoint：`1c112f7`。
>
> 代码 checkpoint：`3f897b2`。

## 1. 计划 checkpoint

计划文档已在 `1c112f7` 落档，代码实现由 `3f897b2` 收口。本文件记录
实现、验证和治理结果。

## 2. 实施记录

### 2.1 Document / runtime

实现于 `src/lib/directorProjectDocument.ts`、
`src/lib/directorProjectRuntimeAdapter.ts` 和相关 duplicate/clipboard adapter：

- 新增 `DirectorShotRecordV1`，作为 portable document 的独立 authoring record；
- `shots` 保持 V1 兼容扩展，旧 payload 缺少该字段时由 camera、timeline duration
  和 capture descriptor 派生默认 Shot；
- capture descriptor 的可选 `shotId` 与 Shot `captureIds` 做 strict normalize；
- export 始终写规范化 Shot，active Shot、selection、playback 和 capture bytes
  仍不进入 portable document；
- clipboard 和 whole-project duplicate 使用独立 Shot ID map，保留内部 camera、
  track 和 capture 引用，不复制 session-only runtime。

### 2.2 Store / lifecycle

实现于 `src/store/directorStore.ts`、`src/lib/directorDeletePlanner.ts`：

- `activeShotId` 只属于 session UI，切换时同步 active camera、selection 和
  selected camera track，不新增 history；
- `addDirectorCamera()` 以一个 semantic command 创建 camera、camera track 和
  Shot，并维护 active fallback；
- `updateShot()` 对名称和有限时间范围做 strict validation；成功更新只产生一条
  history，同值返回 `NOOP`，非法/缺失引用返回 `REJECTED`；
- 删除 camera 会连带删除 Shot，清空相关 capture 的 camera/shot provenance，
  修复 active Shot/camera、selection 和 timeline；
- 删除最后一个 camera 继续返回
  `DIRECTOR_LAST_CAMERA_REQUIRED`，不产生部分 mutation；
- capture 写入和 Shot gallery 分组共用 canonical provenance，避免只按名称匹配。

### 2.3 UI / responsive

实现于 `DirectorDesk.tsx`、`DirectorInspector.tsx` 和 `DirectorViewport.tsx`：

- Director header 增加稳定的 Shot bar 和 `[data-director-shot-option]`；
- camera Inspector 暴露 Shot 名称、起止时间和稳定 `data-*` selectors；
- capture gallery 先按 Shot 分组，组内继续显示 camera 名称；
- desktop/mobile 均保持既有 workspace/drawer 布局，Shot bar 和 Inspector 不
  产生横向溢出；
- 本批不新增截图，视觉记录沿用已有 `SCREENSHOT_ANALYSIS.md`，避免重复识别。

## 3. 验证记录

专项命令：

```bash
LIBLIB_BASE_URL=http://localhost:4317 \
  python3 scripts/verify-liblib-batch96.py
```

结果：`SCRIPT_RECORDED_PASS`。结构化记录见
[`runtime-audit.json`](runtime-audit.json)，其中 desktop/mobile diagnostics
均为 `console/page/request = 0/0/0`。

| 场景 | 结果 |
|---|---|
| Static contract | portable Shot、legacy decode、clipboard/duplicate remap、delete repair、store/UI selectors 均通过 |
| Desktop `1440x900` | legacy decode/export、Shot create/switch/update、history undo/redo、capture provenance/gallery、delete repair、last-camera block、duplicate、reload/import/export 通过 |
| Mobile `390x844` | Shot bar、Inspector drawer、Shot interaction、无横向溢出通过 |
| Browser diagnostics | desktop/mobile console、page、request failures 均为 `0/0/0` |
| Screenshot cost | `screenshotsWritten=false`；未执行截图识别 |

相邻 current gates 按本批影响边界复跑并通过：

- Batch 94：Director workspace/drawer focus containment；
- Batch 95：canvas image ingress/session-only environment preview；
- Batch 93：Director final desktop/mobile and cross-batch regression；
- Batch 59、82、92：Director asset/resource/materialization/lease slices。

最终全量质量门、文档链接检查和 git hygiene 结果在本文件收口段追加。

## 4. 剩余风险

- LibTV 原站的 Director shot schema、时段语义和视觉布局仍为 `SOURCE_UNKNOWN`；
- capture bytes 仍是 session memory sidecar，不能宣称 durable media storage；
- 真实相机/镜头渲染和 cloud project sync 不在本批范围。

## 5. 治理与收口

已更新：

- `LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md`
- `VERIFICATION_LEDGER.md`
- `HARNESS.md`
- `LIBTV_FIXTURE_CATALOG.md`
- `TRACEABILITY_MATRIX.md`
- `BIG_PICTURE.md`
- `AGENT_TASK_MAP.md`
- `research/README.md` 与 `docs/index.md`

本批的证据标签仍严格分为 `CLONE_FACT`、`STORYAI_UPSTREAM_FACT`、`DECISION`
和 `SOURCE_UNKNOWN`；通过结果只证明 clone-owned Director 多机位/Shot 合同，
不升级 LibTV source parity。

## 6. 收口验证结果

2026-08-29 在固定 `http://localhost:4317` 上重新运行 Batch 96 专项 verifier，
并复跑本批影响边界内的相邻 current gates：

| 验证入口 | 结果 | 关键结果 |
|---|---|---|
| `verify-liblib-batch96.py` | `SCRIPT_RECORDED_PASS` | static contract、legacy decode/export、Shot create/switch/update、history undo/redo、capture provenance/gallery、delete repair、last-camera guard、clipboard/duplicate remap、reload/import/export、desktop/mobile overflow；诊断 `0/0/0` |
| `verify-liblib-batch59.py` | pass | Director asset-library search/preview/add、tree/Inspector continuity、mobile bounds、no-overflow 和 graph isolation |
| `verify-liblib-batch82.py` | pass | local model materialization、失败 proxy、retry/cancel/release、UI feedback；诊断 `0/0/0` |
| `verify-liblib-batch92.py` | `SCRIPT_RECORDED_PASS` | owner-scoped lease、deferred/final release、reference cleanup；诊断 `0/0/0` |
| `verify-liblib-batch93.py` | `SCRIPT_RECORDED_PASS` | Director desktop/mobile final regression、R3F nonblank、close/reopen、普通画布跨批入口；诊断 `0/0/0` |
| `verify-liblib-batch94.py` | `SCRIPT_RECORDED_PASS` | desktop workspace 与 mobile drawer focus containment、focus return、ARIA/inert、overflow；诊断 `0/0/0` |
| `verify-liblib-batch95.py` | `SCRIPT_RECORDED_PASS` | canvas-image ingress、session-only environment preview、stale/clear、malformed data URL isolation；诊断 `0/0/0` |

所有 browser verifier 均使用固定本地 dev server 和 fresh BrowserContext；本轮没有
写截图，也没有执行截图识别。上述通过只证明 clone-owned 合同，不升级
LibTV source parity。

## 7. 质量门与远端 checkpoint

以下命令在本批文档和代码变更上通过：

```text
npm run check
npm run docs:check
python3 scripts/verify-docs.py
git diff --check
```

本批收口提交包含本实施记录、专项 verifier、结构化运行时审计、治理索引和
Shot 草稿同步修复；提交哈希以仓库历史为准。推送后应核对 `master` 与
`origin/master` 同步、工作区干净且仅保留主 worktree。Batch 96 完成后停止，
不自动启动 Batch 97。
