# batch 747 — 把 16 个记账命令里最后两个「从未真跑」的跑通，并**撤回 745 的一条待拍板项**

## 起点

744 把 16 个记账命令分成 A 档 8 / B 档 8；745 走完 B 档 7 个（5 真跑 / 2 被时长挡住）；
746 走完 A 档剩下 4 个。走完之后 16 个里**只剩两个从未被真正触发过**：

- `createPictureEdit`（主体消除）—— 745 证到「面板能开、提交按钮 disabled」，
  但「标记主体」那一跳没做 ⟹ 命令本身没被调用。
- `clearVideoContinuation`（清除续写）—— 745/746 都只验到「入口条件不满足」。

本批把这两个跑通。全部读数来自 clone，**不碰源站**。

## 汇总表：16 个记账命令的「真跑过」状态

口径沿用 744 的 A/B 分档；「真跑过」是**跨批次累计**的结论。

| 命令 | 档 | 跑过的批次 | `past` | 节点 | 边 |
|---|---|---|---|---|---|
| `createFirstFrameReference` | A | 744 | +1 | ±0 | ±0 |
| `createFirstLastFrameReference` | A | 744 | +1 | ±0 | ±0 |
| `updateNodeData`（`setAttempt`） | A | 744/745/746 | +1 | ±0 | ±0 |
| `addNodeAtPosition` + `addEdge`（选特效） | A | 746 | **+2** | +1 | +1 |
| `destroyFirstFrameReference` | A | 746 | +1 | −1 | −1 |
| `createLongVideoProcess` | A | 746 | +1 | **+12** | **+22** |
| `addDerivedNode`（逐帧拉片） | B | 745 | +1 | +1 | +1 |
| `createVideoFrameCapture`（抽帧） | B | 745 | +1 | +1 | +1 |
| `createAudioSplit`（音视频分离） | B | 745 | +1 | **+2** | **+2** |
| `createSubtitleErase`（智能去字幕） | B | 745 | +1 | +1 | +1 |
| `createSmartMatting`（智能抠像） | B | 745 | +1 | +1 | +1 |
| `createDepthMotionCapture`（深度动作捕捉） | B | 745 | +1 | +1（需时长 ≤15s） | |
| `createVideoContinuation`（智能续写） | B | **747** | +1 | +1 | +1 |
| `clearVideoContinuation`（清除续写） | B | **747** | +1 | **±0** | **−1** |
| `createPictureEdit`（主体消除） | B | **747** | +1 | +1（需时长 ≤15s） | +1 |
| `submitLibTVEditorSessionCommit` | A | — | — | — | 742 验出零 UI 入口，从未触发 |

**16 个里 15 个真跑过**，只剩 742 验出「全 `src/` 零调用」的
`submitLibTVEditorSessionCommit`。

## 决定性读数

### ① 撤回 745：提交按钮 disabled **不是没有提示**

745 的待拍板③ 写「主体消除提交按钮 disabled 但无提示『要先标记主体』，要不要给引导？」。
**这条事实不成立** —— `PictureEditPanel.tsx:865-875` 渲染了这句提示：

```jsx
<span data-picture-edit-submit-reason={reason ?? undefined}
      className={cn("min-w-0 flex-1 truncate text-[11px]",
                    reason ? "text-[#bd8c55]" : "text-[#777]")}>
  {submitting ? "分析中" : reason ?? `当前帧 ${currentTime.toFixed(2)}s · 标记将用于整段视频`}
</span>
```

实测：

| 读点 | 值 |
|---|---|
| `data-picture-edit-submit-reason` | **`请先标记主体`** |
| 文本内容 | **`请先标记主体`** |
| `getComputedStyle().color` | `rgb(189, 140, 85)` ← `text-[#bd8c55]`，琥珀色警示调 |
| 提交按钮 `disabled` / `aria-label` | `true` / `提交主体消除` |
| 标记计数 `data-picture-edit-count` | `0/4` |

⟹ **745 是因为面板开了就直接读 `disabled`，没去读旁边的提示文本。**
提示是有的、挂在属性上、还配了警示色。

### ② 主体消除第三段只需**一次 `pointerdown`**

`PictureEditPanel.tsx:379-409` 的 `beginDraw` 在 `tool === "point"` 时直接建标记；
默认工具实测就是 `point`（`data-picture-edit-tool="point"`），不用先切工具。

| | 标记数 | 计数 | 提交 `disabled` |
|---|---|---|---|
| 面板刚开 | 0 | `0/4` | `true` |
| 在 overlay（268×150）中心 `mouse.down/up` 之后 | **1** | **`1/4`** | **`false`** |

点提交 ⟹ 300ms 时 `data-picture-edit-submit-status="analyzing"`、面板仍在；
2.5s 时**属性与面板都已消失**（`submitPictureEdit` 关面板）⟹
这个异步阶段是「**面板关掉**」，不是「状态回到 `idle`」。

store 侧：`past` +1、节点 +1、边 +1，新节点
`filename: "主体消除-视频节点 5-片段重拍"`、`type: "video"`、`status: "pending"`。

### ③ `continuation` 写在**新建的续写卡**上，且确认后**选中会切过去**

```
canvasStore.ts:1712-1733   const targetNode: Node = { id: targetId, type: "video",
                        data: { filename: `续写 ${sourceLabel}`, status: "empty",
                                durationSeconds: 6, …, continuation } }   // ← :1731
canvasStore.ts:1756-1757   selectedNodeIds: [targetId], selectedNodeId: targetId
```

实测：源卡 `video-…` → 确认 → 选中变成 `video-continuation-…`，
新卡 `filename: "续写 视频节点 5-片段重拍"`、`status: "empty"`、`durationSeconds: 6`、
`start: 0` / `end: 30`、`sourceNodeId` 指回源卡。
⟹ 「退出续写模式」按钮出现在**续写卡**的生成面板上，`clearVideoContinuation(id)` 里的
`id` 也是这张卡。

### ④ **「退出续写模式」只降级、不删卡**

`canvasStore.ts:2990-3008` 只做两件事：
`delete nextData.continuation`（从续写卡摘掉元数据）
+ `edges.filter(edge => edge.id !== continuation.edgeId)`（删连线）——
**没有删节点**（静态扫描专门查了 `nodes: canvas.nodes.filter`，0 命中）。

| | 退出前 | 退出后 |
|---|---|---|
| `past` | 2 | **3（+1）** |
| 节点 | 12 | **12（±0）** |
| 边 | 12 | **11（−1）** |
| 带 `continuation` 的卡 | 1 | **0** |
| 续写卡本身 | 在 | **仍在**，`hasCont: false`、`status: "empty"`、`duration: 6` |
| 「退出续写模式」按钮 | 有 | **无** |

⟹ 卡留在画布上，`VideoNode.tsx:548` 的 `data-video-continuation-empty`
渲染「**等待续写内容**」（实测该文案在源码中）。

### ⑤ UI 的 4 秒下限与 store 的 4 秒守卫**同值**

```
VideoContinuationSelector.tsx:23   const MIN_DURATION = 4;
VideoContinuationSelector.tsx:101  const end = clamp(pointerSeconds, session.startSeconds + MIN_DURATION, …);
canvasStore.ts:1687                if (normalizedEnd - normalizedStart < 4) return null;
```

且 `[data-video-continuation-confirm]`（`:231` 起 9 行）**没有 `disabled` 属性** ——
无论区间多窄都可点，全靠 clamp 兜住。
⟹ 走 UI 出不了窄区间，**store 守卫是纯纵深防御、不是可达的拒绝路径**。

### ⑥ 「智能续写」是「一段面板 + 一次确认」

744/745 记的「两段式」是**两次点击**（开面板 → 点确认），不是两个面板：

```
VideoContinuationSelector.tsx:231-238  <button data-video-continuation-confirm
                                        onClick={() => onConfirm(range.start, range.end)}>
                                        <Check size={13} />确认续写</button>
VideoNode.tsx:217-220                  const confirmContinuation = (startSeconds, endSeconds) => {
                                          setActiveTool("generator");
                                          createVideoContinuation(id, startSeconds, endSeconds); }
```

中间没有第二个表单。默认区间实测 `0 → 30.00 秒`（源卡 30 秒整段）。

## 探针返工三处（全部是我自己的错）

1. **读错了节点**（本批最重要的一次）—— 确认续写后我去读**源卡**的
   `data.continuation`，读成 `null`，差点判成「命令没写上」。
   实际 `continuation` 在**新建的续写卡**上，且 `:1756-1757` 已把选中切过去。
   **改法**：快照里加 `contNodes`（按 `data.continuation` 存在与否筛节点），而不是按已知 id 找。
2. **「找那个有 X 的元素」不能按已知 id 找** —— 我手里只有源卡 id，
   而要找的字段长在另一个节点上。746 栽过一次同类坑（`display:none` 元素按自身盒子 hover），
   两批的共同教训：**先确认「要找的东西在哪个节点上」，再动手读**。
3. **起手式控件要先看它到底是什么** —— 我按「滑杆」写了 `min/max/step/value` 的读法，
   实测 `[data-video-continuation-start]` / `-end` 是 `<button>` 手柄（16×16，
   `min/max/step` 全 `null`）⟹ 读数全空。改成先打 `type`/`tagName` 再决定读法。

还有一条方法论修正：**745 那条撤回是靠 746 立的新规矩抓到的** ——
746 因为「`data-video-long-submit-state` 被 `isLongVideo` 门控」而立的
「**穷举一个布尔/状态的全部读点**」这条规矩，本批直接把它用在 `disabled` 上
（`disabled` 的读点不止按钮本身，还有 `:866` 的 `submit-reason` 文本），
才发现 745 漏了。

## 判据（7/7）

| | 判据 | 读数 |
|---|---|---|
| C1 | 静态：三个命令各恰好两处（声明 + 实现）；UI `MIN_DURATION=4` ⟺ store 的 `<4` 守卫；确认按钮无 `disabled`；`clear` 摘元数据 + 删边但**不删节点**；`submit-reason` 读点存在 | `[324,1663]` / `[374,2974]` / `[353,2615]`、`:23`、`:1687`、`:2974-3008`、`:866` |
| C2 | 智能续写入口：工具栏「智能续写」文字按钮 ⟹ 选择器面板出现，默认区间 `0 → 30.00 秒` | `确认续写`、`30.00 秒`、region 511×48 |
| C3 | 确认续写：`past`+1、节点+1、边+1；**选中切到新建的续写卡**；卡 `filename`=「续写 &lt;源卡名&gt;」、`status=empty`；「退出续写模式」按钮出现 | 选中 `video-…` → `video-continuation-…` |
| C4 | 退出续写：`past`+1、节点 **±0**、边 **−1**；续写卡仍在画布上且 `continuation` 已被摘掉 | `2→3` / `12→12` / `12→11`、`contNodes: []` |
| C5 | 主体消除第 1、2 段：改时长到 10 后面板出现；**`submit-reason`=「请先标记主体」**、提交 `disabled`、计数 `0/4` | `rgb(189, 140, 85)` |
| C6 | 主体消除第 3 段：落一个 point 标记 ⟹ 计数 `0/4`→`1/4`、提交解禁；点提交 ⟹ `analyzing` → 面板卸载，`past`+1、节点+1、边+1、新文件名以「主体消除-」开头 | `status: "pending"` |
| C7 | 16 个命令的「真跑过」汇总表 16 行齐（15 真跑 + 1 零入口） | 16 行 |

两轮连跑 **归一化随机 id 后 0 字段差异**；未归一化时的 12 处差异**全部**落在
随机节点 id（`video-…` / `video-continuation-…` / `picture-edit-…`）及其派生的
判据 detail 上 ⟹ 归一化没有吃掉真差异。

## 待拍板（需改 `src/`，等授权）

1. **「退出续写模式」留下空卡要不要改成删卡** —— 现在只摘元数据 + 删连线，
   卡留在画布上显示「等待续写内容」。删卡的话 `:2995-3003` 要多一个
   `nodes.filter(node => node.id !== targetId)`。
2. **`createVideoContinuation` 的 `< 4` 秒守卫要不要留** —— UI 的
   `MIN_DURATION = 4` 已经兜住了，确认按钮也没有 `disabled` ⟹ 这个守卫在当前 UI 下不可达。
   留作纵深防御可以，但值得加一行注释说明它防的是哪条调用路径。
3. **主体消除的「请先标记主体」提示要不要更醒目** —— 现有提示是 11px 琥珀色、
   `truncate`、在页脚左侧（`PictureEditPanel.tsx:865-875`）。
   745 的原提案（「无提示，要加引导」）**已撤回**；如果还要动，是**加强**不是**新增**。
4. **续写卡「等待续写内容」的文案与图标要不要对齐源站** —— 未取证，先问源站行为再定。

## 不声称

- 不声称**续写卡「等待续写内容」空态的视觉与源站是否一致** —— 未取证。
- **「退出续写模式」留下空卡是否有意**（降级 vs 删卡）—— 未取证，**不判定为缺陷**。
- `createVideoContinuation` 的 `< 4` 秒守卫**未真跑**（UI 走不到该区间）；
  只证到 UI clamp 与 store 守卫常量同值。
- **续写卡本身的生成**（`status: "empty"` → 生成出内容）未跑 ——
  那是续写卡的生成按钮，不在本批 3 个命令内。
- `createPictureEdit` 建的节点在 2.5s 时 `status: "pending"`，
  **后续是否会演进未取证**（745 已记过同一限制）。
- 主体消除只验了 `subjectRemove`；`subjectModify` / `subjectReplace` 的另外两条
  `reason` 分支（「请补充每个主体的修改描述」/「请为每个主体选择替换图」）
  **只从源码读到（`:539` / `:545`），未跑**。
- 16 个命令汇总表**沿用 744 的 A/B 分档口径**，本批没有重跑前 13 条 ——
  「真跑过」是**跨批次累计**的结论，不是本批的独立读数。
- 「智能续写」在 failed 卡上不可达（745 已证 L2 `status === "ready"` 门控），
  本批**只在 ready 卡上跑**，未做两态对照。

## 与前批关系

- **744「A 8 / B 8」+ 745 + 746** —— 三批走完后 16 个命令里只剩两个从未触发；
  本批补上 ⟹ **15/16 真跑过**，闭环。
- **745 的待拍板③ 撤回** —— 「主体消除提交按钮 disabled 但无提示」事实不成立。
  纠正记在本批，历史批次不重写。
- **746 立的「穷举一个状态的全部读点」** —— 本批直接用来抓出 745 的漏读：
  `disabled` 的读点不止按钮本身，还有 `:866` 的 `submit-reason` 文本。
- **744/745 的「智能续写两段式」** —— 收窄成「**一段面板 + 一次确认**」，
  「两段」指的是两次点击而非两个表单。
- **741「分清『声明』与『实现』」** —— 本批三个命令各恰好两处
  （`[324,1663]` / `[374,2974]` / `[353,2615]`），静态扫描必须取**实现**那一处。
- **746「静态写点与运行时读数要互相对账」** —— 本批用同一条方法核出
  「`clearVideoContinuation` 的段落里 `nodes: canvas.nodes.filter` **0 命中**」
  ⟹ 静态就已经能说清「它不删卡」，与运行时「节点 ±0」对平。

## 验收器

`scripts/verify-liblib-batch747.py` — 静态读 4 个文件（`canvasStore.ts` /
`VideoContinuationSelector.tsx` / `PictureEditPanel.tsx` / `VideoNode.tsx`）
共 16 个行号字段 / 15 个不同行号，另加 3 个命令的「声明 + 实现」行号对
+ 智能续写三跳（入口 / 确认 / 退出）+ 主体消除三段（开门禁 / 落标记 / 提交）
+ 16 行汇总表，两轮连跑归一化随机 id 后逐字段一致。
