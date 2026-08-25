# LibTV 画布 Batch 6 计划：导航手势闭环

> 建档日期：2026-08-25  
> 原则：只实现原站已公开且当前克隆确实宣传的导航命令；用依赖源码确认交互冲突，不靠猜测。

## 1. 缺口盘点

| 候选缺口 | 当前克隆 | 证据 | 价值 | 本批决策 |
|---|---|---|---:|---|
| Space 临时抓手 | 面板展示，页面无状态 | 原站快捷键直接证据 | 5 | 实现 |
| V 选择/移动工具 | 可切换 `select`，但 pane 仍可平移 | 原站快捷键直接证据 + 当前代码 | 5 | 修正 |
| H 抓手工具 | 节点不可拖，但与 pane 默认状态差异有限 | 原站快捷键直接证据 + 当前代码 | 5 | 修正 |
| 框选 | `selectionOnDrag` 已开，但被固定 `panOnDrag` 覆盖 | xyflow v12 源码 | 5 | 恢复并验证 |
| 输入焦点守卫 | keydown 守卫存在，Space 尚未接入 | 当前代码 | 4 | 实现 |
| 失焦恢复 | 无临时状态 | 浏览器键盘生命周期 | 4 | 实现 |
| 右键拖动画布 | 未实现 | 无当前原站直接证据 | 2 | 暂缓 |
| 自定义触控板算法 | React Flow 原生滚轮/缩放已可用 | 原站只展示入口文案 | 2 | 不做 |

## 2. 实施范围

### P0

1. 页面增加 `isSpacePressed` 临时状态；
2. 非输入焦点下 `Space` keydown：
   - 阻止页面滚动；
   - 进入临时抓手；
3. `Space` keyup、窗口 blur：
   - 清除临时抓手；
4. `effectivePan = canvasTool === "pan" || isSpacePressed`；
5. `panOnDrag`、`selectionOnDrag`、`nodesDraggable`、cursor 均由 `effectivePan` 协调；
6. 关闭 React Flow 内建 `panActivationKeyCode`，避免两套键盘状态叠加；
7. `H` 持久切换 pan，`V` 持久切换 select；
8. Space 不改变持久 `canvasTool`。

### P1

1. 输入框、textarea、contenteditable 内 Space 不触发临时抓手；
2. 框选与 Meta/Control 多选保持兼容；
3. 临时抓手期间不拖动节点、不出现 selection rectangle；
4. 释放 Space 后立即恢复选择工具语义。

## 3. 不做

- 不记录 Space 状态到 Zustand；
- 不把 pane drag 写入 graph history；
- 不改变现有 `panOnScroll` / `zoomOnScroll`；
- 不增加可见教程文字；
- 不实现触摸端 Space 替代控件；
- 不修改快捷键面板中没有直接行为闭环的命令。

## 4. 验收标准

### 选择工具

- 初始工具为 select；
- 空白左键拖动创建 selection rectangle，而不是平移 viewport；
- 框选覆盖节点后至少选中目标节点；
- 节点可拖动。

### 抓手工具

- 按 `H` 后 pane 左键拖动平移 viewport；
- 节点不可拖动；
- 按 `V` 后恢复选择和节点拖动。

### Space 临时抓手

- select 工具下按住 Space，pane 左键拖动平移 viewport；
- 松开 Space 后持久工具仍为 select；
- 松开后空白拖动重新框选；
- 输入框内 Space 不进入临时抓手；
- 窗口失焦后不残留抓手状态。

### 回归

- Batch4、Batch5 验证继续通过；
- 桌面 `1440x900`、移动 `390x844` 无溢出；
- 控制台错误为 0；
- `npm run check` 通过；
- FrameOS 构建不回归。

