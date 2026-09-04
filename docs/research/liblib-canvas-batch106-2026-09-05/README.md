# Batch 106：项目菜单（logo 下拉）对齐 2026-09-05 源站

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-09-05。
>
> 上一批 checkpoint：Batch 105（`batch/105-follow-banner`）。

本批按 2026-09-05 补采样把 logo 下拉复刻为项目菜单：回到主页 / 全部项目 /
（分组线）创建新项目 / 删除项目；四项均为诚实本地 status，不接路由或项目
服务。教程 popover（使用教程/联系客服/联系销售/关注公众号）经 verifier 锁定。

## 导航

- [PLAN.md](PLAN.md)：范围、证据边界与不包含项。
- [runtime-audit.json](runtime-audit.json)：结构化运行时证据。

## 证据边界

| 标签 | 本批含义 |
|---|---|
| `SOURCE_FACT` | 菜单存在、四项命名与 2/2 分组、锚定 logo 下拉、Escape 不关闭（观察） |
| `CLONE_DECISION` | 各项本地 status、chevron 触发、outside-click 关闭、保留 FrameOS Link（开发导航，标题标注） |
| `SOURCE_UNKNOWN` | 四项真实跳转/确认流、菜单精确几何 |

## 完成定义

1. `verify-liblib-batch106.py` 14 checks、`0/0/0` diagnostics 通过。
2. 相邻 `verify-liblib-batch11.py` 通过。
3. `npm run check`、`npm run docs:check` 通过。
4. 特性分支 commit/push。

通过结果只证明 clone-owned 项目菜单展示合同；四项真实行为仍是
`SOURCE_UNKNOWN`。
