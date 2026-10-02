# batch 647 —— 给 `own` 的两个候选修法**定价**：一个在修，一个在让量具闭嘴

## 一句话

646 挖出普查的第三个盲区（`own` 接受祖先命中 ⇒ 被裁掉的控件读成「干净的」），
并留下一个显然的修法 `own := paintedAtCentre`。**本批去给这个修法定价，
量出来的结论是：那个修法会撤销已有的发现而不修任何东西。**
真正的修法是把「可见性」和「可点性」合取成 `ownTop`，爆炸半径恰好等于 646 的盲区。

## 1. 为什么 `paintedAtCentre` 顶替 `own` 是错的

两个判据问的是**两个不同的问题**：

| 判据 | 问题 | 谓词 |
|---|---|---|
| `own`（现状） | 点击有没有落到我头上？ | 可点性 |
| `paintedAtCentre` | 我在不在命中栈里？ | **可见性** |
| `ownTop`（本批提出） | 我在栈里**而且在栈顶**吗？ | 两者合取 |

646 测到的是它们在**一个方向**上的分歧（被裁掉 ⇒ 绘制没了、DOM 树还在）。
但它们在**另一个方向**也分歧：一个控件可以**被绘制着、却仍然被别的东西压在上面**。
拿 `paintedAtCentre` 顶替 `own`，会把这种控件记成 `clean`。

### 40 格实测（8 宽度 × 5 窗高，横跨两族）

| | 新增缺陷主张 | 撤销已有判定 | 移动总数 |
|---|---|---|---|
| `paintedAtCentre` | **0** | **116**（40 格里 32 格非空） | 136 |
| `ownTop` | **0** | **0** | **20** |

**一个只会把控件推向 `clean`、从不指控的判据，是量具被叫去闭嘴的签名，不是量具被修好。**

## 2. 最贵的一条：那个修法会把 632 的在案缺陷退休掉

    收起   box=[64, 5.5, 40, 40]   @339x900（339 的 5 个窗高全部命中）
      现状        covered     ← 632 的 170px 居中视角组压住它；640 每次运行都在断言
      painted     True        ← 它**画在那里**，只是不在最上面
      ownTop      False
      命中元素    导演视角机位视角

- `paintedAtCentre` 修法 ⇒ `收起` 变 **`clean`**，`covered` 计数 1 → 0，
  **632 那个在案缺陷就此消失，而它其实还在。**
- `ownTop` 修法 ⇒ `coveredNow` 与 `coveredTop` 在 40 格里**逐格相同**，
  缺陷原样保留。

`收起` 是**可见但不可点**，正好落在两个判据分歧的那一侧。
把可见性判据当可点性判据用，第一个被牺牲的就是「可见但被压住」这一族。

## 3. 撤销的 116 条，按来源拆开

不是一条都不该动 —— 其中 5 条是**真改善**。但真正被吞掉的判定是 111 条：

| 从哪个桶撤销 | 条数 | 是什么 |
|---|---|---|
| `timelineOverlay` | **95** | 628 的**源站事实**族豁免（时间轴盖住三列的下段） |
| `viewportSqueeze` | **11** | 629/630 的**有界**豁免族 |
| `covered` | **5** | **632 的在案缺陷**（339 的 5 个窗高） |
| `clipped` | 5 | **真改善** —— 见下 |

那 5 条 `clipped → clean` 不是损失，是 646 那条「矩形测试 ≠ 中心测试」
在判决层第一次显形：控件的盒子越出了自己的滚动盒 1px 以上（`isClipped` 的
矩形判真），但**中心点仍完整绘制、仍在栈顶**，所以它其实一直是可点的，
`clipped` 这个「滚回来就能点」的记账本身就是错的。

**撤销量随视口变矮而增长**，而且是在普查最卖力的地方增长（`timelineOverlay`
本来就是矮视口下的产物）：

| 宽度 \\ 窗高 | 400 | 560 | 720 | 900 | 1150 |
|---|---|---|---|---|---|
| 339 | 3 | 1 | 1 | 1 | 1 |
| 620 / 768 | 2 | 0 | 0 | 0 | 0 |
| 899 / 1020 / 1152 / 1440 / 1920 | **14** | 4 | 1 | 1 | 1 |

8 个宽度**无一例外**满足「最矮窗高的撤销量严格大于最高窗高」。

## 4. `ownTop` 的爆炸半径

    ownTop = el 或 el 的后代 ∈ 命中栈，且是**栈顶**

- 40 格里共移动 **20** 条，逐格检查断言**唯一可能的移动是 `clean → clipped`**。
- 新增缺陷主张 **0**，撤销已有判定 **0** —— **两个方向都安全**。
- 移动总数 **20** 与 646 盲区例数 **20** 逐格相等：移动格恰是
  宽度 620 / 768 / 899 / 1020 × 全部 5 个窗高，**每格恰好 1 条**。
- 两个候选修法把**同一批控件**归进 `clipped`（`tightClipped` 与
  `topClipped` 逐格相同）；它们唯一的分歧就是「绘制着但被压住」那一族怎么办，
  而 `ownTop` 是**继续报**的那一个。

646 那个显式修法 `own := paintedAtCentre` 因此**被否掉**，不是被改进。

## 5. 646 的机制断言跨过高度轴仍然成立

646 在**一个窗高**上断言「每个盲例都被裁」且「每个盲例都走祖先那一支」。
本批把窗高变成第二个轴（5 个），两条断言在 40 格里**仍然全成立** ——
这正是 `ownTop` 敢被提名的前提：若出现「被 `own` 判成干净、却**不是**被裁」
的例子，收紧就会**造出**新的缺陷主张。

盲区在本网格里出现的控件：`删除关键帧` / `模型库` / `移除角色01 · 陈默 · 变换轨道`
（646 那四枚里的三枚；第四枚 `添加关键帧` 的窗口是 703–711 与 899–963，
本网格未取那两个宽度）。

## 6. 第二条独立证伪通道：合成（opacity）

646 用**裁剪**证伪了 `own`。**一个机制不等于唯一机制。**
`opacity` 不继承，所以 `opacity: 0` 的包裹层不可见、里面的控件照样接得到点击。
（`visibility` 是继承的，`getComputedStyle(el).visibility` 已经能看到祖先的值；
祖先 `display: none` 会把整棵子树移出命中测试。**只剩合成这一条。**）

40 格实测 **`invisibleButOwn` 0 条、`paintedButFaded` 0 条**。
但**空集不算证据** —— 未被验证过的量具报零，什么都不证明。所以本批**注入探针自证**，
三枚同几何的合成控件，只差一个 `opacity` 包裹层：

| 探针 | own | painted | top | invisibleButOwn | paintedButFaded | minAncestorOpacity |
|---|---|---|---|---|---|---|
| `P647-bare`（无包裹） | true | true | true | false | false | 1 |
| `P647-faded`（0.5） | true | true | true | **false** | **true** | 0.5 |
| `P647-fader`（0） | true | true | true | **true** | **true** | 0 |

阈值从**两侧**都钉住了：只测 0.5 那一档的话，量具分不开「变淡」和「不可见」。

### 顺带当场证伪 646 的字段名

`P647-fader` 是**全透明**的，而它的 `paintedAtCentre` 是 **`True`**。
`paintedAtCentre` 量的是**在不在命中栈里**，**不是**「有没有可见像素」。
字段名与所测之实不符 —— 而**用一个叫「painted」的字段顶替 `own`，
正是踩在这个错上**。

字段名**不改**（改一个已落盘契约的名字不是本批的营生，且会牵动 646 的读数），
但纠正写在案上，反例也在案上。

**本通道的边界**（不声称）：只测了 `opacity`。`filter: opacity(0)`、
`mix-blend-mode`、`content-visibility: hidden` **未测**，仍然开着。

## 7. 共享判据的改动（只增不改）

`scripts/verify-liblib-batch617.py`：**新增 200 行 / 删除 0 行**（`git diff --numstat`）。

新增字段（`items[]`）：`ownTight` / `ownTop` / `topAtCentre` / `bucketNow` /
`bucketTight` / `bucketTop` / `newDefectClaim` / `newDefectClaimTop` /
`silencedNow` / `silencedTop` / `minAncestorOpacity` / `invisibleButOwn` /
`paintedButFaded` / `faderSurface`。

新增返回值：`counterfactual`（含三列桶计数、两套移动直方图、
两类「新增指控 / 撤销判定」的清单与来源直方图、`tightClipped` / `topClipped`）、
`invisibleButOwn`、`paintedButFaded`。

**`own` 与全部既有判定一个字没动** —— `clipped` / `panel` / `timelineOverlay` /
`viewportSqueeze` / `unexplained` / `blocked` / `covered` /
`bothCoveredAndClipped` / 646 的 `paintedAtCentre` / `ownButNotPainted` 全部原样。
理由与 642/643/646 相同：改共享判据的唯一条件是**只增不改 + 机械零回归证明**。

**零回归机械证明**：639（15 checks）与 640（14 checks）重跑后，
两份**已落盘** audit 与 HEAD **逐字节 IDENTICAL**（`git diff --quiet`）。

## 8. 我自己写错的一处

检查 `the-paint-repair-would-retire-632s-standing-defect-…` 第一版把**极性写反了**：
它要求 `retiredByTopRepair` **非空**且 paint 修法的 `covered` 下降**不存在**。
也就是说，它**把失败模式当成了成功模式**去断言 ——
真要是 `ownTop` 把 632 的缺陷退休了，那一版会判绿。

红是对的、断言是错的。数据反而比我想断言的更强：
`retiredByTopRepair: []`（top 修法一条都没退休）、
`coveredCountDroppedByPaintRepair` 在 339 的 5 个窗高上各 1 → 0。
改成「top 修法撤销的必须**为空**、paint 修法的下降必须**非空**、且
339x900 的 `coveredTop` 必须与 `coveredNow` 逐条相同」。

## 9. 本批**不**主张的事

* **不主张**改了判据。`own` 未动，只**加了对照列**。
* **不主张** `ownTop` 就是最终答案。它只被证明**两个方向都无害**且**方向单一**；
  换不换仍然是政策题。
* **不主张** 632 的 `收起` 缺陷该修 —— 那是 clone-only，仍卡源站读数。
  本批只证明**它还在**，以及一个候选修法会把它抹掉。
* **不主张** 合成通道在 clone 之外也空 —— 本批只测了 40 格，且只测了 `opacity`。
* **零源站断言**。

## 10. 门禁

- `scripts/verify-liblib-batch647.py`：**15 checks / 0 failures**，40 格 + 1 个自证格。
- 共享判据纯增量 **200 / 0**。
- 零回归：639（15 checks）+ 640（14 checks）重跑，两份 audit 逐字节 IDENTICAL。
- `npm run lint` / `npm run typecheck` / `npm run build` / `npm run docs:check`
  见提交说明（既有 flake 按路径归因，不在本批）。
