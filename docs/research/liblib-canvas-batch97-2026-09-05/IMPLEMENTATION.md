# Batch 97 实施记录：Agent 抽屉对齐 2026-09-05 源站

> 状态：`SCRIPT_RECORDED_PASS`
>
> 实施日期：2026-09-05。
>
> 计划：[`PLAN.md`](PLAN.md)；合同：[`AGENT_DRAWER_CURRENT_SOURCE.spec.md`](AGENT_DRAWER_CURRENT_SOURCE.spec.md)。

## 1. 实施结果

- `AgentDrawer` 头部按钮集合对齐源站：`当前已是新对话`(disabled)、`历史对话`、`新对话无法分享`(disabled)、`Agent 设置`、`CLI & Skill`、`关闭`（执行既有 `toggleAgent`）。历史对话/Agent 设置/CLI & Skill 仍为无后端的可见入口（`SOURCE_UNKNOWN` 行为，未伪造菜单）。
- Skill 推荐第一批改为源站命名与 handle（皮克斯动画广告 `/pixar-animated-ad-creator` 等 4 项）；第二批保留 clone-shaped 填充。标题随 `editorMode` 切换：分镜 `让 Skill 帮你迈出第一步`，工作台 `选一个 Skill，让创作更快一步`。
- Composer 控件行改为 `添加附件 / 选择模型 / Skill / 生成模式 / Send`；移除旧的 引用工作流/引用节点/刷新上下文。`添加附件`/`Skill` 点击写入 `data-agent-status` 本地预览提示；Send/status、textarea、通知横幅行为不变。
- 新增 `选择模型` 菜单：单滚动列表 + `图片`(7 项)/`视频`(8 项) 分区与锚点 tab；premium 角标 6 项全部在视频区；行内 `+` 提供本地选中/取消（clone decision，源站未见选中样例）。模型目录、说明文案与 premium 分布逐项来自 2026-09-05 源站滚底复核。
- 新增 `生成模式` 菜单：`手动模式`/`自动模式`（含说明），默认 `自动模式`，`aria-checked` 切换。
- 菜单互斥；抽屉级 Escape 只关菜单不关抽屉（`stopPropagation`）。

## 2. verifier replacement

`scripts/verify-liblib-batch14.py` 两处断言按当前源站更新（版本注释已内联，另见
[`../LIBTV_VERIFIER_REPLACEMENT_MAP.md`](../../research/LIBTV_VERIFIER_REPLACEMENT_MAP.md) §新增）：

1. Skill 选中回填 `皮克斯动画风格` → `皮克斯动画广告`；
2. 关闭按钮 aria `关闭 Agent` → `关闭`(exact)。

其余 batch14 断言（4 卡数量、通知横幅、composer、status 本地预览、分享面板）未动且继续通过。

## 3. 验证

| 入口 | 结果 |
|---|---|
| `scripts/verify-liblib-batch97.py` | 55 checks，`0` console / `0` pageerror / `0` requestfailed；desktop `1440x900` |
| `scripts/verify-liblib-batch13.py` | pass（storyboard 投影、关键元素、workbench 往返、移动端溢出） |
| `scripts/verify-liblib-batch14.py` | pass（断言更新后） |
| `npm run check` | lint（9 既有 warning）/ typecheck / build 通过 |
| `npm run docs:check` | 648 个 Markdown、3827 个本地链接通过 |

结构化运行时证据：[`runtime-audit.json`](runtime-audit.json)。本批 verifier 不写截图；Agent 移动端(<640px)不渲染该抽屉（既有 `hidden sm:flex`），移动端溢出由 batch13/14 覆盖。

## 4. 边界与剩余风险

- 本批只对齐 clone UI shell 与菜单目录；不接入真实 Agent、模型调用、上传、历史对话或通知服务；
- 模型行选中语义、`添加附件`/`Skill`/`CLI & Skill`/`历史对话`/`Agent 设置` 的点击行为、通知横幅是否仍出现，均为 `SOURCE_UNKNOWN`；
- 源站模型目录会随时间漂移；后续批次如再触 Agent，应先做 freshness 复核再改断言；
- 不证明 LibTV 原站 Drawer DOM/CSS/交互的 exact 实现，也不升级任何 Director/普通画布 graph 合同。

## 5. 治理更新

`VERIFICATION_LEDGER.md`、`HARNESS.md`、`LIBTV_VERIFIER_REPLACEMENT_MAP.md`、
`docs/research/README.md`、`docs/index.md`、`BIG_PICTURE.md` 已随本批更新。
