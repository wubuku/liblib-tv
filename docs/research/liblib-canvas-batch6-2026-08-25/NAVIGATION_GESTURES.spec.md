# 组件规格：LibTV Navigation Gestures

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
| `panOnDrag` | `effectivePan` |
| `selectionOnDrag` | `canvasTool === "select" && !effectivePan` |
| `nodesDraggable` | `canvasTool === "select" && !effectivePan` |
| `panActivationKeyCode` | `null`，由页面维护单一状态 |

## Visual state

- `effectivePan=false`：默认选择 cursor；
- `effectivePan=true`：grab cursor；
- 不添加状态 Toast、说明文字或新工具条。

## Evidence boundary

原站证据确认命令与工具存在，但未保存按键按下/松开时的 class diff。本规格只定义当前 clone 的一致性状态机，不声明精确复制了原站内部事件实现。

