# Batch 68 实施与验证记录

> 状态：`PLANNED / WORKTREE_CLEANUP_COMPLETE / IMPLEMENTATION_NOT_STARTED`。
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

在该前置完成前不开始 Batch 68 业务代码。

## 4. 后续记录规则

实施后在此追加：

- 实际 registry/session API；
- reverse adapter 与 runtime reset 规则；
- A/B owner fixture 与 rejection cases；
- focused/browser/full gate 命令和结果；
- warning、known boundary、commit/push；
- 下一批的 high-value decision。
