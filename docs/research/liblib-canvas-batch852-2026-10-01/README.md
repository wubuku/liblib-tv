# Batch 852 — 导演台「变换类快捷键」（V／R／F）与「网格吸附」（X）

> 源站：`https://www.liblib.tv/canvas?spaceId=7709759&projectId=a860e1da8e9e4504bececda022386429`
> clone：`http://localhost:4317`
> 源站 chunk：`/tmp/liblib_srcjs2/0fmehki05gkzw.js.js`（1,018,019 字节，导演台组件）
> 本批产物目录：`docs/research/liblib-canvas-batch852-2026-10-01/`

---

## 1. 本批靶子与背景

batch 847–851 依次做完左列五段（847–849）、角色大编辑器预览区（850）、导演台**视图类**快捷键（851）。
导演台的**快捷键面板**（batch 831 照抄源站）印着 **12 组**快捷键：

| 面板左列 | 面板右列 |
| --- | --- |
| 俯视视角 `T` ／ 重置视角 `H` ／ 移动 `V` | 正面视角 `Y` ／ 网格吸附 `X` |
| 旋转 `R` ／ 缩放 `F` ／ 移动当前视角 `WASDQE` | 打组 `⌘G` ／ 解组 `⌘⇧D` ／ 撤销 `⌘Z` ／ 删除 `⌫` |

batch 851 做掉了 `T`／`Y`／`H`／`WASDQE`。**本批做剩下的「变换类」四条**：`V`（移动）／`R`（旋转）／`F`（缩放）／`X`（网格吸附）。

★ `⌘G`／`⌘⇧D`／`⌘Z` 属**结构性操作**（改画布数据、动撤销栈），留给独立批次。

---

## 2. 契约提取（机器提取，17 个片段全部唯一命中）

★ **先读源站 chunk 的逐字实现，再动手** ⟹ 探针与门禁都引用**入库的源站原文**，
而不是「面板上印着 V/R/F/X」这种 UI 文字。

`probes/extract852_contract.py` ⟹ `raw/source-852-contract.json`。
提取纪律：**每个锚点必须恰好命中 1 次**，否则记 `命中数` 并置空（不许静默取第一条）。

### 2.1 提取到的关键片段（逐字）

```js
hY=new Set(["escape","enter","v","r","f","h","x","t","y","c","d","g","delete","backspace","z"])
hX=new Set(["w","a","s","d","q","e"])
```

```js
else if("v"===n)iW("translate");else if("r"===n)iW("rotate");
else if("f"===n)iW("scale");else if("x"===n)eT(e=>!e);
```

```js
let iW=(0,o.useCallback)(e=>{if(t4&&im(),
  "emptyObject"===nf.current.selectedCategory&&"translate"!==e){
  tl("translate"),af.setMode("translate");return}
  tl(e),af.setMode(e)},[im,t4,af]);
```

```js
function p7(e,t){e.translationSnap=t?1:null}
function ha(e,t,r){e.setMode(t),e.showY=!(r&&"scale"===t)}
```

```js
[ts,tl]=(0,o.useState)("translate")     // ts = 变换模式，tl = setter
[eI,eT]=(0,o.useState)(!1)              // eI = snapEnabled，eT = setter
{snapEnabled:eI,gaussianGroundSnapEnabled:…}
```

### 2.2 修饰键条件（`hY` 块的 `&&` 链，逐字）

```js
if(hY.has(n)&&("z"!==n||e.ctrlKey||e.metaKey)&&("g"!==n||e.ctrlKey||e.metaKey)
  &&("d"!==n||e.shiftKey&&(e.ctrlKey||e.metaKey))&&("c"!==n||e.ctrlKey||e.metaKey)
  &&("h"!==n||!e.ctrlKey&&!e.metaKey&&!e.altKey)){
```

⟹ `z`／`g`／`c` 要 ⌘，`d` 要 ⌘⇧，`h` 要**无** ⌘⌥；
⟹ ★ **`v`／`r`／`f`／`x` 没有任何修饰键限制** ⟹ Shift+V 照样生效。

★ 唯一例外是 `v`：源站里 ⌘V 走的是**粘贴**分支
（`if("v"===n&&(e.ctrlKey||e.metaKey)){…paste…;return}`）⟹ ⌘V 永远到不了 `iW`。

### 2.3 ★★ 本批真踩到的坑：**手抄漏了一个字符，结论差点反了**

★ 我第一遍读 chunk 时，把 `hY` 的集合**手抄**进提取脚本，写成了：

```js
hY=new Set(["escape","enter","v","r","h","x","t","y","c","d","g","delete","backspace","z"])
          //                                  ↑ 这里的 "f" 被我漏掉了
```

★★ 于是我一度得出「**F 是死代码**，源站面板印着『缩放 F』但按 F 什么都不发生」的结论，
并准备让 clone 也**不实现 F**（以免和源站不一致）。

★★ 是提取器当场拦住的：**锚点命中 0 次** ⟹ 「我以为读到的」和「源站里真实存在的」对不上。
★ 改成正则整段提取后，真相是：

```js
hY=new Set(["escape","enter","v","r","f","h","x","t","y","c","d","g","delete","backspace","z"])
          //                            ↑ "f" 在这里（"r" 之后、"h" 之前）
```

★★ **「F 可达」** ⟹ ⟹ 后面第 3 节的源站实测也证实了（按 F ⟹ 模式真的变成 scale）。
★★ 这条已写进阴性对照 **N11**：把契约里的 `"f"` 去掉 ⟹ 门禁 S2 必须翻红
⟹ ⟹ 证明那份契约必须是**机器提取**的，手抄的会骗人。

---

## 3. 源站实测（`probes/source852_transformkeys.py` ⟹ `raw/source-852-transformkeys.json`）

### 3.1 三条读数（都只用**可见 DOM**）

1. **变换模式（主）**：底部胶囊的折叠按钮（`aria-haspopup="menu"`，实测 bbox `[789,1020,32,32]`）
   **点开后的下拉**，其中**当前模式那枚**带 `bg-white/8 text-white` ⟹ 读它的**序号**＋**键帽字母**。
   ★ 序号→模式的映射表**从 `raw/source-852-contract.json` 里解析**
   （源站原文 `R=[{mode:"translate",…,"V"},{mode:"rotate",…,"R"},{mode:"scale",…,"F"}]`）⟹ **不手打**。
2. **变换模式（副）**：折叠按钮里那枚 `<svg>` 的 innerHTML 哈希 ⟹ 同一模式应对应同一段
   ⟹ 用**前后对比**判定「图标有没有变」（自指比较，不依赖手打路径数据）。
3. **网格吸附**：右栏所有 `[role="switch"]` 的 `aria-checked` ⟹ 按 X 之后**哪一枚翻转**
   ⟹ 那枚**就是**吸附开关（★ 自证式定位，不手打中文标签）。

### 3.2 读数结果

| 读数 | 前 | 后 | 佐证 |
| --- | --- | --- | --- |
| 按 `R` | translate（序号 0／字母 V） | **rotate**（序号 1／字母 R） | 下拉 active 项移动 ＋ svg 哈希变了 |
| 按 `F` | rotate（序号 1／字母 R） | **scale**（序号 2／字母 F） | 同上（★ **F 可达**） |
| 按 `V` | scale（序号 2／字母 F） | **translate**（序号 0／字母 V） | 同上 |
| `Shift+V` | rotate | **translate** | ★ 证明源站对 `v` **无**修饰键限制 |
| 按 `X` | 网格吸附 `aria-checked=false` | **true** | 再按一次 ⟹ 回到 false（是**翻转**不是置位） |
| 冒泡阶段收到的键 | — | **0 个** | ★ 源站在 window 捕获阶段掐断了所有按键 |

★ 「两条一致」列：序号推出的模式与键帽字母推出的模式**每一步都相等** ⟹ 两条独立读法互相印证。

★ 截图：`images/852src_r-after.png`（旋转高亮）、`images/852src_f-after.png`（**缩放 F 高亮**）、
`images/852src_v-after.png`（移动高亮）、`images/852src_x-before.png` / `852src_x-after.png`（右栏吸附开关）。

### 3.3 ★ 源站还会**吞掉所有按键**（本批顺带测出来的行为）

★ 探针在 `document` 上装了一个**冒泡阶段**的 keydown 监听器 ⟹ 整个探针期间**一个键都没收到**。
⟹ 因为源站的 handler 在 **window 捕获阶段**就调了 `h4(e)`：

```js
function h4(e){e.stopPropagation(),e.stopImmediatePropagation()}
```

⟹ 事件**根本到不了 document 的冒泡阶段** ⟹ 导演台里**任何**按键都不会漏到页面其他监听器。
★ clone 没有照抄这个「全局吞键」（它只在自己的分支里 `preventDefault`）⟹ 登记为差异（§6）。

### 3.4 ★ 探针自己踩的三个坑（都写进了脚本注释）

| 坑 | 症状 | 根因 | 修法 |
| --- | --- | --- | --- |
| ① 点开了**左栏「帮助」** | 下拉找不到；**按 X 没反应** | `nav button[aria-haspopup="menu"]` 在文档顺序里**左栏那枚排在前** ⟹ 点开的是**快捷键对话框（模态）** ⟹ 模态把键吞了 | 改用结构判据：「**nav 内恰好 3 枚按钮**」的那枚才是底部胶囊的变换钮 |
| ② active 项**三枚全中** | 「active 数 = 3」 | 非 active 那枚的类名里有 **`hover:bg-white/8`** ⟹ `includes("bg-white/8")` 把三枚都算上 | 改成 **token 精确匹配**（`bg-white/8` 与 `text-white` 都是独立 class） |
| ③ **点视口**导致右栏换面板 | 开关读数变成 **0** | 点中 3D 视口会**选中一个对象** ⟹ 右栏从「环境面板」换成「对象面板」 | **不点视口**（源站的 `h5` 只在目标是输入框时早退，此时 `activeElement` 是 DIV） |

★ 另有两条「判据不可判」的修正：

- **Shift+V**：第一版按之前模式**已经是 translate** ⟹ 「没变」既可能是「无效」也可能是「本来就是」
  ⟹ ⟹ 改成**先按 R 走到 rotate 再测**。
- **键帽字母→模式的反查**：第一版拿「模式→字母」的表去反查字母 ⟹ 恒为 `None`
  ⟹ ⟹ 门禁因此一开始拿不到模式值 ⟹ ⟹ 改成双向表。

---

## 4. clone 实施

### 4.1 改动清单

| 文件 | 改动 |
| --- | --- |
| `src/components/director/directorViewportMath.ts` | 新增 `DIRECTOR_TRANSFORM_SHORTCUT_MODES`（v→translate／r→rotate／f→scale）、`DIRECTOR_GRID_SNAP_STEP = 1`、纯函数 `resolveDirectorTransformShortcutMode`、类型 `DirectorTransformShortcutCategory` |
| `src/components/director/DirectorViewport.tsx` | `DirectorViewShortcutController` 里加 `v`／`r`／`f`／`x` 四个分支；`translationSnap` 的步长由 `0.5` 改为 `DIRECTOR_GRID_SNAP_STEP`（三处） |
| `scripts/verify-liblib-batch550.py` | 只更正 docstring 里一句已过时的「0.5-unit」（**断言没动**，见 §7） |

### 4.2 键位实现（逐字对齐源站）

```ts
if (key === "v" || key === "r" || key === "f" || key === "x") {
  if (key === "v" && (event.ctrlKey || event.metaKey)) return;   // ⌘V 让给粘贴
  event.preventDefault();
  if (key === "x") { updateScene({ snapToGrid: !snapToGrid }); return; }
  applyTransformShortcut(DIRECTOR_TRANSFORM_SHORTCUT_MODES[key]);
  return;
}
```

- `applyTransformShortcut` ＝ 源站 `iW`：
  ① **正在编辑运动路径时先把路径提交掉**（源站 `t4&&im()` ⟹ clone 用 `finishMotionPathDrawing()`）；
  ② 走纯函数 `resolveDirectorTransformShortcutMode`（空对象守卫，见 §6）。

### 4.3 ★ 吸附步长：0.5 → 1（源站 `p7` 逐字）

★ clone 此前写的是 `translationSnap={snapToGrid ? 0.5 : null}`（batch 550 定的），
但源站 chunk 逐字是 `function p7(e,t){e.translationSnap=t?1:null}` ⟹ **步长是 1**。
★ 本批按源站改成 1（`DIRECTOR_GRID_SNAP_STEP`），三处 `TransformControls` 统一引用。

### 4.4 clone 实测（`probes/clone852.py` ⟹ `raw/clone-852-transformkeys.json`）

★ 判据是「**等于目标值**」，不是「变了」：读 `[data-director-transform-mode]` 的
`aria-pressed` 与 `[data-director-scene-snap-to-grid]` 的 `aria-checked`，
再用 `window.__director_store.getState()` 做**副读数** ⟹ 两条路必须一致。

| 读数 | 前 | 后 | DOM | store | 一致 |
| --- | --- | --- | --- | --- | --- |
| 按 `R` | translate | **rotate** | ✔ | ✔ | ✔ |
| 按 `F` | rotate | **scale** | ✔ | ✔ | ✔ |
| 按 `V` | scale | **translate** | ✔ | ✔ | ✔ |
| `Shift+V` | rotate | **translate** | ✔ | ✔ | ✔ |
| 按 `X` | false | **true** | ✔（DOM 开关） | ✔ | ✔ |
| 再按 `X` | true | **false** | ✔ | ✔ | ✔ |

★ 与源站逐条对表：**完全一致**。

---

## 5. 验收

### 5.1 门禁 `scripts/verify-liblib-batch852.py` — **10/10**

| 判据 | 读什么 |
| --- | --- |
| `S1` | clone 源码里的**结构**（组件／函数／常量／`data-` 属性） |
| `S2` | **源站原文**契约的 13 项逐字检查（含「`hY` 含 `f`」） |
| `S3` | 纯函数 `resolveDirectorTransformShortcutMode` 的 **6 条用例（node 实跑）** |
| `S4` | clone 读数 `②按R` 的 DOM 模式 ＋ store 模式 |
| `S5` | clone 读数 `②按F` 的 DOM 模式 ＋ store 模式 |
| `S6` | clone 读数 `②按V` 的 DOM 模式 ＋ store 模式 |
| `S7` | clone 读数 `③Shift+V` 的**起点是 rotate** ＋ 终点是 translate |
| `S8` | clone 读数 `⑤按X` 的 DOM 开关 false→true→false ＋ 两条路一致 |
| `S9` | clone 源码里的**吸附步长**（源站 `p7` 逐字 = 1） |
| `S10` | **源站**读数（R/F/V 三步、Shift+V、X 翻转、吞按键） |

★ `S3` 是**真跑**：从 TS 源码里抽出那个纯函数、去掉两处类型标注，交给 `node` 实跑 6 条用例
（不是「看代码像对的」）。

### 5.2 阴性对照 `probes/neg852.py` — **11/11**，每条**恰好**翻一条判据

| 阴性 | 变异对象 | 应当翻红 | 实测 |
| --- | --- | --- | --- |
| `N1` | 源码 math：守卫里的 `"emptyObject"` → `"emptyObjectX"` | `S3` | ✔ 恰好一条 |
| `N2` | 源码 math：`DIRECTOR_GRID_SNAP_STEP = 1` → `= 0.5` | `S9` | ✔ 恰好一条 |
| `N3` | 源码 viewport：某一处 `translationSnap` 写死 `0.5` | `S9` | ✔ 恰好一条 |
| `N4` | clone 读数 `②按R` 的「按后.DOM.模式」 | `S4` | ✔ 恰好一条 |
| `N5` | clone 读数 `②按F` 的「按后.**store**.transformMode」 | `S5` | ✔ 恰好一条 |
| `N6` | clone 读数 `②按V` 的「按后.DOM.模式」 | `S6` | ✔ 恰好一条 |
| `N7` | clone 读数 `③Shift+V` 的「按前.DOM.模式」 | `S7` | ✔ 恰好一条 |
| `N8` | clone 读数 `⑤按X` 的「按后一次.值」 | `S8` | ✔ 恰好一条 |
| `N9` | clone 读数 `⑤按X` 的「按后两次.值」 | `S8` | ✔ 恰好一条 |
| `N10` | 源站读数 `④按F` 的「按后.模式」 | `S10` | ✔ 恰好一条 |
| `N11` | ★ 契约里 `hY` 去掉 `"f"` | `S2` | ✔ 恰好一条 |

★ `N5` 故意打在 **store 那一路**上 ⟹ 证明 `S5` 真的读了 store，不只是 DOM。
★ `N11` 是 §2.3 那个坑的**复现**。
★ 全部复原后**字节级**校验一致（`复原字节级一致 = true`），门禁复跑 10/10。

### 5.3 回归 `probes/regress852.py`

★ 清单 46 条（851 的 40 条 ＋ 本批 ＋ ★ **吸附相关五条** `550`／`588`／`741`／`797`／`798`）。
★ 加这五条的理由：本批改了**吸附步长** ⟹ ⟹ 「步长改对了」与「开关语义被改坏了」必须分得开。

（结果见 §5.5）

### 5.4 受控对照 `probes/attrib852.py`

★ 把本批改过的两个源码**按字节换回 HEAD** ⟹ ⟹ 重跑旧门禁 ⟹ ⟹ 看读数**逐条有没有变**。
★ **连跑两遍**（换回源码后 4317 要热更 ⟹ 一轮的差不能当因果）。
★ 复原走**白名单**（明确列出的两个相对路径）＋ **字节备份**，不是黑名单。

（结果见 §5.5）

### 5.5 验收结果

| 项目 | 结果 |
| --- | --- |
| 门禁 `verify-liblib-batch852.py` | **10/10 通过** |
| 阴性对照 `neg852.py` | **11/11 通过**，每条**恰好**翻一条判据；复原**字节级**一致；复原后门禁回到 **10/10** |
| 回归 `regress852.py` | **47 条**，红 **6** 条：`831`／`741`／`736`／`748`／`749`／`782`；★ 盯的 **9** 条里只有 `831` 红 |
| 受控对照 `attrib852.py` | **14/15 条读数逐条完全相同**；唯一「不一致」是 **`852` 自己**（★ 预期的） |
| 构建链 | `npm run build` ✓ ／ `npx tsc --noEmit` ✓ ／ `npx eslint` ✓ ／ `npm run assertions:check` ✓ |

★ ★ **受控对照里那唯一一条「不一致」是 `852` 自己，而且是**预期**的**：

| 状态 | `852` 门禁 |
| --- | --- |
| HEAD（换回旧源码） | **rc=1 ／ 7/10 通过**（结构、纯函数、吸附步长三条判据翻红） |
| 工作副本（本批实施后） | **rc=0 ／ 10/10 通过** |

⟹ ⟹ **这正是「门禁有牙」的证明** ⟹ ⟹ 其余 **14 条**逐条相同 ⟹ ⟹ 本批**未打破**任何一条既有门禁。

★ ★ **`741` 的红已定案为旧账**：★ 回归里 `741` 也红（判据 **11/13**，`C1`／`C3` 是 `setNodes`／`setEdges`
的**条件记账**）。★ 它**看起来**与本批的吸附步长无关（741 里的 `snap()` 只是截图辅助函数），
⟹ ⟹ 但**不能靠「看起来无关」定案** ⟹ ⟹ 已在受控对照里把它加入 `TARGETS`：
**HEAD 上跑出来同样是 `rc=1`／`11/13`** ⟹ ⟹ **不是本批引入的**。

★ **`831` 的红是 batch 834 留下的历史债**（834 把引导气泡拆到 `DirectorTimelineGuide.tsx`，
而 831 的 `S14` 仍在读旧的 `DirectorTimeline.tsx`）⟹ ⟹ 与本批无关，留给独立批次。

---

## 6. 与源站的差异登记（**如实标注，不假装已对齐**）

| # | 差异 | 源站 | clone | 说明 |
| --- | --- | --- | --- | --- |
| `D1` | **全局吞键** | 导演台的 keydown 在 window 捕获阶段 `stopPropagation()+stopImmediatePropagation()` ⟹ 任何键都漏不出去 | 只在自己的分支里 `preventDefault` | clone 保留页面其他监听器能收到键（实测源站冒泡阶段收到 **0** 个键） |
| `D2` | **空对象守卫** | 选中 `emptyObject` 时，旋转／缩放降级成移动 | clone 的对象种类只有 `character`／`prop`／`camera`（`DirectorObjectKind`），**没有** `emptyObject` | ★ 规则**已实现**（纯函数 ＋ `S3` 的 6 条用例），但当前**不可触发**；等 clone 长出空对象时直接生效 |
| `D3` | **路径草稿提交** | `t4&&im()`：切模式前先把正在编辑的路径提交掉 | 用 `finishMotionPathDrawing()` 对齐 | ★ **运行时未取证**（本批没有在 clone 里真的画一条路径去触发它）⟹ 属**结构对齐** |
| `D4` | **均分缩放时隐藏 Y 轴** | `ha(e,t,r){e.setMode(t),e.showY=!(r&&"scale"===t)}` | clone 无「均分缩放」概念 | 无对应物可对齐 |
| `D5` | **吸附作用范围** | `p7` 只作用于主 gizmo | clone 三处 `TransformControls`（对象／分组 rig／路径锚点）都吸附 | 沿用 batch 550 的结构，本批只改**步长** |
| `D6` | **⌘R／⌘F／⌘X** | 源站会吞掉它们**并**触发动作（`hY` 块无修饰键限制） | clone 照抄（`r`／`f`／`x` 不做 ⌘ 排除） | ★ 刻意对齐源站；副作用是导演台里 ⌘R 不能刷新页面 |

---

## 7. 对旧结论的更正

★ **batch 550 的吸附步长**：batch 550 把网格吸附实现成 `translationSnap=0.5`，
其门禁 docstring 也这么写。★ 源站 chunk 的逐字实现是 `translationSnap = 1`
⟹ ⟹ 本批按源站改成 1，并**就地更正** `scripts/verify-liblib-batch550.py` 的 docstring。
★ 550 的**断言没动**（它只断言开关状态 `scene.snapToGrid`，不断言步长）⟹ ⟹ 回归里 550 仍绿。

★ 本批**不**改写任何既有批次的 README（追加式文档不可重写）⟹ 更正写在这里并指回 §4.3。

---

## 8. 遗留

| 编号 | 事项 | 归属 |
| --- | --- | --- |
| `L1` | 导演台剩余快捷键：`⌘G` 打组 ／ `⌘⇧D` 解组 ／ `⌘Z` 撤销 ／ `⌫` 删除 | **独立批次**（结构性操作，要复原策略） |
| `L2` | ⌘T／⌘Y 的修饰键差异：源站 `hY` 块对 `t`／`y` **无**修饰键限制 ⟹ 源站 ⌘T／⌘Y **会**生效；batch 851 的 clone 实现把 ⌘⌥ 一律拦掉 | **独立批次**（牵涉 clone 的 ⌘Y＝重做语义） |
| `L3` | `D3` 的路径草稿提交守卫**运行时未取证** | 本批登记，可在本批的 clone 上补一次「画一条路径再按 V」的取证 |
| `L4` | batch 831 的 `S14` 历史债（batch 834 拆文件后判据未跟着迁） | 独立批次（851 已登记，本批仍未动） |
| `L5` | 782 的 17 条行号漂移债 ＋ 736 的 `C1`／`C3`／`C4`／`C7` 旧账 | 独立批次 |
| `L6` | 素材库 popover 横向差 20px（826 自开） | 独立批次 |
| `L7` | 源站 ⌘C 复制 ／ 撤销栈跨刷新是否保留 ／ 时间轴缩放真值公式（830 自开） | 低优先 |

---

## 9. 证据索引

| 文件 | 内容 |
| --- | --- |
| `raw/source-852-contract.json` | ★ 源站 chunk 的 **17 个逐字片段**（每个都唯一命中 ＋ 字节偏移） |
| `raw/source-852-transformkeys.json` | 源站实测读数（R/F/V 三步、Shift+V、X 翻转、冒泡 0 键） |
| `raw/clone-852-transformkeys.json` | clone 实测读数（DOM ＋ store 两条路） |
| `raw/attrib-852.json` | 受控对照的逐条读数 |
| `runtime-audit.json` | 门禁 10/10 |
| `negative-audit.json` | 阴性 11/11 |
| `probes/extract852_contract.py` | 契约提取器（锚点唯一命中 ＋ 任意值类名自检） |
| `probes/source852_transformkeys.py` | 源站探针（§3.4 的三个坑都写在注释里） |
| `probes/clone852.py` | clone 探针（读 DOM ＋ store 两条路） |
| `probes/neg852.py` | 阴性对照 11 条 |
| `probes/regress852.py` | 回归 46 条 |
| `probes/attrib852.py` | 受控对照（白名单复原 ＋ 连跑两遍） |
| `images/852src_*.png` | 源站截图 10 张（工具栏下拉与 active 项） |
| `images/852clone_*.png` | clone 截图 6 张（整页） |
| `scripts/verify-liblib-batch852.py` | 门禁 10 条 |
