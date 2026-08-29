# Batch 86：Director 变换目标上下文与取消清理

> 状态：`SCRIPT_RECORDED_PASS`。
>
> 建档日期：2026-08-29。
>
> 本批是 clone-owned Director 可发现性与输入生命周期改进，不是 LibTV
> 原站 Director source-exact 结论。

## 入口

- [`PLAN.md`](PLAN.md)：实施范围、证据边界和验收条件；
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：代码变更、验证命令和回归结果；
- [`runtime-audit.json`](runtime-audit.json)：fresh-page Playwright 结构化结果；
- [`../../CANVAS_NAVIGATION.md`](../../CANVAS_NAVIGATION.md)：普通画布导航权威；
- [`../liblib-canvas-batch77-2026-08-28/`](../liblib-canvas-batch77-2026-08-28/)：
  TransformControls explicit attachment 与真实拖动合同；
- [`../liblib-canvas-batch78-2026-08-28/`](../liblib-canvas-batch78-2026-08-28/)：
  Director pointer cancellation 与 R3F teardown 合同；
- [`../liblib-canvas-batch84-2026-08-29/`](../liblib-canvas-batch84-2026-08-29/)：
  locked-target 编辑保护；
- [`../LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md`](../LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md)：
  当前 Director verifier 入口。

## 本批结论

- 变换工具栏现在投影当前目标、目标类型和可编辑状态；
- 无选择、多选、对象、分组、路径锚点、路径绘制、截图/手机录制等状态均有
  稳定的 DOM/ARIA 目标上下文；
- 普通对象和分组的 `TransformControls` 增加显式
  `pointercancel`/`lostpointercapture` 清理；
- 真实 gizmo 拖动仍由显式 attachment、`authoredObjects`、runtime projection
  和 Director gesture/history 共同承担；
- 锁定对象的变换直接调用仍返回 `DIRECTOR_TARGET_LOCKED`，不产生 document 或
  history mutation；
- 移动端工具栏上下文不溢出，fresh-page 诊断为零。

## 证据边界

| 标签 | 本批含义 |
|---|---|
| `CLONE_FACT` | 当前 clone 的 R3F 控制器、目标选择、Inspector 和 store contract |
| `CLONE_DECISION` | 以紧凑目标上下文提升“选中后如何移动”的发现性，并统一取消清理 |
| `SOURCE_UNKNOWN` | LibTV 原站 Director 是否有相同目标上下文、文案、ARIA、gizmo 或拒绝提示 |
| `UPSTREAM_INSPIRATION` | StoryAI/现有 clone 的 Director 组织方式仅作借鉴 |

本批没有重新识别截图，也没有把 StoryAI 或 clone 的 Director UI 反推为
LibTV 原站事实。
