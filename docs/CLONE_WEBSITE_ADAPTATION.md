# clone-website 技能的本项目适配说明

> 本文解释通用 `clone-website` 技能如何适用于当前 LibTV + FrameOS 研究仓库。
>
> 共享技能只负责通用克隆流程；当前项目的用户授权、源站安全、双路线架构和证据纪律优先级更高。本说明不修改 `.claude/skills/clone-website/SKILL.md` 或 `.codex/skills/clone-website/SKILL.md`。

## 1. 权威层级

当指引之间出现冲突，按以下顺序执行：

```text
用户当前明确要求
  -> 仓库 AGENTS.md 与 DECISION_REGISTER.md
  -> 当前任务的组件合同/源站证据
  -> clone-website 通用技能
  -> 个人偏好或旧记忆
```

因此，通用技能中的“发现一个组件后即可交给 builder”只有在当前用户已经授权编码、组件合同完成、fixture 和协作边界明确时才适用。当前研究-only 阶段，builder 不应被派出修改 `src/`。

## 2. 通用技能做什么

[`clone-website`](../.codex/skills/clone-website/SKILL.md) 提供以下通用方法：

- 从 URL 进入浏览器、截取 desktop/mobile 状态并读取 DOM/computed style；
- 扫描 scroll/click/hover/responsive 行为，而不是只复制静态截图；
- 将页面拆成拓扑、行为、token、组件规格和资产；
- 每个组件先形成 `docs/research/components/*.spec.md`，再拆成小 builder 任务；
- 使用隔离 worktree、窄验证和最终视觉回归；
- 对截图、资产、源码事实和实施结果保留可审计记录。

这些方法与本项目一致，尤其是：先保存证据、覆盖多个状态、组件规格先于实现、浏览器验证和小批次提交。

## 3. 当前项目必须覆盖的差异

| 通用技能默认 | 本项目适配 |
|---|---|
| 可以在提取过程中并行构建 | 当前无编码授权时只做提取、分析、计划和文档；授权后也按单 slice 实现 |
| 以目标网站可见页面为主要范围 | LibTV 还必须区分共享源站项目、登录态、可安全只读状态和可能 graph mutation 的动作 |
| 目标是 pixel-perfect clone | LibTV 先服从当前源站证据；旧截图、文章、Open Canvas 和主观视觉都不能覆盖最新 DOM/bundle 事实 |
| 可使用 demo/mock 数据完成视觉效果 | mock 必须显式标记，不得让 UI 暗示真实 Provider、上传、计费、保存或任务轮询已经接通 |
| builder 可独立修改组件 | 先读 `AGENTS.md`、路由/组件合同、相关 Batch 和 `DECISION_REGISTER.md`；不得跨 LibTV/FrameOS store 边界 |
| 只要 build 通过即可交付 | 还必须通过源站合同、状态生命周期、graph/history、移动端/zoom 以及证据分类检查 |
| 统一使用页面级或组件级 overlay | LibTV 图片 toolbar、editor panel、active tool、preview 和 modal 各有不同层级/anchor 合同 |
| 发现素材后直接下载并复用 | 先确认许可证、来源、是否含账号/隐私/用户内容；不保存 cookies、tokens、私有浏览器状态 |

## 4. 当前 LibTV 的执行流程

### Phase A：任务识别

1. 判断任务属于 LibTV、FrameOS、Open Canvas 研究、共享基础设施还是纯文档；
2. 读取 [`AGENTS.md`](../AGENTS.md)、[`DECISION_REGISTER.md`](DECISION_REGISTER.md) 和 [`AGENT_TASK_MAP.md`](AGENT_TASK_MAP.md)；
3. 搜索现有 `SCREENSHOT_ANALYSIS.md`、`LIVE_AUDIT.md`、component spec 和相关 Batch；
4. 确认用户是否授权编码，以及是否需要 local/disposable fixture。

### Phase B：只读研究

1. 复用已有证据，只有问题确实未覆盖时才重新打开截图或浏览器状态；
2. 使用 DOM、computed rect、bundle 字符串和结构化 JSON 支持精确结论；
3. 记录 viewport、zoom、登录态、项目 ID、交互状态和可能的副作用；
4. 把每条结论分类为 `SOURCE_FACT`、`ARTICLE_EVIDENCE`、`OPEN_CANVAS_INSPIRATION`、`INFERENCE` 或 `CLONE_DECISION`；
5. 任何需要输入、接受建议、上传、生成、保存、下载、发布或 graph mutation 的共享源站操作，都转成 `BLOCKED_BY_FIXTURE`。

### Phase C：规格与计划

1. 更新对应组件合同、能力矩阵、状态图或 Batch `PLAN.md`；
2. 明确节点/边/媒体版本/任务/保存状态的副作用；
3. 为新状态写最小验证断言和 fixture reset 规则；
4. 更新 `docs/research/README.md`、`docs/index.md` 或本项目任务入口；
5. 没有明确编码授权时，到此结束，不派 builder、不改 `src/`。

### Phase D：获得编码授权后

```text
组件合同
  -> 授权的单一 slice
  -> local/disposable fixture
  -> 最小实现
  -> 窄 Playwright / pure contract check
  -> npm run check
  -> 实施记录
  -> path-scoped commit + push
```

编码授权必须明确 route、store、组件、测试/截图范围、允许副作用和不包含的范围。不要把“继续克隆”解释为一次性授权全部功能。

## 5. LibTV 复刻的特殊合同

### 5.1 图片双浮层

- toolbar 在节点上方，editor panel 在节点下方；
- 两者共享 node center、live viewport 和 selection lifecycle，但不是同一定位公式；
- 当前顶部工具条动作集合与宽度以最新源站证据为准，旧 `900.5px` 只作历史快照；
- 下方面板使用源站的 `16 * zoom` gap 和 inverse scale；
- 节点靠近画布边缘时自然裁切，不凭感觉加窗口居中或自动避让。

详见 [`LibTVOverlayPositioning.contract.md`](research/components/LibTVOverlayPositioning.contract.md) 和 [`LIBTV_UI_STATE_HIERARCHY.md`](research/liblib-seedance-2.5-2026-08-25/LIBTV_UI_STATE_HIERARCHY.md)。

### 5.2 Auto Link

- 全局偏好、候选池、inline ghost 和 structured mention 是不同状态；
- graph edge、reference role 和 mention token 不合并；
- 正式引用保存 stable node ID、媒体类型、职责和 ordinal；
- 不用固定候选数组、独立确认弹窗或字符串前缀写回冒充当前源站合同。

详见 [`LibTVAutoLink.contract.md`](research/components/LibTVAutoLink.contract.md)。

### 5.3 Seedance 与过程型能力

- 生成参数和费用展示属于提交上下文，但采样数字不是永久后端合同；
- 片段重拍、逐帧拉片和超长视频过程依赖 ready-video、版本、时间范围和状态分层；
- 没有 disposable fixture 时不能在共享项目试探结果态；
- 逐帧拉片、智能剪辑、视频后处理保持独立节点/能力边界。

详见 [`LIBTV_DEPENDENCY_RISK_QUEUE.md`](research/liblib-seedance-2.5-2026-08-25/LIBTV_DEPENDENCY_RISK_QUEUE.md) 和 [`LIBTV_RESEARCH_GO_NO_GO.md`](research/liblib-seedance-2.5-2026-08-25/LIBTV_RESEARCH_GO_NO_GO.md)。

## 6. Open Canvas 的借鉴边界

Open Canvas 固定 submodule 是研究对象，不是第二个源站，也不是 LibTV 的实现模板。可以借鉴：

- measured node + live viewport 的 screen anchor 组织；
- typed input bucket 与 provider projection 的分离；
- node/run/save status 的正交表达；
- serialized subgraph 与 ID map 的 graph 边界。

不能直接搬入：

- Open Canvas 的节点类型、Provider、model slug、scene 命名、Handle 布局和具体间距；
- 它的官网预览或营销文案作为 LibTV 产品事实；
- 它的保存、KV、cookie 或后端路径作为当前项目真实能力。

详见 [`OPEN_CANVAS_PATTERN_CARDS.md`](research/open-canvas-2026-08-26/OPEN_CANVAS_PATTERN_CARDS.md)。

## 7. 同步与维护

- `.claude/skills/clone-website/SKILL.md` 是共享技能源文件，`.codex/skills/clone-website/SKILL.md` 是同步副本；
- 修改共享技能时运行 `node scripts/sync-skills.mjs`，并确认两份文件 `cmp` 一致；本说明不替代同步脚本；
- 新正式文档链接到 [`docs/index.md`](index.md)，新研究链接到 [`research/README.md`](research/README.md)；
- 文档变更运行 `python3 scripts/verify-docs.py`；代码变更还需按 [`HARNESS.md`](HARNESS.md) 验证；
- 在共享工作区只使用 path-scoped `git add`/commit，不使用 `stash`、reset 或覆盖其他人的 WIP；关键进展 commit/push。

## 8. 适配结论

通用技能解决“如何系统地克隆一个网站”；本项目适配说明解决“在共享、研究驱动、双路线、证据优先的 LibTV/FrameOS 仓库里，什么时候只能研究，什么时候可以编码，以及如何不把上游启发误当成源站事实”。两者应同时阅读。

