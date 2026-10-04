# batch 760 — 分组框的拖动是**单向**的；`canvasTool` 两态行为完全正确，但底栏那枚工具按钮把状态绑错了对象

## 起点

757 结案时留了一条「不声称」：**分组框本身能不能被拖动，没测**。同一批还留了
`canvasTool` 两态（`select` / `pan`）的行为没测。759 则留了一条「新建项目」
没单独验。本批把前两条结清——第三条（`/project` 的新建项目）留在 761。

选题时先做静态复核，发现 `StoryboardGroupNode` 在 757 里是「框与成员无任何跟随
关系」。这个说法当时只有**一个方向**的证据（拖子节点，框不动），所以本批第一件事
就是去量另一个方向。量出来是：**跟随关系存在，但只有一个方向**。

同时静态复核扫到一处对不上的东西（`src/components/LeftSidebar.tsx:156`，一行里
`label` 和 `active` 跟的是两个不同的状态源），于是临时加了探针 c。

三段探针都跑满两轮且一致：

| 探针 | 原始读数 | 轮次 | 一致 |
|---|---|---|---|
| a | `/tmp/vb760a.json` | 2 | ✅ |
| b | `/tmp/vb760b.json` | 2 | ✅ |
| c | `/tmp/vb760c.json` | 2 | ✅ |

---

## 一、更正 757：跟随关系不是「没有」，是**只有一个方向**

757 的判据写的是「`storyboard-group` 框与成员**无任何跟随关系**」。这句话当时只有
单向证据，属于**过度概括**。本批把另一个方向量出来了：

拖 `g-EFbbHpwq5w`（722×460，带子节点 `v-UGQZzZOpbv`）的框内空白点 (1021,168)，
位移 (+110,+70)：

| 量 | 值 |
|---|---|
| `groupDelta`（store 绝对位移） | **[258, 165]** |
| `childAbsDelta`（子节点绝对位移） | **[258, 165]** |
| `childRelDelta`（子节点相对父位移） | **[0, 0]** |
| `childRelBefore` / `childRelAfter` | `{x:62,y:62}` / `{x:62,y:62}` |
| `parentIdKept` | true |
| `childStillInsideBox` | true |
| `pastDelta` | 1 |

**子节点的绝对位移与父框的位移逐位相同，相对位移恒为 [0,0]** —— 也就是子节点被父
框**完整带着走了**，相对布局一点没变。这是 React Flow 父子坐标系的标准行为。

于是两批合起来才说得清：

- **父动 → 子跟**（本批实测，位移逐位相同）
- **子动 → 父不跟**（757 实测，横向拖出 501px，框不移动也不缩放）

⟹ **跟随关系是单向的：父动子跟着，子动父不跟。**

这不是「零跟随」，757 的结论范围要收窄成「子→父方向完全没有」。757 的判据本身
没错（它量到的那一格读数是真的），错的是把一个方向的观察写成了全称命题——按 R32
的规矩，收窄上一批的结论要在这里显式写出来。

顺带一个正面结论：这个拖动**可以撤销**。`Cmd+Z` 之后 `groupRel` / `groupDom` /
`childRel` / `childAbs` 四组坐标全部回到 before，`past` 从 1 回到 0。

## 二、分组框本身**能**被拖动，包括空组

757 留下的第二个疑问：

| 分组 | 尺寸 | 空白点 | 移动 | `pastDelta` | 拖后 children |
|---|---|---|---|---|---|
| `g-EFbbHpwq5w` | 722×460 | (1021,168) | true | 1 | `["v-UGQZzZOpbv"]` 不变 |
| `g-245IDFh8sB` | 430×452 | (918,419) | true | 1 | `[]` 不变 |

空组（757 验过：成员归零后照样画 430×452 的完整框 + 标题 + 两个 20×20 handle）
照样能整体拖动。这条本身不是缺陷，但它把 757 的画面补完整了——**空组是一个可以被
拖来拖去的空壳**，不是残骸。

## 三、★ `canvasTool` 两态 × 三路手势：行为完全正确

两态各三路，起点都先过 `elementFromPoint` 断言命中（hit=false 当场记失败），
**每格之前先 `Meta+0` 复位视口**：

| | pane 左键拖 | pane 中键拖 | 拖节点（子节点 `v-UGQZzZOpbv`） |
|---|---|---|---|
| `select` | **否**，`deltaX=0` | **是**，`deltaX=+200` | **是**，`childDelta=[258,0]`，`pastDelta=1` |
| `pan` | **是**，`deltaX=+200` | **是**，`deltaX=+200` | **否**，`childDelta=[0,0]`，`pastDelta=0` |

`pan` 态再拖分组框：`groupMoved=false`、`pastDelta=0`、`childMovedAbs=false`
⟹ 分组框和普通节点一样，`pan` 态下都不可拖。

这与静态读法逐项吻合，**没找到行为缺陷**：

- `src/app/page.tsx:1550` `panOnDrag={effectivePan ? [0, 1] : [1]}`
  —— `[1]` 是**仅中键**，`[0,1]` 是**左键 + 中键**
- `src/app/page.tsx:1554` `nodesDraggable={canvasTool === "select" && !effectivePan}`
  —— `pan` 态恒 false
- `src/app/page.tsx:477` `effectivePan = canvasTool === "pan" || isSpacePressed`

顺带第三次钉死 757：`select` 态拖子节点时 `groupMoved=false`。同一个探针里，
「父拖子跟」「子拖父不跟」两件事同时成立，不必跨批次拼接。

`data-canvas-tool` 在两态下的 class 差异只有一处：`pan` 态多一个 `cursor-grab`。

## 四、探针缺陷：760a 的「`pan` 态节点点不到」是我量错了

760a 报 `tool_pan.nodeHit = false`。按规矩，`hit=false` 当场就该记失败停下，
**不能解释成「节点在 pan 态不可拖」继续往下跑**。本批重测，原因是探针自己：

760a 的四格共用一个视口，`select` 格里左键拖（无平移）、中键拖（+200），到了
`pan` 格累计平移已达 400px，节点被推出视口，`NODE_PT` 因此返回 null。

760b 每格之前都 `Meta+0` 复位，两态的命中点**回到同一个坐标**：

- `select` 态 `nodePoint = {"x":1068,"y":204}`
- `pan` 态 `nodePoint = {"x":1068,"y":204}`

⟹ 起点命中没问题，**`pan` 态拖不动是真的**（`childDelta=[0,0]`、`pastDelta=0`）。
760a 那一格作废，记入返工 R34。

这条也是「每格固定动作清单含 `Meta+0`」这条规矩的又一个正例：batch 760a 违反了它，
代价是一格结论作废。

## 五、缺陷（中）：底栏工具按钮的 `aria-pressed` 跟错了对象

`src/components/LeftSidebar.tsx:156`，**一行里两个状态源**：

```tsx
<ToolButton
  label={canvasTool === "pan" ? "抓手工具" : "移动"}   // 跟 canvasTool 走
  active={activePrimaryPanel === "move"}               // 跟面板开关走
  onClick={() => togglePanel("move")}
/>
```

`ToolButton` 把 `active` 同时接到 `aria-pressed={active}`（`:47`）和高亮底色
`active && "bg-white/10 text-white"`（`:51`）。走一遍真实路径，每步同时记
`canvasTool` / 面板开合 / `aria-label` / `aria-pressed` / 计算后底色：

| 步骤 | `canvasTool` | 面板 | `aria-label` | 图标 | `aria-pressed` | 底色 |
|---|---|---|---|---|---|---|
| C0 基线 | `select` | 关 | 移动 | `mouse-pointer-2` | **false** | 透明 |
| C1 点按钮开面板 | `select` | **开** | 移动 | `mouse-pointer-2` | **true** | oklab 白 10% |
| C2 面板内选「抓手工具」 | **`pan`** | 关 | **抓手工具** | **hand** | **false** | 透明 |
| C3 面板关着按 `H` | **`pan`** | 关 | **抓手工具** | **hand** | **false** | 透明 |
| C4 面板内选回「移动」 | `select` | 关 | 移动 | `mouse-pointer-2` | **false** | 透明 |

- **`label` 跟工具：5/5 步全对**（`aria-label`、`title`、图标三者同步翻转）
- **高亮跟工具：5 格里只有 2 格一致，而那 2 格恰好都是 `select` 态**
  - C1：画布在 `select`，但高亮亮着——面板开着而已
  - C2：画布已经切成抓手工具，**高亮灭了**
  - C3：同上

最扎人的是 C2：**你刚在面板里点了「抓手工具」，`selectTool` 里那句
`setPrimaryPanel(null)`（`:141`）把面板关掉，高亮随之熄灭——选完工具的那一刻，
恰恰是按钮说「没在用任何工具」的那一刻。**

C3 是隐藏入口：`page.tsx:1373` 的 `H` 快捷键在界面上**没有任何提示**，按下去之后
唯一的变化是图标从 `mouse-pointer-2` 变成 `hand`；`aria-pressed` 纹丝不动。

**阳性对照**：面板里两枚条目的青色圆点确实跟着 `canvasTool` 走（C1 时 `dots =
[true, false]`，对应 `select`）。所以**「指示当前工具」这件事有实现**，坏的是底栏
那枚**常驻**按钮绑错了对象——它是唯一一块一直显示在屏幕上的工具控件，却不表达工具
状态。面板一关，全屏就没有任何东西告诉用户现在用的是哪个工具。

修的方向（需改 `src/`）：要么 `active` 改跟 `canvasTool`；要么保留现在的语义，
但那就该用 `aria-expanded` 而不是 `aria-pressed`——现在这枚按钮是个 toggle
button，`aria-pressed` 按契约必须反映被 toggle 的状态，而它和同一枚按钮的
`aria-label` 指向两个不同的状态源。

顺带：`ToolButton` 没有任何 `data-*` 测试钩子（底栏这一排按钮都没有），和 758 记的
钩子覆盖问题同源。

---

## 六、`data-canvas-tool` 是死属性

运行时 DOM 里带这个属性的元素恒为 **1** 个（两态都是 1）；全 `src/` 搜索
`data-canvas-tool` 只有 `page.tsx:1540` **写入**一处，**零读取方**。

两态切换时它唯一的作用（如果有）只能是通过属性选择器做样式，但实测 class 差异只有
`cursor-grab` 一个，而那是由 `:1538` 的 `className` 表达式直接算的，与该属性无关。

## 七、判据（14 条）

1. 分组框 `g-EFbbHpwq5w` 自身可拖：`groupMoved=true`、`pastDelta=1`。
2. 空组 `g-245IDFh8sB` 自身也可拖：`groupMoved=true`、`pastDelta=1`。
3. 拖框后子节点跟着走：`childAbsDelta=[258,165]` 与 `groupDelta=[258,165]` 逐位相同。
4. 子节点相对父的位移恒为 `[0,0]`，`childRelBefore == childRelAfter == {x:62,y:62}`。
5. 拖框后 `parentId` 未变、`childStillInsideBox=true`。
6. `Cmd+Z` 后 `groupRel`/`groupDom`/`childRel`/`childAbs` 四组坐标全部复原，`past` 1→0。
7. **757 结论收窄**：跟随关系是单向的（父动子跟 / 子动父不跟），不是「无任何跟随关系」。
8. `select` 态：pane 左键拖不动（`deltaX=0`）、中键拖得动（`+200`）、节点可拖（`childDelta=[258,0]`、`pastDelta=1`）、拖子节点时 `groupMoved=false`。
9. `pan` 态：pane 左键（`+200`）与中键（`+200`）都能拖、节点**不可**拖（`childDelta=[0,0]`、`pastDelta=0`）。
10. `pan` 态分组框也不可拖：`groupMoved=false`、`pastDelta=0`。
11. 该矩阵与 `page.tsx:1550` / `:1554` / `:477` 的静态读法逐项吻合 ⟹ **`canvasTool` 两态行为无缺陷**。
12. **缺陷**：`aria-pressed` 与同枚按钮的 `aria-label` 指向不同状态源——`label` 跟 `canvasTool`（5/5 步全对），`active` 跟 `activePrimaryPanel`；高亮与真实工具相反的 3 格为 C1（工具 select 却亮）、C2/C3（工具已 pan 却灭）。
13. 阳性对照：面板内青色圆点跟着 `canvasTool` 走（C1 `[true,false]` 对 `select`）⟹ 指示机制存在，坏的是底栏常驻按钮。
14. `data-canvas-tool` 运行时元素数恒 1，`src/` 内零读取方（全仓仅 `page.tsx:1540` 一处写入）。

## 八、返工五处（三处探针 + 一处结论纪律 + 一处验收器）

- **R34（探针 c，派生层读错键名）**：把 dict 的 `label` 写成 `"aria-label"`、
  `ariaPressed` 写成 `"aria-pressed"`，三个派生布尔全成**恒定常数**
  （`labelMatchesTool` 恒 false、`pressedIsTrue` 恒 false、
  `highlightMatchesTool` 恒 true），**与原始读数直接矛盾**（C0 的 `label` 明明是
  「移动」而工具正是 `select`）。按「读数与已确认结论冲突是最可靠的探针缺陷信号」
  这条规矩回头查，才定位到键名。

  **这次最值得记的一条**：`highlightMatchesTool` 恒 true，**而两轮判定照样通过**
  ——确定性错误执行两遍必然一致。所以「两轮一致」**不能**单独当作派生层正确的
  证据。产物里已把这条写进 `twoRound.caveat`，并让验收器对原始读数做叶子级核对，
  派生量必须能从原始 JSON 现算出来。

- **R35（探针 a，未复位视口导致一格作废）**：760a 四格共用一个视口，累计平移 400px
  把节点推出视口，`pan` 态 `nodeHit=false`。已按「hit=false 当场记失败」重测——
  结论是**探针错了，产品没错**（`pan` 态节点确实不可拖，但证据要换成 760b 的）。

- **R36（探针 a，缺格子）**：760a 拖分组框时只记了 `children` 列表（`parentId` 还在），
  **没记子节点位置** ⟹ 当时只能说「parentId 没变」，不能推断「子节点没跟着动」。
  760b 补上 `childAbsDelta` / `childRelDelta` / `childStillInsideBox`，并且这个补充
  直接把 757 的结论推翻了一半。

- **R37（结论纪律）**：760a 的 `pan` 态读数「看起来」完全支持「pan 态节点不可拖」，
  差点直接落进判据。是 R35 的复测才让它变成「起点没命中」。**一个结论和自己的直觉
  一致时，反而要多查一遍它是怎么来的。**

- **R38（验收器，13 发阴性对照里有 3 发漏放）**：首版验收器 45/45 全过，但注入式
  阴性对照有 3 发蒙混过关，全是同一类：
  - 「单向跟随」「pan 态拖框」这类事实**各存两份**（`findings` 与判据证据），
    只改其中一份 ⟹ 检查器仍从另一份读到真值；
  - 只守住了**派生布尔**，没守住**被派生的原始字段**——伪造 `steps[2].ariaPressed`
    时派生量没跟着改，「产物 vs 重算」仍然相等。

  **这是 batch 759 的 R33 原地复发。**补 7 条结构检查：两份读数必须同源、
  5 格的 `canvasTool`/`panelOpen`/`label`/`ariaPressed` 逐格与 `/tmp` 原始读数对账、
  三条「派生量必须能由该格原始字段现算得出」的自洽检查。

  补完 **52/52 通过、阴性对照 16/16 全拦**，且每发都由对应的那条检查拦下
  （报告里 `firstFail` 字段可查）。

## 九、待拍板（需改 `src/`，等授权）

1. **底栏工具按钮**：`active` 改跟 `canvasTool`（工具态高亮）还是保留面板语义但改用
   `aria-expanded`？前者会让「面板开着」失去指示（需要另找办法），后者只修 a11y 契约、
   不修「关掉面板就看不到当前工具」。
2. **`H`/`V` 快捷键无提示**：界面不写这两个键，但面板里却标着 `V` / `H` 角标
   （`LeftSidebar.tsx:68` / `:74`）——是入口该露出来，还是角标该去掉？
3. **分组框跟随成员**（757 的老项，现在范围更准了）：只需要实现**子→父**方向
   （拖子节点时重算 bounds）；父→子方向已经是好的，不要一起改坏。
4. **`data-canvas-tool`**：接（给样式或测试用）还是删？全仓零读取方。
5. **`ToolButton` 补 `data-*`**：底栏一排工具按钮全无测试钩子（758 同源问题）。

## 十、不声称

- **没有与源站对照**：全部读数来自 clone（4317），源站画布未参与本批。
- **`pan` 态在分组框上左键拖时，画布是否跟着平移，没测**：只记了 `groupMoved` /
  `pastDelta`（两者都 false），没有同时记 viewport 位移。`nodesDraggable=false` 时
  按理会冒泡到 pane 触发平移，但**没量就不能说**。
- **`Space` 临时平移态**只引 757 的三路实测（batch 760 没重测），760b 的矩阵只覆盖
  `canvasTool` 两个静态态。
- **只测了画布空白区与节点主体**：分组框上两个 20×20 handle、节点上的各类 handle
  在两态下能不能拖/能不能连，本批没测。
- **一次 zoom 档位**：760b 的 store 位移（258/165）与屏幕位移（110/70）之比约 2.35，
  即当轮 zoom ≈ 0.43；换 zoom 后分组是否仍精确跟随（相对位移仍为 [0,0]）未复验。
- **只测了一个带子分组和一个空分组**；757 那个 501px 拖出场景没有重做。
- **底栏按钮只测了 5 个状态格**，没有遍历「面板开着 + 按 V/H」这类组合（面板开着时
  按快捷键，`aria-pressed` 会与 label 同时矛盾，未测）。
- **没有测键盘可达性**：底栏按钮能否 Tab 到、Enter/Space 能否触发。
- **`H`/`V` 与 758 查到的 `Tab` 开面板等快捷键的冲突面**没查。

## 产物

- `docs/research/liblib-canvas-batch760-2026-10-01/runtime-audit.json`
- `docs/research/liblib-canvas-batch760-2026-10-01/README.md`（本文）
- `scripts/verify-liblib-batch760.py`（三层：静态 `src/` 复核 / 产物层 / 原始读数叶子级交叉核对）
- 探针：`/tmp/dbg760a.py`、`/tmp/dbg760b.py`、`/tmp/dbg760c.py`
- 原始读数：`/tmp/vb760a.json`、`/tmp/vb760b.json`、`/tmp/vb760c.json`
- 汇编器：`/tmp/mk760audit.py`（产物全部数字现算，不手抄）
