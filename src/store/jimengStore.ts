"use client";

import { create } from "zustand";
import {
  applyEdgeChanges,
  applyNodeChanges,
  addEdge as addEdgeRf,
} from "@xyflow/react";
import type { Edge, EdgeChange, NodeChange } from "@xyflow/react";
import { FEEDBACK } from "@/components/jimeng/jimengFeedback";

import type {
  JimengAudioNodeData,
  JimengImageNodeData,
  JimengNode,
  JimengVideoNodeData,
} from "@/types/jimeng";

/**
 * 即梦画布复刻的独立 store。
 * 与 canvasStore / frameosStore 完全隔离 (AGENTS.md 硬约束)。
 *
 * 初始 mock 数据对齐源站提取证据:
 * - 节点 1: 本地上传视频节点 (有内容, 6s), 世界坐标 (675.6, 280.5)
 * - 节点 2: 空视频节点 "视频 1", 世界坐标 (1442.1, 323.2)
 * - 初始视口 zoom 0.7299 (源站底栏显示 73%)
 * 坐标/尺寸为 SOURCE_FACT (见 docs/research/jimeng-canvas/README.md)。
 */

/* ⭐⭐⭐ Batch 1032-④-B（C11）：**真的视频文件**（ffmpeg 生成的 mp4，
 * 落在 `public/videos/` 下 ⇒ 走 Next 的静态托管）。
 * ⚠️ 路径是**相对站点根**的 ⇒ 同一份资源在 `/jimeng/canvas/demo` 这类
 *   子路径页面上也能取到（用 `/videos/...` 而不是相对的 `videos/...`）。 */
const DEMO_VIDEO_SRC = "/videos/jimeng-demo.mp4";

const MOCK_POSTER =
  "data:image/svg+xml;utf8," +
  encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" width="569" height="320">` +
      `<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">` +
      `<stop offset="0" stop-color="#2E2E30"/><stop offset="0.55" stop-color="#1B1B1D"/><stop offset="1" stop-color="#121214"/>` +
      `</linearGradient></defs>` +
      `<rect width="569" height="320" fill="url(#g)"/>` +
      `<circle cx="180" cy="210" r="70" fill="#242426"/>` +
      `<circle cx="410" cy="190" r="52" fill="#28282A"/>` +
      `<rect x="0" y="248" width="569" height="72" fill="#161618"/>` +
      `</svg>`,
  );

/** ⭐ Batch 1032-②b-2：图片生成产物用的 mock 画面 (data URI)。
 *
 *  ⚠️ **不是源站资产** —— 源站的图片生成要付费才能看到产出，
 *  ⇒ ⇒ 复刻侧用一张合成占位图 (CLONE_DECISION)，与视频侧 `MOCK_POSTER` 同族。 */
const MOCK_IMAGE =
  "data:image/svg+xml;utf8," +
  encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360">` +
      `<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">` +
      `<stop offset="0" stop-color="#34343A"/><stop offset="0.6" stop-color="#232328"/><stop offset="1" stop-color="#17171A"/>` +
      `</linearGradient></defs>` +
      `<rect width="480" height="360" fill="url(#g)"/>` +
      `<circle cx="150" cy="140" r="52" fill="#3A3A42"/>` +
      `<rect x="250" y="96" width="150" height="150" rx="14" fill="#2C2C33"/>` +
      `<rect x="0" y="296" width="480" height="64" fill="#141416"/>` +
      `</svg>`,
  );

/** 批 938：走「互斥槽位」的瞬时浮层。
 *
 * ⚠️ 只列**源站实测过互斥**的那几个（探针 937）。
 * 源站的 `canvas-agent-panel`（与 AI 对话侧栏）**不在**这张表里 ——
 * 它是**开关式常驻侧栏**，语义与瞬时浮层**不对称**（见下面的 `openAiDrawer`）。 */
export type JimengTransientLayer =
  | "search"
  | "history"
  | "more"
  | "zoom";

export interface JimengCanvasState {
  /** 画布元信息 (顶栏) */
  project: { name: string; saved: boolean };

  nodes: JimengNode[];
  edges: Edge[];

  /** 当前选中节点 (驱动 NodeToolbar / 生成面板) */
  selectedNodeId: string | null;

  /** 底栏缩放百分比显示 */
  zoomPercent: number;

  /** 全局 toast 文本 (Batch 40: 生成面板发送等 mock 反馈) */
  toast: string | null;
  pushToast: (text: string) => void;
  clearToast: () => void;
  /** 生成面板设置 (Batch 61: 持久化到 store) */
  genModel: string;
  setGenModel: (model: string) => void;

  // ───── Actions ─────
  onNodesChange: (changes: NodeChange<JimengNode>[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  /** Batch 1032-②a: 用户在画布上**拖出一条连线** ⇒ 落一条边。
   *
   *  ⚠️⭐⭐ 此前 `<ReactFlow>` **没有 `onConnect`** ⇒ 节点明明有
   *   `JimengConnectHandles`（两个 `<Handle>` 都在）、用户明明能拖出连线的样子，
   *   **却一条边也建不出来** ⇒ 这是「FEATURE_MISSING」那一类里最伤的一条：
   *   画布的核心交互（把两个节点连起来）整个不存在。
   *
   *  ⚠️ 边的形状照抄 `addVideoNodeAfter` 里已有那条（`{id, source, target}`）
   *   ⇒ **不带 `sourceHandle` / `targetHandle`** ——
   *   本仓的 `<Handle>`（见 `JimengConnectHandles.tsx`）**根本没有 id**
   *   ⇒ ⇒ React Flow 的 handle 匹配按 `null` 走
   *   ⇒ ⇒ ⇒ 而 `src/app/frameos/canvas/[id]/page.tsx` 那份实现**带** handle
   *   ⇒ ⇒ ⇒ **不同口径，不能照抄**（照抄会把 handle 传成不存在的 id）。
   *
   *  重复边用 React Flow 官方的 `addEdge` 判重（同 id 即视为重复）
   *  ⇒ ⇒ **不自己写一套判重**（「同一个东西要比同一个口径」）。 */
  addEdge: (edge: Edge) => void;
  selectNode: (id: string | null) => void;
  /** Batch 803: 顶栏「节点摘要」弹层点节点 → 选中并聚焦该节点。
   *  nonce 用于重复点同一节点时也能重新触发（否则值不变、effect 不跑）。 */
  focusNodeRequest: { id: string; nonce: number } | null;
  requestFocusNode: (id: string) => void;
  setZoomPercent: (z: number) => void;
  /** "+" 手柄菜单 → 新建视频节点 (右侧 160 间距) 并连线 (Batch 4) */
  addVideoNodeAfter: (sourceId: string) => void;
  removeNode: (id: string) => void;
  /** 批量删除选中节点 (Batch 38 多选深化)，单条历史记录 */
  removeNodes: (ids: string[]) => void;
  duplicateNode: (id: string) => void;
  /** 右键菜单 复制/粘贴 (Batch 4/52: 泛化为多节点剪贴板，含内部连线) */
  clipboard: { nodes: JimengNode[]; edges: Edge[] } | null;
  copyNode: (id: string) => void;
  copyNodes: (ids: string[]) => void;
  pasteNodes: () => void;
  /** 局部重拍编辑态 (Batch 5): 进入后节点显示帧条选区 + 重拍面板 */
  repaintNodeId: string | null;
  enterRepaint: (id: string) => void;
  exitRepaint: () => void;
  /** 视频编辑模式 (Batch 6): 工具药丸 + 编辑提示条 */
  editNodeId: string | null;
  enterEdit: (id: string) => void;
  exitEdit: () => void;
  /** 提示词反推面板 (Batch 8, mock) */
  inferNodeId: string | null;
  enterInfer: (id: string) => void;
  exitInfer: () => void;
  /** 截取帧-自定义 帧选择器 (Batch 9)；mode: first/last 为首帧/尾帧预选 (Batch 10) */
  framePickerNodeId: string | null;
  framePickerMode: "first" | "last" | "custom";
  enterFramePicker: (id: string, mode?: "first" | "last" | "custom") => void;
  exitFramePicker: () => void;
  /** 视频修剪编辑态 (Batch 10) */
  trimNodeId: string | null;
  enterTrim: (id: string) => void;
  exitTrim: () => void;
  /** 智能超清/补帧 mock 任务 (Batch 11, CLONE_DECISION — 源站会真实提交付费任务) */
  tasks: JimengTask[];
  startTask: (nodeId: string, kind: JimengTask["kind"]) => void;
  /* ⭐⭐⭐⭐⭐ Batch 1032-④-B（C09）：**生成历史** —— 真的生成任务列表。
   *
   * 此前顶栏「生成历史」面板恒显一句写死的「暂无生成历史」——
   * 而整个文件**不 import store** ⇒ ⇒ 它**永远**是那句话。
   * ⇒ ⇒ 现在它读 store 里的 `generationHistory`：每一次生成（视频/图片/音频）
   *   真的留下一条记录，面板把它**逐条列出来**。
   *
   * ⚠️ 为什么不用现成的 `tasks` 字段：那个是**瞬态**的（4s 后自动清除），
   *   它是「处理中」的指示，不是「历史」⇒ ⇒ 两者必须分开。
   */
  generationHistory: JimengGenerationRecord[];
  /** 往生成历史里记一条（由各生成动作自动调用） */
  pushGeneration: (rec: Omit<JimengGenerationRecord, "id" | "seq">) => void;
  /** 「与 AI 对话」右侧抽屉 (Batch 12) */
  aiDrawerOpen: boolean;
  setAiDrawerOpen: (open: boolean) => void;
  /** 批 216: 打开抽屉时的预填提示词 (提示词反推 → 视频反解流程) */
  aiDrawerPrefill: string | null;
  /** 批 269 SOURCE_FACT: 预填携带的视频引用 chip (缩略图+截断标题) */
  aiDrawerRefChip: { poster: string; label: string } | null;
  openAiDrawer: (prefill?: string, refChip?: { poster: string; label: string }) => void;
  /** 批 219 SOURCE_FACT: 抽屉草稿跨关闭保留 (源站重开后预填仍在) */
  aiDrawerDraft: string;
  /** Batch 834：AI 抽屉的**真会话模型**。
      此前 `messages` 是 `JimengAiDrawer` 的组件本地 useState ——
      抽屉一卸载会话就没了，而「新建会话」按钮是 `setMessages([])`，
      也就是**直接销毁**当前会话、不可恢复。那不是「新建」，是「删除」。
      搬进 store 之后：新建 = 追加一条并切过去，旧会话仍在列表里可切回。 */
  aiSessions: AiSession[];
  aiActiveSessionId: string | null;
  /** 追加一条消息到当前会话；没有当前会话就**先建一条**。
      标题取首条用户消息的前 24 字（与 `send()` 里 mock 回复的截断长度一致）。 */
  appendAiMessage: (role: "user" | "agent", text: string) => void;
  /** 新建会话并切过去（**不删**旧的） */
  newAiSession: () => void;
  /** 切换当前会话；id 不存在时不动 */
  selectAiSession: (id: string) => void;
  setAiDrawerDraft: (draft: string) => void;
  /** 批 938 SOURCE_FACT：**瞬时浮层的互斥槽位**。
   *
   * 源站实测（探针 937，2 轮 × 20 个有向配对，两轮逐项完全相同）：
   * 开 A 再开 B，**B 把 A 关掉 24/24，一个例外都没有** ——
   * `canvas-feature-panel`（搜索/生成历史）10/10、`canvas-zoom-menu`（缩放）6/6、
   * `canvas-context-menu`（右键）8/8 全部被对方关掉。
   *
   * ⚠️⚠️ 而在此之前，复刻这边**每个层各自一个本地 useState**
   * （TopBar 的 search/history/more、BottomDock 的 zoomMenu、Workspace 的
   * contextMenu/paneMenu）⇒ **没有任何一处能实现「开一个关掉另一个」**，
   * 只有 TopBar 内部手动关掉了 search↔history 一对。
   * ⇒ 这里给出**单一来源**的槽位，互斥才成为结构保证而不是自觉。
   *
   * ⚠️ 复刻**允许**哪些层走这个槽位、源站其余形态（资产库/项目信息/时间线全屏/
   * 视频全屏）的互斥**本批没测** ⇒ 推广到那些层是**推断、未验证**。
   * 这里只把**已测到的 4 个**接进来，其余保持原样。 */
  transientLayer: JimengTransientLayer | null;
  /** 开一个瞬时层：先关掉当前占着槽位的那个（**同 id 再开 = 关**，源站的 toggle 语义） */
  openTransientLayer: (id: JimengTransientLayer) => void;
  /** 关掉瞬时层；不给 id 就无条件清空（Escape / 点击空白走这条） */
  closeTransientLayer: (id?: JimengTransientLayer) => void;
  /** 资产库模态框 (Batch 72, SOURCE_FACT 左栏 资产库 点击打开) */
  assetsOpen: boolean;
  setAssetsOpen: (open: boolean) => void;
  /** 引用参考「从画布选择」点选模式 (Batch 793, SOURCE_FACT 2026-09-27:
      面板发起, 整画布蓝色描边 + 顶部 pill, workspace 拦截节点点击) */
  refPicking: boolean;
  pickedRefNodeId: string | null;
  startRefPicking: () => void;
  cancelRefPicking: () => void;
  pickRefNode: (id: string) => void;
  clearPickedRefNode: () => void;
  /** ⭐⭐⭐ Batch 1032-②b-3：@ 提及面板**是否开着**。
   *
   *  为什么要放 store（而不是组件本地 state）：
   *  源站的退出路径是**分级**的（手册 20-reference「退出路径」表）：
   *    | 操作 | 面板 | 提示词 |
   *    | `Esc` | **关** | **保留** |
   *  ⇒ ⇒ Esc 在 @ 面板开着时**只关面板**，**不退出编辑态**、**不清空提示词**。
   *  ⇒ ⇒ 而「Esc 的总调度」在 workspace（`JimengWorkspace` 的 window keydown）
   *  ⇒ ⇒ 若面板开关只在组件本地 ⇒ ⇒ workspace **看不见它**
   *  ⇒ ⇒ Esc 会直接退出整个编辑态 ⇒ ⇒ 与源站不符。
   *  ⇒ ⇒ 所以这个开关必须是**全局可见**的一等状态。
   */
  mentionPanelOpen: boolean;
  /** 开/关 @ 面板（开=面板当前挂在某处；关=没有） */
  setMentionPanelOpen: (open: boolean) => void;
  /**
   * ⭐⭐⭐ Batch 1032-②b-4：「**已展开的生成器**」浮层（SOURCE_FACT 批次 1032-②b-1：
   * 源站点「展开视频生成器」⇒ 出一个 `role="dialog"` / `aria-label="已展开的视频生成器"`
   * / `position: fixed` / 920×480 / radius 20 / z 50 的**居中浮动面板**）。
   *
   * ⭐⭐⭐ **为什么它必须住在 store 里**（与 `mentionPanelOpen` 同一个理由）：
   * 源站的退出路径是**分级的** —— `Esc` 先关**最上层浮层**、**不退编辑态**
   * ⇒ ⇒ 而 `Esc` 的总调度在 workspace ⇒ ⇒ **组件本地 state 会被 workspace 看不见**
   * ⇒ ⇒ ⇒ 于是 Esc 会直接退出整个编辑态 ⇒ ⇒ **与源站不符**。
   */
  expandedGenLayer: { kind: "video" | "image" | "audio"; nodeId: string } | null;
  /** 打开「已展开的生成器」浮层（kind = 从哪枚面板打开的） */
  openExpandedGenLayer: (kind: "video" | "image" | "audio", nodeId: string) => void;
  /** 关闭「已展开的生成器」浮层 */
  closeExpandedGenLayer: () => void;
  /** 离线编辑冲突对话框 (Batch 82, SOURCE_FACT 81-after-reload-state.png)；
      复刻侧无真实离线态，经 dev window hook 触发 */
  offlineDialogOpen: boolean;
  setOfflineDialog: (open: boolean) => void;
  /* ⭐⭐⭐⭐⭐ Batch 1032-④-B（C10）：**离线同步 / 丢弃**要有真的动作。
   *
   * 此前对话框那两枚按钮只弹一句「离线修改已同步 / 已丢弃离线修改」⇒
   * ⇒ **一个字都没同步、也没丢弃**。
   *
   * 现在：
   *  · `offlineEdits` 是**真的待同步列表**（离线期间的每次改动都记一条）；
   *  · `syncOfflineEdits()` 把当前画布**存成新的服务器快照**并清空待同步列表
   *    ⇒ 「同步了」这件事**有状态变化**可核对；
   *  · `discardOfflineEdits()` 把画布**真的退回服务器快照**
   *    ⇒ 「丢弃了」这件事**看得到画布变了**。
   *
   * ⚠️ `offlineMode` 是**离线态开关**（默认关）。它开着时，画布的任何改动
   *   都会被记进 `offlineEdits` ⇒ ⇒ 对话框才有东西可同步 / 可丢弃。
   *   （此前这个对话框**没有任何东西可丢** —— 「丢弃」是空的。）
   */
  offlineMode: boolean;
  offlineEdits: { id: string; label: string }[];
  setOfflineMode: (on: boolean) => void;
  syncOfflineEdits: () => void;
  discardOfflineEdits: () => void;
  /** 小地图开关 (Batch 91, SOURCE_FACT 底部 dock 小地图按钮) */
  minimapOpen: boolean;
  setMinimapOpen: (open: boolean) => void;
  /** 连线显隐 (Batch 93, SOURCE_FACT dock 显示连线 canvas-dock-lines) */
  edgesVisible: boolean;
  setEdgesVisible: (visible: boolean) => void;
  /** 顶部项目名行内重命名 (Batch 29, SOURCE_FACT) */
  renameProject: (name: string) => void;
  /** ⭐⭐⭐ Batch 1032-④-B（C02）：**项目列表** —— 「新建画布项目」要真建出项目来。
   *
   *  此前「新建画布项目」只弹一句复述按钮名的话（`新建画布项目（mock）`），
   *  而 `jimengFeedback.ts` 的注释自己就写着：**复述按钮名＝零信息量**。
   *  ⇒ ⇒ 「建出项目来」这件事**没有任何状态承载** ⇒ ⇒ 点了等于没点。
   *
   *  现在它是真的：`projects` 是一条**真的列表**，`createProject` 往里加一条，
   *  顶栏项目名切到新项目，项目面板把列表**逐条列出来**（可切回去）。
   *
   *  ⚠️ 列表项的 `id` 是**计数器**而不是 `Date.now()` —— 产物/门禁里不许出随机量，
   *   而这个列表会被 1033/1034 的门读。
   */
  projects: { id: string; name: string }[];
  createProject: (name?: string) => void;
  /** 切换到列表里的某个项目（顶栏项目名跟着变） */
  switchProject: (id: string) => void;
  /* ⭐⭐⭐ Batch 1032-④-B（C05）：**AI 生成水印设置**要真的存下来。
   *
   * 此前「保存设置」只 `setSaved(true)` —— 改的是**组件自己的 useState**，
   * 关窗即丢；而界面上却写着「已保存」。
   * ⇒ ⇒ 现在设置落在 **store**（跨关窗/重开都还在）**并持久化到
   *   localStorage**（连刷新也还在）。
   */
  watermark: { noWatermark: boolean };
  setWatermark: (noWatermark: boolean) => void;
  /** 底部 dock 工具态 (Batch 20): V 切换移动工具 */
  toolActive: "select" | "move";
  setToolActive: (tool: "select" | "move") => void;
  /** Batch 837: 工具切换的**唯一**实现。dock 那枚钮与 V 快捷键此前各写一遍
   *  「select ↔ move」，其中按钮那侧还写成了**强制置 select** —— 于是键盘能切、
   *  按钮不能，两条路会漂。共用一条（同批 832 的规矩）。 */
  toggleToolActive: () => void;
  /** 播放交互 (Batch 15/24): 切换播放态 / mock 时间走动 / 双击从头重播 */
  togglePlay: (id: string) => void;
  restartPlay: (id: string) => void;
  tickPlay: (id: string, delta: number) => void;
  /** 编组 (Batch 39): ⌘G 创建编组 / ⌘⇧G 取消编组 (快捷键面板 SOURCE_FACT) */
  groupSelected: () => void;
  ungroupSelected: () => void;
  /** 全选 (Batch 46): ⌘A */
  selectAll: () => void;
  /** 全屏预览 (Batch 46): store 驱动，Escape/pane 点击统一关闭 */
  previewNodeId: string | null;
  openPreview: (id: string) => void;
  closePreview: () => void;
  /** 静音切换 (Batch 29) */
  toggleMute: (id: string) => void;
  /** ⭐⭐⭐⭐⭐ 1032-⑫：**音量**（0–1）—— 全屏播放器的音量滑杆是**真状态**。
   *
   *  此前那枚滑杆是静态 span（`role="slider"` 却零处理器）⇒ 拖了没反应。
   *  ⇒ ⇒ 现在拖动写回这里，`JimengVideoPreview` 与卡面上的 `<video>` 同步
   *  `.volume` ⇒ ⇒ 拖完**听得见**。
   */
  setVolume: (id: string, volume: number) => void;
  /** 媒体失效态 (Batch 67, SOURCE_FACT 视频播放失败+重试): 触发/清除 */
  setMediaError: (id: string, error: boolean) => void;
  /** 进度条点击 seek (Batch 32)，fraction ∈ [0,1] */
  seek: (id: string, fraction: number) => void;
  /** 修剪确认 (Batch 33/44): 裁剪后的时长与新起点写回节点并入撤销栈 */
  applyTrim: (
    id: string,
    trimmedDuration: number,
    startOffset?: number,
  ) => void;
  /** 生成面板发送 (Batch 50)：空节点进入生成中，3s 后完成变为有内容节点 (mock) */
  generateInto: (id: string, prompt: string) => void;
  /** ⭐⭐⭐ Batch 1032-②b-2：图片生成 (CLONE_DECISION)。
   *
   *  **为什么此前没有这个 action**：图片生成面板的「生成」按钮**整枚没有 onClick**
   *  ⇒ ⇒ 1032 审计把它登记成死按钮（DEAD_NO_HANDLER）。
   *  ⇒ ⇒ 而**不能**用「加个空 handler」把它从死按钮清单里摘掉 ——
   *  那样它只是从「点不动」变成「点了什么也不会发生」，**比死按钮更坏**。
   *
   *  **它做什么**：与视频侧 `generateInto` **同构** —— 立即进入「生成中」，
   *  3s 后节点变成**有画面的**图片节点（`poster` 被填上）。
   *  ⇒ ⇒ 判据可以写成「**某个可观察的东西变了**」（节点里出现了 `<img>`），
   *  而不是一个假 toast。
   *
   *  ⚠️ **CLONE_DECISION，不是 SOURCE_FACT**：源站点「生成」会提交付费任务，
   *  ⇒ ⇒ 复刻侧不观测那个结果（也不该观测），
   *  ⇒ ⇒ 因此这里只保证「有一个可观察的状态变化」，**不假装复刻了源站产出**。 */
  generateImageInto: (id: string, prompt: string) => void;
  /** ⭐⭐⭐ Batch 1032-②b-2：音频生成 (CLONE_DECISION)，与上面同构。
   *
   *  **注意它修的不是死按钮**：音频面板的「生成」**有 onClick**，
   *  但函数体是空的（`if (canSend) { /* mock: 未接入 *\/ }`）
   *  ⇒ ⇒ 静态门把它算成 `WIRED` ⇒ ⇒ **静态门看不见这一类糊弄**
   *  ⇒ ⇒ 这是「有 onClick 但函数体是空的」（NOOP）那一类，只能靠运行时门抓。
   *
   *  它做什么：立即「生成中」，3s 后完成 ⇒ ⇒ 节点上出现时长徽标。 */
  generateAudioInto: (id: string, prompt: string) => void;
  /** 节点数据 patch (Batch 31 颜色标记；Batch 38 泛化为任意节点) */
  updateNodeData: (id: string, patch: Record<string, unknown>) => void;
  /** 节点数据 patch，**且可整体撤销** (Batch 825，时间线剪辑动作)
   *
   *  为什么不直接让 `updateNodeData` 记历史：它被**逐字输入**等热路径调用
   *  （`JimengTextNode.tsx:143` 每次改字都调），那样按一次撤销只能退一个字，
   *  历史栈还会被撑爆。而时间线的分割 / 剪裁 / 增删片段是低频、语义上
   *  该**整体**撤销的动作 —— 这类才走本入口。
   *
   *  另一个理由：撤销按钮与 store 的历史栈必须对得上。若剪辑动作不进栈，
   *  点「撤销」撤掉的会是很久之前的别的动作（全屏编辑器里点一下就把
   *  时间线节点本身撤没了，浮层随之消失）。 */
  updateNodeDataUndoable: (id: string, patch: Record<string, unknown>) => void;
  /** 节点重命名 (Batch 87, SOURCE_FACT 标题行即 Rename 按钮)：入撤销栈 */
  renameNode: (id: string, title: string) => void;
  /** 插入节点 (Batch 17/19): 左栏 / + 菜单 */
  addNodeAt: (
    kind:
      | "video"
      | "image"
      | "text"
      | "audio"
      // Batch 805 SOURCE_FACT: 左栏「时间线」「主体」「导演台」点下去
      // 是在画布中心插入对应**节点**，不是打开浮层。
      | "timeline"
      | "subject"
      | "director",
    position: { x: number; y: number },
  ) => void;
  /** 本地上传 (Batch 73, SOURCE_FACT): 上传文件 → 本地视频节点
      (标题=文件名, mock 海报)，单文件单条历史 */
  addLocalUpload: (name: string, position: { x: number; y: number }) => void;
  /** 本地上传图片 (Batch 832): 资产栏拖放 / 「导入」按钮的真入库路径。
      与 `addLocalUpload` 同构，但带**真实的 poster**（调用方用 FileReader
      读出的 data URL）—— 图片节点渲染的是真 `<img src>`，所以画布上会出现
      真的那张图。一次 `set` 完成 ⇒ 只产生**一条**撤销记录。 */
  addLocalImage: (name: string, dataUrl: string, position: { x: number; y: number }) => void;
  /** 截取帧 首帧/尾帧 (Batch 62, SOURCE_FACT): 直接产出图片节点到源节点
      右侧 (自动右移避让同行节点)，带 poster 与 lineage 连线，不打开帧选择器。
      ⭐⭐⭐ Batch 1032-④-B（C06）：`atTime` 是**选中的那一帧的时间码** ——
      此前帧选择器把时间传出来了（`onConfirm(frameTime)`），
      而调用点 `onConfirm={() => …}` 把它**丢掉** ⇒ 用户选的帧不是他要的那一帧。
      ⇒ ⇒ 现在时间码**真的被用起来**：写进产出节点的 `frameTime`，
      且**源节点的播放头真的移到那一帧**（`currentTime`）。 */
  captureFrame: (
    sourceId: string,
    frame: "first" | "last" | "custom",
    atTime?: number,
  ) => void;
  /** 布局-智能布局 (Batch 63, SOURCE_FACT 菜单项/CLONE_DECISION 语义):
      选中节点按 x 排成一行 (y 对齐选区最小值)，单条历史 */
  arrangeSelected: () => void;
  /** 布局-宫格布局 (Batch 63, SOURCE_FACT 菜单项/CLONE_DECISION 语义):
      选中节点按 x 排成 ceil(√n) 列网格，单条历史 */
  arrangeSelectedGrid: () => void;
  /** 组背景色 (Batch 63, SOURCE_FACT 背景色调色板: 无颜色+青绿/靛蓝/紫/橙/黄) */
  groupColors: Record<string, string>;
  setGroupColor: (groupId: string, color: string | null) => void;
  /** 组显示名 (Batch 63, SOURCE_FACT: 源站编组生成「编组 N」标题卡片) */
  groupNames: Record<string, string>;
  /** 撤销/重做历史栈 (Batch 14)；仅记录图结构变更，不含选中态 */
  past: { nodes: JimengNode[]; edges: Edge[] }[];
  future: { nodes: JimengNode[]; edges: Edge[] }[];
  undo: () => void;
  redo: () => void;
}

/** Batch 834：AI 抽屉的一条会话。 */
export interface AiSession {
  id: string;
  /** 取首条用户消息的前 24 字；还没有用户消息时是「新会话」 */
  title: string;
  messages: { role: "user" | "agent"; text: string }[];
}

export interface JimengTask {
  id: string;
  nodeId: string;
  // 批 528 SOURCE_FACT (用户手册): 深度动作捕捉 为工具下拉编辑组付费项
  kind: "upscale" | "interpolate" | "motion-capture";
}

/** ⭐⭐⭐ Batch 1032-④-B（C09）：一条生成历史。
 *
 * ⚠️ `id` 用**序号**而不是时间戳 ⇒ 确定、可被门禁逐条核对
 * （且 `at` 也用**序号**而非墙上时钟 ⇒ 产物里不许出现随机量/时间戳）。
 */
export interface JimengGenerationRecord {
  id: string;
  seq: number;
  /** 生成类型：图片 / 视频 / 音频 / 任务 */
  kind: "图片" | "视频" | "音频" | "任务";
  /** 这次生成的标题（节点标题或提示词摘要） */
  title: string;
  /** 提示词（用户当时输入的那句） */
  prompt: string;
}

// Batch 66 (SOURCE_FACT): 顶栏 保存中…/已保存 + 下载按钮 导出前请保存画布
// 门控 — 任何内容变更为未保存态，mock 自动保存 2s 后恢复已保存。
let saveTimer: number | null = null;

/* ── Batch 1032-④-B（C10）：**服务器快照** ────────────────────────────────
 *
 * 它表示「**服务器上的那份画布**」—— 是「保留并同步」与「丢弃修改」两枚按钮的
 * **共同基准**：
 *  · 「保留并同步」⇒ 把当前画布**存成**新快照（此后它就是服务器那份）；
 *  · 「丢弃修改」  ⇒ 把画布**退回**快照（离线期间的改动真的没了）。
 *
 * ⚠️ 为什么放**模块级**而不是 state：它不是 UI 状态，是「外部世界的那一份」。
 *   放 state 会被 `past` / `future` 的历史栈一起快照/回滚 ⇒ 语义会漂。
 */
let serverSnapshot: { nodes: JimengNode[]; edges: Edge[] } | null = null;

/* 离线期间的改动序号（不用时间戳 ⇒ 产物与门禁里不许出随机量）。 */
let offlineEditSeq = 0;

/* ── Batch 1032-④-B（C09）：**往生成历史里记一条** ───────────────────────
 *
 * ⚠️ 为什么是**模块级函数**而不是 store 里的一个 action：
 *   生成动作（`generateInto` 等）就在 store 的**对象字面量**里，
 *   而对象字面量内部**不能引用同级属性**（TS 会报 `Cannot find name`）。
 *   ⇒ ⇒ 所以把「怎么记」抽成模块级函数，由 action 转调。
 */
function pushGeneration(rec: Omit<JimengGenerationRecord, "id" | "seq">): void {
  useJimengStore.setState((state) => {
    const seq = state.generationHistory.length + 1;
    return {
      generationHistory: [
        ...state.generationHistory,
        { id: `gen-${seq}`, seq, ...rec },
      ],
    };
  });
}

/* ── Batch 1032-④-B（C05）：水印设置的**持久化** ─────────────────────────
 *
 * ⚠️ 为什么不用 zustand 的 `persist` 中间件：那是**整个 store** 的初始化路径，
 *   而本仓的 store 有一大堆**内存态**（任务、浮层槽位、播放态）——
 *   把它们一起持久化会把「这一轮对话的临时状态」写进磁盘 ⇒ 副作用远超本条整改。
 *   ⇒ ⇒ 所以只给**这一个**字段配一对读写函数。
 *
 * ⚠️ 三条硬要求（缺一条就会在别的环境下崩）：
 *   ① `typeof window` 判空 —— SSR / 静态导出时**没有 window**，
 *      而这段代码在**模块求值期**就会跑 ⇒ 不判空则 import 即崩；
 *   ② try/catch —— 隐私模式 / 配额满时 localStorage 会抛；
 *   ③ 初值**确定** —— 读不到就是 `false`，不许造出随机/时间相关的值
 *      （产物与门禁里不许出现随机量）。
 */
const WATERMARK_KEY = "jimeng-clone-watermark";

function readStoredWatermark(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return window.localStorage.getItem(WATERMARK_KEY) === "1";
  } catch {
    return false;
  }
}

function writeStoredWatermark(noWatermark: boolean): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(WATERMARK_KEY, noWatermark ? "1" : "0");
  } catch {
    /* 存不了就算了 —— 不能让「保存设置」这个动作把整个 store 弄崩。 */
  }
}

function markDirty(state: JimengCanvasState): {
  project: JimengCanvasState["project"];
  offlineEdits?: { id: string; label: string }[];
} {
  if (saveTimer !== null) window.clearTimeout(saveTimer);
  saveTimer = window.setTimeout(() => {
    saveTimer = null;
    useJimengStore.setState((s) =>
      s.project.saved ? s : { project: { ...s.project, saved: true } },
    );
  }, 2000);
  /* ⭐⭐⭐⭐⭐ Batch 1032-④-B（C10）：**离线期间的改动要被记下来** ——
   * 否则「保留并同步」与「丢弃修改」两枚按钮**没有任何东西可同步 / 可丢弃**
   * （此前它们只弹一句 toast，什么也没做）。 */
  if (state.offlineMode) {
    offlineEditSeq += 1;
    return {
      project: { ...state.project, saved: false },
      offlineEdits: [
        ...state.offlineEdits,
        { id: `offline-edit-${offlineEditSeq}`, label: "画布修改" },
      ],
    };
  }
  return { project: { ...state.project, saved: false } };
}

/** Batch 834：AI 会话 id 计数器（模块级，避免同毫秒撞号，见 appendAiMessage 注释） */
let aiSessionSeq = 0;
const nextAiSessionSeq = () => (aiSessionSeq += 1);

const initialNodes: JimengNode[] = [
  {
    id: "video-local-1",
    type: "video",
    position: { x: 675.6, y: 280.5 },
    data: {
      title: "sb_518102884867410fb...20260622155459-tf5q2",
      source: "local-upload",
      hasMedia: true,
      poster: MOCK_POSTER,
      /* ⭐⭐⭐ Batch 1032-④-B（C11）：**真的视频源** ——
         此前视频节点只有海报 + 模拟进度条 ⇒「视频节点能播放」那句是假的。 */
      src: DEMO_VIDEO_SRC,
      duration: 6,
      currentTime: 2,
      muted: true,
      /* 1032-⑫：音量初值 0.6（源站全屏音量滑杆 aria-valuenow 口径 0–1） */
      volume: 0.6,
      width: 569,
      height: 320,
    },
    selected: false,
  },
  {
    id: "video-empty-1",
    type: "video",
    position: { x: 1442.1, y: 323.2 },
    data: {
      title: "视频 1",
      source: "empty",
      hasMedia: false,
      width: 569,
      height: 320,
    },
    selected: false,
  },
  // ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **Batch 1031-④c：补上契约要求的另外三种节点类型**
  //   契约 `node_kinds` 是 `["文本", "时间线", "音频"]`，而此前初始 mock **只有 video**
  //   ⇒ 节点级契约（`全屏编辑` / `导出时间线` / `静音` / `替换媒体` / `添加素材到时间线`）
  //   永远量不到 ⇒ 探针 1031d 的 `P8` 只能记 `null`（「没测到」）⇒ 原型永远不被验到这一层。
  //   ⚠️ 下面的 `data` 形状**不是猜的**，逐条照本文件 `insertNode(kind)` 的既有分支抄：
  //   text `{title, text, width:368, height:368}` / timeline `{title, width:1200, height:207,
  //   duration:0, clips:[]}` / audio `{title, duration:15, width:368, height:368}`
  //   ⇒ mock 初始态与「点左栏插入」**同构** ⇒ 验的是同一条路径。
  {
    id: "text-1",
    type: "text",
    position: { x: 120.5, y: 160.2 },
    data: { title: "文本 1", text: "", width: 368, height: 368 },
    selected: false,
  },
  {
    id: "timeline-1",
    type: "timeline",
    // ⚠️⚠️⚠️ 104c 第一版写的是 x=110.8 ⇒ 渲染后节点左缘落在 x≈20，
    //   而左栏按钮在 x=16..56 ⇒ **这个节点有一部分压在左栏底下** ⇒
    //   它顶行右簇与静音按钮（源站实测 rect 就在 x=134 一带）被
    //   `rail-beta-badge` 挡住 ⇒ verifier 的 S.8（项目信息模态下
    //   「未确认」必须为 0）当场转红：by_layer=9 / 仍留未确认=2。
    //
    //   ⇒ 根因是**我随手写的坐标**，不是门：门量的是「这个状态有没有分好桶」。
    //   ⚠️ 而且这个红**长得像门的问题**（因为 S.8 自己都说
    //   「demo 画布逐轮动态插节点」），很容易顺手去把门的强度调松 ——
    //   那是 866 那次刚踩过的坑（「钉条数就是把易变量当契约」）。
    //
    //   ⇒ 改坐标而不是改门：源站 `source-canvas-census.json` 里
    //     `timeline-flow-node` rect = **121, 265, 1200×207**
    //     —— 源站的时间线节点**本来就不贴左缘**，是我这份 mock 贴太近了。
    position: { x: 240, y: 700.4 },
    data: { title: "时间线 1", width: 1200, height: 207, duration: 0, clips: [] },
    selected: false,
  },
  {
    id: "audio-1",
    type: "audio",
    position: { x: 1560.4, y: 180.6 },
    data: { title: "音频 1", duration: 15, width: 368, height: 368 },
    selected: false,
  },
];


// 批 528 SOURCE_FACT (用户手册 create-first-node 实测): 副本命名用「 (2)」后缀
const withCopyTitle = (data: Record<string, unknown>): Record<string, unknown> =>
  typeof data.title === "string"
    ? { ...data, title: `${data.title} (2)` }
    : data;

export const useJimengStore = create<JimengCanvasState>((set) => ({
  // ⚠️⭐⭐⭐⭐⭐ **这里原来有 `nodeCount: 2`，1031-④c 删掉了。**
  //   全仓无人读它 —— 顶栏用的是 `s.nodes.length + groups.size` 现算。
  //   而它硬编码成 `2`：**节点数一变它就是谎话**，谁哪天图省事改成读它，
  //   顶栏立刻开始撒谎（插三个节点它仍然显示 2）。
  //   ⇒ 「一个数字如果只是被**声明**在某处而没有从**源头**算出来，它就只是一段注释。」
  project: { name: "测试项目", saved: true },

  nodes: initialNodes,
  edges: [],

  selectedNodeId: null,

  zoomPercent: 73,

  groupColors: {},
  groupNames: {},

  onNodesChange: (changes) =>
    set((state) => {
      // Batch 56 重构: selected 标志完全交由 xyflow 内部管理 (marquee/
      // shift+click 天然支持多选)，store 仅镜像 selectedNodeId 供消费方。
      // 编组联动 (Batch 39): 拖拽编组内节点时，同组节点跟随相同位移。
      const expanded: NodeChange<JimengNode>[] = [...changes];
      const byId = new Map(state.nodes.map((n) => [n.id, n]));
      for (const c of changes) {
        if (c.type !== "position" || !c.position) continue;
        const srcNode = byId.get(c.id);
        const gid = srcNode?.groupId;
        if (!gid || !srcNode) continue;
        const dx = c.position.x - srcNode.position.x;
        const dy = c.position.y - srcNode.position.y;
        for (const other of state.nodes) {
          if (other.id === c.id || other.groupId !== gid) continue;
          if (expanded.some((e) => e.type === "position" && e.id === other.id))
            continue;
          expanded.push({
            id: other.id,
            type: "position",
            position: {
              x: other.position.x + dx,
              y: other.position.y + dy,
            },
            dragging: (c as { dragging?: boolean }).dragging,
          });
        }
      }
      const nodes = applyNodeChanges(expanded, state.nodes);
      const lastSelect = [...changes]
        .reverse()
        .find(
          (c): c is Extract<NodeChange<JimengNode>, { type: "select" }> =>
            c.type === "select",
        );
      const selectedNodeId = lastSelect
        ? lastSelect.selected
          ? lastSelect.id
          : state.selectedNodeId === lastSelect.id
            ? null
            : state.selectedNodeId
        : state.selectedNodeId;
      // Batch 66 (SOURCE_FACT): 画布有未保存变更时顶栏 保存中…，
      // 自动保存后 已保存；下载按钮被 导出前请保存画布 门控。
      const contentChanged = changes.some(
        (c) => c.type === "position" || c.type === "remove" || c.type === "add",
      );
      return {
        nodes,
        selectedNodeId,
        ...(contentChanged ? markDirty(state) : null),
      };
    }),

  onEdgesChange: (changes) =>
    set((state) => ({ edges: applyEdgeChanges(changes, state.edges) })),

  addEdge: (edge) =>
    set((state) => {
      // ⭐ 用 **React Flow 官方的 `addEdge`** 判重，不自己写一套
      //   ⇒ 官方遇到重复会**原样返回旧数组**（同一引用）⇒ 指针没变
      //   ⇒ ⇒ 重复边**不进历史栈**（否则「撤销」会撤掉一个不存在的动作）
      const next = addEdgeRf(edge, state.edges);
      if (next === state.edges) return {};
      return {
        ...markDirty(state),
        past: [...state.past, { nodes: state.nodes, edges: state.edges }],
        future: [],
        edges: next,
      };
    }),

  focusNodeRequest: null,

  requestFocusNode: (id) =>
    set((state) => ({
      focusNodeRequest: { id, nonce: (state.focusNodeRequest?.nonce ?? 0) + 1 },
    })),

  selectNode: (id) =>
    set((state) => ({
      selectedNodeId: id,
      nodes: state.nodes.map((n) => ({ ...n, selected: n.id === id })),
    })),

  setZoomPercent: (z) => set({ zoomPercent: Math.round(z) }),

  toast: null,

  pushToast: (text) => set({ toast: text }),

  clearToast: () => set({ toast: null }),

  genModel: "即梦 Seedance 2.0 VIP",

  setGenModel: (model) => set({ genModel: model }),

  generateInto: (id, prompt) => {
    // mock 生成：立即进入生成中，3s 后完成填充 mock 内容 (CLONE_DECISION)
    set((state) => ({
      ...markDirty(state),
      nodes: state.nodes.map((n) => {
        if (n.id !== id || n.type !== "video") return n;
        const vd = n.data as JimengVideoNodeData;
        return {
          ...n,
          data: { ...vd, generating: true, prompt },
        };
      }),
    }));
    /* ⭐⭐⭐ Batch 1032-④-B（C09）：**真的记一条生成历史** ——
     * 否则顶栏「生成历史」永远是那句写死的「暂无生成历史」。 */
    pushGeneration({ kind: "视频", title: "视频生成", prompt });
    window.setTimeout(() => {
      set((state) => ({
        ...markDirty(state),
        nodes: state.nodes.map((n) => {
          if (n.id !== id || n.type !== "video") return n;
          const vd = n.data as JimengVideoNodeData;
          return {
            ...n,
            data: {
              ...vd,
              generating: false,
              hasMedia: true,
              source: "generated",
              poster: MOCK_POSTER,
              /* ⭐⭐⭐ Batch 1032-④-B（C11）：生成出来的视频也有真源。 */
              src: DEMO_VIDEO_SRC,
              duration: 6,
              currentTime: 0,
              playing: false,
            },
          };
        }),
      }));
    }, 3000);
  },

  /* ⭐⭐⭐ Batch 1032-②b-2：图片生成 (CLONE_DECISION，与视频侧 generateInto 同构)。
     立即「生成中」→ 3s 后变成有画面的图片节点。 */
  generateImageInto: (id, prompt) => {
    set((state) => ({
      ...markDirty(state),
      nodes: state.nodes.map((n) => {
        if (n.id !== id || n.type !== "image") return n;
        const d = n.data as JimengImageNodeData;
        return { ...n, data: { ...d, generating: true, prompt } };
      }),
    }));
    /* ⭐⭐⭐ Batch 1032-④-B（C09）：记一条历史（同上）。 */
    pushGeneration({ kind: "图片", title: "图片生成", prompt });
    window.setTimeout(() => {
      set((state) => ({
        ...markDirty(state),
        nodes: state.nodes.map((n) => {
          if (n.id !== id || n.type !== "image") return n;
          const d = n.data as JimengImageNodeData;
          return {
            ...n,
            data: {
              ...d,
              generating: false,
              poster: MOCK_IMAGE,
              source: "generated",
            },
          };
        }),
      }));
    }, 3000);
  },

  /* ⭐⭐⭐ Batch 1032-②b-2：音频生成 (CLONE_DECISION)。
     与上面同构：立即「生成中」→ 3s 后完成 ⇒ 节点上出现时长徽标。 */
  generateAudioInto: (id, prompt) => {
    set((state) => ({
      ...markDirty(state),
      nodes: state.nodes.map((n) => {
        if (n.id !== id || n.type !== "audio") return n;
        const d = n.data as JimengAudioNodeData;
        return { ...n, data: { ...d, generating: true, prompt } };
      }),
    }));
    /* ⭐⭐⭐ Batch 1032-④-B（C09）：记一条历史（同上）。 */
    pushGeneration({ kind: "音频", title: "音频生成", prompt });
    window.setTimeout(() => {
      set((state) => ({
        ...markDirty(state),
        nodes: state.nodes.map((n) => {
          if (n.id !== id || n.type !== "audio") return n;
          const d = n.data as JimengAudioNodeData;
          return {
            ...n,
            data: { ...d, generating: false, duration: 12, source: "generated" },
          };
        }),
      }));
    }, 3000);
  },

  addVideoNodeAfter: (sourceId) =>
    set((state) => {
      const src = state.nodes.find((n) => n.id === sourceId);
      if (!src) return state;
      const id = `video-${Date.now()}`;
      const node: JimengNode = {
        id,
        type: "video",
        position: {
          x: src.position.x + (src.data.width ?? 569) + 160,
          y: src.position.y + 44,
        },
        data: {
          title: `视频 ${state.nodes.filter((n) => n.type === "video").length + 1}`,
          source: "empty",
          hasMedia: false,
          width: 569,
          height: 320,
        },
        selected: false,
      };
      return {
        ...markDirty(state),
        past: [
          ...state.past,
          { nodes: state.nodes, edges: state.edges },
        ],
        future: [],
        nodes: [...state.nodes, node],
        edges: [
          ...state.edges,
          {
            id: `e-${sourceId}-${id}`,
            source: sourceId,
            target: id,
            // ⭐⭐ Batch 1032-②a: **handle 口径归一化** ——
            //   官方 `addEdge` 的判重条件含 `sourceHandle`/`targetHandle` 相等
            //   ⇒ 若这条边是 `undefined` 而用户拖出来的是 `null`，
            //   ⇒ ⇒ `undefined === null` 为 false ⇒ ⇒ **判重失效** ⇒ ⇒ 能连出重复边
            //   ⇒ ⇒ ⇒ ⇒ 所以这里显式写成 `null`，与 `onConnect` 建的那条同口径。
            sourceHandle: null,
            targetHandle: null,
          },
        ],
      };
    }),

  removeNode: (id) =>
    set((state) => ({
      ...markDirty(state),
      past: [...state.past, { nodes: state.nodes, edges: state.edges }],
      future: [],
      nodes: state.nodes.filter((n) => n.id !== id),
      edges: state.edges.filter((e) => e.source !== id && e.target !== id),
      selectedNodeId: state.selectedNodeId === id ? null : state.selectedNodeId,
    })),

  // 截取帧 首帧/尾帧 (Batch 62): 源站点击下拉项后直接异步产出带画面的
  // image 节点 (62-first-frame-result / 62-multiselect 截图证据)，不打开
  // 帧选择器 (选择器仅 自定义 使用)。落点为源节点右侧 80 间距，与现有
  // 节点重叠时继续右移避让 (源站实测落点即避让后的空位)。
  captureFrame: (sourceId, frame, atTime) =>
    set((state) => {
      const src = state.nodes.find((n) => n.id === sourceId);
      if (!src || src.type !== "video") return state;
      const v = src.data as JimengVideoNodeData;
      if (!v.hasMedia) return state;
      const w = v.width ?? 569;
      const h = v.height ?? 320;
      const rowOverlap = (n: (typeof state.nodes)[number], x: number) =>
        x < n.position.x + (n.data.width ?? 569) &&
        x + w > n.position.x &&
        src.position.y < n.position.y + (n.data.height ?? 320) &&
        src.position.y + h > n.position.y;
      let x = src.position.x + w + 80;
      for (let guard = 0; guard < state.nodes.length + 1; guard += 1) {
        const blocker = state.nodes.find((n) => rowOverlap(n, x));
        if (!blocker) break;
        x = blocker.position.x + (blocker.data.width ?? 569) + 80;
      }
      // 批 204 SOURCE_FACT: 自定义帧产出标题「{视频}_截帧_{N}」(aria
      // 「图片 node: sb_...-tf5q2_截帧_1」)；N 为计数器，重复截取递增
      // (源站计数口径未采样，mock 按「同源已有截帧节点数 + 1」)
      const customIndex =
        frame === "custom"
          ? state.nodes.filter(
              (n) =>
                n.type === "image" &&
                ((n.data as JimengImageNodeData).title ?? "").startsWith(
                  `${v.title}_截帧_`,
                ),
            ).length + 1
          : null;
      const label =
        frame === "first"
          ? "首帧"
          : frame === "last"
            ? "尾帧"
            : `截帧_${customIndex}`;
      const id = `image-${Date.now()}`;
      /* ⭐⭐⭐ Batch 1032-④-B（C06）：**选中的那一帧的时间码**。
       * `atTime` 是用户真的选中的位置 ⇒ ⇒ 它必须被**用起来**，而不是丢掉：
       *  ① 写进产出节点的 `frameTime`（可被读回核对）；
       *  ② 源节点的播放头**真的移到那一帧**（`currentTime`）。
       * 首帧/尾帧没传时间码 ⇒ 按语义补上（0 / duration）。 */
      const resolvedTime =
        typeof atTime === "number" && Number.isFinite(atTime)
          ? Math.max(0, atTime)
          : frame === "first"
            ? 0
            : frame === "last"
              ? (v.duration ?? 0)
              : (v.currentTime ?? 0);
      const node: JimengNode = {
        id,
        type: "image",
        position: { x, y: src.position.y },
        data: {
          // 批 195 SOURCE_FACT: 源站产出节点标题为「{视频标题}_{首帧|尾帧}」
          // (下划线连接, aria-label 「图片 node: sb_...-tf5q2_」)
          title: `${v.title}_${label}`,
          poster: v.poster,
          width: w,
          height: h,
          // ⭐⭐⭐ 那一帧的时间码（C06）
          frameTime: resolvedTime,
          // 批 197 SOURCE_FACT: 产出瞬间为「正在上传图片 0%」瞬态
          uploadProgress: 0,
        },
        selected: false,
      };
      // 批 197: mock 上传进度 (源站 1-2s 内完成)。直接 setState,
      // 不再走 markDirty (进度变化不产生新的脏态/撤销步)。
      const advance = (progress: number) =>
        useJimengStore.setState((cur) => ({
          nodes: cur.nodes.map((n) =>
            n.id === id
              ? {
                  ...n,
                  data: { ...(n.data as JimengImageNodeData), uploadProgress: progress },
                }
              : n,
          ),
        }));
      window.setTimeout(() => advance(46), 500);
      window.setTimeout(() => advance(100), 1000);
      // 上传态消隐由组件侧以 uploadProgress < 100 判定 (100 = 完成)
      // CLONE_DECISION (批 417 评估, 406 留档): 源站存在上传失败态
      // (「重试上传」「图片上传失败」+ 重试钮，406-image-toolbar.png)，
      // 但该态仅在真实网络失败时出现；clone 本地上传 mock 恒成功，
      // 不建模失败路径 (失败态 UI 证据已留档，如需可后续扩展
      // uploadProgress = -1 语义)。
      return {
        ...markDirty(state),
        past: [...state.past, { nodes: state.nodes, edges: state.edges }],
        future: [],
        /* ⭐⭐⭐ Batch 1032-④-B（C06）：**源节点的播放头真的移到那一帧** ——
         * 否则「选中的那一帧」在源视频上**看不出来**（用户无从确认自己选了哪帧）。 */
        nodes: [
          ...state.nodes.map((n) =>
            n.id === sourceId
              ? {
                  ...n,
                  data: {
                    ...(n.data as JimengVideoNodeData),
                    currentTime: resolvedTime,
                  },
                }
              : n,
          ),
          node,
        ],
        edges: [
          ...state.edges,
          { id: `e-${sourceId}-${id}`, source: sourceId, target: id },
        ],
      };
    }),

  // 本地上传 (Batch 73): 文件名即节点标题 (源站上传节点标题为
  // sb_... 文件名形态)，mock 海报 + 6s 时长
  addLocalUpload: (name, position) =>
    set((state) => {
      const id = `video-${Date.now()}`;
      const node: JimengNode = {
        id,
        type: "video",
        position,
        data: {
          title: name,
          source: "local-upload",
          hasMedia: true,
          poster: MOCK_POSTER,
          duration: 6,
          currentTime: 0,
          muted: true,
          width: 569,
          height: 320,
        },
        selected: false,
      };
      return {
        ...markDirty(state),
        past: [...state.past, { nodes: state.nodes, edges: state.edges }],
        future: [],
        nodes: [...state.nodes, node],
      };
    }),

  // Batch 832: 本地图片入库（资产栏拖放 / 「导入」共用）
  // ⚠️ id 不能用 Date.now() 单键：一次拖入多张时同毫秒会撞号，
  // React 会把两个 key 相同的节点当成同一个，表现为「只进了一张」。
  // 批 825 已经在 `nextClipId` 上踩过同族问题，这里跟着走。
  addLocalImage: (name, dataUrl, position) =>
    set((state) => {
      const seq = state.nodes.filter((n) => n.type === "image").length + 1;
      const id = `image-local-${seq}-${state.nodes.length}`;
      const node: JimengNode = {
        id,
        type: "image",
        position,
        data: {
          title: name,
          poster: dataUrl,
          width: 320,
          height: 320,
        },
        selected: false,
      };
      return {
        ...markDirty(state),
        past: [...state.past, { nodes: state.nodes, edges: state.edges }],
        future: [],
        nodes: [...state.nodes, node],
      };
    }),

  // 布局-智能布局 (Batch 63; 前 batch 62 自动排列): 选中节点按 x 排序后
  // 排成一行 (y 对齐选区最小值，间距 80)
  arrangeSelected: () =>
    set((state) => {
      const sel = state.nodes.filter((n) => n.selected);
      if (sel.length < 2) return state;
      const minY = Math.min(...sel.map((n) => n.position.y));
      const ordered = [...sel].sort((a, b) => a.position.x - b.position.x);
      const positions = new Map<string, { x: number; y: number }>();
      let cursor = Math.min(...ordered.map((n) => n.position.x));
      for (const n of ordered) {
        positions.set(n.id, { x: cursor, y: minY });
        cursor += (n.data.width ?? 569) + 80;
      }
      return {
        ...markDirty(state),
        past: [...state.past, { nodes: state.nodes, edges: state.edges }],
        future: [],
        nodes: state.nodes.map((n) => ({
          ...n,
          position: positions.get(n.id) ?? n.position,
        })),
      };
    }),

  // 布局-宫格布局 (Batch 63, SOURCE_FACT 菜单项 / CLONE_DECISION 排列语义):
  // 按 x 排序后填充 ceil(√n) 列网格 (行内 y 对齐、列距 80、行距 80)
  arrangeSelectedGrid: () =>
    set((state) => {
      const sel = state.nodes.filter((n) => n.selected);
      if (sel.length < 2) return state;
      const minX = Math.min(...sel.map((n) => n.position.x));
      const minY = Math.min(...sel.map((n) => n.position.y));
      const ordered = [...sel].sort((a, b) => a.position.x - b.position.x);
      const cols = Math.ceil(Math.sqrt(ordered.length));
      const positions = new Map<string, { x: number; y: number }>();
      ordered.forEach((n, i) => {
        const col = i % cols;
        const row = Math.floor(i / cols);
        positions.set(n.id, {
          x: minX + col * ((n.data.width ?? 569) + 80),
          y: minY + row * ((n.data.height ?? 320) + 80),
        });
      });
      return {
        ...markDirty(state),
        past: [...state.past, { nodes: state.nodes, edges: state.edges }],
        future: [],
        nodes: state.nodes.map((n) => ({
          ...n,
          position: positions.get(n.id) ?? n.position,
        })),
      };
    }),

  // 批量删除选中节点 (Batch 38 多选深化)，单条历史记录
  removeNodes: (ids) =>
    set((state) => {
      if (!ids.length) return state;
      return {
        ...markDirty(state),
        past: [...state.past, { nodes: state.nodes, edges: state.edges }],
        future: [],
        nodes: state.nodes.filter((n) => !ids.includes(n.id)),
        edges: state.edges.filter(
          (e) => !ids.includes(e.source) && !ids.includes(e.target),
        ),
        selectedNodeId: null,
      };
    }),



  duplicateNode: (id) =>
    set((state) => {
      const src = state.nodes.find((n) => n.id === id);
      if (!src) return state;
      const copy: JimengNode = {
        ...src,
        id: `video-${Date.now()}`,
        selected: false,
        position: { x: src.position.x + 60, y: src.position.y + 60 },
        data: withCopyTitle(src.data) as typeof src.data,
      };
      return {
        ...markDirty(state),
        past: [...state.past, { nodes: state.nodes, edges: state.edges }],
        future: [],
        nodes: [...state.nodes, copy],
      };
    }),

  clipboard: null,

  copyNode: (id) => {
    const src = useJimengStore.getState().nodes.find((n) => n.id === id);
    if (!src) return;
    useJimengStore.setState({
      clipboard: { nodes: [src], edges: [] },
    });
  },

  copyNodes: (ids) => {
    const state = useJimengStore.getState();
    const nodes = state.nodes.filter((n) => ids.includes(n.id));
    if (!nodes.length) return;
    const idSet = new Set(nodes.map((n) => n.id));
    const edges = state.edges.filter(
      (e) => idSet.has(e.source) && idSet.has(e.target),
    );
    useJimengStore.setState({ clipboard: { nodes, edges } });
  },

  pasteNodes: () => {
    const clip = useJimengStore.getState().clipboard;
    if (!clip || !clip.nodes.length) return;
    const state = useJimengStore.getState();
    const idMap = new Map(clip.nodes.map((n) => [n.id, `${n.type}-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`]));
    const offsetX = 60;
    const offsetY = 60;
    const newNodes = clip.nodes.map((n) => ({
      ...n,
      id: idMap.get(n.id)!,
      selected: false,
      position: { x: n.position.x + offsetX, y: n.position.y + offsetY },
      data: withCopyTitle(n.data) as typeof n.data,
    }));
    const newEdges = clip.edges.map((e) => ({
      ...e,
      id: `e-${idMap.get(e.source)}-${idMap.get(e.target)}`,
      source: idMap.get(e.source)!,
      target: idMap.get(e.target)!,
    }));
    useJimengStore.setState({
      ...markDirty(state),
      past: [...state.past, { nodes: state.nodes, edges: state.edges }],
      future: [],
      nodes: [...state.nodes, ...newNodes],
      edges: [...state.edges, ...newEdges],
    });
  },

  past: [],
  future: [],

  undo: () =>
    set((state) => {
      const prev = state.past[state.past.length - 1];
      if (!prev) return state;
      return {
        past: state.past.slice(0, -1),
        future: [
          { nodes: state.nodes, edges: state.edges },
          ...state.future,
        ],
        nodes: prev.nodes,
        edges: prev.edges,
      };
    }),

  redo: () =>
    set((state) => {
      const next = state.future[0];
      if (!next) return state;
      return {
        past: [
          ...state.past,
          { nodes: state.nodes, edges: state.edges },
        ],
        future: state.future.slice(1),
        nodes: next.nodes,
        edges: next.edges,
      };
    }),

  repaintNodeId: null,

  enterRepaint: (id) => set({ repaintNodeId: id }),

  exitRepaint: () => set({ repaintNodeId: null }),

  editNodeId: null,

  enterEdit: (id) => set({ editNodeId: id }),

  exitEdit: () => set({ editNodeId: null }),

  inferNodeId: null,

  enterInfer: (id) => set({ inferNodeId: id }),

  exitInfer: () => set({ inferNodeId: null }),

  framePickerNodeId: null,
  framePickerMode: "custom",

  enterFramePicker: (id, mode = "custom") =>
    set({ framePickerNodeId: id, framePickerMode: mode }),

  exitFramePicker: () => set({ framePickerNodeId: null }),

  trimNodeId: null,

  enterTrim: (id) => set({ trimNodeId: id }),

  exitTrim: () => set({ trimNodeId: null }),

  tasks: [],

  /* ⭐⭐⭐ Batch 1032-④-B（C09）：生成历史（真的任务列表）。 */
  generationHistory: [],

  pushGeneration: (rec) => pushGeneration(rec),

  startTask: (nodeId, kind) => {
    const id = `task-${Date.now()}`;
    set((state) => ({
      tasks: [
        ...state.tasks,
        { id, nodeId, kind },
      ],
      // mock 任务提交同步 toast 反馈 (Batch 11/40)
      toast: FEEDBACK.taskSubmitted(
        kind === "upscale" ? "智能超清" : kind === "motion-capture" ? "深度动作捕捉" : "补帧",
      ),
    }));
    // mock 生命周期 (Batch 53)：4s 后自动完成并清除任务
    window.setTimeout(() => {
      useJimengStore.setState((state) => ({
        tasks: state.tasks.filter((t) => t.id !== id),
      }));
    }, 4000);
  },

  // Batch 797 SOURCE_FACT (2026-10-01 登录态实测 + 点击「与 AI 对话」对照):
  // 源站 Agent 面板**默认收起**，画布右下只暴露一个 118×34 / r20 的
  // 「与 AI 对话」触发钮；点击后才展开 @[1268,12] 400×802 面板，并出现
  // 新建会话/收起/使用技能/引用参考/发送消息 五类控件。
  // 此前「默认展开」是批 398 的约定，但源站取样从未出现过展开态，且默认展开
  // 会把顶栏「分享」挤成竖排、并遮住顶栏右簇（台账待决问题 #2）。
  // 该待决问题至此以源站事实关闭：默认收起。
  // 「Escape 不关闭面板」是 381 的独立契约，与默认态无关，仍然成立。
  aiDrawerOpen: false,

  aiDrawerPrefill: null,

  aiDrawerRefChip: null,

  setAiDrawerOpen: (open) =>
    set((state) => ({
      aiDrawerOpen: open,
      aiDrawerPrefill: open ? state.aiDrawerPrefill : null,
      aiDrawerRefChip: open ? state.aiDrawerRefChip : null,
      // ⚠️⚠️ 批 938 SOURCE_FACT：源站的侧栏与瞬时浮层**不对称** ——
      //    开侧栏**会**把瞬时浮层收掉（实测：`生成历史→侧栏`、`右键菜单→侧栏`
      //    两个方向的 A 都没了），**反过来不会**。
      //    ⇒ 只在**开**的时候清槽位；关侧栏不该动任何瞬时浮层。
      // ⚠️ 反方向**故意不做**：开搜索/缩放/右键**不关**侧栏。
      transientLayer: open ? null : state.transientLayer,
    })),

  openAiDrawer: (prefill, refChip) =>
    // ⚠️ 这里**无条件**清槽位：开侧栏收掉瞬时浮层是实测事实（937），
    //    而这一路不需要读旧 state（侧栏的预填/chip 是**整体替换**不是保留）。
    set({
      aiDrawerOpen: true,
      aiDrawerPrefill: prefill ?? null,
      aiDrawerRefChip: refChip ?? null,
      transientLayer: null,
    }),

  aiDrawerDraft: "",

  setAiDrawerDraft: (draft) => set({ aiDrawerDraft: draft }),

  // ── 批 938：瞬时浮层的互斥槽位（源站实测 24/24，见类型上的说明）────────
  transientLayer: null,

  openTransientLayer: (id) =>
    set((state) => ({
      // ⭐ **同 id 再开 = 关**（源站的 toggle 语义）：先比再赋值，
      //    顺序反了就会变成「点了永远关不掉」。
      transientLayer: state.transientLayer === id ? null : id,
    })),

  closeTransientLayer: (id) =>
    set((state) => (id && state.transientLayer !== id
      ? state                                     // 不是它就**别动**别人的
      : { transientLayer: null })),

  // ── Batch 834：真会话模型 ────────────────────────────────────────────
  // ⚠️ 会话 id 用**模块级计数器**而不是 Date.now()：同毫秒连发两条会撞号，
  // 后一条覆盖前一条，表现为「新建了会话但列表没变多」。批 832 在
  // addLocalImage 上踩过同族问题，这里一开始就避开。
  aiSessions: [],
  aiActiveSessionId: null,

  appendAiMessage: (role, text) =>
    set((state) => {
      const id = state.aiActiveSessionId ?? `ai-session-${nextAiSessionSeq()}`;
      const idx = state.aiSessions.findIndex((s) => s.id === id);
      const base =
        idx >= 0
          ? state.aiSessions[idx]
          : { id, title: "新会话", messages: [] as AiSession["messages"] };
      const updated: AiSession = {
        ...base,
        // 标题取**首条用户消息**（不是最后一条，也不是 agent 回复）
        title:
          base.messages.length === 0 && role === "user"
            ? text.slice(0, 24)
            : base.title,
        messages: [...base.messages, { role, text }],
      };
      const sessions =
        idx >= 0
          ? state.aiSessions.map((s) => (s.id === id ? updated : s))
          : [...state.aiSessions, updated];
      return { aiSessions: sessions, aiActiveSessionId: id };
    }),

  newAiSession: () =>
    set((state) => {
      const id = `ai-session-${nextAiSessionSeq()}`;
      // ⚠️ 追加而不是替换：源站的「新建会话」是开一条新的，旧的仍在列表里。
      // 此前复刻写的是 `setMessages([])` —— 那是**销毁**，不是新建。
      return {
        aiSessions: [...state.aiSessions, { id, title: "新会话", messages: [] }],
        aiActiveSessionId: id,
      };
    }),

  selectAiSession: (id) =>
    set((state) =>
      state.aiSessions.some((s) => s.id === id) ? { aiActiveSessionId: id } : {},
    ),

  assetsOpen: false,

  setAssetsOpen: (open) => set({ assetsOpen: open }),
  // Batch 793: 从画布选择点选模式 (面板发起, workspace 拦截节点点击)
  refPicking: false,
  pickedRefNodeId: null,
  startRefPicking: () => set({ refPicking: true, pickedRefNodeId: null }),
  cancelRefPicking: () => set({ refPicking: false, pickedRefNodeId: null }),
  pickRefNode: (id) => set({ refPicking: false, pickedRefNodeId: id }),
  clearPickedRefNode: () => set({ pickedRefNodeId: null }),

  // Batch 1032-②b-3: @ 提及面板开关（Esc 分级退出的依据）
  mentionPanelOpen: false,
  setMentionPanelOpen: (open) => set({ mentionPanelOpen: open }),

  // Batch 1032-②b-4: 「已展开的生成器」浮层（Esc 分级退出的**最上层**）
  expandedGenLayer: null,
  openExpandedGenLayer: (kind, nodeId) => set({ expandedGenLayer: { kind, nodeId } }),
  closeExpandedGenLayer: () => set({ expandedGenLayer: null }),

  offlineDialogOpen: false,

  setOfflineDialog: (open) => set({ offlineDialogOpen: open }),

  /* ⭐⭐⭐⭐⭐ Batch 1032-④-B（C10）：离线态与两枚**真动作**。
   *
   * ⚠️ 「服务器快照」用**模块级**变量存（不是 state）⇒ 因为它要表达
   *   「**服务器上的那份**」—— 它是同步动作的**基准**，不是 UI 状态。
   *   初值 = 画布的初态 ⇒ 「丢弃」会退回到「还没改过」的样子。
   */
  offlineMode: false,

  offlineEdits: [],

  setOfflineMode: (on) => set({ offlineMode: on }),

  syncOfflineEdits: () =>
    set((state) => {
      /* 真的把当前画布**存成新的服务器快照** ⇒ 「同步了」有状态变化。 */
      serverSnapshot = { nodes: state.nodes, edges: state.edges };
      return { offlineEdits: [], offlineDialogOpen: false };
    }),

  discardOfflineEdits: () =>
    set(() => ({
      /* 真的把画布**退回服务器快照** ⇒ 「丢弃了」看得到画布变了。
       * ⚠️ 快照可能还是 `null`（一次都没同步过）⇒ ⇒ 退回**画布初态**。 */
      nodes: serverSnapshot ? serverSnapshot.nodes : initialNodes,
      edges: serverSnapshot ? serverSnapshot.edges : [],
      offlineEdits: [],
      offlineDialogOpen: false,
    })),

  minimapOpen: false,

  setMinimapOpen: (open) => set({ minimapOpen: open }),

  edgesVisible: true,

  setEdgesVisible: (visible) => set({ edgesVisible: visible }),

  renameProject: (name) =>
    set((state) => ({
      ...markDirty(state),
      project: { ...state.project, name },
    })),

  /* ⭐⭐⭐ Batch 1032-④-B（C02）：真建项目。
   * ⚠️ `id` 用**计数器**（`p2`、`p3`…）而不是 `Date.now()` ⇒ 列表是确定的、
   *   可被门禁逐条核对（且 `project.name` 不会被写成随机串）。 */
  projects: [
    { id: "p1", name: "测试项目" },
    { id: "p2", name: "未命名项目" },
  ],

  createProject: (name) =>
    set((state) => {
      const id = `p${state.projects.length + 1}`;
      const label = name ?? `画布项目 ${state.projects.length + 1}`;
      return {
        ...markDirty(state),
        projects: [...state.projects, { id, name: label }],
        project: { ...state.project, name: label },
      };
    }),

  switchProject: (id) =>
    set((state) => {
      const target = state.projects.find((p) => p.id === id);
      if (!target) return state;
      return {
        ...markDirty(state),
        project: { ...state.project, name: target.name },
      };
    }),

  /* ⭐⭐⭐ Batch 1032-④-B（C05）：水印设置**真的存下来**。
   * ⚠️ 持久化走 localStorage，但**必须**：
   *   ① 判 `typeof window`（SSR 下没有 window ⇒ 崩在 import 阶段）；
   *   ② try/catch（隐私模式 / 配额满会抛 ⇒ 不能让整个 store 初始化失败）；
   *   ③ **初值是确定性的**（读不到就是 `false`）⇒ 产物/门禁里不许出随机量。 */
  watermark: { noWatermark: readStoredWatermark() },

  setWatermark: (noWatermark) => {
    writeStoredWatermark(noWatermark);
    set({ watermark: { noWatermark } });
  },

  toolActive: "select",

  setToolActive: (tool) => set({ toolActive: tool }),
  toggleToolActive: () =>
    set((state) => ({ toolActive: state.toolActive === "select" ? "move" : "select" })),

  togglePlay: (id) =>
    set((state) => ({
      nodes: state.nodes.map((n) => {
        if (n.id !== id || n.type !== "video") return n;
        const vd = n.data as JimengVideoNodeData;
        // 播放到结尾后再点播放 = 从头重播 (控件语义完善, Batch 32)；0.05s 容差
        const atEnd =
          (vd.duration ?? 0) > 0 &&
          (vd.currentTime ?? 0) >= vd.duration! - 0.05;
        return {
          ...n,
          data: {
            ...vd,
            playing: !(vd.playing ?? false),
            ...(atEnd && !(vd.playing ?? false)
              ? { currentTime: 0, playing: true }
              : null),
          },
        };
      }),
    })),

  // 双击视频卡片 = 从头重播 (SOURCE_FACT batch 24)
  restartPlay: (id) =>    set((state) => ({
      nodes: state.nodes.map((n) => {
        if (n.id !== id || n.type !== "video") return n;
        const vd = n.data as JimengVideoNodeData;
        if (!vd.hasMedia) return n;
        return {
          ...n,
          data: { ...vd, currentTime: 0, playing: true },
        };
      }),
    })),

  toggleMute: (id) =>
    set((state) => ({
      nodes: state.nodes.map((n) => {
        if (n.id !== id || n.type !== "video") return n;
        const vd = n.data as JimengVideoNodeData;
        return { ...n, data: { ...vd, muted: !(vd.muted ?? true) } };
      }),
    })),

  // 音量 (1032-⑫)：钳到 [0,1] ⇒ ⇒ 越界值不可能进 store。
  setVolume: (id, volume) =>
    set((state) => ({
      nodes: state.nodes.map((n) => {
        if (n.id !== id || n.type !== "video") return n;
        const vd = n.data as JimengVideoNodeData;
        const v = Math.min(1, Math.max(0, volume));
        return { ...n, data: { ...vd, volume: v } };
      }),
    })),

  // 媒体失效态 (Batch 67): 不脏化画布 (非文档内容)
  setMediaError: (id, error) =>
    set((state) => ({
      nodes: state.nodes.map((n) => {
        if (n.id !== id || n.type !== "video") return n;
        const vd = n.data as JimengVideoNodeData;
        return { ...n, data: { ...vd, mediaError: error } };
      }),
    })),

  groupSelected: () =>
    set((state) => {
      const ids = state.nodes.filter((n) => n.selected).map((n) => n.id);
      if (ids.length < 2) return state;
      const gid = `group-${Date.now()}`;
      // Batch 63 (SOURCE_FACT): 源站编组生成「编组 N」标题卡片
      const seq = Object.keys(state.groupNames).length + 1;
      return {
        ...markDirty(state),
        nodes: state.nodes.map((n) =>
          ids.includes(n.id) ? { ...n, groupId: gid } : n,
        ),
        groupNames: { ...state.groupNames, [gid]: `编组 ${seq}` },
      };
    }),

  ungroupSelected: () =>
    // CLONE_DECISION: 清除画布上全部编组（源站语义为取消选中组的编组）
    set((state) => ({
      ...markDirty(state),
      nodes: state.nodes.map((n) =>
        n.groupId ? { ...n, groupId: undefined } : n,
      ),
    })),

  // 组背景色 (Batch 63): color=null 表示 无颜色
  setGroupColor: (groupId, color) =>
    set((state) => {
      const next = { ...state.groupColors };
      if (color === null) delete next[groupId];
      else next[groupId] = color;
      return { ...markDirty(state), groupColors: next };
    }),

  selectAll: () =>
    set((state) => ({
      nodes: state.nodes.map((n) => ({ ...n, selected: true })),
      selectedNodeId: null,
    })),

  previewNodeId: null,

  openPreview: (id) => set({ previewNodeId: id }),

  closePreview: () => set({ previewNodeId: null }),

  seek: (id, fraction) =>
    set((state) => ({
      nodes: state.nodes.map((n) => {
        if (n.id !== id || n.type !== "video") return n;
        const vd = n.data as JimengVideoNodeData;
        return {
          ...n,
          data: {
            ...vd,
            currentTime: Math.min(1, Math.max(0, fraction)) * (vd.duration ?? 0),
          },
        };
      }),
    })),

  applyTrim: (id, trimmedDuration, startOffset = 0) =>
    set((state) => ({
      ...markDirty(state),
      past: [...state.past, { nodes: state.nodes, edges: state.edges }],
      future: [],
      nodes: state.nodes.map((n) => {
        if (n.id !== id || n.type !== "video") return n;
        const vd = n.data as JimengVideoNodeData;
        return {
          ...n,
          data: {
            ...vd,
            duration: Math.max(0.1, trimmedDuration),
            currentTime: startOffset,
            playing: false,
          },
        };
      }),
    })),

  updateNodeData: (id, patch) =>
    set((state) => ({
      ...markDirty(state),
      nodes: state.nodes.map((n) => {
        if (n.id !== id) return n;
        return { ...n, data: { ...n.data, ...patch } };
      }),
    })),

  updateNodeDataUndoable: (id, patch) =>
    set((state) => ({
      ...markDirty(state),
      past: [...state.past, { nodes: state.nodes, edges: state.edges }],
      future: [],
      nodes: state.nodes.map((n) => {
        if (n.id !== id) return n;
        return { ...n, data: { ...n.data, ...patch } };
      }),
    })),

  // 节点重命名 (Batch 87, SOURCE_FACT: 源站标题行即 Rename 按钮，
  // ⌘Z 可撤销) — 单条历史
  renameNode: (id, title) =>
    set((state) => ({
      ...markDirty(state),
      past: [...state.past, { nodes: state.nodes, edges: state.edges }],
      future: [],
      nodes: state.nodes.map((n) => {
        if (n.id !== id) return n;
        return { ...n, data: { ...n.data, title } };
      }),
    })),

  tickPlay: (id, delta) =>
    set((state) => ({
      nodes: state.nodes.map((n) => {
        const vd = n.data as JimengVideoNodeData;
        if (n.id !== id || !(vd.playing ?? false)) return n;
        const dur = vd.duration ?? 0;
        const cur = (vd.currentTime ?? 0) + delta;
        if (dur > 0 && cur >= dur) {
          return { ...n, data: { ...vd, currentTime: dur, playing: false } };
        }
        return { ...n, data: { ...vd, currentTime: cur } };
      }),
    })),

  addNodeAt: (kind, position) =>
    set((state) => {
      const id = `${kind}-${Date.now()}`;
      const seq = state.nodes.filter((n) => n.type === kind).length + 1;
      // 批 236 SOURCE_FACT: 源站插入的节点立即处于选中态
      const base = {
        id,
        position,
        selected: true,
      } as const;
      if (kind === "video") {
        return {
          ...markDirty(state),
          past: [...state.past, { nodes: state.nodes, edges: state.edges }],
          future: [],
          // ⭐⭐⭐ Batch 1032-②b-4 修掉的**真缺陷**：此前 `addNodeAt`
          // 只把新节点设成 `selected: true`，**没有取消旧节点的选中态**
          // ⇒ ⇒ 插入后 store 里**有两个** selected
          // ⇒ ⇒ `soloSelected`（selected 数量 === 1）变成 false
          // ⇒ ⇒ 按 SOURCE_FACT 批 62（多选时不显示生成面板）
          // ⇒ ⇒ **任何节点都不显示生成面板/工具条** ⇒ 新插的节点等于废掉。
          // ⇒ ⇒ 同时补上 `selectedNodeId`：否则 ⌘C/⌘D/Delete 仍作用在**旧**节点上。
          selectedNodeId: id,
          nodes: [
            // ⭐⭐⭐ 取消旧节点的选中态（详见上面 `selectedNodeId` 处的说明）
            ...state.nodes.map((n) => (n.selected ? { ...n, selected: false } : n)),
            {
              ...base,
              type: "video" as const,
              data: {
                title: `视频 ${seq}`,
                source: "empty" as const,
                hasMedia: false,
                width: 569,
                height: 320,
              },
            },
          ],
        };
      }
      if (kind === "image") {
        return {
          ...markDirty(state),
          past: [...state.past, { nodes: state.nodes, edges: state.edges }],
          future: [],
          // ⭐⭐⭐ Batch 1032-②b-4 修掉的**真缺陷**：此前 `addNodeAt`
          // 只把新节点设成 `selected: true`，**没有取消旧节点的选中态**
          // ⇒ ⇒ 插入后 store 里**有两个** selected
          // ⇒ ⇒ `soloSelected`（selected 数量 === 1）变成 false
          // ⇒ ⇒ 按 SOURCE_FACT 批 62（多选时不显示生成面板）
          // ⇒ ⇒ **任何节点都不显示生成面板/工具条** ⇒ 新插的节点等于废掉。
          // ⇒ ⇒ 同时补上 `selectedNodeId`：否则 ⌘C/⌘D/Delete 仍作用在**旧**节点上。
          selectedNodeId: id,
          nodes: [
            // ⭐⭐⭐ 取消旧节点的选中态（详见上面 `selectedNodeId` 处的说明）
            ...state.nodes.map((n) => (n.selected ? { ...n, selected: false } : n)),
            {
              ...base,
              type: "image" as const,
              data: { title: `图片 ${seq}`, width: 320, height: 320 },
            },
          ],
        };
      }
      if (kind === "audio") {
        return {
          ...markDirty(state),
          past: [...state.past, { nodes: state.nodes, edges: state.edges }],
          future: [],
          // ⭐⭐⭐ Batch 1032-②b-4 修掉的**真缺陷**：此前 `addNodeAt`
          // 只把新节点设成 `selected: true`，**没有取消旧节点的选中态**
          // ⇒ ⇒ 插入后 store 里**有两个** selected
          // ⇒ ⇒ `soloSelected`（selected 数量 === 1）变成 false
          // ⇒ ⇒ 按 SOURCE_FACT 批 62（多选时不显示生成面板）
          // ⇒ ⇒ **任何节点都不显示生成面板/工具条** ⇒ 新插的节点等于废掉。
          // ⇒ ⇒ 同时补上 `selectedNodeId`：否则 ⌘C/⌘D/Delete 仍作用在**旧**节点上。
          selectedNodeId: id,
          nodes: [
            // ⭐⭐⭐ 取消旧节点的选中态（详见上面 `selectedNodeId` 处的说明）
            ...state.nodes.map((n) => (n.selected ? { ...n, selected: false } : n)),
            {
              ...base,
              type: "audio" as const,
              data: { title: `音频 ${seq}`, duration: 15, width: 368, height: 368 },
            },
          ],
        };
      }
      // Batch 805 SOURCE_FACT: 时间线/主体/导演台 三种节点，尺寸取源站实测
      if (kind === "timeline") {
        return {
          ...markDirty(state),
          past: [...state.past, { nodes: state.nodes, edges: state.edges }],
          future: [],
          // ⭐⭐⭐ Batch 1032-②b-4 修掉的**真缺陷**：此前 `addNodeAt`
          // 只把新节点设成 `selected: true`，**没有取消旧节点的选中态**
          // ⇒ ⇒ 插入后 store 里**有两个** selected
          // ⇒ ⇒ `soloSelected`（selected 数量 === 1）变成 false
          // ⇒ ⇒ 按 SOURCE_FACT 批 62（多选时不显示生成面板）
          // ⇒ ⇒ **任何节点都不显示生成面板/工具条** ⇒ 新插的节点等于废掉。
          // ⇒ ⇒ 同时补上 `selectedNodeId`：否则 ⌘C/⌘D/Delete 仍作用在**旧**节点上。
          selectedNodeId: id,
          nodes: [
            // ⭐⭐⭐ 取消旧节点的选中态（详见上面 `selectedNodeId` 处的说明）
            ...state.nodes.map((n) => (n.selected ? { ...n, selected: false } : n)),
            {
              ...base,
              type: "timeline" as const,
              data: { title: `时间线 ${seq}`, width: 1200, height: 207, duration: 0, clips: [] },
            },
          ],
        };
      }
      if (kind === "subject") {
        return {
          ...markDirty(state),
          past: [...state.past, { nodes: state.nodes, edges: state.edges }],
          future: [],
          // ⭐⭐⭐ Batch 1032-②b-4 修掉的**真缺陷**：此前 `addNodeAt`
          // 只把新节点设成 `selected: true`，**没有取消旧节点的选中态**
          // ⇒ ⇒ 插入后 store 里**有两个** selected
          // ⇒ ⇒ `soloSelected`（selected 数量 === 1）变成 false
          // ⇒ ⇒ 按 SOURCE_FACT 批 62（多选时不显示生成面板）
          // ⇒ ⇒ **任何节点都不显示生成面板/工具条** ⇒ 新插的节点等于废掉。
          // ⇒ ⇒ 同时补上 `selectedNodeId`：否则 ⌘C/⌘D/Delete 仍作用在**旧**节点上。
          selectedNodeId: id,
          nodes: [
            // ⭐⭐⭐ 取消旧节点的选中态（详见上面 `selectedNodeId` 处的说明）
            ...state.nodes.map((n) => (n.selected ? { ...n, selected: false } : n)),
            {
              ...base,
              type: "subject" as const,
              data: { title: `主体 ${seq}`, width: 352, height: 352, description: "", imported: [] },
            },
          ],
        };
      }
      if (kind === "director") {
        return {
          ...markDirty(state),
          past: [...state.past, { nodes: state.nodes, edges: state.edges }],
          future: [],
          // ⭐⭐⭐ Batch 1032-②b-4 修掉的**真缺陷**：此前 `addNodeAt`
          // 只把新节点设成 `selected: true`，**没有取消旧节点的选中态**
          // ⇒ ⇒ 插入后 store 里**有两个** selected
          // ⇒ ⇒ `soloSelected`（selected 数量 === 1）变成 false
          // ⇒ ⇒ 按 SOURCE_FACT 批 62（多选时不显示生成面板）
          // ⇒ ⇒ **任何节点都不显示生成面板/工具条** ⇒ 新插的节点等于废掉。
          // ⇒ ⇒ 同时补上 `selectedNodeId`：否则 ⌘C/⌘D/Delete 仍作用在**旧**节点上。
          selectedNodeId: id,
          nodes: [
            // ⭐⭐⭐ 取消旧节点的选中态（详见上面 `selectedNodeId` 处的说明）
            ...state.nodes.map((n) => (n.selected ? { ...n, selected: false } : n)),
            {
              ...base,
              type: "director" as const,
              data: { title: `导演台 ${seq}`, width: 320, height: 320, entered: false },
            },
          ],
        };
      }
      return {
        ...markDirty(state),
        past: [...state.past, { nodes: state.nodes, edges: state.edges }],
        future: [],
        // ⭐⭐⭐ Batch 1032-②b-4 修掉的**真缺陷**：此前 `addNodeAt`
        // 只把新节点设成 `selected: true`，**没有取消旧节点的选中态**
        // ⇒ ⇒ 插入后 store 里**有两个** selected
        // ⇒ ⇒ `soloSelected`（selected 数量 === 1）变成 false
        // ⇒ ⇒ 按 SOURCE_FACT 批 62（多选时不显示生成面板）
        // ⇒ ⇒ **任何节点都不显示生成面板/工具条** ⇒ 新插的节点等于废掉。
        // ⇒ ⇒ 同时补上 `selectedNodeId`：否则 ⌘C/⌘D/Delete 仍作用在**旧**节点上。
        selectedNodeId: id,
        nodes: [
          // ⭐⭐⭐ 取消旧节点的选中态（详见上面 `selectedNodeId` 处的说明）
          ...state.nodes.map((n) => (n.selected ? { ...n, selected: false } : n)),
          {
            ...base,
            type: "text" as const,
            data: {
              title: `文本 ${seq}`,
              // 占位提示在组件层渲染 (Batch 68 SOURCE_FACT 双击编辑文本)
              text: "",
              width: 368,
              height: 368,
            },
          },
        ],
      };
    }),
}));

// Batch 67: dev/test 专用 — 验证器经 window hook 驱动 mock 态
// (如 setMediaError)；生产构建不挂载。
if (process.env.NODE_ENV !== "production" && typeof window !== "undefined") {
  (window as unknown as Record<string, unknown>).__jimengStore =
    useJimengStore;
}
