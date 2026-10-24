# batch 864 —— D17 复核与推翻 ＋ 整改「构图参考线开关点不到」＋ 本地埋点等价实现

> ★ **一句话**：本批先**推翻**了一条自己登记过的差距（**D17**：源站把比例与
> `reference_line` **写进机位对象** —— 真相是它**只发埋点**），
> 再**整改**了 batch 863 带出来的一个**真缺陷**
> （取景框右上角那枚「构图参考线」开关**被坐标控件盖住 ⟹ 点不到**），
> 并把源站那条埋点做成 clone 的**本地等价实现**（**不触网**）。

---

## 1. 靶子与结论（★ 先说结论）

| # | 靶子 | 结论 |
| --- | --- | --- |
| ① | **D17**（batch 862 登记：「源站把比例与 `reference_line` 写进机位对象」） | ★ **推翻** ⟹ ⟹ 源站**只发埋点**、**不改任何状态** ⟹ ⟹ clone 的全局单值模型**本就同构** ⟹ ⟹ 「clone 的差距」**不存在** |
| ② | batch 863 加的遮罩容器（`z-10`）**压住了**框上那枚开关 ⟹ ⟹ **开关点不到** | ★ **真缺陷，已整改**（把 clone 自有的坐标控件从 `z-20` 降到 `z-10`） |
| ③ | 源站那条埋点在 clone 侧怎么办 | ★ 做成**本地等价记录**（事件名与属性**逐字同构**，**不触网**） |
| ④ | batch 863 的「源站运行时待补」 | ★ **补齐**（源站已恢复 ⟹ 真实读数入库） |
| ⑤ | 「源站截图/导出的比例档位」（batch 860 登记为**未取证**） | ★ **结案**：源站的「截图」按钮**没有比例面板**（直接出图，用**当前取景比例**）⟹ ⟹ clone 的三档截图比例是 **clone 自己的扩展** |

---

## 2. D17 的复核与推翻（三条独立证据）

### 2.1 源站逐字：`n4` 是埋点，不是写状态

```js
// chunk /tmp/liblib_srcjs2/0fmehki05gkzw.js.js
n4 = useCallback((e,t,r,n) => {
  (0,nZ.S)("libtv.canvas.director.camera.update", {
    director_session_id: nb.current, camera_uuid: e,
    setting_name: t, setting_value: r, operation_source: n })
}, [])

// 右侧面板选比例：
o$ = useCallback(e => { tn(e);
  let t = e1 || rL.cameras[0]?.id;
  t && n4(t, "aspect_ratio", (0,nZ.R)(e), "right_panel"); }, [e1, rL.cameras, n4])

// 框上那枚「构图参考线」开关：
onToggleCompositionGrid: null !== tr ? () => {
  let e = !ti, t = e1 || rL.cameras[0]?.id;
  t && n4(t, "reference_line", (0,nZ.p)(e), "right_panel"), to(e); } : void 0
```

⟹ ⟹ `n4` **只调 `nZ.S` 发一条埋点** ⟹ ⟹ **不改任何状态**。
★ ★ 顺带把源站的**真实模型**说清楚了：
`tr`（取景比例）与 `ti`（参考线）**都是组件级单值**，
机位 id 只是**埋点里报给后端的那台机位**（选中机位，否则第一个）。

### 2.2 源站运行时实测（`raw/source-864-camera-write.json`）

★ 探针：开导演台 ⟹ 点右侧面板「16:9」⟹ 点框上那枚「构图参考线」⟹ **全程抓请求**。

两条事件（**逐字**）：

```json
{"e":"libtv.canvas.director.camera.update",
 "var":{"camera_uuid":"director-main-camera",
        "setting_name":"aspect_ratio","setting_value":"16:9",
        "operation_source":"right_panel", …17 个环境属性…}}
{"e":"libtv.canvas.director.camera.update",
 "var":{"camera_uuid":"director-main-camera",
        "setting_name":"reference_line","setting_value":1,
        "operation_source":"right_panel", …17 个环境属性…}}
```

⟹ ⟹ **落点是 `POST https://api2.liblib.art/api/www/log/acceptor/f`**（埋点接收端点）；
⟹ ⟹ **没有任何工程状态写入请求**（只有 `api.liblib.tv/api/canvas/project/heartbeat` 心跳）；
⟹ ⟹ `setting_value` 的**类型**也不同：比例是**字符串**、参考线是**数字 1**。

### 2.3 静态反证

★ 整个 chunk（**1,018,130 字符**）里 **`reference_line` 只出现 1 次**（就在上面那条埋点里）
⟹ ⟹ 它**从来不是**机位对象上被读写的字段。

### 2.4 ⟹ 结论

★ **D17 被推翻**：
源站的模型是「取景比例与参考线都是**组件级单值状态**」，
⟹ ⟹ clone 的全局 `frameAspectRatio` ＋ `showThirds` **与源站同构**
⟹ ⟹ 「clone 缺了机位级写入」这个**差距不存在** ⟹ ⟹ **从待办里划掉**。
★ 源站与 clone 在这一处**真正的差别**只有一条：源站**上报到后端**，
clone **不触网** ⟹ ⟹ 本批做的是**本地等价记录**（§4）。

---

## 3. ★★ 整改：batch 863 带出来的真缺陷（开关点不到）

### 3.1 症状

★ 取景框右上角那枚「构图参考线」按钮（batch 862 加的）**点不动** ⟹ ⟹
命中测试显示它的位置上是 **3D 视口的坐标控件**（`aria-label="X 反向"`）。

### 3.2 根因（★ 两个原因叠在一起）

① **batch 863 的遮罩容器创建了层叠上下文**：
   源站逐字的容器是 `… z-10` ⟹ ⟹ 它**创建**层叠上下文
   ⟹ ⟹ 容器里那枚开关的 `z-20` 被**困在 z-10 里**；
② **clone 自有的坐标控件是 `z-20`** ⟹ ⟹ 与容器**平级打架** ⟹ ⟹ 控件赢了。

★ ★ 为什么 863 自己的门禁**没抓到**：
863 门禁里**有**「点开关 ⟹ 分线 0→4」那条判据，**它当时是绿的**
⟹ ⟹ 因为**坐标控件的屏幕位置会随取景框的宽高比移动**
⟹ ⟹ 有时重叠、有时不重叠 ⟹ ⟹ **这条判据是「看运气」的**
⟹ ⟹ ★ **教训：一条判据若「有时红有时绿」，它就不是判据，是运气。**

### 3.3 修法（★ **不动源站逐字结构**）

★ 把**clone 自有**的那枚坐标控件容器从 `z-20` 降到 `z-10`
⟹ ⟹ 遮罩容器（DOM 上**更靠后**）盖过它 ⟹ ⟹ 开关恢复可点；
⟹ ⟹ 而且那枚控件会**跟着视口里除取景框外的一切一起被压暗**
⟹ ⟹ 与源站「取景框外整片都压暗＋模糊」的模型**一致**。

★ ★ 为什么**不改**源站逐字的那个 `z-10`：
源站的容器与开关**本来就在 z-10 层叠里**，
⟹ ⟹ 源站没这个问题**只因为**它的取景框是**全屏**容器里算的（框右边缘 ≤1591），
而那枚控件在**视口右上角**（≈1840）⟹ ⟹ 两者不重叠；
⟹ ⟹ clone 的视口**更窄**（1358 vs 1920）⟹ ⟹ 才会撞上
⟹ ⟹ 根因仍是 **D18（布局级）** ⟹ ⟹ 本条只是把**交互**修回来。

★ 实测（改后）：命中测试返回的**最顶层元素就是那枚开关** ⟹ ⟹ 点击成功 ⟹ ⟹ 分线 0→4 ✔

---

## 4. 实施（★ 4 个源文件）

### 4.1 新增 `src/lib/directorTelemetry.ts`

★ 事件名与属性**逐字同构**于源站：
`{e:"libtv.canvas.director.camera.update", var:{camera_uuid, setting_name, setting_value, operation_source}}`；
★ `var` 里**只有**源站那四个语义键（源站多的 17 个是**埋点 SDK 自动附加的环境属性**
—— `dpr`／`sw`／`sh`／`region`／`lang`／硬件与 GPU 指纹／会话 id ⟹ ⟹ clone 没有 SDK ⟹ ⟹ 不该有）；
★ 另有两个小工具：`resolveDirectorTelemetryCameraId`（**选中机位优先，否则第一个机位** —— 源站逐字 `e1 || rL.cameras[0]?.id`）与日志上限。

### 4.2 `src/store/directorStore.ts`

★ 加 `telemetryLog: DirectorTelemetryCameraUpdateEvent[]`（初始 `[]`）
＋ `recordTelemetry(event)` 动作（上限 50 条）⟹ ⟹ **刻意不进持久化 schema**（视图态）。

### 4.3 `src/components/director/DirectorAspectPanel.tsx`

★ 点七档里的任意一档 ⟹ ⟹ 记一条 `setting_name:"aspect_ratio"`
（`setting_value` ＝ 比例字符串；**「自适应」是 `null`** —— 源站逐字 `{label:null,value:null}`）。

### 4.4 `src/components/director/DirectorViewport.tsx`

★ 框上那枚「构图参考线」开关 ⟹ ⟹ 记一条 `setting_name:"reference_line"`
（`setting_value` ＝ **数字** `1`／`0` —— 源站逐字 `(0,nZ.p)(e)` 把布尔转成了数字）；
★ ★ **clone 自己那枚底部胶囊按钮（源站没有这个入口，D19）⟹ ⟹ 不记事件**
⟹ ⟹ 不为 clone 自己的入口编造源站事件。

★ ★ **底线**：这套「埋点」**绝不触网**（原型不碰真实接口）
⟹ ⟹ 门禁里有一条**底线判据**：这四个文件里**不许出现** `fetch(`／`XMLHttpRequest`／`sendBeacon`／`axios`。

---

## 5. 验收

（★ 数字以本 README 落盘时的实测为准。）

### 5.1 门禁

| 门禁 | 结果 |
| --- | --- |
| `scripts/verify-liblib-batch864.py` | **38 判据、0 失败** |
| `scripts/verify-liblib-batch863.py`（复验） | **113 判据、0 失败**（gizmo 的 z 改动后仍全绿；★ 本批给 863 门禁**补了 3 条**：命中测试的前提比例、z 序机制、命中测试本体） |

★ 864 门禁的判据构成：S1 静态（事件名／四个属性键／`operation_source`／**不触网底线**／
store 有日志与动作／两个入口都在／★ **不许造出 D17 那个假字段**）＋
S2 **源站运行时取证**（端点是埋点端点／**没有工程状态写入**／两条事件的取值逐字／
多出来的键只是环境属性）＋
S3 **clone 运行时读数**（初始日志为空／点比例记一条／「自适应」记 `null`／
参考线记**数字** 1／0／`camera_uuid` ＝ 选中机位／★ **底部扩展按钮不记**）＋
S4 **同口径对照**（clone 的 `var` 恰好四个键／`operation_source` 相等／两个 `setting_name` 的**值类型**相等）。

### 5.2 阴性对照

`probes/neg864.py` ⟹ ⟹ **7/7**（N1 事件名／N2 `operation_source`／N3 **塞进 `fetch(`**／
N4 参考线取值反转／N5「自适应」不记 `null`／N6 **造出 D17 的假字段**／N7 `camera_uuid` 写死）。

### 5.3 回归

`probes/regress864.py` ⟹ ⟹ **108 条**（沿用 863 的清单 ＋ 本批 `864`；
★ 其中 batch 91 有 `.py` ＋ `.mjs` **两份** ⟹ ⟹ 实际是 **107 个不同批次号**）
⟹ ⟹ **红 18 条**。

★ ★ **判据不是「红 0 条」，而是「**本批引入的红 == 0**」**：

| 分类 | 条数 | 明细 |
| --- | --- | --- |
| 既有旧账（基线就红） | **17** | `831`／`835`／`741`／`91`／`736`／`748`／`749`／`782`｜`626`（D7：源站同款）／`546`＋`542`（fixture `/private/tmp/batch542-fixture/hero-character.fbx` 缺失）／`738`（C7 写死个数过期）／`656`（场景预测）／`648`（casualty 判据）／`645`（四个常数在每个宽度下成立）／`722`／`629`（底部压盖带） |
| ★ **已归因的偶发** | **1** | `62`（★ 定点归因见下） |
| ★★★ **本批引入的红** | **0** | — |
| ★ WATCH（54 条「**基线为绿**、且本批动过其比对对象」）里红的 | **0** | — |

★ 复算（`python3 …/probes/regress864.py --rescore`）⟹ ⟹ **判定：通过**（退出码 0）。
★ ★ 本批把「**跑**」与「**判定**」**分开**了 ⟹ ⟹ 改判据时**不必重跑 108 条**
（`--rescore` 只按已有读数复算）⟹ ⟹ 但读数**必须**来自真实那一跑。

#### ★ 「`62.py`」的定点归因（★ 新红必须归因，不能放过）

★ 第二轮回归报出 **1 条新红**：`62.py`
（★ 863 基线与本批**第一轮**回归里它都是**绿的**）⟹ ⟹ 必须归因。

★ 归因证据（三条，缺一不可）：

1. **红条原文**（不是「它好像坏了」）：
   `requestfailed:GET:http://localhost:4317/images/liblib-panels/toolbox-24.webp:net::ERR_ABORTED`
   （`toolbox-25.webp` 同款）⟹ ⟹ 是**图片请求被中止**，
   典型的 **teardown 竞态**（浏览器在图片加载完之前就关闭）；
2. ★ **作用域**：本批**只**改了 `directorTelemetry.ts`／`directorStore.ts`／
   `DirectorAspectPanel.tsx`／`DirectorViewport.tsx` 四个文件
   ⟹ ⟹ 而 `62.py` 里 `aspect`／`telemetry`／`director-aspect` **出现 0 次**
   ⟹ ⟹ 它**根本不碰**本批改的区域；
3. ★ **连跑三次**：**红 / 绿 / 绿** ⟹ ⟹ 它**本来就会偶发**。

★ ⇒ 结论：`62.py` 是**已归因的偶发门禁**，**不是**本批引入。
★ ⇒ 它被**单列**在 `KNOWN_FLAKY`（而不是塞进 `KNOWN_RED`）
⟹ ⟹ 「平时是绿的」与「基线就红」是**两回事**
⟹ ⟹ 塞进旧账会让它以后真坏了也不报 ⟹ ⟹ 那就是**掩盖**。

### 5.4 受控对照

`probes/attrib864.py` ⟹ ⟹ 把**源码**换回 HEAD ⟹ ⟹ 新门禁必须翻红（证明有牙）。

#### ★★ 第一轮：**门禁没牙**，差点放过去（★ 本批最重要的自曝）

★ 第一轮读数：

| 状态 | 864 门禁 | 863 门禁 | 说明 |
| --- | --- | --- | --- |
| `HEAD-1`／`HEAD-2` | rc=1，**1 条「红」＝CRASH**（`FileNotFoundError`） | rc=0，**0 条红** | ★ 863 门禁**没抓到**那个遮挡缺陷 |
| `MIX` | rc=1，**1 条「红」＝CRASH**（`Locator.click` 超时 8000ms） | rc=0，**0 条红** | ★ 同上 |
| `WORK-1`／`WORK-2` | rc=0，0 红 | rc=0，0 红 | ✔ |

★ ★ **两个「红」其实是「崩」** ⟹ ⟹ 脚本的 `newGateHasTeeth` 判据（HEAD rc≠0）
**照样给了 True** ⟹ ⟹ ★ **「崩」也是「有牙」** —— 这是最险的一种假绿：
门禁只要**崩得够厉害**就算「证明了它有牙」。

★ ★★ **真正的发现**：MIX 态那条崩溃的**日志原文**里写着

```
<button title="X 反向" … data-director-viewport-gizmo-button="x-negative" …>
  from <div aria-label="3D视口原生坐标控件" data-director-viewport-gizmo="true"
        class="absolute right-5 top-5 z-20 h-20 w-20">
  subtree intercepts pointer events
```

⟹ ⟹ ★ **遮挡缺陷在 MIX 态确实复现**（坐标控件的「X 反向」按钮拦住了开关）
⟹ ⟹ 但 **863 门禁的命中测试判据却判绿** ⟹ ⟹ ⇒ **那条判据测的不是这个缺陷**。

★ ★★ **根因**：863 门禁的比例循环是
`RATIOS = ["21:9", "16:9", "4:3", "1:1", "3:4", "9:16"]`
⟹ ⟹ 循环**结束在 `9:16`**（**最窄**的一档）
⟹ ⟹ 而命中测试跑在循环**之后** ⟹ ⟹ 那一档的框**很窄**
⟹ ⟹ 框的右上角离视口右上角的坐标控件**很远** ⟹ ⟹ **两者永不重叠**
⟹ ⟹ ⇒ **在那一档上判「点得到」，永远测不出遮挡**。
★ ⇒ **判据的前提（比例）本身没被钉住** ⟹ ⟹ 这是「判据要钉住前提」的又一例。

#### ★ 修法（三条，都落在门禁里）

1. **命中测试之前先切到会重叠的那一档**：用 **store**（不是点选项，
   避开「点选项会被 gizmo 挡住」那个坑）把比例设成 `16:9`（最宽）；
2. **把当前比例钉成一条判据**（`clone:the-hit-test-runs-at-the-ratio-where-they-overlap`）
   ⟹ ⟹ 免得以后又悄悄跑到不重叠的那一档；
3. **加一条机制侧判据**（`clone:the-viewport-gizmo-does-not-outrank-the-mask-container`）：
   读坐标控件与遮罩容器的**计算样式 z-index** ⟹ ⟹ 直接把层叠机制摆到台面上；
4. 864 门禁**点之前先判命中**（`clone:the-frame-toggle-is-the-topmost-element-at-its-center`）
   ⟹ ⟹ 被盖住时**具名判红**，不再超时崩溃；
5. 864 门禁**缺文件判红、不判崩**（`source:the-file-…-exists`）⟹ ⟹ HEAD 态也能说出缺什么。

#### ★ 第二轮读数（★ 修完之后）

| 状态 | 864 门禁 | 863 门禁 |
| --- | --- | --- |
| `HEAD-1`／`HEAD-2` | rc=1，**47 条红（全部具名，零 CRASH**） | rc=1，**18 条红（含具名命中测试红）** |
| `MIX` | rc=1，**50 条红（零 CRASH）**，第一条就是命中测试 | rc=1，**18 条红**，第一条就是 z 序判据 |
| `WORK-1`／`WORK-2` | rc=0，**0 红** | rc=0，**0 红** |

★ **决定性的两条 detail**（都不是「感觉像坏了」，是**读数**）：

- HEAD 态 863 门禁的命中测试红，detail 原文：
  `'isToggle': False`、`'命中标签': 'X 反向'`
  ⟹ ⟹ **开关的最顶层命中者是坐标控件的「X 反向」按钮** ⟹ ⟹ 缺陷**客观存在**；
- MIX 态 863 门禁的 z 序红，detail 原文：
  `'gizmoZ': '20'`、`'containerZ': '10'`
  ⟹ ⟹ 坐标控件**高过**遮罩容器 ⟹ ⟹ 容器里的开关（`z-20`）被**困在容器里**
  ⟹ ⟹ 这就是缺陷的**机制**。

★ 脚本自检：`稳定AcrossTwoRuns=**True**`／`newGateHasTeeth=**True**`／
`restored=**True**`／`MIX行数中性=**True**`／
`newGateCrashOnHEAD=[]`／`gate863CrashOnHEAD=[]`／`mixCrash864=[]`／`mixCrash863=[]`
／**diffs**：863 门禁 **HEAD 独有 18 条、WORK 独有 0 条**（⟹ ⟹ 隔离干净）。

★ 产物：`controlled-comparison.json` ＋ `raw/attrib/<态>/*.txt`（各态的完整门禁输出）。

### 5.5 构建链

| 项 | 结果 |
| --- | --- |
| `npx tsc --noEmit` | ✔ |
| `npx eslint`（本批 4 个源文件） | ✔ |
| `npx next build` | ✔ |
| `npm run assertions:check` | ✔ **810** 个脚本、**0** 个空洞断言 |
| `npm run docs:check` | exit=1 ⟹ ★ 断链**全部**在 `docs/user-manual/**`（他人并发编辑区）⟹ ⟹ 本批目录 **0** 处断链 |

---

## 6. 差异登记（如实登记，不假装已对齐）

- ★★ **D17 推翻**（★ 前向更正，batch 862 的台账行**保留不改**）：
  「源站把比例与 `reference_line` 写进机位对象」**不成立** ⟹ ⟹ 源站**只发埋点**
  ⟹ ⟹ clone 的全局单值模型**本就同构** ⟹ ⟹ **这个差距不存在** ⟹ ⟹ 从待办里划掉。
- ★ **D18 结案（定性完成，不改）**：取景框的**像素几何**差异 **不是公式写错**，而是**布局级**：
  源站的框在**全屏容器**（1920×1080）里按逐字公式算
  （`o = 宽 − 左面板281 − 右面板281`、`s = 高 − 224`、`框宽 = min(o − 96, s × 比例)`、居中），
  ⟹ ⟹ **六档全部命中**（21:9 1262×541／16:9 1262×710／4:3 1141×856／1:1 856×856／3:4 642×856／9:16 482×856）；
  clone 的视口是 **810 高的盒子** ⟹ ⟹ 绝对像素**不可比** ⟹ ⟹ **不改**。
  ★ 它也是 §3 那个「开关被盖住」缺陷的**根因**。
- ★ **D19（仍在）**：clone 视口底部胶囊那枚「九宫格辅助线」是 **clone 自己的扩展** ⟹ ⟹ 保留。
- ★ **D20（已在 batch 863 结案）**：框外遮罩已改成源站逐字。
- ★ **D21（新登记）**：源站在「改取景比例」与「切参考线」时会**上报一条埋点**
  （逐字属性见 §2.2）⟹ ⟹ clone **不触网** ⟹ ⟹ 只做**本地等价记录**
  ⟹ ⟹ 这**不是功能差距**，但**如实登记**（源站有、clone 没有对外上报）。
- ★ **D22（新登记，并**核实为非差距**）**：源站的遮罩层铺满 **1920×1080**（全屏），
  clone 铺满 **1358×810**（3D 区）⟹ ⟹ **看着像差距**，实测**不是**：
  源站的左右两列是 `z-20`（**在遮罩之上**）⟹ ⟹ 那点覆盖差**看不见** ⟹ ⟹ **不是差距**。
- ★ **D23（新登记）**：源站的「截图」按钮**没有比例面板**（点一下**直接出图**，
  埋点里用的是**当前取景比例** `aspect_ratio:(0,nZ.R)(tr)`）；
  clone 的截图/导出有**独立的三档比例** ⟹ ⟹ 那是 **clone 自己的扩展** ⟹ ⟹ 如实登记。
- ★ **D25（新登记）**：源站取景框那三层的**嵌套**是
  「遮罩层／**空框**／三分线层／开关」**四者平级**（都是遮罩容器的直接子元素）；
  clone 把**三分线与开关塞进了框里** ⟹ ⟹ **结构与源站不同**（视觉无差别）⟹ ⟹ **只登记、不改**
  （改了会动到 862／863 两条门禁的比对对象 ⟹ ⟹ 留待专门一批处理）。

---

## 7. 本批新增的方法学

① ★★ **「有时红有时绿」的判据不是判据，是运气。**
   863 门禁里「点开关 ⟹ 分线 0→4」在**坐标控件没重叠时**是绿的
   ⟹ ⟹ 掩盖了 863 带出来的真缺陷 ⟹ ⟹ ★ 修法：把会移动的元素（坐标控件的屏幕投影）
   也纳入读数 ⟹ ⟹ 或者干脆断言「命中测试的最顶层元素就是目标」。
② ★★ **层叠上下文会把 `z-index` 困住。**
   容器只要**定位 ＋ 有 z-index** 就创建层叠上下文 ⟹ ⟹ 里面所有 `z-20` 都**出不来**
   ⟹ ⟹ 「加了一层遮罩」这件事**顺手改掉了别的元素的层叠关系**。
   ⟹ ⟹ ★ **每次给界面加一层带 z-index 的容器，都要重测那一层里所有可点元素。**
③ ★★ **登记的差距要能被推翻。**
   D17 登记时只看了 `n4(cameraId, "aspect_ratio", …)` 这一行
   ⟹ ⟹ 把它读成了「写进机位对象」⟹ ⟹ ★ 教训：**看到「往某个 id 上写某个字段」，
   要先确认那个函数**是**状态写入**（不是埋点／不是日志／不是上报）。
④ ★★ **源站会不定期弹模态（A/B 实验）**，探针必须能扛：
   「找不到关闭按钮」是**正常状态**；定位要按**叶子节点的精确文本**、
   再用 **DOM `.click()`** 绕过可操作性检查。
   ★ 顺带：★ **别用「那枚只在特定状态下才存在的按钮」当「界面已打开」的判据**
   ——我第一版用「构图参考线开关在场」判「导演台已打开」⟹ ⟹ 三次尝试全判成「未打开」⟹ ⟹ 白跑。
⑤ ★★★★ **「崩」也是「有牙」** —— 最险的一种假绿。
   受控对照第一轮：HEAD 态的 864 门禁因为**读不到新增文件**而 `FileNotFoundError`
   ⟹ ⟹ 脚本的「HEAD 态 rc≠0 ⟹ 有牙」判据**照样给了 True**。
   ⟹ ⟹ ★ **门禁「崩得够厉害」就会被当成「证明了它有牙」**。
   ⟹ ⟹ ⇒ **判据必须要求「具名红条 ＋ 零 CRASH」**，不能只看退出码。
   ★ 这一条是本批**差点放过去**的东西：它把「有牙」这个结论**伪装**成了真的。
⑥ ★★★★ **判据的前提（比例／断点／状态）本身必须被钉住。**
   863 门禁的命中测试跑在比例循环**结束的那一档**（`9:16`，最窄）
   ⟹ ⟹ 那一档开关与坐标控件**永不重叠** ⟹ ⟹ 判据**测不出**缺陷 ⟹ ⟹ HEAD/MIX 态都判绿。
   ★ ⇒ 修法两条：① 判据**之前**先把前提切到「会出问题的那一档」；
   ② **把前提本身写成一条判据**（`the-hit-test-runs-at-the-ratio-where-they-overlap`）。
   ★ ⇒ 通用式：**「在什么前提下这条判据才有意义」必须出现在判据里。**
⑦ ★★★ **回归的 WATCH 名单不许放「基线就是红」的旧账。**
   第一版把 10 条旧账放进了 WATCH ⟹ ⟹ 脚本报「10 条红的 WATCH」⟹ ⟹ 退出码 1
   ⟹ ⟹ **把旧账算成本批引入的红** ⟹ ⟹ 真正的判据被淹没。
   ★ ⇒ 修法：旧账单列一份 `KNOWN_RED`，判据改成「**新红**（红 − 旧账）== 0」。

---

## 8. 用户可达（怎么点、怎么测）

★ **clone 跑起来**：见 `docs/research/LIBTV_CLONE_REACHABILITY.md` 的 §0
（`npm run dev` ⟹ 浏览器打开 `http://localhost:4317/`）。

★ **看本批两件事的路径**：

1. 打开 `http://localhost:4317/`；
2. hover 画布上的**导演台卡片** ⟹ ⟹ 点「**打开导演台 →**」；
3. 左侧 **rail** 点「**选择画幅比例**」⟹ ⟹ 点「**16:9**」
   ⟹ ⟹ **取景框出现**（框外压暗＋模糊，框内被 mask 挖空）；
4. ★ **点取景框右上角那枚「构图参考线」** ⟹ ⟹ ★ **现在一定能点到**
   （batch 863 之后它会被坐标控件盖住 ⟹ ⟹ 本批已整改）⟹ ⟹ 框内出现 4 条分线；
5. ★ **看本地事件记录**（浏览器控制台）：
   ```js
   window.__director_store.getState().telemetryLog
   // ⟹ ⟹ 形如
   // [{e:"libtv.canvas.director.camera.update",
   //   var:{camera_uuid:"director-camera-main", setting_name:"aspect_ratio",
   //        setting_value:"16:9", operation_source:"right_panel"}}, …]
   ```
   ⟹ ⟹ 点第 4 步那枚开关 ⟹ ⟹ 日志里**多一条** `setting_name:"reference_line"`、
   `setting_value:1`（**数字**）⟹ ⟹ 再点 ⟹ ⟹ `setting_value:0`。

★ **选择器**（给自动化用）：

- 取景框：`[data-director-aspect-frame]`；框上开关：`[data-director-frame-thirds-toggle]`
- 遮罩层：`[data-director-aspect-mask]`；容器：`[data-director-aspect-mask-container]`
- 面板七格：`[data-director-aspect-option]`
- 坐标控件：`[data-director-viewport-gizmo]`（★ 本批把它的 z 从 20 降到 10）

★ **自己跑门禁**：

```bash
python3 scripts/verify-liblib-batch864.py      # 期望：37 判据，0 失败
python3 scripts/verify-liblib-batch863.py      # 期望：110 判据，0 失败
python3 docs/research/liblib-canvas-batch864-2026-10-01/probes/neg864.py   # 期望：7/7
python3 docs/research/liblib-canvas-batch864-2026-10-01/probes/regress864.py
```

---

## 9. 复现步骤（一条链）

1. **契约提取**：chunk 的 `n4` 定义 ＋ `o$` ＋ `onToggleCompositionGrid` 三段逐字；
2. **源站运行时取证**：`probes/source864_camera_write.py`
   ⟹ ⟹ `raw/source-864-camera-write.json`（两条事件 ＋ 全部请求）；
3. ★ **源站遮罩运行时复核（补 batch 863 的「待补」）**：`probes/source863_frame_mask.py`
   ⟹ ⟹ `raw/source-863-frame-mask.json`（真实读数已入库）；
4. **clone 实测**：`probes/source864_capture_ratios.py`（源站截图面板取证）
   ⟹ ⟹ `raw/source-864-capture-ratios.json`；
5. **门禁**：`scripts/verify-liblib-batch864.py`（源站期望值**只从入库 raw 读**）；
6. **阴性**：`probes/neg864.py`（行数中性 ＋ 变异已落地 ＋ 字节级还原）；
7. **回归**：`probes/regress864.py`（108 条）；
8. **受控对照**：`probes/attrib864.py`（HEAD↔WORK）。
