# Batch 103：顶栏模式切换对齐 2026-09-05 源站

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-09-05。
>
> 上一批 checkpoint：Batch 102（`batch/102-asset-drawer-source`）。

本批把顶栏模式切换文案对齐 2026-09-05 源站：`工作台`→`工作流`、
`分镜`→`故事板`（title + aria；内部 `editorMode` 值与切换行为不变），
并按 replacement 协议迁移 batch11/13/14/17 的 aria 断言。

## 导航

- [PLAN.md](PLAN.md)：范围、证据边界与不包含项。
- [runtime-audit.json](runtime-audit.json)：结构化运行时证据。

## 证据边界

| 标签 | 本批含义 |
|---|---|
| `SOURCE_FACT` | 顶栏 `工作流`/`故事板` 命名与 aria-pressed 双态 |
| `CLONE_DECISION` | 内部 mode 值保留英文；icon 沿用 lucide 近似 |
| `SOURCE_UNKNOWN` | 源站图标精确形状与按钮几何 |

## 实施结果

- `TopNavBar` 两个模式按钮 aria/title 更名；点击行为、Agent 联动、
  故事板投影、快捷键隔离均不变。
- batch11/13/14/17 断言同步更名（版本注释内联）；batch17 的资产空态文案
  断言顺带按 Batch 102 的源站事实更新为 `画布暂无节点`。

## 完成定义

1. `verify-liblib-batch103.py` 11 checks、`0/0/0` diagnostics 通过。
2. 相邻 `verify-liblib-batch11/13/14/17.py` 迁移后全部通过。
3. `npm run check`、`npm run docs:check` 通过。
4. 特性分支 commit/push。

通过结果只证明 clone-owned 顶栏命名合同；内容性「分镜」文案（Skill 卡、
工具箱预设、生成面板图片名）不在本批范围。
