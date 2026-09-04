# Batch 105 Plan：协作跟随状态条

> 状态：`PLANNED`
>
> 建档日期：2026-09-05。
>
> 上一批 checkpoint：Batch 104（`batch/104-storyboard-sections`）。
>
> 源站证据：[`../liblib-live-2026-09-05/README.md`](../liblib-live-2026-09-05/README.md) §2（`fixed left-1/2 top-0 z-[305]` 淡出态容器 + 「正在跟随 / 取消ESC / 按ESC 退出」胶囊，computed style 直接观察）。

## 1. 范围

### 包含

1. **横幅组件** `FollowBanner`（`SOURCE_FACT` 结构 + `CLONE_DECISION` 视觉近似）：顶部居中 `z-[305]` 胶囊，含 `正在跟随`、`取消`（`data-follow-cancel`）与 `按 ESC 退出` tooltip；非跟随态 `opacity:0` 且 `pointer-events-none`/`aria-hidden`。
2. **会话状态**（`CLONE_DECISION`）：uiStore 新增 `isFollowingSession` + `setFollowingSession`；触发来自协作事件（源站不可采样），clone 不提供可见触发入口。
3. **单层 ESC 退出**（合同内接入）：`follow-banner` 注册为 `LibTVBlockingForegroundSurface` 最高优先层；跟随中 ESC 经既有 `closeTopForegroundSurface` 仅退出跟随（batch62 契约顺延）。

### 不包含

- 真实协作/多人会话、跟随视口联动、跟随发起入口；
- 横幅淡出计时的源站精确值（clone 用 200ms 近似）。

## 2. 证据边界

| 标签 | 内容 |
|---|---|
| `SOURCE_FACT` | 横幅存在性、fixed top-0 居中 z-[305]、opacity 过渡、胶囊结构与文案、ESC 退出提示 |
| `CLONE_DECISION` | 会话状态挂 uiStore、过渡时长、取消按钮交互、surface 优先级位于最顶 |
| `SOURCE_UNKNOWN` | 跟随触发与可见态源站样式、可见时长、与协作系统的关系 |

## 3. 影响面与兼容

- 新增 `src/components/FollowBanner.tsx`；`page.tsx` 挂载；uiStore/context 各一小块；
- batch62 surface 枚举为显式列表，不含 follow-banner，且默认 false 不改变既有解析顺序（复跑确认）。

## 4. 验证

- 新增 `scripts/verify-liblib-batch105.py`：desktop `1440x900`，断言默认淡出、经 `window.__libtv_ui_store` 置跟随态后可见、文案齐全、`取消` 退出、跟随中 ESC 仅退跟随（add-node 同时打开时不受影响）、零诊断。
- 复跑 `verify-liblib-batch62.py`、`verify-liblib-batch11.py`。
- `npm run check`、`npm run docs:check`。

## 5. 完成定义

1. 横幅结构与源站 computed style 一致；非跟随态零干扰。
2. ESC 单层退出符合 batch62 契约。
3. 相邻 verifier 与全量检查通过；特性分支 commit/push。
