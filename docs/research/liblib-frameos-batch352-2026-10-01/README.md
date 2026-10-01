# Batch 352 — 死状态普查改用真 AST；5 个 store 全量扫描；记录一处跨线发现

日期：2026-10-01
范围：`scripts/deadstate_census.mjs`（新增）、`scripts/frameos_deadstate_census.py`（移除）
性质：**CLONE_DECISION**（工具质量；不动产品行为）

---

## 为什么要重写工具

Batch 349 引入的普查工具是**正则实现**。把它推广到其它 store 的过程中，
它先后暴露了 **5 类误报**，每一类都差点让人把「活字段」当成死状态：

| # | 误报 | 具体例子 | 为什么正则搞不定 |
|---|---|---|---|
| 1 | 多行函数签名的**参数**被当字段 | jimengStore 的 `applyTrim: (\n id: string,\n trimmedDuration: number,\n)` | 参数单独占一行，完全符合「标识符 + 冒号」 |
| 2 | **解构**读取被漏 | `const { groupNames } = useJimengStore.getState()` | 只匹配 `s.field` 属性访问；且 hook 真名 `useJimengStore` 与文件名 `jimengStore` 之间**没有词边界**，`\bjimengStore\b` 永远匹配不到 |
| 3 | 多行 action 的**首行**像字段 | canvasStore 的 `addNodeAtFlowCenter: (` | 首行没有 `=>`，冒号右边是 `(` |
| 4 | 多行**解构**里字段单独占一行 | canvasStore 的 `removedCanvases` | 该行没有 hook 名 |
| 5 | 切接口 body 太天真 | canvasStore 的 `cohortId` / `attachedAssetIds` / `skippedAssetIds` | 用「第一个 `\n}`」切，把**邻近的其它接口**也扫进来了 |

**结论：继续打补丁是错的方向。** 一个误报率这么高的工具留在仓库里，
就是给未来的人埋陷阱 —— 它每次都会产出「看起来很确凿」的假线索。
直接改用 **TypeScript 自己的 AST**（仓库本来就装了 `typescript` 5.9.3），
5 类误报一次性归零：

- 字段抽取走 `ts.isPropertySignature` + `ts.isFunctionTypeNode`（排除 action）；
- 读取点分两层：层 A = `ts.isPropertyAccessExpression` 的属性名；
  层 B = **变量声明的绑定模式**里出现该字段、且 initializer 提到 store（解构）；
- 「只被解构读取」的字段单独标出，避免再次被误判。

**测量方法本身要先验证** —— 这次是用真实编译器 AST 来验证的。

## 全量扫描结果（5 个 store 全扫完）

| store | 数据字段数 | 死状态候选 |
|---|---|---|
| `frameosStore` / `FrameosCanvasState` | 33 | **无**（Batch 349 删除 `generations` 后的基线） |
| `canvasStore` / `CanvasState` | — | **无**（原报的 5 个全是误报 3/4/5） |
| `jimengStore` / `JimengCanvasState` | — | **无**（`groupColors`/`groupNames` 为「只被解构读取」，活着） |
| `directorStore` / `DirectorState` | 33 | 2 个候选，**手工核实后确认都活着**（见下） |
| `uiStore` / `UIState` | 30 | **4 个真候选**（见下） |

> 即：**全仓 5 个 store 扫完，唯一的真死状态是 Batch 349 已删的 `generations`。**

### `directorStore` 那 2 个候选为何是活的

工具报 `authoredObjects` / `clipboardPasteCount` 两层都为 0，但它们**全都在
`directorStore.ts` 内部**被读：`authoredObjects` 有 94 处内部引用
（如 `state.authoredObjects.find(...)`），`clipboardPasteCount` 在 3964 行被读
（`pasteOrdinal: state.clipboardPasteCount + 1`）。

这正是工具 docstring 里写明的局限：「零外部读」对「**只在 store 内部读**」的字段会误报。
所以候选必须**手工判读**，不能直接当死状态。

## 跨线发现：`uiStore` 的 4 个面板开关是不可达状态（**只记录，未改**）

`uiStore` 报出 4 个两层都为 0 的字段，手工核实**确认是真的**：

`isToolboxPanelOpen` / `isMaterialPanelOpen` / `isCharacterPanelOpen` / `isHistoryPanelOpen`
—— 外加它们各自的 `toggleXxxPanel` 动作，**同样零调用**。

而 `src/components/LeftSidebar.tsx:128-141` 是这样驱动这些面板的：

```tsx
<ToolButton label="打开工具箱" active={activePrimaryPanel === "toolbox"} onClick={() => togglePanel("toolbox")} />
```

也就是说：**真正生效的机制是 `activePrimaryPanel`**，那 4 个 boolean 是
`activePrimaryPanel` 重构之前遗留的旧机制，从没被清掉。它们不可达
（flag 永远变不成 true），也是给未来的人埋的陷阱 —— 谁调用
`toggleToolboxPanel` 都会发现界面上什么都不会发生。

**为什么不改**：`uiStore` 属于 **liblib/jimeng 主应用**，不在「帧界画布复刻」这条线上，
而那条线此刻正有并行 session 在作业（jimeng 79x/80x 批次）。
按「绝不干扰其他人的工作」与「不擅自跨线改动」两条纪律，
**这里只记录，不动手**；要清就由那条线的作者连同它的验证器一起清。

## 未完成 / 边界

- 普查**仍然不宜直接门禁化**，原因已由实测坐实：**「只在 store 内部读」的字段会误报**
  （`directorStore` 的 `authoredObjects` 94 处内部引用、`clipboardPasteCount`
  都在 store 内被读，却报成候选）。层 B 的判据也只覆盖「从 store 直接解构」，
  间接引用（把整个 store 传给别的函数再解构）仍可能漏。
  真要门禁化，需要先为这两类形态各造一个「已知活着」的样本做反向测试 ——
  也就是 Batch 351 对 `diagnostics:zero` 做的那件事。
