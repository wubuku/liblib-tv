# Batch 68 实施与验证记录

> 状态：`PLANNED / IMPLEMENTATION_NOT_STARTED`。
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

计划 checkpoint 提交并推送后，先完成：

1. 枚举 Git 注册 worktree 与 `.claude/worktrees`；
2. 检查每个 worktree status、HEAD 和相对 `master` 独有提交；
3. 对疑似已合入但 hash 不同的提交比较 patch；
4. 仅在内容已被 `master` 吸收或目录为空时移除；
5. 清理后确认只保留主工作区，`git status` 干净。

在该前置完成前不开始 Batch 68 业务代码。

## 4. 后续记录规则

实施后在此追加：

- 实际 registry/session API；
- reverse adapter 与 runtime reset 规则；
- A/B owner fixture 与 rejection cases；
- focused/browser/full gate 命令和结果；
- warning、known boundary、commit/push；
- 下一批的 high-value decision。
