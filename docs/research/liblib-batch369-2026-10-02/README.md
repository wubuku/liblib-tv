# Batch 369 — 「有文件但没有 caller」的组件普查：一个负结果，和一个自指测量陷阱

日期：2026-10-02
范围：`src/components/**`（含 `frameos/`，跨线 `director/` `jimeng/` 只统计不判红）

## 起因：往上一层问

Batch 367/368 都在查「按钮」。往上一层还有一类更根本的问题：
`src/components/` 下 **153 个**组件级文件，有几个**从来没被任何东西调用**？

两个 Dialog 早被记成「无人渲染」（batch 360），但那只是**已知的两个**——其余的呢？

## 结果：5 个，全部已登记。这是个负结果

```text
src/ 里零 caller 的组件: 6 个（含 1 个跨线）
CameraConfigDialog  CameraMovementDialog  CustomHandle
PlusIndicator  ScriptHeader              JimengInferPanel(跨线)
```

本线 5 个**全部已在 `docs/research/components/COVERAGE_MATRIX.md` 登记**，
且状态与处置理由都很具体：

| 组件 | 状态 | 文档给的处置 |
|---|---|---|
| `ScriptHeader` | `LEGACY` | 当前未挂载；不把固定标题或装饰圆点重新引入运行态 |
| `PlusIndicator` | `LEGACY` | no-op stub；真实连接 affordance 是 React Flow `<Handle>` |
| `CustomHandle` | `LEGACY` | 当前未使用的旧 handle prototype，不作为新连接交互参考 |
| `CameraConfigDialog` | `SPEC_COMPLETE` / caller `EVIDENCE_GATED` | 当前无已证普通 caller |
| `CameraMovementDialog` | `SPEC_COMPLETE` / caller `EVIDENCE_GATED` | 不能以 dormant component 推导 source/runtime capability |

**结论：仓库没有「写了却忘了接」的组件债，文档是诚实的。**
负结果同样要钉住——否则下一个写了没人接的组件会静默进来。

### 顺带纠正一条旧记录，并否定一个差点做错的动作

Batch 360/367 把这两个 Dialog 记为「**属导演台跨线范围，只记录不动**」。
本批**第一次查了全仓库引用**，结论是：**director 也没引用**，
它们是纯顶层 dormant 组件。错判的原因不是结论错，而是**从来没查过全仓库引用，
只在跨线目录里找过**。

也正因为先查了，才**没有**做出「删掉 554 行没人用的死代码」这个动作 ——
`COVERAGE_MATRIX` 已明写 `caller EVIDENCE_GATED`，且明确禁止
「以 dormant component 推导 source/runtime capability」。删掉会违反项目既有决策。

## 本批最有价值的发现：一个自指测量陷阱

第一版普查把 `scripts/*.py` 也算进引用来源，结果 `CameraConfigDialog`
**没有**被报成「无 caller」——因为它被**我自己的门禁脚本**提到了 **11 次**
（`verify-liblib-batch367.py` 与 `verify-liblib-batch368.py` 的白名单里都写着它）。

> **记录死代码的门禁，本身成了「它还活着」的证据。**
> 而且这个偏差是**自我强化**的：越是把某个组件写进白名单「好好记账」，
> 普查越看不见它是死的。

判据因此明确：**caller 只从 `src/` 里数，审计脚本不是产品接线。**
`scripts/**` 提到某个组件只说明有人在审计它，不说明用户能碰到它。

### 还有两个判据缺陷（都靠变异测试抓出来，不是靠读代码）

1. **没排除自身文件**。第一版按「全仓库出现次数」算，而
   `CameraConfigDialog` 在自己文件里出现了 3 次（`CameraConfigDialogProps` /
   `export function` / props 解构）—— 于是真正的死代码从名单上消失。
2. **正则型提取器可能悄悄匹配不到任何东西**。`matrix_referenced_paths()` 第一版
   写成 `` `([^|]*?)`(src/components/…)` ``，用 `[^|]` 跨两个反引号之间的内容 ——
   **但矩阵的列分隔符本身就是 `|`**：

   ```markdown
   | `PlusIndicator` | `src/components/PlusIndicator.tsx` | `LEGACY` | … |
   ```

   于是提取器**一条都抓不到**，`drifted` 恒为空，`matrix:no-path-drift` 变成
   **恒真的空断言**。变异测试把路径改成一个不存在的文件，门禁照样 10/10 通过。

   > 光看「绿了」不会发现这种问题。必须配一条
   > 「提取器确实抓到了东西」的自检（`matrix:extractor-found-rows`），
   > 并用变异测试确认它抓得住。

## 门禁 10 项

1. **正向**：每个没有 caller 的组件，**必须**在 `COVERAGE_MATRIX.md` 登记，
   且那一行必须带明确状态词（`LEGACY` / `SPEC_COMPLETE` / `EVIDENCE_GATED` /
   `DEPRECATED` / `DORMANT` / `REMOVED`）—— 不接受沉默；
2. **反向（文档漂移）**：矩阵里每条指向 `src/components/*.tsx` 的行，那个文件必须还在；
3. 「无 caller 且未登记」的本线组件数为 0；
4. **自指陷阱自检（双向）**：
   - 阴性：造一个只在 `scripts/` 里被提到的组件，普查**必须**仍报它无 caller；
   - 阳性：给一个已登记的 dormant 组件造一个 `src/` 内 caller，普查**必须**
     不再报它 —— 证明判据不是恒真；
5. 跨线（`director` / `jimeng`）只统计不判红，且**判红集合里一个跨线组件都不许有**。

### 门禁自己踩的两个坑

- **过滤器没双向验证**：第一版把 jimeng 的 `JimengInferPanel` 判成了本线的账 ——
  规则文档里写了「跨线只统计不判红」，**实现没跟上**。补了
  `census:cross-line-excluded-from-failure` 专门盯这个。
- **变异测试被副作用异常抓住**：第一次注入「caller 计入 scripts/」时，门禁崩在
  `ValueError: … is not in the subpath of src` 上，**一条断言都没跑到**。
  exit code 是 1，但那**不算**变异验证成功。顺带把 `relative_to` 的脆弱点修掉
  （路径只是给人看的，兜住即可），重跑后才拿到精确的断言失败。

### 变异测试（三项，全部精确红在对应断言）

| 变异 | 结果 |
|---|---|
| caller 计数把 `scripts/*.py` 也算进来（复现自指陷阱） | `census:found-some` + **`criteria:audit-mention-is-not-wiring`** + `criteria:has-dormant-sample`；detail 里直接列出「caller 是门禁脚本自己」 |
| 造一个无 caller 且未登记的组件 | `census:no-undocumented-unreferenced` |
| 把矩阵里的路径改成不存在的文件（文档漂移） | `matrix:no-path-drift`（**修好提取器之后才红得出来**） |

## 回归

- 本批门禁 10/10
- `verify-assertions.py`：572 个脚本 0 个空洞断言
- 产品代码**零改动**（本批是纯审计批）

## 产物

- `scripts/verify-liblib-batch369.py` —— 10 项门禁 + 普查
- `docs/research/liblib-batch369-2026-10-02/unreferenced-components.json`

## 遗留

- `JimengInferPanel`（jimeng 跨线）无 caller 且**未在矩阵登记** ——
  已如实记录在 `unreferenced-components.json` 的 `crossLineNoted` 里。
  属那边并行 session 的范围，本线不判红也不代改。
