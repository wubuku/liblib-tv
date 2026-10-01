# Batch 365 — 画布右键菜单关不掉, 而且会跟着鼠标跑

## 立项依据

Batch 364 建的覆盖普查(`probe_liblib_batch364_coverage.py`)报 PARTIAL = 10,
逐个核实漏网标记时落到 `CanvasContextMenu` 的 `canvas-context-backdrop` ——
它是该组件**唯一**没被任何门禁引用的标记:

| 标记 | 覆盖它的门禁 |
|---|---|
| `canvas-context-menu` | 172 / 173 / 179 / 185 / 187 |
| `canvas-context-item` | 172 / 173 / 179 / 185 / 187 |
| `canvas-context-variant` | 172 / 173 |
| **`canvas-context-backdrop`** | **无** |

菜单的打开/尺寸/项序/快捷键都验了, **唯独漏掉「点了菜单外面会关掉」** ——
而这恰恰是菜单唯一的逃逸方式。

## 缺陷

菜单开在 (1123,738), 在 (300,250) 右键 → 菜单**跳到 (300,250) 重新出现**
(`sameNode=False`, 是重建的)。用户右键想取消, 菜单不但关不掉, 还跟着鼠标跑。

根因: 浏览器一次右键依次派发 `mousedown` → `contextmenu`。backdrop 的
`onMouseDown` 调了 `onClose` → **菜单连同 backdrop 立刻卸载** → 随后的
`contextmenu` 落到**已不存在的 backdrop 之后**, 直接命中 `.react-flow__pane`,
React Flow 的 `onPaneContextMenu` 在新位置把菜单重开。

关键实测(把两个事件拆开派发):

| 派发方式 | 结果 |
|---|---|
| 只 `contextmenu` | 菜单**关闭** ✅ |
| 完整右键序列 | 菜单**重开** ❌ |

## 修复绕了五个错方向才找到根因

前四轮都在改「怎么拦 contextmenu」, 全部无效。逐个记录, 因为它们都**看起来
很有道理**:

1. **backdrop 加 `stopPropagation`** —— 无效。React 17+ 事件委托到 root。
2. **`page.tsx` 的 pane handler 加 `if (canvasContextMenu) return`** —— 无效。
   React Flow 的 handler 走缓存闭包, 读到的是打开前那次渲染的 `null`。
   改成 ref 读最新值后**仍然无效**(这个 ref 改动最后证明也不需要)。
3. **改用 document 捕获阶段 + `stopImmediatePropagation`** —— 反而更糟。
   实测对照: `stopPropagation` 让 pane 收到 **0** 次(菜单关闭 ✅),
   加上 `immediate` 后 pane 收到 **1** 次(菜单重开 ❌) ——
   `stopImmediatePropagation` 只停掉「同一节点上其他监听器」, 而 React 的委托
   监听在**子节点**上, 照样收得到冒泡上去的事件。
4. **查 DOM 祖先链** —— 发现 pane 在 `main` 下而**不在 `#__next` 里**,
   属于另一个 React 根, 委托注册更早。这解释了为什么 backdrop 侧拦不住,
   但**没直接导向修法**。

第五轮才测出真正的差异: 拆开派发事件。**根因是事件时序(mousedown 提前卸载
backdrop), 不是事件传播**。前四轮全在错误的维度上用力。

## 最终修法

```ts
// mousedown: 右键不在这里关, 只吃掉默认行为
if (event.button !== 2) closeRef.current();
// contextmenu: 这里才是右键的关闭入口(此时 backdrop 还在)
event.stopPropagation();
closeRef.current();
```

加上 `onClose` 用 `useRef` 固定(它每次渲染都是新引用, 直接进 `useEffect`
依赖会导致反复重挂, 存在监听短暂缺席的窗口)。

## 修完立刻踩到自己引入的回归

第一版修完, batch172 / batch173 直接红:

- `menu:add-node-opens-panel` —— 点「添加节点」后菜单没关
- `duplicate:adds-node` —— 同上

因为监听挂在 **document**, 连**菜单项自己**的点击也吃掉了(`insideMenu` 判据
是后加的)。加 `insideMenu(event)` 放行菜单内事件后, 6/6 回归全过。

> **过滤器必须双向验证**: `insideMenu` 既不能漏放菜单项(会打破 172/173),
> 也不能误放菜单外(会退回本缺陷)。172/173 绿 + batch365 绿, 两侧同时成立
> 才算判据可用。

## 门禁 7 项 + 变异

1. 防假零: 菜单**必须真的打开**才测关闭(打不开直接红, 不许报 0 问题);
2. backdrop 必须存在, 且**盖住整个视口**、在菜单**之下**;
3. 关闭路径 A: 左键点菜单外 → 关闭;
4. 关闭路径 B: 右键点菜单外 → 关闭;
5. 无「关掉又弹回」的重开循环。

变异: 把 `if (event.button !== 2)` 去掉(退回原始缺陷) → exit=1, 精确红在
`close:right-click-outside` + `close:no-reopen-loop`。**门禁抓得住真回归。**
