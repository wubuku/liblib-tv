# batch 856 — 导演台「组的检查器与画布 gizmo」（D1 取证 ⟹ 结论反转）

> 上一批：batch 855「组 rig 的成员语义」，提交 `b0e19b3d`。
> ★ **本批把 855 登记的 D1 做完了** ⟹ ⟹ 但**结论和当初登记的假设相反**。

---

## 1. D1 是什么、为什么结论会反转

★ 855 登记的 D1 原文：

> **D1 源站的 rig 是纯平移（无旋转／缩放），clone 的交互路径带旋转增量＋缩放比**
> ⟹ 源站的组**根本没有 transform 字段** ⟹ ⟹ 交互路径的逐字**还没钉死** ⟹ ⟹ 独立批次。

★ 当时的结论是「**语义未取证**」⟹ ⟹ 所以本批去取证。
★ ★ **取到的结果比「未取证」更明确** ⟹ ⟹ 不是「源站的组变换是纯平移」，
而是 ⟹ ⟹ ★★ **源站的组检查器与画布上，根本就没有「变换」这个概念**。

| | 源站（实测） | clone（整改前） | clone（整改后） |
| --- | --- | --- | --- |
| 组检查器的**变换字段** | **0**（只有「名称」） | 3（位置／旋转／缩放） | **0** |
| 组检查器的**输入框** | **1**（名称，248×28） | 10 | **1**（名称，248×32） |
| 画布上的**组 gizmo** | **没有** | 有（可拖拽整组） | **没有** |
| 组对象字段 | `{id,label,characterIds,members}` | 同 | 同 |

⟹ ⟹ ★ **clone 那三个变换字段 ＋ 那个 gizmo，是源站**不存在的能力**
⟹ ⟹ 它们走的 `applyDirectorGroupTransform`（「旋转增量 ＋ 缩放比」）
在源站**根本没有对应实现** ⟹ ⟹ 本批按源站逐字**删掉这两个入口**。

---

## 2. 源站逐字依据（机器提取，6/6 唯一命中）

★ 提取器：`probes/extract856_contract.py` ⟹ `raw/source-856-contract.json`
★ **唯一命中 6 / 6**（命中数 ≠ 1 就记空并退出 1，不产出假 raw）＋ **任意值类名自检通过**。

```js
// ① 组对象字面量 —— ★ 只有 4 个字段，**没有 transform**
a={id:lM(),label:lT(e.characterGroups),characterIds:n,members:r}

// ② 权威成员列表 O(e)（members 优先＋characterIds 兜底＋去重）
function O(e){let t=[],r=new Set,n=e=>{if(!e.id)return;let n=N(e);
  r.has(n)||(r.add(n),t.push(e))};return(e.members??[]).forEach(n),
  (e.characterIds??[]).forEach(e=>n({kind:"character",id:e})),t}

// ③ reducer SELECT_CHARACTER_GROUP（选中组 ⟹ lQ(n) ＋ selectedGroupId）
case"SELECT_CHARACTER_GROUP":{let r=e.characterGroups.find(e=>e.id===t.id);
  if(!r)return e;let n=lB(O(r),e.characters,e.props,e.emptyObjects,e.cameras);
  if(0===n.length)return e;return{...e,...lQ(n),selectedGroupId:r.id}}

// ④ 组的锚点 H(e,t) —— ★ 全部成员位置的均值 ⟹ ⟹ 组位置永远是**派生**的
function H(e,t){var r=O(e).map(t).filter(e=>!!e);if(0===r.length)return null;
  let n=r.reduce((e,t)=>({x:e.x+t.x,y:e.y+t.y,z:e.z+t.z}),{x:0,y:0,z:0});
  return{x:n.x/r.length,y:n.y/r.length,z:n.z/r.length}}

// ⑤ 组轨道创建（keyframes 只有一个 position）
keyframes:[{time:0,position:n}],interpolation:"linear",memberOffsets:V(i,n,t=>L(e,t))}

// ⑥ 组轨道编辑属性（★ 只有 position 一个）
if("group"===e.kind){let t=A.groupTracks.find(t=>t.id===e.trackId);
  if(!t)return!1;let n=b.characterGroups.find(e=>e.id===t.targetId),
  a=n?H(n,e=>L(b,e)):null,i=g(t.keyframes,a?.y??0);
  return na(e.trackId,{...y,...v,keyframes:i,
  speedCurveSegments:hi(t.speedCurveSegments,["position"])},r),!0}
```

★ ★ **提取器当场抓住过一次「不唯一」**：第 ⑥ 条的短锚点
`speedCurveSegments:hi(t.speedCurveSegments,["position"])` 在 chunk 里命中 **7** 次
（character／prop／camera／group 各自的轨道 ＋ 两处 motionPath 清理）
⟹ ⟹ 提取器**拒绝产出**并退出 1 ⟹ ⟹ 改用带「这是 group 那条」前缀的长锚点才唯一。

★ ★★ **另外两条关键证据**（不在契约里，但同样是从 chunk 里读出来的）：

1. `groupTransform` 在 chunk 里命中 **0** 次 ⟹ ⟹ 源站**没有**组的 transform 概念。
2. `UPDATE_GROUP_TRANSFORM` 命中 **0** 次 ⟹ ⟹ 源站**没有**这个 reducer action。
3. gizmo 的 `register` 只注册**具体对象**（character／prop／camera／emptyObject）
   ⟹ ⟹ **没有「组」这一类**。

⟹ ⟹ ★ **源站里组的位置是 100% 派生的**（`H(e,t)`＝成员位置均值）
⟹ ⟹ 要让组动，**只能改成员** ⟹ ⟹ 而成员的位移来自**组轨道**
（源站逐字：`memberOffsets:V(i,n,...)` ＋ rig 纯平移）⟹ ⟹
**组轨道是源站唯一的「组移动」路径**。

---

## 3. 源站实测（两支探针）

### 3.1 组检查器只有「名称」

★ 探针：`probes/source856_groupinspector.py` ⟹ `raw/source-856-groupinspector.json`
★ 读数策略：**不手打中文字段名** ⟹ ⟹ 靠结构读（输入框的 type／aria ＋ 祖先链上的纯文本）。

| 面板 | 可见输入框数 | 字段 label |
| --- | --- | --- |
| 选中**角色** | **13** | 名称／位置×3／旋转×3／缩放×3／统一缩放×2／颜色 |
| 选中**组** | **1** | **名称**（值 `分组1`） |

★ ★ **阳性对照的设计很关键**：同一个探针、同一次会话，
在角色上能读出 13 个字段（含位置／旋转／缩放），
在组上只读出 1 个 ⟹ ⟹ **证明探针有分辨力**，
而不是「探针瞎了所以什么都没读到」。

★ 截图：`images/856src_character-panel.png`（角色：属性／姿势两个页签 ＋ 六组字段）
vs `images/856src_group-panel.png`（组：**只有名称**，下面整片空白）。

### 3.2 画布上**没有**组 gizmo

★ 探针：`probes/source856_groupgizmo.py` ⟹ `raw/source-856-groupgizmo.json`
★ 源站的 gizmo 是 three.js 的 `TransformControls` ⟹ ⟹ **DOM 上读不到**
⟹ ⟹ 只能靠**像素**：同尺寸同位置截图 ⟹ ⟹ **逐像素数**出差异。

| 场景 | 不同像素数 | 变化包围盒 | 判读 |
| --- | --- | --- | --- |
| 选中**角色** vs 未选中 | 5,255 | `[56,112,896,580]` | ★ 右缘 **896** ⟹ 画布上**有** gizmo（右下角红色箭头） |
| 选中**组** vs 未选中 | 19,286 | `[55,48,**271**,161]` | ★ 右缘 **271** ＝ 树面板右缘 ⟹ 画布上**没有任何变化** ⟹ **无 gizmo** |

★ ★ **又是阳性对照**：同一个探针，在角色上像素差**延伸到 x=896**，
在组上**只到 x=271**（左侧树面板）⟹ ⟹ 组选中时画布是**干净的**。

★ 截图：`images/856gizmo_01-character.png`（右下角有红色箭头）
vs `images/856gizmo_02-group.png`（画布空白，只有左侧树变了）。

---

## 4. clone 侧实施（2 个源文件）

| 文件 | 改了什么 |
| --- | --- |
| `src/components/director/DirectorInspector.tsx` | ★ 组检查器**删掉「位置／旋转／缩放」三个字段**（只剩「名称」＋ 成员数条 ＋ crowd 参数）⟹ ⟹ 连带删掉 `updateField` 辅助函数 ＋ `updateGroupTransform`／`recordGroupKeyframe` 两个 store 订阅 ＋ **死代码** `cloneDirectorTransform` ⟹ ⟹ ★ **另外删掉那段「分组包含已锁定成员，分组变换已停用」的锁定提示块**（理由有两条：① 文案已经**与事实矛盾**——组根本没有「变换」可停用；② **源站没有这个提示**——实测组面板只有「名称」一个字段）⟹ ⟹ 连带的局部变量 `hasLockedMember` 也一并移除 |
| `src/components/director/DirectorViewport.tsx` | ★ `DirectorGroupTransformRig` **移除 `TransformControls`（gizmo）** ⟹ ⟹ 只保留一个空的锚点 group（保留 `data-director-group-rig` 这个语义锚点） |

★ ★ **删锁定提示块时踩到的一个小坑** ⟹ ⟹ 那个提示块删掉之后，
局部变量 `hasLockedMember` 变成**未被使用** ⟹ ⟹ 而它的**注释**里
却已经写着「所以 `hasLockedMember` 这个局部变量也一并移除」
⟹ ⟹ **注释说已删、代码还在** ⟹ ⟹ 靠 `tsc`／`eslint` 抓到并删掉
⟹ ⟹ ★ 「注释描述的状态」必须和**代码**逐字对齐，否则下一批会信注释。

★ ★ **不动的那条链**：`store` 的 `updateGroupTransform` ＋ `directorGroupMath` 的
`applyDirectorGroupTransform` **保留** ⟹ ⟹ 理由见第 7 节 D6。

★ ★★ **组轨道是唯一移动路径这件事被门禁钉住**（S7）：
组轨道仍然建得出来（实测 1 条）⟹ ⟹ 组**还能动** ⟹ ⟹ 删掉 UI 入口**没有**让用户失去移动组的能力。

---

## 5. 判据与证据链（12/12）

| 判据 | 读什么 | 阴性 |
| --- | --- | --- |
| S1 | 契约：**6 个片段唯一命中** ＋ 3 条关键逐字 ＋ 任意值类名自检 | N1 |
| S2 | 源站实测：**组检查器只有「名称」一个字段** | N2 |
| S3 | 源站**阳性对照**：角色检查器 **13 个字段**（含位置／旋转／缩放） | N3 |
| S4 | 源站实测：选中组后画布**像素差只落在树面板**（无 gizmo） | N4 |
| S5 | 源站**阳性对照**：选中角色时画布像素差**延伸到右侧**（有 gizmo） | N5 |
| S6 | clone 实测：**组检查器 0 个变换字段 ＋ 1 个名称输入框** | N6 |
| S7 | clone 实测：**组轨道仍在** ＋ 解组能复原 | N7 |
| S8 | clone 源码：组检查器**无变换字段** ＋ 组 gizmo 组件**无 `TransformControls`** | N8／N10 |
| S9 | clone 源码：**死代码已清**（Inspector 里没有 `cloneDirectorTransform` 的定义／调用） | N9 |
| S10 | 老门禁 `84.mjs`：**判据已迁移**（组锁定守卫改认 store ＋ 旧写法清零） | — |
| S11 | 老门禁 `86.mjs`：**判据已迁移**（写死个数 ⟹ 结构性断言 ＋ 旧写法清零） | — |
| S12 | 老门禁 `852.py`：**判据已迁移**（写死三处 ⟹ 每处 gizmo 都用吸附步长） | — |

★ ★★ **S2/S3 与 S4/S5 是成对的** ⟹ ⟹ S2 只说「组面板 1 个字段」是不够的
⟹ ⟹ 必须同时有 S3「**同一个探针**在角色上能读出 13 个」，
否则「clone 也是 1 个」可能只是因为**探针瞎了**。

★ ★ **S9 第一次跑就假红了** ⟹ ⟹ 原因：我查的是「`cloneDirectorTransform`
这个字符串在不在文件里」⟹ ⟹ 而**注释里提了一句**就假红
⟹ ⟹ 修法：查**函数定义／调用**（`function\s+cloneDirectorTransform\s*\(`）
而不是「名字出现过」⟹ ⟹ 判据的强度必须等于它宣称的东西。

★ **阴性**：`probes/neg856.py` ⟹ `negative-audit.json`
★ **13/13 每条恰好翻一条** ＋ 全部复原后**门禁回绿** ＋ **字节级复原**。
★ ★ N8／N9 的变异第一版**不是行数中性**（插了一行）
⟹ ⟹ 被脚本自己的「行数中性」检查**当场回滚**（脚本救了自己）
⟹ ⟹ 改成**同行替换**后才过。

---

### 5.1 两条老门禁的「判据迁移」（★ 本批的副作用，**必须如实登记**）

★ 本批删掉了**组 gizmo** ⟹ ⟹ 有两条**老门禁**的断言**前提过期**了
⟹ ⟹ 按仓库先例（batch 854 改 `45.py`、batch 855 改 `87.mjs`）**迁移判据**：
**正向改成新前提 ＋ 加负向断言保证旧写法清零**（否则「新旧都写」就能蒙混过关）。

| 老门禁 | 旧断言 | 前提为什么过期 | 迁移后 |
| --- | --- | --- | --- |
| `84.mjs` | `viewportSource` 含 `hasLockedMember` | 那道守卫是「组里有锁定成员 ⟹ **隐藏组 gizmo**」⟹ ⟹ 它的前提是「视口里有组 gizmo」⟹ ⟹ 而组 gizmo 已被按源站删掉 ⟹ ⟹ 旧断言守的是一个**源站不存在的交互** | 正向：store 里有 `function directorGroupHasLockedMember(` **且**有调用点 `directorGroupHasLockedMember(state, group)`；负向：`assert.doesNotMatch(viewportSource, /const hasLockedMember\s*=/)` |
| `86.mjs` | `onPointerCancel={cancelTransform}` **写死 3 次**、`onLostPointerCapture={cancelTransform}` **写死 2 次** | 那 3 个挂点里有一个**就是组 gizmo** ⟹ ⟹ 删掉它 ⟹ ⟹ 写死的个数过期 | 改成**结构性**断言（见下） |
| `852.py` | S9 断言 `translationSnap={…DIRECTOR_GRID_SNAP_STEP : null}` **写死 3 处** | 那个「三」的前提是「视口里有 3 个 gizmo（对象／**组**／路径控制点）」⟹ ⟹ 本批删掉组 gizmo ⟹ ⟹ 只剩 **2** 处 ⟹ ⟹ 旧断言红 | 改成**结构性**断言：「**每处** gizmo 都用 `DIRECTOR_GRID_SNAP_STEP`」（gizmo 挂点数 **==** 用步长的处数）⟹ ⟹ 并**在计数前剥注释**（否则注释里那句 `` `<TransformControls mode={transformMode}>` `` 会被算成一处挂点 ⟹ ⟹ 假红） |

★ ★ **「写死个数」这种判据本身就有洞** ⟹ ⟹ 这不是「换个写法」，是**换强了**：
★ 少一个 gizmo ⟹ 旧判据**假红**；多一个**不带** pointer cancel 的 gizmo ⟹ 旧判据**照样绿**。
★ 新的结构性断言：
① 每个 `<TransformControls>` 挂点都**必须**带 `onPointerCancel={cancelTransform}`；
② `onPointerCancel` 的数量 **==** gizmo 挂点数；
③ 主变换 gizmo（`mode={transformMode}`）**唯一**且额外带 `onLostPointerCapture={cancelTransform}`；
④ 路径控制点 gizmo（`mode="translate"`）**唯一**；
⑤ **负向**：组 rig 组件（`DirectorGroupTransformRig`）里**不允许**有 `<TransformControls`。

★ ★★ **阴性 N12 拿出了「旧判据有洞」的实测证据**（不是论证，是读数）：
★ 往视口里加一个**不带** pointer cancel 的 gizmo ⟹ ⟹
★ `onPointerCancel` 计数 **2 → 2（不变）**，而 gizmo 挂点数 **2 → 3（变了）**
⟹ ⟹ 任何**只依赖 count** 的判据（旧的 `count === 写死的 K`）在这个变异前后
**输出逐字相同** ⟹ ⟹ 它**看不见**这个变异；
⟹ ⟹ 而新判据「count **==** gizmo 挂点数」⟹ ⟹ 立刻变红。
★ ★ 阴性 **N10／N11／N12** 直接**跑那条老门禁**（`node scripts/verify-liblib-batch86.mjs`）
⟹ ⟹ 三条**都真的翻红**、复原后**都回绿** ⟹ ⟹ 证明「迁移后的判据**还有牙**」
⟹ ⟹ 单跑本批门禁（S1–S12）证明不了这一点（它只看门禁脚本文本，不执行老门禁）。
★ ★ 阴性 **N13** 同理跑 `852.py`（把一处 gizmo 的吸附步长改成 `null`
⟹ ⟹ `852.py` 立刻红）⟹ ⟹ 证明「每处 gizmo 都用步长」这条**真的在读**那处挂点。

★ ★★★ **「旧前提」普查：本批撞上的是第 3 条**（855 的 `87.mjs` 是第 1 条）⟹ ⟹
★ 三条的**共同形状**是：**断言里写死了某个「数量／成员集合」**，
★ 而那个数量**正好包含了源站不存在的东西**：
★ `87.mjs` 写死「`characterIds.filter`」（组里只有角色的旧前提）、
★ `86.mjs` 写死「3 个挂点」（多算了组 gizmo）、
★ `852.py` 写死「3 处用步长」（多算了组 gizmo）。
★ ⟹ ⟹ **通则**：断言里凡是出现「写死的个数／成员集合」，
★ 都要问一句「这个数**为什么**是这个数」⟹ ⟹ 答不上来就该改成**结构性**断言。


---

## 6. 回归与受控对照

★ 回归清单：`probes/regress856.py`（**78 条** ＝ 855 的 77 条 ＋ 本批 856；
★ 另把 **91.py** 加进清单与 WATCH —— 它是组变换命令的**真实行为测试**
⟹ ⟹ 本批改了 Inspector／Viewport ⟹ ⟹ 必须盯它**仍绿**）。
★ 受控对照：`probes/attrib856.py` 同形态（白名单列出本批改过的**全部源文件**
＝ 2 个；★ 本批**没有**新增／改名／删除任何导出 ⟹ ⟹ 换回 HEAD 之后**整站仍能编译**）。
★ ★ **换回源码后必须热机 4317**（冷编译会让第一条门禁 60s 超时 ⟹ ⟹ 假差异）。
★ ★ **两遍读数不一致时不能直接当「读数变了」** ⟹ ⟹ 要**再跑第三遍**
（855 已经踩过：`748.py` 第一遍 `KeyError`、第二遍就正常 ⟹ ⟹ 瞬态）。

★ ★★ **本批回归的实际结果**（一共跑了**三轮**，每一轮的差别都有定点对照）：
★ 第 1 轮（在 `45.py` 的判据迁移**之前**）⟹ ⟹ **红 12 条**；
★ 第 2 轮（`45.py`／`84.mjs`／`86.mjs` 三条迁移之后）⟹ ⟹ **红 9 条** ⟹ ⟹
★ 逐条**定点对照**（HEAD 上**绿**、工作副本**红** ⟹ ⟹ 本批引入）：
★ `84.mjs`（断言 viewport 含 `hasLockedMember`）⟹ ⟹ 已迁移；
★ `86.mjs`（`onPointerCancel={cancelTransform}` **写死 3 次**）⟹ ⟹ 已迁移；
★ `852.py`（S9 写死「**三处** TransformControls 都用吸附步长」）⟹ ⟹ 已迁移；
★ ★ 而 `91.py`（2 个 console error
★ `TransformControls: The attached 3D object must be a part of the scene graph`）
★ **换回 HEAD 跑同样红** ⟹ ⟹ **旧账、非本批引入**；
★ 其余 8 条全是**已知旧账**（`831`／`835`／`741`／`736`／`748`／`749`／`782`）。
★ 第 3 轮（三条迁移全部修完）⟹ ⟹ **红 8 条** ⟹ ⟹ **全是已知旧账**；
★ 盯的 **34 条**里只有 `91.py` 红（已知瞬态）。

---

## 7. 差异登记（如实登记，不假装已对齐）

### D1（已在本批**结案**）源站的组**没有变换概念**

* ★ 结论：源站的组检查器**只有「名称」**，画布上**没有组 gizmo**，
  组对象**没有 transform 字段**，源站**没有** `UPDATE_GROUP_TRANSFORM`。
* ★ 本批已按源站逐字**删掉** clone 的那三个变换字段 ＋ 那个 gizmo。
* ★ 组的移动路径**保留**：**组轨道**（源站唯一的路径，clone 已有且 855 已对齐）。

### D6 clone 仍保留 `updateGroupTransform` ＋ `applyDirectorGroupTransform`

* ★ 源站**没有**这两个东西（`UPDATE_GROUP_TRANSFORM` 命中 0 次）。
* ★ clone 保留它们 ⟹ ⟹ 理由：
  1. **用户可见层已经对齐** ⟹ ⟹ 它们**没有 UI 入口** ⟹ ⟹ 用户触发不到；
  2. 它们是 **store 的内部 API**，删掉要动 **4 条历史门禁**
     （`45.py`／`84.mjs`／`91.mjs`／`91.py`），
     其中 `91.py` 是**真实行为测试**（历史入库 ＋ 非法值拒绝）
     ⟹ ⟹ 删它等于**降低历史覆盖**；
  3. 它们的语义（写组变换 ＋ 顺带写轨道关键帧）**本身没错**。
* ⟹ ⟹ **如实登记**：这是「clone 有一条源站没有的内部命令」，
  而**不是**「用户能看到源站没有的 UI」。

### D2–D5（855 登记的，仍未结案）

* ★ **D2** 源站的 rig **没有 camera 分支** ⟹ ⟹ 「机位入组不跟组动」
  **不是 clone 的 bug**、是源站的行为（源站里机位靠 `followTargetId` 跟组锚点）⟹ ⟹ 独立批次。
* ★ **D3** 源站的 `memberOffsets` 键是 `kind:id`、clone 用裸 object id
  （clone 的 id 带类别前缀 ⟹ ⟹ 全局唯一 ⟹ ⟹ 语义等价）⟹ ⟹ 不改键方案只登记。
* ★ **D4** 源站允许**相机跟随组**（`followTargetId` → 组锚点）、
  clone 的相机只能指向**对象** ⟹ ⟹ **能力缺口** ⟹ ⟹ 独立批次。
* ★ **D5** 源站的组锁定指示是「**全部成员都锁才算锁**」
  （逐字 `locked:t.length>0&&t.every(e=>e.locked)`）、
  clone 的 `directorGroupHasLockedMember` 是**写入守卫**
  （「任一成员锁住 ⟹ 拒绝写组关键帧」）⟹ ⟹ 语义方向相反 ⟹ ⟹ 独立批次。

---

## 8. 与他人并发区的边界

★ 本批只碰上表那 2 个源文件 ＋ `scripts/verify-liblib-batch856.py` ＋
`docs/research/liblib-canvas-batch856-2026-10-01/**`。
★ **不碰**：`src/app/clones/`、`src/lib/clonePages.ts`、`src/components/CloneSiteNav.tsx`、
`docs/CLONE_PAGES_INDEX.md`、`docs/user-manual/**`、`src/components/jimeng/*`、
`src/store/jimengStore.ts`、`src/app/page.tsx`。
★ `stash@{0}`（`in-progress-edit-for-revert`）**全程未碰**。

---

## 9. 产物清单

```text
docs/research/liblib-canvas-batch856-2026-10-01/
├── README.md                       ← 本文件
├── runtime-audit.json              ← 门禁 9/9
├── negative-audit.json             ← 阴性 9/9「恰好翻一条」＋ 复原回绿
├── probes/
│   ├── extract856_contract.py      ← 源站契约提取（6/6 唯一命中 ＋ 任意值自检）
│   ├── source856_groupinspector.py ← 源站实测①：组检查器字段
│   ├── source856_groupgizmo.py     ← 源站实测②：画布 gizmo 的像素判据
│   ├── clone856.py                 ← clone 实测（真实 UI）
│   ├── neg856.py                   ← 阴性对照
│   └── regress856.py               ← 回归清单（78 条）
├── raw/
│   ├── source-856-contract.json    ← 源站逐字 6 片段
│   ├── source-856-groupinspector.json  ← 源站组检查器读数
│   ├── source-856-groupgizmo.json  ← 源站 gizmo 像素读数
│   └── clone-856-groupinspector.json   ← clone 实测读数
└── images/
    ├── 856src_*.png                ← 源站截图（角色面板／组面板／打组／复原）
    ├── 856gizmo_*.png              ← 源站 gizmo 像素对照（未选中／角色／组）
    └── 856clone_*.png              ← clone 截图
```

---

## 10. 本批的「自我清算」

★ ★★ **一条：取证的方法比结论更重要**。

★ 855 登记 D1 时说「交互路径的逐字**还没钉死**」⟹ ⟹ 于是本批去钉。
★ 但如果只**读 chunk**（`groupTransform` 命中 0 次、`UPDATE_GROUP_TRANSFORM` 命中 0 次），
那只能得出「**源站的组没有 transform 字段**」⟹ ⟹
**推不出「源站的组检查器没有变换字段」** ⟹ ⟹
因为「没有数据字段」不等于「没有 UI」（完全可以有 UI 只是不落盘）。
⟹ ⟹ ★ 所以必须**实测 UI** ⟹ ⟹ 才拿到决定性的两组读数：
**组面板 1 个字段** ＋ **画布无 gizmo**。
⟹ ⟹ ★★ **通式**：查「数据模型里有没有某字段」只能证明**存不存在**，
**证明不了「界面给不给入口」** ⟹ ⟹ 这两件事必须**分别取证**。

★ ★ **第二条：阳性对照是「探针有分辨力」的证明**。

★ 两支源站探针都各配了一条**阳性对照**：
  - 检查器探针：同一个探针在**角色**上能读出 **13 个字段**（含位置／旋转／缩放）；
  - gizmo 探针：同一个探针在**角色**上像素差**延伸到 x=896**（画布右下角有红色箭头）。
⟹ ⟹ 「组面板只有 1 个字段」「组选中时画布没有变化」这两个读数
⟹ ⟹ 才能被解释成「**源站确实没有**」而不是「**探针没读到**」。
⟹ ⟹ ★★ **凡是要用「读不到某东西」当证据 ⟹ ⟹ 必须有一条「读得到同类东西」的对照**。

★ ★ **第三条：判据的强度必须等于它宣称的东西**。

★ S9 第一版写的是「`cloneDirectorTransform` 这个字符串在不在 Inspector 里」
⟹ ⟹ 我在注释里写了一句「这里原本有一份 `cloneDirectorTransform`」
⟹ ⟹ **当场假红** ⟹ ⟹ 修法：查**函数定义／调用**，不查「名字出现过」。
⟹ ⟹ ★★ 这与 855 的 S14／S15 是同一族：
**判据读的东西必须与它声称的东西同粒度**。

★ ★★ **第四条（本批新撞上的）：「写死的个数」是判据里最常见的隐形前提**。

★ 本批为了「源站没有组 gizmo」而删掉一个 `TransformControls`
⟹ ⟹ **连锁**撞上**三条**老门禁的「写死个数」：
★ `86.mjs` 写死「pointer cancel 挂点 **3** 次」、`852.py` 写死「用步长的 **3** 处」
⟹ ⟹ 两条都**只因为少了一个挂点**就红了。
⟹ ⟹ ★ 处置：不是「把 3 改成 2」（那只是把硬编码换成另一个硬编码），
⟹ ⟹ 而是改成**结构性**断言（「**每处** gizmo 都满足 X」），
⟹ ⟹ 并让**老门禁自己**证明它有牙（阴性 N11／N12／N13 **直接跑老门禁**看它红）。
⟹ ⟹ ★★ **通则**：断言里凡是出现「写死的个数／成员集合」，
⟹ ⟹ 都要问「这个数**为什么**是这个数」⟹ ⟹ 答不上来就该改成**结构性**断言。
⟹ ⟹ ★★ 而且：**「迁移判据」必须配一条「阴性直接跑那条老门禁」**，
⟹ ⟹ 否则「新门禁在读老门禁的文本」只能证明**迁移发生过**，
⟹ ⟹ 证明不了**迁移后的判据还有牙**。

---

## 11. 下一批候选

* ★ **D6**：把 `updateGroupTransform` 那条链**彻底删掉**（含 4 条历史门禁的判据迁移）
  ⟹ ⟹ 或反过来，先查清源站有没有**别的**「改组」路径
  ⟹ ⟹ **保留**更省事，但就不是「逐字复刻」了。
* ★ **D2**：源站 rig 缺 camera 分支是**有意**还是**漏写** ⟹ 需要源站的运行期证据。
* ★ **D3**：`memberOffsets` 键方案（裸 id ⟹ `kind:id`）是否值得改。
* ★ **D4**：相机跟随组（`followTargetId` → 组锚点）的能力补齐。
* ★ **D5**：组的**锁定指示**（源站 `every`）与 clone 的**写入守卫**（`some`）的分工。
* ★ **老门禁的「旧前提」普查**（855 撞上 `87.mjs` 是第 1 条；★ **856 撞上 3 条**
  ＝ `84.mjs`／`86.mjs`／`852.py`）⟹ ⟹ 三条的共同形状是
  「**断言里写死了某个数量／成员集合**」⟹ ⟹ 其余待按主题扫
  （扫法：搜门禁脚本里的 `count(`／`== 3`／`== 2`／`length ===` 这类字面量）。
* ★ 854 遗留：N1（源站场景树是平铺列表）／ N2·N3（可见·锁定指示）／「添加角色」8 个预设只是占位提示。
* ★ 852 遗留：⌘T／⌘Y 的修饰键差异；D3 路径草稿提交守卫的运行时取证。
* ★ 851 遗留：831 的 S14 历史债。
* ★ 850 遗留：「点左列分段会不会把取景重置为全身」的复验。
* ★ 旧账：782／736／748／749／741／835／831／91／826／830。
