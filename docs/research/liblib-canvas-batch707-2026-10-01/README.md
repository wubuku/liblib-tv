# batch 707：输入框聚焦时导演台里哪些命令到不了 —— 4 焦点 × 6 快捷键全表

日期：2026-10-03　验收器：`scripts/verify-liblib-batch707.py`（7 条判据，30 格，每格一个全新页面，零 store 写入，不改 `src/`）

## 起点

706 查出一件事：焦点在任一输入框内时 `Cmd+Z` **到不了** `undoDirector` ——
`DirectorDesk.tsx:484` 的 `if (isEditable) return;` 排在修饰键分支**之前**；
而且在一种特定状态下**浏览器的表单撤销会顶替这次按键**。

706 只测了 `Cmd+Z` 一条、一个焦点位置。**一条读数不是一张表。**

## 五条预测（写死在验收器里，先于任何测量）

| 预测 | 内容 | 结果 |
|---|---|---|
| **P1** | 6 个全局快捷键在**任何**可编辑控件聚焦时都到不了 | **成立** |
| **P2** | 6 个在面板聚焦时**全部**到得了 | **成立** |
| **P3** | `Meta+Shift+z` 与 `Meta+y` 是同一动作的别名 | **成立** |
| **P4** | `Delete` 与 `Backspace` 共用一个分支 | **成立** |
| **P5** | 浏览器表单撤销的触发条件是「文档表单历史里有过键入」（706 的说法） | **推翻** |

## 全表：可达性只由「焦点在不在可编辑控件上」决定

| 焦点 ＼ 键 | `Meta+z` | `Meta+Shift+z` | `Meta+y` | `Delete` | `Backspace` | `Escape` |
|---|---|---|---|---|---|---|
| **文本框** `object-name` | 到不了 | 到不了 | 到不了 | 到不了 | 到不了 | 到不了 |
| **滑块** `camera-fov` | 到不了 | 到不了 | 到不了 | 到不了 | 到不了 | **到了（另一套处理器）** |
| **下拉** `camera-switch` | 到不了 | 到不了 | 到不了 | 到不了 | 到不了 | 到不了 |
| **面板**（无可编辑控件） | `UNDO` Δ(−1,+1) | `REDO` Δ(+1,−1) | `REDO` Δ(+1,−1) | `DELETE_OBJECTS` / `REJECTED` | 同左 | **关掉整个导演台** |

**18 格到不了、6 格到得了，一条例外都没有漏。** 每格都断言了「按下去之后账上最后一条命令没变」，
不是只看 store —— 到不了的键连一条命令都不记。

**`Delete` / `Backspace` 在面板列记的是 `REJECTED` / `DIRECTOR_LAST_CAMERA_REQUIRED`**：
备料用的是**受守卫保护的机位**，而 `REJECTED` 本身就证明按键到了导演台。
补充格另测「面板焦点 + 真正可删的对象」⟹ 对象数 **5 → 4**、账上 `DELETE_OBJECTS` / `COMMITTED`、
历史 +1 —— 所以那个 `REJECTED` 不是「这个键永远被拒」，是「机位不能删」。

## 唯一的例外不是漏网：`Escape` 到的是另一套处理器

| 焦点 | 账 | 手势 | 导演台 |
|---|---|---|---|
| 滑块 | **`GESTURE_CANCEL` / `NOOP`** | `camera-fov` → `null` | **还开着** |
| 面板 | `null`（它不记账） | — | **关掉** |

同一个键、同一个「到不了全局处理器」的形状（都被 `isEditable` 或控件自己接住），
**但滑块那一格到的是手势边界，不是导演台**。
⟹ 「到得了 / 到不了」这���分类装不下 `Escape`：它既不是到得了，也不是到不了，
**它到的是另一套处理器**。这是本批唯一一个「一个词装不下两种情况」的格子。

## P5 被推翻：hijack 的触发条件是两个变量的与

706 说「文档表单历史里有过键入」就会触发。五个状态实测：

| 臂 | 键入过 | 方向键 | 中途点画布 | 浏览器 hijack |
|---|---|---|---|---|
| `rename+arrow+no-canvas` | ✓ | ✓ | ✗ | **✓** 焦点跳到名字框、`nameDom` 退回原名、`nameStore` 未变 |
| `rename+no-arrow+no-canvas` | ✓ | ✗ | ✗ | **✓** 同样 |
| `rename+arrow+canvas-click` | ✓ | ✓ | ✓ | ✗ 什么也没发生 |
| `no-rename+arrow+no-canvas` | ✗ | ✓ | ✗ | ✗ |
| `rename+arrow+canvas+back` | ✓ | ✓ | ✓（点完又走回滑块） | ✗ |

**触发条件 = 键入过「且」中途没点过非可编辑表面。**
两件事 706 都没分开测过：
**方向键按不按都无所谓**（`no-arrow` 那臂照样 hijack ——
所以 706 读到的「手势被顺手提交成一条条目」是**按了方向键才有**的附带效果，不是 hijack 本身）；
**点一次画布就足以让它失效**（两次点画布的臂都不 hijack）。

⟹ **706 的读数全部存活，它对触发条件的描述要收窄成一个「与」。**
（浏览器内部为什么这样属**未取证**，本批只断言「哪个状态 hijack、哪个不」。）

## 判据

| 判据 | 断言 |
|---|---|
| `every-shortcut-is-blocked-while-any-editable-control-has-focus` | 3 个可编辑焦点 × 6 键（`range`+`Escape` 除外）：账上最后一条命令不变、历史 Δ=(0,0) |
| `all-six-shortcuts-reach-the-desk-when-the-focus-is-on-the-panel` | `UNDO` Δ(−1,+1)、两枚 redo 键都 `REDO` Δ(+1,−1)、`Delete`/`Backspace` 都 `DELETE_OBJECTS`/`REJECTED`/`DIRECTOR_LAST_CAMERA_REQUIRED`、`Escape` 关掉导演台 |
| `delete-and-backspace-share-one-command-branch` | 面板列账上三元组逐字相同、历史 Δ 相同；三个可编辑焦点列也相同 |
| `the-two-redo-keys-are-aliases` | 面板列两枚 redo 键账上与历史 Δ 完全一致 |
| `the-browser-form-undo-hijack-needs-a-prior-text-edit-and-no-canvas-click-in-between` | 五臂逐一断言；并断言 `expectHijack == (renamed and not canvasClickInBetween)` |
| `escape-reaches-the-gesture-boundary-not-the-desk-while-a-slider-has-focus` | 滑块列：手势 `camera-fov`→`null`、账 `GESTURE_CANCEL`/`NOOP`、台还开着；面板列：台关掉 |
| `delete-on-a-deletable-object-actually-deletes` | 补充格对象 5→4、`DELETE_OBJECTS`/`COMMITTED`、历史 +1 |

## 记成不适用（不记成失败，也不悄悄跳过）

- **`Cmd+C` / `Cmd+V`**：会写系统剪贴板，属外部可见状态变更，**未获授权**。
- **方向键**：源码里**没有任何方向键绑定**（`DirectorDesk.tsx` 的 keydown 只有
  `c` / `v` / `z` / `y` / `Delete` / `Backspace` / `Escape`）。
  那是「**无绑定**」，不是「**到不了**」—— 两回事，分开记。

## 本批自己踩的坑：普查器的备料错了三次，而且三次都伪装成读数

1. **`set_focus("panel")` 点 treeitem 并不把焦点拿过去** ——
   `role="treeitem"` 不可聚焦，点它不动焦点。头三行 undo/redo 的焦点其实还在可编辑控件上，
   那三格是「**我没造出差异**」。
2. **`Delete` 备料改用「可删对象」后，那个选中让 `shot-end` 字段消失** ⟹ range 那一列直接 Timeout。
   **读面不存在，不是控件惰性。** 最后一版改用受守卫保护的机位当备料（`REJECTED` 即证明到达）。
3. **`focus_panel` 的最后一步会重新选回机位** —— 我自己忘了两次，
   直到补充格删掉的是机位（理由 `DIRECTOR_LAST_CAMERA_REQUIRED`）才暴露。

**这三次的共同形状：仪器没到位，而产出物长得和「控件到不了」一模一样。**
本版每格都断言焦点真的到位（`focused` 元素 + `editable` 布尔），不到位就**报错**而不是产出一格读数；
备料的效果也断言（redo 那两格断言 `future ≥ 1`，补充格断言真的选中）。
**普查器的「设状态」和「造差异」一样需要断言，否则它会把第三态印成结论。**

## 待拍板（不阻塞）

- 18 格到不了的快捷键：要不要在输入框聚焦时对 `Meta+z` 单独接管走 `undoDirector`（706 已提）
- `Escape` 的双重语义（滑块上手势边界 / 面板上关导演台）要不要在 UI 上分开
- 「点一次画布就让浏览器的表单撤销失效」这一条若要修，只能靠**在输入框内接管 `Cmd+Z`** ——
  那是唯一能绕开浏览器原生撤销的办法
