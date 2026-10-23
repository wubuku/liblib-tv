# Batch 853 — 导演台「打组／解组快捷键」（⌘G／⌘⇧G／⌘⇧D）

> 本批是导演台**快捷键面板右列最后两条没实现的**（面板共 12 条：
> 左列 T／H／V／R／F／WASDQE，右列 Y／X／**打组 ⌘G**／**解组 ⌘⇧D**／撤销 ⌘Z／删除 ⌫）。
> 前两批（851／852）做完了视图类与变换类，本批做**打组／解组**。
>
> ★ 本批只做**快捷键接线** ＋ **源站／clone 取证** ＋ **如实登记差异**；
> ★ 「clone 的组只收角色、源站收任意场景成员（含机位）」属于**组模型**问题，
> ⟹ ⟹ 留给独立批次（见 §6 D1）。

---

## 1. 本批靶子与背景

**靶子**：导演台快捷键面板里的「打组 ⌘G」与「解组 ⌘⇧D」两条。

**为什么单独一批**：这两条与 851／852 的四条不同——它们**会改工程数据**（建组／解组），
不是只改一个瞬时状态。建组是**有副作用**的操作 ⟹ ⟹ 源站实测必须自己复原。

**clone 侧现状（本批之前）**：

- store 里**已经有** `groupSelectedCharacters` 与 `ungroupSelectedCharacters` 两个 action
- `DirectorObjectTree.tsx` 里**已经有**「打组／解组」两枚按钮（`data-director-group-action="group"`／`"ungroup"`）
- ⟹ ⟹ **缺的只是「快捷键 → action」这一段接线**

**所以本批的改动面很小**：一个新纯函数文件 ＋ `DirectorDesk.tsx` 里一个分支。
真正的工程量在**取证**：源站的行为矩阵必须**逐字**读出来，而不是照面板文案猜。

---

## 2. 契约提取（机器提取，**16 个片段全部唯一命中**）

提取器：`probes/extract853_contract.py` ⟹ `raw/source-853-contract.json`
（源站 chunk `/tmp/liblib_srcjs2/0fmehki05gkzw.js.js`，1,018,130 字节）。

### 2.1 提取纪律（沿用 852）

1. 每个锚点**必须恰好命中 1 次** ⟹ 否则记 `命中数` 并置空（不许静默取第一条）。
2. 片段**逐字**复制，记录**字节偏移**。
3. 片段里不许出现**截断**的 Tailwind 任意值类名（缺右方括号的形式）——★ v4 会扫到文档与探针里。

### 2.2 关键片段（逐字）

```js
// 键位白名单（★ g 与 d 都在里面）
hY=new Set(["escape","enter","v","r","f","h","x","t","y","c","d","g","delete","backspace","z"])

// 修饰键条件（★ hY 块里的 && 链）
&&("g"!==n||e.ctrlKey||e.metaKey)&&("d"!==n||e.shiftKey&&(e.ctrlKey||e.metaKey))

// 分支体
else if("g"===n||"d"===n)if(e.shiftKey){
  let e=nf.current.selectedGroupId;e&&rY(e)}else"g"===n&&rW()

// 可分组的类别（★ 含机位）
function sg(e){return"character"===e||"prop"===e||"emptyObject"===e||"camera"===e}

// 组名
function lT(e){return`${(0,tS.V)("canvas:nodeTypeGroup")}${e.length+1}`}

// 右键菜单的 canGroup 判定式
X(e,s,!l&&s.length>1&&s.every(e=>sg(e.category)),l?.id)

// 树行的 onClick（★ ⇧／⌘／Ctrl 三者之一 = additive，且只对 sg 类别）
onClick:t=>{if("motionPath"===e.category)return void s?.(e.id);
  let r=t.shiftKey||t.metaKey||t.ctrlKey;
  a(e.id,e.category,sg(e.category)?{additive:r,individual:!0}:void 0)}

// reducer：建组（★ 成员不足两个 ⟹ 直接 return，什么都不做）
case"CREATE_CHARACTER_GROUP":{let r=lB(...);if(r.length<2)return e;
  let n=U({characterIds:[],members:r}),a={id:lM(),label:lT(e.characterGroups),characterIds:n,members:r};
  return{...e,characterGroups:[...e.characterGroups,a],...lQ(r),selectedGroupId:a.id}}

// reducer：解组（★ 删组 ＋ 解绑相机与 groupTracks ＋ selectedGroupId=null ＋ 重选原成员）
case"UNGROUP_CHARACTER_GROUP":{...selectedGroupId:null}}

// 快捷键面板右列（★ 打组 ⌘G ／ 解组 ⌘⇧D）
{label:e("canvas:directorShortcutGroup"),keys:[{id:"group-command",icon:"command"},{id:"group-key",label:"G"}]},
{label:e("canvas:directorShortcutUngroup"),keys:[{id:"ungroup-command",icon:"command"},{id:"ungroup-shift",label:"⇧"},{id:"ungroup-key",label:"D"}]}
```

### 2.3 ★★ 本批新增：**行为矩阵由提取串推导**，不是手打

★ 上面那两段（修饰键条件 ＋ 分支体）是**从 chunk 里逐字取出来的**。
★ `extract853_contract.py` 里有一个**通用的小解释器**：输入 ＝ 那两段**提取出来的字符串**，
★ 输出 ＝ 16 种组合（2 个字母 × Ctrl × Cmd × Shift）各自的动作。
⟹ ⟹ **矩阵是算出来的，不是人写上去的。**

推出来的表（`raw/source-853-contract.json` 的 `★行为矩阵（由提取串推导）`）：

| 按键 | 动作 | 依据 |
| --- | --- | --- |
| `⌘G` | **打组** | `g` 段要求 ctrl∥meta ✔ ＋ 无 ⇧ ⟹ `"g"===n&&rW()` |
| `⌘⇧G` | **解组** | `g` 段只要求 ctrl∥meta（⇧ 不 disqualify）＋ 分支体 ⇧ 优先 ⟹ `rY(e)` |
| `⌘⇧D` | **解组** | `d` 段要求 ⇧ ＋ ctrl∥meta ✔ ＋ ⇧ 分支 ⟹ `rY(e)` |
| `⌘D` | **无** | `d` 段要求 ⇧ ⟹ 门禁不放行 |
| 裸 `G`／裸 `D`／裸 `⇧D` | **无** | `g`／`d` 都要 ⌘ |

★ **⌘⇧G 是源站的行为，但源站面板没列它**（面板只印 ⌘G／⌘⇧D）⟹ ⟹ 这是个
「**实现里有、面板里没有**」的别名。clone 同样实现它、面板同样不列 ⟹ ⟹ 行为一致。

### 2.4 ★★ 本批真踩到的坑：`&&` 拆分被括号打断 ＋ 去掉括号会改掉优先级

★ 写完提取器第一次跑 ⟹ ⟹ 报「无法解析 gate 片段」。

**根因一**：`str.split("&&")` 把条件切成了三段——因为**第二个 `&&` 在括号内**：

```
&&("g"!==n||e.ctrlKey||e.metaKey)&&("d"!==n||e.shiftKey&&(e.ctrlKey||e.metaKey))
                 ↑ 顶层 &&                        ↑ 括号内的 &&（不能在这里切）
```

⟹ ⟹ 修法：写一个**按括号深度切分**的 `split_top_level()`。

**根因二（更要命）**：最初想「把括号去掉再按 `&&`/`||` 拆」——**这是错的**：

```
e.shiftKey&&(e.ctrlKey||e.metaKey)     ⟹  shift AND (ctrl OR meta)
去掉括号 ⟹ e.shiftKey&&e.ctrlKey||e.metaKey  ⟹  (shift AND ctrl) OR meta   ★ 优先级被改掉！
```

⟹ ⟹ 两种组合在 `ctrl=False, meta=True, shift=True` 时结论**相反**。
⟹ ⟹ 修法：改成**递归下降**的布尔解析器（`||` 低于 `&&`、括号单独一层）。

★ 同一个坑在**门禁里又踩了一次**——所以门禁用**另一条路**（把 minified 条件**翻译成
Python 再 `eval`**）重算一遍 ⟹ ⟹ 两套独立实现必须给出同一张表（门禁 S3）。

★ ★ 还有一个小坑：源站 chunk 里 `rW()` 后面**没有分号**（压缩代码在 `}` 前省略末尾分号）
⟹ ⟹ 正则写成 `rW\(\);` 就匹配不上。

---

## 3. 源站实测（`probes/source853_groupkeys.py` ⟹ `raw/source-853-groupkeys.json`）

### 3.1 读数设计

★ 源站的组是**树上的一个条目**（带 lucide `Group` 图标 ＋ 自己的 label）
⟹ ⟹ 「组出现了」＝ **树里多了一行**；「组消失了」＝ **树里少了一行**。
★ 行的定位用**结构**（label span 的 class 含 `truncate pl-1` ＋ x<300），
★ **不手打中文条目名**（机位1／机位2／角色A 都是读出来的）。

### 3.2 ★ 为什么用「机位1 + 机位2」而不是两个角色

★ 源站这个工程里**只有一个角色** ⟹ ⟹ 想触发建组只能用**两个机位**
⟹ ⟹ ★★ **顺带证明了一件事**：源站的组**可以装机位**
（`sg(e)` 里 `"camera"===e`），而 clone 的 `groupSelectedCharacters` **只收角色**
⟹ ⟹ 这是**功能差异**（不是快捷键差异）⟹ ⟹ 登记为 D1。

### 3.3 读数结果

| 步骤 | 树里的行 | 结论 |
| --- | --- | --- |
| 基线 | 机位1／机位2／角色A（3 行） | — |
| 只选 1 个，按 ⌘G | 不变（Δ=0） | ★ reducer 逐字 `r.length<2 ⟹ return e` |
| ⌘+点击加选第 2 个，按 ⌘G | **多 1 行**（Δ=+1），新行标签是 `分组1`，**成员 x 各自 +16**（缩进） | 建组成功，且是**父子结构** |
| 按 ⌘D | 不变 | `d` 要求 ⇧ ＋ ⌘ |
| 按 ⌘⇧D | **回到基线**（逐字相等） | 解组 |
| 探针结束时 | 仍等于基线 | ★ 已复原（源站建组会存进用户工程） |

★ 组行带的是**另一枚图标指纹**（lucide `Group`），与基线三行的图标都不同；
★ 成组后**只有那两行成员被缩进**（`角色A` 的 x 没变）⟹ ⟹ 组是父子结构，不是"平铺多一行"。

截图：`images/853src_baseline.png`（基线）、`images/853src_single-group.png`（单选 ⌘G 无变化）、
`images/853src_two-selected.png`（选中两行）、`images/853src_after-group.png`（★ **建组后**，
成员缩进可见）、`images/853src_after-ungroup.png`（解组后）、`images/853src_final.png`（复原）。

---

## 4. clone 实施

### 4.1 改动清单

| 文件 | 改动 |
| --- | --- |
| `src/components/director/directorShortcutRules.ts` | **新增**：纯函数 `resolveDirectorGroupShortcutAction` ＋ 类型 |
| `src/components/director/DirectorDesk.tsx` | 绑定两个 action ＋ 在 ⌘Y 分支后插入 g／d 分支 ＋ 依赖数组补三项 |

### 4.2 判定抽成纯函数（为了门禁能**实跑**那张动作表）

```ts
export function resolveDirectorGroupShortcutAction(
  input: DirectorGroupShortcutInput,
): DirectorGroupShortcutAction | null {
  const { key, modifier, shift } = input;
  if (!modifier) return null;
  if (key === "g") return shift ? "ungroup" : "group";
  if (key === "d") return shift ? "ungroup" : null;
  return null;
}
```

★ 逐条对应源站那两段：

| 纯函数这一行 | 对应源站哪一句 |
| --- | --- |
| `if (!modifier) return null;` | `("g"!==n\|\|e.ctrlKey\|\|e.metaKey)` 与 `("d"!==n\|\|e.shiftKey&&(e.ctrlKey\|\|e.metaKey))` 里**共同**要求的 ⌘ |
| `if (key === "g") return shift ? "ungroup" : "group";` | 分支体 `if(e.shiftKey){…rY(e)}else"g"===n&&rW()` |
| `if (key === "d") return shift ? "ungroup" : null;` | `d` 段要求 ⇧ ＋ ⌘；且不带 ⇧ 时分支体里 `d` 落不到 `rW()` |

★ 本模块**只回答「这个按键组合该做什么」**，**不做任何状态判断**：
「够不够两个成员」「有没有选中组」是**运行时**的判据，由 store 那两个 action 自己把关
（源站的 `r.length<2` 与 `e&&rY(e)` 同理）。

### 4.3 clone 实测（`probes/clone853.py` ⟹ `raw/clone-853-groupkeys.json`）

★ ★ clone 侧要触发 ⌘G **必须先凑够两个角色**：clone 的 `groupSelectedCharacters`
**只收角色**，而 clone 默认场景**只有 1 个角色** ⟹ ⟹ ⌘G 在默认场景里是**死键**。
★ clone 里唯一能真造角色的入口是**「添加群众阵列」**（`1×2` ⟹ 2 个角色 ＋ 1 个已存在的组）
⟹ ⟹ 用它既造出成员，也顺带得到一个**已存在的组**用来测解组。

★ 探针全程走**真实 UI**：点 rail 的「添加角色」⟹ 群众 ⟹ 弹窗填 1×2 ⟹ 添加；
★ 再点树上的角色行（点第一个 ＋ ⇧ 点第二个）⟹ ⟹ 最后**真按键盘**。

| 按键 | 期望（来自契约矩阵） | 实测 | 读数 |
| --- | --- | --- | --- |
| `⌘D` | 无 | 无 | DOM 组数 1→1、`store选中组` 不变，**逐字段相同** |
| `⌘⇧D` | 解组 | 解组 | DOM 组数 1→0、`store选中组` → null、最后命令 `DELETE_GROUP/COMMITTED` |
| `⌘G` | 打组 | 打组 | DOM 组数 0→1、`store选中组` 指向新组、最后命令 `GROUP_CHARACTERS/COMMITTED` |
| 裸 `G` | 无 | 无 | **逐字段相同** |
| 裸 `D` | 无 | 无 | **逐字段相同** |
| `⌘⇧G` | 解组 | 解组 | DOM 组数 1→0、最后命令 `DELETE_GROUP` |

★ 六条**全部与契约矩阵一致**（期望值不是手打的，是从 `raw/source-853-contract.json`
的矩阵表里取的）。

截图：`images/853clone_01-baseline.png`、`images/853clone_02-crowd.png`（1×2 群众 ＋ 组）、
`images/853clone_05-two-selected.png`（两个角色已选，「打组」按钮解禁）、
`images/853clone_07-cmd-g.png`（⌘G 之后）、`images/853clone_08-bare-g.png`、
`images/853clone_09-bare-d.png`、`images/853clone_10-cmd-shift-g.png`。

---

## 5. 验收

### 5.1 门禁 `scripts/verify-liblib-batch853.py` — **11/11**

| 判据 | 读什么 | 阴性 |
| --- | --- | --- |
| S1 | clone 源码里的**结构**（纯函数／接线／依赖数组） | N2 |
| S2 | 契约里**除两段 keydown 原文之外**的片段（16 个唯一命中 ＋ 8 条逐字） | N8 |
| S3 | 契约里的**修饰键条件 ＋ 分支体 ＋ 矩阵**（门禁**自己重算**一遍） | N9 |
| S4 | clone 纯函数 `resolveDirectorGroupShortcutAction` 的**运行时**（node 实跑 16 格） | N1／N3 |
| S5 | clone 读数 `③⌘D`（无变化） | N4 |
| S6 | clone 读数 `④⌘⇧D`（解组） | N5 |
| S7 | clone 读数 `⑦⌘G`（打组） | N6 |
| S8 | clone 读数 `⑧裸G`／`⑨裸D`（无变化） | N7 |
| S9 | clone 读数 `⑩⌘⇧G`（解组） | N10 |
| S10 | **源站**读数（建组／缩进／⌘D 无／解组回基线／复原） | N11 |
| S11 | clone 快捷键面板的两行 ＋ 源站面板片段 | N12 |

★ ★ **S3 是「第二套独立实现」**：提取器走**递归下降**解析器，
门禁走**「翻译成 Python 再 `eval`」** ⟹ ⟹ 两条路线必须给出同一张 16 格表。
⟹ ⟹ 这不是自证，是交叉验证。

★ ★ **S11 的期望值也不手打**：「打组」那行的字母是从**分支体原文**里推出来的
（`else"g"===n&&rW()` ⟹ 那个 `g`），再拿它跟源站面板片段逐字比。

### 5.2 阴性对照 `probes/neg853.py` — **12/12**，每条**恰好**翻一条判据

| 阴性 | 变异的对象 | 翻红的判据 |
| --- | --- | --- |
| N1 | 源码 rules：`if (!modifier) return null` ⟹ `if (modifier) return null` | S4 |
| N2 | 源码 desk：`else ungroupSelectedCharacters()` ⟹ `else groupSelectedCharacters()` | S1 |
| N3 | 源码 rules：`d` 的返回值改成恒为 `"ungroup"`（⟹ ⌘D 也解组） | S4 |
| N4 | clone 读数：`③⌘D` 的「按后.DOM组数」（假装它解了组） | S5 |
| N5 | clone 读数：`④⌘⇧D` 的「按后.store选中组」（假装没清空） | S6 |
| N6 | clone 读数：`⑦⌘G` 的「按后.DOM组数」（假装没建组） | S7 |
| N7 | clone 读数：`⑧裸G` 的「按后.DOM组数」 | S8 |
| N8 | 契约：`sg` 片段里去掉 `\|\|"camera"===e`（⟹ 源站不许装机位） | S2 |
| N9 | 契约：修饰键条件里 `d` 段去掉 `\|\|e.metaKey`（⟹ 矩阵变了） | S3 |
| N10 | clone 读数：`⑩⌘⇧G` 的「按后.DOM组数」 | S9 |
| N11 | 源站读数：`③行数变化`（⟹ 假装源站 ⌘G 没建组） | S10 |
| N12 | clone 面板源码：`group-key` 的字母 G ⟹ H | S11 |

★ **字段互不重叠**是这套阴性成立的前提：S2 只断言**除两段 keydown 原文之外**的片段
⟹ ⟹ N9 改的正是那两段 ⟹ ⟹ 只翻 S3；S5–S9 各读 clone raw 里**不同的键**。

★ 全部复原后**字节级**校验一致。

### 5.3 回归 `probes/regress853.py` — **62 条，红 8 条**

★ 清单 62 条：852 的清单 ＋ 853 ＋ **组相关十四条**（`45`／`47`／`48`／`49`／`50`／`59`／
`72`／`75`／`85`／`86`／`87`／`88`／`91`／`792`）
⟹ ⟹ 凡是读 `selectedGroupId`／`data-director-group-action` 的门禁都在里面，
⟹ ⟹ 否则「快捷键接对了」与「组本身被改坏了」分不开。

红 8 条：`831`／`741`／`736`／`748`／`749`／`782`／**`87`**／**`91`**。

### 5.3.1 ★★ `87`／`91` 是**新进清单**的，必须自己归因（不能猜）

★ `87` 与 `91` 以前**根本不在回归清单里**（它们是组相关门禁，上一批没列）
⟹ ⟹ 它们红的原因**不能靠「看起来无关」打发** ⟹ ⟹ 做了定点对照
（`probes/attrib8791.py` ⟹ `raw/attrib-87-91.json`）：

| 门禁 | HEAD 上（换回本批源码前） | 工作副本 | 判定 |
| --- | --- | --- | --- |
| `87` | rc=1 ｜ `missing-selection-repair:console:error:TransformControls: The attached 3D object must be a part of the scene graph.` | **逐字相同** | 既有旧账 |
| `91` | rc=1 ｜ `group-command:console:error:TransformControls: The attached 3D object must be a part of the scene graph.` ×2 | **逐字相同** | 既有旧账 |

★★ 两条的报错**都是 TransformControls 的「attached 3D object must be a part of
the scene graph」**（batch 50 的输出里把它列为「Known transient」，
但 `87`／`91` 没收进它们的过滤名单）⟹ ⟹ **不是本批引入的**。
★ 而且 `91` 的 `group-command` 阶段是**直接调 store**
（`addCrowdArray` → `ungroupSelectedCharacters` → `groupSelectedCharacters`），
**没有按 ⌘G** ⟹ ⟹ 本批接的快捷键根本没参与这两条。

### 5.4 受控对照 `probes/attrib853.py`

★ 把本批改过的源码**按字节换回 HEAD**（`DirectorDesk.tsx` 走 `git checkout --`，
★ 新建的 `directorShortcutRules.ts` **移走**——★ 它不在 HEAD 里，`git checkout` 对它无效）
⟹ ⟹ 重跑旧门禁 ⟹ ⟹ 看读数**逐条有没有变**。
★ ★ **连跑两遍**：换回源码后 4317 要热更 ⟹ ⟹ 「一轮的差」不能直接当因果。

**结果：22 条里 21 条读数逐条完全相同**（`raw/attrib-853.json`），
★ 唯一不一致的是 **853 自己**：

| 批次 | HEAD 上 | 工作副本 | 判定 |
| --- | --- | --- | --- |
| `853` | rc=1 ｜ `FileNotFoundError: .../directorShortcutRules.ts` | rc=0 ｜ **11/11 通过** | ★ **门禁有牙** |

★ 在 HEAD 上它连跑都跑不起来（本批新建的文件不存在）⟹ ⟹ 这正是「门禁真的在读
本批的源码」的直接证据；其余 21 条（含 `87`／`91` 这两条红的）读数**逐字相同**
⟹ ⟹ 本批**没有**动到它们的比对对象。

### 5.5 验收结果

| 项 | 结果 |
| --- | --- |
| 契约提取 | **16/16 唯一命中**（另有两个多命中项已改成唯一化正则） |
| 源站实测 | 行为矩阵 5 条全部成立；结束时**已复原到基线** |
| clone 实测 | 行为矩阵 6 条全部与契约矩阵一致 |
| 门禁 | **11/11** |
| 阴性对照 | **12/12**，每条恰好翻一条，字节级复原 |
| 回归 | **62 条，红 8 条**；红的是**既有旧账**（`831`／`741`／`736`／`748`／`749`／`782` ＋ **新进清单的 `87`／`91`**，后两条已用定点对照证明**在 HEAD 上同样红、读数逐字相同**） |
| 受控对照 | **21/22 条读数逐条相同**；唯一不一致的是 **853 自己**（HEAD 上 FileNotFoundError，工作副本 11/11）⟹ ⟹ **门禁有牙** |
| `npx tsc --noEmit` | ✓ |
| `npx eslint`（本批两个文件） | 零问题 |
| `npm run build` | ✓ |
| `npm run assertions:check` | ✓ |
| `npm run docs:check` | 断链全在 `docs/user-manual/`（他人并发区） |

★ ★ **里程碑**：导演台快捷键面板的 **12 条至此全部落地**——
`851` 视图类 6 条（`T`／`H`／`Y`／`WASDQE`）＋ `852` 变换类 4 条（`V`／`R`／`F`／`X`）
＋ 本批 2 条（打组 `⌘G`／解组 `⌘⇧D`）；撤销 `⌘Z` 与删除 `⌫` 本来就有。

---

## 6. 与源站的差异登记（**如实标注，不假装已对齐**）

| 编号 | 差异 | 证据 | 影响 |
| --- | --- | --- | --- |
| D1 | ★★ **clone 的组只收角色**（`groupSelectedCharacters` 只过滤 `kind === "character"`）；源站的组收**任意场景成员**（character／prop／emptyObject／camera） | 源站逐字 `sg(e)` ＋ 源站实测「两个机位能成组」 | 源站能对两个机位打组，clone 不能 ⟹ **组模型**问题，留给独立批次 |
| D2 | clone 的组名是 `角色组N`；源站是 `分组N`（i18n `canvas:nodeTypeGroup` ＋ N） | 源站逐字 `lT(e)` vs clone `label: \`角色组${groupIndex}\`` | 命名不一致（文案级） |
| D3 | clone 的树多选是**⇧+点击且仅限 character**；源站是 **⇧／⌘／Ctrl ＋ 点击**，且**只对可分组类别**生效 | 源站逐字 `t.shiftKey\|\|t.metaKey\|\|t.ctrlKey` ＋ `sg(e.category)?{additive:r…}` | 多选手感不一致（且源站的 ⌘+点击还能选机位） |
| D4 | clone 的组**默认折叠**成员（成员要展开才看得见）；源站的组成员**始终展开**（只是缩进） | 源站实测：成组后树上 4 行；clone 实测：`DOM角色行数` 3→1 | 树上结构观感不一致 |
| D5 | clone 的解组走 `deleteDirectorEntity({kind:"DELETE_GROUP", memberPolicy:"UNGROUP"})`；源站是独立的 `UNGROUP_CHARACTER_GROUP` reducer 分支（**解绑相机** ＋ 过滤 `animation.groupTracks`） | 源站逐字 `case"UNGROUP_CHARACTER_GROUP"` | clone 没有 `groupTracks` 对应物 ⟹ 暂无实际影响 |
| D6 | 源站在 window **捕获**阶段 `stopPropagation()+stopImmediatePropagation()` ⟹ **吞掉所有按键**；clone 只在自己的分支里 `preventDefault()` | 852 已实测（源站冒泡阶段收到 0 个键） | 沿用 852 的既有差异登记（D1） |

★ **已对齐**（不是差异）：面板两行逐字一致（打组 ⌘G ／ 解组 ⌘⇧D）；
★ `⌘⇧G` 这个「实现里有、面板没列」的别名，源站与 clone 行为一致。

---

## 7. 遗留

| 编号 | 事项 | 说明 |
| --- | --- | --- |
| L1 | ★★ **组模型扩展**（`members` 字段、树渲染、rig、`groupTracks`） | D1／D3／D4／D5 的共同根因 ⟹ ⟹ 独立批次 |
| L2 | **clone 默认场景只有一个角色** ⟹ ⟹ ⌘G 在默认态是死键 | 需要「添加群众阵列」或加角色入口先落地 ⟹ ⟹ 随 L1 一起处理 |
| L3 | clone 的「添加角色」飞层里 8 个预设**只是占位提示**（不真建角色） | 现有唯一能真造角色的是「群众阵列」 |
| L4 | **`87`／`91` 的 TransformControls 瞬态**（本批新进回归清单才发现；已定点对照证明**不是本批引入的**） | 两条在 HEAD 上同样红、报错逐字相同 ⟹ ⟹ 属独立批次（可仿 batch 50 把这个瞬态收进过滤名单） |
| L5 | 旧账（独立批次）：`782` 的 17 条行号漂移债 ＋ `736` 的 C1/C3/C4/C7、`748` C1/C3/C4、`749` 7/9、**`741` 的 C1/C3**、`831` 的 S14、`826` popover 20px、`830` 的 ⌘C 复制／撤销栈跨刷新／时间轴缩放公式 | 沿用 851／852 的登记 |

---

## 8. 证据索引

| 产物 | 内容 |
| --- | --- |
| `probes/extract853_contract.py` | 契约提取器（16 片段 ＋ 行为矩阵推导器） |
| `probes/source853_groupkeys.py` | 源站探针（**有副作用**，末尾复原） |
| `probes/clone853.py` | clone 探针（真实 UI ＋ 真按键盘） |
| `probes/neg853.py` | 阴性对照（12 条，每条恰好翻一条） |
| `probes/regress853.py` | 回归（61 条） |
| `probes/attrib853.py` | 受控对照（换回 HEAD ＋ 连跑两遍） |
| `raw/source-853-contract.json` | 契约（16 片段 ＋ 推导出的矩阵） |
| `raw/source-853-groupkeys.json` | 源站实测读数 |
| `raw/clone-853-groupkeys.json` | clone 实测读数 |
| `runtime-audit.json` | 门禁报告（11/11） |
| `negative-audit.json` | 阴性报告（12/12） |
| `images/853src_*.png` | 源站截图 6 张（树区域） |
| `images/853clone_*.png` | clone 截图 10 张（左树区域） |

---

## 9. 复现步骤

```bash
export PATH="$HOME/.pyenv/shims:$PATH"
cd /Users/yangjiefeng/Documents/wubuku/liblib-tv

# ① 契约提取（需要 /tmp/liblib_srcjs2/0fmehki05gkzw.js.js）
python docs/research/liblib-canvas-batch853-2026-10-01/probes/extract853_contract.py

# ② 源站实测（★ 有副作用：会建组，末尾自动复原）
python docs/research/liblib-canvas-batch853-2026-10-01/probes/source853_groupkeys.py

# ③ clone 实测（需要 4317 在跑）
python docs/research/liblib-canvas-batch853-2026-10-01/probes/clone853.py

# ④ 门禁
python scripts/verify-liblib-batch853.py

# ⑤ 阴性对照
python docs/research/liblib-canvas-batch853-2026-10-01/probes/neg853.py

# ⑥ 回归 / 受控对照
python docs/research/liblib-canvas-batch853-2026-10-01/probes/regress853.py
python docs/research/liblib-canvas-batch853-2026-10-01/probes/attrib853.py
```
