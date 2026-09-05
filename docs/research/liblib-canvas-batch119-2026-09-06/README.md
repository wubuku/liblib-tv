# Batch 119：/project 项目列表页落地

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-09-06。
>
> 上一批 checkpoint：Batch 118。
>
> 源站证据：[`../liblib-projects-page-2026-09-06/README.md`](../liblib-projects-page-2026-09-06/README.md)。

新增 clone 的 `/project` 路由：返回（回画布）、全部项目标题、回收站/新建
文件夹（本地 status）、开始创作创建卡（addCanvas + 回画布）、画布卡列表
（点击激活并回画布）。logo 菜单「全部项目」从 no-op 接线为真实导航
`/project`。

## 导航

- [PLAN.md](PLAN.md)：范围与证据边界。
- [runtime-audit.json](runtime-audit.json)：结构化运行时证据。

## 证据边界

| 标签 | 本批含义 |
|---|---|
| `SOURCE_FACT` | 页面分区与文案（返回/全部项目/回收站/新建文件夹/开始创作/创建新的视频项目） |
| `CLONE_DECISION` | 画布卡映射（单项目多画布 → 每画布一卡）、日期取当日、status no-op |
| `SOURCE_UNKNOWN` | 项目卡操作入口、回收站行为、源站分页 |

## 完成定义

1. `verify-liblib-batch119.py` 15 checks、`0/0/0` diagnostics 通过。
2. 相邻 batch106/65 通过（65 首跑出现已知 ownership 竞态 flake，重跑通过——
   Batch 108 sweep 中同模式，早于本系列改动）。
3. `npm run check`、`npm run docs:check` 通过。
4. master commit/push。
