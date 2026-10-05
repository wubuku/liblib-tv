# batch 802 —— 普查驱动：坐标系错误的**第三处**，且**用户可达**

> 结论先行：799（组框写回）、800（取消分组）是同一类错误——把「相对直接父节点的
> 坐标」当成「绝对坐标」。本批不再抽样，而是**用 TypeScript AST 把 `canvasStore.ts`
> 里「把 nodes 写进 canvas」的每一个写点普查出来**，逐个标注是否经 fit、是否碰
> 坐标系换算，**找出第三处**：`createImageHdPreset`。它由 UI 上的**「图片高清」按钮**
> 直接触发 ⟹ **不需要注入就是用户可达的**，比 799/800 的触发面宽。

## 一、为什么必须普查而不是继续抽样

799 留下了一条明确的待办：「其余 14 处未普查写点」，并写明「本批的发现说明那一栏
**可能还藏着同类的坐标系错误**，优先级应当提高」。800 在清单里又手工找到一处。

**两次手工抽样，两次都中** ⟹ 这不是偶发笔误，是一个**类**。抽样无法回答「还有几处」，
于是本批换成机器普查。普查器 `probes/scan802.mjs` 用 TypeScript 编译器 API 建 AST，
遍历 `PropertyAssignment{name: "nodes"}` 取全部写点，再按**所属动作**聚合。

★ 三个数全部由机器数出（794 的教训：手写的普查数字本身是错的）：

| 口径 | 值 |
| --- | --- |
| `nodes:` 写点合计（去掉类型声明与回读） | 41 |
| 涉及的动作数 | 37 |
| `fitStoryboardGroupsToChildren` 调用点合计 | 4 |
| 风险分布 | 高 10 ｜ 中 23 ｜ 低 4 |

★ **「所属动作」的取法第一版是错的**：沿 parent 链找最近的 `PropertyAssignment` ⟹
35 个写点全被吸到嵌套的 `canvases: state.canvases.map(...)` 上，真正的动作名全丢了。
动作的特征是「initializer 是**函数**」——`foo: (...) => {`。

## 二、普查结果：37 个动作里只有 4 个经过 fit

经 `fitStoryboardGroupsToChildren` 的动作恰好 4 个：

| 动作 | 说明 |
| --- | --- |
| `removeNode` | 删一个 |
| `removeSelectedNodes` | 删一批 |
| `nudgeSelectedNodes` | 方向键微调 |
| `routeReactFlowChanges` | react-flow 每次变化（含 `dimensions` 反馈）——799 查清的隐藏调用者 |

其余 33 个动作改完 `nodes` **不经 fit**。风险判据（普查器**不做语义判断**，只采集）：

> **高** = 改了 nodes 但不经 fit，且碰了 `parentId` / 坐标系换算
> **中** = 改了 nodes 但不经 fit
> **低** = 其余

### 高风险 10 个动作里，9 个本来就是对的

| 动作 | 行（修复后） | 写点 | 写 parentId | 已用坐标系换算 |
| --- | --- | --- | --- | --- |
| `createFirstFrameReference` | 1471 | 1 | 0 | 是 |
| `createFirstLastFrameReference` | 1545 | 1 | 0 | 是 |
| **`createImageHdPreset`** | **1633** | **1** | **1** | **否 ← 唯一漏网的** |
| `addDerivedNode` | 1767 | 1 | 0 | 是 |
| `createVideoContinuation` | 1822 | 1 | 0 | 是 |
| `createSubtitleErase` | 1925 | 1 | 0 | 是 |
| `createAudioSplit` | 2058 | 1 | 0 | 是 |
| `completeShotBreakdown` | 3171 | 1 | 0 | 是 |
| `groupSelectedNodes` | 3482 | 1 | 1 | 是 |
| `ungroupSelectedNodes` | 3568 | 1 | 0 | 是（800 本批已修） |

★ 普查只负责**缩小范围**，语义判断仍然是逐个读源码做的。结论：**10 个里只有
`createImageHdPreset` 在建节点时用了相对位置**。这是一个**阴性面同样重要**的结果——
它说明「机器普查」不是只会捞出坏消息，也顺带证明了另外 9 处是好的。

## 三、缺陷：源节点在组里时，新建组落在错的地方

```ts
// 修复前
const group: Node = {
  id: groupId,
  type: "storyboard-group",
  position: { x: source.position.x + 320, y: source.position.y - 60 },  // ← source.position 是**相对直接父节点**的
  ...
};
const child: Node = { ..., parentId: groupId, position: { x: 40, y: 60 }, ... };
```

新建的 `group` 是**顶层**（没有 `parentId`），于是它的 `position` 会被当成绝对坐标。
但 `source.position` 是相对源节点**直接父节点**的 ⟹ 沿途所有祖先的偏移被整段丢掉。

★ **触发条件比 799/800 宽**：**不需要嵌套**。源节点只要在**任何一个组里**就会错。

### 用户可达，不需要注入

`src/components/nodes/ImageNode.tsx:294` 的「图片高清」按钮直接调
`useCanvasStore.getState().createImageHdPreset(id)`。这与 799/800 不同——那两处
必须靠注入才能造出前提数据（792 遗留：`groupSelectedNodes` 的 children 过滤里
`node.type !== "storyboard-group"`，UI 造不出嵌套）。**本批的缺陷在普通使用路径上。**

## 四、判据：位移对照，完全不涉及任何常量

- **不变量 F1**：宿主组移动 Δ，新组**也必须移动同一个 Δ**。
- ★ 不需要知道源码里的偏移是 320 还是 −60。缺陷（新组纹丝不动）一眼可见。

★ **为什么不能用「单臂比对新组与源的距离」**：那会踩一个坑。pre 侧 A 臂的源节点
`position` 已被 fit 重基成 `(40,40)`，于是「新组 − 相对位置」也恰好等于 `(320,-40)`
——**与 post 一模一样**。也就是说，只看单臂 + 只看相对坐标，**修复前后分不出来**。
必须做**两条臂之间的位移对照**才抓得到。

### 三条臂

| 臂 | 源节点 | 宿主组位置 | 角色 |
| --- | --- | --- | --- |
| `presetFromLoose` | **顶层**（无祖先） | `(200,150)` | **阴性对照** |
| `presetFromGroupedA` | 在组内 | `(200,150)` | 缺陷臂 |
| `presetFromGroupedB` | 在组内 | `(500,450)` | 缺陷臂（A→B 即位移对照） |

★ **阴性对照 `presetFromLoose` 的前提被显式验证**（S2）：祖先偏移为 0 是「相对 == 绝对」
成立的前提，不成立就什么也证明不了。验收器**从 raw 的 `parentId` 链独立重算**并与探针
记录的 `srcAbs` 逐位比对，不是默认成立。

★ **阳性对照不可省**（S3）：组与 child 都确实建出来了、child 的 `parentId` 确实指向新组。
否则「什么都没发生」也会让「新组不动」成立 ⟹ 假绿。

## 五、读数（同一份探针 pre/post 各 2 轮 × 3 臂）

「源绝对」是沿 `parentId` 链求和的值；`new` 是新组的绝对位置。

| 相位 | 臂 | 源绝对 | 新组绝对 | 新组 − 源绝对 |
| --- | --- | --- | --- | --- |
| pre | `presetFromLoose` | `(800,600)` | `(1120,560)` | `(320,-40)` |
| pre | `presetFromGroupedA` | `(250,200)` | `(360,0)` | `(110,-200)` ✗ |
| pre | `presetFromGroupedB` | `(550,500)` | `(360,0)` | `(-190,-500)` ✗ |
| post | `presetFromLoose` | `(800,600)` | `(1120,560)` | `(320,-40)` |
| post | `presetFromGroupedA` | `(250,200)` | `(570,160)` | `(320,-40)` |
| post | `presetFromGroupedB` | `(550,500)` | `(870,460)` | `(320,-40)` |

**位移对照**：A→B 宿主移动 `(300,300)`。

| 相位 | 宿主移动 | 新组移动 | 跟着动 |
| --- | --- | --- | --- |
| pre | `(300,300)` | `(0,0)` | **否 ← 缺陷** |
| post | `(300,300)` | `(300,300)` | **是** |

### 一个必须说清的数值差：源码写 −60，实测 −40

源码里的偏移是 `(320, −60)`，实测是 `(320, −40)`，y 差 **+20**。原因：组与 child 建好之后
`routeReactFlowChanges` 会跑 fit 把组框贴合唯一子节点（child 相对 `(40,60)`），
组原点因此**统一下移 20**（`child.rel.y − GROUP_PADDING = 60 − 40`）。
★ 这个位移在三条臂里**完全一致**，所以它在「臂间相减」时**相消** —— 判据不受影响。
第三行的 `presetFromLoose`（无祖先、同样被 fit 下移 20）就是这条解释的对照证据。

### 无回归：`presetFromLoose` 逐位相同

修复对「祖先偏移为 0」必须是**恒等变换**。该臂 pre/post 两轮读数**逐位相同**
（`(1120,560)`），由 S7 钉死。

## 六、修复

```diff
+    const nodesById = new Map(canvas.nodes.map((node) => [node.id, node]));
+    const sourceAbsolute = getAbsoluteNodePosition(source, nodesById);
     const group: Node = {
-      position: { x: source.position.x + 320, y: source.position.y - 60 },
+      position: { x: sourceAbsolute.x + 320, y: sourceAbsolute.y - 60 },
```

与 800 同一套路：改一个函数、不新增 API、不动 UI。`nodesById` 必须在**旧**节点集合上建
（含祖先，链才走得通）。`getAbsoluteNodePosition`（`:569`）沿父链逐层求和，
**起点必须是 `position` 不能是 `abs`**（800 的独立重算第一版踩过：重复计入）。

## 七、验收结果

汇编器（`probes/mk802audit.py`）断言 **8/8**、0 失败；验收器
（`scripts/verify-liblib-batch802.py`，**独立实现**，不 import 汇编器）主检查 **11/11**、
阴性对照 **4/4**，阴性后 `canvasStore.ts` 与三份 raw **字节级复原**（sha256 核对）。

### ★ 本批造出并修掉的**两个坏检查**（比实现错更值得记）

| 坑 | 教训 |
| --- | --- |
| 验收器 S1 声称「现场重跑 scanner 交叉核对」 | ★ **假的**：scanner 只有固定输出路径 ⟹ 重跑把入库那份**原地覆写**，然后「入库的 vs 重跑的」读的是**同一个文件**，自比恒等；而且 `subprocess` 的**退出码根本没检查**，scanner 崩了照样读旧文件 PASS ⟹ **假绿**。修法：给 scanner 加可选输出参数、重跑到 `/tmp`，并把 rc 与「入库文件未被覆写」都列进证据（现在是 S1a） |
| 阴性对照 N2 第一版把 pre 的 A 臂改成与 B **相同**（与 N1 逐字一样的变异） | ★ **翻不了红**：S4 的判据是「新组**不动**」——真实缺陷让新组不动、这个变异也让它不动，**性质根本没被改变**。正确做法是给 A 一个「移动量恰好等于宿主位移」的位置。**阴性对照必须打在被测性质真正读取的量上**（801 已踩过一次，本批又踩一次变体） |

★ 另有一处判据设计上的坑：S1 比对时**不能比行号**。本批修复在 `:1636` 之后插了 7 行
⟹ 37 个动作里 32 个的行号整体 +7，拿行号比会把「修复存在」误判成「普查不可复现」。
改成**剥掉 `line`/`ownerLine` 后逐动作比对**，并断言差异**只可能落在 `absHelpers` 上**
（`createImageHdPreset` 由 `[]` 变成 `["getAbsoluteNodePosition"]` —— 正是那一行修复）。
这条同时给出了一个漂亮的自证：普查器重跑与入库那份的**唯一语义差异就是本批的修复**。

### 第四次踩「锚点抓到接口声明」

needle 只写 `createImageHdPreset: (imageNodeId` 会先命中 `CanvasState` 的**接口声明**
而不是实现（`:1633`）⟹ 段长只剩 112、里面没有函数体。799（`updateNodeData`）、
800（`ungroupSelectedNodes`）、801（`duplicateGraphSelection`）各踩过一次，本批是第四次。
**锚点必须带完整的参数类型标注**：`createImageHdPreset: (imageNodeId: string) => {`，
并断言段长 > 500。

### 变异器的写入时机

799 踩过「`mut_text` 在 `assert` 之前就写文件」，真在 `canvasStore.ts` 里留下过
`// 799 修`。本批所有校验都在**写入之前**完成 ⟹ 阴性对照中途失败也不会把脏文件留在
工作区。实测：N4 当场崩在 assert 上，之后 `canvasStore.ts` 的 sha256 与运行前**逐位相同**。

## 八、遗留

- ★ **未与源站对照**（源站需登录）⟹「源节点在组里时，新建子画布应落在源的绝对位置旁边」
  是工程判断，不是源站实测值。
- ★ **另外 9 个高风险动作只有「读过源码确认已走 `getAbsoluteNodePosition`」这一层证据，
  没有行为证据**。按 794 的教训（`removeNode` 只有静态证据、报告**不许**说「都验过了」），
  它们**不能**算已验收。下批应逐个取行为证据，优先级最高的建议：
  `groupSelectedNodes`（会建组，碰 parentId）、`completeShotBreakdown`（批量建节点）。
- ★ **`restoreCanvas`（`:1211`）这个写点普查归到「低」风险**（不经 fit、也不碰坐标系），
  但它是回填整张图的入口 ⟹ 「低」只说明**本批的判据**不命中，不等于它是对的。
- ★ 中风险 23 个动作里，`duplicateNode` / `duplicateSelectedNodes` / `setNodes` 不经 fit，
  但 801 已证明复制路径正确、`setNodes` 靠 `dimensions` 反馈触发 fit（799 查清）⟹
  同样是「静态看着没问题」，不是「验过了」。
- ★ 793 遗留的「空组要不要收缩/弱化」（757 待拍板 ②）仍未碰。