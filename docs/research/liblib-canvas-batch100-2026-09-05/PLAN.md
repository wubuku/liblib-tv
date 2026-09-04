# Batch 100 Plan：空画布状态与快捷生成芯片

> 状态：`PLANNED`
>
> 建档日期：2026-09-05。
>
> 上一批 checkpoint：Batch 99（`batch/99-shortcuts-panel-source`）。
>
> 源站证据：[`../liblib-live-2026-09-05/README.md`](../liblib-live-2026-09-05/README.md) §1（空画布提示与 4 个快捷芯片，`SOURCE_FACT`）。

## 1. 范围

### 包含

1. **空画布状态组件** `CanvasEmptyState`：当工作台模式下当前画布 `nodes.length === 0` 时，画布中央渲染「双击画布 / 自由生成节点」提示行与 4 个快捷芯片：故事脚本生成、角色三视图、全能参考生视频（`SD 2.5`）、音频生视频（`SD 2.5`）。
2. **可达性**：clone 的 `canvas-1` 本就是空画布（fixture catalog §2），通过画布下拉真实切换即可到达；不新增 store/fixture。
3. **芯片点击**：`SOURCE_UNKNOWN`（本轮未采样点击流）；clone 给出诚实本地 status「本地原型：快速生成入口未接入」，不伪造创建。
4. **层级与交互安全**：容器 `pointer-events-none`（不阻断平移/选择），仅芯片与 status 行 `pointer-events-auto`；不进入 graph/history。

### 不包含

- 双击画布的自由生成流程（未采样）；
- 芯片真实生成流（需 fixture 授权与节点能力研究）；
- 故事板模式的空态（源站为 文本/图片/视频 三组，另批处理）。

## 2. 证据边界

| 标签 | 内容 |
|---|---|
| `SOURCE_FACT` | 空态提示两段文案与排布、4 芯片命名与 SD 2.5 角标、芯片位于画布中央偏下 |
| `CLONE_DECISION` | 芯片/status 的视觉近似、点击本地 status、容器 pointer-events 策略 |
| `SOURCE_UNKNOWN` | 芯片点击流、双击生成 UI、芯片 hover/间距精确值 |

## 3. 影响面与兼容

- 新增 `src/components/CanvasEmptyState.tsx`；`page.tsx` 仅加一处条件渲染；
- 不触碰 store/graph/history；storyboard 模式不受影响；
- 空画布上既有 verifier（Batch 24-33 在 `canvas-1` 构造状态）会在空画布上看到该浮层——专项 verifier 复跑 batch24/26 抽查确认不破坏定位/创建。

## 4. 验证

- 新增 `scripts/verify-liblib-batch100.py`：desktop `1440x900`，经画布下拉切到 `canvas-1` → 断言空态提示与 4 芯片（含角标）、芯片点击本地 status、切回 `canvas-2` 空态消失且 graph 保持；mobile `390x844` 无横向溢出；零诊断。
- 复跑 `verify-liblib-batch24.py`、`verify-liblib-batch26.py`（空画布构造路径）。
- `npm run check`、`npm run docs:check`。

## 5. 完成定义

1. 空画布可见源站空态；非空画布与故事板模式不可见。
2. 芯片点击有诚实本地反馈；graph/history 零副作用。
3. 相邻 verifier 与全量检查通过；特性分支 commit/push。
