# batch 753 — 画布多选态可达性 + 选择/图记账命令真跑：一条挂了很久的伪结论被推翻

## 起点

台账里躺着一行很硬的待拍板项：

> 【拍板】多选态（`selectedNodeCount>1`）下 16 个画布命令全部不可达 —— 要不要补一格测

同时「33 个记账命令里还剩 14 个未真跑」，其中 6 个是选择类命令
（`duplicateSelectedNodes` / `removeSelectedNodes` / `groupSelectedNodes` /
`ungroupSelectedNodes` / `removeEdge` / `setNodes`+`setEdges`）。

这两件事其实是同一件事：**如果多选真不可达，那 6 个命令就只能测 N=1 那一档**，
测出来的记账结论是残的。所以本批先回答「多选到底能不能到」，再把命令逐个跑完。

---

## 一、静态层先摆出矛盾

我在 `src/` 里读到的东西**全部指向「多选不可达」**：

| 证据 | 位置 | 读出来的话 |
|---|---|---|
| `selectNode` 只写单元素 | `store/canvasStore.ts`（`nextSelectedNodeIds = validNodeId ? [validNodeId] : []`） | 永远 ≤1 |
| `onNodeClick` 带修饰键时什么都不做 | `app/page.tsx:1473` `if (!event.metaKey && !event.ctrlKey) selectNode(node.id)` | 加选被短路 |
| `selectNodes(ids)` / `selectEdges(ids)` | 全项目 **0 个调用点** | 两个死 action |
| `selectElements` 的两处调用 | `page.tsx:1338`、`page.tsx:1476` | **都传空数组** |
| `selectionOnDrag={false}` | `app/page.tsx:1552` | 框选也是关的 |

**但**同一份源码里还有一条相反的路：`routeReactFlowChanges` 会处理 ReactFlow
自己的 `select` 变更（`lib/libtvReactFlowChangeRouting.ts:197`/`:327`），
经 `applySelectionDelta` **toggle** 进 `selectedNodeIds`。

声明 vs 实现。**只有实跑能分。** 于是有了这一批。

---

## 二、结论：多选可达，而且有两条独立入口

### 入口一：`Cmd + 点击`（macOS）

| 手势 | `selectedNodeIds.length` |
|---|---|
| 裸点 A | 1 |
| 裸点 A → **`Meta` + 点 B** | **2** |
| 裸点 A → `Ctrl` + 点 B | 1（替换） |
| 裸点 A → `Shift` + 点 B | 1（替换） |

**只有 Meta 能加选。** 不是 Shift，不是 Ctrl，也没有第二条加选路径。

### 入口二：`Shift + 拖` 框选

从左上空白点拖到右下空白点 ⟹ `selectedNodeIds.length === 10`，**一次选满整张画布**。
`selectionOnDrag={false}` 与此不矛盾：那是「不按修饰键、直接拖也框选」，
`Shift+拖` 是另一条路。

### 入口三（意外收获）：命令自身的结果

`ungroupSelectedNodes` 解组之后把 `selectedNodeIds` 设成**全部子节点**
（`canvasStore.ts:3360`）⟹ **不用任何修饰键**也能落进多选态。

⟹ 台账那行「16 个命令在多选态下全部不可达」是**伪结论**，撤回。
准确说法是：**多选可达，但只有 Meta+点击、Shift+框选、解组这三条入口**，
其中两条是平台/手势相关的单点。

---

## 三、`Cmd+D` 的 N 分支：一个能证伪的差分

`canvasStore.ts:3166` 这一行是本批最值得测的地方：

```ts
const result = duplicateGraphSelection(
  currentCanvas, requestedIds,
  requestedIds.length === 1 && !includesGroup,   // ← includeExternalEdges
);
```

而 `duplicateGraphSelection` 里边的边过滤是：

```ts
includeExternalEdges ? (sourceCopied || targetCopied)
                     : (sourceCopied &&  targetCopied)
```

⟹ **N=1 复制「所有碰到它的边」，N≥2 只复制「两端都在选区里的边」。**

用同一个靶点 `i-1FQ9tErTcC`（实测边度数 **3**）做两档：

| 档 | 选中 | 节点增量 | 边增量 | 与实现对账 |
|---|---|---|---|---|
| N=1 | `i-1FQ9tErTcC` | **+1** | **+3** | 3 = 它的全部度数 ✅ |
| N=2 | ＋ `b-bTLLuU4w5q` | **+2** | **+1** | 1 = 两端都在选区的那一条 ✅ |

差分与实现**逐字对平**。这条判据是可证伪的：任何一边改了过滤条件，N=2 那一格立刻会跳。

---

## 四、六个命令逐个跑通 + 记账对账

### `groupSelectedNodes` —— 硬门是真的

`canvasStore.ts:3269` `if (children.length < 2) return state`。

- 选 **1** 个按 `G` ⟹ `nodes` / `edges` / `past` **三项全零变化**（`noop=true`）
- 选 **2** 个按 `G` ⟹ 节点 **+1**、边 **±0**、`past` +1、选中集**塌回 1**

新组节点的几何可以逐项算出来（`GROUP_PADDING = 32`）：

| 项 | 实现算出的值 | 实测 | |
|---|---|---|---|
| `x` | `minX - 32` = 132−32 | **100** | ✅ |
| `y` | `minY - 32` = −187−32 | **−219** | ✅ |
| `w` | `maxX−minX+64` = 1418−132+64 | **1350** | ✅ |
| `h` | `maxY−minY+64` = 623−(−187)+64 | **874** | ✅ |

`title=组合节点`、`groupKind=selection`、`zIndex=-1001` 也都读到了。

### `ungroupSelectedNodes` —— 多选的第三条入口

`Shift+G` ⟹ 节点 −1 回到 10，`selectedNodeIds` = **两个子节点**。

### `removeSelectedNodes` —— 边的归属可以预判

选 A+B 按 `Delete` ⟹ 节点 **−2**、边 **−8**，存活 3 条：

```
e-VQACH36eJC   i-dnwoQ7jsG → v-UGQZzZOpbv
e-XmiJkHfFAL   i-YDfWhFlthe → v-UGQZzZOpbv
e-xNVTHNFZZl   i-dnwoQ7jsG → i-YDfWhFlthe
```

11 条边里另外 8 条**至少一端在选区** ⟹ 与静态逐条数的清单一致。

### `withDescendantIds` 级联

选**含 1 个子节点的分组** `g-EFbbHpwq5w` 按 `Delete`：

- 节点 **−2**（分组 + `v-UGQZzZOpbv`）
- 边 **−4** = 子节点挂的 3 条 + **分组自身挂的 1 条**（`e-yEqrTOR2Ya`）
- 另一个分组 `g-245IDFh8sB` 还在

### `removeEdge` —— 静态担心的死锁不成立

我在静态层担心过一条死锁链：

> 按钮未激活时 `pointer-events: none` ⟹ 收不到自己的 `mouseenter` ⟹ 永远不激活；
> 而 `app/page.tsx` **没有 `onEdgeClick`** ⟹ 边选不中 ⟹ `selected` 永远 false。

**运行时点边真的选中了**（`selectedEdgeIds` 含 `e-8IgMkf6Vbj`）——
ReactFlow 的内部 `select` 变更不走 `onEdgeClick`，它走 `onEdgesChange` →
`routeReactFlowChanges`。于是按钮解禁：

| | 点边前 | 点边后 |
|---|---|---|
| `opacity` | `0` | **`1`** |
| `pointer-events` | `none` | **`auto`** |
| 命中测试 `topIsBtn` | `false` | **`true`** |
| 包围盒 | 6×6 | 12×12 |

点它 ⟹ 边 **−1**、`past` **+1**、该边从选中集清空、
`document.body.dataset.hoverEdge` 副作用也在（753f 悬停时读到 `'e-8IgMkf6Vbj'`）。

### `setNodes` —— 两个真入口

| 入口 | 读数 |
|---|---|
| 拖动节点（3 个不同抓点） | **3/3 `moved=true`**、`past` 各 +1 |
| `Alt+Shift+F` 整理 | **9/10** 节点位置变、`past` +1、出现「**还原**」48×32 按钮 |

### `setEdges` —— 零调用点的死 action

静态普查：`canvasStore.setEdges` 在全应用**只剩声明 `canvasStore.ts:387`
与实现 `:3415`**，所有 `setEdges` 引用都指向 `frameosStore` 的同名 action。
本批所有操作跑完后边数组只被 `duplicateSelectedNodes` / `removeEdge` /
`removeSelectedNodes` 改过，**没有任何一条路径走 `setEdges`**。

和 `duplicateNode` / `removeNode` 是同一族问题：store 里实现了、UI 里没有入口。

---

## 五、顺带坐实的一条机制：平移是**中键**

`app/page.tsx:1550`：

```tsx
panOnDrag={effectivePan ? [0, 1] : [1]}
```

ReactFlow 的 `panOnDrag` 收的是**鼠标键号数组**（0=左 1=中 2=右），不是布尔。
默认 `canvasTool="select"` 且 `isSpacePressed=false` ⟹ `panOnDrag=[1]` =
**只有中键能平移**。三格对照：

| 手势 | viewport 变化 |
|---|---|
| 中键拖 pane | **变** |
| 左键拖 pane（默认工具） | 不变 |
| `Space` + 左键拖 pane | **变**（`effectivePan` 转 true，`panOnDrag=[0,1]`） |

753c 早就读到「裸拖不 pan / Space+拖 pan」这组读数，一直是对的 ——
**本批补上的是机制，以及漏掉的中键那一格。**

---

## 六、判据

**13 条，两轮一致**（轮间整页 `reload` ⟹ zustand 回到种子 10 节点 / 11 边，两轮互相独立）。
唯一在原始比对里跳出来的字段是 `group_geom.id`，它来自
`createNodeId()` = `group-${Date.now()}-${random}`，按「异步过程值不能进两轮比对」
的规矩剔除；几何本身（`x/y/w/h/title/kind/z/children`）两轮逐项相同。

| # | 判据 | 关键读数 |
|---|---|---|
| 1 | `Meta+点击` 可加选 | `n: 1 → 2` |
| 2 | 只有 Meta 累加 | `Ctrl=1` / `Shift=1` / `Meta=2` |
| 3 | `Shift+拖` 框选可选满 | `n = 10` |
| 4 | `Cmd+D` 的 N 分支差分 | N1 边 **+3** / N2 边 **+1** |
| 5 | `G` 的 `children.length<2` 硬门 | `noop=true`、`pastDelta=0` |
| 6 | 组节点几何 = 包围盒 ± 32 | `100 / −219 / 1350 / 874` |
| 7 | 解组是第三条多选入口 | `ungroup → n=2` |
| 8 | 多选删除的边归属 | 存活 **3** 条，与静态清单一致 |
| 9 | `withDescendantIds` 级联 | 节点 **−2**、边 **−4** |
| 10 | `removeEdge` 可达 + 按钮真门 | `opacity 0→1`、`pe none→auto`、边 **−1** |
| 11 | `setNodes` 两个真入口 | 拖动 **3/3**、整理 **9/10** + 「还原」48×32 |
| 12 | `setEdges` 零调用点死 action | 只剩 `:387` 声明与 `:3415` 实现 |
| 13 | `panOnDrag=[1]` 是中键 | 中键**变** / 左键**不变** / Space+左键**变** |

---

## 七、探针与验收器返工七处（**全是我自己的错**）

| # | 批次 | 错在哪 | 规矩 |
|---|---|---|---|
| **R1** | 753a | 把**被子节点覆盖**的分组几何中心当第二个靶子 ⟹ `Meta`/`Ctrl`/`Shift`/裸点四次手势**实际命中同一个元素**，整轮作废 | 真实鼠标交互的坐标来源不能是不可见/被覆盖的元素；每个坐标先过 `elementFromPoint` 断言 `topId === 目标` |
| **R2** | 753b | 拖拽起点 `(30,30)` **落在节点上** ⟹ 「框选无效」「裸拖不平移」两格都作废 | 起拖点先扫描出一批经 `elementFromPoint` 验证确实在 `.react-flow__pane` 内的空白点 |
| **R3** | 753c | 框选两个端点 **y 都是 50** ⟹ 框高 **2px**，扫不到任何节点 ⟹ 「框选无效」是伪结论 | 「没变化」必须分层归因；手势类读数要先验选框**本身有面积** |
| **R4** | 753f | 拖动循环 `pg.mouse.move(x+60, y+40)` **目标点没乘 `i`** ⟹ 指针一次跳到位，ReactFlow 拿不到中间 `pointermove`，把拖动读成了点击 ⟹ 误判「节点拖不动 / `setNodes` 走不通」 | **先怀疑探针再怀疑产品**；拖动类读数要打印实际命中元素与逐步轨迹 |
| **R5** | 753e | 口头预判写成「剩 **4** 条边」，清单是 **3** 条 | 预判清单和口头数字必须一起写；自己审计里的数字要互相对账 |
| **R6** | 753f | 静态认定删边按钮是**死代码**（「没有 `onEdgeClick` ⟹ 边选不中 ⟹ 死锁」）⟹ 运行时点边真选中了 | 断言「某能力不可达」前先穷举它的全部命名形态与**全部中间态**；ReactFlow 的内部选择是第二条变更通道 |
| **R7** | 753 验收器 | 验收器**第一版 43 项里 5 个 ❌**，其中 3 个是静态扫描只按**文件名**排除 `frameosStore.ts`/`jimengStore.ts`、漏了 frameos 的路由页 `src/app/frameos/canvas/[id]/page.tsx`（那本来就是 frameos 的同名 action）；另两个是删边按钮门的正则按单行写（源码是三元里的换行字面量）、「解掉挂起项」那条按我以为的措辞做子串匹配 | 静态断言的「排除范围」要按**功能树**排除（frameos / jimeng 各自是 store + 路由页 + 组件一族），不是按文件名；按文本匹配的断言先看真实源码字面量再写 |

R4 与 R6 是同一类错误的两个方向：R4 是**读数无效被当成产品缺陷**，
R6 是**静态推理被运行时推翻**。
R7 则是第三类：**验收器自己没全绿** —— 43 项跑出来 5 个 ❌ 时，
必须逐条归因到「探针错 / 判据错 / 产品错」三类之一，而不是改判据去迁就。


---

## 八、待拍板（需改 `src/`，等授权）

1. **`setEdges` 删掉还是接上？** 零调用点的死 action，与 `duplicateNode` /
   `removeNode` 同族。接上的话至少要有一条真实路径（比如把某条从
   `routeReactFlowChanges` 改走 `setEdges`）。
2. **`duplicateNode` / `removeNode` 同上** —— 静态零入口，本批没为它们做运行时穷举。
3. **多选只有 `Meta+点击` 一条加选路径** —— Windows/Linux 的用户没有等价的
   `Ctrl+点击`。源站是什么手势没验（本批没做源站对照）。
   要不要补 `Shift+点击` 或框选之外的第三条？
4. **平移只有中键 + Space** —— 触屏用户和没有中键的鼠标用户怎么平移？
   源站行为待验。
5. **`Cmd+D` 的 N 分支差异要不要在 UI 上说清楚** —— 单选复制会带上所有邻边、
   多选只带内部边，这个差异用户看不到。

---

## 九、不声称

- 只用了 `canvas-2` 这一张种子画布；另一张空画布 `canvas-1` 本批没纳入。
- 多选只验到 **N=2** 与 **N=10** 两档；N=3..9 的边归属规则未逐档实测。
- 框选只验了「覆盖全画布」这一档；**半选**（部分覆盖）未验。
- `Meta`/`Ctrl` 的差异只在本机 macOS 上测过，**未在 Windows/Linux 复现**。
- `setNodes` 的第三个入口 `restoreOrganize()` **只看到「还原」按钮出现，
  没有点它验证能否复原**。
- `removeEdge` 只验了 1 条边（`e-8IgMkf6Vbj`），11 条边的按钮几何没逐条取。
- `duplicateNode` / `removeNode` 的零入口是**静态**结论。
- **本批没有与源站对照**画布的这批交互（源站在 752 里只用于导演台对照）。
- 「还原」按钮的文案匹配用了 `indexOf('还原')`，若源站用别的词会漏。

---

## 产物

| 文件 | 内容 |
|---|---|
| `runtime-audit.json` | 13 条判据 + 每条的实现对账 + 两轮比对 + **7 条返工** + 不声称清单 |
| `verify-report.json` | 验收器输出，**43/43**（静态 17 + 产物 7 + 运行时 15 + 原始读数交叉核对 4） |
| `../../scripts/verify-liblib-batch753.py` | 判据校验器（两轮一致性 + 易变字段剔除） |
| `/tmp/dbg753{a..h}.py` | 8 个探针；`/tmp/vb753{a..h}.json` 原始读数；`/tmp/mk753audit.py` 汇编器 |
