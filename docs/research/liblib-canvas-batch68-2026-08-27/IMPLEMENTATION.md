# Batch 68 实施与验证记录

> 状态：`IMPLEMENTED_FOCUSED_PASS / BROWSER_AND_FULL_GATES_PENDING`。
>
> 日期：2026-08-27。

## 1. 计划 checkpoint

本批计划已综合：

- Batch 67 portable project codec；
- StoryAI project/version/session 与 scoped persistence 方法；
- Open Canvas stable document owner、hydrate、generation 与 multi-document
  lifecycle 方法；
- 当前 clone `uiStore` surface owner 与 singleton `directorStore` 的不对称；
- current Director verifier manifest。

本批不以 StoryAI/Open Canvas 视觉或 schema 替代 LibTV source evidence。

## 2. 预实施状态

| 项目 | 状态 |
|---|---|
| Batch 67 codec | `PROJECT_CODEC_FOCUSED_PASS` |
| Owner/session runtime | 未实现 |
| 新截图识别 | 未执行 |
| Browser persistence | 不在本批 |
| History/delete | 不在本批 |
| 两个 submodule | 计划保持固定 |
| 工作位置 | `master` 主工作区 |

## 3. Worktree 清理前置

计划 checkpoint `39deb21` 提交并推送后，已完成：

| 检查项 | 结果 |
|---|---|
| Git 注册 worktree | 只有 `/Users/yangjiefeng/Documents/wubuku/liblib-tv` 主工作区 |
| `.git/worktrees` | 不存在，无 stale metadata |
| `.claude/worktrees` | 空目录，已移除 |
| remote `worktree-agent-*` branch | 无 |
| 主工作区 | `master` 与 `origin/master` 同步 |

残留的 5 个本地 agent 分支均通过
`git merge-base --is-ancestor <branch> master`：

```text
worktree-agent-a40ad05698eaa6e8b 15b1962 absorbed-by-master=yes
worktree-agent-a46f3e13dd9606a6e 37f1397 absorbed-by-master=yes
worktree-agent-a49f826b731a6b601 2123941 absorbed-by-master=yes
worktree-agent-a91acb41cb4e231ca 53e60c2 absorbed-by-master=yes
worktree-agent-aba09f525c5282859 bad875e absorbed-by-master=yes
```

因此不需要 cherry-pick、patch-id 补偿或保存额外 WIP。已执行 worktree prune，并
使用安全的 `git branch -d` 删除上述已合并分支。最终只保留主 worktree 和
`master` 分支。

该前置完成后，Batch 68 业务代码已在主工作区开始实施。

## 4. 已实施代码

- `src/lib/directorProjectRegistry.ts`
  - structured owner key；
  - in-memory project record、session、generation 与 lifecycle；
  - create/focus/restore/update/close/tombstone typed result；
  - detached V1 document 与 memory-only capture sidecar；
  - injected normalizer/clock/ID dependency；
  - stale/invalid/tombstoned zero-partial。
- `src/lib/directorProjectRuntimeAdapter.ts`
  - V1 document -> current Director scene/object/group/timeline/output shape；
  - motion path derived points 重建；
  - playback、selection、editor、path draft 和 camera preset runtime reset。
- `src/store/directorStore.ts`
  - current project owner/project ID/session ID/generation/lifecycle；
  - full-owner `openSession` 与 owner-aware `closeSession`；
  - switch 前 snapshot current project，restore/create target；
  - per-project memory capture sidecar，global local model catalog 保持原边界；
  - browser diagnostics registry snapshot。
- `src/components/director/DirectorDesk.tsx`
  - 接收 canvas/source owner；
  - workspace 暴露 project/session/generation diagnostics；
  - manual close 进入 owner-aware close。
- `src/app/page.tsx`
  - invalid Director UI owner 在关闭 surface 前关闭对应 session；
  - UI owner 清空时补偿关闭 active Director session；
  - 只在 canvas/source owner 都存在时挂载 workspace。

## 5. Verifier 实施

- `scripts/verify-liblib-batch68.mjs`：直接执行实际 registry + Batch 67 codec；
- `scripts/verify-liblib-batch68.py`：计划组合 pure corpus 与 focused Playwright；
- 没有截图识别或视觉 artifact 写入。

当前 pure 结果：

```text
status=PASS
ownerKeys=3
projects=3
activeGeneration=2
create=CREATED
focus=FOCUSED
restore=RESTORED
stale=STALE
tombstonedOpen=REJECTED
documentIsolation=true
memorySidecarIsolation=true
zeroPartialRejection=true
```

当前 focused gates：

```text
npm run typecheck：PASS
npx eslint changed TS/TSX + verifier：PASS
git diff --check：PASS
Batch 68 Playwright：PENDING
Batch 67 / Batch 59 regression：PENDING
npm run check：PENDING
```

## 6. 当前已知边界

- `objects` 仍是 authored/sampled 混合容器，本批 restore 在 playhead 0 重建可见
  runtime，但不宣称 portable authored stability 已完成；
- source duplicate 采用新 owner/new default project 的安全 reset policy，尚未实现
  deep project clone/remap；
- active source invalid 会 close session，inactive project tombstone/reachability
  reconciliation 尚未接普通 graph 全量 lifecycle；
- capture `dataUrl/sentNodeId` 仅在内存 sidecar 隔离，不进入 V1 codec 或 persistence；
- capture/export async destination owner 仍是后续 slice。

## 7. 后续记录规则

实施后在此追加：

- 实际 registry/session API；
- reverse adapter 与 runtime reset 规则；
- A/B owner fixture 与 rejection cases；
- focused/browser/full gate 命令和结果；
- warning、known boundary、commit/push；
- 下一批的 high-value decision。
