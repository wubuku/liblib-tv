# Batch 765 — 导入/导出面板内的焦点围栏、disclosure 契约与 Esc 阶梯

## 选题

763 挂了三条没测的，移动端 focus scope 与导演台自己的快捷键已在 763 测完，
剩下第三条就是**导入/导出面板内部**。本批把它一次走完，并且不满足于「量到读数」
—— 每一处「看起来像缺陷」的读数都配了**对照实验**，把机制钉死。

静态侦察先说清楚被测对象（`src/components/director/DirectorExportPanel.tsx`
共 148 行）：

- 面板根 `data-director-export-panel`（`:43`）是个 `<section>`，带
  `data-director-export-status`；
- 5 个可聚焦控件：1 个时长 `input[type=number]`（`:60`）、3 枚画幅按钮
  `data-director-export-aspect`（`:81`）、1 枚提交按钮
  `data-director-export-submit`（`:132`）；
- 面板是 `absolute bottom-full right-0 z-50` 挂在时间轴右端的 popover，
  **不是 modal**；
- 面板内**没有** `useDirectorGestureBoundary`、**没有** `onKeyDown`、
  **没有** `stopPropagation`；
- 关闭路径只有一处：`DirectorDesk.tsx:557-560` 的
  `if (exportPanelOpen) { setExportPanelOpen(false); return; }`；
- 触发器 `data-director-export-trigger`（`DirectorDesk.tsx:1338`）只给了
  `aria-expanded`，面板挂在它**之后**（`:1351`）；
- 导入侧：`data-director-project-import` 按钮（`:1128`，`aria-label`=
  「导入导演台项目」）+ 隐藏 file input（`:1110`）。

## 判据（17 条：11 PASS / 6 FAIL）

FAIL 里 4 条是缺陷（D3/D4/D5/D6），1 条是不声称（J10），1 条是 D6 的另一半（J13）。
探针两轮**逐字段一致**，而且是**先证明可比再谈一致**（765a 比 10 个 key、
765b 比 9 个 key 的归一化 diff 全为空；本批无破坏性动作，两轮起点相同）。

| 判据 | 结论 | 读数 |
| --- | --- | --- |
| J1 | PASS | 两轮可比且逐字段一致（765a 10 key / 765b 9 key，diff 全空） |
| J2 | PASS | 面板内无手势边界 ⟹ D1 在这块不成立（静态 + 运行时都是 0） |
| J3 | PASS | 5 个控件里除时长框外每一个按 Esc 都关面板（8/8 格），0 格关导演台，10/10 格聚焦成功 |
| J4 | **FAIL** | **缺陷 D3**：时长数值框里 Esc 关不掉面板（1440：面板不关、导演台不关 2/2 轮；800px：只关更早的抽屉档、面板仍开 2/2 轮） |
| J5 | PASS | 注入对照定位机制：text/number/contenteditable 6/6 格关不掉、tabindex 2/2 格关得掉，且 **8/8 格 `reachedWinBubble=true`** ⟹ 不是原生吞、不是 D1 的 stopPropagation |
| J6 | PASS | 焦点围栏三向成立：正向从面板 12 步 0 逃出、正向从触发器 12 步 0 逃出、**反向 Shift+Tab 12 步 0 逃出**（765 只量过正向） |
| J7 | PASS | 打开不移动焦点，焦点留在触发器（`isTrigger=true`、`inPanel=false`），`aria-expanded` 由 `false`→`true` 同步 |
| J8 | **FAIL** | **缺陷 D4**：Esc 关掉面板后焦点掉到 `BODY`、逃出 dialog、**不在触发器上**（2/2 轮） |
| J9 | PASS | ★ **更正本批设计阶段的预期**：以为焦点掉到 body 后 Tab 会走原生序跑到画布页面形成死路 —— 实测 Tab 6 步 **6/6 全部落回 dialog 内部**，不是死路 |
| J10 | **FAIL** | ★ **那一轮 Tab 谁接管的判不了**：原生顺序焦点导航与围栏 hook 的数组**都是 DOM 序**，落点序列无法区分两者 |
| J11 | **FAIL** | **缺陷 D5**：点面板外空白（`(320,300)`，命中面板外非可点的 `absolute inset-0` 容器）后**面板仍然开着**，2/2 轮 |
| J12 | **FAIL** | **缺陷 D6**：disclosure 只做了 `aria-expanded` —— 触发器无 `aria-controls`、无 `aria-haspopup`；面板是**无 role、无 aria-label、无 id** 的 `<section>` |
| J13 | **FAIL** | ★ J12 的另一半：焦点在触发器且面板展开时 **Shift+Tab 12 步 0 次进过面板**（走的全是 DOM 序更早的「下一步」「跳过」「新增机位」） |
| J14 | PASS | 800px 三档 Esc 逐档推进、一次一档：抽屉 → 面板 → 导演台，2/2 轮全对，第四下保持关闭 |
| J15 | PASS | 导入侧是活的：2/2 轮真弹 file chooser，`accept=".json,application/json"`，按钮 `aria-label`+`title` 齐、未 disabled |
| J16 | PASS | ★ **坐实并更正 762**：隐藏 file input **零可访问名**（`aria-label`/`title`/`id`/`label[for]` 全空），但 `display:none` 不可聚焦 ⟹ **不构成可操作性缺陷** |
| J17 | PASS | 注入元素 0 污染：8 格全在面板内获得焦点；不关面板的 6 格按 Esc 后仍在 DOM 并被手动移除，关面板那 2 格随面板卸载消失 |

## 缺陷

### D3（低，新增）焦点在时长数值框里时 Esc 关不掉导出面板

`DirectorDesk.tsx:475-480` 把 `isEditable` 定义成「`isContentEditable` 或
`tagName` 是 `INPUT`/`TEXTAREA`/`SELECT`」，`:487` 的 `if (isEditable) return;`
排在整个 Escape 分支（`:549-568`）**之前**，于是焦点在
`<input type="number">` 里时，「关面板」那一档（`:557`）**永远走不到**。

- **不是** D1 那个 stopPropagation：注入对照实测 **8/8 格
  `reachedWinBubble=true`**，事件确实到了 window 冒泡（`escTargetAtWin`
  逐格记下了 `INPUT/text`、`INPUT/number`、`DIV/`），是被自己的守卫 return 掉的。
  这与 D1 的 `reachedWinBubble=false` 干净地分开。
- **不是**「`type=number` 原生吞 Esc」：同位置现插的 `type=text`、
  `contenteditable` 的 `div` 也都关不掉；`div[tabindex=0]` 照关不误。
- 实测：1440 下面板不关、导演台不关（2/2 轮）；800px 下这一下**只关掉更早
  那一档的抽屉**，面板仍然开着（2/2 轮）。
- 同一个守卫（`:487`）继 764 的 D2 之后**第三个受害档位**，修法可一起考虑。

### D4（低，新增）Esc 关掉导出面板后焦点掉到 body、逃出对话框

- `DirectorExportPanel.tsx:38` 的 `if (!open) return null;` 在关闭时把**正在
  聚焦的元素整个卸载**，浏览器把焦点退回 `body`；
- 而 `DirectorDesk.tsx:557-560` 的关闭分支只调了
  `setExportPanelOpen(false)`、**没有任何焦点处理**（静态层已断言该分支里
  不出现 `.focus(` 或 `restoreFocus`）；
- 围栏 hook `useDirectorFocusContainment.ts:149-172` 只在 root 上监听
  `keydown` 管 Tab，**没有 focusin/focusout 监听**，`restoreFocus()` 只在导演台
  **整体卸载**时才被调用（`:181-188` 的 `returnFocus`）⟹ 捞不回来。
- 实测 2/2 轮 `activeElement=BODY`、`inDialog=false`、不在触发器上。
- 对照 762：那条记的是「Esc 关抽屉/关导演台都会把焦点交还触发按钮」——
  **面板这一档漏了焦点归还**。
- **但不是死路**：之后按 Tab 6 步，6/6 全部落回 dialog 内部（J9 的更正）。
  焦点环消失、读屏上下文丢失是真的，「彻底回不去」不是。

### D5（低，新增）导出面板没有外点关闭，与 D3 叠加成退不回去的组合

`setExportPanelOpen` 全仓**恰好 3 处**调用：`:294` 初始化、`:558` Esc、
`:624` toggle —— **没有任何 pointerdown / 外点监听**。实测点面板外空白后
面板 2/2 轮仍然开着，导演台也没关。

与 D3 叠加的后果：**时长框里既按 Esc 关不掉、点外面也不关**。用户只能再次点
触发器，或把焦点挪到别的控件再按 Esc 才收得回去。

### D6（低，新增）disclosure 契约残缺，且反向 Tab 进不去

- 触发器只给了 `aria-expanded`（`:1341`），**没有 `aria-controls`、
  没有 `aria-haspopup`**；
- 面板根是个 `<section data-director-export-panel>`，**没有 role、没有
  aria-label、没有 id**（里面的 `<h2>导出设置</h2>` 不构成可访问名）；
- 面板又挂在触发器**之后**（`:1351`），围栏 hook 的 Tab 数组就是 DOM 序
  ⟹ 反向 Tab 走不到它：焦点在触发器、面板展开时 Shift+Tab 12 步
  **0 次进过面板**（`escapedDialog=0`，围栏本身没问题）。

## 观察

- **O1**：围栏 hook 的 Tab 接管是**手算 + `preventDefault`** —— 它在 keydown 时
  重新算一遍 `getDirectorFocusableElements(root)` 再手动 focus。所以 762/765
  量到的「Tab 序列」是这个数组的序（恰好也是 DOM 序），**不是**浏览器原生
  Tab 序；两者在本批**无法区分**（J10）。
- **O2**：围栏**只管 Tab、不管焦点丢失**。D4 的修法要在**关面板这一档**单独补
  焦点归还，不能指望围栏兜底。
- **O3**：点「导入导演台项目」**不会收起已开的导出面板**（`i_after` 里
  `panel.present` 仍为 true、触发器 `aria-expanded` 仍为 true）。但这一格
  **是探针自己先开着面板**才点导入的，所以只能当观察、**不能当判据**。
- **O4**：面板视觉位置在触发器**上方**（`bottom-full`）、DOM 顺序却在触发器
  **之后** ⟹ 视觉序与 Tab 序相反。与 D6 的「反向 Tab 进不去」同源。

## 探针教训（返工项）

- **R63｜按 Esc 之前先读状态**。765a 初版在 800px 那一格里无脑
  `press("Escape")` 想「关掉可能开着的抽屉」，那时并没有抽屉开着，Esc 顺着
  阶梯把**整个导演台关掉了**，后面三格读数全空。修法：先读状态，只在该关的
  时候关，按完还要**断言**目标真的变了自己要的样子，否则该格记 FAILED，不留
  空读数。这与 763 的 R59（开一个抽屉前先关另一个）同族：**任何「准备动作」
  都可能顺手触发别的状态迁移**。
- **R64｜先怀疑自己写的预期，再怀疑产品**。765b 设计阶段我断言「焦点掉到
  body 之后按 Tab 会走原生序、跑到画布页面，因为围栏 hook 的 keydown 挂在
  root 上、body 的事件冒泡不到 root」—— 听起来很硬。实测 6/6 步全落回
  dialog 内部，**预期被否掉**。教训：静态推理能证明「某条路径可达/不可达」，
  但**证明不了浏览器顺序焦点导航的起始点行为** —— 后者只能读，不能推。
- **R65｜注入对照必须在结论所在的位置重做，不能拿上一批的当证据**。763 的
  注入对照是在属性面板里做的；765b 在导出面板里**重新插了一遍**，四组对照
  （text / number / contenteditable / tabindex）× 2 轮 = 8 格，
  `reachedWinBubble` 全为 true —— 这同时把 D1（事件没上来）与 D3（事件上来
  被自己的守卫 return）**干净地分开**。
- **R66｜注入元素必须自证没污染后续读数**。每格都记
  `injectedStillInDom` 与 `removed.removed`；「关掉面板」那两格的元素随面板
  卸载而消失（`removed=0`）**不是读数缺失，而是另一种正确**。汇编器要把两种
  「不在 DOM」分开计数，污染计数必须为 0 才允许出结论。

## 不声称

- **无源站对照**：本批全部结论只针对 clone 自身的行为自洽性。
- **没有点提交按钮**（`data-director-export-submit`）—— Batch 596 的注释写明
  点它可能直接在用户项目上启动一次真实导出，属付费/破坏性动作，未授权。
  所以导出流程本身（`status` 从 `idle`→`exporting`→`done`/`error`、progress、
  error 文案）**全部未测**。
- **没有选文件**（只触发了 file chooser 就放弃），所以导入解析、校验失败、
  覆盖种子项目这些路径**未测**。
- **那 6 次 Tab 到底是原生顺序焦点导航还是围栏 hook 接管的，判不了**（J10）：
  两者的落点序列都是 DOM 序。「浏览器的顺序焦点起始点仍停在面板原处」只是
  **推断**，不是读数。
- 只测了 1440 桌面与 800px 移动端两档视口；640–850px 的隐藏区间（761 记的）
  没测。
- 800px 那一档只量了「属性抽屉 + 导出面板」这一个组合；「树抽屉 + 导出面板」
  没测。
- 面板在 `status=exporting`（提交之后）时的焦点与 Esc 行为**未测** ——
  前置条件就是不许点提交。
- 没测屏幕阅读器实际播报什么；D6/D4 的可访问性后果是从 DOM 契约与焦点读数
  推出来的。
- D3 只在导出面板的时长数值框上测过。属性面板那 43 个边界控件（764 的 D1）
  与本条的守卫是**两回事**，本批没有重新测它们。
- 面板的 `maxDurationSeconds` 取自 `timelineDuration`，本批读到 `max=8`；没有
  测过更长的时间轴下这个上限是否跟着变。

## 复现

```bash
export PATH="$HOME/.nvm/versions/node/v24.6.0/bin:$PATH"
cd /Users/yangjiefeng/Documents/wubuku/liblib-tv

# 1. 起 clone（4317）
npm run dev

# 2. 两个探针（各 2 轮，原始读数落在 raw/）
$HOME/.pyenv/shims/python3 /tmp/dbg765a.py   # → raw/vb765a.json
$HOME/.pyenv/shims/python3 /tmp/dbg765b.py   # → raw/vb765b.json
# 探针原件同批提交在 probes/ 下：dbg765a.py / dbg765b.py

# 3. 汇编（数字全部现算，findings 与 judgments[].evidence 写盘前逐条断言相等）
$HOME/.pyenv/shims/python3 \
  docs/research/liblib-canvas-batch765-2026-10-01/probes/mk765audit.py

# 4. 验收（静态层 + 产物层 + 原始读数交叉核对 + 阴性对照）
$HOME/.pyenv/shims/python3 scripts/verify-liblib-batch765.py
```

**授权边界**：源站可执行副作用 CRUD，但禁止付费与真实生图生视频；导出面板的
提交按钮**只读不点**。本批未碰源站，也未改 `src/`。
