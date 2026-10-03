# batch 728：script-v2 的两个把手运行时确认为无名 —— 该类型连不出任何边

日期：2026-10-03　验收器：`scripts/verify-liblib-batch728.py`（7 条判据，零 store 写入，不改 `src/`）

闸门：判据 **7/7 通过（连跑两轮读数逐条一致）**；typecheck 绿；
`docs:check` 里 `docs/research/` **0 条**；本批文件 lint **0 error / 1 warning**；
**build 跳过** —— `src/` 自 batch 690 起 0 提交。

## 起点

727 的完成度表里只剩一个「⚠️需空画布」：**`INVALID_HANDLE_DIRECTION`**。
本批把那一步真做了。

## 破坏与恢复

- **破坏**：`Shift` + 左键在 pane 上框选全部 10 枚 → 按 `Delete`。
  `page.tsx:1552` 是 `selectionOnDrag={false}` 且未改 `selectionKeyCode`
  ⟹ react-flow 默认以 **`Shift`** 为框选键；这是用户能做的正常操作。
- **恢复**：`page.reload()` —— 721 已实测 `canvasStore.ts` 零持久化写入，
  画布每次加载都回到 10 枚种子节点 ⟹ **破坏在会话内完全可逆**。
- **「可逆」这件事本身被写成了判据 7**，它同时复核了 721 的结论。

## 决定性读数

### ① 框选与清空

| 步骤 | 读数 |
|---|---|
| 框选 | `nodeIds` **10 枚全中** |
| `Delete` | **nodes 10 → 0**、**edges 11 → 0** |

### ② 空画布的 4 枚芯片

`story-script`（故事脚本生成）/ `character-turnaround`（角色三视图）/
`reference-to-video`（全能参考生视频）/ `audio-to-video`（音频生视频）。

### ③ 「故事脚本生成」成对造节点，且二者间无连线

| 读数 | 值 |
|---|---|
| 新增节点 | **2**：`text-<时间戳>-<随机>` + `script-v2-<时间戳>-<随机>` |
| 新增边 | **0** |

⟹ 与 `canvasStore.ts:1272` 的注释一致：「成对创建预填剧本的 text 节点与
script-v2（脚本生成器）节点，**二者间无连线**；单条历史（原子动作）」。
源码注释在本批第一次被运行时读到。

### ④ `script-v2` 的两个把手运行时确认为无名

| 把手 | `data-handleid` | 宽 |
|---|---|---|
| 左（target 位） | **`null`** | 9.81 |
| 右（source 位） | **`null`** | 9.81 |

⟹ 727 的静态普查结论在运行时得到确认，两边对上。

### ⑤ 从它起手：连接注册了，但落点永远拿不到 `valid`

拖 `script-v2`(右把手) → `text`(左把手)：

| 读数 | 值 |
|---|---|
| 起手柄 | `connectingfrom`，**`id: null`** |
| 落点柄 | `connectingto`，**无 `valid`**，底色 **`rgb(9, 202, 245)` 青** |
| 新增边 | **0** |

⟹ `normalizeLibTVConnection` 的 `INVALID_HANDLE_DIRECTION`
（`libtvGraphConnection.ts:74-76`）要求翻正后必须是 `"source"` / `"target"`，
而这里的 handle id 是 `null` ⟹ 拒绝。

**⟹ `script-v2` 这个节点类型在 UI 上连不出任何边。**
而且它在**两个方向上撞的是同一条规则** —— 无论自己当 source 还是当 target，
它的 handle id 都是 `null`。

## 六条拒绝规则的最终完成度

| 规则 | UI 可达？ | 首次测于 |
|---|---|---|
| `DUPLICATE_NODE_PAIR` | ✅ | 725 |
| `DIRECTED_CYCLE` | ✅ | 726 |
| `SELF_LOOP` | ✅ | 727 |
| **`INVALID_HANDLE_DIRECTION`** | **✅（走完空画布）** | **728** |
| `DANGLING_ENDPOINT` | ❌ 按构造不可达 | 727 |
| `MISSING_ENDPOINT` | ❌ 按构造不可达 | 727 |

**六条全部定性完毕，没有一条悬着。**

## 不声称

- **不声称第二次尝试（`text` → `script-v2`）的读数** ——
  那一次连接态标记**一个都没出现**（marks 为空），说明手势根本没进入连接态，
  **原因未取证；不作为结论依据**。已确认的是 `script-v2` 起手那一侧。
  验收器把它写成判据 6，只断言「没新增边」并**显式记录 marks 为空**，
  不让读者误以为那条也是证据。
- **不声称源站有没有 script-v2 这种节点**（源站未测）。
- **不声称这是「唯一连不出的类型」** —— 只测了这一种。

## 新增待拍板

1. **`ScriptV2Node` 的两个 `<Handle>` 缺 `id`** ——
   照 `TextNode.tsx:77-78` 的 batch 355 做法补 `id="target"/"source"`
   （**需改 `src/`，等授权**）。
   **在本批读数下：补之前该类型完全无法连线。**
2. **「故事脚本生成」造出的两个节点之间没有连线** ——
   它们在流程上是先后关系还是并列关系？UI 上无从判断，未取证。

## 方法论

1. **「到不了」和「到了而且规则确实拒它」是两件事** ——
   727 用静态普查 + 可达性分析给出「需要空画布」，本批走完之后结论落地。
   **静态可达性分析只能把路指出来，替代不了走一遍。**
2. **破坏性操作要先写好恢复路径，再把它变成判据** ——
   `page.reload()` 能恢复这件事值得断言：它同时复核了 721 的结论，
   让「破坏」这一格也有证据而不是靠信任。
3. **框选的起点必须验证命中的是 pane** ——
   我第一版从 (30, 40) 起手，那里是顶栏；按节点包围盒外扩 30px 计算，
   并在按下前断言 `startIsPane` 才选中。**「操作没反应」先查操作落在谁身上。**
4. **同一次实验里失败的那一格不要硬解释** ——
   「text → script-v2」marks 为空，我只记「未取证」，不编一个原因；
   并把它写成一条只断言已证部分的判据。

## 探针返工三处

1. 第一版以为「左键在 pane 上是框选」—— 实际 `selectionOnDrag={false}`，
   框选键是默认的 `Shift`。
2. 起点写死 (30, 40)，落在顶栏上 ⟹ 框选始终选不中（`nodeIds` 恒 `[]`），
   Delete 因此变成空操作（**没造成破坏**，反而验证了「选区为空则 Delete 无效」）。
3. 读把手的 JS 括号写崩（`SyntaxError: missing ) after argument list`），
   改成扁平箭头函数后通过。
