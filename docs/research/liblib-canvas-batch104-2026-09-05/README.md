# Batch 104：故事板空态三组对齐 2026-09-05 源站

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-09-05。
>
> 上一批 checkpoint：Batch 103（`batch/103-mode-toggle-source`）。

本批把故事板主区对齐 2026-09-05 源站空画布观察：列顺序 文本/图片/视频、
`放大图片/放大视频` 列头按钮、`暂无文本/暂无图片/暂无视频` 空态文案，以及
关键元素侧栏在关键元素为空时隐藏（源站空画布无侧栏）。

## 导航

- [PLAN.md](PLAN.md)：范围、证据边界与不包含项。
- [runtime-audit.json](runtime-audit.json)：结构化运行时证据。

## 证据边界

| 标签 | 本批含义 |
|---|---|
| `SOURCE_FACT` | 三组顺序、空态文案、放大按钮存在、空画布无侧栏 |
| `CLONE_DECISION` | 侧栏隐藏阈值（图片+文本均空）、文本列复用 script 节点投影 |
| `SOURCE_UNKNOWN` | 放大按钮点击行为、非空画布源站是否有关键元素侧栏、banner 几何 |

## 实施结果

- `StoryboardColumn` 支持 `script` 列；主区列序 文本→图片→视频，最小宽度
  432→636px。
- 图片/视频列头新增 `放大图片/放大视频`（`data-storyboard-zoom`，行为
  `SOURCE_UNKNOWN`，本批不加 handler）。
- 列空态文案 `暂无文本/暂无图片/暂无视频`；关键元素侧栏在 图片+文本 均空时
  隐藏（`hidden`/`flex` 切换），demo 画布侧栏与卡片计数不变。
- batch13 两处列空态文案断言按源站更新（版本注释内联）。

## 完成定义

1. `verify-liblib-batch104.py` 18 checks、`0/0/0` diagnostics 通过。
2. 相邻 `verify-liblib-batch13/14.py` 通过。
3. `npm run check`、`npm run docs:check` 通过。
4. 特性分支 commit/push。

通过结果只证明 clone-owned 故事板空态展示合同；放大行为与非空画布源站
布局仍是 `SOURCE_UNKNOWN`。
