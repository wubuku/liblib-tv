# batch 863 —— 取景框外的遮罩（源站逐字对齐）

> ★ **一句话**：batch 862 把「构图参考线」开关接到了取景框上之后，**框外那圈暗区**
> 仍然是 clone 自己用 `box-shadow: 0 0 0 9999px rgba(0,0,0,0.24)` 撑出来的
> ⟹ ⟹ **黑 24%、没有模糊**；
> ⟹ ⟹ 源站是**独立的一层遮罩**：`bg-black/20 backdrop-blur-md`
> ＋ **CSS mask 把取景框那块挖空**。
> ⟹ ⟹ 本批把 clone 改成源站逐字结构（**D20 结案**）。

---

## 1. 靶子：clone 的框外遮罩不是源站那一套

| | clone（本批之前） | 源站 |
| --- | --- | --- |
| 遮罩是谁 | **框自己的 `box-shadow`**（`0 0 0 9999px rgba(0,0,0,0.24)`） | **独立的一层**，`absolute inset-0`，与框**平级** |
| 框外暗度 | **黑 24%** | **黑 20%**（`bg-black/20`） |
| 框外模糊 | **没有** | **有**（`backdrop-blur-md` ＝ `blur(12px)`） |
| 框内 | 靠「shadow 从框边缘往外撑」**天然**不受影响 | 靠 **CSS mask 挖空**（`mask-composite: exclude` ＋ 两次 `linear-gradient`） |

★ 差别不只是颜色深浅：源站框外是**模糊**的（背景被 `backdrop-filter` 化开），
clone 框外只是**压暗**（一层半透明黑盖在上面）⟹ ⟹ 两者在观感上是两回事。

★ 本批的靶子编号：**D20**（由 batch 862 登记）。

---

## 2. 源站取证

### 2.1 源站逐字（已入库：`raw/source-863-mask-literal.txt`）

★ chunk：`/tmp/liblib_srcjs2/0fmehki05gkzw.js.js`（1,018,130 字符）的 `mP` 组件。
★ 摘录的范围是**「外层容器 → 遮罩层 → 取景框」这三层连续 JSX**，
  文件头记录了**来源 chunk 路径、字符偏移、chunk 与摘录的两个 sha256**。

```js
(0,o.jsx)("div",{ref:l,
  className:"pointer-events-none absolute bottom-0 left-0 right-0 top-0 z-10",
  children:u&&(0,o.jsxs)(i.Fragment,{children:[
    (0,o.jsx)("div",{className:"absolute inset-0 bg-black/20 backdrop-blur-md",
      style:{WebkitMaskImage:"linear-gradient(#000 0 0), linear-gradient(#000 0 0)",
             WebkitMaskPosition:`0 0, ${u.left}px ${u.top}px`,
             WebkitMaskRepeat:"no-repeat, no-repeat",
             WebkitMaskSize:`100% 100%, ${u.width}px ${u.height}px`,
             WebkitMaskComposite:"xor",maskComposite:"exclude"}}),
    (0,o.jsx)("div",{className:"outline-white/18 absolute rounded-xl outline -outline-offset-1",
      style:{left:u.left,top:u.top,width:u.width,height:u.height}}), …]})})
```

⟹ ⟹ 逐字结论五条：

1. 遮罩是**独立的一层**（`absolute inset-0`，与框平级），**不是**框的 box-shadow；
2. 容器 `pointer-events-none … z-10` ⟹ ⟹ 遮罩**不吃指针事件**、**盖在 3D 场景之上**；
3. 框外＝ **黑 20% ＋ 背景模糊**；
4. 框内被 **mask 挖空**（`exclude` ＋ 两次 `linear-gradient`）
   ⟹ ⟹ 框内**不压暗、不模糊**；
5. ★ mask 的**第二个位置/尺寸**正好是「框在容器坐标系里的偏移与大小」
   ⟹ ⟹ 挖出来的洞**就是框**。

### 2.2 源站运行时实测：★ **待补**（不是「已实测」）

★ 本批取证时**源站项目页打不开**：画布节点 **0**、正文停在「项目加载中...」、
  **不发任何 XHR/fetch、无 4xx/5xx、无 WebSocket**；
  而**首页正常渲染**（登录态有效）⟹ ⟹ 已排除本地环境问题
  （curl 通、首页通、cookie 20 条在）
  ⟹ ⟹ 判定为**源站侧临时故障／风控**。
★ 证据：`raw/source-863-frame-mask.json`（异常原文已入库）。
★ 因此本批的源站侧依据是**入库的逐字**（§2.1），
  **源站恢复后必须补跑** `probes/source863_frame_mask.py`，
  并把运行时读数补进 `raw/source-863-frame-mask.json`。
★ ★ **本批不假装已实测**：门禁的源站侧是**静态逐字判据**，不是运行时读数。

---

## 3. clone 整改（1 个源文件）

### `src/components/director/DirectorViewport.tsx`（`AspectFrame`）

| # | 改动 | 依据 |
| --- | --- | --- |
| ① | **新增外层容器** `pointer-events-none absolute bottom-0 left-0 right-0 top-0 z-10`（`data-director-aspect-mask-container`） | 源站逐字 |
| ② | 容器内**第一个子元素**＝**遮罩层** `absolute inset-0 bg-black/20 backdrop-blur-md`（`data-director-aspect-mask`） | 源站逐字 |
| ③ | 遮罩层加**源站逐字的 inline style**：`WebkitMaskImage`（两次 `linear-gradient(#000 0 0)`）／`WebkitMaskPosition`（`0 0, ${left}px ${top}px`）／`WebkitMaskRepeat`（`no-repeat, no-repeat`）／`WebkitMaskSize`（`100% 100%, ${width}px ${height}px`）／`WebkitMaskComposite:"xor"`／`maskComposite:"exclude"` | 源站逐字 |
| ④ | ★ **删掉**框自己的 `shadow-[0_0_0_9999px_rgba(0,0,0,0.24)]`（框上**不再有** box-shadow） | 源站的框只有 `outline-white/18 … outline -outline-offset-1` |
| ⑤ | 框与遮罩层**同在**容器里（容器含框 ⟹ ⟹ 结构与源站同构） | 源站逐字 |

★ ★ **`bg-black/20` 与 `backdrop-blur-md` 为什么能直接照抄类名**：
  4317 的 **Tailwind 扫描是冻结的**（新增类不生成 CSS）⟹ ⟹ 但这两个类
  **clone 已在别处使用** ⟹ ⟹ 扫描已覆盖 ⟹ ⟹ 可以直接用。
  （对比：862 用的 `outline-white/18` 是**任意值类** ⟹ ⟹ 未生成 ⟹ ⟹ 才要走 inline style。）
★ **运行时验证过这两个类真的生效**：遮罩层计算样式
  `backgroundColor: oklab(0 0 0 / 0.2)`（＝ 黑 20%）、`backdropFilter: blur(12px)`。

---

## 4. 验收

（见下面各小节；★ **数字以本 README 落盘时的实测为准**。）

### 4.1 门禁

`scripts/verify-liblib-batch863.py` ⟹ ⟹ **110 判据，0 失败**。

| 段 | 内容 | 条数 |
| --- | --- | --- |
| S1 | **源站逐字证据必须在场且可解析**（缺证据文件 ⟹ ⟹ **直接判失败**，不许凭印象补） | 2 |
| S2 | clone **源码契约**（静态、剥注释后比）：容器类／遮罩类／mask 图像／位置结构／尺寸结构／重复／合成／★ 框**不再有 9999px box-shadow**／框描边 18%／862 的开关与四条分线**不许被改坏** | 13 |
| S3 | clone **运行时读数**（六档逐档）：容器／遮罩在场、类名逐字、`pointer-events:none` ＋ `z-index:10`、遮罩**铺满**容器、容器含框且首子元素是遮罩层、黑 20%、`blur(12px)`、两次 `linear-gradient`、`exclude`、`no-repeat`、★ mask 的洞**正好是框的位置与尺寸**、框**无 box-shadow**、框描边 18%／1px／−1px／12px | 6×14 ＋ 若干 |
| S3′ | ★ **红色探针**（见 §6 方法学④⑤）：框外 R=**151.58**／G=18.44 ⟹ **红味 133.14**；框内 R=**32.0**／G=37.0 ⟹ **红味 −5**；差 **119.58** | 1 |
| S3″ | **862 回归**：开关仍可点（0 ⟹ 4 ⟹ 0）；「自适应」时容器／遮罩／框**一起消失** | 4 |

★ **期望值的来源**：S2 的每一个期望串都**从 `raw/source-863-mask-literal.txt` 解析**
  ⟹ ⟹ **不凭记忆手打**；
  ★ 连「黑 20%」「描边 18%」都是从证据串里**正则解析**出来的
  （`bg-black/(\d+)` ／ `outline-white/(\d+)`）⟹ ⟹ 证据文件若被改动，门禁会跟着变。
★ **位置/尺寸只比「结构」**：源站是 `${u.left}`、clone 是 `${frameRect.left}`
  ⟹ ⟹ 逐字比会假红 ⟹ ⟹ 归一化成 `0 0, Xpx Xpx`／`100% 100%, Xpx Xpx` 再比。

### 4.2 阴性对照

`probes/neg863.py` ⟹ ⟹ **7/7 通过**（每条：行数中性 ＋ **变异已落地** ＋ 字节级还原 ＋ 打红在预期判据上）。

| # | 变异 | 命中判据 | 红条数 |
| --- | --- | --- | --- |
| N1 | `maskComposite: "exclude"` → `"add"` | `clone:the-red-probe-proves-the-mask-hollows-the-frame` | 8 |
| N2 | 遮罩类 `bg-black/20` → `bg-black/40` | `clone:the-mask-is-black-at-20-percent-for-` | 13 |
| N3 | 遮罩类 `backdrop-blur-md` → `backdrop-blur-sm` | `clone:the-mask-blurs-the-backdrop-for-` | 13 |
| N4 | mask 洞高 `${frameRect.height}px` → `${frameRect.height - 10}px` | `clone:the-mask-hole-matches-the-frame-size-for-` | 6 |
| N5 | mask 洞位 `${frameRect.top}px` → `${frameRect.top + 10}px` | `clone:the-mask-hole-matches-the-frame-position-for-` | 6 |
| N6 | 把框的 `9999px` box-shadow **加回来** | `source:the-frame-no-longer-carries-a-9999px-box-shadow` | 7 |
| N7 | 容器类去掉 `z-10` | `clone:the-container-pierces-no-pointer-for-` | 13 |

### 4.3 回归

`probes/regress863.py` ⟹ ⟹ **107 条**（沿用 862 的清单 ＋ 本批 `863`）
⟹ ⟹ **红 18 条**。

★ **其中 17 条是既有旧账**（与 862 的红集合**完全相同**）：
`831`／`835`／`741`／`91`／`736`／`748`／`749`／`782`／`626`（D7 源站同款）／
`546`＋`542`（fixture `/private/tmp/batch542-fixture/hero-character.fbx` 缺失）／
`738`（C7 写死个数过期）／`656`（预测被证伪）／`648`（2 条）／
`645`／`722`／`629`（扩大清单后可见的旧账）⟹ ⟹ 归因：与本批无关。

★ ★ **第 18 条是本批自己的门禁**（`863.py`）⟹ ⟹ **如实记录**，不藏：

- 首跑红在 `clone:the-red-probe-proves-the-mask-hollows-the-frame`，
  红灯原文是
  `{'框内R': 32.0, '框外R': 222.0, '差值': 190.0, …}`
  ⟹ ⟹ ★ **三个阈值其实全都满足**（差值 190 ≥ 40／框外 222 ≥ 100／框内 32 ≤ 80）
  ⟹ ⟹ 真因**不在 clone**，而在**门禁自己**：
  `red_probe()` 的**成功**返回**漏了 `可用: True`**（只有失败分支有）
  ⟹ ⟹ `probe.get("可用") is True` **恒假** ⟹ ⟹ 判据永远红。
- ★ 修法：成功返回补 `可用: True`；并把判据从「只看 R 通道」加强为
  **「红味」R−G**（框外 ≥ 60、框内 ≤ 30）＋ 差值 ≥ 40
  ⟹ ⟹ **只看 R 通道分不清「被染红」与「底色本来就亮」**
  （那次框外 R＝**222** 就是亮底色，不是红）⟹ ⟹ 加 G 通道后：
  红色油漆压在任何底色上 R−G 都很大，而「本来就白」的 R−G ≈ 0 ⟹ ⟹ 不会冒充。
- 修后重跑 `863.py` ⟹ ⟹ **110 判据、0 失败**。
- ★ ★ **其余 106 条的结果不受影响**（本批只改了这**一个**门禁脚本，
  源码在整个回归期间**没有变动**）⟹ ⟹
  **本批引入 0 条新红**；`35`／`859`／`860`／`861`／`862`／`590`／`617`／`863` 全绿。

### 4.4 受控对照

`probes/attrib863.py` ⟹ ⟹ 五态：`HEAD-1`／`HEAD-2`（源码换回 HEAD）
／**`MIX`**（只把 `maskComposite` 改成 `"add"`）／`WORK-1`／`WORK-2`。

| 判据 | 结果 |
| --- | --- |
| **稳定**（两遍读数一致） | ✔ HEAD-1＝HEAD-2（各 124 条红）、WORK-1＝WORK-2（各 0 条红） |
| **新门禁有牙** | ✔ HEAD 态 `rc=1`／WORK 态 `rc=0` |
| **复原自检** | ✔ SHA-256 回到基线 |
| **HEAD 态零 CRASH** | ✔ 124 条**具名**红条，`CRASH: 0` 条（★ 「缺元素 ⟹ 具名判红」那条纪律生效了） |
| **MIX 隔离** | ✔ **只有 mask 合成相关的判据翻红**（静态 1 条 ＋ 逐档 6 条 ＋ 红色探针 1 条），**几何／黑度／模糊／位置尺寸／描边全部保持绿** |
| **旁门禁无连带损伤** | ✔ `860`／`859` 在**全部五态**都是 0 红；`diffs` 为空 |

★ ★★ **MIX 态的红灯 detail 直接给出了机理证据**（只改 mask 合成一个词）：

```
框内R: 222.0  框外R: 222.0   差值: 0.0
框内红味: 216.0  框外红味: 216.0   （框内 G=6 / B=6 ⟹ 确实被红漆盖住）
```

⟹ ⟹ `mask-composite: exclude` 一改成 `add` ⟹ ⟹ 遮罩**不再挖空**
⟹ ⟹ **框内也被染红** ⟹ ⟹ 差值归零 ⟹ ⟹ 判据翻红
⟹ ⟹ 这就是「**mask 真的在挖空**」的**反向**证明。

### 4.5 ★ 改前／改后**同口径**读数（同一支探针，两态各跑一次）

`raw/clone-863-frame-mask-HEAD.json`（改前）vs `raw/clone-863-frame-mask-WORK.json`（改后）：

| 读数 | 改前（HEAD ＝ batch 862 的旧实现） | 改后（本批） |
| --- | --- | --- |
| **独立遮罩层** | **0 个**（根本没有这层） | **1 个**，class 逐字 `absolute inset-0 bg-black/20 backdrop-blur-md` |
| 遮罩背景 | — | `oklab(0 0 0 / 0.2)`（＝黑 **20%**） |
| 遮罩模糊 | — | `blur(12px)` |
| mask 合成 | — | `exclude, exclude` |
| mask 位置／尺寸 | — | `0px 0px, 65.6667px 32px` ／ `100% 100%, 1226.67px 690px`（＝框） |
| **框的 box-shadow** | `rgba(0,0,0,0.24) 0px 0px 0px **9999px**` | **`none`** |
| **红色探针·框外** | R=**27.83**、G=32.19 ⟹ **红味 −4.36**（**根本没被染红**：没有遮罩层可染） | R=**151.58**、G=18.44 ⟹ **红味 133.14**（**被染红**） |
| **红色探针·框内** | R=32.0、G=37.0（红味 −5） | R=32.0、G=37.0（红味 −5，**没被染到**） |
| 框外/框内亮度比（**只作参考**） | 0.8702 | 0.9033 |

★ 两条「红味」的对照就是本批最核心的证据：
  **改前**框外**染不上红**（因为压根没有遮罩层）⟹ ⟹ 没有「挖空」这回事；
  **改后**框外**红味 133**、框内**红味 −5** ⟹ ⟹ 洞**正好是框**。

### 4.6 构建链

| 项 | 结果 |
| --- | --- |
| `npx tsc --noEmit` | ✔ 通过 |
| `npx eslint`（本批源文件） | ✔ 通过 |
| `npx next build` | ✔ 通过（路由表正常） |
| `npm run assertions:check` | ✔ **809** 个门禁脚本、**0** 个空洞断言 |
| `npm run docs:check` | exit=1 ⟹ ★ 断链**全部**在 `docs/user-manual/**`（**他人并发编辑区**）⟹ ⟹ **本批目录 0 处断链** |

---

## 5. 差异登记（如实登记，不假装已对齐）

- ★ **D20 结案**：框外遮罩已改成源站逐字（独立遮罩层 ＋ `bg-black/20 backdrop-blur-md`
  ＋ CSS mask 挖空），框上的 `9999px` box-shadow 已删。
  ★ ★ **登记口径**：batch 862 的台账行**保留不改**（追加式文档不可重写历史行）；
  以本 README 与本批台账行为准。
- **D18（仍在）**：取景框**像素几何**与源站不同（源站全屏 1080 ＋ 逐字公式
  「减左右面板 281×2 ＋ 上下 224」；clone 是 810 高 ＋ padding 公式）
  ⟹ ⟹ 竖档差最多（4:3：源站 1141×856 vs clone 920×690）⟹ ⟹ **布局级**，未做。
- **D19（仍在，保留）**：clone 视口底部胶囊那枚「九宫格辅助线」是 **clone 自己的扩展**
  ⟹ ⟹ 保留，并与框上那枚共享 `showThirds`。
- **D17（仍在）**：源站把比例与 `reference_line` **写进机位对象** ⟹ ⟹ clone 未做。
- ★ **本批新登记的一条（诚实口径）**：
  **源站遮罩的「模糊程度」只对齐到「类名与计算样式」这一层**
  ⟹ ⟹ `backdrop-blur-md` 在**源站与 clone 的 Tailwind 版本**下都是 12px
  （实测 clone ＝ `blur(12px)`）⟹ ⟹ 一致；
  ★ 但**源站运行时复核尚未做**（§2.2）⟹ ⟹ 源站那一侧的值是**逐字推出来的**，
  不是**实测读出来的** ⟹ ⟹ 源站恢复后必须补。

---

## 6. 本批新增的方法学（四条，都是自己踩的）

① ★★ **「负控打空」的第一嫌疑永远是「变异根本没注入」。**
   本批第一版 `apply_mutation` **算出了**变异文本却**没写回文件**
   （写回的是原文）⟹ ⟹ 7 条变异**一条都没落地** ⟹ ⟹ 门禁 7 次全绿
   ⟹ ⟹ 负控 **0/7** 打空。
   ⟹ ⟹ 修法两条：① `apply_mutation` 必须**返回变异后的源码**；
   ② 每条变异加一条**「变异已落地」自检**（文件里必须真的出现新值）。
   ⟹ ⟹ 通式：**rc=0 ＋ 零红灯** ⇒ 先查「注入」这一层，再谈「判据有没有牙」。

② ★★ **取样点必须取在「这一刻的目标」上，不能拿上一轮的坐标去采样。**
   六档循环跑完**页面停在 9:16**，我却用 **16:9 的框坐标**去取像素
   ⟹ ⟹ 两个取样点都落在**别的 UI**上 ⟹ ⟹ 两边 R 都是 **222** ⟹ ⟹ 差值 0。
   ⟹ ⟹ 修法：**探针在目标那一档「当场」做**；
   ★ 顺带发现「回头重选比例」也不可靠 —— 重选时选项位置会挪，
   那个点会被 3D 视口的坐标控件（gizmo，`right-5 top-5 z-20`）**挡住**
   ⟹ ⟹ Playwright 报 `subtree intercepts pointer events`。

③ ★★ **「先计数、再决定要不要测」**：
   受控对照的 HEAD 态（= 旧实现）**没有遮罩层** ⟹ ⟹ 若照样去采样，
   拿到的就是两个**毫不相干**的点 ⟹ ⟹ 差值可能**碰巧** ≥ 40
   ⟹ ⟹ 那条判据会变成**随机灯** ⟹ ⟹ 受控对照会误判「有牙」。
   ⟹ ⟹ 修法：遮罩层不在场 ⟹ ⟹ 该判据**具名**判红（而不是去采样）。

④ ★★ **像素差不可当判据，确定性探针才可。**
   「框内/框外亮度比」受 3D 场景**一直在动**影响（实测 0.87 ↔ 0.90 漂移）
   ⟹ ⟹ 只能作参考。
   ⟹ ⟹ 红色探针是**确定性**的：把遮罩层临时染成 `rgba(255,0,0,0.85)`
   ⟹ ⟹ 框外**必红**、框内**必不红**（被 mask 挖空）
   ⟹ ⟹ 判据＝「框外 R − 框内 R ≥ 40」**且**「**红味** R−G：框外 ≥ 60、框内 ≤ 30」
   ⟹ ⟹ 若 mask 没挖空 ⟹ ⟹ 框内也会被染红 ⟹ ⟹ 差值 ≈ 0 ⟹ ⟹ 判据翻红。

⑤ ★★ **红灯原文与阈值自相矛盾 ⟹ ⟹ 先怀疑「判据自己」，不是先怀疑被测对象。**
   回归里 `863.py` 首跑红了，detail 里 `差值 190／框外 222／框内 32`
   —— **三个阈值全都满足** ⟹ ⟹ 那就**不可能**是 clone 的问题
   ⟹ ⟹ 真因是 `probe.get("可用") is True` 恒假（成功返回漏了那个键）。
   ⟹ ⟹ ★ **通则**：拿到一条红，先把它的 detail 与自己的阈值**逐条对照**
   ⟹ ⟹ 对不上 ⟹ ⟹ 门禁的实现有问题 ⟹ ⟹ 先修门禁再谈被测对象。

★ 另：★ **期望值要从入库证据里解析，而不是凭记忆手打**
  —— 本批的「黑 20%」「描边 18%」都是从证据串里**正则解析**出来的。

---

## 7. 用户可达（怎么点、怎么测）

★ **clone 跑起来**：见 `docs/research/LIBTV_CLONE_REACHABILITY.md` 的 §0
  （`npm run dev` ⟹ 浏览器打开 `http://localhost:4317/`）。

★ **看到框外遮罩的路径**：

1. 打开 `http://localhost:4317/`；
2. hover 画布上的**导演台卡片** ⟹ ⟹ 点「**打开导演台 →**」；
3. 左侧 **rail** 点「**选择画幅比例**」；
4. 点「**16:9**」⟹ ⟹ **机位取景框出现在视口里**（clone 是 1227×690）；
5. ★ **框外立刻变暗并被化开**（黑 20% ＋ `blur(12px)`），
   **框内那一块保持清晰**（被 mask 挖空）；
6. ★ **怎么自己验「框内真的被挖空了」**：
   打开 DevTools 的 Elements 面板 ⟹ ⟹ 找到 `data-director-aspect-mask`
   那个 `div` ⟹ ⟹ 在 Styles 里把 `background-color` 改成
   `rgba(255,0,0,0.85)` ⟹ ⟹ **框外立刻变红、框内仍然是原来的画面**
   ⟹ ⟹ 这就是「mask 真的挖空了框那块」的**人眼版**证明；
7. 点「**自适应**」⟹ ⟹ **框与遮罩一起消失**（源站逐字：容器 `u&&` 才渲染子元素）。

★ **选择器**（给自动化用）：

- 遮罩容器：`[data-director-aspect-mask-container]`
- 遮罩层：`[data-director-aspect-mask]`
- 取景框：`[data-director-aspect-frame]`（带 `data-director-aspect-ratio="16:9"` 等标记）
- 框上那枚开关：`[data-director-frame-thirds-toggle]`
- 三分线：`[data-director-thirds]`
- 面板七格：`[data-director-aspect-option]`（值即档名，如 `16:9`／`自适应`）

★ **自己跑门禁**：

```bash
python3 scripts/verify-liblib-batch863.py      # 期望：110 判据，0 失败
python3 docs/research/liblib-canvas-batch863-2026-10-01/probes/neg863.py   # 期望：7/7
python3 docs/research/liblib-canvas-batch863-2026-10-01/probes/regress863.py
```

---

## 8. 复现步骤（一条链）

1. **契约提取**：源站 chunk 的 `mP` 组件里「外层容器 → 遮罩层 → 取景框」三段
   ⟹ ⟹ 逐字入库 `raw/source-863-mask-literal.txt`（含 chunk 路径／偏移／两个 sha256）；
2. **源站运行时**：`probes/source863_frame_mask.py` ⟹ ⟹ **本批失败**（源站项目页不可用）
   ⟹ ⟹ 异常入库 `raw/source-863-frame-mask.json` ⟹ ⟹ **待补**；
3. **clone 实测**：`probes/clone863_frame_mask.py`（遮罩层计算样式 ＋ 红色探针）
   ⟹ ⟹ `raw/clone-863-frame-mask.json` ＋ 两张红色探针截图；
4. **门禁**：`scripts/verify-liblib-batch863.py`
   （★ 源站期望值**只从入库的逐字证据解析**）；
5. **阴性**：`probes/neg863.py`（行数中性 ＋ 变异已落地 ＋ 字节级还原）；
6. **回归**：`probes/regress863.py`（107 条）；
7. **受控对照**：`probes/attrib863.py`（HEAD×2 ／ **MIX 单点变异** ／ WORK×2）。
