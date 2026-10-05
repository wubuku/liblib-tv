# batch 785 —— 更正 784 的覆盖面：**3 有 / 7 没有** ⟹ **4 有 / 6 没有**

> 日期：2026-10-01 ｜ 范围：782 普查出的 10 个**可写门状态**的外点关闭覆盖面
> ｜ 本批**未改 `src/`**（收尾时确认工作区 `src/` 零改动）、无注入、不做破坏性操作
> ｜ 汇编器断言 **16 条 / 27 个行锚点 / 0 失败**；验收 **14/14**、阴性对照 **7/7**

## 本批是**更正自己上一批的静态结论**

784 报「11 个 `Escape` 主人的门状态里**只有 3 个**有任何外点关闭，其余 7 个没有」。
本批复查发现**三处**错，其中两处让覆盖面数字偏小、一处让 **key 本身就是错的**。

## C785-1：3 有 / 7 没有 ⟹ 更正为 **4 有 / 6 没有**

### 更正一：`set<S>(null)` 判据造成**假阴性**

784 的判据是「监听器自己的处理器体里直接出现 `set<S>(null)`」。
但「关掉」是一个**语义族**（`null` / `false` / `undefined`），不是一个字面量：

| 状态 | 监听行 | 关写行 | 关写实参 |
| --- | --- | --- | --- |
| `modelLibraryOpen` | `DirectorViewport.tsx:2747` | `:2739` | ★ `setModelLibraryOpen(false);` |

⟹ 模型库**有**外点关闭，784 漏了它。

### 更正二：key `open` **不是可写状态**，784 从没找过真正的那个

783 把 `PhoneVcamPanel` 的门记成 `open` —— 那是 **prop**：

| 步骤 | 证据 |
| --- | --- |
| 面板把 `open` 当参数解构 | `DirectorPhoneVcamPanel.tsx:96` `open,` |
| 类型标注是 `boolean`、不是 state | `DirectorPhoneVcamPanel.tsx:99` `open: boolean;` |
| ★ 真状态在这里声明 | `DirectorViewport.tsx:2544` `const [phoneVcamOpen, setPhoneVcamOpen] = useState(false);` |
| 父组件以 `open=` 透传 | `DirectorViewport.tsx:3080` `open={phoneVcamOpen}` |
| 唯一的**关闭**路径由父组件接上 | `DirectorViewport.tsx:3081` `onClose={() => setPhoneVcamOpen(false)}` |

784 把它**硬编码**进了 `census784.py:57` 的 `STATES` 清单 ⟹ **两批都从没找过真状态**。

★ **归属要更正**：784 的 raw 里 `open` 记的是 **`[]`（没有外点关闭）**。
所以**没有发生**「`setOpen(false)` 属于 `TopNavBar` 的另一个 `open` ⟹ 跨文件撞名算成有」——
那是本批第一版普查器自己写进产物的**错误理由**。784 的错是**整个漏掉一个门状态**，
恰好落进同一个桶 ⟹ 桶数只动了一次（3→4），**分母从来没对过**。

★ **所以「把 `open` 剔除」也是错的**：那会让分母从 10 掉到 9，
把 vcam 面板从「无外点关闭」的风险面里**藏起来**。正确动作是**改名**。

### 更正后的完整清单

| 分类 | 状态 |
| --- | --- |
| 第①类·**有**外点关闭（4） | `contextMenu`、`modelLibraryOpen`、`pathMenuLeft`、`presetPanelLeft` |
| 第②类·**无**外点关闭（6） | `activeDirectorNodeId`、`exportPanelOpen`、`followTargetId`、`motionPathDraft`、★ `phoneVcamOpen`、`viewerCaptureId` |

⟹ 「**没有全局保障**」这个大结论**仍然成立**，但支撑数字从 3/7 换成 4/6。

## C785-2：4 个外点关闭的**事件全是 pointer 类**

| 状态 | 事件 | 目标 | 注册行 |
| --- | --- | --- | --- |
| `contextMenu` | `mousedown` | `window` | `DirectorObjectTree.tsx:212` |
| `modelLibraryOpen` | `pointerdown` | `document` | `DirectorViewport.tsx:2747` |
| `pathMenuLeft` | `pointerdown` | `window` | `DirectorTimeline.tsx:569` |
| `presetPanelLeft` | `pointerdown` | `window` | `DirectorTimeline.tsx:593` |

784 把风险形状写成「逐个手写、仓里没有统一机制」。这句**不准确**：
**4 个全是 pointer 类事件** ⟹ 键盘 `Enter` 激活 `<button onClick>` **一律绕过**。

⟹ 真正的形状不是「写漏了」，而是「**只能用鼠标**」——
即使有人照着补齐第 5、第 6 个，也只会得到同一个键盘盲区。

## C785-3：D1i **纯鼠标也可达**，读数 782 就有了（本批**复用**，不跑浏览器）

784 报的是**键盘**路径。★ 但 782 的 `captureOwner` 臂早就是同一形态，而且纯鼠标：
**导出面板**（**没有任何外点关闭**）+ **模型库**（`pointerdown` 外点关闭）。

| 读数（从 782 raw **重算**） | 值 |
| --- | --- |
| 第①道·第 1 次按 Escape 的 `cap` | **0**（`sIP` 截断整条链，阶梯跑不到） |
| 第①道·第 1 次按 Escape 的 `win` | 0 |
| 第①道·第 1 次之后模型库 | 已关 |
| 第①道·第 1 次之后**导出面板** | ★ **仍在原地** |
| 第②道·第 2 次之后导出面板 | 关 |

⟹ **D1i 的严重度维持「中」，覆盖面比 784 写的更宽**：不止键盘路径。

★ 本批按 **R152**（同一形态的读数常被归档在不同框架下，先换框架重读既有 raw
往往比再跑一轮更值钱）**复用** 782 的 raw，**本批不跑浏览器**。

## ★ 顺带撞见的一条事实（结论留给 786）

查 `phoneVcamOpen` 的可写性时看到 `DirectorViewport.tsx:2825-2829`：

| 方向 | 证据 |
| --- | --- |
| 开模型库 ⟹ 关 vcam | `:2826` `setPhoneVcamOpen(false);` + `:2828` `setModelLibraryOpen((value) => !value);` |
| 开 vcam ⟹ 关模型库 | `:3538` `setModelLibraryOpen(false);` + `:3540` `setPhoneVcamOpen((value) => !value);` |

⟹ 两个方向**都**有交叉写入（与 783 在 `DirectorTimeline` 里发现的那对同形，但**在另一个文件**）。
★ 但「因此这两个状态**不能共活**」是**推论**，静态不可判 ⟹
本批只把**事实**用行锚定钉死（汇编器检查 G），运行时两方向验证**留给 batch 786**。

## 本批踩到的六个坑（都记成纪律）

| 编号 | 坑 | 修法 |
| --- | --- | --- |
| 第①道 | 第一版断言写「784 把 `open` 算成**有**外点关闭」⟹ **断言炸了** | 查 784 raw：它记的是 `[]` ⟹ 是**断言**错不是机制错，归属改写 |
| 第②道 | 第一版普查器**把 `open` 整个丢掉** | 改成改名 `phoneVcamOpen`，并在产物里写明为什么不能丢 |
| 第③道 | 想用正则判据「`set<S>(` 在主人文件里被调用过」⟹ **当场失败并作废** | 三个真状态是**对象字面量键**形态（不过判）；`setOpen(` 全仓 **38 处**（误过判）⟹ 改由汇编器行锚定 |
| 第④道 | 验收器的阴性对照**改了源码却没复原**（复原函数塞进了空 lambda） | 复原内建且强制（`finally`），并加 **S14 核对字节一致** |
| 第⑤道 | ★ **基线本来就红**，于是每条阴性对照的 `flipped` 里都出现那一项 ⟹ **7/7 全是假通过** | 基线不全绿**直接断言失败**，不许开跑 |
| 第⑥道 | `DirectorTimeline` 里 `close` 有**两个同名**处理器 ⟹ 按名回查分辨不出，只改一个翻不了 | 对照改成**两处一起改**；两种方法（行锚定 / 按名重算）互为兜底 |

## 交付物

| 文件 | 作用 |
| --- | --- |
| `probes/census785.py` | 普查器：只**采集**外点关闭命中 + 每个 key 的全部写入点 |
| `probes/mk785audit.py` | 汇编器：**行锚定字面量**从源码下结论，再与普查器**对账** |
| `scripts/verify-liblib-batch785.py` | 验收器：**独立**重算（状态优先 + 括号链，与普查器方法三样都不同） |

★ **三方对账**：汇编器（源码行锚定）、普查器（正则扫描）、验收器（状态优先重算）
三个**独立**实现必须给出同一份清单，否则验收器直接判红（S12）。

## 不覆盖的（显式列出）

- `viewerCaptureId` 在 clone 默认数据下**不可达**（`[data-director-capture-view]` 命中 0）
  ⟹ 不能当共活搭档 ⟹ 纯鼠标那一路改用 `exportPanelOpen`
- 「某个状态能不能被置上」是**可达性**问题，逐条单列
- **交叉写入不在本普查**：783 的 `crossWrites` 层另有**两处**缺陷
  （prop 状态被下游静默剔除 / 内联 JSX 箭头不被包裹函数正则匹配 ⟹ `fn` 误归），
  加上本批撞见的第②类事实 ⟹ 全部留给 batch 786
