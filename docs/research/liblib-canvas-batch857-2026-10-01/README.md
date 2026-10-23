# batch 857 — 导演台「群众阵列（crowd）」对话框（对齐源站逐字 ＋ 删掉多出来的第二个入口）

> 上一批：batch 856「组的检查器与画布 gizmo」（结论反转），提交 `c9e17071`。
> ★ 本批的靶子是**导演台的群众阵列（crowd）**：
> ⟹ ⟹ 一开始怀疑的是「默认值 1.2 / 1.6 搞反了」⟹ ⟹ **一读代码就发现这个怀疑本身是错的**。

---

## 0. 一句话结论

★ **源站只有一个 crowd 入口**（自指判据：全页 `aria-label == 添加群众阵列` 的元素**只有 1 个**），
⟹ ⟹ clone **有两个**（rail 的对话框 ＋ 视口工具栏那枚按钮）⟹ ⟹ **多出来的那个入口本批删掉**。

★ ★ 但**本批最值钱的一条不是「删」**，而是**差点判反**：

| 数字 | 源站位置 | 语义 |
| --- | --- | --- |
| **1.2** | `[K,Q]=(0,o.useState)(1.2)` | ★ **对话框的间距初值**（**真正生效的默认值**） |
| **1.6** | `c=a??1.6` | ★ **add 回调的兜底值**（`crowdSpacing` 为 undefined 时才用）⟹ ⟹ 对话框**永远**传 K ⟹ ⟹ **1.6 永远不生效** |

⟹ ⟹ 「clone 的默认间距 1.2 应改成 1.6」是**错的** ⟹ ⟹ **clone 的 1.2 本来就对**。
⟹ ⟹ ★ **通则**：看到「默认值」时，要分清它是「**state 初值**」还是「**兜底常量**」；
⟹ ⟹ 只读到一个数字就说它是默认值 ⟹ ⟹ 极可能**把兜底当成了初值**。
⟹ ⟹ 本批的契约提取器因此加了一条**跨片段防呆自检**（初值 ≠ 兜底）。

---

## 1. 源站逐字依据（机器提取，**17/17 唯一命中**）

★ 提取器：`probes/extract857_contract.py` ⟹ `raw/source-857-contract.json`
★ **唯一命中 17 / 17**（命中数 ≠ 1 就记空并退出 1，不产出假 raw）
＋ **任意值类名自检通过** ＋ ★ **跨片段防呆自检通过**（初值 1.2 ≠ 兜底 1.6）。

```js
// ① 对话框 state 初值（★ 行3／列3／间距1.2 ＝ 真正生效的默认值）
[U,H]=(0,o.useState)(3),[V,G]=(0,o.useState)(3),[K,Q]=(0,o.useState)(1.2)

// ②③④ 三个输入的量程（★ 步长也逐字）
type:"number",min:1,max:10,step:1,"aria-label":D("canvas:directorRows"),value:U
type:"number",min:1,max:10,step:1,"aria-label":D("canvas:directorCols"),value:V
type:"number",min:.1,max:10,step:.1,"aria-label":D("canvas:directorSpacing"),value:K

// ⑤ 间距 onChange（★ 夹 [0.1,10] ＋ **保留 1 位小数**）
Math.min(10,Math.max(.1,Math.round(10*t)/10))

// ⑥ 「添加」按钮的载荷（count ＝ 行×列）
h({count:U*V,crowdRows:U,crowdCols:V,crowdSpacing:K}),O(null)

// ⑦ add 回调的兜底（★ **不夹取**；1.6 只是兜底、不是默认值）
let{count:t,crowdRows:r,crowdCols:n,crowdSpacing:a,...i}=e,o=t??1,s=r??1,l=n??o,c=a??1.6

// ⑧⑨ 创建 N 个成员（length ＝ count）＋ 成员类型（加的是**角色**）
u=Array.from({length:o},()=>hZ())
asset_type:o>1?"crowd"

// ⑩ rail 入口的结构特征（★ 同时也是「唯一入口」判据的结构基础）
"aria-haspopup":"dialog","aria-expanded":"crowd"===L

// ⑪⑫⑬ 文案键 ＋ 对话框 role/aria
D("canvas:directorCrowd3x3")
D("canvas:directorCrowdTotalN",{n:U*V})
role:"dialog","aria-label":D("canvas:directorAddCrowdArray")

// ⑭ ★ **开关**：对话框开着时**再点一次就是关掉它**
if("crowd"===L)return void O(null)

// ⑮ ★ **点外面关闭**：点在按钮/对话框之外 ⟹ 关闭
en.current?.contains(t)||ea.current?.contains(t)||O(null)

// ⑯ ★ **落点公式**：锚在**按钮自己**身上（right+8 / top）＋ 8px 视口安全边
W({left:Math.max(8,Math.min(t.right+8,window.innerWidth-r-8)),
   top:Math.max(8,Math.min(t.top,window.innerHeight-n-8))})

// ⑰ ★ 落点用的尺寸：对话框**自己**的宽高（量不到时兜底 220）
r=ea.current?.offsetWidth??220,n=ea.current?.offsetHeight??220
```

★ ★ **⑭⑮⑯⑰ 这四条是本批补录的** ⟹ ⟹ 因为它们是**行为**逐字（不是量程数字），
⟹ ⟹ 门禁要靠它们才能证明「clone 的开关／点外面关闭／落点」不是 clone 自己发明的。

---

## 2. 源站实测（`probes/source857_crowd.py` ⟹ `raw/source-857-crowd.json`）

| 读数 | 值 |
| --- | --- |
| 对话框几何 | **220 × 204 @(280, 388)** |
| 行数输入 | `min 1` / `max 10` / `step 1` / 初值 **3** |
| 列数输入 | `min 1` / `max 10` / `step 1` / 初值 **3** |
| 间距输入 | `min 0.1` / `max 10` / `step 0.1` / 初值 **1.2** |
| ★ 间距填 **1.55** ⟹ 读回 | **1.6**（⟹ ⟹ **行为证据**：源站保留 1 位小数） |
| ★ 全页同 `aria-label` 的元素 | **count == 1**（⟹ ⟹ 源站**只有 1 个入口**） |
| 「添加」之后 | 3D 场景里出现 **9 个人偶、3×3、**无组框**（⟹ ⟹ 源站**不建组**） |
| 撤销后重载读树 | **== 基线**（`['机位1','机位2','角色A']`，源站工程完好） |

★ ★ **「唯一入口」用的是自指判据** ⟹ ⟹ 记下对话框**自己的** `aria-label`，
再全页扫「等于它」的元素 ⟹ ⟹ **不手打任何中文**。

### 2.1 ★ 源站**没有移动端布局**（`probes/source857_mobile.py` ⟹ `raw/source-857-mobile.json`）

★ 390×844 下实测：源站渲染的**仍是桌面画布**（页面上大量元素的 x 超出 390，
⟹ ⟹ 页面比视口宽），**导演台根本没开**（`aside` 列表为空）⟹ ⟹

⟹ ⟹ ★ **源站没有移动端导演台** ⟹ ⟹ 「源站的移动端 crowd 入口」**不存在**，
⟹ ⟹ 也就**无从对齐** ⟹ ⟹ 但这**不等于**「clone 可以把移动端的能力删掉」⟹ ⟹ 见 §4。

---

## 3. clone 整改（3 个源文件）

| # | 文件 | 改了什么 | 对应源站逐字 |
| --- | --- | --- | --- |
| C1 | `DirectorIconRail.tsx` | 间距 onChange **保留 1 位小数** ＋ 夹 [0.1,10] ＋ 非数字兜底 0.1 | ⑤ |
| C2 | `DirectorIconRail.tsx` | crowd 按钮改成**开关**（再点一次关）＋ `aria-expanded` ＋ 打开态高亮 `rgba(255,255,255,.08)` | ⑩⑭ |
| C3 | `DirectorIconRail.tsx` | **点外面关闭**（document mousedown；点在按钮/对话框之外才关） | ⑮ |
| C4 | `DirectorIconRail.tsx` | 落点改**源站公式**（按钮 right+8 / 按钮 top，8px 视口安全边）⟹ ⟹ 替掉写死的「rail+294」 | ⑯⑰ |
| C5 | `directorStore.ts` | `addCrowdArray` **删掉 clone 自造的量程**（行≤6／列≤8／列再夹 `floor(24/行)`／间距 [0.6,3]）⟹ ⟹ 兜底照抄源站 | ⑦ |
| C6 | `DirectorViewport.tsx` | **删掉** legacy 视口群众面板 ＋ 加回**移动端专用**入口（桌面隐藏） | ⑩ |

★ C4 的实测（`raw/clone-857-crowd.json` 的「③落点是否符合源站公式」）：

```
期望_left ＝ 按钮 right ＋ 8 ＝ 273 ＋ 8 ＝ 281   实测_left ＝ 281   ✅
期望_top  ＝ 按钮 top        ＝ 435             实测_top  ＝ 435   ✅
```

★ ★ 顺带发现并**修掉**了一个「写了等于没写」的隐患：
★ 源站的 `W({left:…,top:…})` 里 `r`/`n` 是**对话框自己的** `offsetWidth/offsetHeight`，
⟹ ⟹ 源站是**先渲染、再按实测尺寸定位**⟹ ⟹ clone 也照做（首帧用兜底 220×220，
⟹ ⟹ 挂载后 layout effect 用**实测**尺寸再算一遍）⟹ ⟹ 视口一变就重算（resize ＋ 捕获阶段 scroll）。

---

## 4. ★ 「删掉第二个入口」这件事，差点做成一个**移动端功能缺口**

★ 本批第一版整改：把视口工具栏那枚「添加群众阵列」按钮**整个删掉**，
⟹ ⟹ 因为源站的自指判据说「只有 1 个入口」。

★ ★ 但 clone 的 **rail 在 <899px 是 `hidden`** ⟹ ⟹ 移动端**根本没有 rail** ⟹ ⟹
⟹ ⟹ ★ 那一删，**移动端就再也加不了群众阵列了**（这枚按钮原本是 clone 移动端的**唯一**入口）。

⟹ ⟹ 处置（已落地）：

- **桌面端**：可见的 crowd 入口**只有 rail 那一枚** ⟹ ⟹ 与源站一致（S9 钉住）；
- **移动端**：可见的 crowd 入口**只有视口底部工具条那一枚** ⟹ ⟹ 开的是**同一个**对话框
  （量程／默认值／落点规则与桌面**完全同源**）；
- ★ 判据要**分断点**取证（S9 桌面 / S10 移动端）⟹ ⟹ 不能笼统说「一个入口」。

---

## 5. 判据（`scripts/verify-liblib-batch857.py`，**12/12**）

| 判据 | 读什么 | 阴性 |
| --- | --- | --- |
| S1 | 契约：**17 个片段唯一命中** ＋ 5 条关键逐字 ＋ 两项自检 | N1 |
| S2 | 源站实测：对话框 **220×204 @(280,388)** ＋ 三个输入的量程/初值 | — |
| S3 | 源站**行为**：间距填 1.55 ⟹ **读回 1.6** | N2 |
| S4 | 源站**唯一入口**（自指判据 count == 1） | N3 |
| S5 | 源站逐字：开关 ＋ 点外面关闭 ＋ aria-expanded | — |
| S6 | clone 实测：落点 **＝ 按钮 right+8 / 按钮 top** | N4 |
| S7 | clone **行为**：间距填 1.55 ⟹ **读回 1.6**（与 S3 同口径） | N5 |
| S8 | clone 实测：再点一次关 ＋ 点外面关 | N6 |
| S9 | clone 实测：**桌面可见入口 == 1** | N7 |
| S10 | clone 实测：**移动端可见入口 == 1** ＋ 开的是同一个对话框 ＋ **那枚也是开关** | N8／N9 |
| S11 | clone 源码：legacy 清零 ＋ 1 位小数 ＋ store 不夹取 | N9／N10／N11 |
| S12 | 老门禁迁移：`45.py` ＋ `625.py` | N12／N13 |

★ ★ **S3/S7 是「源站 ↔ clone」的行为交叉**：只断言 clone 是 1.6 ⟹ ⟹ 那可能只是「探针瞎了」⟹ ⟹
★ 所以必须**同时**断言「**同一个动作**在源站上读回 1.6」（S3）与「在 clone 上读回 1.6」（S7）。

---

## 6. 阴性对照（`probes/neg857.py`，**14 条 ＋ 复原自检 ＝ 15/15**）

| 阴性 | 变异 | 应当翻红 |
| --- | --- | --- |
| N1 | 契约：「间距 onChange」逐字被改 | S1 |
| N2 | 源站读数：间距读回 1.55 | S3 |
| N3 | 源站读数：同 aria 元素 count ＝ 2 | S4 |
| N4 | clone 读数：落点不等于按钮 right+8 | S6 |
| N5 | clone 读数：间距读回 1.55 | S7 |
| N6 | clone 读数：再点一次后对话框仍可见 | S8 |
| N7 | clone 读数：桌面可见入口 ＝ 2 | S9 |
| N8 | clone 读数：移动端可见入口 ＝ 2 | S10 |
| N9 | clone 读数：移动端**再点一次**后对话框仍可见（那枚不是开关） | S10 |
| N10 | clone 源码：间距不再保留 1 位小数 | S11 |
| N11 | clone 源码：视口加回 legacy 选择器 | S11 |
| N12 | clone 源码：store 加回 `Math.min(` 夹取 | S11 |
| N13 | clone 源码：落点改回写死偏移 | ★ **老门禁 `625.py` 直接跑会红** |
| N14 | clone 源码：**去掉开关** | ★ **重跑 clone 探针 ⟹ S8 红** |

★ ★ **N13 与 N14 是本批最要紧的两条**：

- **N13**：本批**迁移过** 625 门禁里「crowd-dialog 落点」那条判据
  （旧的写死坐标 `[294,52,220,208]` ⟹ 改成「按源站公式 ＋ 实测锚点」推导）
  ⟹ ⟹ 光跑本批门禁证明不了「迁移后的判据还有牙」⟹ ⟹ 必须**直接跑 625**
  ⟹ ⟹ 实测：`625 退出码 1`、输出 `FAILED: the-portal-moved-nothing` ✅
- **N14**：S7/S8 读的是**探针跑出来的 JSON** ⟹ ⟹ 只变异 JSON 只能证明
  「判据读的是它声称的那个字段」⟹ ⟹ 要证明「探针真能测出行为不对」，
  必须**改源码 → 重跑探针 → 门禁红** ⟹ ⟹ 实测：探针退出码 0、翻红判据**恰好 [S8]** ✅

★ ★★ 另外，本批在**自查里抓到一个真缺陷**（不是判据问题）：
★ 移动端那枚按钮**一度不是开关** —— mousedown 先按「点外面」把对话框关了、
click 又把它打开 ⟹ ⟹ 净效果「一直开着」⟹ ⟹ **与源站语义不一致**。
⟹ ⟹ 修法：outside-mousedown 的判据要**把两个入口都算成「入口自己」**
（`closest("[data-director-character-option='crowd-3x3'], [data-director-crowd-mobile-trigger]")`），
⟹ ⟹ 再由 click 走统一的开关逻辑 ⟹ ⟹ 并把这条行为**写进 S10 ＋ N9**。

★ 全部复原后 **6 个文件字节级回到原样** ✅（即第 15 条：复原自检）

---

## 7. 回归 ＋ 受控对照 ＋ 构建链

### 7.1 回归（`probes/regress857.py`，**92 条**，比 856 扩了 14 条 crowd 相关）

| 类别 | 条数 | 结论 |
| --- | --- | --- |
| **绿** | 78 | — |
| **红 ＝ 已知旧账** | 9 | `831`／`835`／`741`／`91`／`736`／`748`／`749`／`782` ＋ `45`（★ 迁移后已修好，见 §7.3） |
| **红 ＝ 新发现、逐条归因** | 5 | `541`／`546`／`542`／`738`／`656` ⟹ ⟹ **逐条定点对照**（HEAD 上**同样红** ⟹ ⟹ 不是本批引入） |

★ ★ **「扩大回归清单后新出现的红必须定点对照归因」** —— 这 5 条的归因：

| 门禁 | 红在哪 | 归因 | 证据 |
| --- | --- | --- | --- |
| `541.py` | `crowd:objects-increase` | ★ **老前提**：它的前提是「点『群众 (3x3)』**直接加**人群」⟹ ⟹ 但 **batch 590 起**（源站逐字）那一枚是**打开对话框** ⟹ ⟹ 老前提早于本批 | 源站逐字 ＋ 590 的门禁 |
| `546.py`／`542.py` | `FileChooser.set_files: ENOENT … /private/tmp/batch542-fixture/hero-character.fbx` | ★ **环境缺件**（那个 fixture 目录**不存在**）⟹ ⟹ 与源码无关 | `ls /private/tmp/batch542-fixture/` ⟹ No such file or directory |
| `738.py` | C7「根外 button 轨迹 47 → 52 → 55」⟹ 实测 **49 → 54 → 57** | ★ **写死的个数过期**（那个差值 ＝ 某个更早批次的按钮增减）⟹ ⟹ **本批没动它** | ★ **同一探针在 HEAD 态实测**：根外 button 同样是 **38 / 49 / 54** ⟹ ⟹ 与本批无关 |
| `656.py` | `the-scene-prediction-was-wrong-and-scene-is-a-dom-level-no-op` | 「场景面板」的**预测被证伪** ⟹ ⟹ 本批**没改**「场景」入口 | 本批只改了 crowd 那一路 |

### 7.2 受控对照（`probes/attrib857.py`）

★ 做法：把本批改过的 **3 个源文件按字节换回 HEAD** ⟹ ⟹ 重跑门禁 ⟹ ⟹
★ 读数**逐条有没有变**（**每条连跑两遍** ⟹ ⟹「一轮的差」不能当因果）⟹ ⟹
★ 复原走**字节备份**（不是 `git checkout`）⟹ ⟹ 复原后逐字节校验哈希
⟹ ⟹ ★ **绝不用 `git stash`**（本仓库的 `stash@{0}` 是别人的 WIP ⟹ ⟹ 全程不碰）。

★ **读数完全相同（10 条）**：`541`／`546`／`542`／`738`／`656`
（⟹ ⟹ **证明这 5 条红不是本批引入**）＋ `590`／`626`／`613`／`84.mjs`／`86.mjs`。
★ **预期差异（3 条，恰恰是「判据有牙」的证据）**：

| 门禁 | HEAD 上的读数 | 为什么这是**预期**差异 |
| --- | --- | --- |
| `857.py` | rc=1，**11/12** | 本批门禁在 HEAD 上必然红（HEAD 的源码里没有本批的改动）⟹ ⟹ 门禁真的在读本批源码 |
| `625.py` | rc=1，**5/6**，`FAILED: the-portal-moved-nothing` | ★ 迁移后的落点判据在 HEAD 上必然红（HEAD 的对话框落点是**写死**的「rail+294」）⟹ ⟹ **正是**「迁移后的判据有牙」的证据 |
| `45.py` | rc=1，`AssertionError: 视口里还有 legacy 群众阵列选择器：data-director-crowd-trigger` | ★ 迁移后 45.py 加了 legacy 选择器的**负向断言** ⟹ ⟹ HEAD 的视口里**确实还有**那个选择器 ⟹ ⟹ 同样是有牙的证据 |

★ **受控对照总结：10/13 条读数逐条完全相同**，3 条差异全是预期内的
（`raw/attrib-857.json`）。
★ 复原后 **3 个源文件哈希逐个校验一致**（`e28811ea…`／`486126ac…`／`5b6c9e69…`）。

### 7.3 两条老门禁的「旧前提」整改（本批撞上的）

| 门禁 | 旧前提 | 改成 |
| --- | --- | --- |
| `45.py` | crowd 段走 **legacy 视口面板**（`data-director-crowd-panel`） | 迁到 **rail 的对话框** ＋ 补「**点 rail 的「场景」关掉浮层**」那一步（否则点组行 toggle 会被浮层截走）＋ ★ **移动端段改走移动端那枚入口**（clone 的 rail 在 <899px 是 `hidden` ⟹ ⟹ 点 rail 会超时）＋ 补 legacy 选择器的**负向断言**（只写正向的话「旧写法还在」也能过） |
| `625.py` | crowd-dialog 落点**写死** `[294, 52, 220, 208]` | 改成「**按源站公式 ＋ 实测锚点**」推导（源站的 `W({left:…t.right+8…,top:…t.top…})`）＋ 另立一条「宽度 220」的断言 |

★ ★ **「写死的个数」是老门禁「旧前提」的通用形状** ⟹ ⟹ 本批又撞上 2 条
（856 那批撞上 4 条：87.mjs／84.mjs／86.mjs／852.py）。

### 7.4 构建链

| 命令 | 结果 |
| --- | --- |
| `npx tsc --noEmit` | ✔ |
| `npx eslint`（本批 3 个源文件） | ✔ |
| `npx next build` | ✔ |
| `npm run assertions:check` | ✔ **803 个脚本、0 个空洞断言** |
| `npm run docs:check` | exit=1 ⟹ ★ 断链**全部**在 `docs/user-manual/`（**他人并发编辑区**）⟹ ⟹ **本批目录 0 处断链** |

## 8. ★ 登记的差异（**如实登记，不假装已修**）

| # | 差异 | 证据 | 处置 |
| --- | --- | --- | --- |
| **D1** | ★ **clone 的「添加角色」是浮层，源站是左侧面板模式切换** | clone 浮层 x=**48..280** ⟹ ⟹ 与场景树 x=48..280 **完全重叠** ⟹ ⟹ 浮层里的 `[data-director-character-option]` **截走**落在组行上的点击（命中测试：`BUTTON[option=standard-female]`）⟹ ⟹ 场景树**看着能点、其实点不动**；源站逐字：`"scene"===z?n:null,"character"===z?(…添加角色…)` ⟹ ⟹ 两者**互斥** | **batch 858 整改**（面板化）。★ 已算好预期：面板化后「群众 (3x3)」按钮 ＝ **(56, 388, 216×32)** ⟹ ⟹ 对话框 ＝ **(280, 388)** ⟹ ⟹ **与源站逐字命中** |
| **D2** | clone 的对话框高 **208**，源站 **204** | `raw/clone-857-crowd.json` vs `raw/source-857-crowd.json` | 登记（4px 观感差） |
| **D3** | clone 的对话框落点 left ＝ **281**，源站 **280** | 差 1px：clone 浮层卡片内边距 `p-1.5` vs 源站面板 `px-2` | 随 D1 一并解决（858） |
| **D4** | clone 把 crowd 成员**自动包成一个组**，源站**不建组** | 源站实测：3×3 之后 3D 场景里 9 个人偶、**无组框**；源站 add 回调只创建角色、从不碰 `characterGroups` | 登记（影响 **7** 个文件：工程 schema／runtime adapter／clipboard／整工程复制／Inspector ⟹ ⟹ 本批**只登记、不改**） |
| **D5** | clone 有**移动端专用**的 crowd 入口 | §2.1：源站**没有移动端布局** | 登记为 **clone 自己的扩展**（不冒充源站行为） |

★ ★ D1 是本批**顺手挖出来的「糊弄」点** ⟹ ⟹ 用户明确要求「发现糊弄之处必须整改」
⟹ ⟹ 整改在 **batch 858**（面板化）⟹ ⟹ 本批**不假装已修**。

---

## 9. ★ 用户可达（用户硬要求：**从根可达 ＋ 写清怎么测**）

★ 复刻站的根地址：**`http://localhost:4317/`**（**无参数**即可打开）。

### 9.1 桌面端：从根走到「群众阵列」对话框

1. 浏览器打开 `http://localhost:4317/`（根目录，无参数）
2. 在画布上找到标题为「**第一集：咖啡馆对峙**」的那张 **导演台卡片**
   （节点类名 `.react-flow__node-script-execution`）
3. ★ **鼠标悬停**在它上面 ⟹ 卡片里出现「**打开导演台 →**」按钮 ⟹ 点它
   （按钮默认透明，悬停才显形，与源站一致）⟹ ⟹ 导演台盖在画布上（等约 6.5 秒）
4. 点**左侧图标栏**（rail，宽 48px）的「**添加角色**」按钮
   （`[data-director-rail-entry='add-character']`，实测 @(8,116) 32×32）
   ⟹ ⟹ 浮层列出 **11 项**（本地上传 ＋ 8 个体型 ＋ **群众 (3x3)** ＋ 几何模型）
5. 点「**群众 (3x3)**」（`[data-director-character-option='crowd-3x3']`）
   ⟹ ⟹ **对话框**出现在按钮**右侧**（源站规则：按钮 right+8）
   ⟹ ⟹ 桌面实测 **220×208 @(281,435)**（源站是 220×204 @(280,388) ⟹ 差 D2/D3）
6. 对话框里改**行数／列数／间距**（量程与源站逐字一致：1–10／1–10／0.1–10）
   ⟹ ⟹ ★ 想验证「保留 1 位小数」：把**间距**填成 `1.55` ⟹ ⟹ 它会读回 **`1.6`**
7. 点「**添加**」⟹ ⟹ 场景树里多出一个**组行**（`群众 (3x3)`）
   ⟹ ⟹ 成员数 ＝ 行×列（成员**默认展开**）
8. ★ **回到场景树**：点 rail 的「**场景**」（`[data-director-rail-entry='scene']`）
   ⟹ ⟹ 浮层关闭、左侧仍是场景树

★ ★ **两个交互可以顺手验证**（都是本批新补的源站行为）：

- ★ **再点一次「群众 (3x3)」⟹ 对话框关闭**（源站：`if("crowd"===L)return void O(null)`）
- ★ **点对话框外面 ⟹ 对话框关闭**（源站：mousedown 落在按钮/对话框之外 ⟹ 关）
  ⟹ ⟹ ⚠️ 顺便说：源站的「添加角色」是**左侧面板模式切换**，
  ⟹ ⟹ 源站在这个模式下**场景树是不在的**；clone 是浮层 ⟹ ⟹ **两者同时可见**
  ⟹ ⟹ 所以 clone 里**浮层盖住的那块场景树点不动**（这是 D1，batch 858 整改）

### 9.2 移动端（390×844）：入口在视口底部工具条

★ clone 的 rail 在 **<899px 是 `hidden`** ⟹ ⟹ 移动端走**另一枚**入口：
⟹ ⟹ 视口底部工具条里的「**添加群众阵列**」按钮
（`[data-director-crowd-mobile-trigger]`，实测 @(219,628) 32×32）
⟹ ⟹ 它开的是**同一个**对话框（量程／默认值／落点规则与桌面**完全同源**）
⟹ ⟹ 桌面端这枚按钮**不出现** ⟹ ⟹ 所以桌面可见入口仍然**只有 1 枚**。

### 9.3 怎么写探针自己测（三个选择器就够）

```python
page.locator("[data-director-rail-entry='add-character']").click()   # 打开浮层
page.locator("[data-director-character-option='crowd-3x3']").click() # 打开对话框
page.locator("[data-director-crowd-input='spacing']").fill("1.55")    # 应当读回 1.6
page.locator("[data-director-crowd-confirm]").click()                 # 添加
```

★ 探针纪律（沿用仓库既有约定）：
① 4317 的探针**先移除 `nextjs-portal`**（Next.js 的 dev 浮层会挡住读数）；
② 探针一律 `headless=True`；③ **4317 多人共用 ⟹ 不要并发**跑多个浏览器脚本。

### 9.4 ★ batch 856（组）的可达性：**本批补上**

★ 856 的 README 里**没有**「用户可达」章节 ⟹ ⟹ 那是用户硬要求的一个缺口
⟹ ⟹ **本批补齐**（不改 856 已提交的审计文档，只在这里标注）：

| 想测什么 | 怎么点 | 看什么 |
| --- | --- | --- |
| 打组 | 树上多选 ⟹ 点「**打组**」（或 `⌘G`） | 多出一个**组行**，成员缩进在组标题**右侧 16px** |
| 解组 | 选中组 ⟹ 点「**解组**」（或 `⌘⇧D`） | 组行消失、成员回到原来的分区 |
| ★ 组的**移动路径** | 选中组 ⟹ 时间轴上建**组轨道** ⟹ 加关键帧 ⟹ 拖时间 | 成员**随轨道一起走**（★ 源站**没有**组 gizmo ⟹ ⟹ 轨道是组唯一的移动路径） |
| ★ 组的**检查器** | 选中组 ⟹ 看右侧检查器 | ★ **只有「名称」一个字段**（源站逐字：组对象**没有** transform） |

★ 中心文档：`docs/research/LIBTV_CLONE_REACHABILITY.md`（§2.1 已补本批两行 ＋ §5 证据索引）。

---

## 10. 复现步骤（一条链）

```bash
export PATH="$HOME/.nvm/versions/node/v24.6.0/bin:$PATH"   # node
export PATH="$HOME/.pyenv/shims:$PATH"                      # playwright / PIL
cd /Users/yangjiefeng/Documents/wubuku/liblib-tv

# ① 源站逐字契约（17/17 ＋ 两项自检）
python3 docs/research/liblib-canvas-batch857-2026-10-01/probes/extract857_contract.py

# ② 源站实测（★ 有副作用：会真的加一组群众 ⟹ 脚本末尾撤销复原）
python3 docs/research/liblib-canvas-batch857-2026-10-01/probes/source857_crowd.py
# ②b 源站**没有移动端布局**的实测
python3 docs/research/liblib-canvas-batch857-2026-10-01/probes/source857_mobile.py

# ③ clone 实测（桌面 ＋ 移动端）
python3 docs/research/liblib-canvas-batch857-2026-10-01/probes/clone857_crowd.py
# ③b clone 几何探针（浮层 vs 场景树的重叠与命中测试）
python3 docs/research/liblib-canvas-batch857-2026-10-01/probes/clone857_geometry.py

# ④ 门禁（12/12）
python3 scripts/verify-liblib-batch857.py

# ⑤ 阴性（14/14）⟹ ★ 会**改源码**做变异 ⟹ ⟹ 跑完必须确认文件已复原
python3 docs/research/liblib-canvas-batch857-2026-10-01/probes/neg857.py

# ⑥ 回归（92 条既有门禁）
python3 docs/research/liblib-canvas-batch857-2026-10-01/probes/regress857.py
```

★ **产物**：

```
raw/source-857-contract.json    ← 源站逐字 17 片段 ＋ 两项自检
raw/source-857-crowd.json       ← 源站实测（几何／量程／1 位小数／唯一入口）
raw/source-857-mobile.json      ← 源站在 390px 的实测（无移动端布局）
raw/clone-857-crowd.json        ← clone 实测（落点／行为／两断点的入口数）
raw/clone-857-geometry.json     ← clone 浮层 vs 场景树的重叠与命中测试
runtime-audit.json              ← 门禁 12 条的逐条结果
negative-audit.json             ← 阴性 14 条的逐条结果
images/857src_*.png             ← 源站截图
images/857clone_*.png           ← clone 截图
```
