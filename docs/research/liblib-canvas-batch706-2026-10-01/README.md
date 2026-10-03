# batch 706：手势的原子性 —— 悬手势归谁、一次交互并成几条、`Cmd+Z` 在输入框里去哪了

日期：2026-10-03　验收器：`scripts/verify-liblib-batch706.py`（6 条判据，11 个全新页面，零 store 写入，不改 `src/`）

## 起点

704 留下一条读数：`shot-end` 填越界值 9 按 `Tab` 之后，`activeGesture` **一直开着**（「不自动收」），账上写 `GESTURE_BEGIN` / `COMMITTED`。
705 补上另一半：12 枚 `transform:*` 数字框提交后账上一律记 `GESTURE_COMMIT`。

于是本批的问题写得很具体：**「悬着手势时做第二次编辑，撤销一次能撤掉什么、悬着手势的 baseline 会不会被写进后来那次真实编辑的撤销条目。」**

## 五条预测（写死在验收器里，先于任何测量）

| 预测 | 内容 | 结果 |
|---|---|---|
| **P1** | 活手势在手时第 1 次 `Cmd+Z` 会先取消手势（回滚文档）再撤上一条 | **推翻** |
| **P2** | `Escape` 在活手势上回滚值，且账上分得清「回滚了」与「什么都没发生」 | **一半**：回滚成立，**账上分不清** |
| **P3** | 悬着手势是那次**被拒**的编辑留下的 | **推翻** |
| **P4** | 一次聚焦内 N 次方向键并成 1 条撤销条目 | **成立** |
| **P5** | 悬着手势的 baseline 会被写进后来那次真实编辑的撤销条目 | **推翻** |

**P4 成立 ⟹ 手势的原子性本来就是对的，本批的原始担心不成立。**
被推翻的三条方向各不相同：P1 是「按键根本没进处理器」，P3 是「归属错了、因果也错了」，P5 是「什么都没发生」。

## 判据 1：悬着的手势不是 `shot-end` 的，是焦点落到的下一枚滑块的

四条臂，全部用真实点击 + 真实 `Tab` / `Shift+Tab`：

| 臂 | 动作 | `activeGesture` | 焦点 | 历史 | `shots[0].endTime` |
|---|---|---|---|---|---|
| 被拒 | `shot-end` 填 9 + `Tab` | **`camera-fov` / `fov`** | `data-director-camera-fov` | 0 条 | 8（未变） |
| 被接受 | `shot-end` 填 6 + `Tab` | **`camera-fov` / `fov`** | `data-director-camera-fov` | 1 条 `UPDATE_SHOT` | 6 |
| 什么都不填 | 只点一下 + `Tab` | **`camera-fov` / `fov`** | `data-director-camera-fov` | 0 条 | 8（未变） |
| 反向 Tab | `shot-end` 填 6 + `Shift+Tab` | **`null`** | `body` | 1 条 `UPDATE_SHOT` | 6 |

**704 的读数全部存活**（被拒时一条叶子都没变、历史没长、手势不自动收），
**归属要换**：手势是 `Tab` 把焦点交给下一枚可聚焦控件时，它自己的 `onFocus` 开的 ——
和「被拒」无关（被接受、什么都不填都开），只有焦点直接离开面板（`Shift+Tab` 落到 `body`）才不开。

## 判据 2：原子性是对的（本批的原始担心被推翻）

纯键盘路径：`Tab` 进 fov 滑块 → 连按 3 次 `ArrowRight` → 点画布收尾。

| 阶段 | fov | 历史条目 |
|---|---|---|
| `Tab` 进滑块 | 43 | 0 条，账上 `GESTURE_BEGIN` / `COMMITTED` |
| +1 次 `ArrowRight` | 44 | **0 条**，账上 `UPDATE_CAMERA` / `COMMITTED`（`historyEntries: 0`） |
| +2 次 | 45 | **0 条** |
| +3 次 | 46 | **0 条** |
| 点画布收尾 | 46 | **1 条** `camera-fov` |

那一条覆盖的字段**恰好两个**：`.objects[4].camera.fov` 和 `.timeline.tracks[1].keyframes[0].value.fov`（后者是 `recordObjectKeyframe` 写的）。

鼠标臂（直接点滑块，值跳变 + `pointerup` 提交）复现同一形状：一次点击一条、再 3 次方向键一条，两条都只覆盖同样那两个字段。

**⟹ 9 次测量里没有任何一条历史条目跨到用户没碰过的字段。P5 被推翻。**
（`useDirectorGestureBoundary` 的 `activeRef` 早退 + 焦点丢失即提交，正好实现了这个语义。）

## 判据 3：`Escape` 确实回滚了文档，账上却写「什么都没发生」

| 阶段 | fov | 账 |
|---|---|---|
| 初始 | 43 | — |
| 活手势 + 3 次 `ArrowRight` | **46** | `UPDATE_CAMERA` / `COMMITTED` / `projectChanged: true` / `historyEntries: 0` |
| 按 `Escape` | **43** | **`GESTURE_CANCEL` / `NOOP` / `projectChanged: false`** |

值精确回到基线，全 store 逐叶投影里这一段变化过的叶子有三个：
`authoredObjects[4].camera.fov`、`objects[4].camera.fov` **回滚了**，
而 **`timeline.selectedKeyframeId` 没有回滚** ——
`cancelDirectorGesture` 还原的是**文档快照**，不还原选择态，
所以按完 `Escape` 之后 `selectedKeyframeId` 可能还指着刚被回滚掉的那个关键帧。历史仍是 0 条。

**账上分不清**：那一行是 `projectChanged: false` 的 `NOOP` ——
和「按了 `Escape` 但什么也没发生」在账上**逐字相同**。用户丢掉 3 次改值，账上说无事发生。

## 判据 4、5：`Cmd+Z` 在输入框里不是撤销 —— 本批最值钱的一条

`DirectorDesk.tsx:484` 的 `if (isEditable) return;` 排在修饰键分支**之前**，
所以焦点在任一输入框内时 `Cmd+Z` **到不了** `undoDirector`。

两条输入框臂（`fov-gesture` 有活手势、`name-field` 无手势）连按 2 次 `Cmd+Z`：
**history 一字未改、store 一叶未改、账上没多命令、焦点没动。**
对照臂（焦点不在输入框）同一按键立刻记 `UNDO` / `NOOP` / `DIRECTOR_HISTORY_EMPTY` ⟹ 处理器本身是通的。

**但「什么都没发生」只在下一种情况下成立**：文档的表单历史里**有过一次键入**时，
浏览器自己的**表单撤销**接管这次按键。实测链条（每一步都读了读面）：

| 阶段 | `nameDom` | `nameStore` | 焦点 | 历史 | 账 |
|---|---|---|---|---|---|
| 改名已提交 | 改名试试706 | 改名试试706 | `camera-switch` | 1 条 `UPDATE_OBJECT` | `UPDATE_OBJECT` / `COMMITTED` |
| 焦点进 fov + 1 次 `ArrowRight` | 改名试试706 | 改名试试706 | `data-director-camera-fov` | 1 条 | `UPDATE_CAMERA` / `COMMITTED` |
| **按 `Cmd+Z`** | **机位01 · 对峙中景** | 改名试试706 | **`data-director-object-name`** | **2 条**（多了 `camera-fov`） | `GESTURE_COMMIT` / `COMMITTED` |
| **点画布** | — | **机位01 · 对峙中景** | 面板 | **3 条**（多了 `UPDATE_OBJECT`） | `UPDATE_OBJECT` / `COMMITTED` |

一次按键同时做了三件事：把旧值塞进**另一个字段**的 DOM、把焦点挪到那个字段、
并把顺手开着的手势**提交成一条历史条目**。下一次点击把那个暂存值提交掉 ——
**改名被静默回退，而且为这次回退新写了一条 `UPDATE_OBJECT` / `COMMITTED`。**
用户全程没碰过那个名字框。

对照臂（同样先改名、同样点画布、**不发** `Cmd+Z`）：名字不变、历史仍是 1 条
⟹ 回退不是画布点击造成的，`Cmd+Z` 是必要条件。

## 判据 6：账本上那一条属于谁，取决于你什么时候读

`shot-end` 填 6：

| 读的时刻 | 账上最后一条 | 历史 |
|---|---|---|
| 刚填完（还没提交） | **`null`**（一条命令都没有） | 0 条，`endTime` 仍 8 |
| 按下 `Tab` 之后 | **`GESTURE_BEGIN` / `COMMITTED`** | 1 条 `UPDATE_SHOT`，覆盖 `.shots[0].endTime` |

条目是 `shot-end` 自己的（`UPDATE_SHOT`，只覆盖 `endTime`），
但**单槽账本最后写的是 fov 滑块那个手势** —— 它把真正的提交盖住了。
⟹ 704 表格里 `shot-end` 那格的 `GESTURE_BEGIN` 是**焦点副作用**，不是这一格的命令。

## 判据

| 判据 | 断言 |
|---|---|
| `the-open-gesture-belongs-to-the-next-focusable-slider-not-to-the-rejected-edit` | 四条臂：三条正向臂手势归 `camera-fov` 且焦点在滑块上；被拒臂 `endTime` 未变、历史 0 条（复现 704）；反向 Tab 无手势且焦点落 `body` |
| `three-arrow-presses-collapse-into-one-entry-covering-only-the-two-fields-touched` | 3 次方向键期间历史恒 0 条，收尾后恰好 1 条且覆盖范围等于那两个字段；鼠标臂同形状 |
| `escape-on-a-live-gesture-reverts-the-document-yet-is-ledgered-as-noop` | 值 43→46→43、两个 fov 叶子回滚、`timeline.selectedKeyframeId` **不**回滚、历史仍 0 条、账上 `GESTURE_CANCEL` / `NOOP` / `projectChanged: false` |
| `cmd-z-inside-a-focused-input-never-reaches-undo` | 两条输入框臂各按 2 次：history / store / 账 / 焦点四样都不变；对照臂记 `UNDO` |
| `cmd-z-stages-a-reverse-edit-that-the-next-click-commits` | 按下后 `nameDom` 已是旧名而 `nameStore` 仍是新名、焦点跳到该字段、顺手长出一条 `camera-fov`；点画布后 `nameStore` 回退且新写一条 `UPDATE_OBJECT`；对照臂同样点击无事发生 |
| `ledger-ownership-flips-with-timing` | 填完未提交时账为 `null`；`Tab` 后条目是 `UPDATE_SHOT`（只覆盖 `endTime`）而账上最后一条是 `GESTURE_BEGIN` |

## 本批自己踩的坑：第五次「读面太窄」，而且这次两个探针互相矛盾

**坑一：归属。** 第一版探针只读账上最后一条命令的 `commandKind`，
于是把 `Tab` 之后那条 `GESTURE_BEGIN` 记在了 `shot-end` 头上 ——
和 704 犯的是同一个错。**读命令的 `commandKind` 不等于读这条命令属于哪个控件。**
必须同时读 `activeGesture.commandKind` 和 `document.activeElement`。

**坑二：两个探针对同一个按键给出相反读数。**
探针 a 记「`Cmd+Z` 什么都没发生」，探针 d 记「`Cmd+Z` 提交了手势、改名被回退」。
两轮都是真读数，差别在**前置状态**：a 的文档表单历史里没有键入过，d 有。
拆成 5 条臂（E1–E5）才定位到那个变量。**自相矛盾的两轮不是「其中一轮错了」，
是「两轮测的不是同一个状态」** —— 和 696 那条纪律同源，但这次是它第一次真的救了本批。

**坑三：自己点的鼠标动作也在手势里。** 第一版用 `el.click()` 点 range，
而点击 range 会**跳值**并且 `pointerup` 会**提交**（`onPointerUp` 只豁免 `type="number"`），
于是第一次点击自己造了一条条目、把 4 次方向键挤进第二条。
改用 `Tab` 进滑块的纯键盘路径之后形状才干净。**探针自己的每个动作都在污染下一次读数。**

**坑四：判据自己写错两处，两处都是「我以为的比实测的整齐」。**
判据 1 拿 `focus == "body"` 比，而读面返回的是 `tagName`（`BODY`）—— 大小写，不是被测物变了；
判据 3 断言「这一段变化过的叶子全部回到基线」，而 `selectedKeyframeId` 真的没回滚 ——
**这条不是判据错，是发现**：取消只还原文档、不还原选择态。改成断言真实形状，
并把「哪个叶子没回滚」本身写成读数。**判据失败时先问「是判据的形状太整齐，还是被测物不齐」。**

## 待拍板（不阻塞）

- `Cmd+Z` 在输入框内既不撤销、又会给下一次交互埋一个反向编辑 —— 建议在输入框内接管 `Cmd+Z` 走 `undoDirector`，并对 `isEditable` 早退放宽到修饰键
- `GESTURE_CANCEL` 回滚了文档却记 `projectChanged: false` / `NOOP` —— 账上要不要给回滚一个自己的 disposition
- 手势开着时界面上**没有任何**可见反馈（`[data-director-workspace]` 的 `data-director-active-gesture` 带着手势 id，但那是测试钩子，不是 UI）
