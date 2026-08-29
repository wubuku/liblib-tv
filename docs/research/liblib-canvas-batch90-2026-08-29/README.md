# Batch 90：Director project/session authority 与场景命令

- [`PLAN.md`](PLAN.md)：本批计划、边界和验收矩阵。
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：实施范围、结果、验证命令和下一批入口。
- [`current-gate-regression.json`](current-gate-regression.json)：Batch 59、67–90
  串行 current gate 与全量检查的结构化结果。

> 状态：`FOCUSED_RUNTIME_RECORDED_PASS`
>
> 日期：2026-08-29。
>
> 本批是连续五批中的第 2 批；完成后继续 Batch 91，不在本批宣称
> Director 整体成熟。

## 1. 本批目标

本批承接 StoryAI Director 评估提出的 P0 建议：让 Director 的 project/session
authority 在用户界面和 agent/verifier 入口中可观察，并把 Batch 89 暂时保留的
`updateScene` 直接写入改为有明确语义边界的 project command。

```text
owner/project/session/generation
  -> visible lifecycle outcome + stable diagnostics
scene draft input
  -> Enter/blur commit
scene toggle/color command
  -> normalized document
  -> persistence + one history entry
```

## 2. 证据与边界

| 内容 | 证据等级 |
|---|---|
| clone 有 owner、project、session、generation、registry 和 persistence | `CLONE_STATIC_FACT` |
| StoryAI 使用 project/version/session 分层 | `UPSTREAM_INSPIRATION` |
| LibTV 原站 exact project/session DOM、持久化和 history 语义 | `SOURCE_UNKNOWN` |
| scene field 的 draft、blur/Enter commit 与 one-entry history | `CLONE_DECISION` |

本批不把 StoryAI 或 clone 行为写成 LibTV 原站事实，也不改变普通画布 graph、
FrameOS、Three.js/R3F renderer 或远端服务。

## 3. 实施范围

- Director store 增加非 portable 的 session outcome 诊断；
- workspace 暴露 project lifecycle 和 session outcome 的稳定 `data-*` 入口；
- `updateScene` 经过 owner/session 校验、文档规范化、持久化和一条 history；
- 场景名称输入使用 draft，Enter/失焦提交一次；
- 场景 toggle/color 继续即时预览，但每个完成动作只产生一条 semantic history；
- 新增 pure/source 与 fresh-page Playwright verifier；
- 更新 current manifest、验证台账和本批实施记录。

不包含：

- 云端 project sync、source-exact LibTV project schema；
- 新的 shot schema、真实资源 loader 或多机位产品语义；
- 对已有 Director action 做全面 command kernel 重写。

## 4. 验收标准

- workspace 能读取 owner、project ID、session ID、generation、lifecycle 和
  session outcome；
- scene name 输入连续编辑不逐字符增加 history，Enter/blur 后最多一条；
- 空白 scene name 不会写入无效 document；
- scene toggle/color/name 的成功命令会更新 registry/persistence；
- scene 同值更新为 `NOOP`，失效 session 为 `STALE/REJECTED` 且零 history；
- undo/redo 能恢复 scene document；
- desktop/mobile scene inspector 无 panel 水平溢出；
- Batch 90 verifier、Batch 59/67-89 current gates、全量 check 和 docs check
  通过，browser diagnostics 为 `0 / 0 / 0`。

## 5. 当前决策

- `sessionOutcome` 是 session UI/diagnostic state，不进入 portable project；
- `projectLifecycle` 继续由 registry/session authority 驱动；
- 场景名称允许用户暂时编辑为空，但 commit 时回退到上一个非空名称；
- scene command 复用现有 `DirectorCommandResult`、document snapshot 和 history
  kernel，不新增平行 history。

## 6. 相关权威

- [`LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md`](../LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md)
- [`LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md`](../LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md)
- [`liblib-canvas-batch89-2026-08-29/IMPLEMENTATION.md`](../liblib-canvas-batch89-2026-08-29/IMPLEMENTATION.md)
- [`storyai-3d-director-desk-2026-08-27/NEXT_RESEARCH_AND_IMPLEMENTATION_ROADMAP.md`](../storyai-3d-director-desk-2026-08-27/NEXT_RESEARCH_AND_IMPLEMENTATION_ROADMAP.md)

## 7. 结果

Batch 90 pure/source verifier 通过 12 项断言；fresh-page Playwright verifier
覆盖 session outcome、scene draft/commit/no-op/reject、persistence、undo/redo
和 mobile Inspector，browser diagnostics 为 `0 / 0 / 0`。Batch 59、67–90
current gate 串行通过；具体实施边界和限制见 [`IMPLEMENTATION.md`](IMPLEMENTATION.md)。

下一批继续处理 Director 旧 mutation entrypoint 的 typed command/history
迁移，优先对象属性、相机设置和分组创建。
