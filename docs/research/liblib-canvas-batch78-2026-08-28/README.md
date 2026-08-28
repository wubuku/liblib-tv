# Batch 78: Director Pointer Cancellation and Cleanup

> 状态：`FOCUSED_RUNTIME_RECORDED_PASS`。
>
> 建档日期：2026-08-28；实施前代码基线：`8e59409`。

## 1. 目标

Batch 77 修复了 R3F `TransformControls` 的真实拖动绑定，但代码审计发现
三个相邻 Director DOM/runtime 手势仍缺少完整的中断清理：

- Curve Editor 只监听 `pointermove`/`pointerup`，且没有检查 gesture begin 结果；
- 手机虚拟相机姿态盘在 `pointercancel`、失焦或关闭时可能保留 capture/pointer id；
- Timeline scrub 在取消、失焦、页面隐藏或卸载后可能继续响应 stale pointermove。

本批只修复 clone-owned 指针生命周期，不改变视觉、时间轴数据模型、手机
runtime-only 语义或 LibTV 未核实的 source-exact 行为。

## 2. 入口

- [`PLAN.md`](PLAN.md)：范围、验收条件和停止条件；
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：代码改动、专项运行和回归结果；
- [`runtime-audit.json`](runtime-audit.json)：无截图的结构化运行记录；
- [`../../CANVAS_NAVIGATION.md`](../../CANVAS_NAVIGATION.md)：普通画布导航入口；
- [`../liblib-canvas-batch71-2026-08-27/`](../liblib-canvas-batch71-2026-08-27/)：
  Director 原有 gesture boundary 合同；
- [`../LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md`](../LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md)：
  Director command/history/cancel 权威。

## 3. 当前结果

- Curve Editor：commit 一条 history；pointercancel、blur、hidden、卸载均取消并
  恢复 baseline；begin rejected 不消费已有 owner gesture；
- Phone Vcam：姿态盘 pointercancel、blur、关闭后释放 capture，下一次 pointer
  仍可使用；姿态保持 runtime-only；
- Timeline：scrub pointercancel、hidden 后不再响应 stale pointermove，完成后
  可再次 scrub，且不引入 Director history；
- Batch 78 专项 Playwright：`SCRIPT_RECORDED_PASS`；
- 截图：0；console/page/request errors：0。

## 4. 证据边界

这些结果证明当前 clone 的指针生命周期合同，不证明 LibTV 原站 Director 的
DOM/CSS、内部事件实现、真实手机陀螺仪或真实资源/provider 行为。普通画布
鼠标/触摸板导航仍以 Batch 77 的源站 runtime audit 和
[`CANVAS_NAVIGATION.md`](../../CANVAS_NAVIGATION.md) 为准。

