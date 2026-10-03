# batch 711：刷新页面到底带走了什么 —— 一次全叶投影的前后差集

日期：2026-10-03　验收器：`scripts/verify-liblib-batch711.py`（6 条判据，含一条前提判据，零 store 写入，不改 `src/`）

## 起点

710 留下一条硬读数：**同一个节点上，刷新页面是「内容留住、历史没留住」**。
但那条只说了两件事。本批要问的是**完整的边界**：还有哪些东西跟着刷新走了、哪些没跟。

做法是 699–711 一直在用的那条：**判「有没有变」用全 store 逐叶投影** ——
一次投影 → 关台 → 刷新 → 重开 → 再投影，**差集就是持久化的完整边界**。

沿用 710 立的两条规矩：**先跑前提判据**（全程是不是同一个 `sourceNode`）、
**节点 id 从按钮的 `closest()` 读**不硬编码。

## 五条预测（写死在验收器里，先于任何测量）

| 预测 | 内容 | 结果 |
|---|---|---|
| **P1** | 文档内容（对象名、fov、轨道、镜头时长）**过**刷新 | **成立** |
| **P2** | `history` 整个**不过**刷新 | **成立** |
| **P3** | 播放头与 zoom **不过**刷新 | **落在第三态** |
| **P4** | 选区与选中轨**不过**刷新 | **推翻** |
| **P5** | 时间轴的折叠态**不过**刷新 | **成立** |

## 全表

刷新前 778 枚叶子 → 刷新后 373 枚：**消失 406 / 新增 1 / 变了 5 / 相同 367**。

| 读数 | 刷新前 | 刷新后 | 过刷新？ |
|---|---|---|---|
| 对象名（含 `改名试试711`） | 改名试试711 | 改名试试711 | **过** |
| fov | 46 | 46 | **过** |
| 轨道 id 列表 / `duration` / `editorMode` / `isPlaying` / `shotEnd` / `zoom` | — | 一字不差 | **过** |
| **`selectedObjectId` / `selectedObjectIds`** | **`director-character-lead`** | **同** | **过（P4 被推翻）** |
| **`timeline.selectedTrackId`** | **`director-track-character-lead-transform`** | **同** | **过（P4 被推翻）** |
| `history.past`（2 条 × 196 枚叶子） | 2 条 | **0 条、整棵子树不见** | **不过** |
| `lastCommandResult` | `SET` | `null` | **不过** |
| `timeline` 折叠态 / 高度属性 | `true` / `88` | **`false` / `182`** | **不过** |
| `generation` | 1 | **2** | 重建 |
| `sessionId` | `…-2` | 新的（`…-1`） | 重建 |
| 播放头 `playheadTime` | **0（压根没动过）** | 0 | **未取证** |
| `zoom`（点过 zoom 簇唯一那枚按钮） | 44 | 44 | **未取证** |
| `captures` / `localModelLibrary` | 0 条 | 0 条 | **不适用** |

## 两条最有价值的读数

**① 选区与选中轨是**过**刷新的。** 刷新前我用一个真实点击把选中从机位换成角色
（`director-character-lead`），刷新后**原样回来**，`selectedTrackId` 也是。
**应用把「你当时选中了谁」记进了持久化。** 而 `history` 一个字都没带 ——
⟹ **持久化是按内容逐项挑的，不是「整个 store 存一遍」**，
「选了谁」这种纯视图状态被当成内容存下来了，而撤销栈没有。

**② history 是整棵子树消失，不是长度变 0。** 2 条条目 × 196 枚叶子 = 392 枚
`history.past[*]` 的叶子在刷新后的读面里**一枚都不存在**
（`pastLen` 2 → 0 只是表象）。这和「历史被清空成空栈」是两件事：
**条目连同它们携带的 before/after 文档快照一起没进持久化。**

## 两项落在第三态、一项不适用（不记成失败也不悄悄跳过）

- **播放头**：点了标尺 75% 处，刷新前 `playheadTime` **仍然是 0** ——
  **这个动作没造出差异**，所以「播放头过不过刷新」**未取证**。
- **zoom**：`[data-director-timeline-zoom-cluster]` 里**只有一枚按钮**，点完 `zoom` 仍是 44
  —— 同样**没造出差异**，**未取证**。
- **`captures` 与 `localModelLibrary`**：全程 0 条，我没有真实控件能造出样本 ——
  **0 → 0 是第三态，不是「它们也过刷新」**，记成**不适用**并写明理由。

## 本批自己踩的坑：探针的动作顶掉了自己要测的读数

第一版探针在**重开之后**又调了一次「选中机位」（为了让右栏渲染），
于是 `selectedObjectId` 和 `selectedTrackId` 的变化**分不清是刷新造成的还是探针造成的** ——
差集里那两行是假的。改法就是**重开后什么都不做**，直接读 store。
**要测某个读面，就不能在读面两侧碰它** —— 这是 706–710 反复出现的那条纪律的第七次应用。

## 判据

| 判据 | 断言 |
|---|---|
| `every-step-stays-on-the-same-source-node` | 开台/刷新前/重开后 `sourceNode` 只有一个取值，且等于按钮所属节点 |
| `document-content-survives-the-reload` | 改名在、fov 46 在、`duration`/`editorMode`/`isPlaying`/`shotEnd`/`tracks`/`zoom` 一字不差 |
| `the-whole-history-subtree-does-not-survive-the-reload` | 刷新前 ≥2 条历史、刷新后 0 条、**消失的 `history.past[*]` 叶子 ≥300 枚**、且没有新增的 `history.past[*]` |
| `the-selection-and-selected-track-survive-the-reload` | 刷新前确实选中了角色（不是默认值）、刷新后 `selectedObjectId`/`selectedObjectIds`/`selectedTrackId` 原样 |
| `the-timeline-collapse-state-does-not-survive-the-reload` | 刷新前 `isCollapsed="true"`、刷新后 `"false"`、高度属性不同 |
| `the-session-identity-is-rebuilt-on-reload` | `generation` 加 1、`sessionId` 换新、`lastCommandResult` 由 `SET` 变 `null` |

## 方法论收获（可复用）

**① 一次全叶投影的差集，比十条针对���断言便宜，而且不会漏。**
本批没有预先列「要测哪几项」——**差集自己长出了两条最有价值的读数**
（选区过刷新、history 是整棵子树消失），而我原本列的 P3 反而落进了第三态。

**② 「整棵子树消失」和「长度变 0」要分开断言。**
`pastLen: 2 → 0` 看上去像「历史被清空」，但叶子级读数说明
**连条目携带的 before/after 文档快照都没了** —— 这是两种不同的持久化行为，
只断言长度会把它读成前一种。

**③ 挑持久化的不是「文档 vs 视图」，是「谁被写进了那条记录」。**
`selectedObjectId` 是纯视图状态却**过了**刷新，而 `history` 是核心状态却**没过** ——
分类轴不是「重要不重要」，是「save 时有没有顺手带上」。

## 待拍板（不阻塞）

- **history 不入持久化**（710 提出，本批把范围量清了：392 枚叶子整个没有）：
  要不要在持久化里带上历史？带上的话「刷新后能撤销」就成立，但要考虑体积与代际（`generation` 每次刷新 +1）
- **选区被持久化、折叠态不被持久化** 这个组合要不要统一：
  用户刷新后「选中了谁」还记得、但「时间轴是折叠的」不记得
- 播放头与 zoom 的持久化**未取证**：下批要先找到能真正改变它们的控件
  （标尺点击不生效、zoom 簇只有一枚按钮 —— 这两条本身也值得单独查）
