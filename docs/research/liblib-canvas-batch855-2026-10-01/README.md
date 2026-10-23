# batch 855 — 导演台「组 rig 的成员语义」（锚点／成员偏移／组轨道／解组）

> 上一批：batch 854「组模型的成员语义」（组可含任意成员／默认展开／树多选 ⌘·Ctrl），
> 提交 `cad50017`。
> ★ **本批是 854 的下半截**：854 让组**可以**装下机位，但**组 rig 整条链仍然只认角色**
> ⟹ ⟹ 机位入组后不跟着组动、混合组的轨道**根本建不出来**、解组后选中态**选不全成员**。
> ⟹ ⟹ 本批把这条链按源站逐字对齐。

---

## 1. 这批要守住的东西（源站逐字）

★ 源站 chunk：`/tmp/liblib_srcjs2/0fmehki05gkzw.js.js`（1,018,130 字节）
★ 机器提取：`probes/extract855_contract.py` ⟹ `raw/source-855-contract.json`
★ **8 个片段全部唯一命中**（脚本会打印「唯一命中：8 / 8」；命中数 ≠ 1 就记空并退出 1）。

```js
function N(e){return`${e.kind}:${e.id}`}                       // 成员的键
function O(e){let t=[],r=new Set,n=e=>{if(!e.id)return;let n=N(e);
  r.has(n)||(r.add(n),t.push(e))};return(e.members??[]).forEach(n),
  (e.characterIds??[]).forEach(e=>n({kind:"character",id:e})),t}   // 权威成员列表
function H(e,t){var r=O(e).map(t).filter(e=>!!e);if(0===r.length)return null;
  let n=r.reduce((e,t)=>({x:e.x+t.x,y:e.y+t.y,z:e.z+t.z}),{x:0,y:0,z:0});
  return{x:n.x/r.length,y:n.y/r.length,z:n.z/r.length}}           // ★ 锚点＝全部成员均值
function V(e,t,r){return O(e).reduce((e,n)=>{let a=r(n);
  return a&&(e[N(n)]={x:a.x-t.x,y:a.y-t.y,z:a.z-t.z}),e},{})}    // ★ 成员偏移＝全部成员
let i=t.memberOffsets??V(r,a,f);O(r).forEach(t=>{let r=i[N(t)];   // ★ 遍历 O(r)＝全部成员
  r&&A.set(N(t),{position:{x:e.position.x+r.x,y:e.position.y+r.y,z:e.position.z+r.z},
                 yaw:n?.orientToPath?e.rotation.y:void 0,moving:v.has(e.id)})})
A.forEach((e,t)=>{…if("character"===o){…}if("prop"===o){…}if("emptyObject"===o){…}})
```

★ ★ **三个要害**（本批逐条钉住）：

1. **锚点 `H` 与成员偏移 `V` 都遍历 `O(e)`**（权威成员列表，**任意类别**）
   ⟹ ⟹ 机位入组后，锚点与偏移**都算机位**。
2. **rig 的应用块 `A.forEach` 只有三个分支**：`"character"===o` ／ `"prop"===o` ／
   `"emptyObject"===o` ⟹ ⟹ **没有 `"camera"===o` 分支**（可解析器却认 camera）
   ⟹ ⟹ **机位入组后不会被组轨道带动**（源站里机位靠 `followTargetId` 跟组锚点）。
3. **rig 的位置是纯平移**：`position ＝ 组的采样位置 ＋ 成员偏移`
   ⟹ ⟹ 偏移**不参与旋转／缩放**，成员保留自己的 `rotation`／`scale`。

★ 解组 reducer 逐字：

```js
case"UNGROUP_CHARACTER_GROUP":{let r=e.characterGroups.find(e=>e.id===t.id);if(!r)return e;
  let n=lB(O(r),e.characters,e.props,e.emptyObjects,e.cameras);
  return{...e,characterGroups:e.characterGroups.filter(e=>e.id!==t.id),
  cameras:e.cameras.map(r=>lV(r,e,new Set([t.id]))),
  animation:{...e.animation,groupTracks:e.animation.groupTracks.filter(e=>e.targetId!==t.id)},
  ...lQ(n),selectedGroupId:null}}
```

⟹ ⟹ 四件事：**复原任意类别成员** ／ **移除该组轨道** ／ **选择态＝复原的成员**
（`lQ` 的 `selectedSceneMembers`）／ **`selectedGroupId` 置空**。

---

## 2. clone 侧改了什么（8 个源文件）

| 文件 | 改了什么 |
| --- | --- |
| `src/components/director/directorGroupMath.ts` | ① 新增 `resolveDirectorGroupMemberRefs`（组数学侧的一份权威列表实现）② `getDirectorGroupMembers` 去掉「只认角色」③ 新增 `applyDirectorGroupRig`（源站逐字的纯平移 rig）④ `DIRECTOR_GROUP_RIG_DRIVEN_KINDS`＝`character`＋`prop`（**无 camera**）⑤ `applyDirectorGroupTransform`（交互路径）的成员集改成「全部非机位成员」 |
| `src/store/directorStore.ts` | ① 时间轴 rig 改走 `applyDirectorGroupRig` ② 新增 `directorGroupHasLockedMember`（锁定守卫按全部成员）③ **6 处选中态**从「只认角色」改成「全部成员」 |
| `src/lib/directorProjectDocument.ts` | 组轨道的 `memberOffsets` 键集校验改成按**权威成员列表**（854 留的「D5 遗留」） |
| `src/lib/directorDeletePlanner.ts` | 轨道 closure 按**全部成员**保留偏移 |
| `src/components/director/DirectorInspector.tsx` | 锁定守卫 ＋ 成员数显示（标签写的是「个成员」，854 之前只数 `characterIds`） |
| `src/components/director/DirectorViewport.tsx` | 锁定守卫 ×2 |
| `src/components/director/DirectorTimeline.tsx` | 组轨道的锁定守卫 |
| `src/components/director/DirectorCurveEditor.tsx` | 组轨道的锁定守卫 |
| `scripts/verify-liblib-batch87.mjs` | ★ **老门禁的判据迁移**（见第 5b 节）：正向改成「按权威成员列表过滤」＋ 加负向断言保证旧写法清零 |

★ ★ 除这 8 个源文件外，本批还改了**一个老门禁脚本**（`scripts/verify-liblib-batch87.mjs`）
⟹ ⟹ 理由与依据见第 5b 节 ⟹ ⟹ 仓库先例：batch 854 改 `scripts/verify-liblib-batch45.py`
是**同一性质**（组模型变了 ⟹ ⟹ 断言的前提也得跟着迁）。

★ ★ **6 处选中态**（全部是「把 `characterIds` 当成员集用」）：

1. `repairDirectorSelectionState`（从文档恢复后的选中态）
2. `projectDirectorDeleteState`（一次删除操作之后存活组的选中态）
3. `selectGroup`（选组 ⟹ 选全部成员）
4. `selectTimelineTrack`（选组轨道）
5. `selectTimelineKeyframe`（选组轨道的关键帧）
6. `addTimelineTrack`（给组建轨道）＋ `recordGroupKeyframe`（记组关键帧）

⟹ ⟹ 这 6 处合起来造成了实测到的现象：**「角色＋机位」的组，一建轨道／一改位置，
选中态就塌成只剩角色** ⟹ ⟹ 源站的 `lQ(n)` 要把**复原的成员**全选上 ⟹ ⟹ 选不全。

---

## 3. 实测抓到的 5 个真缺陷（不是「听起来像」）

★ 全部来自 `probes/clone855.py` 的**真实 UI 操作**（走真实点击，不调 store），
读数在 `raw/clone-855-grouprig.json`。

1. **组 rig 只认角色** ⟹ 机位入组后，锚点／成员偏移／整体变换**全都不算机位**。
   ⟹ ⟹ 修完之后：组的锚点从「角色的位置」变成「角色＋机位的均值」
   （实测：改组位置 x ＋1.2 ⟹ 锚点只动了 **＋0.6** ＝ 半个身位 ⟹ ⟹ 锚点确实把机位算进去了）。
2. **混合组的轨道建不出来** ⟹ 文档层要求 `memberOffsets` 的键集 ⊆ `group.characterIds`
   ⟹ ⟹ 机位成员的偏移键被判成悬挂引用 ⟹ ⟹ 混合组根本加不了轨道（854 登记的「D5 遗留」）。
3. **道具不跟组动** ⟹ 源站 rig 有 `prop` 分支，clone 没有 ⟹ ⟹ 实测：组里放道具，
   组移动 ＋1.2 ⟹ **角色动了 ＋1.2，道具纹丝不动**。
4. **选中态塌成只剩角色**（6 处，见上表）⟹ ⟹ 实测：解组后 `selectedObjectIds`
   ＝ `['director-character-lead']`，**机位成员丢了** ⟹ ⟹ 源站 `lQ(n)` 要求全选。
5. **锁定守卫只认角色** ⟹ 「角色没锁、组里的机位锁了」这种混合组**仍然可以加组关键帧**。

★ 还有一个**不是缺陷、但是真差异**的发现：**rig 的应用块没有 camera 分支**
⟹ ⟹ 「机位入组后不跟组动」**不是 clone 的 bug，而是源站的行为**
⟹ ⟹ 本批按源站逐字复刻（机位不动）并登记为差异 D2。

---

## 4. 判据与证据链

| 判据 | 读什么 | 阴性 |
| --- | --- | --- |
| S1 | clone 源码里的**结构**（符号／逐字） | N1 |
| S2 | 契约里 **8 个片段** ＋ 4 条关键逐字 ＋ 任意值类名自检 | N2 |
| S3 | clone raw：**组成员**含机位 ＋ `characterIds` **由门禁自己重算**是不是派生量 | N3 |
| S4 | clone raw：**组轨道 `memberOffsets` 键集 ＝ 全部成员**（含机位） | N4 |
| S5 | clone raw：**rig 是纯平移**（同一时间点的前后对比） | N5 |
| S6 | clone raw：**机位不被 rig 带动** | N6 |
| S7 | clone raw：**道具跟组动**，且与角色的位移**相同** | N7 |
| S8 | clone raw：**解组**（组／轨道都没了、成员都在、选中态＝全部成员、`selectedGroupId` 空） | N8 |
| S9 | **三套独立实现**抽成 JS 跑 node：组数学侧 ＋ store 侧 ＋ 文档层侧 | N9 |
| S10 | 文档层：组轨道键集按全部成员校验（旧写法已移除） | N10 |
| S11 | 删除规划器：轨道 closure 按全部成员保留偏移 | N11 |
| S12 | 锁定守卫：按全部成员判锁（旧的「只认角色」写法**清零**） | N12 |
| S13 | **可达性**：根地址无参可达 ＋ 导演台可交互 | N13 |
| S14 | 选中态：按**全部成员**算（旧写法清零 ＋ 建组路径按 `members` **3 处**都算） | N14 |
| S15 | **老门禁 `87.mjs` 的判据已迁移**（旧写法清零 ＋ 有负向断言防双写放宽） | N15 |

★ **S9 的期望值不手打**：rig 的期望位置由门禁**按源站逐字公式现算**
（`采样位置 ＋ 成员偏移`；机位保持原样）⟹ ⟹ 门禁里没有一个手打的坐标常数。
★ **S3 自己重算**：「`characterIds` 是派生量」这条由门禁从 `组成员` 复算，
不采信探针写好的 flag（flag 是探针的**说法**，复算才是**事实**）。

---

## 5. 阴性对照（15/15「恰好翻一条」）

★ `probes/neg855.py` ⟹ `negative-audit.json`。
★ 全部复原后**门禁回绿** ＋ **字节级复原**校验通过。
★ ★ 源码变异**行数中性**：所有变异都是同一行内的替换 ⟹ ⟹ 文件行数不变。
★ ★★ **本批踩到的坑（已修）**：阴性脚本的「行数中性」检查**抛异常前已经把变异写进文件**
⟹ ⟹ `SystemExit` 把**文档层留在变异态**却没人发现 ⟹ ⟹ 是门禁 S10 变红才暴露出来。
⟹ ⟹ 现在 `patch_text` 在行数不中性时**当场回滚**再抛异常。

★ ★★ **N14／N15 的两个设计教训**：

1. **N14 第一版没翻红** ⟹ ⟹ 原因：S14 当时查的是「`members.map` 这个字符串**存在**」
   ⟹ ⟹ 而 store 里那行出现了 **3 次** ⟹ ⟹ 变异其中一处，S14 照样绿。
   ⟹ ⟹ 修法：S14 改成断言**出现次数 ＝ 3** ⟹ ⟹ 「只改一处」这种退化就蒙混不过去。
   ⇒ **判据问「在不在」还是「有几处」**：后者才抓得住**局部退化**。
2. **N15 第一版没翻红** ⟹ ⟹ 原因：S15 查的是「文件里含 `resolveGroupMemberRefs`」
   ⟹ ⟹ 而**注释里提到这个名字**也算命中 ⟹ ⟹ 变异只改正则、注释照旧 ⟹ ⟹ S15 照样绿。
   ⟹ ⟹ 修法：S15 改成查**活代码行里的正则字面量**（先剔掉 `//` 注释行再查）。
   ⇒ **判据查的是「符号名」还是「活代码里的字面量」**：后者才抓得住**「注释留个名字蒙混过关」**。
   ⇒ 这两条与「S14 查 `store_src`（含注释）⟹ ⟹ 旧写法残留检查会误伤注释」
   是同一族：**判据要读的东西必须与它声称的东西同粒度**。

---

## 5b. 本批引入的一条回归：老门禁 `87.mjs` 的**判据迁移**

★ ★ **这不是「旧账」** ⟹ ⟹ 它是**本批引入的新红**，已按仓库先例整改。

**怎么发现的**：回归清单从 76 条扩到 77 条后，红条从 854 的 **11 条**变成 855 的 **8 条**
（854 红的 4 条——45／79／72／75——本批变绿了）⟹ ⟹ 但**多了一条 `87.mjs`**。

**定点对照归因**（不是凭「看起来无关」打发）：

| 状态 | `87.mjs` |
| --- | --- |
| HEAD（换回本批的 8 个源文件） | **绿** |
| 工作副本（本批改动） | **红** |

⟹ ⟹ **本批引入** ⟹ ⟹ 逐条拆它的 9 条断言 ⟹ ⟹ **只有 1 条红**：
`selection repair validates group membership`。

**根因**：那条断言硬编码了 `selectedGroup.characterIds.filter(...)`
⟹ ⟹ 它假定「**组里只有角色**」⟹ ⟹ `characterIds` 就是权威成员列表。
⟹ ⟹ 但 854 已把 `characterIds` **降为派生量**（源站逐字 `U(e)`＝从 `members` 里滤出角色），
855 又把选择态改成**按全部成员**算 ⟹ ⟹ 旧写法**既漏了非角色成员、又与源站不符**。

**处置**（按仓库先例：batch 854 改 `45.py` 是同一性质）：

1. **正向**改成「按权威成员列表解析出的成员逐个过滤存在性」
   （`resolveGroupMemberRefs(selectedGroup).map(...).filter((objectId) => objectIds.has(objectId))`）。
2. ★★ **加一条负向断言**：`assert.doesNotMatch(storeSource, /selectedGroup\.characterIds\.filter\(/)`
   ⟹ ⟹ 保证旧写法**清零** ⟹ ⟹ 否则「新旧两条都写」就能让正向断言**放宽蒙混过关**。
3. **门禁 S15 钉住「迁移这件事本身」** ⟹ ⟹ 免得以后有人把老门禁改回旧写法
   （那样新语义就没人守了）⟹ ⟹ 阴性 N15 变异**老门禁脚本本身**来证明 S15 真的在读它。

★ ★★ **迁移后立刻验「门禁有牙」**：换回 HEAD ⟹ ⟹ `87.mjs` **变红**
（HEAD 的 store 还是旧写法）⟹ ⟹ 证明它真的在读本批的源码 ⟹ ⟹ 不是一条空断言。

---

## 6. 回归与受控对照

★ **回归清单**：`probes/regress855.py`（77 条：854 的 76 条 ＋ 本批 855）。
★ **受控对照**：`probes/attrib855.py`（白名单列出本批改过的**全部 8 个源文件**）。
★ ★ **换回源码后必须热机 4317**（冷编译会让第一条门禁 60s 超时 ⟹ ⟹ 假差异）。
★ ★ **中断用 SIGINT**（SIGTERM 不跑 `finally` ⟹ ⟹ 工作副本恢复不回来）。
★ ★★ **受控对照自己的一个坑（已修）**：**两遍读数不一致时不能直接当「读数变了」**
⟹ ⟹ 第一遍可能撞上 dev server 热更期（实测 `748.py` 第一遍 `KeyError: 'submitDisabled'`、
第二遍就正常）⟹ ⟹ 修法：**第三遍再判**（第三遍与第二遍相同 ⟹ ⟹ 首遍是瞬态 ⟹ ⟹ 取稳定读数）。
⟹ ⟹ ★ 这跟「一轮的差不能当因果」是同一条纪律，只是发生在**受控对照这一层**。

★ ★ **回归读数与归因**（本批实测，判据迁移**前后**各跑一轮）：

| | 854 的回归 | 855（判据迁移**前**） | 855（判据迁移**后**） |
| --- | --- | --- | --- |
| 条数 | 76 | 77 | **77** |
| 红条数 | 11 | 8 | **7** |
| 红条清单 | 831／835／741／45／79／72／75／736／748／749／782 | 831／835／741／**87**／736／748／749／782 | 831／835／741／736／748／749／782 |
| 「盯的」里红的 | 45／79／72／75 | 无 | **无** |

⟹ ⟹ 854 红的 45／79／72／75 在 855 **变绿**（854 当年已逐条整改，只是那次回归跑在整改之前）。
⟹ ⟹ 855 多出的那条 `87.mjs` 已按第 5b 节**判据迁移**整改 ⟹ ⟹ **转绿** ⟹ ⟹
红条回到 7 条，**全部是已知旧账**（`831`／`835`／`741`／`736`／`748`／`749`／`782`）。

★ ★ **受控对照结论**：**29/31 条读数逐条完全相同** ⟹ ⟹ 唯二不同**都是预期内的**：

| 条目 | HEAD 上 | 工作副本上 | 为什么是预期差异 |
| --- | --- | --- | --- |
| `855.py`（本批门禁） | rc=1，**9/15** | rc=0，**15/15** | HEAD 的源码里没有本批的改动 ⟹ ⟹ **门禁有牙** |
| `87.mjs`（老门禁，判据已迁移） | rc=1 | rc=0（PASS） | 迁移后的判据在 HEAD 上**必然红**（HEAD 的 store 还是旧写法）⟹ ⟹ **迁移后有牙** |

★ ★ 8 个源文件在受控对照结束后**逐字节复原**（SHA-256 校验 8/8 通过）。

★ ★ **构建链**：

| 检查 | 结果 |
| --- | --- |
| `npx tsc --noEmit` | ✔ 通过 |
| `npx eslint`（本批 8 个源文件） | ✔ 4 条既有告警 ⟹ ⟹ **定点对照**：HEAD 上**逐字相同** ⟹ ⟹ 非本批引入 |
| `npx next build` | ✔ 编译 ＋ TypeScript ＋ 静态生成（8 个路由）全通过 |
| `npm run assertions:check` | ✔ 801 个脚本、**0** 个空洞断言 |
| `npm run docs:check` | exit=1 ⟹ ★ 23 处断链**全部**在 `docs/user-manual/`（**他人并发编辑区**）⟹ ⟹ 本批**零提及**该目录 ⟹ ⟹ 与本批无关 |

★ ★ **eslint 那 4 条的定点对照**：本批 8 个文件上 eslint 报 2 个 error ＋ 2 个 warning
（`react-hooks/set-state-in-effect` ×2 ／ `no-unused-vars` ×1 ／ `exhaustive-deps` ×1）
⟹ ⟹ **换回 HEAD 再跑一遍** ⟹ ⟹ **同样的 4 条、同样的话**（只有行号因本批加了注释而偏移）
⟹ ⟹ **既有旧账，非本批引入** ⟹ ⟹ 本批**不动**它们（动了就是改别人的历史债）。

---

## 7. 差异登记（如实登记，不假装已对齐）

### D1 源站的 rig 是**纯平移**，clone 的**交互路径**带旋转增量 ＋ 缩放比

* ★ 源站逐字：rig 的位置公式里**没有**旋转／缩放；组轨道能编辑的属性**只有 position**
  （`speedCurveSegments:["position"]`、`propertyKey:"position"`）。
* ★ clone 的 `applyDirectorGroupTransform`（**交互路径**：组检查器里改位置／旋转／缩放）
  会按「旋转增量 ＋ 缩放比」把成员绕锚点转过去。
* ★ 更根本的一条：**源站的组根本没有 transform 字段**
  （源站建组逐字：`{id: rz(…), label: t.ref, characterIds: …, members: n}`）⟹ ⟹
  源站的「组位置」永远是**成员位置派生**出来的（`H(e,e=>L(t,e))`）。
* ⟹ ⟹ **本批只把 rig（时间轴回放）这条路径对齐成纯平移**（`applyDirectorGroupRig`），
  **交互路径保持原样** ⟹ ⟹ 因为源站交互路径的逐字**还没钉死**
  （`onTransformCommit` 的 `isGroup` 参数那条分支还没追到底）⟹ ⟹ **独立批次**。

### D2 源站的 rig **没有 camera 分支**（机位入组不跟组动）

* ★ 源站的解析器认 camera（`"camera"===r`），但应用块**只处理 character／prop／emptyObject**。
* ★ 源站里机位跟组走的是**另一条路**：相机的 `followTargetId` 指向组，
  源站按**各组的锚点**重算相机绑定（`lV`：`t.characterGroups.forEach(e=>{let r=H(e,e=>L(t,e));…})`）。
* ⟹ ⟹ 本批**按源站逐字复刻**（机位不被 rig 带动）⟹ ⟹ 并登记：
  「源站是不是有意如此」尚未取证 ⟹ ⟹ **独立批次**。

### D3 源站的 `memberOffsets` 键是 `kind:id`，clone 用裸 object id

* ★ 源站逐字：`e[N(n)]={…}`（`N(e)`＝`kind:id`）。
* ★ clone 的对象 id 是**类别前缀**的（`director-character-lead`／`director-camera-main`／…）
  ⟹ ⟹ 全局唯一 ⟹ ⟹ 裸 id 与 `kind:id` **语义等价**。
* ⟹ ⟹ **本批不改键方案**（改了要动 4 条消费端 ＋ 文档 schema）⟹ ⟹ 只登记。

### D4 源站允许**相机跟随组**（`followTargetId` → 组锚点），clone 不允许

* ★ 源站逐字：`lV` 把 `groupPositions`（各组锚点）喂给相机的 follow 解析。
* ★ clone 的相机 `followTargetId`／`lookAtObjectId` 只能指向**对象**，没有「指向组」这条路。
* ⟹ ⟹ 这是**能力缺口**（不是 bug）⟹ ⟹ **独立批次**。

### D5 源站的组**锁定指示**是「全部成员都锁才算锁」，clone 是「任一成员锁就拒绝」

* ★ 源站逐字：`locked:t.length>0&&t.every(e=>e.locked)`。
* ★ clone 的 `directorGroupHasLockedMember` 是**写入守卫**（「任一成员锁住 ⟹ 拒绝写组关键帧」），
  语义方向相反 ⟹ ⟹ 源站那一句是**组的锁定指示**（树上的锁图标，＝ 854 遗留 N2／N3 的范畴）。
* ⟹ ⟹ 本批只把守卫的**成员集合**对齐（任意类别），**判定口径保持 clone 原样**。

---

## 8. 与他人并发区的边界

★ 本批只碰上表那 8 个源文件 ＋ `scripts/verify-liblib-batch855.py` ＋
`scripts/verify-liblib-batch87.mjs`（判据迁移，见第 5b 节）＋
`docs/research/liblib-canvas-batch855-2026-10-01/**`。
★ **不碰**：`src/app/clones/`、`src/lib/clonePages.ts`、`src/components/CloneSiteNav.tsx`、
`docs/CLONE_PAGES_INDEX.md`、`docs/user-manual/**`、`src/components/jimeng/*`、
`src/store/jimengStore.ts`、`src/app/page.tsx`。
★ `stash@{0}`（`in-progress-edit-for-revert`）**全程未碰**。

---

## 9. 用户可达

★ 沿用 854 建立的中心文档：`docs/research/LIBTV_CLONE_REACHABILITY.md`。
★ 本批复跑 `probes/reachability855.py` ⟹ `raw/reachability-855.json`：
根地址 `http://localhost:4317/`（**无参**）⟹ hover 画布上的「导演台」节点 ⟹
点「打开导演台 →」⟹ 场景树 5 行／rail 7 项／28 个可交互元素；
另有角色大编辑器、资产管理两条路径。
★ 门禁 S13 把「根可达」钉住。

---

## 10. 产物清单

```text
docs/research/liblib-canvas-batch855-2026-10-01/
├── README.md                       ← 本文件
├── runtime-audit.json              ← 门禁 15/15
├── negative-audit.json             ← 阴性 15/15「恰好翻一条」＋ 复原回绿
├── probes/
│   ├── extract855_contract.py     ← 源站契约提取（8/8 唯一命中）
│   ├── clone855.py                 ← clone 实测（真实 UI）
│   ├── reachability855.py          ← 根可达普查
│   ├── neg855.py                   ← 阴性对照
│   ├── regress855.py               ← 回归清单（77 条）
│   └── attrib855.py                ← 受控对照（白名单 ＝ 8 个源文件）
├── raw/
│   ├── source-855-contract.json    ← 源站逐字 8 片段
│   ├── clone-855-grouprig.json     ← clone 实测读数
│   ├── reachability-855.json       ← 根可达读数
│   └── attrib-855.json             ← 受控对照读数
└── images/855clone_*.png  855reach_*.png
```

---

## 11. 本批的「自我清算」

★ ★ **一条设计失误，被上一批的门禁当场抓住**：
我一开始把 store 的 `resolveGroupMemberRefs` **收敛成「转发给组数学模块」**
（理由：避免同一份规则出现两份实现）⟹ ⟹ 结果 **batch 854 的门禁 S1 与 S10 立刻变红**：

* S1 断言 store 里有 `export interface DirectorSceneMemberRef` ⟹ ⟹ 我把它改成了 type 别名；
* S10 要把「store 的这一份」与「文档层的那一份」**各自抽出来跑 node 交叉验证**
  ⟹ ⟹ 一旦 store 的变成「转发」，抽出来就是一行调用 ⟹ ⟹ node 里找不到被调用的函数 ⟹ ⟹ 报错。

⟹ ⟹ **结论：上一批刻意保留的「两份独立实现」不是冗余，是交叉验证的前提。**
⟹ ⟹ 本批的处置：**把 store 那份还原成 854 的独立实现**（854 门禁恢复 11/11），
⟹ ⟹ 并把本批的门禁 S9 **升级成三套实现交叉验证**
（组数学侧 ＋ store 侧 ＋ 文档层侧）⟹ ⟹ 交叉验证比上一批**更强**，而不是更弱。
⟹ ⟹ ★ **「消除重复」与「保留可交叉验证的重复」是一对矛盾** ⟹ ⟹
**在有交叉验证门禁的地方，不要为了「看起来干净」把实现合并掉。**

★ ★★ 另一条：**探针自己也会骗人**。本批的受控检查第一版有**两个**采样缺陷：

1. 「改前」读数在 `t=4`、「改后」在 `t=0` ⟹ ⟹ 成员**自身轨道**的贡献混了进来
   ⟹ ⟹ 修法：**前后读数取在同一个时间点**。
2. 改写 `timeline` 之后**没有重新采样** ⟹ ⟹ 运行时对象是 `setTimelineTime` 时算出来的，
   不是 `timeline` 的派生值 ⟹ ⟹ 读到的是**旧值**。
   ⟹ ⟹ 这两处都是「读数看着合理、但结论是假的」⟹ ⟹ 属于最贵的一类失败。

★ ★★★ **第三条（本批撞上的，关于「判据自己」）**：

★ **一条门禁红了，先别急着改实现 —— 先问「它红是因为实现错了，还是因为它的前提过期了」。**
⟹ ⟹ 本批的 `87.mjs` 红了 ⟹ ⟹ 我第一反应是「我又改坏了」⟹ ⟹ 但**定点对照**证明
是**本批引入**（HEAD 绿、工作副本红）⟹ ⟹ 逐条拆它的 9 条断言 ⟹ ⟹ **只有 1 条红**，
而那一条红在的**原因**是：它断言的 `selectedGroup.characterIds.filter(...)`
**本身就是个过期的前提**（854 起 `characterIds` 已是派生量）⟹ ⟹
**它红的不是「实现错了」，是「判据的前提过期了」**。
⟹ ⟹ 这两种红的**处置完全相反**：前者改实现，后者**迁移判据**
（仓库先例：batch 854 改 `45.py` 就是这一类）⟹ ⟹ 弄反了就会**把一个对的实现改成错的**。
⟹ ⟹ ★ **通式**：门禁红了 ⟹ ⟹ 先拆到**那一条** ⟹ ⟹ 再问「这条断言的前提，
   在**源站逐字**里还成立吗」⟹ ⟹ 成立 ⟹ ⟹ 改实现 ⟹ ⟹ 不成立 ⟹ ⟹ 迁移判据
   （**且必须加负向断言**保证旧写法清零 ⟹ ⟹ 否则「新旧都写」就能蒙混过关）。

★ ★★ **第四条**：迁移判据之后**必须立刻验「门禁有牙」** ⟹ ⟹ 本批换回 HEAD 跑 `87.mjs`
⟹ ⟹ **变红**（HEAD 的 store 还是旧写法）⟹ ⟹ 证明它真的在读本批的源码
⟹ ⟹ 不是一条「怎么都能过」的空断言。

---

## 12. 下一批候选（本批自开遗留）

* ★ **D1**：源站交互路径的组变换（旋转／缩放）逐字取证 ⟹ 然后决定 clone 的交互路径怎么改。
* ★ **D2**：源站 rig 缺 camera 分支是**有意**还是**漏写** ⟹ 需要源站的运行期证据。
* ★ **D3**：`memberOffsets` 键方案（裸 id ⟹ `kind:id`）是否值得改。
* ★ **D4**：相机跟随组（`followTargetId` → 组锚点）的能力补齐。
* ★ **D5**：组的**锁定指示**（源站 `every`）与 clone 的**写入守卫**（`some`）的分工。
* ★ 854 遗留：N1（源站场景树是平铺列表）／ N2·N3（可见·锁定指示）／「添加角色」8 个预设只是占位提示。
* ★ **本批自开**：**老门禁的「旧前提」普查** ⟹ ⟹ `87.mjs` 是本批撞上的第 1 条
  （判据已迁移，见第 5b 节）⟹ ⟹ 其余门禁是否还有同型「假设组里只有角色」的断言，
  需要按主题扫一遍（与 831 的 S14 历史债同一性质）。
* ★ 旧账：782／736／748／749／741／835／831／91／826／830。
