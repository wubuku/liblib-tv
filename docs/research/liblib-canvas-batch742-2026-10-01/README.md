# batch 742 — 命令入口普查：**记账 33 × LibTV 有入口 29 / 零入口 4**；一条从未被调用过的记账命令

## 起点

741 把 canvasStore 54 个命令按「记不记账」分了桶，但没问
**用户在 LibTV 画布里到底能触发到哪些**。本批做两件事的交叉，
再核一件事：**「登记在反馈清单里」和「接了线」是不是同一件事**。

全部读数来自 clone，**不碰源站**。

## 交叉表

| | LibTV 画布内有入口 | LibTV 零入口 |
|---|---|---|
| **记账**（33） | **29** | **4** |
| **不记账**（21） | **17** | **4** |

### LibTV 零入口的 4 个记账命令

| 命令 | 位置 | 实际情况 |
|---|---|---|
| `submitLibTVEditorSessionCommit` | `canvasStore.ts:3991` | **全 src/ 零调用点**（唯一） |
| `duplicateNode` | `:3104` | 只被 FrameOS(2 处)、Jimeng(3 处) 调 |
| `removeNode` | `:3187` | 只被 FrameOS(5 处)、Jimeng(3 处) 调 |
| `setEdges` | `:3415` | 只被 `src/app/frameos/canvas/[id]/page.tsx:143` 调 |

LibTV 画布用的是**复数版**：`duplicateSelectedNodes:3150`（`page.tsx:1355` ← Cmd+D）
与 `removeSelectedNodes:3223`（`page.tsx:1326` ← Delete 键，740 已验）。
改边只用 `addEdge` / `removeEdge`，两个都记账，**从不整体替换 `setEdges`**。

### 四个零入口命令直调都「有能力」

| 命令 | `past` | 节点 | 边 | 返回 |
|---|---|---|---|---|
| `duplicateNode(id)` | 0 → **1** | 10 → 11 | 11 → 12 | `null` |
| `removeNode(id)` | 0 → **1** | 10 → 9 | 11 → 10 | `null` |
| `setEdges(edges)` **不带 flag** | 0 → **0** | 10 → 10 | 11 → 11 | `null` |
| `setEdges(edges, {recordHistory:true})` | 0 → **1** | — | — | — |
| `submitLibTVEditorSessionCommit(req)` | 0 → **1** | 10 → 10 | 11 → 11 | `{"status":"accepted","historyPushed":true,…}` |

⟹ **能力在、入口不在**。
`setEdges` 那两格直接对上 741 的条件记账读数：同一个命令，参数给不同就两种结果。

## 「预留能力」不是「回归掉的接线」

```
$ git log --oneline -S "submitLibTVEditorSessionCommit(" -- src/     # 空
```

⟹ 「命令名 + 左括号」**从未在任何提交里出现过**。
它由 `d9c745b4`（batch 446 VR-022 等值感知提交适配器）引入 store，
`0902def1`（batch 467 VR-018 命令反馈清单）只加了字符串元数据。

（全仓范围内该字符串唯一的另一处出现在
`docs/research/liblib-canvas-batch446-2026-09-13/README.md:19` —— **文档，不是调用点**。
第一版的 `git log` 路径写错，把这句说明算成了一次外部调用。）

## 反馈清单登记 ≠ 接线（承 729「两套未接线契约」）

`src/lib/libtvCommandFeedback.ts` 的 **13** 个 surface 里，2 个直接指向 store 方法：

```ts
{ surfaceId: "editor-session-commit", component: "canvasStore.submitLibTVEditorSessionCommit",
  feedbackKind: "none", commands: ["editor-session-commit"] }      // ← 从不执行
{ surfaceId: "asset-reference-attach", component: "canvasStore.attachAssetReferences",
  feedbackKind: "none", commands: ["asset-reference-attach"] }      // ← 真在跑（AddNodePanel.tsx:76）
```

⟹ 两条都写着 `feedbackKind: "none"`（清单**自己知道**这条命令没有反馈通道），
但其中一条**登记了却从不执行**。清单里的 `component: "canvasStore.xxx"` 是**字符串**，
不是调用点 —— 这正是 730 立下的「分清声明与实现」在清单层的同一个坑。

## `purgeRemovedCanvas` 零入口**与 UI 自洽**（不是缺口）

回收站面板 `src/app/project/page.tsx:151`，由 `data-project-recycle` 按钮控制展开。
**先让它真的有内容再读**——空回收站的面板里一个按钮都没有，第一版的判据写成
「按钮数 ≤ 2」于是**零信息地通过**（740 立过的坑）：

| 步骤 | `removedCanvases` | 面板 |
|---|---|---|
| 展开回收站（还没删过） | `[]` | `items 0`、**按钮 0 个**、`data-recycle-empty` 在 |
| `removeCanvas('canvas-1')` 之后 | `["canvas-1"]` | `items ["canvas-1"]`、**按钮 1 个「恢复」**（`data-recycle-restore`） |
| 点那个「恢复」 | `[]` | `items 0`、回到 `data-recycle-empty` |

`purgeRemovedCanvas` 在整个回收站区块的 `onClick` 里 **0 命中** ⟹
**没有「永久删除」按钮**，所以这个命令零入口是**与 UI 自洽**的，不列为缺陷。

稳定属性全集：`data-recycle-panel` / `-item` / `-check` / `-selection` / `-empty`
/ `-restore` / `-restore-selected` / `data-project-recycle`。

## 撤回的三条（探针返工三次，全是自己的错）

- **「8 个记账命令零入口」** —— 正则 `(?<![\w.$])name\s*\(` 用「前面没有点号」来避开
  store 自调用，结果把 `useCanvasStore.getState().name(...)` 这种正常入口**全杀了**。
- **「`setNodes` 在 LibTV 零入口」** —— 漏了**解构改名**：
  `page.tsx:366` 写的是 `setNodes: setStoreNodes`，调用点是 `setStoreNodes(...)`，
  名字 `setNodes` 后面从来不跟 `(`。而 741 刚在**运行时**证过拖动停下会调它 ——
  两份读数互相矛盾，先怀疑 census。修法：先建 `命令 → 别名` 映射（本批实测 3 个）。
- **「FrameOS/Jimeng 归属判定」** —— 只按路径段 `/frameos/` 判，漏了
  `src/store/frameosStore.ts`、`src/lib/frameosUpload.ts` 这类**只有文件名带 frameos** 的文件。

另修两处探针错：`selectElements:3500` 收的是 `{nodeIds, edgeIds}` 对象不是数组；
`onClick={canUndo ? undo : undefined}` 里的 `undo: undefined` 被当成了解构改名。

**还有一处判据零信息**：C6 写成「按钮数 ≤ 2」而空回收站里**一个按钮都没有**，
于是这条判据**因为错误的原因通过**（与 740 的 `past=0` 刷新格同一类）。
改成「先删一张画布让回收站有内容，再读按钮、再点真按钮」。

## 判据（7/7）

| | 判据 | 读数 |
|---|---|---|
| C1 | 交叉表：记账 33 = LibTV 29 / 零 4；不记账 21 = 17 / 4 | `{acct_total:33, acct_libtv:29, noacct_total:21, noacct_libtv:17}` |
| C2 | 4 个零入口记账命令点名；`submitLibTVEditorSessionCommit` 全 src/ 零调用且从未调用过 | `git log -S` = 0 提交 |
| C3 | 别名映射 3 个；**用 741 的运行时事实反证 census**（`setNodes` 必须有 LibTV 入口） | `setNodes` LibTV 4 处 |
| C4 | 零入口命令直调：3 个无条件记账，`setEdges` 需带 flag | `setEdges` 0/0 → 1/1 |
| C5 | Cmd+D 走 `duplicateSelectedNodes`：节点 +1、`past` +1、Cmd+Z 撤回 | `10→11, past 0→1, undo 回 10/0, future 1` |
| C6 | 回收站真有内容：每个按钮都是「恢复」、点它真的回来了 | `items ["canvas-1"]`、按钮 1 个、点后 `removed=[]` |
| C7 | 反馈清单 13 个 surface，登记了那条从不执行的命令 | `editor-session-commit` |

## 不声称

- 不声称 4 个零入口记账命令是缺陷还是有意保留 —— 未取证。
- 不声称源站是否有对应的单节点复制 / 单节点删除能力 —— 未取证。
- 「零入口」只覆盖 `src/` 内的静态调用点；运行时字符串派发或反射调用本普查读不到
  （已用 `git log -S` 交叉查过 8 个命令，仍不能排除一切动态路径）。
- 「清单登记 ≠ 接线」只对本批核到的这 1 条成立，其余 12 个 surface 未逐条核接线。
- 回收站只验了单条「恢复」；批量「恢复所选 N 项」（`data-recycle-restore-selected`）
  需要多选态，本批未走到那一步。

## 验收器

`scripts/verify-liblib-batch742.py` — 静态普查（复用 741 的命令解析口径，不另写一份）
+ 5 组运行时读数，两轮连跑逐字段一致。
