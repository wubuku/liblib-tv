# batch 804 —— 点项目卡打开的新标签页，**是你点的那张**了

> 结论先行：修掉 759 记的高严重度缺陷 ①。`/project` 的画布卡原本把目标 id
> `setActiveCanvas` 到**当前标签页**，然后 `window.open("/")` 开一个**没有这个状态**
> 的新标签页 ⟹ 无论点哪张，开出来的都是默认那张。修复把目标 id 放进 URL 的查询参数，
> 由根页在挂载时消费 —— 而这**不是发明**：源站的画布地址本身就带查询参数。

## 一、缺陷与机制

```ts
// src/app/project/page.tsx —— 修复前
const openCanvas = (canvasId: string) => {
  setActiveCanvas(canvasId);      // ← 只改**当前标签页**的内存
  window.open("/", "_blank");     // ← 新标签页有**自己的** store 实例
};
```

`canvasStore.ts` 全文**没有** `persist` / `localStorage`，`activeCanvasId` 只活在内存里
（`:287` 类型、`:1175` 初始值 `"canvas-2"`）。`window.open` 开出来的新标签页从
`createInitialState` 起步 ⟹ **无论点哪张，开出来的都是 `canvas-2`**。

★ 759 实测过一遍；本批**独立复现**（两轮，见下），不是引用它的读数。

## 二、★★ 本批最关键的一条：只跑一个方向会判成「已修」

默认 `activeCanvasId` 就是 `canvas-2`。于是：

| 臂 | 修复前 | 修复后 |
| --- | --- | --- |
| 点 `canvas-1` 的卡 | 新标签页显示 **canvas-2**、10 个节点 ✗ | 新标签页显示 **canvas-1**、0 个节点 ✓ |
| 点 `canvas-2` 的卡 | 新标签页显示 **canvas-2**、10 个节点 ✓ | 新标签页显示 **canvas-2**、10 个节点 ✓ |

★ 第二条臂在**修复前就是绿的** —— 它是**默认蒙对**，不是功能生效。
只跑这一个方向，一个完全没修的版本会被判成「已修」。

⟹ 所以验收器把它单列为 **S2**：判据不是「这条臂红不红」，而是
**「它绿的时候，新标签页 URL 里到底有没有携带目标参数」**。pre 侧两条臂的
URL 都是干净的 `http://localhost:4317/`，**不带任何参数** ⟹ 蒙对被钉死。

## 三、读数（pre/post 各 2 轮，两轮逐位相同）

判据**只用 DOM**，不读 store：

- `[data-canvas-active="true"]` 所在的 `[data-canvas-row]` ⟹ 画布下拉里被标成当前
  的那一行，其 `data-canvas-row` 值**就是画布 id**（`CanvasTabDropdown.tsx:242-243`）。
- `.react-flow__node` 的**数量** ⟹ 这张画布上画了几个东西。种子数据里两张画布
  分别是 **0** 与 **10** 个节点，**数量互不相同** ⟹ 足以区分二者。

| 相位 | 点的卡 | 新标签页 URL | 新标签页显示 | 节点 |
| --- | --- | --- | --- | --- |
| pre | `canvas-1` | `…/`（无参数） | `canvas-2` | 10 |
| pre | `canvas-2` | `…/`（无参数） | `canvas-2` | 10 |
| post | `canvas-1` | `…/?canvas=canvas-1` | `canvas-1` | **0** |
| post | `canvas-2` | `…/?canvas=canvas-2` | `canvas-2` | 10 |

★ `data-project-card={canvas.id}`（`/project/page.tsx:238`）⟹ 卡片自带目标 id，
探针不必去问 store「我要点的是哪张」。

## 四、修复

```ts
// src/app/project/page.tsx
window.open(`/?canvas=${encodeURIComponent(canvasId)}`, "_blank");
```

```ts
// src/app/page.tsx（挂载时消费）
const wanted = new URLSearchParams(window.location.search).get("canvas");
if (!wanted) return;
const state = useCanvasStore.getState();
if (state.activeCanvasId === wanted) return;
if (!state.canvases.some((canvas) => canvas.id === wanted)) return;
state.setActiveCanvas(wanted);
```

`setActiveCanvas(canvasId)` **保留** —— 本标签页跟着点的那张走，本来就是对的，
实测两轮都成立（S6 无回归）。

★ **为什么用 URL 而不是给 store 加持久化**：这是**源站形状**。源站的画布地址
本身就带查询参数 —— `https://www.liblib.tv/canvas?spaceId=…&projectId=…`。
「用 URL 指定画布」不是我发明的形状。给 store 加持久化是另一件事、影响面大得多
（803 实测导演台**确实**做了持久化，画布 store 没有 ⟹ 两者行为不一致，值得单独立项）。

### 三条边界，都写在代码注释里

① 认不出来的 id **静默忽略并保留默认画布**；② 已经是当前画布就**不重复切**；
③ 用 `getState()` 取，**不把 `canvases` 引进依赖数组**。

★ 第 ① 条不是凑数：修复**引入了一条新路径**（从 URL 读 id 并切画布）⟹ 它自带
一个**新失败模式**。实测 `/?canvas=canvas-does-not-exist` ⟹ 回落到 `canvas-2`、
画布下拉 2 行可见、10 个节点、**页面正常**，两轮一致。不测它等于把新风险放进代码
却不看它。

## 五、验收结果

主检查 **8/8**，阴性对照 **6/6**（全部是**纯内存**变异，两份 raw 的 sha256 未变）。

| 阴性对照 | 打在哪个字段上 | 翻红 |
| --- | --- | --- |
| N1 | post 声称点 canvas-1 打开 canvas-2 | S3 |
| N2 | post 声称坏参数没回落到任何画布 | S7 |
| N3 | pre 声称点 canvas-1 打开的就是 canvas-1 | S1 |
| N4 | post 把两臂节点数改成相同 | S4 |
| N5 | post 声称本标签页没跟着走 | S6 |
| N6 | 反向对照：只动 `cards` 这个无关字段 | 无 |

`typecheck` rc=0、`build` 全绿。

## 六、探针返工一处（我自己，而且它差点变成一条假结论）

第一版的 `sameTabAfterClick` 是在 `/project` 页面上找 `[data-canvas-trigger]` ——
那个钩子**只存在于画布页**，`/project` 上永远找不到 ⟹ 读数恒为
`{activeCanvasId: null}`。

★ 一条**恒定无信息**的读数比没有读数更危险：它看起来像「本标签页没跟着走」。
改成读 `window.__libtv_store.getState().activeCanvasId`，并**挪到点击之后**才取。
★ 这条读数是**唯一**读 store 的地方；缺陷本体全部用 DOM 判定 ——
能读 DOM 就不读 store。

## 七、不声称

- ★ **跨标签页的未保存改动不会带过去**。新标签页看到的是那张画布的**种子内容**。
  本批只保证「打开的是那张画布」，**不保证**「是你改过的那张画布」——
  后者需要画布 store 持久化，是另一件事、影响面大得多，**未立项**。
- ★ 「新建项目」侧栏按钮（`/project/page.tsx:52-55`）仍是
  `addCanvas(); window.open("/")`，**没有**跟着改。理由：那会在新标签页里开一个
  **该标签页并不存在**的画布 id（`canvas-3` 只在当前标签页的 store 里），属于
  同一个「跨标签页不共享 store」的根问题 ⟹ 修它需要持久化，不在本批范围。
  **未测**它现在的行为。
- ★ **未与源站对照**（源站需登录）。本批的依据是「源站的画布地址带查询参数」
  这一**可观察事实**（用户给的测试地址），不是源站点击行为的实测。
- ★ pre 侧的 `invalidParam` 臂**没有**（那条路径在 pre 里根本不存在）；
  post 的 `sameTabAfterClick` 读数比 pre 的一版 probe **多**（探针改过）。
  两份 raw 因此字段不完全对称，验收器按相位分别取用，**没有跨相位比同一字段**。