# batch 762 — 导演台的焦点围栏：**完整成立，0 缺陷**

## 起点

748 挂了一条没做的：「导演台键盘/焦点围栏未测」。静态侦察发现导演台是一整块
`role="dialog" aria-modal="true"`（`DirectorDesk.tsx:901-902`），四周挂着：

| 行 | 东西 |
|---|---|
| `:896` | `data-director-focus-scope="workspace"` |
| `:897` | `data-director-focus-return={returnDisposition}` |
| `:898` | `data-director-focus-state={activeMobileFocusScope ? mobile-X : workspace}` |
| `:1179` | `aria-hidden={viewportPanelsCollapsed \|\| treeMobileInactive}` |
| `:1182` | `inert={treeMobileInactive \|\| viewportPanelsCollapsed}` |
| `:400-404` | 挂载时 `requestAnimationFrame` 把焦点打到 `workspaceRef` |

入口是现成的：种子画布里有 **1 个 `script-execution` 节点**，它的
`[data-open-director]` 按钮（`ScriptExecutionNode.tsx:58`）直接调
`openDirectorDesk(id, activeCanvasId)`。

`aria-modal="true"` 的承诺是「框外的世界对辅助技术不可达」。本批就去核这个承诺。

---

## 一、围栏成立：36 次按键、0 次逃逸

| 格 | 动作 | 结果 |
|---|---|---|
| D1 | 点「打开导演台」 | dialog 出现：`aria-modal=true`、`z-index:100`、`position:fixed`、视口中心最上层 |
| D2 | **打开瞬间**读焦点 | 落在 `role=dialog` 自身（`aria-label="3D导演台工作区"`），`inDialog=true`，**没留在 body** |
| D3 | Tab × 24 | **0 次逃出 dialog、0 次落到 body** |
| D4 | Shift+Tab × 12 | **0 次逃出** |
| B2 | 折叠后 Tab × 14 | **0 次逃出** |

三枚焦点读数齐备：`focus-scope=workspace`、`focus-state=workspace`、
**`focus-return=trigger`**。

## 二、Esc 与焦点返回

| 格 | 条件 | 结果 |
|---|---|---|
| D6 | 焦点在 dialog 根上按 Esc | **整个导演台关闭**（不是只关移动端面板） |
| D6 | 关闭后读焦点 | 落在 `[data-open-director]` 按钮上（「打开导演台 →」）—— 与 `focus-return=trigger` 吻合 |
| B4 | 先 Tab 五次、焦点落在子面板按钮「导出导演台项目」上，再按 Esc | **照样关闭**，焦点同样回到触发按钮 |
| B3 | **折叠态**下按 Esc | 照样关闭，焦点同样回到触发按钮 |

## 三、那 2 个「不可达」的元素是谁

128 个可聚焦元素，126 个可达。逐个点名，两个都是隐藏的 file input：

| 元素 | `aria-label` | `display` | class |
|---|---|---|---|
| `<INPUT type="file">` | 「导入本地角色模型」 | `none` | `hidden` |
| `<INPUT type="file">` | 无 | `none` | `hidden` |

对应 `DirectorIconRail.tsx:664` 与 `DirectorDesk.tsx:1111`（后者带
`data-director-project-import-input`）。

**这不是缺陷**：隐藏 file input 靠可见元素代理点击是标准做法，而且它们
`display:none` 本来就不可聚焦，屏幕阅读器也到不了。

## 四、折叠后的面板与围栏

点 `[data-director-panels-toggle]`（`aria-label="收起"`）之后：

| 面板 | `inert` | `aria-hidden` | `display` | 宽度 |
|---|---|---|---|---|
| 场景对象（树） | **true** | **"true"** | **none** | **0** |
| 属性 | false | 无 | block | 281 |

⟹ 三个属性**同步**，不是只设了其中一个。可达焦点 126 → 125（正好少树里那一个），
围栏仍在（Tab 14 步 0 次逃出）。

## 五、三处「看着像问题、查清都不是」

1. **折叠后收起按钮消失** —— 源码 `:963` 是
   `{!viewportPanelsCollapsed ? <button …/> : null}`，所以收起后按钮确实没了。
   但 `DirectorIconRail.tsx:355-359` 有明确注释（Batch 587，源站 2026-10-01 实测）：
   > 收起之后顶栏与「收起」按钮一并消失，浮层内没有第二个恢复按钮——**点图标栏的
   > 「场景」条目即恢复**顶栏与左侧场景面板。图标栏本身在收起态保留。

   `:359` 确实调了 `setViewportPanelsCollapsed(false)`。**这是对着源站量过的刻意设计。**

2. **`viewportPanelsCollapsed` 是复数命名，却只收左半边**（树收、属性不收）——
   这是命名与措辞的问题，不是行为错误。真要收两边，改的是 `aria-label="收起"`
   这句承诺，不是行为。

3. **焦点返回机制** —— 存在且工作正常（见第二节）。

## 六、判据（12 条）

1. 导演台是 `role=dialog` + `aria-modal=true` 的模态框，`z-index:100`、`fixed`、视口中心最上层。
2. 三枚焦点读数齐备：`focus-scope=workspace` / `focus-state=workspace` / `focus-return=trigger`。
3. 打开瞬间焦点真的进了 dialog（落在 `role=dialog` 自身、`aria-label="3D导演台工作区"`）。
4. **★ 围栏成立：Tab 24 + Shift+Tab 12 共 36 次按键，0 次逃出、0 次落到 body。**
5. Esc 能关闭整个导演台。
6. 关闭后焦点回到触发按钮 `[data-open-director]`，与 `focus-return=trigger` 吻合。
7. 焦点在子面板按钮上时 Esc 同样能关闭（不依赖焦点落在 dialog 根上）。
8. 折叠态下 Esc 依然能关闭，焦点同样回到触发按钮。
9. 128 个可聚焦元素里 2 个不可达，逐个点名：两个都是 `<input class="hidden">`。
10. **★ 这 2 个不是缺陷**：隐藏 file input 的标准做法，且 `display:none` 不可聚焦。
11. 折叠后场景树 `inert` / `aria-hidden` / `display` 三者同步；围栏仍成立（Tab 14 步 0 逃出）。
12. **折叠后恢复入口存在**（点图标栏「场景」），是 Batch 587 与源站核对过的刻意设计，**不是缺陷**。

## 七、返工五处（四处探针与结论纪律 + 一处验收器，零产品问题）

- **R48**：探针 b 把命中断言**写死**成查 `[data-director-panels-toggle]`，拿去点
  「打开导演台」当然永远 `ok=false` → FATAL 停下。**当场停是对的，是探针错了。**
  「命中断言」这个工具自己必须参数化。
- **R49**：探针 a 用 `/收起|折叠|展开/` 去 button 的 `textContent` 里找开关，拿到
  `null` —— 那枚按钮是**纯图标**（`PanelLeftOpen` + svg `aria-hidden`），根本没有文本。
  **图标按钮只能按钩子找，不能按文案找**；「找不到元素」和「元素没有那个字」是两回事。
- **R50**：关闭后再去读 `[data-open-director]` 上的 `data-director-focus-return`，
  拿到 `null` —— 那个属性长在 dialog 上，dialog 已卸载。焦点返回的**行为**证据在
  B3/B4，不依赖这次读取。
- **R51**：「2 个元素不可达」「折叠后按钮消失」「复数命名只收一半」三处我**先当成了
  缺陷候选**。查清机制后全部结案。**「看着不对」只是待查项，不是结论。**
- **R52（★ 验收器，同一个洞第四次复发）**：首版 34/36 时有两条检查是我自己写错的
  （用子串 `"b 是单轮"` 判断有没有把单轮算进去，结果被 `762b 是单轮` 命中；
  headline 写的是「标准的隐藏 file input」而我去找「标准做法」）。把那两条修对之后，
  **19/21 阴性对照里有 2 发漏放**：改 `findings.dialog.ariaModal` 与
  `findings.openFocus.inDialog` 一路通过 —— 因为 `findings` 与 `judgments[].evidence`
  在 JSON 往返之后是**两份独立副本**，我只守了判据那一份。

  759 的 R33、760 的 R38、761 的 R46、**这里是第四次**。同一个洞复发四次，
  说明「事后补检查」不是办法 —— 所以这次把它写成一条**默认结构检查**：
  凡是 `findings` 里出现过的键，都必须有一条 `findings.X == J[n].evidence` 的同源断言。
  补完 **38/38 通过、阴性对照 26/26 全拦**，并新增 5 发「只改 `findings` 那一份」
  的注入，把这五条同源断言逐条打一遍。

## 八、待拍板（需改 `src/`，等授权）

1. **`viewportPanelsCollapsed` 的命名 vs 行为**：只收树不收属性，属性名却是复数。
   改名字、还是让「收起」真的收两侧？（属措辞一致性，不影响当前行为正确性）
2. `DirectorDesk.tsx:1111` 那个隐藏的「导入项目」file input **没有 `aria-label`**，
   另一个有。它不可聚焦所以当下无碍，但要不要补齐保持一致。
3. 导演台的移动端 focus scope（`mobile-tree` / `mobile-inspector`）完全没测 ——
   是否要单独排一批。

## 九、不声称

- **没有与源站对照**：全部读数来自 clone（4317）。恢复入口那条只核了代码注释与调用点，
  **没有重新回源站复核**。
- **762b 是单轮补格**（点名那 2 个不可达元素、折叠后 inert 围栏），
  只有用它的判据（9/10/11）没有两轮判定。
- 只测了 **1440×1000 桌面视口**；导演台的**移动端 focus scope 完全没测**。
- 只测了 **Tab / Shift+Tab / Esc** 三个键；导演台自己的快捷键
  （`:482` / `:549` 两个处理器覆盖了哪些键）没测。
- **没有测屏幕阅读器实际播报什么**，只量了 DOM 属性与焦点落点。
- 焦点围栏只压了 **36 次按键**；128 个可聚焦元素没逐个走到，
  **后半程是否仍不逃逸未测**。
- 只开了导演台一个项目；多项目切换、导入/导出面板内的焦点行为没测。
- 没碰任何付费/真实生成任务（只做只读导航与 Tab）。

## 产物

- `docs/research/liblib-canvas-batch762-2026-10-01/raw/vb762a.json`（两轮）
- `docs/research/liblib-canvas-batch762-2026-10-01/raw/vb762b.json`（单轮）
- `docs/research/liblib-canvas-batch762-2026-10-01/probes/dbg762a.py`
- `docs/research/liblib-canvas-batch762-2026-10-01/probes/dbg762b.py`
- `docs/research/liblib-canvas-batch762-2026-10-01/probes/mk762audit.py`
- `docs/research/liblib-canvas-batch762-2026-10-01/runtime-audit.json`
- `docs/research/liblib-canvas-batch762-2026-10-01/README.md`（本文）
- `scripts/verify-liblib-batch762.py`（**38/38 通过，阴性对照 26/26 全拦**）
