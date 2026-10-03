# batch 725：手工连线是通的 —— 724 那三对全是重复对，被 `valid` 正确挡下

日期：2026-10-03　验收器：`scripts/verify-liblib-batch725.py`（7 条判据，零 store 写入，不改 `src/`）

闸门：判据 **7/7 通过（连跑两轮读数逐条一致）**；typecheck 绿；
`docs:check` 里 `docs/research/` **0 条**；本批文件 lint **0 error / 1 warning**；
**build 跳过** —— `src/` 自 batch 690 起 0 提交。

## 起点

724 试了两对连线（照抄一条现有连线的配对、以及一对自称「新」的），都是 11 → 11，
记成「手工连线未成立、成因未取证」，并点名下一步该 instrument `isValidConnection`。
本批做了那件事，拿到的答案比预期好得多。

## 决定性读数

### 我挑的配对全是非法的

`libtvGraphConnection.ts:93-100` 的 `hasUnorderedNodePair` 是**无序**判定：

| 724 试的配对 | 已有的边 | 判定 |
|---|---|---|
| `i-1FQ9tErTcC → b-bTLLuU4w5q` | 同向已有 | `DUPLICATE_NODE_PAIR` |
| `i-1FQ9tErTcC → i-YDfWhFlthe` | 同向已有 | `DUPLICATE_NODE_PAIR` |
| `g-EFbbHpwq5w → b-bTLLuU4w5q` | **反向**已有 | `DUPLICATE_NODE_PAIR`（无序判定） |

**三对全部是「已经连过了」，规则在正常工作。**
724 的读数（11 → 11）本身没错，**错的是它顺带说的概括**。

### 配对让探针自己算，别手挑

从 store 的边集复算无序对与有向可达，再挑配对：
10 枚节点 11 条边 ⟹ **无序对 11 个、规则允许的候选 60 个**。
（`t-9j2MoccxBj`「剧本」一条边都没有，是最干净的一端。）

### 合法配对：全成

| 试法 | 拖法 | 到目标时的 class | 结果 |
|---|---|---|---|
| 正向 | `g-245IDFh8sB`(source 柄) → `g-EFbbHpwq5w`(target 柄) | 起手 `connectingfrom`；落点 **`connectingto` + `valid`** | **11 → 12** ✓ |
| 正向 | `g-245IDFh8sB`(source 柄) → `t-9j2MoccxBj`(target 柄) | 同上 | **12 → 13** ✓ |
| **反向** | `g-245IDFh8sB`(**target** 柄) → `i-YDfWhFlthe`(**source** 柄) | 落点 `connectingto` + `valid` | **13 → 14** ✓，**方向被翻正**为 `i-YDfWhFlthe → g-245IDFh8sB` |
| **对照** | `i-1FQ9tErTcC → b-bTLLuU4w5q`（已连过） | 落点 `connectingto`，**没有 `valid`** | **14 → 14** ✗ |

新增边 id 形如 `e-<source>-<target>-<时间戳>`，与 `page.tsx:617-625` 一致；
松手后所有 connecting 标记清空。

**反向拖成立** ⟹ `normalizeLibTVConnection`（`libtvGraphConnection.ts:63-76`）
会把「从 target 柄起手」整体翻正，
所以 `INVALID_HANDLE_DIRECTION` 这条拒绝规则在真实交互里几乎碰不到。

### 关键：判别合法与否的是 `valid` 这一个 class

| 配对 | 到目标时的 class | 是否新增边 |
|---|---|---|
| 合法 | `connectingto` **+ `valid`** | **是** |
| 重复 | `connectingto`（**无 `valid`**） | **否** |

⟹ **`connectingto` 只说明 react-flow 在几何上认出了这个落点；
`valid` 才是 app 自己的 `isValidConnection` 给出的裁决。**

**⟹ 应用对「这条能不能连」给了逐目标的实时视觉反馈，没有静默拒绝。**
这在交互质量上是一条正面结论，而 724 的读数会让人以为相反。

## 撤回 724

**724 判据 7 `hand-drawing-an-edge-never-completes-for-either-pair` 测的不是那个东西** ——
它测的是「重复配对被正确拒绝」。读数存活，**概括连同判据名一起作废**。

顺带纠正 724 的探针：它数的是 `.react-flow__handle.valid` 与
`.react-flow__handle.connecting`，而 **`connecting` 根本不是 react-flow 的 class 名** ——
真正会变的是 **`connectingfrom`（起手柄）与 `connectingto`（落点柄）**。
所以「valid 恒 0」在重复对上是对的，在合法对上也是 0 —— **因为当时试的全是重复对**。

这是同一类错误的第三次：**721**（比错了对象）、**723 被 724 纠正**、**724**（挑的值控件不收）。
两次作废的结论都出在同一批方法论里写着的那一条：
**造出来的值必须是控件能接受的值。**

## 不声称

- **不声称画布的连线行为与源站一致**（源站未测）。
- **不声称 60 个候选全部可连** —— 只测了三对；
  `DIRECTED_CYCLE` 那条规则是探针按源码逻辑复算后**排除**掉的候选，
  没有单独构造用例验证它确实会被拒。
- **不声称 `valid` 的视觉呈现已核对**（本批只读 class 名，未比对源站样式）。

## 新增待拍板

1. **`DIRECTED_CYCLE`（画成环）这条拒绝规则至今没有用例** ——
   探针只是用它来筛候选。**要不要专门造一个成环的用例把它测出来**，
   以及被拒时用户看到的是不是与重复对相同的视觉（都没有 `valid`）。
2. **重复对被静默接受不了，但视觉上只有「没有 `valid`」** ——
   要不要在拒绝对上补一个更明确的原因提示（与 719 的 `aria-live` 同一条线）。
3. **反向拖能连且自动翻正** —— 源站是否也这样，未测。

## 方法论

1. **「造出来的值必须是控件能接受的值」—— 这条早已在方法论里，本批又犯了一次。**
   手挑的配对恰好全是已存在的无序对。
   **正确做法是让探针从 store 复算规则、再自己挑配对**，
   并把「选中的配对不在已有边集里」写成一条独立判据。
2. **规则的「无序」不是细节** —— `hasUnorderedNodePair` 无序判定，
   所以 `A→B` 已存在时 `B→A` 同样被拒。
   **拿反向当对照组，会被同一条规则挡下，看起来像「反向不支持」。**
3. **要分「被规则拒绝」与「手势没被接住」，就得找一个能同时解释两者的读数** ——
   `valid` 就是那个读数：几何认出了但校验没过 ⟹ 有 `connectingto` 无 `valid`。
4. **作废的成本远低于写进台账后再改** —— 724 那条作废只花了一个批次就查清，
   而台账里如果留着「画布不能连线」，后面每一批都会被它带偏。

## 探针返工三处

1. **724 的 class 名错了**：`connecting` 不是 react-flow 的 class，
   该读 `connectingfrom` / `connectingto`。**「valid 恒 0」这个读数本身没错**，
   错的是我以为它意味着「校验没跑」。
2. 第二版 `POSITION` 的 JS 解构是 `[a, b, sa, sb]`、我传的是 `[a, sa, b, sb]`
   ⟹ 四个 trial 全报「拿不到某一侧的 Handle」，
   又一次差点被我写成「Handles 不存在」。**四个同因失败就该怀疑探针，不是怀疑被测对象。**
3. 第一版靠手挑配对（见上）；改成从 store 复算后才拿到真读数。
