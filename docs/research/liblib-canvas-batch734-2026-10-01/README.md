# batch 734 — 14 个写点全打开；推翻 732 的「6 个写点无 UI 入口」；46 写点全表收口

## 起点

733 把 46 个 `data-inert` 写点里的 28 个逐处打开，10 个记为「条件门控」，
8 个仍未打开。本批把那 8 个全打开 —— 顺带把 732 的一个结论推翻了。

## 决定性读数

### ① 入口要按稳定属性选（本批把它总结成三种）

| 面板 | 稳定选择器 | 出处 |
|---|---|---|
| 「添加节点」 | `[data-add-node-entry=type]` | `AddNodePanel.tsx:206`（733 用上） |
| 图片卡工具条 | `[data-testid=image-toolbar-panorama-slash]` | `ImageToolbar.tsx:30-31` |

按可见文本找，本轮已连续踩空三次，三种踩法各不相同：

1. **文案带 badge** —— 「智能剪辑**Beta**」「逐帧拉片**SD 2.5**」，`startsWith` 落空；
2. **同一组件里文案相近** —— `ScriptGeneratorNode` 的「剧本生成分镜脚本」
   与真正的入口「打开脚本节点 →」；
3. **图标 + 文字混排** —— `textContent.trim()` 不等于 `label`。

### ② 全景分支 4 处打开

`ImageNode.tsx:161` `runAction("全景")` 会 `addDerivedNode(..., { editorVariant: "panorama" })`，
而 `ImageEditPanel.tsx:50` `variant === "panorama"` 才渲染 `PanoramaEditPanel`。
选中那张派生卡后全景面板内 4 处全出现：**展开全景编辑器 / 全景参考图添加 /
全景模型选择 / 全景生成参数**。

### ③ **推翻 732**：不是「无 UI 入口」，是「种子那张视频卡恰好 `failed`」

| | 读数 | 出处 |
|---|---|---|
| 种子里视频卡的 `status` | **`"failed"`** | `canvasStore.ts:940` |
| **新建**视频卡的 `status` | **`"ready"`** | `canvasStore.ts:4207` |
| 实测：新建一张视频卡并单选 | 自身 6 枚：**播放视频**（`VideoNode:498`）+ 该功能 / 翻译视频提示词 / 该设置 + **撤销视频处理 / 重做视频处理**（`VideoProcessingToolbar:244-245`） | — |

732 那句「种子画布上**没有任何 UI 入口**」**读数对、理由错**：
UI 有路径，只是**起点是另一张卡**。种子 fixture 把视频卡钉在 `failed`，
于是同一套 UI 在默认画布上看不到那几处。

> 这属于项目里记过的第三档 —— **读数对、理由错** ⟹ 读数保留、理由作废，
> 纠正记在本批，不改历史批次。

### ④ 再点三下，又开 7 处

| 动作 | 触发器 | 新打开的写点 |
|---|---|---|
| 点「特效」pill | `VideoGenerationPanel.tsx:394` `setEffectsOpen(!effectsOpen)` | **特效收藏**（`:550`）**一个写点 → 4 枚实例** |
| 点元素选择模式 | `[data-mark-select-trigger]`（`:476`，横幅在 `:571` `markSelectMode &&`） | **返回节点**（`:597`）+ **关闭**（`:613`） |
| 点「片段重拍」 | `VideoProcessingToolbar.tsx:131` | `SegmentReshootPanel` **4 写点 → 6 枚实例**：参考 / 标记 / 角色库（`:138` 的 `.map` 撑成 3 枚）+ 积分选择（`:230`）+ 生成参数选择（`:236`）+ 翻译片段重拍提示词（`:257`） |

### ⑤ 全表收口

| 状态 | 写点数 | 来源 |
|---|---|---|
| **已逐处打开并实测** | **42** | 730 的 22 + 732 的 2 + 733 的 4 + **本批的 14** |
| 条件门控，**已带源码 + DOM 双证** | **4** | `StoryboardScriptEditor` 3（门控：`ScriptGeneratorNode.tsx:50` `inStoryboardSession`）+ `ShotBreakdownResultNode` 1（门控：动作按钮是「上传视频后开始」） |
| **合计** | **46** | 与静态普查完全对上 |

逐文件（静态 = 打开 + 门控）：

| 文件 | 静态 | 打开 | 门控 |
|---|---|---|---|
| `ImageEditPanel` | 11 | **11** | 0 |
| `VideoGenerationPanel` | 6 | **6** | 0 |
| `HistoryPanel` / `SegmentReshootPanel` | 4 / 4 | **4 / 4** | 0 / 0 |
| `AgentDrawer` | 3 | **3** | 0 |
| `StoryboardScriptEditor` | 3 | 0 | **3** |
| `LibraryShowcasePanel` / `ToolboxPanel` / `TopNavBar` / `VideoClipEditPanel` / `VideoProcessingToolbar` | 各 2 | **各 2** | 0 |
| `LeftSidebar` / `AudioNode` / `ScriptGeneratorNode` / `VideoNode` | 各 1 | **各 1** | 0 |
| `ShotBreakdownResultNode` | 1 | 0 | **1** |

本批新开的 14 处**全部** `role=button`（AX 通道）+ `focusable=true`（DOM 通道）——
与 730 / 731 / 732 / 733 的读数**五处同构**。

## 不声称

- **不声称那 4 个门控写点不可达** —— 只是本轮没走到那一步；条件满足后应当可达，未证。
- **不声称 42 个写点的运行时实例总数** —— 多实例写点会显著放大
  （`LibraryShowcasePanel:130` → 16 / 24 枚、`:550` → 4 枚、`:138` → 3 枚、
  `HistoryPanel:208-210` → 9 枚、`LeftSidebar:101` → 4 枚）。
- **不声称种子 fixture 的 `failed` 是缺陷** —— 本批只报告它改变了可见控件集合。
- **不声称 AX 树等同于真实屏幕阅读器播报** —— 沿用 731。

## 新增待拍板

1. **种子 fixture 把视频卡钉在 `"failed"` 是不是有意的** ——
   它让 `VideoNode:498`、`VideoProcessingToolbar` 2、`SegmentReshootPanel` 4
   共 **7 个写点**在**默认画布**上永远看不到，用户必须自己新建一张视频卡才能遇到。
   **需改 `src/`（或 fixture），等授权**；本批只报告，不裁决。
2. **`VideoGenerationPanel:550` 一个写点渲染 4 枚「收藏」** —— 与
   732 的 `LibraryShowcasePanel:130` → 40 枚同族；要不要收敛成一枚？

## 方法论

1. **入口按稳定属性选** —— `data-add-node-entry` / `data-testid` 是**合同**，
   文案是给人看的；本批把踩空的三种方式一起记下来，因为它们长得不一样。
2. **「读数对、理由错」单独记一档** —— 732 的读数（种子画布上看不到）是对的，
   理由（没有路径）是错的；**保留读数、作废理由**，纠正记在本批。
3. **fixture 的取值也是 UI 的一部分** —— 「种子里那张卡恰好 `failed`」
   会改变用户能看到的控件集合，**这不是测试的偶然，是产品状态**。
4. **能派发就别模拟真实点击** —— 见「探针返工」。

## 探针返工一处

节点选中从「在元素上直接派发 `mousedown`/`mouseup`/`click`」改成
「按 `boxModel` 中心发真实鼠标点击」后，**图片卡选不中**（中心被封面图挡住），
`[data-image-toolbar]` 不渲染 ⟹ 全景分支打不开，`own` 读数为 0。
改回 730 的做法即通过。⟹ **模拟真实点击会引入遮挡问题，能派发就别模拟**。

## 与前几批的关系

- **732**：其「6 个写点在种子画布上无 UI 入口」的**理由被本批推翻**；
  「写点数 ≠ 控件数」在本批又添两个例子（`:550` → 4 枚、`:138` → 3 枚）。
- **733**：其「条件门控」定性被本批沿用 —— 那 4 处仍带双证、不下结论。
- **730 / 731**：本批 14 处读数与它们在 `role=button` / `focusable` 上同构。
