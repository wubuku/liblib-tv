# Batch 358 — 「启用却点了没反应」普查：liblib 画布线

日期：2026-10-01
工具：`scripts/probe-liblib-batch358-fake-clickable.py`（运行时）
门禁：`scripts/verify-liblib-batch358.py`（47 项，覆盖 16 个 UI 态）

## 背景

frameos 那边已经有三类交互谎言的门禁（350/355 静默丢弃输入、344/356 假可点按钮、
357 谎称成功）。**liblib 这条线一个都没有**——302 个 `verify-liblib-batch*.py`
里，没有一条检查「可点外观却没有 handler」。

## 结果：16 个 UI 态，95 个死控件

普查在 16 个态里找到 **95 个**「启用、无 handler」的控件：

| 组 | 位置 | 数量 | 核实 |
|---|---|---|---|
| 教程菜单 | `LeftSidebar` `TutorialMenu` | 4 | 无 onClick，带 `hover:bg-white/[0.07]` |
| 生成历史卡片 | `HistoryPanel` | 9 | 查看/使用/下载 × 3 卡，均无 onClick，带 `hover:bg-white/30` |
| 时间倒序 | `HistoryPanel` | 1 | 无 onClick，带 `hover:bg-white/[0.05] hover:text-white` |
| 卡片收藏 | `LibraryShowcasePanel` | ~46 | 无 onClick，`group-hover:opacity-100` 悬停显形 |
| 筛选 | `LibraryShowcasePanel` | 2 | 无 onClick |
| 模板说明 / 模板选择 | `ToolboxPanel` | 2 | 无 onClick，带 hover 变色 |
| Agent header | `AgentDrawer` | 3 | 历史对话 / Agent 设置 / CLI & Skill，无 onClick |
| 开通会员 | `TopNavBar` | 1 | 付费入口 |
| 积分余额 | `TopNavBar` | 1 | 读数，不是控件 |

逐组都读过源码确认，**不是静态扫描的推断**。几处值得单说：

- `HistoryPanel` 卡片上同一行的「收藏」**有** `toggleFavorite`，所以没被算进去——这正说明同组控件的判定不能靠位置猜。
- `AgentDrawer` 里紧挨着「新对话无法分享」是**正确的写法**：`disabled` + `title` + `opacity-40`。同一个抽屉里，正确示范和四个谎言并排。
- 「开通会员」是付费入口，**按纪律绝不接线**。

## 修法：保持启用 + 去掉悬停骗人的反馈 + title 说明

**没有用 `disabled`**，因为那会动到已采样的源站形态：

- `verify-liblib-batch97.py` 依据 2026-09-05 源站审计断言 Agent header 三项 `is_disabled() == False`；
- `verify-liblib-batch106/121.py` 断言教程四项**可见**。

所以沿用「新对话无法分享」已有的视觉语言（降饱和 + title），只是不落 `disabled`：
保留几何与文案，去掉 hover，`cursor: default`，加 `title` 说明为什么不会有反应，
并加 `aria-disabled="true"` 让语义对辅助技术也诚实。

> 这正是 Batch 357 里 batch170 vs batch251 的那条分野：**断的是不是源站事实**。
> batch170 断的是 `BEHAVIORS.md:33` 采样到的启用态，所以该改我的代码；
> 这里断的同样是已采样的启用态，所以也不能靠 `disabled` 来「修」。

## 门禁的规则：例外必须自证

例外（付费入口、只读读数、以及全部修好的惰性控件）不按**名字**开白名单，而是
要求它们**同时**带 `aria-disabled="true"` 与非空 `title`。

白名单只会在下一次重构里悄悄失效：新增一个死按钮不会被列进去，门禁仍然绿，
而用户多点了一次。属性判据不会——任何新的死按钮都必须自己写清「我不可用」
和一句给用户看的理由，否则立刻红。

## 扫描器自己假绿了五次

这个工具在能给出可信数字之前，**先假绿了五次**，而且五次全是「扫不全」伪装成
「没问题」：

1. **只用 `cursor: pointer` 判可点** → liblib 不用内联 cursor（36 个按钮里 35 个是
   `default`），扫出「0 个假可点」。**那个结论是无效的**，差点当成体检报告交出去。
2. **只扫 `button`** → workspace 与 canvas 两态元素数完全相同（36/36），
   可画布态明明多了 10 个节点。工具条大量用 div + onClick。
3. **把继承了父元素 cursor 的子节点算成独立控件** → 一度冒出 35 个「pointer 且无
   handler」，实际是 34 个 `<path>` + 1 个 `<svg>`。`cursor` 是**可继承**属性。
4. **特征集只取 data/aria/role** → 把「面板开了但控件是纯文本 div」的 4 个态误判成
   「没打开」。判据太弱时，「没变化」会被误读成「没打开」。
5. **只收 pointer 或已接线** → 正好滤掉了要找的缺陷。`TutorialMenu` 那四个按钮既没有
   onClick 也没有 cursor，而「启用却无 handler 的按钮」按定义就是这类缺陷本身。

第 5 条最值得记：它不是漏掉了某一个缺陷，而是**系统性地对最纯的那一类缺陷失明**。

外加两条**构造性假阳性**的正确处理（不是开白名单）：

- `onChange` / `onInput` 同样算已接线 —— `<input type=range>` 天生没有 onClick
  （HistoryPanel「历史缩略图大小」）；
- `<label>` 的接线看**后代控件** —— 点 label 等于点它包的 checkbox
  （LibraryShowcasePanel「仅看可商用」）。

## 防假绿与防过滤过头

**防假绿**：每个态都必须与默认态**元素集合不同**，否则「零违规」只是把默认态数了
16 遍。`user_menu` 是已知死状态（见下），显式豁免并在代码里写明原因。

**防过滤过头**：扫描器先后加了五层过滤，「全清」很可能来自滤得太狠。所以有
一条**反向变异**：从一个**本来是活的**控件（工具箱「关闭工具箱」的 `onClose`）上
摘掉 handler。若扫描器把活控件也当死控件，这个变异会看不见；实测它被抓了出来，
说明判据没有过宽。

### 变异测试（4 项全红）

| 变异 | 结果 |
|---|---|
| 撤销修复：教程项去掉 `aria-disabled` | 红（`no-dead-control:tutorial`） |
| 半修：历史「查看」保留 `aria-disabled` 但抹掉 `title` | 红（`no-dead-control:history`） |
| 半修：Agent 设置只降饱和不声明不可用 | 红（`no-dead-control:agent`） |
| **反向**：摘掉「关闭工具箱」的 `onClick` | 红（`no-dead-control:toolbox`） |

## 顺带查到、但本批不动的两处死状态

- `uiStore` 的 `isToolboxPanelOpen` / `isMaterialPanelOpen` / `isCharacterPanelOpen` /
  `isHistoryPanelOpen` / `isTutorialPanelOpen` **零读取**——面板早已改由
  `activePrimaryPanel` 单一槽位驱动，这五个布尔是遗留物。
- `toggleUserMenu` **全项目无人调用**；`isUserMenuOpen` 只被
  `libtvSelectionCommandContext` 读来抑制快捷键。用户菜单没有触发器也没有渲染器。

两处都是用户不可见的死状态，不在本批「交互谎言」范围内，只记录。

## 覆盖缺口（如实记录）

liblib 这条线**没有 runner**，302 个验证器串行约需 4 小时，本批未全量跑。
跑的是与本次改动的 6 个组件相关的 **16 个**定向验证器
（62/97/101/106/112/121/139/169/197/198/199/281/343/478/514/529），
全部通过。
