# Batch 97：Agent 抽屉对齐 2026-09-05 源站

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-09-05。
>
> 上一批 checkpoint：`86673b6`（Batch 96）。

本批把 Agent 抽屉从 2026-08-25 的 source-shaped 快照升级到 2026-09-05 登录态
源站复核结果：头部动作集合、Skill 推荐命名、composer 控件、选择模型目录菜单
与生成模式菜单。只做本地 shell 对齐，不接真实服务。

## 导航

- [PLAN.md](PLAN.md)：范围、证据边界、兼容影响与停止条件。
- [AGENT_DRAWER_CURRENT_SOURCE.spec.md](AGENT_DRAWER_CURRENT_SOURCE.spec.md)：
  模型目录/生成模式/Skill 数据合同、组件合同与验证断言。
- [IMPLEMENTATION.md](IMPLEMENTATION.md)：实施结果、断言迁移、验证与剩余风险。
- [runtime-audit.json](runtime-audit.json)：结构化运行时证据。

## 本批价值

2026-09-05 源站审计（[`../liblib-live-2026-09-05/README.md`](../liblib-live-2026-09-05/README.md)）
确认 Agent 抽屉出现了 clone 未建模的选择模型菜单（图片 7 + 视频 8，含 premium
角标）与生成模式菜单，composer 控件集合、头部动作集合和 Skill 推荐命名均已
漂移。本批以该审计为唯一源站证据完成一次有界 UI 对齐。

## 证据边界

| 标签 | 本批含义 |
|---|---|
| `SOURCE_FACT` | 头部按钮/disabled、Skill 卡命名与 handle、composer 控件、模型菜单分区结构/15 项目录/premium 分布、生成模式两项与默认项 |
| `CLONE_DECISION` | 模型行 `+` 选中态、菜单开合与 Escape 分层、第二批 Skill 填充、图标近似、`添加附件`/`Skill` 本地 status 反馈 |
| `SOURCE_UNKNOWN` | 模型行真实添加语义、头部各入口点击行为、通知横幅是否仍出现、精确图标/DOM/CSS |

## 实施结果

- 头部：`当前已是新对话`(disabled)、`历史对话`、`新对话无法分享`(disabled)、
  `Agent 设置`、`CLI & Skill`、`关闭`。
- Skill：标题随模式切换；第一批 4 张源站命名卡；换一批循环并清空选择。
- Composer：`添加附件 / 选择模型 / Skill / 生成模式 / Send`。
- 选择模型菜单：单滚动列表 `图片(7)/视频(8)` 分区 + 锚点 tab + premium 角标 +
  行内 `+` 本地选中。
- 生成模式菜单：`手动模式/自动模式`，默认自动，`aria-checked` 切换。
- `verify-liblib-batch14.py` 两处断言按当前源站更新并记录到
  `LIBTV_VERIFIER_REPLACEMENT_MAP.md`。

## 完成定义

1. `verify-liblib-batch97.py` 55 checks、`0/0/0` diagnostics 通过（desktop `1440x900`）。
2. `verify-liblib-batch13.py`、`verify-liblib-batch14.py` 相邻回归通过。
3. `npm run check`、`npm run docs:check` 通过。
4. 治理文档（LEDGER/HARNESS/REPLACEMENT_MAP/research README/index/BIG_PICTURE）更新。
5. 特性分支 commit/push 后工作区干净。

通过结果只证明 clone-owned 的 Agent 抽屉当前源站对齐合同，不升级 LibTV
source-exact 行为，也不改变 Director 或普通画布 graph 合同。
