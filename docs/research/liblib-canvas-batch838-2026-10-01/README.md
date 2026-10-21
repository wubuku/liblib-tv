# batch 838 — 把默认角色名改成源站口径「角色A」，并**更正 batch 837 的一条结论**

日期：2026-10-22
范围：clone 导演台（默认角色命名）＋ 三处旧门禁期望值 ＋ batch 837 的一条结论更正
上一批：batch 837（`9565b0f3`，默认机位名「机位01 · 对峙中景」→「机位1」）

---

## 一、这批为什么存在：batch 837 的结论**有一条是错的**

batch 837 的 README 里写着：

> 「源站画布上真实显示的镜头名是『**S83·镜2**』⟹ 源站用的是另一套命名体系」

本批去查「S83·镜2」的**来源**，查穿了：

**它是用户上传的一个 mp4 文件名。**

权威证据（`api/canvas/project/detail-by-space` 的响应，`raw/source-838-detail-by-space.json`）：

```json
{"nodeKey":"v-3CmzlptLJl","type":3,"name":"S83·镜2",
 "data":"{\"type\":\"video\",\"name\":\"S83·镜2\",
          \"alt\":\"S83·镜2.mp4\",
          \"action\":\"video_resource\",
          \"uploaded\":true,
          \"generatorType\":\"default\", …}"}
```

★ 三个字段合起来说明一切：`alt` 带 `.mp4` 扩展名 ⟹ 它是**上传文件的原名**；
`action` 是 `video_resource` ⟹ 它是一个**视频资源节点**；
`uploaded: true` ⟹ 它是**上传**来的，不是系统生成的。

★ 而「S83·镜2」在画布上的**位置**（x 113, y 122）也在一个 `react-flow__node-video` 节点里
（盒 232×133，文字「S83·镜2」＋「864 × 496」尺寸标注）——**是节点标题**。

⟹ ★★ **batch 837 那句「源站用 S83·镜2 体系」不成立**，本批更正。
（旧批次 README 不可重写 ⟹ 更正写在本文件 ＋ 台账。）

### ★★ 顺带查清的第二件事：**源站根本没有「镜头」实体**

导演台节点的权威数据 `compositionData` 的顶层只有六个键：

| 键 | 内容 |
| --- | --- |
| `characters` | 角色数组（`label` = 「角色A」） |
| `characterGroups` | 空数组 |
| `cameras` | 机位数组（`label` = 「机位1」「机位2」） |
| `props` | 空数组 |
| `animation` | `version` / `duration` / `motionPaths` / `characterTracks` / `propTracks` / `cameraTracks` / `groupTracks` / `activeCameraTrackId` |
| `environment` | 全景球、地面、天空等 |

★ **没有 `shots`**，`animation` 里也没有任何 shot 类键。

⟹ ★★ clone 的 `shots[]`（镜头层）是**借自 StoryAI 上游**的分层设计
（batch 96 的 PLAN.md 自己就写明了：「固定 StoryAI submodule 提供了独立 `DirectorCameraShot`…
本批只借鉴这种分层方法，**不把上游 schema、CSS 或行为称为 LibTV 源站事实**」）⟹

⟹ ★★ **镜头命名没有源站口径可对齐** ⟹ 本批**不改**它
（不去制造一个「对齐了源站镜头名」的假结论）。

---

## 二、源站实测：角色的默认命名规则

### 2.1 决定性实验（单趟闭环）

在源站点「添加角色」⟹ 它打开的是一个**体型预设面板**（11 枚：本地上传／标准男性／标准女性／
健硕／纤细／少年／儿童／宽厚／二头身／群众 (3x3)／几何模型）⟹ 选一枚体型 ⟹ 源站**新建一个角色** ⟹
读右栏「名称」输入框的值 = 「**角色B**」（进站基线里那个叫「角色A」）。

⟹ ★★ 默认名规则 = 「**角色 + 字母序号**」。

### 2.2 这条读数是**单趟闭环**出来的（★ 前面踩了五次坑）

| 探针 | 出了什么问题 | 怎么修的 |
| --- | --- | --- |
| v9 | 读到「角色B」了，但**下一趟进站它没了** ⟹ 跨趟状态与读数无法对齐 | 改成**单趟**闭环 |
| v11 | 单趟闭环的**读数器口径坏了**：把**体型预设面板的行**当成了「新增的角色行」 ⟹ 于是去右键「标准男性」⟹ 副作用：右键菜单弹出并**停留在页面上** | ★ 收窄口径 |
| v15 | 收窄口径**还不够**：面板是**浮层**，它的行也在 `x∈[80,240]` 里 ⟹ 还是混进来了 | ★★ 改用 **class** 判别 |
| v16 | ★ **class 口径在「选中态」下失效**（树读数返回 0 行）⟹ 且删除**没落盘** | ★★ 换**权威状态源** |
| v17 | ★★★ **决定性的一趟**：把「权威状态」从 DOM 换成 **API** | 见 §2.3 |

★★ **根因与正解（这一条值得记住）**：
前两版都试图用**几何**（x/y 区间）区分「场景树对象行」与「浮层面板行」⟹
**浮层会盖在场景树上面**，几何上它们是重叠的 ⟹ 分不开。

正解（第一版）是**用 class**：

- 场景树对象行：`className` 含 `z-10` **且** 含 `pl-1`
- 体型预设面板行：`className` 只有 `truncate`

⟹ ★ 判据改成「**class 同时含 `pl-1` 与 `z-10`**」⟹ 实测只读到 4 行（全是场景树行），
**面板行一个都没混进来**。

★ 但 v16 又把它打回来了：**class 口径在「选中态」下失效** ⟹ 树读数返回 **0 行** ⟹
「新增了一行」这条前提**测不出来** ⟹ ⟹ **DOM 根本不该承担「有几个角色」这个判定**。

### 2.3 ★★ 权威状态 = **API**，不是 DOM

源站导演台的状态在 `api/canvas/project/detail-by-space` 的响应里 ⟹
导演台节点（`type=36`）的 `data.compositionData.characters` 就是**权威角色列表**
（每项有 `id` 与 `label`）。

⟹ 于是整个判定链改写成**在权威数据上闭环**：

```
① 权威基线：compositionData.characters == [{id: xqns9rxe, label: "角色A"}]
② 点「添加角色」→ 选体型预设「标准男性」
③ 读右栏「名称」输入框 = "角色B"          ← DOM 只用在这一步（它是「人看到的名字」）
④ ★ 轮询 API 直到 characters 变成 2 项      ← ⟹ 已落盘，不是内存态
⑤ ★ 新增那项的 label == ③ 读到的值         ← ★ 关系式判据，不是两个常量相等
⑥ 收尾：删掉它 → 轮询 API 直到回到 1 项
```

★ 鉴权有个坑：源站**不用 cookie 鉴权 API**，而是**自定义请求头** `token` ＋ `webid`
⟹ 页面内 `fetch` 和 `page.request` 不带这两个头都只回 90 字节
`{"code":10001,"msg":"用户未授权"}` ⟹ **解析不到任何节点** ⟹ 静默返回空列表
⟹ ★ 那正是「**读数方法坏了**」的典型形态 ⟹ 这两个值**只能从页面自己发的请求里抄**。

### 2.4 ★ 顺带查清了源站的**保存机制**

删除角色后，源站**约 30 秒**才发 `POST /api/canvas/nodes/batch`（保存的是导演台节点
`n-gYB1c2Peq9` 的 `compositionData`）⟹ ⟹ 「跨刷新复验」必须**等够时间**，
否则会把「还没落盘」误判成「没删掉」（v13 就这样误判过一次）。

★ 这也是「**副作用必须复核**」的一个具体形态：内存里消失 ≠ 存盘了。

---

## 三、clone 的改动

`src/store/directorStore.ts`（种子对象 `director-character-lead`）：

```diff
   {
     id: "director-character-lead",
-    name: "角色01 · 陈默",
+    // ★★ Batch 838：源站实测的第一个角色叫「角色A」（字母序号）
+    name: "角色A",
```

★ 源站的口径是「**角色 + 字母**」，clone 的旧名是「**数字序号 + 语义后缀**」⟹
与 batch 837 那次机位的事**完全同构**（自拟名 vs 源站口径）。

### 3.1 派生量**自动跟随**（无需另改）

| 派生量 | 派生式（源码位置） | 改名前 | 改名后 |
| --- | --- | --- | --- |
| 变换轨道 label | `src/store/directorStore.ts:1180` `${object.name} · 变换` | 角色01 · 陈默 · 变换 | **角色A · 变换** |
| 姿态轨道 label | `src/store/directorStore.ts:1276` `${object.name} · 姿态` | 角色01 · 陈默 · 姿态 | **角色A · 姿态** |

---

## 四、被同步的旧门禁（三处**真断言**）

| 门禁 | 位置 | 旧期望值 | 新期望值 |
| --- | --- | --- | --- |
| `720` | `scripts/verify-liblib-batch720.py:287` `FIXTURE` 首项 | 角色01 · 陈默 | **角色A** |
| `42` | `scripts/verify-liblib-batch42.py:253` 姿态轨道 label | 角色01 · 陈默 · 姿态 | **角色A · 姿态** |
| `43` | `scripts/verify-liblib-batch43.py:185` option 列表 | 角色01 · 陈默 | **角色A** |

★ 720 改后**全量跑通 7/7**；42 与 43 也**全绿**。

★ 617／629／666／736 里的「角色01 · 陈默」是**docstring 的历史文字** ⟹ **不动**。

---

## 五、门禁（`scripts/verify-liblib-batch838.py`）

| 判据 | 内容 |
| --- | --- |
| S1 | ★★★ **「S83·镜2」是上传的 mp4 文件名**：raw 里 `alt` 带 `.mp4`、`action` 是 `video_resource`、`uploaded` 为真 |
| S2 | ★★ **源站没有「镜头」实体**：`compositionData` 顶层键与 `animation` 子键**都已枚举** ⟹ 无 shot 类键 |
| S3 | ★★ **源站的命名口径**：`cameras[].label` 全是「机位N」、`characters[].label` 全是「角色 + 单个大写字母」 |
| S4 | ★★★ **角色默认名规则 = 「角色 + 字母序号」**（★ **权威 API 口径**）：清理后基线**只剩**「角色A」⟹ 新建后**权威 API 里真多了一个**角色（轮询达成 ⟹ 已落盘）⟹ ★ **重算关系**：那个角色的 `label` **==** 右栏名称输入框的值 == 「角色B」⟹ ⟹ 字母序号递进；★ 收尾**已复原**（**独立进程**再读 API） |
| S5 | ★★ **clone 默认角色名 == 「角色A」** ＋ 派生跟随（变换/姿态轨道 label）＋ **DOM 上可见** |
| S6 | ★★ **三处旧门禁期望值已同步**（且 42 那条**成功抽出**了期望值 ⟹ 不是「抽不出而静默通过」） |
| S7 | ★★★ **否定性结论的扫描器有效性** ＋ **更正已落地**（顶层键数、animation 子键数、raw 节点数都已记下 ⟹ 零命中不是因为扫不到） |

★ S4 的判据**结构**值得写下来（它是「默认名规则」这类断言的通用形状）：

> 默认名 = 「角色 + 字母序号」 ⟺ **必须同时**满足：
> ① **权威 API 的基线**只剩一个角色，且它的 `label` 是「角色A」；
> ② 新建后**权威 API 里真多了一个**角色（⟹ 轮询达成 ⟹ 已落盘，不是内存态）；
> ③ ★ **关系式**：新增那项的 `label` **==** 右栏「名称」输入框读到的值；
> ④ 该值 == 「角色B」⟹ ⟹ 字母序号递进；
> ⑤ 收尾**已复原**，且由**独立进程**再读一次 API 证明（⟹ 服务端状态，不是内存残留）。

★ 只满足 ③ 就下结论是不够的 —— v9 就是只满足 ③ 而没有 ② ⟹ 读数无法自证。

★★ ③ 之所以要**重算关系**、而不是直接读 raw 里那条存好的布尔
（`E_★★新增角色的label是否等于右栏读到的名`）⟹ 是因为**存好的布尔是结论不是测量**：
它可以被改、被抄错，却看不出「它当时是从哪两个值算出来的」⟹ ⟹ 门禁重算，
把那条布尔只当**交叉印证**（两条一致 ⟹ 更可信；不一致 ⟹ 当场露馅）。

---

## 六、本批**没有**解决的问题（如实记下）

1. ★ **crowd（群众）成员的命名未对齐** —— clone 仍用 `角色01`／`角色02`（数字）⟹
   源站的 crowd 命名**未测** ⟹ 本批**不猜**。
2. ★ **源站角色名是不是字母表**（A→B→C…）**只有一个递进点** ⟹ 不声称。
3. ★ **镜头命名体系仍未对齐** —— 但**现在知道了原因**：源站**没有镜头实体**可比 ⟹
   这不是「还没查到」，而是「**没有可对齐的对象**」。
4. 748 的 C1/C3/C4 期望值过时（batch 835 已提供关系式替代但未改 748）—— 仍未处理。
5. batch 833／837 的 README **不可重写** ⟹ 那两条错结论的原文仍在，
   更正写在本文件 ＋ 台账 ⟹ **没有**改写旧批次。

---

## 七、源站状态：**已完整复原**

本批在源站新建过角色（用于测默认名）⟹ ★ 收尾**必须**复原。

★ 复原这件事本身走了**三段**，每一段都是**权威 API 读数**：

| 段 | 做了什么 | 权威读数 | 产物 |
| --- | --- | --- | --- |
| v19（`charname838j`） | 建角色 → 测名 → 尝试删 | 新建后 API 有 2 项 ✅；但**它自己删的那次没删掉**（`F_★是否点了删除 = False`，选中态下 class 口径找不到那一行） ⟹ **未复原** | `raw/source-838-charname-closedloop.json` |
| `cleanup838` | 按 API 的 `id` 定位 → 右键 → 删除 → **轮询 API** | 删掉 id `p6past1f`（label「角色B」）⟹ 轮询 16 秒后 API 只剩「角色A」 ✅ | `raw/source-838-cleanup.json` |
| ★ `source_restored838` | **全新进程、全新浏览器会话**，**只读不点**，再读一次 API | 角色 = `[{id: xqns9rxe, label: 角色A}]`、相机 = `["机位1","机位2"]` ✅ ⟹ ⟹ **没有遗留的「角色B」** | `raw/source-838-restored-final.json` |

★★ 第三段是**必要**的，不是重复：前两段都在**同一个浏览器进程**里 ⟹
「内存里的 DOM 没了」与「服务端真存了」只由**同一份 API 读数**支撑 ⟹
而已入库那条纪律说得很直白：**内存里消失 ≠ 存盘了** ⟹ ⟹
必须换一个**独立进程**再读一次，才敢说「已复原」。

★ 全程以**进站基线**为准（源站有并发活动）⟹ 只删本批新建的那一个。

---

## 八、文件清单

```
docs/research/liblib-canvas-batch838-2026-10-01/
├── README.md                                   ← 本文件
├── runtime-audit.json                          ← 门禁产物
├── raw/
│   ├── source-838-detail-by-space.json         ← ★ 权威数据（节点 + compositionData）
│   ├── source-838-shotlike-scan.json           ← 「S..」形态文本扫描
│   ├── source-838-node-titles.json             ← 各画布节点的类型与标题
│   ├── source-838-video-node-dom.json          ← video 节点的 DOM 与祖先链
│   ├── source-838-fiber-props.json             ← React fiber（证明这条路走不通）
│   ├── source-838-network-index.json           ← 网络层：哪条 API 返回了 S83
│   ├── source-838-charname-baseline.json       ← 角色命名的进站基线
│   ├── source-838-charname-new.json            ← 新建角色后的读数
│   ├── source-838-restore-network.json         ← ★ 自动保存机制的证据（nodes/batch）
│   └── source-838-charname-closedloop.json     ← ★ 单趟闭环（门禁 S4 的证据）
│   ├── source-838-cleanup.json                 ← ★ 清理实验遗留角色的过程与复核
│   └── source-838-restored-final.json          ← ★★ 独立进程复核「已复原」
└── probes/
    ├── shotname838.py      ～ shotname838e.py  ← 「S83·镜2」溯源（五趟）
    ├── charname838.py     ～ charname838j.py   ← 角色命名（**十趟**，含踩坑记录）
    ├── trackname838.py                             ← 轨道名相关的一趟探针
    ├── restore838.py / restore838b.py / restore838c.py  ← 复原与保存机制
    ├── verify_source_restored.py               ← ★ 跨刷新复验（独立进程）
    ├── source_restored838.py                    ← ★★ 当下独立复核（只读，不点）
    ├── cleanup838.py                            ← ★ 清理实验遗留角色（按 id 删）
    ├── clone838.py                              ← clone 侧派生读数
    └── neg838.py / ledger838.py                 ← 阴性对照 ＋ 台账
```

改动文件：

```
src/store/directorStore.ts                      ← 种子角色名
scripts/verify-liblib-batch720.py               ← FIXTURE 首项
scripts/verify-liblib-batch42.py                ← 姿态轨道 label
scripts/verify-liblib-batch43.py                ← option 列表
scripts/verify-liblib-batch838.py               ← 新门禁
```
