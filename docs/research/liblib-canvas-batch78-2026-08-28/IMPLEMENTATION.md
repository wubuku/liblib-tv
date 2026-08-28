# Batch 78 实施与验证记录

> 状态：`POINTER_CANCELLATION_AND_R3F_TEARDOWN_RECORDED_PASS`。
>
> 日期：2026-08-28。

## 1. 风险审计

沿用 Batch 71 的 Director gesture/history 合同和 Batch 77 的 R3F pointer
cleanup 结果，对全部 Director 指针入口做了静态检索。确认以下三处需要独立
修复：

| 组件 | 审计结果 |
|---|---|
| `DirectorCurveEditor` | begin 结果未检查；没有 pointer id 过滤、pointercancel、blur、hidden 或卸载清理；结束时无条件 commit |
| `DirectorPhoneVcamPanel` | 姿态盘有 pointer capture，但没有 cancel/失焦/关闭的统一释放路径 |
| `DirectorTimeline` | scrub 只移除 pointermove/pointerup；cancel/失焦/hidden/unmount 后可能留下 stale listener |

截图不是本批必要证据；此前的 `SCREENSHOT_ANALYSIS.md` 与 Batch 77 导航记录
已足够说明当前视觉边界，本批不重复识图、不写截图。

## 2. 代码实施

### 2.1 Curve Editor

`src/components/director/DirectorCurveEditor.tsx`：

- 读取 `beginDirectorGesture` 返回值，只有 `COMMITTED` 才注册 drag；
- 保存触发元素和 pointer id，忽略其他 pointer；
- 以 `dragCleanupRef` 保存当前 cleanup；
- pointerup 调用一次 `commitDirectorGesture`；
- pointercancel、window blur、`visibilitychange=hidden`、lost pointer capture
  和 unmount 调用 cancel；
- cancel 前释放 capture，store cancel 会恢复 gesture baseline，因此曲线不会
  留下半成品，也不会新增 history。

### 2.2 Phone Vcam 姿态盘

`src/components/director/DirectorPhoneVcamPanel.tsx`：

- 保存姿态盘 DOM ref；
- 新增统一 `releasePosePointer`；
- `pointerup`、`pointercancel`、`lostpointercapture`、window blur、页面隐藏和
  panel close 都清理 pointer capture/id；
- 保持姿态更新为 runtime-only，不接入 Director semantic history。

### 2.3 Timeline Scrub

`src/components/director/DirectorTimeline.tsx`：

- 保存 scrub 触发元素和 pointer id；
- 以 `scrubCleanupRef` 管理一次 scrub 的全部 listener；
- pointerup、pointercancel、blur、hidden、lost pointer capture 和 unmount
  均清理；
- scrub 仍只调用 `setTimelineTime`，不创建 Director history；
- 取消后继续移动鼠标不会再次改变 playhead。

### 2.4 R3F Canvas 异步 teardown

跨批 Batch 68 回归发现，Director 在跨 canvas/owner 自动关闭时，R3F `Canvas`
可能在父 DOM 已卸载后才完成异步 `configure`；默认事件源此时为 `null`，
内部 `connect()` 会触发 `null.addEventListener` pageerror。

`src/components/director/DirectorViewport.tsx` 为主视口和方向控件分别增加
稳定的事件源 ref：

- Canvas 挂载时，事件源指向实际可见的 wrapper，因此正常 pointer 行为不变；
- wrapper 卸载时，ref 回落到该 Canvas 实例专属的脱离 DOM fallback；
- 晚到的 R3F 初始化最多连接到这个安全 fallback，不再对 `null` 调用事件 API；
- 没有修改 R3F/node 交互模型，也没有把该 clone-owned 修复写成 LibTV 原站
  的 source fact。

## 3. 专项 verifier

新增 [`scripts/verify-liblib-batch78.py`](../../../scripts/verify-liblib-batch78.py)，
先运行静态 contract，再用 fresh-page Playwright：

| 场景 | 结果 |
|---|---|
| Curve commit | 一条 history，active gesture 清空 |
| Curve pointercancel/blur/hidden | baseline 恢复，0 history，gesture 清空 |
| Curve begin rejected | 不消费已有 owner gesture |
| Phone pointercancel | capture 释放 |
| Phone blur/close | capture/id 清理 |
| Phone pointer reuse | 取消后下一次 pointerdown 可用 |
| Timeline pointercancel | listener 清理 |
| Timeline stale move | cancel 后不再 seek |
| Timeline pointer reuse/hidden | 可再次 scrub，hidden 后 stale move 停止 |
| Diagnostics | console/page/request errors 均为 0 |
| Artifacts | screenshots 为 0 |

运行命令：

```bash
LIBLIB_BASE_URL=http://localhost:3001 \
  python3 scripts/verify-liblib-batch78.py
```

最终专项结构化结果见 [`runtime-audit.json`](runtime-audit.json)，状态为
`SCRIPT_RECORDED_PASS`；跨批串行结果见
[`current-gate-regression.json`](current-gate-regression.json)。

## 4. 静态与专项结果

- `npm run lint`：通过；保留仓库既有 9 条 warning，无新增 error；
- `npm run typecheck`：通过；
- `git diff --check`：通过；
- Batch 78 专项：通过；
- 通过前曾修正两处 verifier 基线问题：
  - rejected begin 场景保留原 owner 的 active 状态，只比较 past/future 与曲线；
  - hidden scrub 以本次 pointerdown 后的 seek 时间作为基线；
- 上述修正没有放宽产品断言。

### 4.1 跨批与全量门禁

2026-08-28 重启唯一的 `localhost:3001` Next dev server 后，按顺序运行：

```text
Batch 59
Batch 67
Batch 68
Batch 69
Batch 70
Batch 71
Batch 72
Batch 73
Batch 74
Batch 75
Batch 76
Batch 77
Batch 78
```

全部 `PASS`。其中 Batch 68 在 R3F fallback 修复后 pageerror 为 0；Batch 77
真实 Director gizmo 拖动和 Batch 78 全部 pointer cancellation 场景均保持
通过。

项目门禁：

- `npm run check`：通过；lint 0 error、既有 9 条 warning、typecheck/build 通过；
- `npm run docs:check`：通过，588 份 Markdown、3495 个本地目标；
- `git diff --check`：通过；
- `python3 -m py_compile scripts/verify-liblib-batch77.py scripts/verify-liblib-batch78.py`：通过。

## 5. 待完成门禁

- [x] 三处 pointer lifecycle 风险审计；
- [x] Curve/Phone/Timeline 修复；
- [x] R3F Canvas 异步 teardown 修复；
- [x] Batch 78 专项 verifier；
- [x] `runtime-audit.json` 结果落档；
- [x] 跨批回归：Batch 59、67-78；
- [x] `npm run check`、`npm run docs:check`；
- [x] 更新治理台账；
- [x] checkpoint commit/push，确认工作区干净。

## 6. 边界与后续

本批没有把所有 Director 组件重构成通用 pointer hook，也没有改变普通画布
导航。完成全量门禁后，下一批应优先评估：

1. Director whole-project duplicate 的 owner/resource/history 事务；
2. durable tombstone、storage/resource cleanup 的明确合同；
3. ordinary canvas media ingress/async/editor session 中仍缺的 current runtime
   slice。

选择下一项前必须重新检查 source evidence、fixture 前提和现有
`LIBTV_UIUX_PARITY_BACKLOG.md`，不能把 clone-only Director pass 当成 LibTV
source parity。

本批完成后只留下下一批计划，不在同一批继续实施。
