# batch 746 — A 档剩下 4 个命令逐个走完：**`createLongVideoProcess` 有一条被菜单藏起来、芯片能进的路径；同一个「已加入本地任务」提示，真假各有一条**

## 起点

744 把 16 个记账命令分成 A 档 8 / B 档 8；745 把 B 档 7 个逐个走完（5 真跑 / 2 被时长挡住）。
A 档里只验过 3 枚尝试芯片，`createLongVideoProcess`、选特效（`addNodeAtPosition` + `addEdge`）、
`destroyFirstFrameReference`、`clearVideoContinuation` 这 4 个**还没真跑过**。

全部读数来自 clone，**不碰源站**。

## 汇总表：A 档 8 个命令的运行时状态

| 命令 | 入口 | `past` | 节点 | 边 | 本批结论 |
|---|---|---|---|---|---|
| `createFirstFrameReference` | 芯片 | +1 | ±0 | ±0 | 744 已跑（failed 卡上只写 `attempt`、跳过建图） |
| `createFirstLastFrameReference` | 芯片 | +1 | ±0 | ±0 | 744 已跑（同上） |
| `updateNodeData`（`setAttempt`） | 芯片 | +1 | ±0 | ±0 | 744 已跑 |
| `addNodeAtPosition` + `addEdge`（选特效） | 4 张效果卡 | **+2** | **+1** | **+1** | 746 真跑 |
| `destroyFirstFrameReference` | hover 才显现的「销毁」 | +1 | **−1** | **−1** | 746 真跑 |
| `clearVideoContinuation` | 条件渲染 | — | — | — | 746 只验到「入口条件不满足」 |
| `createLongVideoProcess` | **芯片**（不在模式菜单里） | **+1** | **+12** | **+22** | 746 真跑通 |

（`selectNodeOutput` 等不在 `VideoNode` 内，其运行时状态见 744 的分档表。）

## 决定性读数

### ① `long-video` 在模式菜单里进不去，但芯片能进 —— **两条赋值路径**

```
VideoGenerationPanel.tsx:110  { id: "long-video", label: "超长视频",
                                 disabled: true, inMenu: false, badge: "Beta" }
VideoGenerationPanel.tsx:974  .filter((item) => !("inMenu" in item && item.inMenu === false))
VideoGenerationPanel.tsx:172  const isLongVideo = mode === "long-video";
VideoGenerationPanel.tsx:225-229  if (attempt === "5分钟超长视频") {
                                     setMode("long-video");   // ← 芯片路径，菜单管不着
                                     setModel("2.5"); setRatio("Auto"); setDuration(300);
                                   }
```

模式菜单实测 5 项，**没有 `long-video`**：

| `data-video-mode-option` | 文案 | `disabled` |
|---|---|---|
| `text` | 文生视频 | `false` |
| `omnireference` | 全能参考 | `true` |
| `image` | 图生视频 | `true` |
| `first-last` | 首尾帧 | `true` |
| `image-reference` | 图片参考 | `true` |

但点节点卡的**「5分钟超长视频」芯片**之后：

| | 芯片前 | 芯片后 |
|---|---|---|
| 模式触发器 | 文生视频 | **超长视频** |
| 参数触发器 | `16:9 · 720P · 5s · 1个` | **`Auto · 720P · 300s · 1个`** |
| `data-video-long-submit-state` | **属性不存在** | **`"idle"`** |
| 「查看过程」按钮 | 无 | **有** |
| `past` | 1 | 2（芯片自己记一条） |

⟹ **模式菜单的 5 项里没有「超长视频」，但面板上会显示「超长视频」。**
用户进得去（芯片）、也退得出（见 ④），但**看不到自己在哪个模式里** ——
8 个 `modeItems` 里有 **3 个 `inMenu: false`**（`video-edit` / `long-video` / `first-frame`）。

### ② `createLongVideoProcess` 真跑通：`past` +1、节点 **+12**、边 **+22**

| 时刻 | `long-state` | `title` | 图标 | `disabled` | 页脚「过程」钮 |
|---|---|---|---|---|---|
| 芯片后 | `idle` | 生成视频 | 上箭头 | `false` | 查看过程 |
| 点后 250ms | `submitting` | 正在创建本地过程 | **spinner** | **`true`** | 查看过程 |
| 520ms 后 | `created` | 已加入本地任务 | **对勾** | `false` | **返回编辑** |

store：`past` 2→**3**、节点 11→**23**、边 11→**33**，
其中 `long-video-process` 类型 **12** 个。

### ③ 静态写点与运行时读数**逐个对平**

`canvasStore.ts:2244 createLongVideoProcess` 一次建出：

| | 静态写点 | 个数 |
|---|---|---|
| 节点 | `makeProcessNode({` 在 `:2332/2341/2350`（material）+ `:2361/2370/2379`（shot）+ `:2390/2400/2410/2420`（candidate）+ `:2431`（assembly）+ `:2439`（final） | **12** |
| 边 | `:2462` `source→shot` 3 + `:2463-2468` `material→shot` 6 + `:2469-2476` `shot→candidate` 8 + `:2477-2479` `candidate→assembly` 4 + `:2480` `assembly→final` 1 | **22** |

⟹ 运行时实测 **+12 / +22**，两个数都对得上。

顺带记录：`createLongVideoProcess:` 在全文件恰好出现**两次** ——
`:348`（store 类型里的**接口声明**）与 `:2244`（**函数实现**）。
静态扫描取的是**后一处**；只按第一个匹配点切段落会数出 0 个写点。

### ④ **同一个「已加入本地任务」提示，真假各有一条**

| | 非长视频路径（默认态） | 长视频路径（芯片后） |
|---|---|---|
| `data-video-long-submit-state` | **属性不存在** | `idle` → `submitting` → `created` |
| 提交中 `disabled` | `false`（**无防重入**） | `true` + spinner |
| 提交中 `title` | 「生成视频」不变 | 「正在创建本地过程」 |
| 终态 `title` | **「已加入本地任务」** | **「已加入本地任务」** |
| 终态图标 / 底色 | 对勾 / 变蓝 | 对勾 / 变蓝 |
| **`past`** | **+0** | **+1** |
| **`nodeIds` / `edgeIds`** | **逐项完全相同** | 真写入 |

```
VideoGenerationPanel.tsx:308-312
  const submitVideo = () => {
    if (!isLongVideo) {
      setSubmitted(true);   // ← 纯组件态，一个字节都不写 store
      return;
    }
```

而 `:852-863` 的底色 / 图标 / `title` 三元**不区分 `isLongVideo`** ⟹
**非长视频分支复用了长视频的整套「已提交」反馈，却什么都不做。**
撒谎的不是那句话，是那个早退分支借用了别人的反馈。

⟹ 附带：非长视频路径**没有防重入**（提交中 `disabled` 恒 `false`、无 spinner）；
长视频路径有 `longVideoSubmitting` + `longVideoSubmitTimerRef` 双重守卫（`:313-319`）。
**同一枚按钮，两条路径的并发语义不同。**

### ⑤ 退出路径：进得去，也退得出

长视频态下从模式菜单选「文生视频」⟹ `:268-270` 顺带清掉芯片：

| | 退出前 | 退出后 |
|---|---|---|
| 模式触发器 | 超长视频 | **文生视频** |
| 参数触发器 | `Auto · 720P · 300s` | `Auto · 720P · 30s` |
| 「查看过程」按钮 | 有 | **无** |
| 该卡 `attempt` | `5分钟超长视频` | **`None`** |
| 节点 / 边 | 23 / 33 | **23 / 33（过程节点不删）** |

⟹ 模式状态退出了，但**已经建出来的 12 个过程节点 + 22 条边留在画布上**，
只能靠撤销（`past` +1）回去。

**「5分钟超长视频」芯片不是 toggle**：在芯片**仍激活**时再点一次同一枚 ⟹
`past` +1 但页脚、模式、节点、边**逐项零变化**（与 `:218` 注释「芯片非 toggle」一致）。

### ⑥ 选特效：**一次点击记两条账**

`[data-effects-trigger]` 打开横排 4 张效果卡，点第一张「试妆特写」：

| | `past` | 节点 | 边 | 新文件 |
|---|---|---|---|---|
| 前 → 后 | 1 → **3**（**+2**） | 11 → **12** | 11 → **12** | `素材 - 特效 - 试妆特写` |

`addNodeAtPosition`（建 `image` 节点）与 `addEdge`（连线）是两次独立记账
⟹ **`past` +2，撤销要点两次才完全回退**。（用户视角是「一次点击」，历史栈视角是「两步」。）

### ⑦ 销毁首帧：**hover 目标是外层整条 slot，不是缩略图**

```
VideoGenerationPanel.tsx:736  <div data-video-firstframe-slot className="group mt-1 flex w-full …">
VideoGenerationPanel.tsx:747                  className="absolute inset-0 hidden items-center justify-center … group-hover:flex">
```

`group` 类挂在外层 slot 上，而按钮是**内层 48×55 槽**的 `absolute inset-0`：

| | `display` | 盒子 | 说明 |
|---|---|---|---|
| hover 前 | `none` | **0×0（恒在原点 0,0）** | `elementFromPoint` 证明 group 中心命中 slot 内 |
| hover 外层 slot 中心 (640, 732) | `flex` | **46×53** | 外层 slot 实测宽 **642px** |

⟹ 在这 **642px 宽**的整条 slot 上任意位置悬停，都会在 **48px 宽**的缩略图上
冒出「销毁」—— **悬停区比可见控件宽 13 倍**。

点它：`past` +1、节点 −1、边 −1、该卡 `attempt` 归 `None`。
造 `attempt` 之前按钮**根本不在 DOM**（`onDestroyFirstFrame` 传空）。

### ⑧ 清除续写：**条件渲染**

`isContinuation && onClearContinuation` ⟹ 新建 ready 卡 `continuation = None` 时
`[data-video-continuation-exit]` 根本不渲染（开合菜单各试一次仍为 0 枚）
⟹ 要先经「智能续写」两段式建出 continuation 才够得着。

## 探针与静态推理返工五处（**四处是我自己的错，一处是判据写错**）

1. **我自己的静态推理漏了一条赋值路径**（本批最重要的一次返工）——
   第一版只追了 `selectMode`（菜单那条 `setMode`）就断言 `mode` 永远到不了 `"long-video"`
   ⟹ `createLongVideoProcess` 是死代码。实际 `:226` 在 `prevAttempt` 重放块里
   **另有一条** `setMode("long-video")`，由芯片触发。
   **根因是判据 C1 第一版只断言了我已经读到的东西 —— 等于没断言。**
   ⟹ 规矩补一条：静态断言某个变量的取值前，必须穷举该变量的**全部**赋值点
   （`setX` / 直接 `x=` / props 传参 / 派生 `useMemo`），而不是只跟一条调用链。
2. **静态扫描把「声明」当成了「实现」** —— `createLongVideoProcess:` 全文件两处
   （`:348` 接口声明、`:2244` 实现），取第一个匹配点切段落 ⟹ 静态写点读成 **0**。
   改法：取**最后一处**，并把两处行号都记进判据。
3. **C3 第一版点不到按钮** —— 用 `Escape` 想收掉模式菜单，实际 `Escape` 走画布级
   **取消选中**（实测选中数 1→0）⟹ 整块 `VideoGenerationPanel` 卸载，
   `[aria-label="生成视频"]` 自然不在 DOM ⟹ `clicked=False`。
   改法：用同一枚触发器再点一次关菜单，不碰 `Escape`。
4. **C3 第一版判据选错测点** —— 以为 `data-video-long-submit-state` 会变 `created`，
   但它被 `isLongVideo` 门控、在非长视频路径上整段不存在。改判 class 底色 / `title` /
   图标字形（Lucide 的 `svg.lucide-check`、`svg.lucide-loader-circle` vs 原始
   `svg[aria-hidden]`），并**另开一条芯片路径**去读同一个属性。
5. **C9 的前置条件搭错了** —— 我把「再点同一芯片」接在「退出长视频」**之后**，
   那时芯片已被清、再点是**重新进入**，页脚当然变。芯片是否 toggle 必须在
   **芯片仍激活**时连点。改法：把 C9 挪到 C8 之前，各自带独立基线。

还有一条通用教训：**「按元素自身盒子做真实交互」的探针必须先确认元素可见** ——
`display:none` 时 `getBoundingClientRect()` 不报错但恒为 0×0，鼠标坐标是垃圾
（本批 C7 第一次就踩了，把鼠标移到了屏幕左上角）。

## 判据（11/11）

| | 判据 | 读数 |
|---|---|---|
| C1 | 静态：`long-video` 是 `inMenu:false`（被 `:974` 过滤），但 `:226` 有 `setMode("long-video")` ⟹ 存在第二条赋值路径；且 `createLongVideoProcess` 恰好两处（`:348` 声明 + `:2244` 实现） | 两处行号 + `:226` |
| C2 | 运行时：模式菜单里**没有** `long-video` | 5 项 |
| C3 | 非长视频路径点「生成视频」：store 零写入（`past`/节点/边/`nodeIds`/`edgeIds` 全同），但按钮变蓝 + `title` 变「已加入本地任务」；`long-state` 属性整段不存在 | `1→1` / `11→11` / `11→11` |
| C4 | 芯片路径：芯片 ⟹ 模式触发器「超长视频」+ `long-state` 变 `idle` + 「查看过程」出现；点生成视频 ⟹ `submitting`(`disabled`) → `created`，`past` +1、节点 +12、边 +22、「返回编辑」出现 | 全链路逐项 |
| C5 | 对账：静态 12 个 `makeProcessNode` 写点、22 条边 ⟺ 运行时 +12 / +22 | 12 / 22 / 12 / 22 |
| C6 | 选特效：节点 +1、边 +1，**`past` +2** | `1→3` / `11→12` / `11→12` |
| C7 | 销毁首帧：group 挂外层 ⟹ hover 后 `display:none→flex`、尺寸 0→非 0；点它 `past` +1、节点 −1、边 −1、`attempt` 归 `None` | group 宽 642、按钮 0×0→46×53 |
| C8 | 退出路径：长视频态下从模式菜单选 `text` ⟹ 芯片被清、模式回落、过程节点**不删** | `attempt: None`、23/33 不变 |
| C9 | 芯片不是 toggle：**仍激活时**再点一次同芯片 ⟹ `past` +1 但页脚与节点/边/模式逐项零变化 | `footIdentical: true` |
| C10 | 清除续写：无 `continuation` 时按钮不渲染 | `False` / `False` |
| C11 | A 档汇总表 7 行齐 | 7 行 |

两轮连跑 **0 字段差异**（随机节点 id 未进 `runtime-audit.json`）。

## 待拍板（需改 `src/`，等授权）

1. **非长视频分支的「已加入本地任务」要不要收掉** —— `:308-312` 那个只
   `setSubmitted(true)` 就 return 的分支，借用了长视频的蓝底 / 对勾 / `title` 三元。
   最小改法：`title` 与底色都加上 `isLongVideo &&` 前置条件，别的模式点它就**什么都不提示**。
2. **「超长视频」这个模式要不要给个可见的来源标注** —— 面板触发器显示「超长视频」，
   但模式菜单里选不到它（`inMenu: false`）。最小改法：菜单里那枚**当前选中**的模式项
   即使 `inMenu: false` 也渲染出来（只读、不可点）。
3. **退出长视频后 12 个过程节点 + 22 条边要不要跟着清** —— 现在模式退回「文生视频」，
   过程节点留在画布上，只能靠撤销。
4. **非长视频路径要不要补防重入** —— 现在 `disabled` 恒 `false`、无 spinner，
   与长视频路径的并发语义不一致。
5. **选特效要不要合并成一条原子历史** —— 现在一次点击记两条账，撤销要点两次
   （`onSelectEffect` 里 `addNodeAtPosition` + `addEdge` 需共用一个 `historySnapshot`）。
6. **销毁首帧的悬停区要不要收窄** —— `group` 从 642px 外层 slot 挪到 48px 内层槽
   （`:736` / `:737` 加/去 `group`），否则悬停区比控件宽 13 倍。
7. **「5分钟超长视频」芯片要不要做成 toggle** —— 现在再点只多记一条历史、画面零变化；
   要么做成可取消，要么加一句说明「点此芯片不能取消」。

## 不声称

- **超长视频在源站是否可用 —— 未取证。** 也不声称 `inMenu: false` + `badge: "Beta"`
  是有意未开放还是遗留。
- **`clearVideoContinuation` 未真跑** —— 要先经「智能续写」两段式建出 `continuation`，
  本批只验到「入口条件不满足」。
- 选特效**只验了第一张效果卡**；4 张卡是否都建图 + 连线，未逐个验。
- 「素材 - 特效 - X」节点与视频节点的**连线方向、handle 类型**未验。
- 销毁首帧只在**新建的 ready 卡**上跑；种子 failed 卡（已有 image 入边）上点
  「销毁」的行为未验。
- `past +2` 的两条记录**各自的内容**（快照是否只差节点/边）未展开验，只验了条数。
- 长视频过程节点的**阶段内容**（标题/副标题/图片）未逐个验，只数了 12 这个总数
  并与静态写点对平；12 个 `long-video-process` 节点**是否会继续演进**
  （`status: "pending"` → …）未取证。
- 8 个 `modeItems` 里另两个 `inMenu: false` 项（`video-edit` / `first-frame`）
  **只从源码读到 `inMenu: false`**，未像 `long-video` 那样走芯片路径单独验。
- 「悬停区比控件宽 13 倍」只在本视口（1280×1150、面板 642px）测得，
  **不声称窄视口下同样是 13 倍**。
- 「模式菜单里没有它 ⟹ 用户看不到自己在哪个模式里」是**推断**（菜单确实无该项），
  但**源站是否也这样未取证**。

## 与前批关系

- **744「A 8 / B 8」** —— 本批把 A 档里剩下的 4 个走完，补上「有几条真跑过」这一维。
- **745「门控四层」** —— 本批给出**门控的另一半**：不是所有门控都阻止执行，
  `inMenu: false` 这类**配置项**根本不进入交互面（用户没有可点的入口），
  而芯片是绕过它的**第二条入口**。门控要分「条件挡住」与「入口不存在」两类。
- **743「两态按钮文案一致 / `status` 不是门控」** —— 得到边界补充：
  门控不只 `status` 一个维度，还有 `durationSeconds`（745）、`inMenu`（本批）、
  `selectedNodeCount`（744）、`attempt`（本批 ⑦）、`isLongVideo`（本批 ③）。
- **734 待拍板①「种子 fixture 取值是不是有意」** —— 与 745 的「新建卡默认 30 秒」
  同属一类；本批的 `inMenu: false` + `badge: "Beta"` 是同一族的第三个例子：
  **配置里的预留项本身就是 UI 的一部分**。
- **741「`pushHistory` 调用点与命令级清单逐个对平」** —— 本批把这条方法用在**节点数**上：
  静态 12 个 `makeProcessNode` 写点 ⟺ 运行时 12 个 `long-video-process`，
  静态 22 条边 ⟺ 运行时 +22。**一个对不上的数字自己就是线索。**
- **741「分清『声明』与『实现』」** —— 本批又踩了一次：`createLongVideoProcess:`
  的第一个匹配点是接口声明。纠正记在本批，历史批次不重写。

## 验收器

`scripts/verify-liblib-batch746.py` — 静态读 `VideoGenerationPanel.tsx` 与 `canvasStore.ts`
共 **20 个行号**（面板 18 + store 2），外加 `createLongVideoProcess` 段的 12 个写点与 22 条边
+ 模式菜单 5 项 + 非长视频路径 8 个观测量 + 芯片路径四时刻读数 + 静态/运行时对账
+ 选特效 + 销毁首帧 hover/点击 + 退出路径 + 芯片非 toggle + 续写入口条件，
两轮连跑逐字段一致。
