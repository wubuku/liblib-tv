# Batch 854 — 导演台「组模型的成员语义」

> 本批靶子 ＝ 导演台**组**这个东西本身：谁能进组、组成员在树上怎么显示、树里怎么多选。
> 上一批（853）做的是**打组／解组的快捷键接线**；本批把**组模型**本身对齐源站。
>
> ★ 源站逐字依据（机器提取，**17 个片段全部唯一命中**）：
> `raw/source-854-contract.json`
>
> ★ 本批的**用户新要求**也一并落地：**「所有复刻成果必须从根目录用户可达」**
> ⟹ ⟹ 中心说明文档 `docs/research/LIBTV_CLONE_REACHABILITY.md`（见 §10）。

---

## 1. 本批要解决的三个差异

| 编号 | 差异 | 源站逐字依据 |
| --- | --- | --- |
| D1 | clone 的组**只收角色**；源站的组能装**任意场景成员**（含机位） | `function sg(e){return"character"===e\|\|"prop"===e\|\|"emptyObject"===e\|\|"camera"===e}` |
| D2 | clone 的组**建出来是折叠的**；源站**默认展开** | `expanded:!!F\|\|!j.has(e.id)`（`j` 是**被折叠**的组集合） |
| D3 | clone 的树**只有 ⇧ 能加选**、且**只对角色**生效；源站 **⇧／⌘／Ctrl** 三者皆可、且对**可分组成员**生效 | `let r=t.shiftKey\|\|t.metaKey\|\|t.ctrlKey;` ＋ `sg(e.category)?{additive:r,individual:!0}:void 0` |

★ D1 与 D3 **必须同做**才自洽：能加选机位、却不能把机位放进组，是半吊子。

★ D2 顺带牵出一个**实现细节**：源站的缩进是**做在行内**的（见 §5）。

---

## 2. 契约提取（**17 个片段全部唯一命中**）

`probes/extract854_contract.py` ⟹ `raw/source-854-contract.json`
（源站 chunk `/tmp/liblib_srcjs2/0fmehki05gkzw.js.js`，1,018,130 字节）

| 片段 | 作用 |
| --- | --- |
| `N(e)` ＝ `kind:id` | 成员的**去重键**（跨组唯一性也用它） |
| `O(e)` | **权威成员列表**：`members` 优先 ＋ `characterIds` 兜底 ＋ 按 `N(e)` 去重 |
| `U(e)` | `characterIds` ＝ 从 `O(e)` 里**派生**的角色子集 |
| `lB(...)` | 按场景集合过滤 ＋ 去重 |
| `lQ(...)` | 选择态：`selectedSceneMembers` ＋ `selectedCharacterIds` |
| `sg(e)` | **可分组的类别**：character／prop／emptyObject／camera |
| `CREATE_CHARACTER_GROUP` case | 建组成员取 **`selectedSceneMembers`**（任意场景成员） |
| `UNGROUP_CHARACTER_GROUP` case | 解组按 `O(r)` 复原成员 |
| 树行 `onClick` | 加选修饰键 ＝ **⇧／⌘／Ctrl**，且只对 `sg` 类别生效 |
| `K=new Set(u.map(N))` | 树里当前选中的场景成员集合 |
| `W=[...U,...H,...G,...V].filter(...)` | 树里**已选的可分组成员**过滤 |
| `expanded:!!F\|\|!j.has(e.id)` | ★ **默认展开** |
| `(F\|\|!j.has(e.id))&&r.map(...indent:!0...)` | ★ 成员是**缩进子行** |
| `visible/locked` 按全部成员算 | 组的可见／锁定是**成员聚合**出来的 |
| `lT(e)` | 组名 ＝ `i18n(canvas:nodeTypeGroup)` ＋ 序号 |
| 组的 Group 图标那一支 | 树里组行的折叠按钮与图标 |

★ ★ **纪律**：期望值**不手打**。门禁的每条判据要么读**入库的源站原文**，
要么读**源站实测的 raw**。

---

## 3. 源站实测（`probes/source854_groupmembers.py` ⟹ `raw/source-854-groupmembers.json`）

★ 有副作用（会建组／解组），**末尾自动复原**（读数 `⑦结束时标签` ＝ `①基线标签`）。

### 3.1 关键读数

- 源站的场景树是**平铺列表**：`①基线节标题` ＝ `[]`（**没有**类别分节）
- 基线三行 x **全部 96**（`机位1`／`机位2`／`角色A`）
- **点机位 ＋ ⌘+点角色 ⟹ 按 ⌘G** ⟹ 树上变成 4 行：
  `['分组1', '机位1', '角色A', '机位2']`
- 类别：`['other', 'camera', 'character', 'camera']`
  ⟹ ⟹ ★★ **组里同时有机位和角色**（跨类别）
- x：`[96, 112, 112, 96]`
  ⟹ ⟹ 两名成员**各缩进 +16**，未入组的「机位2」仍平铺在 96
- ⌘⇧D ⟹ **逐字回到基线**

### 3.2 ★★ 「缩进 +16」到底是**哪一种**缩进（口径问题）

★ 第一版探针量的是 clone 的**行元素** x，源站量的是**标签 span** 的 x
⟹ ⟹ **口径不同，不能直接相减**（这正是本批踩的坑，见 §5）。

★ 于是源站探针补了**第二层几何**（`rowX`），两边**同粒度**各比各的：

| 层 | 源站 | 结论 |
| --- | --- | --- |
| **标签文本 x** | 组行 96 ⟹ 成员 112（**+16**） | 缩进是**看得见的**文本偏移 |
| **行元素 x** | 组行 56 ⟹ 成员 56（**0**） | ★ 缩进**不是**行整体右移 |

⟹ ⟹ **源站的缩进是「做在行内」的**：行整体不动，行的**前导元素**从 16px 变 32px。
★ 这条决定了 clone 该怎么改（§5）。

---

## 4. clone 实施

### 4.1 改动清单

| 文件 | 改动 |
| --- | --- |
| `src/store/directorStore.ts` | `DirectorCharacterGroup` 加 `members?`；新增 `DirectorSceneMemberRef`／`DIRECTOR_GROUPABLE_KINDS`／`resolveGroupMemberRefs`；`groupSelectedCharacters` 改为**收任意可分组成员**、组名改 `分组N`、`characterIds` 降为**派生量**；`toggleObjectSelection` 不再限定角色 |
| `src/lib/directorProjectDocument.ts` | 组文档加**可选键** `members`（旧工程照旧可读）；`expectGroupMembers`；`resolveDirectorGroupMembers`（导出）；`validateReferences` 改按**权威成员列表**校验，并加「`characterIds` 必须等于成员里的角色子集」的一致性断言 |
| `src/components/director/DirectorObjectTree.tsx` | 组**默认展开**（`useState(true)`）；成员来自**权威成员列表**、图标按类别；入组成员**从类别分区排除**；树行 **⇧／⌘／Ctrl** 加选；组成员行加 `data-director-group-member-kind`；★ **成员行前导按源站重写**（§5） |
| `src/lib/directorDeletePlanner.ts` | 删成员时按**权威列表**过滤，**两个字段一起写回**；级联删按**全部成员**（任意类别） |
| `src/lib/directorClipboard.ts` | 选组取**权威成员列表**；贴组**重映射 `members`** |
| `src/lib/directorWholeProjectDuplicate.ts` | 复制组时**重映射 `members`** |
| `src/lib/directorProjectRuntimeAdapter.ts` | 文档 ⟹ 运行时**把 `members` 带回来**（否则刷新后机位／道具会掉出组） |

★ ★ **`members` 是权威、`characterIds` 是派生**（源站逐字 `O(e)`／`U(e)`）。
★ 名字 `groupSelectedCharacters` **没改**（历史遗留，多条既有门禁引用它）⟹ ⟹ 只改语义。

### 4.2 clone 实测（`probes/clone854.py` ⟹ `raw/clone-854-groupmembers.json`）

★ 走**真实 UI**（不调 store）：点机位行 → **⌘+点**角色行 → 点「打组」→ 点「解组」；
另一轮用 **⇧+点**验第二个修饰键。

| 读数 | 结果 |
| --- | --- |
| 组标签 | `分组1` ＝ 源站实测的组标签 ✅ |
| 组成员类别集合 | `['camera', 'character']` ＝ 源站 ✅ |
| 成员默认展开 | 展开容器 1 个、成员行 2 行 ✅ |
| 入组后剩余类别分区 | 只有 `prop`（3 行）✅ 成员**不在自己的分区里**了 |
| 解组后 | 组数 0、对象行**逐个**回到基线 ✅ |
| ⇧+点 | 选中 2 个道具 ✅ |

---

## 5. ★★ 顺带整改：一个**看得见的糊弄点**

★ 实施中途发现：clone 的**组成员文本比组标题还靠左 17px** ⟹ ⟹
**视觉上「成员完全没有缩进」**（因为组行前面有个 24px 的折叠按钮，成员行没有）。

★ 根因：clone 用**容器的 `pl-4`** 做缩进，而组行与成员行的**前导结构不同** ⟹ ⟹
容器级缩进对两者产生的偏移**不等**。

★ 修法（照源站的结构）：**缩进做在成员行内部**——
`border-l-2 border-transparent`（与组行同一条左边框盒）＋ 24px 空位（对齐折叠按钮位）
＋ **16px 缩进**（源站的缩进量）。

★ 改完的**同粒度**读数：

| 层 | 源站 | clone（改后） |
| --- | --- | --- |
| 标签文本 x 偏移 | **+16** | **+16** ✅ |
| 行元素 x 偏移 | **0** | **0** ✅ |

★ ★ 顺带把源站的「组下**没有竖线**」也对上了（容器不再画 `border-l`）。

---

## 6. ★★ 回归清单扩大 → 新出现的红 → **定点归因** → 已整改

★ 853 的回归清单里 **19 条 `.mjs` 静态门禁被漏掉了**（那个跑法只找 `.py`）
⟹ ⟹ 本批把 `.mjs` 也纳入（`node` 直跑）⟹ ⟹ 清单从 62 涨到 **76 条**。

★ 扩大清单后**新出现 4 条红**：`45`／`72`／`75`／`79`。

★ ★ **归因（`probes/attrib45727579.py` ⟹ `raw/attrib-45-72-75-79.json`）**：
把这三个源文件**按字节换回 HEAD** 再跑一遍 ⟹ ⟹

| 门禁 | HEAD 上 | 工作副本上 | 归因 |
| --- | --- | --- | --- |
| `45.py` | 绿 | 红 | ★ **本批引入** |
| `72.mjs` | 绿 | 红 | ★ **本批引入** |
| `75.mjs` | 绿 | 红 | ★ **本批引入** |
| `79.mjs` | 绿 | 红 | ★ **本批引入** |

★ 根因**是同一类**：`members` 是权威列表，但**删除规划器／粘贴器／整工程复制
只重映射 `characterIds`、不碰 `members`** ⟹ ⟹ 两个字段打架 ⟹ ⟹
本批新加的一致性断言把它们**拦下来了**（断言是有牙的）。

★ 整改（§4.1 的后四行）：三处都改成**按权威列表处理**，并且
**两个字段一起写回**；另修了 `45.py` 的**前提**——它假设「组建出来是折叠的」，
而源站逐字与实测都证明**默认展开** ⟹ ⟹ 断言改成「默认展开、点一下才收起」，
且**限定在该组内**计数。

★ ★ 顺带一个**真坑**：`.mjs` 门禁用 **node 直跑** ⟹ ⟹
`@/lib/...` **别名解析不了**（只有 `import type` 才被擦除）⟹ ⟹
本批第一次写成别名导入时 `72.mjs` 直接报 `ERR_MODULE_NOT_FOUND`
⟹ ⟹ 改成相对路径 `./directorProjectDocument.ts`（同目录其他文件的既有写法）。

---

## 7. 验收

| 环节 | 结果 |
| --- | --- |
| 门禁 `scripts/verify-liblib-batch854.py` | **11/11** |
| 阴性 `probes/neg854.py` | **12/12**，每条**恰好**翻一条判据，**字节级**复原 |
| 回归 `probes/regress854.py` | 76 条；红条**全部**是已知旧账（§7.2） |
| 受控对照 `probes/attrib854.py` | **28/30 条读数逐条完全相同**，唯二不同的两条都是**预期内**的（见下） |

★ ★ 受控对照的两条差异（`raw/attrib-854.json`）：

| 门禁 | HEAD 上 | 工作副本上 | 为什么**应该**不同 |
| --- | --- | --- | --- |
| `854.py` | **9/11**（红） | **11/11**（绿） | ★ 本批的门禁在 HEAD 上必然红（结构／文档层两套实现都不存在）⟹ ⟹ **门禁有牙** |
| `45.py` | 红（`assert group_expanded.count() == 1`） | 绿 | ★ HEAD 上那句断言编码的是**旧前提**（「组默认折叠」）⟹ ⟹ 本批按源站逐字改成「默认展开」⟹ ⟹ 读数**必然**不同 |

★ ★ 受控对照本身踩了三个坑（已修进脚本，并写进 agent memory）：
① **白名单必须列全部 7 个改动文件** —— 只换回 3 个 ⟹ 消费者仍 import 新导出
⟹ ⟹ **整站 500** ⟹ ⟹ 浏览器门禁全变成 60s 超时 ⟹ ⟹ 读数全是假的；
② 换回源码后必须**热机 4317**（冷编译会让第一条门禁超时）；
③ 要中断脚本用 **SIGINT**（让 `finally` 跑到）⟹ ⟹ SIGTERM 会让工作副本**恢复不回来**
⟹ ⟹ 本批为此**丢过一次 3 个文件的改动**（靠重放编辑记录恢复 ⟹ ⟹
重跑 clone 探针，**14 个顶层键逐字一致** ⟹ ⟹ 恢复是忠实的）。

### 7.1 门禁判据分工（★ 各条读的字段互不重叠）

| 判据 | 读什么 |
| --- | --- |
| S1 | clone 源码里的**结构**（符号存在性） |
| S2 | 契约 **17 个片段** ＋ 关键逐字 |
| S3 | 源站／clone 的**缩进量**（**同粒度**两层各比各的） |
| S4 | clone raw：组成员 ＝ 被选中的那些对象（id＋kind 逐个相等） |
| S5 | clone raw：**默认展开** |
| S6 | clone raw：入组后成员**不在类别分区** |
| S7 | clone raw：解组**逐字回到基线** |
| S8 | clone raw：**⇧ 加选** |
| S9 | **源站** raw：跨类别成组 ＋ 缩进 ＋ 回到基线 |
| S10 | 文档层**两套独立实现**（store ＋ document）交叉验证 |
| S11 | **可达性** raw：根地址无参可达 ＋ 导演台可交互 |

### 7.2 已知旧账（**在 HEAD 上也是红的** ⟹ 不是本批引入）

`831`（S14 历史债）／`835`（C3／C4）／`741`（C1／C3）／`736`（C1／C3／C4／C7）／
`748`（C1／C3／C4）／`749`（7／9）／`782`（17 条行号漂移债）。

★ **另**：第 2 轮回归里 `36`／`47`／`48`／`49`／`50` 曾一起红 ⟹ ⟹
定点复跑**全部转绿**（第 1 轮它们是绿的）⟹ ⟹ **环境瞬态**
（当时另一位开发者正在写 `src/lib/clonePages.ts`，dev server 在重编译）
⟹ ⟹ **不是本批引入**。⟹ ⟹ 「一轮的差」不能直接当因果。

---

## 8. 差异登记（**如实标注，不假装已对齐**）

| 编号 | 差异 | 说明 |
| --- | --- | --- |
| N1 | 源站的场景树是**平铺列表**，clone 是**按类别分节** | 源站实测 `①基线节标题` ＝ `[]`；clone 有「角色／场景物体」分节。⟹ 要全面对齐得重构树的布局（影响多条门禁）⟹ ⟹ **本批只登记** |
| N2 | 源站组行有**可见／锁定**聚合指示，clone 的组行没有 | 源站逐字 `visible:0===t.length\|\|t.every(e=>e.visible),locked:t.length>0&&t.every(e=>e.locked)`；clone 的组行只有成员数与删除按钮 |
| N3 | 源站的组成员行右侧有**可见／锁定**按钮，clone 没有 | 源站截图可见（角色A 行右侧两枚） |
| N4 | clone 的组**轨道**仍只按**角色成员**算 | 改成「全部成员」会让已有组轨道立刻校验失败 ⟹ ⟹ 留作下一批（见 §9 L1） |
| N5 | clone 的组行**前导结构**与源站不同（24px 折叠按钮 vs 16px） | ⟹ ⟹ 组的**绝对**文本 x 与源站不同；**相对**缩进已对齐（§5） |
| N6 | 源站 i18n 里另有一套组名模板 `角色组{index}` | 属**另一条**路径；导演台建组这条实测是 `分组N` |

---

## 9. 遗留

| 编号 | 事项 | 归属 |
| --- | --- | --- |
| L1 | 组轨道（`groupTracks`）改按**全部成员**算 | 下一批（要同时处理轨道的 `memberOffsets` 校验） |
| L2 | 源站**平铺列表**布局（§8 N1） | 独立批次（树布局重构） |
| L3 | 组行的可见／锁定聚合指示（§8 N2／N3） | 独立批次 |
| L4 | 852 登记的 D3 路径草稿提交守卫运行时取证 | 独立批次 |
| L5 | 852 的 ⌘T／⌘Y 修饰键差异 | 独立批次 |
| L6 | 831 的 S14 历史债 | 独立批次 |
| L7 | 850 的「点左列分段会不会把取景重置为全身」复验 | 独立批次 |
| L8 | 旧账：`782`／`736`／`748`／`749`／`741`／`835`／`831` | 各批自己清 |
| L9 | `87`／`91` 的 TransformControls 瞬态 | 可仿 batch 50 收进过滤名单 |
| L10 | 826 的素材库 popover 20px 差；830 的 ⌘C 复制／撤销栈／时间轴缩放 | 独立批次 |

---

## 10. ★ 用户可达性（用户新要求）

★ 用户要求：「所有完成的克隆成果都必须通过克隆网站根目录**用户可达**，
并且文档中说明如何『可达』、用户可以如何进行交互测试」。

★ 本批的交付：

1. **中心说明文档** `docs/research/LIBTV_CLONE_REACHABILITY.md`
   ⟹ ⟹ 写了「怎么把 clone 跑起来」「根目录长什么样」「三条主干路径（导演台／
   角色大编辑器／资产管理）怎么点」「怎么交互测试（手动／跑门禁／自己写探针）」
   ⟹ ⟹ 以及**如实登记**了「不在根可达范围内的东西」（FrameOS／即梦／`/project`）。
2. **已挂进索引** `docs/research/README.md`（Route Research → LibTV 段 ＋ Batch History 段）。
3. **实测证据** `probes/reachability854.py` ⟹ `raw/reachability-854.json`
   ⟹ ⟹ 三条路径**每一条都是点完再读**（★「这个入口没有 X」必须真的点一下才算数）。
4. **门禁 S11** 把「根地址无参可达」钉成一条判据（`N11` 可把可达性读数改成 false ⟹ S11 翻红）。

★ 实测结果：导演台**不换 URL**（盖在画布上），**7 个 rail 项／5 个对象树行／
28 个可交互元素**；角色大编辑器**左列 5 段**、官方库 **17 张**角色卡。

★ ★ **与他人并发区的关系**：另一位开发者正在做 `src/app/clones/page.tsx` ＋
`src/lib/clonePages.ts`（**站内的**复刻页面索引路由）。
本批**没有碰他的任何文件**（他那两个文件当时还处于**语法未闭合**的半成品状态，
因此 `npx tsc --noEmit` 会报他的错 ⟹ ⟹ 本批的类型检查**只统计自己文件的错误**：
**0 个**）。两份产物互补：他的在**运行时**给用户一个页面清单，
本批的在**文档**里讲清「怎么到达 ＋ 怎么测」。

---

## 11. 证据索引

| 文件 | 内容 |
| --- | --- |
| `raw/source-854-contract.json` | 源站逐字契约（17 片段，全部唯一命中） |
| `raw/source-854-groupmembers.json` | 源站实测（跨类别成组／缩进两层／复原） |
| `raw/clone-854-groupmembers.json` | clone 实测（真实 UI 打组／解组／⇧ 加选） |
| `raw/clone-854-reachability.json` | 根地址无参可达 ＋ 导演台 21 个可交互元素 |
| `raw/reachability-854.json` | ★ 三条路径的可达性普查读数 |
| `raw/attrib-45-72-75-79.json` | ★ 四条新红的定点归因（HEAD 绿 / 工作副本红 ⟹ 本批引入） |
| `raw/attrib-854.json` | 受控对照（HEAD vs 工作副本逐条读数） |
| `runtime-audit.json` | 门禁 11/11 |
| `negative-audit.json` | 阴性 12/12 |
| `images/854src_*.png` | 源站截图（基线／两选／成组／解组／复原） |
| `images/854clone_*.png` | clone 截图（基线／选机位／⌘ 加选／成组／解组／道具组） |
| `images/854reach_*.png` | 根页／导演台／角色大编辑器／资产管理 截图 |

---

## 12. 复现步骤

```bash
export PATH="$HOME/.nvm/versions/node/v24.6.0/bin:$PATH"
export PATH="$HOME/.pyenv/shims:$PATH"
cd <仓库根>

# ① 契约提取（需要源站 chunk /tmp/liblib_srcjs2/0fmehki05gkzw.js.js）
python3 docs/research/liblib-canvas-batch854-2026-10-01/probes/extract854_contract.py

# ② 源站实测（★ 有副作用：会建组／解组，末尾自动复原）
python3 docs/research/liblib-canvas-batch854-2026-10-01/probes/source854_groupmembers.py

# ③ clone 实测（需要 4317 在跑）
python3 docs/research/liblib-canvas-batch854-2026-10-01/probes/clone854.py

# ④ 可达性普查（★ 三条路径，每条都点完再读）
python3 docs/research/liblib-canvas-batch854-2026-10-01/probes/reachability854.py

# ⑤ 门禁
python3 scripts/verify-liblib-batch854.py

# ⑥ 阴性对照
python3 docs/research/liblib-canvas-batch854-2026-10-01/probes/neg854.py

# ⑦ 回归 ／ 受控对照
python3 docs/research/liblib-canvas-batch854-2026-10-01/probes/regress854.py
python3 docs/research/liblib-canvas-batch854-2026-10-01/probes/attrib854.py
python3 docs/research/liblib-canvas-batch854-2026-10-01/probes/attrib45727579.py
```

★ 4317 是**多人共用**的 ⟹ ⟹ **不要并发跑多个浏览器脚本**。
