# Component Contract Coverage Matrix

> 审计日期：2026-08-26
> 适用范围：LibTV clone 的 `src/components/`，不含 FrameOS 独立组件目录。
> 用途：从源码组件反查组件合同、源站证据、验证入口和下一步文档工作。

## 1. 读法与边界

本表是组件研究索引，不替代具体合同。修改组件时，先按本表找到合同入口，再阅读该合同引用的 source evidence、截图分析和 verifier。

| 状态 | 含义 |
|---|---|
| `SPEC_COMPLETE` | 有稳定的独立组件合同，组件级入口足以指导一次窄修改。 |
| `DOMAIN_CONTRACT` | 行为由 Director、视频处理或其他领域合同覆盖，暂不重复创建同内容的组件 spec。 |
| `COVERED_BY_PARENT` | 组件是父节点、跨切面或共享浮层的一部分，主要语义由父合同覆盖。 |
| `BATCH_CONTRACT` | 只有批次级合同；修改前必须同时读该批次的 `PLAN.md`、`IMPLEMENTATION.md` 和证据记录。 |
| `NEEDS_SPEC` | 当前有实现或证据，但没有足够稳定的单一合同；只记录缺口，不把它当作已完成。 |
| `LEGACY` | 遗留或当前未使用的组件，不应作为新功能入口。 |
| `DEBUG_ONLY` | 仅用于 clone 调试，不是源站功能合同。 |
| `PARALLEL_WIP` | 相关批次或实现可能由其他开发者并行推进；本表只引用，不覆盖其 WIP。 |
| `OUT_OF_SCOPE` | 属于另一条 route/store 或当前原型明确不覆盖的能力。 |

“有合同”不等于“已经达到源站像素级一致”。合同仍需区分源站事实、证据支持的推断和 clone-only 决策，并以 [`TRACEABILITY_MATRIX.md`](../TRACEABILITY_MATRIX.md) 与 [`VERIFICATION_LEDGER.md`](../VERIFICATION_LEDGER.md) 为验证状态入口。

## 2. LibTV shell 与节点

| 组件 | 源码入口 | 合同/证据入口 | 验证入口 | 状态 | 文档动作 |
|---|---|---|---|---|---|
| `TopNavBar` | `src/components/TopNavBar.tsx` | [`TopNavBar.spec.md`](TopNavBar.spec.md)、`BEHAVIORS.md` 顶部导航 | Batch 11 overlay lifecycle | `SPEC_COMPLETE` | 修改导航、Agent 或共享入口前先读互斥浮层合同。 |
| `LeftSidebar` | `src/components/LeftSidebar.tsx` | [`LeftSidebar.spec.md`](LeftSidebar.spec.md)、`BottomToolbar.spec.md` | Batch 1 panels / Batch 11 lifecycle | `SPEC_COMPLETE` | 当前名称兼容旧实现；不要把它误判成源站左侧竖栏。 |
| `BottomToolbar` | `src/components/BottomToolbar.tsx` | [`BottomToolbar.spec.md`](BottomToolbar.spec.md)、`PAGE_TOPOLOGY.md` | Batch 18 zoom/minimap | `SPEC_COMPLETE` | 修改入口面板、缩放、minimap 时同步检查 overlay lifecycle。 |
| `ScriptHeader` | `src/components/ScriptHeader.tsx` | [`ScriptHeader.spec.md`](ScriptHeader.spec.md)、`PAGE_TOPOLOGY.md` | no current verifier | `LEGACY` | 当前未挂载；不把固定标题或装饰圆点重新引入运行态。 |
| `StoryboardBoard` | `src/components/StoryboardBoard.tsx` | [`StoryboardBoard.spec.md`](StoryboardBoard.spec.md)、Batch 13 `STORYBOARD_MODE.spec.md` | Batch 11/13 | `SPEC_COMPLETE` | active-canvas 投影、selection 和 Agent mode lifecycle 已形成独立合同。 |
| `AgentDrawer` | `src/components/AgentDrawer.tsx` | Batch 14 `AGENT_SHARE.spec.md`、Batch 11 overlay lifecycle | Batch 11/14 | `BATCH_CONTRACT` | 修改分享、Skill 推荐或 composer 前先读 Batch 14 全套记录。 |
| `script` / `ScriptNode` | `src/components/nodes/ScriptNode.tsx` | [`ScriptNode.spec.md`](ScriptNode.spec.md) | Batch 4-10 历史回归 | `SPEC_COMPLETE` | 这是运行态脚本标题/内容载体；不要依赖未挂载的 `ScriptHeader`。 |
| `image` / `ImageNode` | `src/components/nodes/ImageNode.tsx` | [`ImageNode.spec.md`](ImageNode.spec.md)、[`LibTVOverlayPositioning.contract.md`](LibTVOverlayPositioning.contract.md)、[`LIBTV_IMAGE_ACTION_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md) | `VERIFICATION_LEDGER.md` image rows | `SPEC_COMPLETE` | 这是图片节点、上下浮层、派生节点和 active tool 的总入口；改动前必须看多 zoom 几何合同。 |
| `text` / `TextNode` | `src/components/nodes/TextNode.tsx` | [`TextNode.spec.md`](TextNode.spec.md) | Batch 4-10 历史回归 | `SPEC_COMPLETE` | 保持 inline edit 与 graph selection 分离。 |
| `video` / `VideoNode` | `src/components/nodes/VideoNode.tsx` | [`VideoNode.spec.md`](VideoNode.spec.md)、视频处理跨切面合同 | Batch 21-33、视频专项 verifier | `SPEC_COMPLETE` | ready/empty/pending/failed 是不同状态，不能只按媒体类型复用一个面板。 |
| `script-execution` / `ScriptExecutionNode` | `src/components/nodes/ScriptExecutionNode.tsx` | [`ScriptExecutionNode.spec.md`](ScriptExecutionNode.spec.md)、Batch 35 Director workspace | Batch 35+ | `DOMAIN_CONTRACT` | 入口只负责 Director 生命周期；3D 行为读 Director 域合同。 |
| `storyboard-group` / `StoryboardGroupNode` | `src/components/nodes/StoryboardGroupNode.tsx` | [`StoryboardGroupNode.spec.md`](StoryboardGroupNode.spec.md)、Batch 24/29/33 图事务 | 对应 graph verifier | `SPEC_COMPLETE` | 修改相对布局或父子边时同步验证 undo/redo。 |
| `shot-breakdown` / `ShotBreakdownNode` | `src/components/nodes/ShotBreakdownNode.tsx` | [`ShotBreakdownNode.spec.md`](ShotBreakdownNode.spec.md)、Batch 24 | Batch 24 | `SPEC_COMPLETE` | 输入态与结果组必须分别记录。 |
| `shot-breakdown-result` / `ShotBreakdownResultNode` | `src/components/nodes/ShotBreakdownResultNode.tsx` | Batch 24 `SHOT_BREAKDOWN_WORKFLOW.spec.md`、`BEHAVIORS.md` | Batch 24 graph transaction | `COVERED_BY_PARENT` | 结果节点由拉片事务创建，暂不重复创建同语义 spec。 |
| `video-clip` / `VideoClipNode` | `src/components/nodes/VideoClipNode.tsx` | [`VideoClipNode.spec.md`](VideoClipNode.spec.md)、Batch 25 workflow | Batch 25 | `SPEC_COMPLETE` | selected overlay `VideoClipEditPanel` 作为同一工作流阅读。 |
| `audio` / `AudioNode` | `src/components/nodes/AudioNode.tsx` | [`AudioNode.spec.md`](AudioNode.spec.md)、Batch 28 audio split | Batch 28 | `SPEC_COMPLETE` | 输出命名、metadata、source edge 和 atomic history 是一个合同。 |
| `long-video-process` / `LongVideoProcessNode` | `src/components/nodes/LongVideoProcessNode.tsx` | [`LongVideoProcessNode.spec.md`](LongVideoProcessNode.spec.md)、Batch 33 | Batch 33 | `SPEC_COMPLETE` | 这是 process graph 的 stage renderer，不是后端任务状态。 |
| `default` / `DeletableEdge` | `src/components/nodes/DeletableEdge.tsx` | [`DeletableEdge.spec.md`](DeletableEdge.spec.md)、`AGENTS.md` edge rule | Batch 4-33、35-46 | `SPEC_COMPLETE` | 不改变 hover-flow effect，除非重新取得源站证据。 |

## 3. LibTV 面板与对话框

| 组件 | 源码入口 | 合同/证据入口 | 验证入口 | 状态 | 文档动作 |
|---|---|---|---|---|---|
| `AddNodePanel` | `src/components/AddNodePanel.tsx` | [`AddNodePanel.spec.md`](AddNodePanel.spec.md)、Batch 15 | Batch 15 | `SPEC_COMPLETE` | 菜单项、素材子菜单和 upload/history feedback 分开维护。 |
| `CanvasTabDropdown` | `src/components/CanvasTabDropdown.tsx` | [`CanvasTabDropdown.spec.md`](CanvasTabDropdown.spec.md)、`BEHAVIORS.md` | Batch 16/11 lifecycle | `SPEC_COMPLETE` | 导航动作的 close cleanup 是合同的一部分。 |
| `AssetManagerPanel` | `src/components/AssetManagerPanel.tsx` | [`AssetManagerPanel.spec.md`](AssetManagerPanel.spec.md)、Batch 1 panels | Batch 1/资产抽屉 records | `SPEC_COMPLETE` | canvas/assets tab、树和空态要作为一个状态机阅读。 |
| `ToolboxPanel` | `src/components/ToolboxPanel.tsx` | [`ToolboxPanel.spec.md`](ToolboxPanel.spec.md)、Batch 1 `BATCH_1_PANELS.md` | Batch 1 screenshot + Batch 11 lifecycle | `SPEC_COMPLETE` | 合同明确 source geometry、local used state 和无真实 preset transaction 的边界。 |
| `MaterialLibraryPanel` | `src/components/MaterialLibraryPanel.tsx` | Batch 1 `BATCH_1_PANELS.md`、`AddNodePanel.spec.md` | Batch 1 panels | `COVERED_BY_PARENT` | 素材入口由 AddNodePanel/底部入口共同覆盖。 |
| `CharacterLibraryPanel` | `src/components/CharacterLibraryPanel.tsx` | [`CharacterLibraryPanel.spec.md`](CharacterLibraryPanel.spec.md)、Batch 1 `BATCH_1_PANELS.md` | Batch 1 screenshot + Batch 11 lifecycle | `SPEC_COMPLETE` | source identity/filter 与 clone 普通 image-node handoff 已显式分层。 |
| `HistoryPanel` | `src/components/HistoryPanel.tsx` | [`HistoryPanel.spec.md`](HistoryPanel.spec.md)、Batch 1 `BATCH_1_PANELS.md` | Batch 1 screenshot + Batch 11 lifecycle | `SPEC_COMPLETE` | 资产历史与 graph undo history 明确分离；真实查看/使用/下载仍未实现。 |
| `ImageToolbar` | `src/components/ImageToolbar.tsx` | `ImageNode.spec.md`、[`LibTVOverlayPositioning.contract.md`](LibTVOverlayPositioning.contract.md)、[`LIBTV_IMAGE_ACTION_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md) | image rows in `VERIFICATION_LEDGER.md` | `COVERED_BY_PARENT` | 当前源站动作集合为 `1092.5x49` 证据；不得按旧 `900.5px` 截图扩展动作。 |
| `ImageEditPanel` | `src/components/ImageEditPanel.tsx` | [`ImageEditPanel.spec.md`](ImageEditPanel.spec.md)、`LibTVAutoLink.contract.md` | overlay/AutoLink contract-only | `SPEC_COMPLETE` | 上下锚点、inverse scale、mention identity 必须一起审查。 |
| `VideoGenerationPanel` | `src/components/VideoGenerationPanel.tsx` | [`VideoGenerationPanel.spec.md`](VideoGenerationPanel.spec.md)、Batch 21/22 | Batch 21/22 | `SPEC_COMPLETE` | Seedance 数字是 sampled source fact，不是 provider API contract。 |
| `VideoProcessingToolbar` | `src/components/VideoProcessingToolbar.tsx` | [`VideoProcessingToolbar.spec.md`](VideoProcessingToolbar.spec.md)、`LIBTV_FEATURE_GAP_MATRIX.md` | Batch 23/26-33 | `SPEC_COMPLETE` | 动作必须按 ready-video 状态和 panel handoff 区分。 |
| `PictureEditPanel` | `src/components/PictureEditPanel.tsx` | [`PictureEditPanel.spec.md`](PictureEditPanel.spec.md)、Batch 31 | Batch 31 | `SPEC_COMPLETE` | remove/modify/replace 的 normalized mark 状态不可互换。 |
| `DepthMotionCapturePanel` | `src/components/DepthMotionCapturePanel.tsx` | [`DepthMotionCapturePanel.spec.md`](DepthMotionCapturePanel.spec.md)、Batch 32 | Batch 32 | `SPEC_COMPLETE` | intro、resolution、pending handoff 必须保留。 |
| `SegmentReshootPanel` | `src/components/SegmentReshootPanel.tsx` | [`SegmentReshootPanel.spec.md`](SegmentReshootPanel.spec.md)、Batch 23 | Batch 23 | `SPEC_COMPLETE` | 片段区间、filmstrip 和 prompt token 是同一交互。 |
| `VideoContinuationSelector` | `src/components/VideoContinuationSelector.tsx` | [`VideoContinuationSelector.spec.md`](VideoContinuationSelector.spec.md)、Batch 26 | Batch 26 | `SPEC_COMPLETE` | range constraint 与 target-node transaction 不可拆开实现。 |
| `SubtitleErasePanel` | `src/components/SubtitleErasePanel.tsx` | [`SubtitleErasePanel.spec.md`](SubtitleErasePanel.spec.md)、Batch 27 | Batch 27 | `SPEC_COMPLETE` | smart/region 交接和多矩形历史有独立语义。 |
| `VideoClipEditPanel` | `src/components/VideoClipEditPanel.tsx` | [`VideoClipNode.spec.md`](VideoClipNode.spec.md)、Batch 25 `VIDEO_CLIP_EMPTY_WORKFLOW.spec.md` | Batch 25 | `COVERED_BY_PARENT` | 选中态 editor 随 `VideoClipNode` 工作流维护，暂不重复建 spec。 |
| `CameraConfigDialog` | `src/components/CameraConfigDialog.tsx` | [`CameraConfigDialog.spec.md`](CameraConfigDialog.spec.md)、Batch 21/Director camera contracts | Batch 21、Director 35+ | `SPEC_COMPLETE` | 普通视频相机参数与 Director camera state 不合并。 |
| `CameraMovementDialog` | `src/components/CameraMovementDialog.tsx` | [`CameraMovementDialog.spec.md`](CameraMovementDialog.spec.md)、Batch 21、Director preset contract | Batch 21、Batch 44 | `SPEC_COMPLETE` | 普通生成参数与 Director preset motion 是两个边界。 |
| `MainEntryPanels` | `src/components/*` entry lifecycle | [`MainEntryPanels.spec.md`](MainEntryPanels.spec.md)、Batch 11 overlay lifecycle | Batch 11 | `SPEC_COMPLETE` | 入口互斥、Escape、outside click 是共享生命周期。 |
| `KeyboardShortcutsDialog` | `src/components/KeyboardShortcutsDialog.tsx` | [`KeyboardShortcutsDialog.spec.md`](KeyboardShortcutsDialog.spec.md)、Batch 1 panel audit | Batch 1 screenshot + Batch 11 lifecycle | `SPEC_COMPLETE` | source/clone 命令差异和“帮助文案不等于监听器”边界已显式记录。 |
| `SmartMattingPanel` | `src/components/SmartMattingPanel.tsx` | [`SmartMattingPanel.spec.md`](SmartMattingPanel.spec.md)、Batch 30 `SMART_MATTING_WORKFLOW.spec.md` | Batch 30 | `SPEC_COMPLETE` | panel ownership、measured-width anchor、submit state 与 store transaction 已分层。 |

## 4. Director Desk

Director 是 LibTV clone 内的独立领域。组件行为主要由 Batch 35-46 的领域合同覆盖，不能直接套用普通画布的 node/panel 规则。Batch 34 是考古与可借鉴性研究，没有专项 verifier；Batch 45/46 已形成有界 group/crowd 与 capture gallery 合同和专项 verifier。

| 组件/模块 | 源码入口 | 领域合同/证据 | 当前状态 | 下一步 |
|---|---|---|---|---|
| `DirectorDesk` | `src/components/director/DirectorDesk.tsx` | Batch 35 `DIRECTOR_WORKSPACE.spec.md`、Batch 40/41/45 records | `DOMAIN_CONTRACT` | 改生命周期、capture return 或响应式 shell 时读最新 Director maturity assessment。 |
| `DirectorViewport` | `src/components/director/DirectorViewport.tsx` | Batch 35 workspace、Batch 37-44 camera/path contracts | `DOMAIN_CONTRACT` | 真实 R3F、capture、camera target、path/phone guard 必须联动。 |
| `DirectorObjectTree` | `src/components/director/DirectorObjectTree.tsx` | Batch 35 workspace、Batch 43/45 source evidence | `DOMAIN_CONTRACT` | selection 与 group/crowd tree 以 Batch 45 有界合同为准。 |
| `DirectorInspector` | `src/components/director/DirectorInspector.tsx` | Batch 35 workspace、Batch 42 pose、Batch 43 follow、Batch 44 camera、Batch 46 capture gallery | `DOMAIN_CONTRACT` | 角色、相机、路径、capture gallery 控件按 selection route 维护。 |
| `DirectorTimeline` | `src/components/director/DirectorTimeline.tsx` | Batch 36 timeline、37 motion path、42 pose、44 camera、45 groups | `DOMAIN_CONTRACT` | 新轨道先扩展 typed track union，再更新播放/采样/验证合同。 |
| `DirectorCurveEditor` | `src/components/director/DirectorCurveEditor.tsx` | Batch 37 `DIRECTOR_MOTION_PATH.spec.md` | `DOMAIN_CONTRACT` | 只处理 speed curve；不要与 timeline keyframe 语义混成一类。 |
| `DirectorMannequin` | `src/components/director/DirectorMannequin.tsx` | Batch 42 `DIRECTOR_CHARACTER_POSE.spec.md`、Batch 45 groups | `DOMAIN_CONTRACT` | rig 与 crowd/group rendering 以 Batch 42/45 领域合同为准。 |
| `DirectorExportPanel` | `src/components/director/DirectorExportPanel.tsx` | Batch 40 `DIRECTOR_ANIMATION_EXPORT.spec.md` | `DOMAIN_CONTRACT` | 修改导出字段必须同时读 `videoExport` 类型和 capture return。 |
| `DirectorPhoneVcamPanel` | `src/components/director/DirectorPhoneVcamPanel.tsx` | Batch 41 `DIRECTOR_PHONE_VCAM.spec.md` | `DOMAIN_CONTRACT` | 保持 phone preview 与 viewport/path conflict guard。 |
| `directorStore` / math utilities | `src/store/directorStore.ts`, `src/components/director/director*.ts` | Batch 35-46 各领域合同、`COMPONENT_INVENTORY.md` | `DOMAIN_CONTRACT` | 纯数学模块必须保持可序列化、无 Three.js runtime ref；变更需更新对应 domain spec。 |
| Director Batch 45 group/crowd slice | `Director*` + `directorStore` | Batch 45 `DIRECTOR_GROUPS.spec.md`、source evidence | `DOMAIN_CONTRACT` | 专项 verifier 与 serial regression 已记录通过；仍只是有界 clone 合同。 |
| Director Batch 46 capture gallery slice | `Director*` + `directorStore` | Batch 46 `DIRECTOR_CAPTURE_GALLERY.spec.md`、source evidence、focused verifier | `DOMAIN_CONTRACT` | 截图图库、查看器、单/批量回流与清空边界已稳定；仍是有界 clone 合同。 |

## 5. 明确不作为 LibTV 合同的组件

| 组件 | 源码入口 | 状态 | 说明 |
|---|---|---|---|
| `PlusIndicator` | `src/components/PlusIndicator.tsx` | `LEGACY` | no-op stub；真实连接 affordance 是 React Flow `<Handle>`。 |
| `CustomHandle` | `src/components/CustomHandle.tsx` | `LEGACY` | 当前未使用的旧 handle prototype，不作为新连接交互参考。 |
| `Frameos*` | `src/components/frameos/**` | `OUT_OF_SCOPE` | FrameOS 有独立 route/store/研究目录，见 [`research/frameos/COMPONENT_INVENTORY.md`](../frameos/COMPONENT_INVENTORY.md)。 |
| `FrameosNodeEditPanel` | `src/components/frameos/FrameosNodeEditPanel.tsx` | `DEBUG_ONLY` | AGENTS 明确规定它不是源站功能，不能倒灌到 LibTV 合同。 |

## 6. 当前最值得补的合同

按“会阻塞后续复刻决策”的优先级排序，而不是按文件数量排序：

本轮已补齐 `ToolboxPanel`、`CharacterLibraryPanel`、`HistoryPanel`、`SmartMattingPanel`、`StoryboardBoard` 和 `KeyboardShortcutsDialog` 的独立合同，并把未挂载的 `ScriptHeader` 明确降级为 legacy。合同将 source fact、clone fact、clone decision 和未验证业务副作用分开，因此不再列为待补缺口。

| 优先级 | 缺口 | 影响 | 建议触发条件 |
|---|---|---|---|
| P2 | Director 组件级拆分合同 | 目前领域合同已经足够支持连续批次；逐文件拆分会重复大量 domain contract | Director domain 稳定、开始多人并行修改同一组件时再拆。 |

## 7. 新增组件规范的判定规则

新增或升级 spec 前，先回答：

1. 该组件是否有自己的状态机、选中态、overlay anchor 或 graph transaction？如果没有，优先挂到父合同。
2. 是否存在可复核的源站证据，而不是只有一张历史截图或 clone 当前实现？如果没有，状态保持 `NEEDS_SPEC`，不要编造精确数值。
3. 是否会被多个 agent 或多个批次反复修改？如果会，建立稳定组件合同；否则保留批次级合同即可。
4. 是否跨越 LibTV 与 FrameOS 的边界？如果是，拆成独立合同，不共享 route/store 语义。
5. 是否涉及 graph、history、任务消耗或源站共享画布写入？如果是，合同必须包含风险和 fixture gate。

## 8. 维护规则

- 新的独立组件 spec 加入本目录 `README.md`，并在本表增加一行。
- 新的跨切面证据同时更新 [`TRACEABILITY_MATRIX.md`](../TRACEABILITY_MATRIX.md) 与 [`VERIFICATION_LEDGER.md`](../VERIFICATION_LEDGER.md)。
- 新批次只在自身 README/PLAN/IMPLEMENTATION 稳定后再更新本表；并行 WIP 只标记，不覆盖其他开发者文件。
- 组件源码重命名、删除或移动时，先更新本表和 `COMPONENT_INVENTORY.md`，再检查本地 Markdown 链接。
- 组件合同只描述研究和 clone 行为边界；没有明确编码授权时，不由此文档触发代码修改。
