# Batch 94 实施与验证记录

> 状态：`FOCUSED_RUNTIME_RECORDED_PASS`
>
> 日期：2026-08-29。
>
> 实施 checkpoint：`15e8226`（已推送）。

## 1. 代码变更

| 文件 | 变更 |
|---|---|
| [`src/components/director/useDirectorFocusContainment.ts`](../../../src/components/director/useDirectorFocusContainment.ts) | 新增可复用 focus scope hook：动态 tabbable 过滤、Tab/Shift+Tab 循环、初始焦点、回焦目标和 canvas/workspace fallback。 |
| [`src/components/director/DirectorDesk.tsx`](../../../src/components/director/DirectorDesk.tsx) | 接入 workspace、mobile tree 和 Inspector 三个 scope；为非活动移动抽屉增加 `aria-hidden`/`inert`；统一移动抽屉关闭和 Director 关闭回焦；修复移动抽屉 Escape 被 editable guard 吞掉的问题。 |
| [`scripts/verify-liblib-batch94.py`](../../../scripts/verify-liblib-batch94.py) | 新增 desktop/mobile fresh-context verifier，覆盖焦点循环、回焦、编辑边界、inert、ARIA、overflow 和 zero diagnostics。 |

## 2. Clone-owned 行为合同

### 2.1 Workspace

- Director 是唯一顶层 `role="dialog"`；
- workspace 打开后获得焦点；
- 当前可见、未禁用控件组成动态 tabbable 集合；
- `Tab` 和 `Shift+Tab` 都不会离开 workspace；
- 打开或关闭动态面板后，下一次遍历重新计算集合。

### 2.2 移动抽屉

- tree 和 Inspector 属于同一个 Director workspace，不创建第二个顶层 dialog；
- 非活动或折叠抽屉同时使用 `aria-hidden` 与 `inert`；
- 抽屉打开后焦点进入抽屉内；
- backdrop、Escape、close button 关闭后焦点回到原触发按钮；
- 抽屉活动时，Escape 在 Director workspace 命令处理之前关闭抽屉。

### 2.3 异常回退

回焦顺序为原触发元素、普通画布 focus root、Director workspace。目标已卸载、
禁用、隐藏或不可见时，不把焦点留在 document body。

## 3. 专项验证

命令：

```bash
LIBLIB_BASE_URL=http://localhost:4317 \
  python3 scripts/verify-liblib-batch94.py
```

结果：

- desktop `1440x900`：workspace 初始焦点、正/反向 Tab 循环、编辑输入框边界、
  close button/Escape 回焦、overflow 和 diagnostics 通过；
- mobile `390x844`：tree/Inspector 局部循环、非活动 peer `inert`、backdrop/Escape
  回焦、折叠 rail `inert`、overflow 和 diagnostics 通过；
- desktop/mobile console errors、page errors、request failures 均为 `0/0/0`；
- `screenshotsWritten=false`，未执行截图识别。

结构化原始结果见 [`runtime-audit.json`](runtime-audit.json)。

## 4. Director current-gate 回归

在固定 `localhost:4317` 服务上，本批重新运行并通过：

```text
Batch 59、67、68、69、70、71、72、73、74、75、76、77、78、79、80、
Batch 81、82、83、84、85、86、87、88、89、90、91、92、93
```

这些结果证明 Batch 94 没有破坏当前 Director project/session、command/history、
resource、selection、TransformControls、scene command 或 Batch 93 桌面/移动端
回归边界。详细序列见 [`current-gate-regression.json`](current-gate-regression.json)。

## 5. 普通画布回归边界

Batch 93 已记录普通画布 `57/60/61/63/64/65/77` 的完整通过序列。本次为了确认
Batch 94 影响边界，额外完成了 Batch 57、60 和隔离重试的 Batch 64；Batch 64
首次嵌入较长序列时在 stale-canvas 断言处出现一次 `committed` 而非预期
`skipped`，单独 fresh-process 重试通过，未确认产品回归。

随后重复回归在用户明确要求 Batch 93 后停止自动循环时停止，Batch 61 的第二次
执行在 Playwright `page.mouse.down()` 处被中断。该事件不改变已提交代码，也不
应被记为 Batch 61 失败；本批台账保留“继承 Batch 93 的完整通过 + 本次有限
spot check”的双层事实。

## 6. 证据与停止边界

本批不新增截图，不重新识别已有截图，也不声称 LibTV 原站采用完全相同的
focus trap、`inert`、DOM、CSS 或键盘实现。Batch 94 只描述当前 clone-owned
Director reliability。

用户要求本批收口后停止，因此本批之后不启动下一批，不继续运行被中断的普通
画布重复序列，也不自动规划新的复刻任务。
