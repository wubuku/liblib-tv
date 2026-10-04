# batch 772 — 浮层开着时，导演台的全局快捷键会不会穿透进来

> 画布 · 导演台 · disclosure 浮层（导出面板 / 运镜预设面板 / 路径菜单 / 本机预演面板 / 群众阵列面板 / 模型库面板）
> 复刻对象：`http://localhost:4317` 的 `canvas-2`，导演台，桌面 1440×1000，chromium（playwright sync_api）
> 本批**没有改动 `src/`**（`git diff --stat HEAD -- src/` 为 0 行）
> 判据 **13 条（13 PASS / 0 FAIL）**；原始读数 22 格 × 2 轮（两个探针合并）；验收器 `scripts/verify-liblib-batch772.py`

## 0. 这一批在做什么

767–771 连续五批都在 disclosure 浮层的**焦点围栏**上。D8（按 Esc 丢整个工作区）是「窗口级处理器抢在浮层前面动手」的一个**实例**。本批问它的**破坏性同族**：

> **浮层开着、焦点落在浮层里某个控件上时，导演台的全局快捷键会不会照样生效？**

**新缺陷 D14（中）**：4 个浮层里，在**按钮**上按 `Delete` / `Backspace` 会**真的删掉**工作区里选中的对象；`Meta+Z` **6/6 个浮层**都能从浮层里撤销掉已经发生的删除。

## 1. 机制（静态可查，本批逐字读过）

`DirectorDesk.tsx:473-571` 在 **window、冒泡**阶段注册了**一个** keydown 处理器。它管的不止 Escape：

| 键 | 行为 | 行号 |
| --- | --- | --- |
| `Escape` + `activeMobilePanel` | 关移动抽屉 | `:482-486` |
| — | **`if (isEditable) return;` ← 唯一的挡板** | `:487` |
| `Meta/Ctrl+C` | `copyDirectorSelection()` | `:490-494` |
| `Meta/Ctrl+V` | `pasteDirectorClipboard()` | `:495-505` |
| `Meta/Ctrl+Z` / `Shift+Z` | `undoDirector()` | `:506-511` |
| `Meta/Ctrl+Y` | `redoDirector()` | `:512-516` |
| **`Delete` / `Backspace`** | **`deleteDirectorEntity()`（真删东西）** | `:517-548` |
| `Escape` | 手势取消 → 关导出面板 → 退出跟随 → `closeWorkspace()` | `:549-568` |

`isEditable` 只认 `isContentEditable` 与 `INPUT/TEXTAREA/SELECT`（`:475-480`）⟹ **按钮一律不在保护范围内**。

**活路径只有一条**：主画布页自己那条 Delete 在 `src/app/page.tsx:1306-1310` 的第一句业务判断 `if (uiState.activeDirectorNodeId) return;` 处就退出了 ⟹ 导演台开着时它是**死的**，所以不存在「第二条路径」这种解释空间。

而 6 个浮层的可编辑控件数（769/770/771 三批独立读数一致）：

| 浮层 | 可编辑 / 不可编辑 |
| --- | --- |
| export | 1 / 4 |
| preset | **0 / 10** |
| pathmenu | **0 / 5** |
| phonevcam | **0 / 2** |
| crowd | 3 / 2 |
| modellib | 2 / 13 |

⟹ **preset / pathmenu / phonevcam 三个浮层里没有任何一个控件能让那道早退生效。**

## 2. 协议

**22 格 = 21 个实验格 + 1 个对照格**，每格都从**重新加载的页面**开始并清空 localStorage 的导演台项目键。

| 臂 | 落点 | 键 | 格数 |
| --- | --- | --- | --- |
| `del-noneditable` | 浮层内第一个**不可编辑**控件 | `Delete` | 6 |
| `bs-noneditable` | 同上 | `Backspace` | 6 |
| `del-editable` | 浮层内第一个**可编辑**控件 | `Delete` | 3（只有 3 个浮层有） |
| `undo-noneditable` | 浮层内第一个**不可编辑**控件 | `Meta+Z` | 6 |
| `cam-deletable-control` | **任何浮层之外**的对话框控件（`aria-label=关闭`） | `Delete` | 1 |

**每格都自证两件事**（否则读数是退化的）：

- 按键那一刻**真的有选中**（Delete/Undo 分支只在有选中时才动手）；
- undo 臂每次都先在**树上**删掉一个对象并**确认对象数真的掉了**（5→4），才去浮层里按 `Meta+Z`。

**边界**：只点对象树的行、6 个 disclosure 触发器、以及为开 preset/pathmenu 而选中相机；**不点提交/连接/添加，更不做付费或真实生图生视频**。Delete 是被测行为，破坏只存在于探针这一页内。

## 3. 结果：Delete / Backspace 穿透

| 浮层 | 落点 | `Delete` Δ对象 | `Backspace` Δ对象 | 按键前选中 | 按键后选中 | 判定 |
| --- | --- | --- | --- | --- | --- | --- |
| export | BUTTON（本地第 1 个） | **−1** | **−1** | 角色 `director-character-lead` | `[]` | **穿透** |
| phonevcam | BUTTON（本地第 0 个） | **−1** | **−1** | 同上 | `[]` | **穿透** |
| crowd | BUTTON（本地第 3 个） | **−1** | **−1** | 同上 | `[]` | **穿透** |
| modellib | BUTTON（本地第 1 个） | **−1** | **−1** | 同上 | `[]` | **穿透** |
| preset | BUTTON | 0 | 0 | 相机 | 相机 | **结构上不可判** |
| pathmenu | BUTTON | 0 | 0 | 相机 | 相机 | **结构上不可判** |

`Delete` 与 `Backspace` 两条臂的 Δ **逐格相同** ⟹ 同一个症状、同一条代码路径（`:517` 的 `||`），符合 R60 的判别式。

## 4. 对照组：`isEditable` 早退确实在挡，但只挡输入框

| 浮层 | 落点 | Δ对象 | 按键后选中 | 判定 |
| --- | --- | --- | --- | --- |
| export | `INPUT`（本地第 0 个，时长数值框） | 0 | 未变 | **挡住** |
| crowd | `INPUT`（本地第 0 个，行数） | 0 | 未变 | **挡住** |
| modellib | `INPUT`（本地第 0 个，`sr-only` 的 `type=file`） | 0 | 未变 | **挡住** |

3/3 挡住。**这道守卫是 769 量的同一行代码**（`DirectorDesk.tsx:487`）—— 本批把它从 Esc 语境搬到了 Delete 语境，结论是：**它只挡输入框，挡不住按钮。**

## 5. 对照格：为什么 preset / pathmenu 判不了

772a 第一次跑时，preset 与 pathmenu 四格「没删对象」。这**不能**写成「没穿透」——至少有三种解释：

1. 快捷键真的没进去；
2. 进去了但目标不可删；
3. 进去了但那一档 `deleteDirectorEntity` 是 no-op。

**772a 无法区分这三者。** 772b 加了一个只隔离一个变量的对照格：选中相机 → 把焦点放在**任何浮层之外**的对话框控件（`aria-label=关闭`）上 → 只按 `Delete`。

**结果：对象 +0、选中没变 ⟹ 相机根本删不掉。**

于是归因闭合了：这两个浮层的触发器**必须选中主机位**才能开（否则 `disabled`），而打开它们还会把选中**换成主机位**（772a 的读数里 `selectedIds` 从角色变成 `['director-camera-main']`）⟹ 按键时的目标**只能是相机**，而相机删不掉 ⟹ **手上根本没有可删的目标**。

> **本批不声称 preset / pathmenu 安全。** 只声称「在种子项目里这个缺陷测不出来」。要让它可判，需要项目里有**第二台相机**，或开这两个浮层时仍能保持一个**可删对象**的选中。

## 6. `Meta+Z`：6/6 全部穿透

| 浮层 | 设置（树上先删，自证） | 浮层内按 `Meta+Z` 后 Δ对象 | 判定 |
| --- | --- | --- | --- |
| export | 5 → 4 | **+1**（回到 5） | **穿透** |
| preset | 5 → 4 | **+1** | **穿透** |
| pathmenu | 5 → 4 | **+1** | **穿透** |
| phonevcam | 5 → 4 | **+1** | **穿透** |
| crowd | 5 → 4 | **+1** | **穿透** |
| modellib | 5 → 4 | **+1** | **穿透** |

每一格的设置都**自证过**（树上按 Delete 确实把对象数从 5 打到 4），所以「撤销没生效」不会被误读成「本来就没东西可撤」。

## 7. 与 D8 不是一回事

| 键 | 会不会关掉导演台 | 后果类型 |
| --- | --- | --- |
| `Escape`（D8） | **会** | 丢**整个工作区** |
| `Delete` / `Backspace` / `Meta+Z`（D14） | **一个都不会**（4 轮全空） | 改**内容**，工作区还在 |

两条路径的**后果类型不同，修法也不同**：D8 要改 Esc 阶梯（见 D8 的拍板项），D14 要改的是**按键的作用域**。合并成一句「快捷键会搞坏导演台」会让修法选错。

## 8. 新缺陷 D14（中）

| 项 | 内容 |
| --- | --- |
| 标题 | 浮层开着时 `Delete` / `Backspace` / `Meta+Z` 会穿透进导演台：焦点落在浮层里的**按钮**上时，Delete 真的删掉工作区里选中的对象 |
| 位置 | `src/components/director/DirectorDesk.tsx:473-571`（处理器）、`:487`（挡板）、`:517-548`（删除分支） |
| 机制 | 唯一的挡板是 `if (isEditable) return;`，而 `isEditable` 只认 `isContentEditable` 与 `INPUT/TEXTAREA/SELECT` ⟹ 按钮一律不在保护范围内。`workspaceBusy` 与拍摄预览两个守卫在正常编辑态都不成立 ⟹ 这条路径在**正常使用中就是活的** |
| 实测 | 4/6 浮层、8/8 可判格：Δ对象 **−1**、选中被清空；守卫对照 3/3 挡住；`Meta+Z` 6/6 穿透 |
| 后果 | 破坏性且**无确认框**（与主画布页 Batch 177「Delete 立即删除」对齐源站一致）。可被 `Meta+Z` 撤回 —— 而 `Meta+Z` 本身也从浮层里穿透，用户在浮层里按不到正确的撤销入口 |
| 修法 | ① 把 `Delete`/`Backspace`/`Cmd+C/V/Z/Y` 整段移进「焦点在某个浮层内就早退」的守卫（按**浮层**判而不是按标签判）；② 或给 6 个浮层统一接一层**捕获阶段**的 keydown 拦截 + `stopImmediatePropagation()`（同仓现成配方两处：`DirectorViewport.tsx:2734-2753`、`DirectorPhoneVcamPanel.tsx:286-296`）。**两条都要做** —— 只做 ① 的话将来新增的浮层仍会漏 |

## 9. 观察

**O772-1 · 同一个 `isEditable` 早退，在 Esc 上是救命的，在 Delete 上是漏的。** 769 实测：群众阵列在输入框上按 Esc 什么都没发生（早退生效 ⟹ 导演台没被关掉）。本批实测：同一个早退在 Delete 上放行了按钮。**同一行代码，在一个键上是修复、在另一个键上是漏洞。**

**O772-2 · 三个浮层一个可编辑控件都没有** ⟹ `isEditable` 在它们里**永远不可能成立** ⟹ 那道守卫对它们等于不存在。**只挑「有输入框的浮层」验收，会得到「守卫是好的」的错误安心。**

**O772-3 · 这三个键一个都没关掉导演台**（4 轮全空）⟹ D14 与 D8 是两类后果。

**O772-4 · 桌内那道守卫与主画布页那道不等价。** `DirectorDesk:475-480` 认**任何** INPUT（含 `type=file`），而 `libtvSelectionCommandContext.ts:90` 的 `isLibTVEditableCommandTarget` **排除** `input[type=file]`，且额外认 `[role=textbox]/[role=searchbox]/[role=combobox]/[data-libtv-editor-root]`。今天**没有可观测后果**（主画布页那条 Delete 在桌开时是死的），但本批的 `del-editable` 对照格正好落在模型库那个 `sr-only` 的 `type=file` 上 —— 桌内那道认它，所以挡住了。哪天主画布页那条复活，同一个控件就会从「被当编辑框」翻成「不是编辑框」。

## 10. 探针教训

**R94 ·「没变化」有两种读法，必须用对照格分开。** 「按 Delete 没删对象」可能是①快捷键没进去，也可能是②目标根本删不掉。**只写「未观察到穿透」就是把 ① 和 ② 混成一句。** 修法：加一个只隔离一个变量的对照格。「没有证据表明有洞」与「这里测不了」长得一模一样，而它们导向完全相反的下一步（收工 vs 换实验设计）。

**R95 · 探针的设置步骤会污染后面的设置。** 772a 先 `ensure_camera()` 再去点第一个对象 —— 那一击**把刚选中的相机顶掉了**，preset 的触发器重新变 `disabled`，3 格全 FAILED。**凡是「先布置 A、再布置 B」的设置，B 可能悄悄清掉 A。** 判别式：每一个设置动作之后都回读它自己的前提。

**R96 · 一批读数失效时，不要整套重跑。** 772a 的 preset 3 格失效，但另外 18 格**完全有效**。做法是补一个探针**只重取失效的那几格**，在汇编器里**合并**并如实记下「哪几格来自哪个探针、为什么被取代」——失效的原因本身往往比读数更有价值（R95 就是这么沉淀下来的）。

## 11. 判据

13 条，全部 PASS（`runtime-audit.json` 的 `judgments`）：

| 判据 | 内容 | 结论 |
| --- | --- | --- |
| J1 / J2 | 两探针各自两轮逐格一致；合并后 22 格无缺无失败，772a 的 3 个失败格逐个被 772b 取代且其余读数全部保留 | PASS |
| J3 | 每格按键那一刻**真的有选中** | PASS |
| J4 | `Delete` 穿透：4/4 个可判浮层真的删掉选中对象（Δ=−1、选中清空） | PASS |
| J5 | `Backspace` 与 `Delete` 逐格 Δ 相同 ⟹ 同一条代码路径 | PASS |
| J6 | 对照组：落可编辑控件时 3/3 被 `isEditable` 早退挡住 | PASS |
| J7 | preset / pathmenu 的 4 格判为**结构上不可判**，不是「没穿透」 | PASS |
| J8 | 对照格：相机**删不掉** ⟹ J7 的归因成立 | PASS |
| J9 | `Meta+Z` 穿透：6/6 个浮层都撤销掉已发生的删除（每格 setup 自证） | PASS |
| J10 | 这三个键一个都没关掉导演台 ⟹ 与 D8 是两类后果 | PASS |
| J11 | 机制：活路径只有一条（主画布页 Delete 已被 `activeDirectorNodeId` 早退掉） | PASS |
| J12 | 机制：唯一挡板是 `isEditable` 早退，且在 Delete 分支之前 | PASS |
| J13 | 观察：两道守卫不等价（本批无后果，属潜在风险） | PASS |

## 12. 不声称 / 下一批可以做什么

- **不声称 preset / pathmenu 安全**（第 5 节）：种子项目里**测不出来**，只声称「需要第二台相机或可删目标才可判」。
- **不声称 `Meta+C` / `Meta+V` / `Meta+Y` 的后果**：本批只量了它们的**同类**（`Delete`/`Backspace`/`Meta+Z`）能穿透，剪贴板副作用需要另一套读数（导演台剪贴板没挂在 window 上）。
- **不声称 D11 / D12 / D13**：768/769/770/771 的读数仍然有效。
- **修 D14 需要改 `src/`**（等授权）。
- **值得下一批做的**：用**第二台相机**或新建一个可删对象，把 preset / pathmenu 的 4 个不可判格补上；以及给 `Meta+C`/`Meta+V` 找一个可观测的读数。

## 13. 复现

```bash
export PATH="$HOME/.nvm/versions/node/v24.6.0/bin:$PATH"
cd /Users/yangjiefeng/Documents/wubuku/liblib-tv
$HOME/.pyenv/shims/python3 docs/research/liblib-canvas-batch772-2026-10-01/probes/dbg772a.py
$HOME/.pyenv/shims/python3 docs/research/liblib-canvas-batch772-2026-10-01/probes/dbg772b.py
$HOME/.pyenv/shims/python3 docs/research/liblib-canvas-batch772-2026-10-01/probes/mk772audit.py
$HOME/.pyenv/shims/python3 scripts/verify-liblib-batch772.py
```

- 原始读数：`raw/vb772a.json`（21 格 × 2 轮）、`raw/vb772b.json`（7 格 × 2 轮）
- 合并后 22 格的**来源是现算的**：772a 15 格、772b 7 格（preset 的 3 格 + pathmenu 的 3 格 + 对照格都来自 772b —— 772b 覆盖了 772a 的同名格）
- 探针脚本与汇编器都随产物提交（R43）
- 验收器**不采信汇编器的派生字段**：`selectionCleared` / `objectsDropped` 两个信号由验收器**自己从 raw 重算**；合并规则、覆盖完整性、可判/不可判的划分也独立复核一遍
