# batch 792 — 组合 (G) 跨分组多选时**静默掏空已有分组**（静默数据丢失）

## 为什么选这件事

790 修「3 个功能点不到」，791 修「双击入口从未触发」。本批是台账里还没被
修掉的第三条高严重度读数（batch 756）：选中跨分组的多个节点按 `G`（组合），
**已有分组被静默掏空**——不是画错了，是**数据没了**。

## 承重事实（756，本批**独立复现**而不是引用）

`groupSelectedNodes` 的 `children` 过滤只把 `storyboard-group` **自己**排除：

```ts
// src/store/canvasStore.ts（改前）
const children = currentCanvas.nodes.filter(
  (node) => selectedIds.has(node.id) && node.type !== "storyboard-group",
);
```

而 re-parent 的依据是 `absolutePositions`（**由 `children` 生成**）⟹
**在选区里的旧分组**既不进新组、也不移动，**但它的成员**同样在选区里
⟹ 被改写成**新组**的子节点 ⟹ 旧分组 `children` 归零、退化成空壳，
界面上只是「组合成功」。

### pre 实测（与 756 逐项吻合）

| 读数 | 值 |
| --- | --- |
| 选区 | 10 |
| `g-EFbbHpwq5w` children | **1 → 0** |
| 新组 children | 8 |
| toast / alert / status | **0**（零提示） |

## ★ 修法：只堵破坏，**不改**既有设计决定

既有决定是「分组不参与组合」（`type !== "storyboard-group"`）。本批**保留**它，
只补一条：

> **所属的组也在选区里**的节点，一律不进 `children`。

于是那个成员既不会被拽进新组、也不会脱离原组。

```ts
const selectedGroupIds = new Set(
  currentCanvas.nodes
    .filter((node) => selectedIds.has(node.id) && node.type === "storyboard-group")
    .map((node) => node.id),
);
const children = currentCanvas.nodes.filter(
  (node) => selectedIds.has(node.id)
    && node.type !== "storyboard-group"
    && !selectedGroupIds.has(node.parentId ?? ""),
);
```

## 读数（同一份探针，pre / post 各 2 轮，3 臂）

| 臂 | pre | post |
| --- | --- | --- |
| ★ 选中全部 → `g` | 旧分组成员 **1 → 0** ✗，新组 children 8 | 旧分组成员 **无减少** ✓，新组 children **7** |
| 阳性对照一：组 + 它自己的成员 → `g` | 零变化 | 零变化 |
| 阳性对照二：两个散节点 → `g` | 节点 +1、新组 children **2** | 节点 +1、新组 children **2** |

★ **新组 children 8 → 7 不是退化**：少收的那 1 个正是原本会被拽走、
从而掏空旧组的那一个。少收这一点，换的是「不动别人的分组」。

★ 两条阳性对照缺一不可：少了「两个散节点」这条，一个「让 `G` 什么都不做」
的修复能同时满足 S4 与 S6。

## ★ 选区是**用 store 摆的**，不是框选出来的

`src/app/page.tsx:1574` 是 `selectionOnDrag={false}` ⟹ 拖拽**根本不产生框选**。
第一版探针照 756 的手势拖，三条臂**全部读成空读数**（选区 0 / 1 / 节点Δ 0）。

⟹ 这是本批最该记的坑：**旧读数里那个手势，在当前代码里已不可复现**。
缺陷在 `groupSelectedNodes` 本身，所以改用 `selectNodes` 摆选区才是对准靶子，
命令仍然走**真实键盘 `g`**。

## 验收

`scripts/verify-liblib-batch792.py`，**独立实现**、不 import 汇编器：一边用
正则自行定位判据并证明它落在 `groupSelectedNodes` **函数体内**，一边从 raw
的 groups 结构重新算「谁被掏空」。

- 断言 **7 条 / 3 个源码锚点 / 0 失败**（汇编器）
- 验收 **11/11**、阴性对照 **5/5**

| 对照 | 验的是 |
| --- | --- |
| N1 | 闸是**唯一**改动点，拆掉它源码侧必须判红 |
| N2 | 「pre 确实有人被掏空」这个读数**被真读了**（抹平后修复等于没发生） |
| N3 | 正常组合**仍能成**这件事必须**真的**在读 |
| N4 | 选区必须读回长度，否则「我以为选中了」和「真的选中了」分不开 |
| N5 | 受害者必须与**基线**对照才算数（756 的原话） |

### 本批踩的坑

| 编号 | 坑 | 后果 |
| --- | --- | --- |
| 复现旧手势 | 照 756 的框选手势拖 | 三条臂全是**空读数**，差点当成「缺陷已不复现」 |
| JS 箭头返回对象字面量 | `map(g => {id:…})` 被解析成**语句块** | 探针直接 SyntaxError，8 格全 FAILED |
| R25 | `src.find()` 返回**字符偏移**，却拿去和**行号**比 | S2 恒假（量纲不同） |
| 汇编器 check F | 一刀切要求「两阶段都恰好 1 个受害者」 | post 修好后当场打红 —— 正解是 pre 1 个 / post 0 个 |

## ★ 遗留：本批**没有**加任何提示

toast / alert / status 五类选择器 pre 与 post 命中都是 **0**。「选中里有
分组时用户仍然得不到任何告知」这件事**没有**被本批解决，只是「不再破坏」
了。要不要加提示、提示说什么，都需要源站采样才能定。

## 本批未覆盖

- ★ **未与源站对照**（源站需登录、点击语义未采样）⟹ 本批只保证 clone 不再
  静默破坏，**不声称**这就是源站的组合语义
- ★ **嵌套组合**（把一个已有的组连同其成员**一起**放进新组）**没实现**——
  修法是「旧组整体留在原地」，不是「旧组进新组且成员留在旧组里」
- 没测「选中里有分组 + 其他散节点」时散节点是否都进了新组（只测了 children 总数）
- 没测 `Shift+G` 解组路径、撤销路径
- `src/` 改动范围：`groupSelectedNodes` 内一个 `Set` + 过滤加一条；typecheck rc=0；
  未用 `--no-verify`，未跑别人的 build-site.sh
