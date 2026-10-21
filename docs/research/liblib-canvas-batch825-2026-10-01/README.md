# Batch 825 — LibTV 导演台·跟随横幅：「退出跟随」到底点不点得动？

> 2026-10-21 ｜ **源站代码 + 源站运行时双证据** ｜ `src/components/director/DirectorDesk.tsx` 改过，**跑过 build**
>
> 验收：`scripts/verify-liblib-batch825.py` → **主检查 9/9 ｜ 阴性对照 4/4**
> 源站证据全部入库：`raw/source-825-followbanner.js`（**源站自己的代码**）、`raw/source-825-desk-follow.json`（源站运行时读数）

---

## 1. 一句话结论

> ★★ **「源站那枚『取消』根本点不动」是错的。** 错在**把未激活的横幅当成了常态**。
> ⟹ 更要紧的是：★ **源站的「机位跟随目标」根本没有这条横幅** —— 源站那条是**协作跟随**（跟别人的视角）的。
> ⟹ ⟹ ★★ clone 这条「正在跟随／取消ESC／按 ESC 退出」横幅是 **clone-only 的额外物**，皮肤照抄了源站的协作横幅。

---

## 2. ★ 推翻的那条已入库结论

batch 605 的 `runtime-audit.json` 里有这么一段（**至今还在**）：

> `banner:cancel-pointer-events-auto` — 「deliberate deviation: the source's own 取消 pill
> inherits pointer-events:none from the banner panel (panel and banner both write
> pointer-events-none, the button does not re-enable it), and elementFromPoint at the pill
> centre lands on the 机位视角 button underneath — **so the source's cancel is unclickable**
> and its peer-hover hint can never appear.」

★ 这段话是 clone 那句注释、batch 612 的 `follow:clone-keeps-hit-area` 断言、以及 605 自己的
`banner:pointer-events-none` 断言的**共同来源**。本批用**两个独立来源**把它推翻：

### 2.1 证据一：源站**自己的代码**（`raw/source-825-followbanner.js`，9997 字节）

源站那条横幅的组件原文（minified，读法见括号注释）：

```jsx
// 横幅容器：固定 pointer-events-none，portal 到 document.body
<div data-testid="collab-follow-banner"
     className="pointer-events-none fixed left-1/2 top-0 z-[305] -translate-x-1/2
                motion-safe:transition-opacity motion-safe:duration-200"
     style={{opacity: +!!active}} aria-hidden={!active}
     ref={t => { t?.toggleAttribute("inert", !active) }}>
  // ★ 内层面板：★ 按 active 切 pointer-events ★
  <div className={`flex items-center gap-2 rounded-b-xl border px-3 py-1.5 text-white shadow-md
                   ${active ? "pointer-events-auto" : "pointer-events-none"}`}
       style={{backgroundColor: colorHex, borderColor: colorHex}}>
    <span className="inline-block size-2 shrink-0 rounded-full bg-white" aria-hidden />
    <span className="text-sm">{prefix}{nickname ? ` ${nickname}` : ""}</span>
    <span className="relative ml-1 inline-flex">
      // ★ 取消按钮：★ 自己没写 pointer-events（从面板继承）★
      <button type="button" aria-label={t("canvas:collabFollowBannerLogout2")}
              aria-keyshortcuts="Escape" onClick={onClose}
              className="peer rounded-full bg-white px-2 py-0.5 text-xs font-medium
                         leading-none text-gray-900 transition-colors hover:bg-white/90"
              data-testid="collab-follow-banner-close">
        {t("canvas:collabFollowBannerCancelEsc")}   // 「取消ESC」
      </button>
      <span role="tooltip" className="pointer-events-none absolute left-1/2 top-full z-10
                 mt-2 -translate-x-1/2 whitespace-nowrap rounded-md bg-black/90 px-2 py-1
                 text-xs font-normal text-white opacity-0 shadow-md transition-opacity
                 peer-hover:opacity-100 peer-focus-visible:opacity-100
                 motion-safe:duration-150">
        {t("canvas:collabFollowBannerPressEsc")}   // 「按 ESC 退出」
      </span>
    </span>
  </div>
</div>
```

⟹ ★★ **按钮自己没写 pointer-events，但面板在 `active` 时是 `pointer-events-auto`** ⟹ ★★ **源站在显示时，那枚「取消」是点得动的**；⟹ 605 量到的 `none` 属于**未激活**那块（`opacity 0` / `aria-hidden` / `inert`）。

### 2.2 证据二：源站**运行时**（`raw/source-825-desk-follow.json`）

源站画布页此刻就挂着那条横幅（`recon825c` 实测）：

| 序 | 项 | 源站读数 |
|---|---|---|
| 序 1 | 横幅 rect | **174×34 @(713, 0)**（视口 1600 ⟹ 水平居中在 800） |
| 序 2 | 横幅状态 | `opacity: 0`、`aria-hidden: "true"`、`inert: true`、`pointer-events: none` ⟹ ★★ **未激活** |
| 序 3 | 取消按钮 rect | **64×16 @(810, 9)**、own「取消ESC」、aria「退出跟随」 |
| 序 4 | 按钮 `aria-keyshortcuts` | **`Escape`** |
| 序 5 | 按钮 class | `peer rounded-full bg-white px-2 py-0.5 text-xs font-medium leading-none text-gray-900 transition-colors hover:bg-white/90` ⟹ ★ **没有 pointer-events** |
| 序 6 | 按钮 computed `pointer-events` | `none`（**未激活**态的继承结果） |
| 序 7 | 命中测试（按钮中心） | 落在**底下的 DIV**（「脚本 V2 11确认镜头2准备资产3合成…」）⟹ ★★ 命中穿透 ⟹ ⟹ ★★ **605 记的「命中的是机位视角」正是这个现象**（在导演台里，底下是「机位视角」） |

★ 对照 batch 605 当年的读数：横幅 173.7×34 @(873.1,0)、按钮 63.7×16 @(970.1,9)、提示 82.1×24 @(960.9,33) ⟹ ★★ **就是同一块横幅**（视口 1920 ⟹ 中心 960 ✓）。

### 2.3 证据三：源站的 bundle 里**没有第二个跟随横幅**

- 全 160 个 chunk 里，特征串 `rounded-b-xl` 只命中 2 处（一个是协作横幅，一个是无关的圆角容器）、`z-[305]` **只有 1 处**（协作横幅）
- ★★ **点开源站的「导演台」没有懒加载任何新 chunk**（点击前后都是 160 个）⟹ ⟹ ★★ 导演台的代码就在已抓的包里 ⟹ 「机位跟随另有横幅」这条路**彻底堵死**
- ★★ 橙色 `#E46525` / `228, 101, 37` 在 160+160 个 chunk 里**一个字节都没有** ⟹ ⟹ 那个橙色是**运行时传进去的 `colorHex`**（跟随者的颜色），不是代码里的常量

---

## 3. ★★ 更要紧的发现：源站的**机位跟随**没有这条横幅

源站那条横幅组件**只有一个调用点**（`raw/source-825-followbanner.js` 里 `prefix:` 出现 2 次：1 次是组件的参数解构、1 次是真调用）：

```jsx
// ★ 唯一调用点：协作跟随控制器
(0, x.jsx)(ro, { active: P, prefix: z, nickname: D, colorHex: T, onClose: r })
//                        ↑「正在定位」/「正在跟随」  ↑对方昵称  ↑对方颜色
```

⟹ ★★ `prefix` 取的是 **`canvas:collabFollowControllerProcessing` / `…Processing2`**（协作态的 i18n 键），**不是**任何机位跟随的文案。

★ 而源站**机位跟随**自己的那套词汇（`raw/source-825-follow-keys.json`，共 61 个与 follow 有关的键）：

| 序 | 源站 i18n 键 | 中文 | 落在哪 |
|---|---|---|---|
| 序 1 | `directorCameraFollowTarget` | 跟随目标 | 检查器 |
| 序 2 | `directorCameraFollowNone` | 不跟随 | 检查器 |
| 序 3 | `directorCameraFollowViewMode` | 跟随视角 | 检查器 |
| 序 4 | `directorCameraFollowOffset` | 跟随偏移 | 检查器 |
| 序 5 | `directorCameraFollowFirstPerson` / `…ThirdPerson` | 第一人称 / 第三人称 | 检查器 |
| 序 6 | `directorCameraFollowDisableBeforePathBind` | 请先关闭机位跟随，再绘制轨迹 | 路径相关 |
| 序 7 | `directorPhoneVcamDisableFollowHint` | 请先关闭机位跟随，再使用手机运镜 | 手机运镜 |
| 序 8 | `directorCameraMotionPresetFollowBlocked` | 跟随目标时不可使用预设运镜 | 预设运镜（821/822 抄的就是这句） |
| 序 9 | `directorTimelineFollowTargetPrefix` | **跟随：** | 时间轴轨道名前缀 |
| 序 10 | `collabFollowBanner*` | 退出跟随 / 取消ESC / 按 ESC 退出 | ★★ **协作**横幅 |

⟹ ★★ **导演台那 7 个 `directorCameraFollow*` 键里，一个 banner 键都没有** ⟹ ⟹ ★★ 源站的机位跟随**没有顶部横幅**。

★ clone 侧对照：`跟随目标／不跟随／跟随偏移／跟随视角／第一人称／第三人称／跟随目标时不可使用预设运镜` **clone 全都有** ✓ ⟹ ★★ **clone 的机位跟随本身是忠实的**；⟹ ★★ 缺的只有两处：

- ★★ 源站时间轴上的轨道名前缀「**跟随：**」（`directorTimelineFollowTargetPrefix`）⟹ **clone 没有**（0 命中）⟹ ★ 这是**真缺口**（源站用它标出「这条轨道在跟随某个目标」）
- ★★ clone **多**了一条源站没有的顶部横幅（而且用的是源站**协作**横幅的皮肤）

---

## 4. clone 侧实施（`src/components/director/DirectorDesk.tsx`）

| 序 | 改动 | 为什么 |
|---|---|---|
| 序 1 | 横幅**面板** `pointer-events-none` → **`pointer-events-auto`** | 与源站**激活态**同构（源站：面板按 active 切 auto） |
| 序 2 | 取消按钮**去掉**自己的 `pointer-events-auto` | 源站的按钮**自己没写**（从面板继承）⟹ ⟹ ★★ 两者**逐字同构** |
| 序 3 | 取消按钮加 `aria-keyshortcuts="Escape"` | 源站同款（源站实测与代码都有） |
| 序 4 | 提示 span 加 `role="tooltip"` | 源站同款 |
| 序 5 | 提示 span 加 `data-director-follow-hint` | 本批探针钩子（源站用 `role=tooltip` 定位，clone 需要一个稳定钩子） |
| 序 6 | ★ **重写那段注释** | 原文写着「源站这枚按钮继承 pointer-events:none、根本点不动」⟹ ★★ **那句话是错的** ⟹ 改成写明真实原因（面板 active 时 auto）＋ 真实差异（源站的机位跟随没有这条横幅） |

★ **没改什么**：横幅的位置、几何、配色、文案（「正在跟随」「取消ESC」「按 ESC 退出」）**一律不动** ⟹ ★ 它们本来就与源站那块**逐字同形**（见第 5 节读数）。

★ **「要不要删掉这条 clone-only 横幅」是产品决策** ⟹ ★ 本批**只记不发明**（见第 8 节）。

---

## 5. clone 侧纯 UI 读数（`probes/dbg825a.py`，4 个时刻）

| 序 | 时刻 | 读数 |
|---|---|---|
| 序 1 | C0 起点 | 跟随目标为空（store 读数 `null`）、**横幅不在** |
| 序 2 | C1 设上跟随目标 | 横幅 **173.75×34 @(553.13, 0)**（视口 1440 ⟹ 居中 640）；按钮 **63.75×16 @(650.13, 9)**；提示 **82.14×24 @(640.93, 33)**；`aria-keyshortcuts=Escape`；own「取消ESC」；**子元素数 0**（单文本节点）；computed `pointer-events: auto`；**命中就是它 = true** |
| 序 3 | C2 真实鼠标悬停 | 提示 opacity **0 → 1** ⟹ peer-hover 契约成立 |
| 序 4 | C3 真实鼠标点取消 | 横幅**从 DOM 消失**；store 跟随目标回 **null** |

★★ **与源站逐字同形**（源站 173.7×34 / 63.7×16 / 82.1×24）⟹ 因为它本来就是照抄那块皮肤。

★ **诚实标注**：C1 那一步是**程序化**的（`select_option`）⟹ ★★ **macOS 上原生 `<select>` 聚焦后按 `ArrowDown` 是「弹出下拉」而不是「改值」**（实测 before/after 都是 `""`）⟹ 这条键盘路径在本机走不通 ⟹ ⟹ ★★ 823 的「纯 UI」判据在本批**只适用于被测的那两步**（C2 悬停、C3 点取消），**不适用于铺夹具那一步**。探针把这次键盘尝试的读数**照样留档**。

---

## 6. 验收（`scripts/verify-liblib-batch825.py`）

**主检查 9/9 ｜ 阴性对照 4/4**（每条阴性**只**翻它自己那一条）

| 序 | 判据 | 判什么 |
|---|---|---|
| 序 1 | S1 | ★ 前提：4 个时刻**按顺序一个不缺** ＋ 探针源码**零 store 写调用**（正则自证） |
| 序 2 | S2 | 起点：跟随目标**为空** ⟹ 横幅**不在** |
| 序 3 | S3 | ★★★ 源站对照：横幅与按钮的**宽高**与源站那块**逐字同形**（期望值**从源站运行时读数算出来**），且横幅**水平居中于视口** |
| 序 4 | S4 | ★★ 那枚按钮**命中就是它**（点得动）、computed `auto`、**类里没有 pointer-events**、aria/aria-keyshortcuts/单文本节点 |
| 序 5 | S5 | ★★ 真实鼠标悬停 ⟹ 提示 opacity **0→1** ＋ `role=tooltip` |
| 序 6 | S6 | ★★ 真实鼠标点取消 ⟹ 横幅**消失** ＋ store 跟随目标回 null |
| 序 7 | S7 | ★★★ 源站对照（读**入库的 bundle 片段**）：按钮**自己没写** pointer-events、面板**激活时 auto** ⟹ 「点不动」只对**未激活**态成立 |
| 序 8 | S8 | ★★★ 源站对照：横幅**只有一个调用点**、prefix 是**协作** i18n 键、导演台那 7 个 follow 键里**没有 banner 键** ⟹ ⟹ **源站的机位跟随没有这条横幅** |
| 序 9 | S9 | 静态锚点：横幅那段注释**不再说错话**、源站那两个属性已加、按钮/面板的 pointer-events **与源站同构** |

| 序 | 阴性 | 期望翻红 | 实际 |
|---|---|---|---|
| 序 1 | N1 把「点之后横幅还在」 | S6 | S6 |
| 序 2 | N2 把源站片段里的 `pointer-events-auto` 换掉 | S7 | S7 |
| 序 3 | N3 把源站片段的调用点数改成 2 | S8 | S8 |
| 序 4 | N4 把悬停后提示 opacity 改成 0 | S5 | S5 |

★ N2/N3 靠 **raw 里的覆盖副本**把变异送进判据（★ 这正是 batch 824 的 N12 修法：判据若直接读文件，变异就进不去）。

---

## 7. 历史门禁的连带更正

| 序 | 脚本 | 改了什么 |
|---|---|---|
| 序 1 | `scripts/verify-liblib-batch605.py` | ★ ① `banner:pointer-events-none` 断言：面板由「none」改成「**auto**」（源站代码是 `${active ? auto : none}`）；② `banner:cancel-pointer-events-auto` 的 detail **重写**（原文是那句错话）；③ 模块 docstring 第 2 节加了 **Batch 825 更正**块（点明「归因错了」「橙色不在源站代码里」「量到的是未激活态」） |
| 序 2 | `scripts/verify-liblib-batch612.py` | ★ `follow:clone-keeps-hit-area` 的注释与 `cloneDecision` 文案（原文是「源站那枚胶囊继承 pointer-events:none、是个死按钮」）**更正**为「与源站激活态同构，不再是有意偏离」 |

★ 两个脚本的**断言强度都没有降低**：605 仍然断言面板的类、仍然断言按钮的 computed `auto`；612 仍然断言 `cancel["pe"] == "auto"` ⟹ ★ 只是把**期望值**改成有源站代码依据的那个。

★ 复跑结果：**605 38/38** ✓、**612 112/112** ✓、**823 7/7** ✓、**737 10/10** ✓（后两个本批未触碰，复跑确认没被带坏）。

---

## 8. ★ 本批抓到的三处探针/判据缺陷

1. ★★ **入库的证据不够用**：第一版存下来的源站片段只到**组件定义**（+900 字符）⟹ 片段里那个 `prefix:` 是**参数解构**、不是调用点 ⟹ ⟹ ★★ 验收器**数不出「有几个调用点」** ⟹ ★★ 「存下来的证据」必须**够判据用**，不然它只是一段好看的代码。
   ⟹ 修法：提取时**同时圈住组件与调用点**（`recon825a.py`），并把口径写成 **`prefix:` 次数 − 参数解构那 1 处**（★ 不能用 `,{active:` 数 ⟹ 那个形态会把**边框组件**的调用也算进去 ⟹ 数出来 2，**虚高**）。
2. ★★ **否定锚点太粗**：「注释里不再出现『点不动』」做成**文件级** ⟹ ★★ 文件别处（87/386/1302 行）本来就有**合法的**「点不动」措辞（说的是别的控件）⟹ ⟹ 判据**误伤** ⟹ 修法：★ 否定锚点必须**限定范围**（只看横幅那一段）。
3. ★★ **居中判据公式写错**：把「横幅中心」写成「`cx` vs `w/2`」⟹ ⟹ 比的是**横幅自己的半宽** ⟹ 必然不成立 ⟹ 修法：比**视口中心**（视口宽要从读数里带出来）。

★ 另有一处**平台事实**（不是缺陷，但被误当成 bug 查了半天）：**macOS 上原生 `<select>` 聚焦后按 `ArrowDown` 是弹下拉、不是改值** ⟹ 「用键盘选值」这条**纯 UI** 路径在本机**走不通** ⟹ ⟹ ★ 探针把这次尝试**留档**（before/after 都是 `""`）⟹ 不假装它是纯 UI。

---

## 9. ★ 不声称 / 待办

- ★★ **「要不要删掉这条 clone-only 横幅」是产品决策** ⟹ ★ 本批**只记不发明**。★ 两条路：① **删掉**（最忠于源站；但源站的机位跟随**有**退出路径——检查器里「不跟随」⟹ 不会把用户困住）⟹ ★★ 但那会动 605/612 两条门禁的**内容**（不是期望值）⟹ 要单独做；② **保留**（它给了一个显眼的退出入口，但那是**源站没有的**东西）。
- ★★ **源站时间轴的轨道名前缀「跟随：」**（`directorTimelineFollowTargetPrefix`）clone **没有** ⟹ ★ 这是**真缺口** ⟹ 但 clone 的「跟随」是**相机属性**、源站的「跟随：」标的是**某条轨道** ⟹ ★ 两者模型不同 ⟹ 要先弄清源站那条轨道是什么，**不发明**。
- ★★ **源站那条协作横幅的激活态没有实测**（要另一个用户跟着我才能激活）⟹ ★★ 激活态的「点得动」是**从源站代码**读出来的（`${active ? auto : none}`）⟹ ★ **不是**运行时读数 ⟹ 已在 README 里标注。
- ★ **clone 横幅的橙色 `#E46525`** 是硬编码的；源站的颜色是**运行时 `colorHex`**（跟随者的颜色）⟹ ★ clone-only，**记录**。
- ★ **源站的 `collab-follow-border`**（跟随时给整个视口加一圈 4px 内阴影色框）clone 没有 ⟹ ★ 它属于协作功能，**不移植**。
- ★ **没测**协作跟随本身（clone 没有协作功能）⟹ **不声称**。
- ★ **没测**移动端下这条横幅的位置 ⟹ **不声称**。
- ★ 源站 bundle 仍**未逐个反编译**（823 遗留）；本批只读了「跟随横幅」这一处。

---

## 10. 产物清单

| 序 | 路径 | 内容 |
|---|---|---|
| 序 1 | `docs/research/liblib-canvas-batch825-2026-10-01/README.md` | 本文件 |
| 序 2 | `raw/source-825-followbanner.js` | ★★ **源站自己的代码**（组件＋唯一调用点＋协作 i18n 键），9997 字节 |
| 序 3 | `raw/source-825-followbanner-facts.json` | 上面那份代码的**逐条事实**（可复算） |
| 序 4 | `raw/source-825-follow-keys.json` | 源站**全部**含 follow 的 i18n 键与中文值（61 条） |
| 序 5 | `raw/source-825-desk-follow.json` | ★ 源站**运行时**读数（横幅未激活态、按钮命中穿透、类名、aria-keyshortcuts） |
| 序 6 | `raw/vb825a.json` | clone 侧 4 个时刻的读数 |
| 序 7 | `probes/recon825a.py` | 从源站 bundle 里提取上面那份代码片段（**可复算**） |
| 序 8 | `probes/recon825b.py` | 源站：点开导演台 ⟹ **验证没有懒加载新 chunk** |
| 序 9 | `probes/recon825c.py` | 源站：运行时读数（横幅状态、命中测试） |
| 序 10 | `probes/dbg825a.py` | clone：纯 UI 四时刻探针 |
| 序 11 | `scripts/verify-liblib-batch825.py` | 验收器（9/9 ＋ 4/4） |
| 序 12 | `src/components/director/DirectorDesk.tsx` | ★ 实施（已 `npm run build`） |
