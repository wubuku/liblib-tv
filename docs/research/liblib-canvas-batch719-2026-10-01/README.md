# batch 719：场景描述 prompt —— 纯本地回显、store 零变化，而它恰好是默认够不到的那一枚

日期：2026-10-03　验收器：`scripts/verify-liblib-batch719.py`（7 条判据，零 store 写入，不改 `src/`）

## 起点

715/716/717 连着三批都指向同一件事：**底部条里被推出框外的，恰好是
「描述想搭建的场景」这个 prompt 输入框和它的发送按钮** ——
视口里最核心的输入，却是最难够到的控件。

那个控件（`DirectorScenePromptBar.tsx`）**从来没有被测过**。
本批补上：可达性、提交语义、反馈、修饰键、空值守卫、附件、以及 `aria-live`。

## 决定性读数

| 读数 | 值 |
|---|---|
| 打字 / 提交 / 上传 / 带附件提交 / 2 秒后，`objects` | **5 → 5** |
| `history.past` / `history.future` | **0 条 / 0 条**（始终） |
| `lastCommandResult` / `selection` | **null / null**（始终） |
| 提交反馈 | status `opacity` **0 → 1**，**2.2 秒后回 0** |
| 提交后输入内容 | **不清空**（草稿一直在） |
| 提交期间输入框 | `opacity: 0` —— **已输入的文本隐身 2 秒** |
| Enter / Shift+Enter / Control+Enter / Meta+Enter | **四种全部提交** |
| 空值 | 发送按钮 **`disabled = true`**；Enter **无任何反馈** |
| 纯空格 `'   '` | **同样** `disabled = true`、Enter 无反馈 |
| 上传附件后 status 文本 | **「已附上本地图片：X」** |
| 带附件提交时的 status 文本 | **仍是附件那句** ⟹ 提交确认被顶掉 |
| `aria-live="polite"` 区域的文本 | 打字前 / 提交后 / 2 秒后 **恒为同一串** |
| 1280 下 prompt 的命中测试 | 滚之前 **`other`（被 inspector 盖住）**，滚之后 `self` |

## 提交是纯本地回显：store 一个字段都没动

七个时刻（打字 / 提交 / 2 秒后 / 上传 / 带附件提交 / 带附件 2 秒后）逐字段读 store：
`objects` 恒 5、`pastLen` 恒 **0**、`futureLen` 恒 **0**、
`lastCommandResult` 恒 **null**、`selection` 恒 **null**。

⟹ 提交既不建对象、也不进历史、也不记账 —— 与组件注释
「本组件的提交只在本地回显草稿」一致。
**所以「已记录」这三个字是一次 2 秒的视觉替换，不是一次记录。**

## 四种 Enter 组合全部提交

`onKeyDown` 只判 `event.key === "Enter"`，**不看修饰键** ⟹
`Enter` / `Shift+Enter` / `Control+Enter` / `Meta+Enter` 全部触发提交
（status 0→1、输入框 `opacity: 0`、草稿保留）。

这与 706/707/708 立的那条纪律同族：**键位判定不看修饰键**。
同一个文件里另一处 `onKeyDown`（`DirectorViewport.tsx:2325`）值得单独测，本批未做。

## `trim()` 同时管住两件事，纯空格等同空值

| 输入 | `disabled` | 按 Enter |
|---|---|---|
| `'有内容'` | `false` | 提交 |
| `''` | **`true`** | **无任何反馈** |
| `'   '`（三个空格） | **`true`** | **无任何反馈** |

⟹ 「按钮点不动」与「按 Enter 什么都没发生」**不是两个缺陷，是同一个
`if (!value.trim()) return` 的两个入口**。
这是 707 那条「一个词装不下三种情况」的同族问题：
**两个无响应格，共享一个守卫。**

## 附件名把提交确认顶掉了

上传一张本地图片后，status 文本变成 **「已附上本地图片：dbg719-attachment.png」**。
此时再输入文字并提交：状态**确实变可见**（`opacity: 1`），
但**文本仍是附件那句** —— 「场景描述已记录（本地草稿）」**一次都没出现过**。

⟹ 有附件时，提交反馈被附件状态遮蔽；附件状态本身也不会被 2 秒计时器清掉。

## `aria-live="polite"` 区域的内容恒定

打字前、提交后、2 秒后，status 的 `textContent` **始终是同一串**
「场景描述已记录（本地草稿）」，变的只有 `opacity` 0↔1 与 class。

⟹ **反馈的「变化」落在 class 上，不落在内容上。**
`aria-live` 按内容变化播报，所以（**推断，未取证**）辅助技术大概率不会播报这次提交。

## 默认可达性：滚之前它被别的元素盖住

`elementFromPoint` 在 prompt 中心的结果：

| 状态 | 命中 | `scrollLeft` |
|---|---|---|
| 刚进导演台 | **`other`**（被 inspector 压住） | 0 |
| 真实滚轮滚到底部条最右 | **`self`** | 250（= `max`） |

⟹ 用它要「滚一下 + 点一下」两步，而底部条没有滚动条提示（715）。
**最核心的输入，恰好是默认最够不到的那一枚。**

## 判据

| 判据 | 断言 |
|---|---|
| `submitting-changes-nothing-in-the-store` | 六个时刻 store 逐字段恒定：`objects 5`、`past 0`、`future 0`、`lastCommandResult null`、`selection null` |
| `the-confirmation-is-a-2000ms-visual-swap-and-the-draft-survives` | status `0→1`、输入框 `opacity 0`、草稿不清空；2.2 秒后 status 回 `0`、输入框回 `opacity 1`、草稿仍在 |
| `all-four-enter-combinations-submit` | 四种组合各 `0→1`、输入框 `opacity 0`、草稿内容与组合名逐条对上 |
| `trim-governs-both-the-disabled-state-and-the-early-return` | 空值与**纯空格**都 `disabled = true` 且 Enter 后 status 仍 `0` |
| `the-attachment-name-hides-the-submit-confirmation` | 附件态文本以「已附上本地图片：」开头且含文件名；带附件提交时文本**逐字等于**附件那句、不含「场景描述已记录」；2 秒后文本仍在（只是不可见） |
| `the-live-region-text-never-changes-only-opacity-does` | 三个时刻的 status 文本集合恰为 `{场景描述已记录（本地草稿）}`；`aria-live = polite`；只有 opacity 变 |
| `reaching-the-prompt-takes-a-scroll-then-a-click` | 滚之前 `other` / `scrollLeft 0`；滚之后 `scrollLeft == max > 0` / `self`；点击后焦点到手；发送按钮滚之前也是 `other`；输入框盒 **143×16** |

两轮连跑 **7/7**，读数逐条一致。

## 方法论收获（可复用）

**① 直接给受控输入框改 `.value` 再派发 `input`，React 的 value tracker 会去重。**
第一版探针用这招清空输入框，读到「空值时 `disabled` 仍是 false」，
看起来像个真缺陷。**实际上 DOM 的值已经是 `''`，而组件 state 还停在「有内容」** ——
两者永久不一致。更阴的是：在**看起来**是空的框上再按真实按键**不会补上 `onChange`**，
脏状态就一直挂着，于是后续所有读数都被污染。
⟹ **清空受控输入框用真实键盘（`Meta+a` + `Backspace`），
并且对「清空是否生效」本身断言**（`value === ''` **且** `disabled === true`）；
⟹ 同一页面上不要先做会污染 state 的实验再测依赖 state 的行为 ——
**两件事必须分到两个干净页面上**（本批的附件实验就是这么分开的）。

**② 一次读数出现「不合理」时，先怀疑自己上一次动过什么。**
本批的空值格前后变了三次结论（`disabled false` → 断言失败 → 干净页面上 `true`），
每次都对应着自己刚做过的一个动作。**读数与操作的历史要一起记**，
不然会把探针的状态泄漏当成应用的行为。

**③ 滚动手势必须落在目标容器的真实矩形里。**
第一版把滚轮放在 y=1000，而底部条在 1280 下只占 y 920..968 ⟹ 滚了个空，
后面点的是还在框外的坐标，于是「焦点没到手」。
**断言先于操作是对的**（707 的纪律又一次生效），但**坐标要从元素读、不要写死**。

**④ 「两个无响应」先假设它们共享一个守卫。**
按钮 disabled 与 Enter 早退看起来是两件事，实测都是 `!value.trim()` 的两个入口，
连**纯空格**都同时命中两者。⟹ 判「无响应」的成因时，
**先找有没有一个守卫能同时解释多个格子** —— 找得到就别当成两个缺陷开单。

## 待拍板（不阻塞）

- **有附件时提交反馈被顶掉**（显示「已附上本地图片」而不是「已记录」）
  —— 要不要把两者合成一句，或让附件态与提交态分两行
- **提交期间输入框 `opacity: 0`，已输入的文本隐身 2 秒** —— 要不要保留草稿可见
- **`aria-live` 区域内容不变、只有 class 变** —— 要不要在提交时改文本
  （例如「已记录（本地草稿）· 14:32」）让播报真的发生（**播报行为本身未取证**）
- **四种 Enter 组合（含 `Meta+Enter`）都提交** —— 要不要只认裸 Enter
- **默认可达性**：1280 下它被 inspector 盖住、要「滚一下 + 点一下」——
  与 715/716 的底部条溢出是同一件事，修那条会顺带解决这条
- `DirectorViewport.tsx:2325` 那处 `onKeyDown` 的修饰键语义**未取证**，
  值得下一批单独测（与本组件对照）

## 源站未取证

本批全部读数只来自 clone，**没有新增源站读数**。
组件注释里已记明两条未取证项：源站「发送」的 **Enter 提交语义**、
以及上传后是否真的发起云端生成（点它可能触发付费生成，故不测）。
