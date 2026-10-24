# batch 860 — 画幅比例**真的驱动机位取景框**（★ 推翻 batch 859 的 D11 结论）

> ★ 一句话：**batch 859 登记的 D11 说错了**。
> 源站实测证明：源站选画幅比例**【不改画布】**，它改的是**机位取景框**；
> 而 clone 的**取景框只支持三档**、且**左侧面板那七格根本没接到 store**
> ⟹ ⟹ **点哪一档取景框都不动**。本批把这两件事都修好。

---

## 0. 一句话结论

| | batch 859 的 D11 说法 | ★ 本批实测的真相 |
|---|---|---|
| 源站选比例会改什么 | 「改画布的宽高比」 | ★ **改机位取景框**；**画布纹丝不动** |
| clone 的差距 | 「clone 不改画布宽高比」 | ★ clone **本来就不该改画布**；真正的差距是**取景框只支持三档**＋**面板七格没接 store** |

本批整改：

1. ★ store 新增**取景比例**状态 `frameAspectRatio`（七档数值 ＋ `null`＝自适应），
   与导出用的 `aspectRatio`（三值）**彻底分开**（源站逐字：`aspect_ratio` 事件发给**机位**）；
2. ★ `DirectorAspectPanel` 的七格**接到 store**（此前是组件内 `useState` ⟹ ⟹ 点哪档都不动）；
3. ★ `getDirectorFrameRect` 支持**任意数值比例**，`null`（自适应）⟹ ⟹ **不画框**；
4. ★ 视口底部那三枚（**clone 自己的扩展**，源站底部 27 枚控件里没有）也接同一个状态 ⟹ ⟹ 两处不打架。

---

## 1. ★ D11 是怎么被推翻的（方法学样本）

### 1.1 源站逐字（chunk `/tmp/liblib_srcjs2/0fmehki05gkzw.js.js`）

选比例的回调：

```js
o$ = useCallback(e => {
  tn(e);                                                // 写本地 ref
  let t = e1 || rL.cameras[0]?.id;                      // 当前机位
  t && n4(t, "aspect_ratio", (0,nZ.R)(e), "right_panel");  // ★ 发事件给机位
}, [e1, rL.cameras, n4])
```

⟹ ⟹ 源站把比例**发给机位**（不是发给画布）⟹ ⟹ **它改的是机位的取景比例**。

### 1.2 ★ 第一版探针读出一个**假象**

`probes/source860_aspect.py` 读到：点「21:9」**之后**有个 1262×541（ratio **2.3334**）的元素，
而点**之前**读数是 `null`。

★ 这个「null → 有值」的模式**不能**当成「选比例后画布才出现」：
第一版的读法是「取**面积最大**的那个 div/canvas」⟹ ⟹ **每次选中的元素可能都不是同一个**
⟹ ⟹ `null` 只说明「那一刻没有元素满足那个筛选条件」，**不说明**「画布不存在」。

⇒ ⇒ **修法**：第二版改成**枚举 + 分类**（`probes/source860_viewport.py`）：
把所有够大的容器**全部**读出来（带类名与矩形）⟹ ⟹ 两个假设都能被逐条读数区分。

### 1.3 ★ 第二版：画布**纹丝不动**

| | 基线（自适应） | 点「21:9」后 | 复原后 |
|---|---|---|---|
| 画布容器 `h-full w-full`（带 canvas） | 1920×1080 (1.7778) | **1920×1080 (1.7778)** | 1920×1080 |
| `react-flow__viewport` | 732×411 (1.7778) | **732×411 (1.7778)** | 732×411 |
| 机位取景框 | **不在场** | **@(329,270) 1262×541（ratio 2.3334）** | 不在场 |

★ 21:9 态**多出来**的元素只有一个：

```
cls="outline-white/18 absolute rounded-xl outline -outline-offset-1"
@(329,270) 1262×541  ratio 2.3334
```

⟹ ⟹ `outline` ＋ `-outline-offset-1` ⟹ ⟹ 它是**机位取景框**（相机取景器的边框），
**不是**画布。★ 所以 D11 的「改画布宽高比」**是错的**。

### 1.4 ★ 第三版：七档逐档实测（`probes/source860_frame.py`）

| 档 | 取景框 | ratio | 期望（`21/9` 等） | 命中 |
|---|---|---|---|---|
| 自适应 | **不在场** | — | — | ✓ |
| 21:9 | @(329,270) **1262×541** | 2.3334 | 2.3333 | ✓ |
| 16:9 | @(329,185) **1262×710** | 1.7778 | 1.7778 | ✓ |
| 4:3 | @(389,112) **1141×856** | 1.3333 | 1.3333 | ✓ |
| 1:1 | @(532,112) **856×856** | 1.0 | 1.0 | ✓ |
| 3:4 | @(639,112) **642×856** | 0.75 | 0.75 | ✓ |
| 9:16 | @(719,112) **482×856** | 0.5625 | 0.5625 | ✓ |

★ **画布在三态恒为 1920×1080**（每个 ratio 都单独测过）⟹ ⟹ **源站确实不改画布**。

★ 框在**机位视角**下**同样在场**（`④机位视角下` 读到 482×856）⟹ ⟹ 与视角无关。

### 1.5 ★ 反推出的算法（六档全部命中、误差 ≤0.5px）

```
可用区 ＝ 视口去掉 padding
框宽   ＝ min(可用宽, 可用高 × ratio)
框高   ＝ 框宽 ÷ ratio
框     ＝ 在可用区里居中
```

★ 佐证：**所有档的框共享同一个中心**（源站恒为 (960, 540)）。

---

## 2. clone 现状（改之前的实测，`raw/clone-860-aspect.json`）

★ 七档**全部一样**：

```
自适应 → 框 @(347,120) 1227×690  标记 "16:9"
21:9   → 框 @(347,120) 1227×690  标记 "16:9"
16:9   → 框 @(347,120) 1227×690  标记 "16:9"
4:3    → 框 @(347,120) 1227×690  标记 "16:9"
1:1    → 框 @(347,120) 1227×690  标记 "16:9"
3:4    → 框 @(347,120) 1227×690  标记 "16:9"
9:16   → 框 @(347,120) 1227×690  标记 "16:9"
```

⟹ ⟹ **点哪一档都不动**（两处原因）：

① ★ **面板那七格根本没接 store**（`DirectorAspectPanel` 用的是组件内 `useState`）
   ⟹ ⟹ 点它只改自己的本地 state；
② ★ **取景框只支持三档**（`getDirectorAspectValue` 只认 `9:16`／`1:1`，其余一律 16/9）。

★ 而 clone **本来就有**取景框机制（`AspectFrame` ＋ `getDirectorFrameRect`）
⟹ ⟹ **算法是对的、缺的只是档位与接线**。

---

## 3. clone 整改（4 个源文件）

### 3.1 `src/store/directorStore.ts`

- 新增 `DirectorFrameAspectRatio` 类型（六档 ＋ `null`＝自适应）；
- 新增 `DIRECTOR_FRAME_ASPECT_VALUES`（**数值**表：源站逐字 `aj` 的 `value`）；
- 新增 `DIRECTOR_FRAME_ASPECT_ORDER`（源站逐字的七档顺序）；
- 新增状态 `frameAspectRatio: DirectorFrameAspectRatio | null`（初值 `null` ＝ 自适应，
  ⟹ ⟹ 与源站一致：**刚打开导演台时取景框不在场**）＋ action `setFrameAspectRatio`；
- ★ **刻意不动** `aspectRatio`（三值）⟹ ⟹ 它是**截图/导出**用的
  （`directorVideoExport.ts` 的 `outputDimensions[request.aspectRatio]`、
  `directorProjectDocument.ts` 的 `outputPreferences.aspectRatio`）
  ⟹ ⟹ 混用会把导出格式改坏。

### 3.2 `src/components/director/directorViewportMath.ts`

`getDirectorFrameRect` 的第三参从 `DirectorAspectRatio` 改成 **`number | null`**：

- `null` ⟹ ⟹ **返回 `null`** ⟹ ⟹ 取景框**不在场**（源站实测）；
- 其余 ⟹ ⟹ 按**任意数值比例**算（`min(可用宽, 可用高×ratio)` → 居中）。

### 3.3 `src/components/director/DirectorAspectPanel.tsx`

- ★ **接到 store**：`useDirectorStore((state) => state.frameAspectRatio)` ＋ `setFrameAspectRatio`；
- 「自适应」⟹ ⟹ 写 `null`；
- ★ 组件**不再**有 `useState` ⟹ ⟹ 选中态跨模式保留 ＋ **真的生效**。

### 3.4 `src/components/director/DirectorViewport.tsx`

- `AspectFrame` 读 `frameAspectRatio`（不再是导出比例），标记 `data-director-aspect-ratio`；
- `frameRect` 用 `DIRECTOR_FRAME_ASPECT_VALUES[frameAspectRatio]` 换算成数值比例；
- ★ 视口底部那三枚（**clone 自己的扩展**）也接同一个状态；
- ★ 截图链的 `aspectRatio` 另起一个变量名 `captureAspectRatio`（**导出链不动**）。

---

## 4. ★ clone 实测（改之后）：七档全部命中

| 档 | 源站 ratio | clone ratio | 命中 |
|---|---|---|---|
| 21:9 | 2.3334 | **2.3334** | ✓ |
| 16:9 | 1.7778 | **1.7778** | ✓ |
| 4:3 | 1.3333 | **1.3333** | ✓ |
| 1:1 | 1.0 | **1.0** | ✓ |
| 3:4 | 0.75 | **0.75** | ✓ |
| 9:16 | 0.5625 | **0.5625** | ✓ |
| 自适应 | 不在场 | **不在场** | ✓ |

★ **绝对像素不同**（源站 21:9 ＝ 1262×541、clone ＝ 1278×548）
⟹ ⟹ 因为**视口不同**（源站 1920×1080、clone 1358×810）
⟹ ⟹ ⇒ 判据比 **ratio**（可比量）＋ **算法不变量**，**不比**绝对像素。

---

## 5. 判据（`scripts/verify-liblib-batch860.py`，**59/59**）

| 段 | 内容 | 条数 |
|---|---|---|
| S1 | 源码契约（静态、**剥注释后**比） | 7 |
| S2 | 源站实测产物必须存在 ＋ 源站七档 ratio 复核 ＋ 源站共享中心 | 9 |
| S3 | clone 实测（live DOM）逐档 ＋ 共享中心 ＋ 画布恒定 ＋ 底部按钮共享状态 | 42 |
| S4 | 无诊断错误 | 1 |
| | **合计** | **59** |

★ S2 与 S3 里有**一部分判据随档位表展开**（`SOURCE_RATIOS` 七档）：
「自适应」档的判据与其它六档**数量不同**（自适应档框**不在场** ⟹ 多一条
「标记也**不出现**」）。
⇒ ⇒ **别把「每段几条」当固定前提** —— 总数以门禁自己打印的
`59 判据，0 失败` 为准。

### 5.1 ★ 判据的两次「假红」与修法（都是**判据错、不是产品错**）

★ **第一次**：判据写「框必须在 `react-flow__viewport` 里」
⟹ ⟹ **四档假红**（21:9／16:9 过，四档不过）。
★ 根因：`react-flow__viewport` 是**画布**的视口（源站 732×411），
而取景框住在**导演台自己的视口**里（clone 1358×810）
⟹ ⟹ ★ **判据读的东西必须与它声称的东西同粒度**。

★ **第二次**：改判「框在容器里居中」⟹ ⟹ **六档全红**（纵向差 28px）。
★ 根因：**上下 padding 不对称**（clone 32/88、源站 112/968）
⟹ ⟹ 相对**容器**的上下留白**本来就不相等**。

★ **第三次**：想「由撑满的那一维反推可用区」
⟹ ⟹ 又全红（公式把 padding 也算进了可用区）。

⇒ ⇒ **最终修法（不依赖任何 padding 常数）**：
★ **所有档的框共享同一个中心** ⟹ ⟹ 这正是「框在可用区里居中」的无参表述。
  ★ 且**源站也成立**（源站六档中心恒为 (960,540)）⟹ ⟹ 有对照，不是 clone 自己编的。

### 5.2 ★ 静态判据要**精确定位**到具体声明

★ 第一版的「六档都在 store 里」是**全文 `in`** ⟹ ⟹ 漏判：
`DIRECTOR_FRAME_ASPECT_VALUES` 的**键**里也有 `"21:9"` 等字样
⟹ ⟹ 改类型里的那一行**测不出来**。
⇒ ⇒ 改成用正则**只取类型联合块**／**只取值表对象**。

★ 这与 batch 859 的「剥注释后再比」是同一条纪律的两面：
**判据读的东西要与它声称的东西同粒度**（既不能是注释、也不能是同名的别处）。

---

## 6. 阴性对照（`probes/neg860.py` ⟹ `negative-audit.json`）

**9/9 条负控有效**，字节级复原自检 True。

| 变异 | 改坏什么 | 期望翻红的判据 |
|---|---|---|
| N1 | 面板不接 store（读不到也写不进） | `source:panel-writes-to-the-store` ＋ 运行时那几条 |
| N2 | `getDirectorFrameRect` 忽略 `null` | `source:frame-rect-accepts-a-null-ratio` ＋ `panel:auto-has-no-framing-box` |
| N3 | 21:9 的比例值算错 | `source:frame-aspect-values-are-numeric` ＋ `panel:frame-ratio-for-21:9` |
| N4 | 类型里少了 21:9 | `source:frame-aspect-covers-the-six-source-ratios` |
| N5 | 框不居中（`left` 写死 0） | `panel:frame-is-horizontally-centred-for-*` ＋ `panel:all-frames-share-one-centre` |
| N6 | 框不内切（左右边距差 7px） | `panel:frame-insets-the-available-area-for-*` |
| N7 | 面板选中态标记反了 | `panel:selection-is-on-*` |
| N8 | 取景框的比例标记写错 | `panel:frame-marks-*` |
| N9 | store 里删掉 `frameAspectRatio` | `source:store-has-a-separate-frame-aspect-state` |

★ 纪律：每个变异先断言文件**真的被改了**（SHA-256）⟹ ⟹ 不会出现
「脚本崩了 → 文件没改 → 闸门全绿 → 误判成负控有效」；
变异**行数中性**；每条变异后**字节级复原**；收尾再复核一遍全部文件 == 基线。

---

## 7. ★ 源站底部那组三枚比例按钮：clone 自己的扩展

★ 源站视口底部共 **27 枚**控件（`raw/source-860-bottombar.json`）
⟹ ⟹ **没有**任何比例按钮（逐条看过 `aria-label` 与文本）。
⟹ ⟹ clone 底部那三枚（`16:9`／`9:16`／`1:1`）是 **clone 自己的扩展**。

★ 处置：**保留**（不擅自删用户可见功能），但让它们与左侧面板**共享同一个取景比例状态**
⟹ ⟹ 两处不会打架；并在代码注释里**写明**它是 clone 的扩展。

---

## 7.5 ★ 回归（`probes/regress860.py`）

**97 条，红 14 条 ⟹ 全部是已知旧账、零新红。**

★ 与 batch 859 的 **96 条 / 红 14 条**相比：**条数多 1**（多了本批自己的 860 门禁）
而 **红的集合逐条相同** ⟹ ⟹ **本批零新红**。

| 门禁 | 红因 | 性质 |
|---|---|---|
| 门禁 831 | S14／S15／S16／S17 | 旧账 |
| 门禁 835 | 判据 6/7 | 旧账 |
| 门禁 741 | 判据 11/13 | 旧账 |
| 门禁 91 | TransformControls 瞬态 | 旧账 |
| 门禁 736 | 判据 6/10 | 旧账 |
| 门禁 748 | 判据 4/7 | 旧账 |
| 门禁 749 | 判据 7/9 | 旧账 |
| 门禁 782 | 不通过 | 旧账 |
| 门禁 626 | **只剩** `live-controls-reachable/1280x720/crowd-dialog`（**D7**） | 旧账（源站同款） |
| 门禁 546／542 | fixture `/private/tmp/batch542-fixture/hero-character.fbx` 缺失 | 旧账 |
| 门禁 738 | 判据 8/9 | 旧账 |
| 门禁 656 | 2 条 | 旧账 |
| 门禁 648 | 2 条 | 旧账 |

★ **626 仍只有 D7 那 1 条**（`117 checks, 1 failures`）⟹ ⟹
**858 修的时序鲁棒性、859 迁移的结构性断言都没退化**。

★ 本批三道相关门禁在回归里全绿：
`860 → 59 判据，0 失败`／`859 → 48 判据，0 失败`／`858 → 38 判据，0 失败`。

---

## 8. ★ 用户可达（用户硬要求：**从根可达 ＋ 写清怎么测**）

根地址：**`http://localhost:4317/`**（**无参数**）。

### 8.1 桌面端（1920×1080）：从根走到「选择画幅比例」并验证取景框

1. 打开 `http://localhost:4317/`；
2. 在画布上找到标题为「**第一集：咖啡馆对峙**」的那张 **导演台卡片**
   （节点类名 `.react-flow__node-script-execution`）；
3. **鼠标悬停**在它上面 ⟹ 卡片里出现「**打开导演台 →**」按钮；
4. 点它 ⟹ **导演台**盖在画布上 ⟹ 等约 **6.5 秒**；
5. 点左栏 rail 的「**选择画幅比例**」（第 5 枚，`[data-director-rail-entry='aspect-ratio']`）
   ⟹ ⟹ 左侧面板出现七格；
6. ★ 刚打开时**没有取景框**（源站同款：自适应＝无框）；
7. ★ 点「**21:9**」⟹ ⟹ 画面上立刻出现一个**取景框**（白边 ＋ 四周压暗），
   形状是**超宽**的横条（实测 1278×548）；
8. ★ 点「**9:16**」⟹ ⟹ 取景框变成**竖长条**（实测 388×690）；
9. ★ 点「**1:1**」⟹ ⟹ 变成**正方形**（实测 690×690）；
10. ★ 点「**自适应**」⟹ ⟹ 取景框**消失**；
11. ★ 想自己验 ⟹ ⟹ DevTools Console 跑：
    ```js
    document.querySelector('[data-director-aspect-frame]')?.getAttribute('data-director-aspect-ratio')
    // ⟹ 例如 "9:16"；自适应时是 null（框不在场）
    ```

★ 三个选择器就够自己写探针：
`[data-director-aspect-panel]`（面板）、
`[data-director-aspect-option]`（七格）、
`[data-director-aspect-frame]`（取景框）。

### 8.2 移动端（390×844）

★ 源站**没有移动端布局**⟹ ⟹ 移动端这枚入口是 **clone 自己的扩展**；
画幅比例面板与取景框的机制桌面/移动**同源**。

---

## 9. 复现步骤

```bash
export PATH="$HOME/.pyenv/versions/node/v24.6.0/bin:$PATH"
export PATH="$HOME/.pyenv/shims:$PATH"

# ① 源站实测（★ 只读；点比例只改机位参数 ⟹ ⟹ 结束前点回「自适应」复原）
python3 docs/research/liblib-canvas-batch860-2026-10-01/probes/source860_frame.py
python3 docs/research/liblib-canvas-batch860-2026-10-01/probes/source860_viewport.py
python3 docs/research/liblib-canvas-batch860-2026-10-01/probes/source860_bottombar.py

# ② clone 实测（逐档量取景框）
python3 docs/research/liblib-canvas-batch860-2026-10-01/probes/clone860_aspect.py

# ③ 门禁（59/59）
python3 scripts/verify-liblib-batch860.py

# ④ 阴性（会**改源码**做变异 ⟹ ⟹ 跑完必须确认文件已复原）
python3 docs/research/liblib-canvas-batch860-2026-10-01/probes/neg860.py

# ⑤ 回归（既有门禁清单）
python3 docs/research/liblib-canvas-batch860-2026-10-01/probes/regress860.py

# ⑥ 受控对照（★ 会把源码换回 HEAD ⟹ ⟹ 跑完确认已复原）
python3 docs/research/liblib-canvas-batch860-2026-10-01/probes/attrib860.py
# ⑥' MIX 半回退态（★ 必须**紧接** WORK 态跑 ⟹ ⟹ 单独脚本）
python3 docs/research/liblib-canvas-batch860-2026-10-01/probes/attrib860_mix.py
```

---

## 10. ★ 受控对照（`probes/attrib860.py` ＋ `probes/attrib860_mix.py`）

### 10.1 四态：把**源码**换回 HEAD ⟹ ⟹ 读数必须能区分

| 态 | 源码 | 新门禁 860 | 老门禁 | 结论 |
|---|---|---|---|---|
| HEAD-1 | 四个文件全换回 HEAD | rc=1，**19 条红** | 859 绿／626 红 1（D7 旧账）／其余绿 | — |
| HEAD-2 | 同上（第二遍） | rc=1，**19 条红** | 同上 | ★ **两遍读数一致** ⟹ 稳定 |
| WORK-1 | 本批工作副本 | rc=0，**0 条红** | 859 绿／626 红 1（D7 旧账）／其余绿 | — |
| WORK-2 | 同上（第二遍） | rc=0，**0 条红** | 同上 | ★ **两遍读数一致** |

★ `稳定=True`／`新门禁有牙=True`／`复原=True`（SHA-256 复核），
★ **WORK 独有的红条 ＝ 空**（⟹ ⟹ 本批**没有引入任何新问题**）。

★ **HEAD 态那 19 条红**里，静态 7 条（全指向 store／math／panel／viewport
四处新代码）＋ 运行时 12 条（六档各 `frame-exists`／`frame-marks`，
`自适应` 档两条报「框还在 1227×690」与「标记还是 16:9」）
⟹ ⟹ **每一处改动都有牙**，不是靠某一处巧合蒙对的。

★ **HEAD 态里 `panel:frame-ratio-for-16:9` 是绿的** ⟹ ⟹ 因为 HEAD 态的默认比例
**恰好就是 16:9** ⟹ ⟹ 这一条不参与区分 ⟹ ⟹ 这是**设计如此**，不是漏判。

### 10.2 MIX 半回退态：只回退 `DirectorAspectPanel.tsx`

★ **只**把面板文件换回 HEAD（⟹ ⟹ 回到「组件内 `useState`」的老写法），
**保留** store 与 math 的新代码
⟹ ⟹ 正好**隔离出「面板没接 store」这一条**。

| 门禁 | MIX 态读数 |
|---|---|
| 门禁 860 | rc=1，**13 条红**（两遍一致 ⟹ 稳定） |
| 门禁 859 | rc=0，0 红 |
| 门禁 590 | rc=0，0 红 |

★ 13 条红的**构成**（读原始输出原文，不按「我以为的落点」写）：
- **静态 1 条**：`source:panel-writes-to-the-store`
  （⟹ ⟹ 面板没从 store 读／没往 store 写）；
- **运行时 12 条**：六档各 `panel:frame-exists-for-*` ＋ `panel:frame-marks-*`，
  详情全是 `None`（⟹ ⟹ 点了格子，框**压根不出现**）。

★ **store 与 math 那几条静态判据在 MIX 态是绿的**
（`store-has-a-separate-frame-aspect-state`／`initial-state-is-auto`／
`covers-the-six-source-ratios`／`values-are-numeric`／
`frame-rect-accepts-a-null-ratio`）
⟹ ⟹ 说明**隔离干净**：红的确实只是「面板没接 store」这一处。

★ **MIX 态不红**的判据也符合预期：`panel:selection-is-on-*`（HEAD 面板用
**组件内** state ⟹ 选中态本地就生效）、`panel:auto-has-no-framing-box`
（自适应本来就无框）、`panel:the-canvas-never-changes`（画布本来就不动）。

⇒ ⇒ **MIX 态红得「不多不少」** ⟹ ⟹ 证明**判据层**有牙，
而不是「整个功能都没了所以一片红」。

---

## 11. ★ 登记的差异

### D11 **改写**（batch 859 登记的说法被本批实测推翻）

★ 原说法：「clone 的『选择画幅比例』选中项**不改画布宽高比**」
⟹ ⟹ ★ **错**：源站本来就不改画布；clone 的差距是
**① 取景框只支持三档**＋**② 面板七格没接 store**。
★ 本批**已修**这两条。

### 仍存差异（如实登记）

★ **clone 的取景框样式与源站不同**：源站是
`outline-white/18 absolute rounded-xl outline -outline-offset-1`（**描边**在外框），
clone 是 `border border-white/75 shadow-[0_0_0_9999px_rgba(0,0,0,0.24)]`
（**边框** ＋ 四周阴影压暗）⟹ ⟹ 视觉近似但**类名与实现不同** ⟹ ⟹ 登记待对齐。

★ **绝对像素不同**：源站视口 1920×1080、clone 1358×810 ⟹ ⟹ 同一个比例的框
像素不同 ⟹ ⟹ 这是**视口尺寸**的差异，不是算法差异（ratio 与算法不变量都一致）。

★ **导出比例仍是三值**（`16:9`／`9:16`／`1:1`）：源站截图/导出的比例档位
**未取证**（本批没有点「截图」按钮 ⟹ ⟹ 避免副作用）⟹ ⟹ 登记待查。
