# Batch 90 实施与验证记录

> 状态：`FOCUSED_RUNTIME_RECORDED_PASS`
>
> 日期：2026-08-29。

## 1. 目标与范围

本批承接 Director 评估中的 `STORY-R01` project/session authority 建议，
并把场景设置从临时 store 写入提升为一个有 owner、session、document、
persistence 和 project-local history 边界的 semantic command。

实际触及：

- `src/store/directorStore.ts`
- `src/components/director/DirectorDesk.tsx`
- `src/components/director/DirectorInspector.tsx`
- Batch 90 pure/source 与 fresh-page verifier

本批没有修改普通 LibTV graph、FrameOS、R3F renderer、云端服务或源站共享
画布数据。

## 2. 实施结果

### 2.1 Session outcome 与诊断入口

- `openSession` 的 disposition、reason、previous owner 和时间被记录为非
  portable `DirectorSessionOutcome`；
- workspace 暴露 `data-director-project-lifecycle`、
  `data-director-session-disposition`、`data-director-session-reason`、
  project/session/generation 等稳定诊断属性；
- session、selection、playhead、panel 和 R3F runtime 不进入 project document。

### 2.2 Scene semantic command

`updateScene` 现在：

- 校验 active project/session/owner；
- 拒绝未知字段、空名称、空颜色和错误类型；
- 同值 patch 返回 `NOOP`，不增加 history；
- 有效 patch 规范化后更新 registry、browser-local persistence 和一条
  `UPDATE_SCENE` Director history；
- 继续由已有 undo/redo 恢复 portable scene document；
- 在 active gesture 时拒绝并保持 zero-mutation。

### 2.3 Scene name draft

场景名称输入使用 DOM draft，不再逐字符写入 Zustand 或 history；Enter/blur
只提交一次。空白提交会产生 typed invalid outcome，并保留上一个有效名称。
为避免 React effect 更新 state 的 lint 风险，外部 undo/redo 同步只更新未聚焦
输入框的 DOM value。

## 3. 证据边界

| 内容 | 证据等级 |
|---|---|
| clone 有 owner/project/session/generation、registry 和 persistence | `CLONE_STATIC_FACT` |
| StoryAI 使用 project/version/session 分层 | `UPSTREAM_INSPIRATION` |
| scene draft、blur/Enter commit 与一条 history | `CLONE_DECISION` |
| LibTV 原站 Director 的 exact project/session DOM、持久化和 history 语义 | `SOURCE_UNKNOWN` |

本批验证通过只能证明 clone-owned prototype reliability，不证明 LibTV 原站
使用相同 schema、技术实现、文案或视觉。

## 4. 验证记录

专项 verifier：

```bash
node scripts/verify-liblib-batch90.mjs
python3 scripts/verify-liblib-batch90.py
```

结果：

- pure/source：12 项断言通过；
- fresh-page Playwright：session diagnostics、draft/commit/no-op/reject、
  persistence、scene toggle/color、undo/redo、mobile Inspector overflow 全部通过；
- browser diagnostics：console/page/request `0 / 0 / 0`；
- current gate：Batch 59、67–90 串行通过；
- `npm run check`、`npm run docs:check`、`python3 scripts/verify-docs.py` 和
  `git diff --check` 均通过；`npm run check` 保留既有 9 条 lint warning；
  结构化结果见 [`current-gate-regression.json`](current-gate-regression.json)。

本批没有新增截图。已有截图解释记录仍是重新识图前的首选证据。

## 5. 已知限制与下一批

- `updateObject`、`updateCamera`、group/timeline/pose 等旧 action 仍有部分
  直接 writer，尚未全部经过统一 typed command/history 入口；
- LibTV source Director 的 project/session、undo/redo、add-camera 默认行为仍
  `SOURCE_UNKNOWN`；
- Batch 91 先迁移对象属性、相机设置和分组创建，重点保证 valid commit 一条
  history、invalid/no-op zero history、registry/persistence 同步和引用安全。
