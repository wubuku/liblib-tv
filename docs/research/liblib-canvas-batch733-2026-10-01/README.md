# batch 733 — 再开 3 族；另 2 族的「没打开」已从源码取证（条件门控，不是探针坏了）

## 起点

730/731 都在画布 7 个视图里测。732 去开面板，打开了 `LibraryShowcasePanel`
（**2 写点 → 42 枚**），但另外 5 族**一个都没打开** —— 入口脚本按可见文本匹配按钮失配，
节点根本没被造出来（`nodeId: null`）。732 如实记了「**未取证，理由是探针坏了**」。

## 本批的修法

`AddNodePanel.tsx:206` 给每一项面板入口都打了 `data-add-node-entry={entry.type}`。
按这个属性选就够了 —— **不必匹配可见文本**：可见文本还带 badge
（「智能剪辑**Beta**」「逐帧拉片**SD 2.5**」），`startsWith` 必然踩空。

## 决定性读数

### ① 三族打开，4 个写点逐处实测

| 族 | 入口 | 打开的 `data-inert` 写点 |
|---|---|---|
| `AudioNode` | `[data-add-node-entry="audio"]` → 单选该卡 | **1**：播放音频 |
| `VideoClipEditPanel` | `[data-add-node-entry="video-clip"]` → 单选该卡 | **2**：剪辑模式设置 / 输出设置 |
| `ScriptGeneratorNode` | 脚本子菜单 `[data-add-node-entry="script-new"]` → 单选该卡 | **1**：参考图上传 |

四枚**全部** `role=button`（AX 树）+ `focusable=true`（DOM 通道）——
与 730（DOM）对其他族的读数、731（AX）对那 43 枚的读数**三处同构**。

### ② 另 2 族「没打开」的理由是**源码里的条件门控**

| 族 | 门控 | 证据 |
|---|---|---|
| `StoryboardScriptEditor` | `ScriptGeneratorNode.tsx:50` `inStoryboardSession = storyboardSessionNodeId === id` ⟹ 入口按钮 `[data-script-generator-open-storyboard]`（`:113-120`，文案「打开脚本节点 →」）**只在进入「自写会话」之后才渲染** | 实测 **`openStoryboardBtn: false`** —— 该按钮**在 DOM 里根本不存在**；而同一张卡上 `ScriptGeneratorNode` 自己那枚 `data-inert`（参考图上传）**已经渲染** ⟹ 节点在、面板入口不在 |
| `ShotBreakdownResultNode` | 逐帧拉片卡的动作按钮是「**上传视频后开始**」 | 节点确实造出来了（`types` 里有 `shot-breakdown`），但动作按钮文案就是「上传视频后开始」⟹ 需要先上传视频 |

⟹ 这两条与 732 记录的「种子里视频卡 `status: failed` 挡住 6 个写点」**同族** ——
**条件门控**。但证据更硬：**源码 + DOM 双证**，不是「探针没找到」。

### ③ 顺带记一条负读数：同一组件里文案相近的按钮会骗过文本匹配

探针按 `/分镜|拆解|生成/` 找 `ScriptGeneratorNode` 的入口，先撞到的是
**「剧本生成分镜脚本」** —— 而真正的入口叫 **「打开脚本节点 →」**（`:113-120`）。
**两枚按钮文案相近，落在同一个组件里，按文本找会点错。**

## 覆盖面进展

| 状态 | 写点数 |
|---|---|
| 730 已测（画布 7 视图） | 43 枚实例 / 22 个写点 |
| 732 已测（素材库两面板） | 42 枚实例 / 2 个写点 |
| **733 新测** | **4 枚实例 / 4 个写点**（`AudioNode` 1、`VideoClipEditPanel` 2、`ScriptGeneratorNode` 1） |
| 733 记为条件门控 | 4 个写点（`ShotBreakdownResultNode` 1、`StoryboardScriptEditor` 3） |
| 732 记为条件门控 | 6 个写点（`VideoProcessingToolbar` 2、`SegmentReshootPanel` 4） |

⟹ **46 个写点里已逐处打开 28 个；另有 10 个的「打不开」已带证据**（条件门控）；
**还剩 8 个未打开**（`ImageEditPanel` 未渲染到的分支、`SegmentReshootPanel` 其余、
`VideoGenerationPanel` 其余等，取决于条件）。

## 不声称

- **不声称这 2 族不可达** —— 只是**本批没走到那一步**；条件满足后应当可达，未证。
- **不声称 46 个写点已全部实测** —— 详见上表。
- **不声称 AX 树等同于真实屏幕阅读器播报** —— 沿用 731。

## 新增待拍板

1. **「条件门控」这一族要不要给出可达路径的说明** ——
   「按了没反应」与「入口根本没出现」在 UI 上无法区分。**需改 `src/`，等授权**
   （本批只记，不裁决）。

## 方法论

1. **入口按稳定属性选，不按文案选** —— 面板项都带 `data-add-node-entry`；
   **属性是合同的载体，文案是给人看的**，而文案会带 badge、会改、会与兄弟按钮相近。
2. **「没打开」要分两种** —— 探针坏了（本批之前）与**源码里的条件门控**（本批）。
   前者记未取证并去修探针；后者要拿出**源码 + DOM 双证**才算结论。
   **「探针坏了」不能一直当挡箭牌。**
3. **同一组件里文案相近的按钮会骗过文本匹配** —— 记下来，下次直接按属性走。

## 探针返工一处

JS 里 `const b` 重复声明（先取候选列表再取目标元素）⟹ `SyntaxError`；
沿用 732 的教训：**每族采完即落盘**，别攒到最后。

## 与前几批的关系

- **732**：补上 732 的「入口失配」——找到 `data-add-node-entry` 这条稳定选择器，
  开了 3 族、给另外 2 族定了性。
- **730 / 731**：本批 4 枚的读数与它们在 `role=button` / `focusable` 上**三处同构**。
