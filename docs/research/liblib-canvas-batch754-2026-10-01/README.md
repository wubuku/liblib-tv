# batch 754 — 剩下 5 个可跑的记账命令：4 个跑通、1 个提示撒谎，2 个零入口定性

## 起点

753 把 6 个选择/图命令跑完并对平之后，「14 个未跑记账命令」只剩这些：

| 命令 | 入口 | 753 之后的状态 |
|---|---|---|
| `createImageHdPreset` | `ImageNode.tsx:294` 芯片 | 待跑 |
| `attachAssetReferences` | `AddNodePanel.tsx:76` 生成历史 | 待跑 |
| `addResourceCohort` | `AddNodePanel.tsx:140` 本地文件 | 待跑 |
| `completeShotBreakdown` | `ShotBreakdownNode.tsx:84` | 待跑 |
| `createStoryScriptPair` | `CanvasEmptyState.tsx:49` | 待跑 |
| `duplicateNode` / `removeNode` | — | 753 已静态证明零入口 |

**本批全部不碰后端**：生成历史是本地 fixture（`fixture-hist-0/1` + `/images/*.png`），
上传是本地 PNG，字节不进图状态；逐帧拉片是本地 `setTimeout`；
故事脚本对是空画布上造两个节点。**没有触发任何真实生图/生视频。**

---

## 一、`createImageHdPreset`：入口挂在**空态**图片节点上

754a 第一版读到 `[data-image-attempt]` 在 DOM 里 **0 枚**。
按「先怀疑探针」的规矩，我没有把它写成死代码，而是去找渲染门 ——
`AddNodePanel.tsx` 的 Batch 268 注释写着：

> 新建图片节点为空占位（山形图标），不带默认示例图；
> **尝试建议行（图生图/图片高清）依赖空态渲染。**

种子画布的 5 个 image 节点全都带 `imageUrl` ⟹ 芯片不渲染。
先用面板加一个**空图片节点**（`createNode("image")` 传 `imageUrl: null`），
芯片立刻出现 2 枚：

| 芯片 | 尺寸 | `aria-pressed` | 命中校验 |
|---|---|---|---|
| 图生图 | 35×14 | `false` | `topIsSelf: true` |
| 图片高清 | 41×14 | `false` | `topIsSelf: true` |

点「图片高清」⟹ `createImageHdPreset` 跑通：

| | 读数 |
|---|---|
| 节点 | **+2** |
| 边 | **±0** |
| `past` | **+1** |
| 选中集 | 切到**新组 id** |
| 芯片 | 归 **0**（建议行属于被选中的图片节点，而选中集已移到组上） |

新建的两个节点与实现逐项对上：

| 项 | 实现 | 实测 |
|---|---|---|
| 组 | `storyboard-group` 430×452，`position = source + (320, −60)` | 430×452；源 (1346, 747) → 组 **(1666, 687)** = +320 / −60 ✅ |
| 组 title | `"预设 - 图片高清"` | 「预设 - 图片高清」 ✅ |
| 子节点 | `image` 340×330 @组内 (40, 60) | 340×330 @ (40, 60)，`parentId` = 组 id ✅ |
| 子节点 filename | `"图片节点"` | 「图片节点」 ✅ |

---

## 二、`attachAssetReferences`：去重是对的，**提示是错的**

| 动作 | 节点 | 边 | `past` | 提示 |
|---|---|---|---|---|
| attach asset 0 | **+1** | ±0 | **+1** | 「已从生成历史添加资源」178×16 `rgb(143,232,180)` |
| **再 attach 同一个 asset 0** | **+0** | ±0 | **+0** | **仍然是同一句绿色成功文案** |
| attach asset 1（对照） | **+1** | ±0 | **+1** | 同上 |

新节点的 `filename` 就是 `fixture-hist-0`，`type=image`，512×288 @ (60,60)。

### 这一格是本批最重要的产出：一处**真实缺陷**

去重逻辑本身没问题（`already-referenced` 跳过、零历史、零节点），
问题在**结果语义与文案对不上**。根因在 store：

```ts
// canvasStore.ts attachAssetReferences
if (attachedAssets.length === 0) {
  return {
    status: "accepted",          // ← 全部被跳过也返回 accepted
    reasons: [],
    attachedAssetIds: [],
    skippedAssetIds,             // ← 全量
  };
}
```

而 UI 只按 `status === "rejected"` 分流：

```ts
// AddNodePanel.tsx:78-82
if (result.status === "rejected") setStatus({ text: reasons.join(" · "), ... });
else setStatus({ text: "已从生成历史添加资源", tone: "positive" });
```

⟹ **重复添加同一素材时，用户看到绿色成功提示，而图里什么都没变。**
这正是最容易被当成「点了没反应」的那一类。

### 顺带一个静态发现

`attachAssetReferences` 有两个 profile，
`REGISTERED_ASSET_ATTACH` 在全应用**只有类型联合和 profile 表，没有 UI 调用点**
（`libtvMediaIngress.ts:11-12` / `:66`，`canvasStore.ts:427`）。
只有 `GENERATED_HISTORY_ATTACH` 接了 `AddNodePanel.tsx:76`。

---

## 三、`addResourceCohort`：2 个文件 = 2 个节点，但只有 **1 条历史**

喂 2 个本地 PNG：

| | 读数 |
|---|---|
| 节点 | **+2** |
| 边 | **±0** |
| `past` | **+1** ← 关键 |
| filename | `b754-a.png` / `b754-b.png`（两个不同） |
| 位置 | (60, 60) 与 (100, 400)（错开 40px），均 512×288 |
| 面板 | 600ms 后自动关闭 |

「+2 节点 / +1 历史」正是 Batch 453 注释承诺的
`create one node per file in a single accepted-success graph transaction`
—— 整批文件是**一个原子事务**，可以一次撤销。

文件输入是 `accept="image/png,image/jpeg,image/webp"` 的 **1×1 隐藏 input**。

### 成功提示只活到面板关闭那一刻

754a 与 754c 两次都在 700ms 之后才采样状态文本，两次都读到**空**。
密集采样后真相是：**提示确实渲染，但与面板一起在 ~500–600ms 消失**。

| 采样点 | 面板开 | 文本 |
|---|---|---|
| 16ms | ✅ | **已添加 2 个资源** |
| 184ms | ✅ | **已添加 2 个资源** |
| 350ms | ✅ | **已添加 2 个资源** |
| 514ms | ❌ | 已添加 2 个资源 |
| 717ms | ❌ | **（空）** |
| 之后 | ❌ | （空） |

`AddNodePanel.tsx` 的 accepted 分支是
`setStatus('已添加 N 个资源')` 紧接着 `window.setTimeout(closePanel, 600)`
—— 状态文案就渲染在面板**里面**，面板一关就没了。

> 规矩：提示类读数要用**时间序列**而不是单点。「没读到」先怀疑采样时刻。

---

## 四、`completeShotBreakdown`：门链 + 维度数差分 + 几何递推

### 门链（`ShotBreakdownNode.tsx:73-86` 的四道门逐个验到）

| 阶段 | 3 个维度的 `aria-pressed` | start 按钮 |
|---|---|---|
| 刚建好 | 全 `true` | **disabled**，文案「开始拉片」，110×14 |
| 走「从画布选择」 | 全 `true` | **enabled** |
| run 中 | 全 `true` | **disabled**，文案「拉片中」 |
| 完成后 | 全 `true` | **disabled**，文案「拉片完成」 |

节点初始 `status="empty"`，**必须先走「视频素材」菜单的「从画布选择」置 `ready`**
才能开始。执行是 **700ms `setTimeout`**。

### 维度数 → 结果数（差分）

| 激活维度 | 结果节点 | 结果边 |
|---|---|---|
| 3（storyboard + motion + music） | **5** | **5** |
| 1（只留 motion） | **1** | **1** |

> ⚠ 「1 维」那一格**第一版是作废的**：两轮采集（754c）里三次维度点击的
> `elementFromPoint` 校验**全部 `hit=false`** —— 前面那次 run 铺出的 5 张结果卡
> 把后面新建节点的维度芯片**完全盖住**了，于是「1 维」实际以 3 维跑了
> （读到 +5 节点 / 5 边）。详见返工 **R15**。
> 改由探针 **754e** 在**独立页面**上重测（每次只跑一格、跑前先断言命中）：
> 只留 `motion` ⟹ **1 个结果 + 1 条边**，`key=["motion"]`，两轮一致。

5 条的 `resultKey` 是 `storyboard-01 / storyboard-02 / storyboard-03 / motion / music`，
与 `lib/shotBreakdownResults.ts` 的定义表（storyboard 3 + motion 1 + music 1）**逐条对上**。

### 几何逐项对账

5 张结果卡的 x **全部相同** = 源绝对 x + 宽 + 120；y 逐个递推：

| # | resultKey | 尺寸 | y | 与上一张的关系 |
|---|---|---|---|---|
| 1 | storyboard-01 | 1040×**680** | 617 | 起 = 源 y − 80 |
| 2 | storyboard-02 | 1040×**680** | 1345 | 617 + 680 + **48** = 1345 ✅ |
| 3 | storyboard-03 | 1040×**350** | 2073 | 1345 + 680 + 48 = 2073 ✅ |
| 4 | motion | 1040×680 | 2471 | 2073 + **350** + 48 = 2471 ✅ |
| 5 | music | **324×220** | 3199 | 2471 + 680 + 48 = 3199 ✅ |

**跨三种高度全对** —— 如果实现里把 680 写死、或漏掉那个 48，这里立刻会跳。

每条边形如 `e-<sourceId>-<nodeId>`，5 条全是「源 → 结果」。

### 两条守卫

- **已有结果不重跑**：第二次点 start ⟹ 节点 ±0、边 ±0、`past` ±0（`existingResults.length > 0`）
- **维度全关按钮锁**：用**全新节点、在任何 run 之前**逐个关掉 3 个维度 ⟹ start **disabled**

第二格试过两次都**没拿到**：

- 754b 是在 run **之后**关的维度 ⟹ `status` 已是 `complete`，按钮早被 complete 门锁了，
  测的是 complete 门不是维度门；
- 754c 换了新节点但仍在同一次 run **之后** ⟹ 芯片被结果卡盖住，三次点击 `hit=false`。

最后由 754e 拿到：**独立页面、新节点、run 之前**逐个关掉 3 个维度
⟹ `allDimsOff=true`、`startDisabled=true`、零节点变化，
文案仍是「开始拉片」（因为没跑过，`status` 还是 `ready`），两轮一致。

---

## 五、`createStoryScriptPair`：第四条多选生产者

入口只在**空画布**（`page.tsx:1583` `flowNodes.length === 0`），
所以先切到 `canvas-1`：

| | 读数 |
|---|---|
| `[data-canvas-trigger]` | 76×32，文案「画布 2」 |
| 画布行 | 2 行，各 222×40；`data-canvas-active` 分别 `true` / `false` |
| `canvas-1` 切过去后 | **0 节点 / 0 边 / `past` 0** |
| 空态芯片 | **4 枚**：故事脚本生成 126×48 / 角色三视图 112×48 / 全能参考生视频**SD 2.5** 194×48 / 音频生视频**SD 2.5** 166×48 |

点「故事脚本生成」⟹

| | 读数 |
|---|---|
| 节点 | **+2** |
| 边 | **±0** |
| `past` | **+1** |
| **选中集** | **2** |

两个节点与实现对上：`text` 350×180、`content="剧本"`；
`script-v2` 350×350、`title="脚本生成器"`；
**两节点中心 y 相同**、**script x = text x + 350** ——
即两个节点各自按自己的尺寸取视口中心（同一点），再把 script 的 x 偏移 +350。

⟹ 这是 753 之后发现的**第四条多选来源**：

| # | 来源 | 要不要修饰键 |
|---|---|---|
| 1 | `Meta` + 点击 | 要（仅 macOS） |
| 2 | `Shift` + 拖框选 | 要 |
| 3 | `ungroupSelectedNodes` 执行完 | 不要 |
| 4 | **`createStoryScriptPair` 执行完** | 不要 |

### 另外 3 枚芯片是未接入分支

点「角色三视图」⟹ 节点 **+0** + 提示「本地原型：快速生成入口未接入」。

顺带又一次印证「**含角标的按钮不能用精确文本匹配**」：
两枚芯片的 `textContent` 是「全能参考生视频**SD 2.5**」「音频生视频**SD 2.5**」。

---

## 六、判据

**16 条**（14 条两轮一致 + 2 条静态），轮间整页 `reload` ⟹ zustand 回到种子，两轮独立。
验收器 **54/54**（静态 19 + 产物 7 + 运行时 17 + 原始读数交叉核对 11）。

两轮比对**没有手写「哪些字段易变」的路径表**，改成按 `createNodeId()` 的
生成值形态识别（`<prefix>-<epochMillis>-<rand6>`）⟹ 替换成 `<generated-id>`。
**diff 为空。**

判据 11 与 13 各有半边来自**独立页面的补充采集（754e）**，
那两格各自再跑两轮，也一致。

| # | 判据 | 关键读数 |
|---|---|---|
| 1 | 芯片依赖空态渲染 | 种子 **0** 枚 → 加空图片节点后 **2** 枚 |
| 2 | `createImageHdPreset` 记账 | 节点 **+2** 边 ±0 `past` +1，选中集=新组 |
| 3 | 高清预设几何 | 组 430×452 @源+(320,−60)；子 340×330 @组内(40,60) |
| 4 | attach 记账 | 节点 +1 `past` +1，提示 178×16 绿 |
| 5 | **重复 attach 提示撒谎** | 节点 +0 `past` +0 **但文案仍是成功** |
| 6 | 去重是逐 assetId 判的 | 换 asset ⟹ +1 |
| 7 | `REGISTERED_ASSET_ATTACH` 零入口 | grep 命中 0 个调用点 |
| 8 | cohort 是单个图事务 | **+2 节点 / +1 历史** |
| 9 | cohort 提示只活到面板关闭 | 16–514ms 可见，717ms 已空 |
| 10 | 逐帧拉片门链 | empty→disabled / ready→enabled / 拉片中 / 拉片完成 |
| 11 | 维度数→结果数差分 | 3 维 **5** 条 / 1 维（只留 motion）**1** 条 |
| 12 | 结果几何递推 | y = 上一张 + 高 + **48**，跨 3 种高度 5 步全对 |
| 13 | 两条守卫 | 二次 start 零变化；**run 之前**维度全关 ⟹ disabled |
| 14 | 故事脚本对 = 第四条多选入口 | 节点 +2，**选中集 = 2** |
| 15 | 空态另 3 枚芯片未接入 | 节点 +0 + 「本地原型：快速生成入口未接入」 |
| 16 | `duplicateNode`/`removeNode` 零入口 | 沿用 753 验收器的静态断言 |

---

## 七、探针与验收器返工八处（**全是我自己的错**）

| # | 批次 | 错在哪 | 规矩 |
|---|---|---|---|
| **R8** | 754a | 把 Playwright 引擎选择器 `text=…` 传进了 `querySelector` ⟹ `SyntaxError` 整轮中止 | 页面内 JS 只吃标准 CSS；按文本找元素要自己遍历 `querySelectorAll('button')` 再 filter |
| **R9** | 754c | 两轮比对手写「易变字段路径表」，**漏了 3 个**（子节点 `parentId`、选中集 ids、结果的 `sourceBreakdownId`）⟹ 报出 3 处假不一致 | 不要维护路径表；改成按**生成值的形态**识别（正则） |
| **R10** | 754d | 想测 `accept` 拒绝路径，却用 `set_input_files` 喂 `.txt` ⟹ `set_input_files` **绕过 `accept` 过滤**，读到「被接受」+1 节点 | 程序化赋 file ≠ 用户选 file；该格作废，进不声称 |
| **R11** | 754a | 三个维度的 `click()` 放在同一 tick ⟹ `toggleDimension` 从同一份 render 闭包算 `next`，三次写同一 key 被后写覆盖，**只关掉 1 个** | 测会改 state 的连续交互要**一次一个、等一拍** |
| **R12** | 754a | **（正面样本）**读到 0 枚芯片没有当成死代码，而是去找渲染门（Batch 268 注释「依赖空态渲染」）⟹ 754b 跑通了 | 「元素不存在」和「这条路径不存在」是两件事；先找渲染门再下结论 |
| **R13** | 754a/754c | cohort 提示两次都采样到空，差点写成「提示不渲染」⟹ 密集采样后读到「只活到面板关闭」 | 提示类读数用**时间序列**，不用单点 |
| **R14** | 754 验收器 | 验收器**第一版 50 项里 6 个 ❌**，3 个是正则写错：① 找 `data-history-asset={index}` 而源码是**字面量** `="0"`/`="1"`；② 排除 `REGISTERED_ASSET_ATTACH` 时只排掉 `profileId:` 行、漏了 profile 表的**键名行**；③ 两轮 diff 断言**直接用了 754c 那个已知有缺陷的路径表结果** | 静态断言的正则先看真实源码字面量再写；验收器内部要**复用同一个**过滤实现，不要一处手写路径表、另一处用正则 |
| **R15** | 754c | **测试顺序污染**：前面那次 run 铺出 5 张 1040×680 结果卡，把后面新建节点的维度芯片**完全盖住** ⟹ 三次 toggle 的 `hit=false`、一次都没点中。**最险的是我差点把这两格当读数写进判据** | 会铺满画布的测试要**每格独立开一页**；点击前断言命中，`hit=false` 就**当场记失败并停下** —— 顺序污染产生的是「看起来合理但其实没测到」的读数，比缺读数危险得多 |

**R10 和 R12 是一对**：R10 是把探针的能力当成了产品的能力，
R12 是把「探针没做到」当成了「产品没有」。

**R15 是本批最险的一处**：它没有报错、没有空读数，而是产出了
**看起来完全合理**的读数（「1 维 ⟹ 出 5 条结果」——只是那个「1 维」从来没成立过）。
比缺读数更难发现，因为它有数字。

---

## 八、待拍板（需改 `src/`，等授权）

1. **重复 attach 的提示要不要改** —— 建议按 `skippedAssetIds.length > 0` 分支
   给「已存在，未重复添加」之类的中性文案，而不是绿色成功。
2. **cohort 成功提示要不要活久一点** —— 现状是与面板同生共死（~500ms），
   要么延后 `closePanel`，要么把提示移出面板（toast）。
3. **`REGISTERED_ASSET_ATTACH` 接不接** —— 与 `setEdges` / `duplicateNode` /
   `removeNode` 同族：store 支持、UI 不接。接还是删。
4. **高清预设这组是不是该有图** —— 造出来的是 340×330 的空占位图节点
   （`aiGenerated: true` 但 `imageUrl` 为空），点完「芯片归 0」也更反直觉
   （建议行属于被选中的图片节点，而选中集被移到了组上）。要不要点完仍选中源节点？
5. **空态 3 枚未接入芯片** —— 是保持「明确告知未接入」（现状）还是先隐藏。
6. **逐帧拉片 2 维那一档（应出 4 条）** 没测 ⟹ 要不要补一格。

---

## 九、不声称

- 「组相对源节点 +(320, −60)」来自 754b **单轮** —— 两轮那格 `source` 读空了
  （加完节点后连拍两次 snap，第一次还没渲染出来）；其余几何两轮逐项一致。
- `addResourceCohort` 的 `accept` 拒绝路径**没测成**（见 R10）；`rejected`
  分支（数量超限等）也没测。
- 逐帧拉片只验了 3 维（出 5 条）与 1 维（出 1 条）两档，**2 维（应出 4 条）没测**。
- 754c 的「1 维差分」「维度门」两格读数**全部作废**（顺序污染，见 R15），
  对应半边由 754e 在独立页面重测；754e 只挑「没跑过」的节点
  ⟹ **「跑完的节点还能不能改维度」没验**。
- `completeShotBreakdown` 的 700ms `setTimeout` 用固定等待 1.5s 覆盖，
  **没有量真实耗时**。
- 结果节点的 `data.items` 内容没逐条读，只读了 `resultKey` / 尺寸 / 位置。
- `REGISTERED_ASSET_ATTACH`、`duplicateNode`、`removeNode` 的零入口是**静态**结论。
- `canvas-1` 只创建了两个节点就撤销；**多画布各自的视图/历史隔离没验**。
- 空态另外 3 枚芯片只点了 1 枚。
- **本批没有与源站对照**这批命令。

---

## 产物

| 文件 | 内容 |
|---|---|
| `runtime-audit.json` | 16 条判据 + 实现对账 + 两轮比对（生成 id 形态过滤）+ 6 条返工 + 不声称清单 |
| `verify-report.json` | 验收器输出 |
| `../../scripts/verify-liblib-batch754.py` | 判据校验器（静态 + 产物 + 原始读数交叉核对） |
| `/tmp/dbg754{a..e}.py` | 5 个探针（e 是补测两格的独立页面版）；`/tmp/vb754{a..e}.json` 原始读数；`/tmp/mk754audit.py` 汇编器 |
