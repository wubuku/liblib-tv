# batch 727：SELF_LOOP 可达且生效；INVALID_HANDLE_DIRECTION 卡在一个空画布上

日期：2026-10-03　验收器：`scripts/verify-liblib-batch727.py`（7 条判据，零 store 写入，不改 `src/`）

闸门：判据 **7/7 通过（连跑两轮读数逐条一致）**；typecheck 绿；
`docs:check` 里 `docs/research/` **0 条**；本批文件 lint **0 error / 1 warning**；
**build 跳过** —— `src/` 自 batch 690 起 0 提交。

## 起点

725/726 关掉了 `DUPLICATE_NODE_PAIR` 与 `DIRECTED_CYCLE`，
剩下四条拒绝规则：`SELF_LOOP` / `DANGLING_ENDPOINT` / `MISSING_ENDPOINT` /
`INVALID_HANDLE_DIRECTION`。本批逐条给出「UI 上碰不碰得到」的答案。

## 决定性读数

### ① SELF_LOOP：UI 可达且生效

把 `t-9j2MoccxBj`（剧本，零边）的 **source 把手拖到它自己的 target 把手**：

| 读数 | 值 |
|---|---|
| 落点 class | `connectingto`，**无 `valid`**，**无 `invalid`** |
| 落点底色 | **`rgb(9, 202, 245)` 青** |
| 新增边 | **0**（`nEdges` 11 → 11） |
| `lastCommandResult` | `null` → `null` |

⟹ **与 726 的成环拒绝表现完全同构**：同样是「无 `valid` + 青色 + 不记账」。

### ② 顺带一个真实的副作用：拖拽会顺带选中节点

从把手起手的拖拽，把 `t-9j2MoccxBj` 选上了：

| 选区 | 拖之前 | 拖之后 |
|---|---|---|
| `nodeIds` | `[]` | `["t-9j2MoccxBj"]` |
| `kind` | `none` | `node` |

⟹ **「零记账」只对命令通道成立**：连接被拒不记命令，但**拖拽本身改了选区**。
这不是「拒绝的记账」，是拖拽的副作用 —— 两者必须分开说。

### ③ 三层类型数：注册 13 / 面板 9 / 种子 5

| 层 | 数量 | 缺哪些 |
|---|---|---|
| `page.tsx:143-157` 注册 | **13** | — |
| 「添加节点」面板给 | **9** | 注册了但不给的 **5 种**：`long-video-process` / `script-generator` / `script-v2` / `shot-breakdown-result` / `storyboard-group` |
| 种子画布实际有 | **5** | 面板也不给的 **1 种**：`storyboard-group` |

面板的 9 项是：文本 / 图片 / 视频 / 智能剪辑Beta / 导演台NEW / 逐帧拉片SD 2.5 / 音频 / 脚本 / 素材库。
脚本子菜单另给两项：`script-new`（脚本生成器）与 `script-legacy`（脚本旧版）——**仍然没有 `script-v2`**。

### ④ 13 种里只有 `ScriptV2Node` 的把手没写 `id`

逐组件静态普查 `src/components/nodes/*.tsx` 的 `<Handle>`：

| 组件 | `<Handle>` 带 `id` 吗 |
|---|---|
| `TextNode.tsx:77-78` | **带**（`id="target"` / `id="source"`）—— 注释里写着「Batch 355：与其余节点类型对齐补具名把手（`data-handleid` 可寻址，batch 57 连接合同依赖 source/target 命名）」 |
| `ScriptV2Node.tsx:55-56` | **不带** ⟹ `data-handleid` 为 `null`（**全 13 种里唯一一个**） |

⟹ `normalizeLibTVConnection` 的 `INVALID_HANDLE_DIRECTION`
（`libtvGraphConnection.ts:74-76`，要求翻正后必须是 `source`/`target`）
**只对这一种节点类型可达**。

### ⑤ 而它卡在一个空画布上

`script-v2` 全仓只有一处创建点：`canvasStore.ts:1291` 的 `createStoryScriptPair()`；
它唯一被调用处是 `CanvasEmptyState.tsx:49` —— **空画布状态**。

⟹ 在 10 枚种子节点的画布上，**UI 没有任何入口能造出 `script-v2`**，
于是 `INVALID_HANDLE_DIRECTION` **在非空画布上 UI 不可达**。

### ⑥ 另外两条按构造不可达

`DANGLING_ENDPOINT`（端点不在节点集里）与 `MISSING_ENDPOINT`（端点为空）
都要求「有一个端点不是真实节点」—— 而 UI 连线的两个端点必然来自某个已渲染节点的把手。
⟹ **UI 上造不出来**，它们只守程序化调用。

## 五条拒绝规则的完成度

| 规则 | UI 可达？ | 证据 | 首次测于 |
|---|---|---|---|
| `DUPLICATE_NODE_PAIR` | ✅ | 无序重复对被正确拒绝 | 725 |
| `DIRECTED_CYCLE` | ✅ | 8 对现成可用，两节点直达 | 726 |
| `SELF_LOOP` | ✅ | 自己连自己 | **727** |
| `INVALID_HANDLE_DIRECTION` | ⚠️ 需空画布 | 只有 `ScriptV2Node` 把手无名 | **727（仅静态+可达性）** |
| `DANGLING_ENDPOINT` | ❌ 不可达 | 端点必来自真实节点 | **727** |
| `MISSING_ENDPOINT` | ❌ 不可达 | 同上 | **727** |

## 不声称

- **不声称 `script-v2` 连不上** —— 只做了静态普查与可达性分析，
  **没有在空画布上实测**（要先清空 10 枚节点，是破坏性操作）。
- **不声称空画布上一定连不上** —— 只说明 UI 造得出这种节点、其把手没写 id。
- **不声称源站有没有 script-v2 这类节点**（源站未测）。

## 新增待拍板

1. **`ScriptV2Node` 的两个 `<Handle>` 缺 `id`** ——
   要不要照 `TextNode` 的 batch 355 做法补 `id="target"/"source"`
   （**需改 `src/`，等授权**）。补之前该类型在 UI 上连不出任何边。
2. **`storyboard-group` 在种子里有、面板里没有入口** ——
   是有意的（分镜组只能由分镜流程产出）还是漏了，未取证。
3. **拖拽把手会顺带改选区** —— 这一点要不要与 706/707 的选区语义一起核。
4. **被拒落点只换颜色不换形状**（726 遗留）、**两种拒绝零命令记账**（726 遗留）。

## 方法论

1. **「规则有没有用例」要拆成两层** ——
   一层是「规则能不能被触发」，另一层是「触发它的前置状态 UI 造不造得出来」。
   `INVALID_HANDLE_DIRECTION` 两层都过不去 ⟹ **它不是「测不到」，是「到不了」**。
2. **静态普查要落到具体那一行，并给出对照** ——
   「只有一种组件的把手没写 id」必须给出 `ScriptV2Node.tsx:55-56`
   与对照 `TextNode.tsx:77-78`（那个还带着补它的批次注释），否则无法复核。
3. **「注册了的 / 面板给的 / 种子有的」是三份不同的清单** ——
   三者一比就看清覆盖面：13 / 9 / 5，而且**「注册了但面板不给」正好就是规则到不了的那几种**。
4. **「零记账」要分清是命令通道还是副作用** ——
   `lastCommandResult` 恒 null，但选区被拖拽改了。**前者是「没记」，后者是「记了别的」。**

## 探针返工两处

1. **第一版把 `seeded ⊆ offered` 当成断言** —— 实际 `storyboard-group` 在种子里有、
   面板里没有。改成断言两个差集的**精确内容**，覆盖面反而看得更清楚。
2. **第一版在读脚本子菜单前先按了 Escape**，把整个面板关掉了，
   子菜单读出 `None`。**面板是「关掉顶层前景面」语义，按 Escape 是关整个面板。**
