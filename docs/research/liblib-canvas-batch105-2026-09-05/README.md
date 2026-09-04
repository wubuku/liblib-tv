# Batch 105：协作跟随状态条

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-09-05。
>
> 上一批 checkpoint：Batch 104（`batch/104-storyboard-sections`）。

本批按 2026-09-05 源站 computed style 复刻协作跟随横幅：顶部居中 `z-[305]`
胶囊（正在跟随 / 取消 / 按 ESC 退出），非跟随态 opacity 淡出零干扰；会话
状态挂 uiStore，`follow-banner` 注册为单层 ESC 的最高优先 foreground
surface（batch62 契约顺延）。

## 导航

- [PLAN.md](PLAN.md)：范围、证据边界与不包含项。
- [runtime-audit.json](runtime-audit.json)：结构化运行时证据。

## 证据边界

| 标签 | 本批含义 |
|---|---|
| `SOURCE_FACT` | 横幅存在、fixed top-0 居中 z-[305]、opacity 过渡、胶囊文案、ESC 提示 |
| `CLONE_DECISION` | 会话状态挂 uiStore、200ms 过渡、取消按钮交互、surface 最顶优先级 |
| `SOURCE_UNKNOWN` | 跟随触发/可见态源站样式、可见时长、协作系统关系 |

## 实施结果

- 新增 `src/components/FollowBanner.tsx`；`page.tsx` 根部挂载。
- uiStore 新增 `isFollowingSession`/`setFollowingSession`；
  `LibTVBlockingForegroundSurface` 增加 `follow-banner`（最高优先），
  `closeTopForegroundSurface` 支持其单层退出。
- verifier 验证：默认淡出、置态可见、文案齐全、ESC 仅退跟随（同时打开的
  添加面板保留，再按 ESC 才关闭）、取消按钮退出。

## 完成定义

1. `verify-liblib-batch105.py` 15 checks、`0/0/0` diagnostics 通过。
2. 相邻 `verify-liblib-batch62/11.py` 通过。
3. `npm run check`、`npm run docs:check` 通过。
4. 特性分支 commit/push。

通过结果只证明 clone-owned 跟随横幅展示与单层 ESC 合同；真实协作、跟随
视口联动与触发入口仍是 `SOURCE_UNKNOWN`。
