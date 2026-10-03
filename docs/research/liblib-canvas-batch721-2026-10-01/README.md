# batch 721：720 的「加模型关台重开就没了」是比错了对象

日期：2026-10-03　验收器：`scripts/verify-liblib-batch721.py`（7 条判据，零 store 写入，不改 `src/`）

闸门：判据 **7/7 通过（连跑两轮读数逐条一致）**；typecheck 绿；
`docs:check` 里 `docs/research/` **0 条**（21 条全在他人 `docs/user-manual/beeftv-canvas/`）；
本批文件 lint **0 error / 1 warning**（`scripts/*.py` 不在 eslint 配置覆盖内）；
**build 跳过** —— `src/` 自 batch 690 起 0 提交；工作区里有他人 jimeng 的未提交改动
（`JimengBottomDock.tsx` / `JimengTopBar.tsx` / `jimengStore.ts`），未碰。

## 起点

720 测出三条路线：只加模型关台重开后 `objects` 从 6 掉回 5（饮料瓶没了）；
只改名活着；先改名再加速六个全在。720 **明写「不声称成因」**，
把「读 `closeSession`/`persistence.save` 对不同改动类型的处理」留给下一批。

本批顺着这条线走，**结果问题出在探针自己身上**。

## 撤回：模型没有丢

720 的 `reopen()` 是这样写的：

```python
def reopen(page):
    ob = read(page)["openBtn"]          # document.querySelector('[data-open-director]')
    page.mouse.click(ob["x"] + ob["w"] / 2, ob["y"] + ob["h"] / 2)
```

`document.querySelector` 取的是 **DOM 顺序的第一枚** 按钮。
而 `open_desk()` 开的台挂在自己 `addNode` 造的 `script-execution-<时间戳>` 节点上。
**这两个不是同一个节点。**

按 `nodeId` 精确重开之后：

| 读数 | 值 |
|---|---|
| 改名后（先改名） | `objects` 5、`past` 1 |
| 再加模型 | `objects` 6、`past` 2 |
| 关台 | `objects` 6、`past` 0 |
| **按 nodeId 精确重开同一个节点** | **`objects` 6、`authored` 6、`past` 2**，名字与关台前逐条相同 |
| 该节点的持久化记录 | **6 个对象**，含「饮料瓶」（`primitive: "library"`） |
| **720 点的那枚按钮归属** | **`b-bTLLuU4w5q`（fixture 自带的种子节点），不是 nodeX** |
| 点它之后读到的 | `objects` **5**、**另一个 `projectId`**、`generation` 从 1 起 |

**720 路线 A 的「丢了」= 读了另一个项目的对象表。**
按本项目的方法论分档，这是第三档：**测的不是那个东西** —— 读数和推理一起作废。

### 顺带撞见的一枚小事实

改名这一步用的是 `document.querySelector('[data-director-object-name]')`，
**也就是「第一个名字输入框」**。它指向哪个对象，取决于有没有先加过模型：

| 时刻 | 第一个名字输入框的值 |
|---|---|
| 开台 | `角色01 · 陈默` |
| **加完模型之后** | **`饮料瓶`**（新加的那个） |

⟹ 新加的对象会排到名字字段的第一位。**第一版探针「先加模型再改名」，
于是把模型改名成了「改名探针」，五个原始对象一个没动** ——
读数看起来像「少了一个模型」，其实是「改名打在了另一个对象上」。
这与本批的主结论是同一条：**「第一个」也是一种不稳定下标。**

顺带纠正一条会继续误导人的笔记：`b-bTLLuU4w5q` 是**种子节点**，
不是 `open_desk` 造的节点。它之所以稳定出现，是因为 fixture 每次都种同一批节点。

## 「重开」其实有三层，从来被当成一层

| # | 操作 | `objects` | `past` | `projectId` | `generation` |
|---|---|---|---|---|---|
| ① | 关台 → **同页**重开同一节点 | **6（留住）** | **2（留住）** | 不变 | **+1** |
| ② | **整页刷新** → 重开同一节点 | 记录还在（6），**但节点卡没了、台开不起来** | — | — | — |
| ③ | 打开**另一个**节点 | **5** | 0 | **另一个** | 从 1 起 |

**② 是本批真正的新发现**：刷新后 `nodeX` 不在画布节点列表里（回到 10 枚种子节点），
对刷新后按钮列表做断言也只有一枚（`b-bTLLuU4w5q`）；
再用 `openDirectorDesk(nodeX, canvasId)` 走同一条路径试一次，
等 15 秒 `[data-director-workspace]` 都没出现。

⟹ **「刷新后内容还在」这句话在本克隆里对 `addNode` 造的节点是不成立的** ——
不是内容丢了，是**承载它的那个节点整个没了，台开不起来**。

## `past` 不住在 localStorage 里

| 时刻 | `objects` | `past` | localStorage 记录 |
|---|---|---|---|
| 开台 | 5 | 0 | — |
| 加模型 | 6 | 1 | — |
| 再改名 | 6 | 2 | — |
| 关台 | 6 | **0** | **6 个对象，无 `history` 键** |
| 同页重开 | 6 | **2** | 同一条记录，一字未动 |
| 刷新后 | — | — | **与刷新前逐字段相同**（只有 `generation`、`savedAt` 变） |

记录的 `document` 恰好 12 个键：`schemaVersion` / `projectId` / `owner` / `scene` /
`objects` / `groups` / `shots` / `activeCameraId` / `timeline` / `outputPreferences` /
`resourceRefs` / `captureDescriptors` —— **没有 `history`**。

⟹ `past` 回来靠的是 `directorStore.ts:1940` 的模块级 `Map`
（`directorHistoryByProject.set(projectId, cloned)`），刷新即清。
`closeSession` 在 `directorStore.ts:3289` 先 `rememberDirectorHistory` 再写持久化，
顺序上正好是「内存留一份、磁盘留一份」。

### 这收窄了 711 的「history 不入持久化」

711 的表述是「history 不入持久化（392 枚叶子整个没有）」，测的是刷新。
**准确说法是：history 不入 localStorage，只活在内存注册表；
同页关台重开能撤销，刷新后不能。**
711 的读数全部存活，概括要拆成两半。

## 每次重开的记账

| 字段 | 开台 #1 | 同页重开 #2 |
|---|---|---|
| `projectId` | `director-project-…-1` | **同一个** |
| `sessionId` | `…-2` | **`…-3`（新铸）** |
| `generation` | 1 | **2** |
| 记录里的 `generation` | 1 | **2** |

⟹ `generation` 是「**这份项目被打开过第几次**」，不是全局计数器；跨节点互不干扰
（另一个节点从 1 起）。

## 画布本身不落盘（静态）

`src/store/canvasStore.ts` 里 `localStorage` / `sessionStorage` / `indexedDB` /
`persist` / `subscribe` / `STORAGE_KEY` **命中 0**
（文件里的 `persistence` 是节点数据上的另一个字段，不是持久化）。

`localStorage.setItem` 的分布：

| store | 次数 |
|---|---|
| `frameosStore.ts` | >0 |
| `directorStore.ts` | >0 |
| **`canvasStore.ts`** | **0** |

⟹ 刷新后画布回到 10 枚种子节点、`addNode` 造出来的节点整个消失，
**与导演台无关，是画布级行为**。

## 不声称

- **不声称源站在刷新后能不能重开那个节点** —— 源站导演台当前关着，所有读数只能来自 clone。
- **不声称「画布不落盘」是不是缺陷** —— 这可能是 fixture 模式（`?batch70=1`）的性质，
  也可能是 clone 的性质；判据只覆盖「`canvasStore.ts` 里没有任何持久化写入」。
- **不声称 `sessionId` 每次新铸有没有代价** —— 只读到它是新值。

## 新增待拍板

1. **刷新后画布回到种子节点、`addNode` 的节点整个消失** —— 是不是缺陷，要不要让画布入持久化。
2. **711 的「history 不入持久化」拆成两句**（不入 localStorage / 只活在内存注册表）——
   要不要让 history 也进持久化（代价：体积 + `generation` 语义）。
3. **模型库卡片 `role="group"`**（720 遗留）、**`Escape` 双重语义**（707/720 遗留）、
   **8 处组件级 keydown 全修饰键盲**（719/720 遗留）—— 三条仍未决。

## 方法论

1. **「探针自己造的对象」和「页面上现成的对象」不是同一个** ——
   720 用 `addNode` 造了一个节点开台，却用 DOM 顺序第一枚按钮去重开。
   **凡是探针自己造出来的对象，后续每一步都必须按它的稳定标识（`data-*` / id）定位。**
   这与 715 的「因果读数不能用下标」是同一条：**下标在跨状态时不稳定**，
   `querySelector` 的「第一个」也是一种下标。
2. **比出来的差异要问「比的是不是同一个东西」** —— A/B/C 三条路线里，
   A 的重开步骤与 B/C 不是同一步。**三路线对照的前提是三路线的每一步都对齐**；
   对不齐时，三条路线之间的差异**全部作废**，不能只撤回其中一条。
3. **「丢了」还有一个第四种可能：承载它的东西没了** ——
   本批的 ② 不是「内容丢了」而是「节点没了、台开不起来」。
   前三种（关台丢 / 重开丢 / 刷新丢）都假设承载物还在，这个假设没被检查过。
4. **模块级变量要当成一个独立的持久化通道来测** ——
   `past` 回来不来自任何存储层；只查 localStorage 会得出「history 丢了」的错结论。
   **判「什么回来了」要同时读所有通道，而不是只看写下去的那一个。**

## 探针返工三处

1. 第一版 `reopen()` 沿用了 720 的 `querySelector` 写法，跑出来的还是 5 ——
   **一个照抄前一批的探针，会把前一批的错误一起继承**，必须重写成按 id 定位。
2. 中途为了「干净存储」调了一次 `localStorage.clear()` + 刷新，
   结果**连画布节点一起抹了**，`nodes.at(-1)` 变成了 `v-…` 节点，
   后续 `open_by_node_id` 断言失败才发现。
   ⟹ **Playwright 每次 `launch()` 都是全新 profile，存储本来就是空的**，
   这一步既多余又危险。
3. 探针原本只跑到「关台」，读 localStorage 发现记录里**明明有 6 个对象** ——
   说明问题不在持久化而在「重开读什么」。**这一步是整批的转折点**：
   如果只盯 store 不看存储，就会继续在错误的方向上找成因。
