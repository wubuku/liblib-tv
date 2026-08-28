# 组件规格：LibTV Navigation Gestures

> 历史规格：其中的 `Space` / `V` / `H` 状态机仍是当前 clone 的基础，
> 但本页原先定义的选择工具空白框选已被 Batch 77 的登录态源站 runtime
> audit supersede。当前普通画布导航以 [`docs/CANVAS_NAVIGATION.md`](../../CANVAS_NAVIGATION.md)
> 和 [`SOURCE_NAVIGATION_AUDIT_2026-08-28.md`](../liblib-canvas-batch77-2026-08-28/SOURCE_NAVIGATION_AUDIT_2026-08-28.md)
> 为准。

## Goal

把原站快捷键面板公开的三种导航模式实现为明确状态机：

- `V`：持久选择/移动工具；
- `H`：持久抓手工具；
- `Space`：仅按住期间生效的临时抓手。

## State model

```ts
const [isSpacePressed, setIsSpacePressed] = useState(false);
const effectivePan = canvasTool === "pan" || isSpacePressed;
```

`canvasTool` 属于持久 UI 状态；`isSpacePressed` 是页面瞬时状态，不进入 Zustand。

## Keyboard lifecycle

### keydown

- 输入焦点为 `input`、`textarea`、`contenteditable` 时直接返回；
- `Space`：
  - `preventDefault()`；
  - 非 repeat 首次按下进入临时抓手；
- `H`：持久设置 `canvasTool = "pan"`；
- `V`：持久设置 `canvasTool = "select"`。

### keyup

- `Space` 总是清除临时抓手；
- keyup 不受输入焦点守卫限制，避免焦点在按住期间变化后残留状态。

### blur

- `window.blur` 清除临时抓手；
- 页面切到后台后返回不应保持 grab cursor。

## React Flow props

| Prop | Value |
|---|---|
| `panOnDrag` | `effectivePan ? [0, 1] : [1]`，中键始终平移；抓手状态额外允许左键 |
| `selectionOnDrag` | `false`，当前源站 runtime 未显示空白框选 |
| `nodesDraggable` | `canvasTool === "select" && !effectivePan` |
| `panActivationKeyCode` | `null`，由页面维护单一状态 |
| `panOnScroll` | `true`，普通滚轮/触摸板滚动平移 |
| `panOnScrollSpeed` | `1`，与当前源站滚轮平移比例对齐 |
| `zoomOnScroll` | `true`，modifier/pinch wheel 进入缩放路径 |

## Visual state

- `effectivePan=false`：默认选择 cursor；
- `effectivePan=true`：grab cursor；
- `V` 下空白左键拖动 no-op，不声明框选；
- 不添加状态 Toast、说明文字或新工具条。

## Evidence boundary

原站证据确认命令与工具存在，但未保存按键按下/松开时的 class diff。本规格只定义当前 clone 的一致性状态机，不声明精确复制了原站内部事件实现。
