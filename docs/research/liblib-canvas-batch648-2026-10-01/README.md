# batch 648 —— 清 626 第八节那 15 个「未覆盖标记」：**先分类**，再各找打开路径；顺带挖出**尺子的第五个盲区形状**

## 一句话

626 说那批标记「找不到能从 clone 自身控件打开它们的路径」。本批去查了，
发现这句话**两处都不准**：其中 **4 个根本不是浮层**，而画布页那 7 个的打开路径
**是现成的一等 store 动作**。导演台 4 个真浮层全部用**真点击**打开、626 那把尺子
原样跑完 12 格 69 枚活控件 —— 尺子立刻撞上自己的**第五个盲区形状**：
**1×1 的 `sr-only` 控件从「零尺寸不算伤亡」那道门槛底下钻了过去**。

## 1. 626 自己那份清单有两处不准

### 1a. 标题说 16，列表只有 15

626 第八节写「**9 个**导演台浮层标记与 7 个画布页」，然后列出 **8 个**导演台名字。
**第 9 个从未被点名**，因此无法被分类、打开或测量。
本批按**列表的真实长度 15** 验收，并把这条记成**继承下来的开口** ——
清单若要靠凑数去对上自己的标题数字，那它就是没法核对的。

### 1b. 「9 个导演台浮层」里有 4 个不是浮层

| 626 的名字 | 真实选择器 | 实际是什么 | 源码依据 |
|---|---|---|---|
| `pose-panel` | `[data-director-pose-panel]` | **检查器里的一段内容** | `className="space-y-4 px-4 py-3"`，无 absolute/fixed |
| `panel` | `[data-director-panels-toggle]` | 一个 **`<button>`** | `DirectorDesk.tsx` 里 `<button … data-director-panels-toggle>` |
| `mobile-panel` | `[data-director-mobile-panel-state]` | 一个**状态属性** | `={activeMobilePanel === "tree" ? "open" : "closed"}` |
| `flyout` | `[data-director-flyout-title]` | **每个 flyout 一个**的属性 | `DirectorIconRail.tsx` 里出现 **3** 次 |

而 626 **自己已覆盖的 11 个浮层里就有 3 个 flyout**
（`panorama-flyout` / `aspect-flyout` / `add-character-flyout`）——
**「已覆盖」与「未覆盖」两份清单互相打架**。

这四条分类不是凭印象写的，每条都由**源码那一行**钉住（`each-classification-is-pinned-to-the-source-line-that-made-it`）。

### 1c. 一个顺带的确认

默认态下，15 个标记里**只有 2 个在 DOM 里**：
`[data-director-panels-toggle]` 与 `[data-director-mobile-panel-state]` ——
**而这两个正好都是「不是浮层」的那两个**。
**每一个真正的浮层在默认态都不在 DOM 里**，这既解释了为什么需要打开路径，
也从另一头印证了上面的分类。

## 2. 画布页那 7 个：路径是现成的

626 记的是「找不到打开路径」。路径是 `window.__libtv_ui_store` 上的**一等动作**：

| 标记 | 动作 |
|---|---|
| `zoom-menu` | `toggleZoomMenu` |
| `canvas-dropdown` | `toggleCanvasDropdown` |
| `asset` | `toggleAssetPanel` |
| `add-node` | `toggleAddNodePanel` |
| `agent` | `toggleAgent` |
| `shortcuts` | `toggleShortcutsPanel` |
| `share` | `toggleSharePanel` |

**不是路径不存在，是没去查 store。**

## 3. 导演台 4 个：真点击打开，626 的尺子原样跑

| 浮层 | 打开路径 |
|---|---|
| `crowd-panel` | 点 `[data-director-crowd-trigger]`（`添加群众阵列`） |
| `phone-vcam-panel` | 点 `[data-director-phone-vcam-trigger]`（`虚拟相机`） |
| `model-library-panel` | 点 `[data-director-model-library-trigger]`（`模型库`） |
| `model-library-preview-panel` | 先开面板，**再悬停一张卡** —— 源码把它门在 `previewModelLibraryItem` 上，所以是两步，单独成例 |

12 格（4 浮层 × 1920×1150 / 1440×900 / 1280×720），**69 枚活控件**：

| 浮层 | 盒 | z | 活控件 | 结构半 | 伤亡半 |
|---|---|---|---|---|---|
| `crowd-panel` | 272×208 | 20 | 5 | 0 | 0 |
| `phone-vcam-panel` | 340×322 | 30 | 2 | 0 | 0 |
| `model-library-panel` | 500×360（1280 时 330 高） | 30 | 15 | 0 | **1** |
| `model-library-preview-panel` | 498×72 | `auto` | 1 | 0 | 0 |

**结构半 0 失败**：没有任何桌面面板画在这四个浮层之上。

**伤亡半那 1 条不是缺陷 —— 但它暴露了尺子的一个洞。**

## 4. 第五个盲区形状：1×1 的 `sr-only` 控件

那 1 枚「伤亡」是：

    input[data-director-model-library-local-input]   type="file"
    box = 1 × 1        clip = auto        clip-path = inset(50%)
    命中元素 = div.absolute.inset-0（面板自己的遮罩）

626 的伤亡循环里有一道门槛：

    if (cb.width <= 0 || cb.height <= 0) continue;   // zero-size: not a casualty

而 Tailwind 的 `sr-only` **不是零尺寸**：

    position:absolute; width:1px; height:1px; margin:-1px; clip-path:inset(50%)

于是它**整条穿过 `<= 0`**，被当成一枚被遮住的活控件报了出来。
623 当年挖到的正是同一族的「零尺寸控件」盲区 —— **这里是它一个像素之外的姊妹形状**。

**两道门都差一格**：

1. 尺寸门：`<= 0` 差一像素，正确谓词是「**被裁成什么都没有**（clip / clip-path）**或 ≤ 1px**」。
2. 属性门：实测计算样式是 **`clip: auto` + `clip-path: inset(50%)`** ——
   Tailwind **v4** 的 `sr-only` 已经不用旧版的 `clip: rect(0,0,0,0)` 了。
   **只查 `clip` 属性的修法同样会漏。**

**它不是 clone 的缺陷**：`sr-only` 的 `type=file` 是标准做法，由一枚可见按钮驱动，
它那 1×1 的中心落在面板遮罩底下**正是设计如此**。
但**一条分不清「设计上的非控件」与「真伤亡」的尺子，也不该被信任去报真伤亡**。
所以本批的处置是：**记下来、判掉、钉死判据**，而不是把它从读数里抹掉：

* `every-casualty-is-a-designed-non-control-not-a-clone-defect` ——
  12 格里**每一条**伤亡都必须是设计上的非控件，且**至少存在一条**（防空转）。
* `the-zero-size-guard-is-one-pixel-short-of-the-right-predicate` ——
  钉死 `excludedBy626sGuard = false` 且 `w = h = 1`。
* `the-exempted-control-is-an-sr-only-file-input-in-the-source` ——
  **豁免本身是对源码的正则**，所以日后有人把这个 input 改成真实盒子时，
  这条检查会**变红**而不是默默放过它。

## 5. 为什么画布页那 7 个**不在本批测**

626 的 `PANELS` 竞争集**六项全是导演台选择器**
（timeline / inspector / tree / rail / viewport / workspace）。
把它们套到画布页上，`structBad` 会**恒为空** ——
那不是「通过」，是**尺子够不着**。

626 自己用 `overlay-present` 非空断言防过这一类空转，本批沿用同一原则：
**宁可记成「本批未测」并写明原因，也不产出一个空转的绿。**
画布页那 7 个连同它们的打开路径**留在案上**，交给 649 用**自己那套竞争集**去测。

## 6. 我自己写错的三处

1. **marker 数按 16 写** —— 实际 15。查下去才发现是 **626 自己的标题（9+7=16）与列表（8+7=15）对不上**，
   于是把「清单真实长度」与「继承的开口」分成两条断言，而不是把列表凑到 16。
2. **循环变量 `v` 遮住了 Verifier** —— `for k, v in matrix.items()` 之后
   `v.check(...)` 报 `'dict' object has no attribute 'check'`。
   与 642 那次 `cs` TDZ **同类**：在判据里加变量前，先把该作用域已绑定的名字读完。
3. **`Verifier.check()` 不吃 `reason=`** —— 自己临时加的参数，加进签名而不是绕开。

另有一处**探针自己写错**：第一版以为 626 的「零尺寸」门槛能接住 `sr-only`，
红在 `w=1` 上 —— **红是对的**，而且正是本批最有价值的那条发现。

## 7. 本批**不**主张的事

* **不主张**这 15 个标记没问题。
* **不主张**画布页那 7 个已被覆盖 —— 只给了路径，没上尺子，理由见第五节。
* **不主张** 626 那个从未点名的第 9 个导演台标记是什么（**猜不得**）。
* **不主张** `sr-only` 那枚是真缺陷（**它不是**）。
* **零源站断言**。

## 8. 门禁

- `scripts/verify-liblib-batch648.py`：**13 checks / 0 failures**，12 格。
- **共享判据一字未动** —— 626 的 `CENSUS_JS` 与 647 的 `AUDIT_JS` 都是只读引用，
  故本批**无需**基线对照，也无需零回归证明。
- `npm run lint` / `npm run typecheck` / `npm run build` / `npm run docs:check`
  见提交说明（既有 flake 按路径归因，不在本批）。
