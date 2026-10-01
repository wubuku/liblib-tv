"use client";

import { create } from "zustand";
import type { Edge } from "@xyflow/react";
import type { FrameosNode } from "@/types/frameos";

// 外部传入的 viewport 信息 (避免在 store 内直接调用 useReactFlow hook)
interface AddNodeOpts {
  // 视口 (来自 ReactFlow)，用于把节点放到画布中央
  panX?: number;
  panY?: number;
  zoom?: number;
  // 视口尺寸 (window innerWidth/Height)
  viewportWidth?: number;
  viewportHeight?: number;
  // Batch 348: 显式指定落点（**画布流坐标**，不是屏幕坐标）。
  // 「双击空白处添加节点」用双击点作为落点 —— 之前 addNode 只能放视口中央或
  // 随机位置，用户在哪儿双击就必须在哪儿出现，否则这个交互没有意义。
  position?: { x: number; y: number };
}

interface Generation {
  id: string;
  startedAt: number;
  durationMs: number;
  edgeIds: string[];
  nodeIds: string[];
  status: "running" | "done" | "error";
  progress: number; // 0-100
  prompt: string;
}

// Batch 251: 画布分组 (源站 2026-09-27 采样, docs/research/liblib-frameos-batch251-2026-09-27)
export interface FrameosGroup {
  id: string;
  name: string; // 组1, 组2 …
  color: string; // hex, 驱动 bg/border/手柄/色点
  memberIds: string[];
  // flow 坐标 (成员 bbox + PADDING)
  x: number;
  y: number;
  w: number;
  h: number;
}

export const FRAMEOS_GROUP_PADDING = 28;
export const FRAMEOS_GROUP_ARRANGE_GAP = 40;
// 源站调色板顺序 (aria-label: 首位「默认色」, 其余「背景色 #xxx」)
export const FRAMEOS_GROUP_COLORS = [
  "#64748b",
  "#ef4444",
  "#f97316",
  "#eab308",
  "#22c55e",
  "#14b8a6",
  "#3b82f6",
  "#6366f1",
  "#ec4899",
  "#9ca3af",
];

// Batch 331: 撤销栈条目。canvasKey 用于跨画布隔离（见 undo/redo）。
type HistoryEntry = {
  nodes: FrameosNode[];
  edges: Edge[];
  groups?: FrameosGroup[];
  canvasKey?: string;
};

interface FrameosCanvasState {
  // 待确认操作 (删除节点/边时弹窗)

  // 画布名（顶部 breadcrumb 显示）
  breadcrumb: { project: string; scene: string; canvas: string };

  // 多画布场景数据（key: project/scene/canvas）
  // 每个 canvas 包含自己的 nodes/edges
  // Batch 332: 增加 groups —— 分组属于画布，切走时需一并保存
  canvasData: Record<
    string,
    { nodes: FrameosNode[]; edges: Edge[]; groups?: FrameosGroup[] }
  >;

  // 当前激活的 canvas 数据（nodes/edges 派生自 canvasData[breadcrumbKey]）
  nodes: FrameosNode[];
  edges: Edge[];

  // 历史栈（用于撤销/重做）
  // Batch 329: 快照纳入 groups —— 此前只存 {nodes, edges}，而 removeNode
  // (Batch 328 reconcileGroups) / createGroup / ungroup 都会改动 groups，
  // 撤销却只还原 nodes/edges → 节点回来了、分组状态没回来（成员丢失/分组残留）。
  // Batch 331: 快照带 canvasKey —— 换画布后旧画布的快照若被撤销，会把
  // 上一张画布的整份图灌进当前画布。undo/redo 遇到异画布快照即拒绝。
  // canvasKey 缺失 = Batch 331 之前的旧快照，按「与当前画布同源」处理。
  past: HistoryEntry[];
  future: HistoryEntry[];

  // minimap 是否显示 (canvas-map-dock 第一个按钮的 is-active 切换)
  showMinimap: boolean;

  // dock 中"画布小地图"按钮的 active 状态
  minimapPinActive: boolean;

  // prompt bar 输入（受控）
  promptValue: string;

  // 当前选中的节点（控制 prompt bar 显示 + 节点高亮）
  selectedNodeId: string | null;

  // Batch 251: 画布分组 (成组创建的覆盖层) 与选中分组
  groups: FrameosGroup[];
  selectedGroupId: string | null;

  // 添加节点菜单（点击 + 号弹出）
  isAddNodeMenuOpen: boolean;

  // 整理方式菜单（点击一键整理的下拉箭头）
  isOrganizeMenuOpen: boolean;
  organizeMode: "horizontal" | "vertical" | "grid";

  // 模型下拉
  selectedModel: string;

  // 帮助面板
  isHelpOpen: boolean;

  // 调试模式（开启后节点点击会弹出右侧"节点详情"面板）
  isDebugMode: boolean;
  focusModeNodeId: string | null;
  isTemplatePanelOpen: boolean;
  isNodeSearchOpen: boolean;
  isProjectAssetsPanelOpen: boolean;
  paneMenuAt: { x: number; y: number } | null;
  refSelectTargetId: string | null;
  storyboardMode: boolean;
  // Batch 279: 裁剪态 (内容图工具条 裁剪 进入; 源站 cico-root 采样)
  croppingNodeId: string | null;

  // 生成任务: { id, startedAt, durationMs, edgeIds, nodeIds, status }
  generations: Generation[];
  currentGeneration: Generation | null;

  // ───── Actions ─────
  setBreadcrumb: (b: Partial<FrameosCanvasState["breadcrumb"]>) => void;
  setNodes: (nodes: FrameosNode[]) => void;
  setEdges: (edges: Edge[]) => void;
  organizeNodes: (laid: FrameosNode[]) => void;
  beginResize: (id: string) => void;
  resizeNode: (id: string, w: number, h: number) => void;
  addNode: (type: "text" | "image" | "video" | "character" | "scene" | "audio" | "style" | "batch" | "model3d" | "director3d" | "videoEdit", opts?: AddNodeOpts) => string;
  addEdge: (edge: Edge) => void;
  removeEdge: (id: string) => void;
  removeNode: (id: string) => void;
  updateNodeData: (id: string, patch: Record<string, unknown>) => void;
  duplicateNode: (id: string) => void;
  duplicateNodeAt: (id: string, position: { x: number; y: number }) => string | null;
  nodeClipboard: FrameosNode | null;
  copyNodeToClipboard: (id: string) => void;
  pasteNodeFromClipboard: () => void;
  toggleMinimap: () => void;
  setPromptValue: (v: string) => void;
  selectNode: (id: string | null) => void;
  createGroup: (memberIds: string[]) => string | null;
  selectGroup: (id: string | null) => void;
  ungroup: (id: string) => void;
  renameGroup: (id: string, name: string) => void;
  setGroupColor: (id: string, color: string) => void;
  arrangeGroup: (id: string, mode: "grid" | "horizontal" | "vertical") => void;
  moveGroup: (id: string, dx: number, dy: number) => void;
  pushHistory: () => void;
  toggleAddNodeMenu: () => void;
  closeAddNodeMenu: () => void;
  toggleOrganizeMenu: () => void;
  closeOrganizeMenu: () => void;
  setOrganizeMode: (mode: FrameosCanvasState["organizeMode"]) => void;
  setSelectedModel: (model: string) => void;
  undo: () => boolean;
  redo: () => boolean;
  toggleHelp: () => void;
  closeHelp: () => void;
  toggleDebugMode: () => void;
  setFocusModeNodeId: (id: string | null) => void;
  toggleTemplatePanel: () => void;
  toggleProjectAssetsPanel: () => void;
  setPaneMenuAt: (at: { x: number; y: number } | null) => void;
  setRefSelectTargetId: (id: string | null) => void;
  toggleStoryboardMode: () => void;
  setCroppingNode: (id: string | null) => void;
  toggleNodeSearch: () => void;
  closeNodeSearch: () => void;

  startGeneration: (opts: {
    prompt: string;
    edgeIds: string[];
    nodeIds: string[];
  }) => string;
  cancelGeneration: () => void;
  // Batch 333: 挂载后应用持久化内容（避免 SSR hydration mismatch）
  restorePersistedCanvas: () => void;
}

const initialNodes: FrameosNode[] = [
  {
    id: "text-1",
    type: "text",
    position: { x: 442, y: 33 },
    style: { width: 300, height: 200 },
    data: {
      title: "文本节点1",
      content: "一对怨侣在咖啡馆对峙",
    },
  },
  {
    id: "text-2",
    type: "text",
    position: { x: 61, y: 96 },
    style: { width: 300, height: 200 },
    data: {
      title: "文本节点2",
      content: "（双击编辑文本）",
    },
  },
  {
    id: "video-1",
    type: "video",
    position: { x: 996, y: 39 },
    style: { width: 300, height: 169 },
    data: {
      title: "视频节点1",
      imageUrl: "/images/frameos/node-vid-cover-1.jpg",
    },
  },
  {
    id: "video-2",
    type: "video",
    position: { x: 1221, y: 524 },
    style: { width: 300, height: 169 },
    data: {
      title: "视频节点2",
      imageUrl: "/images/frameos/node-vid-cover-2.jpg",
    },
  },
  {
    id: "video-3",
    type: "video",
    position: { x: 723, y: 597 },
    style: { width: 300, height: 169 },
    data: {
      title: "视频节点3",
      imageUrl: "/images/frameos/node-vid-cover-2.jpg",
      reviewFailed: true,
    },
  },
  {
    id: "image-1",
    type: "image",
    position: { x: 855, y: 306 },
    style: { width: 300, height: 169 },
    data: {
      title: "图片节点1",
      imageUrl: "/images/frameos/node-image-1.png",
    },
  },
  {
    id: "image-2",
    type: "image",
    position: { x: 361, y: 359 },
    style: { width: 225, height: 300 },
    data: {
      title: "图片节点2",
      imageUrl: "/images/frameos/node-image-1.png",
    },
  },
];

const initialEdges: Edge[] = [
  {
    id: "e-text1-image1",
    source: "text-1",
    target: "image-1",
    type: "default",
    sourceHandle: "right",
    targetHandle: "left",
    data: { label: "作为 prompt", kind: "default" },
  },
  {
    id: "e-video1-image1",
    source: "video-1",
    target: "image-1",
    type: "default",
    sourceHandle: "right",
    targetHandle: "left",
    data: { label: "参考视频", kind: "generating" },
  },
  {
    id: "e-video1-text1",
    source: "video-1",
    target: "text-1",
    type: "default",
    sourceHandle: "right",
    targetHandle: "left",
    data: { label: "提取文本", kind: "default" },
  },
  {
    id: "e-text2-image1",
    source: "text-2",
    target: "image-1",
    type: "default",
    sourceHandle: "right",
    targetHandle: "left",
    data: { label: "改图 prompt", kind: "error" },
  },
  {
    id: "e-video1-video3",
    source: "video-1",
    target: "video-3",
    type: "default",
    sourceHandle: "right",
    targetHandle: "left",
    data: { label: "参考镜头", kind: "default" },
  },
];

// Batch 223: addNode 生成的 id 计数器 (防同毫秒多文件上传 id 冲突)
let addNodeIdCounter = 0;
// Batch 272: createGroup 同理 — 同毫秒连建两组会产生重复 id (React key 冲突)
let groupIdCounter = 0;
// Batch 327: duplicateNode / duplicateNodeAt / pasteNodeFromClipboard 此前用裸
// Date.now()，同一毫秒内连续 ⌘D / ⌘V 会产生**相同 id** → React Flow 按 id 索引，
// 后写入的副本覆盖前者，用户看到「按了两次只多一个节点」（节点静默丢失）。
// 与 addNode/group 同解：追加单调计数器保证同毫秒内唯一。
let nodeCloneIdCounter = 0;

// Batch 328: 分组完整性 — 移除节点后同步收敛分组状态。
// 此前 removeNode 只过滤 nodes/edges，groups[].memberIds 仍指向已删节点
// （悬空成员），且分组盒 x/y/w/h 不重算 → 分组覆盖层保留旧几何、比成员大，
// 排列/拖拽/解组都基于错误成员集计算。删除后按存活成员重算包围盒。
//
// Batch 341: 无条件重算（此前带 `unchanged` 短路，**只看 memberIds**）。
// 短路把「成员集合没变」当成「盒不用动」，于是**成员整体移动**的路径
// （一键整理 / 拖拽成员）里 memberIds 原封不动 → 盒永远不重算。
// 关键前提（已逐个核对）：createGroup / arrangeGroup / moveGroup 算出的盒
// 都等于「成员包围盒 + 28」，所以无条件重算不会覆盖掉它们的结果 ——
// moveGroup 是盒与成员同量平移，平移不改变「盒 = 包围盒 + 28」这个关系。
// 代价由「无净变化返回同一对象」兜住：值没变就保持引用不变，
// 避免 Batch 333 的持久化订阅（按引用判断变更）反复写同样的内容。
function reconcileGroups(
  groups: FrameosGroup[],
  nodes: FrameosNode[]
): FrameosGroup[] {
  return groups.flatMap((g) => {
    // 按 memberIds 顺序取成员，保证 memberIds 只含存活节点且顺序稳定
    const members = g.memberIds
      .map((id) => nodes.find((n) => n.id === id))
      .filter((n): n is FrameosNode => Boolean(n));
    // 全部成员被删 → 分组无意义，随之消失
    if (members.length === 0) return [];
    const sizeOf = (n: FrameosNode) => ({
      w: ((n.style?.width as number | undefined) ?? 300),
      h: ((n.style?.height as number | undefined) ?? 200),
    });
    const minX = Math.min(...members.map((n) => n.position.x));
    const minY = Math.min(...members.map((n) => n.position.y));
    const maxX = Math.max(...members.map((n) => n.position.x + sizeOf(n).w));
    const maxY = Math.max(...members.map((n) => n.position.y + sizeOf(n).h));
    const x = minX - FRAMEOS_GROUP_PADDING;
    const y = minY - FRAMEOS_GROUP_PADDING;
    const w = maxX - minX + FRAMEOS_GROUP_PADDING * 2;
    const h = maxY - minY + FRAMEOS_GROUP_PADDING * 2;
    const sameMembers =
      g.memberIds.length === members.length &&
      members.every((m, i) => m.id === g.memberIds[i]);
    // 值完全一致 → 返回**同一个对象**，不制造新的数组/对象引用
    if (sameMembers && g.x === x && g.y === y && g.w === w && g.h === h) return [g];
    return [{ ...g, memberIds: members.map((m) => m.id), x, y, w, h }];
  });
}

// Batch 341: 「分组盒 == 存活成员包围盒 + padding」是 createGroup /
// arrangeGroup / moveGroup / reconcileGroups **一致遵守**的不变式。此前它只挂在
// 少数几条 action 上，于是每条**新**的改 nodes 的路径都会重新打破它：
//
//   实测 (probe-frameos-batch341-group-geometry.py)
//     一键整理 (FrameosMapDock → organizeNodes)  盒不动, 成员全被重排  drift x/y/w/h
//     拖拽成员 (page.tsx onNodesChange → setNodes) 盒不动            drift x/w/h
//     面板删除 (FrameosNodeEditPanel → setNodes)    悬空成员 + 盒不收缩
//
// 第三个尤其说明问题：它和 Batch 328 修过的 removeNode 是**同一处缺陷的两条路径**
// （面板直接 setNodes(filter) 绕开了 action），修一条漏一条。
//
// 与 Batch 329（13 处手写历史快照 → 单一 pushHistorySnapshot）、
// Batch 333（多处写 localStorage → 单一订阅）同一个判断：不变式只该有一个出口。
// 所以不逐条路径补调 reconcileGroups，而是把整个 store 的**写入口**包一层——
// 任何 action（包括将来新加的）写完 nodes/groups 后统一收敛一次。实测三条路径
// 一次性全绿。
//
// CLONE_DECISION: 「拖动成员时盒跟随成员」是按克隆自身不变式推的。源站是否
// 允许把成员拖出分组、是否自动退组，源站阻塞无法采样（见
// SOURCE_ACCESS_BLOCKED_2026-10-01.md），**未**发明任何"拖出即退组"的行为。
//
// Batch 343: 同一出口再收一条**同构**的不变式 ——「每条边的 source/target
// 都指向存活节点」。此前剪边只出现在 removeNode 一处
// (`edges.filter(e => e.source !== id && e.target !== id)`)，而 setNodes 是
// 公开 action，FrameosNodeEditPanel 的删除按钮正是 `setNodes(nodes.filter(...))`
// → 删掉一个连着两条边的节点后，边仍指向已删节点。
// 实测 (probe-frameos-batch343-edge-integrity.py): 悬空边 2 条，且**被 Batch 333
// 的持久化写进 localStorage 并在刷新后存活** —— 内存里的潜在缺陷被固化成了
// 持久损坏。放进同一个出口后，也顺带**治愈**已经写坏的存档（restorePersistedCanvas
// 载入时同样会经过这里）。
let enforcingGraphInvariants = false;

function edgesEqual(a: Edge[], b: Edge[]): boolean {
  if (a === b) return true;
  if (a.length !== b.length) return false;
  return a.every((e, i) => b[i].id === e.id && b[i].source === e.source && b[i].target === e.target);
}

function groupsEqual(a: FrameosGroup[], b: FrameosGroup[]): boolean {
  if (a === b) return true;
  if (a.length !== b.length) return false;
  return a.every((g, i) => {
    const o = b[i];
    return (
      g.id === o.id &&
      g.x === o.x &&
      g.y === o.y &&
      g.w === o.w &&
      g.h === o.h &&
      g.memberIds.length === o.memberIds.length &&
      g.memberIds.every((id, k) => id === o.memberIds[k])
    );
  });
}

function enforceGraphInvariants(
  get: () => FrameosCanvasState,
  rawSet: (partial: Partial<FrameosCanvasState>) => void,
  prev: FrameosCanvasState
): void {
  // 收敛过程中的写回不再触发收敛（否则无限递归）
  if (enforcingGraphInvariants) return;
  const next = get();
  // 三者都没变就没有新信息可收敛 —— 绝大多数 UI 开关走这条路
  if (
    next.nodes === prev.nodes &&
    next.groups === prev.groups &&
    next.edges === prev.edges
  ) {
    return;
  }
  enforcingGraphInvariants = true;
  try {
    // 不变式 1: 分组盒 == 存活成员包围盒 + 28 (Batch 341)
    const groups = reconcileGroups(next.groups, next.nodes);
    // 只在**结构上**真的有差异时写回：Batch 333 的持久化订阅按引用判断变更，
    // 无差别写回会让它把同样的内容反复写进 localStorage。
    if (!groupsEqual(groups, next.groups)) rawSet({ groups });

    // 不变式 2: 边的两端都指向存活节点 (Batch 343)
    const live = new Set(get().nodes.map((n) => n.id));
    const edges = get().edges.filter(
      (e) => live.has(e.source) && live.has(e.target)
    );
    if (!edgesEqual(edges, get().edges)) rawSet({ edges });
  } finally {
    enforcingGraphInvariants = false;
  }
}

// Batch 329: 统一的历史快照入口 —— 保证**每条**入栈路径都带上 groups。
// 此前 10 处各自手写 `{nodes, edges}`，漏掉 groups 是 Batch 328 之后
// 「撤销删除成员 → 节点回来但成员集停在删除后」的根因。集中到一处后，
// 新增 action 不再可能漏带。
// Batch 331: 撤销栈按画布隔离。
// 此前快照不记录来自哪张画布，而 setBreadcrumb 换画布时**只**清 groups/选中态、
// 不重置 past/future → 在画布 A 的动作可以「撤销」到画布 B 上，把 A 的
// nodes/edges/groups 整份灌进 B（实测 B 从 0 节点变成 A 的 7 个节点）。
// 修复：快照带 canvasKey，undo/redo 遇到异画布快照即拒绝并清空该侧栈。
function currentCanvasKey(breadcrumb: FrameosCanvasState["breadcrumb"]): string {
  return `${breadcrumb.project}/${breadcrumb.scene}/${breadcrumb.canvas}`;
}

function pushHistorySnapshot(
  state: {
    past: HistoryEntry[];
    nodes: FrameosNode[];
    edges: Edge[];
    groups: FrameosGroup[];
    breadcrumb: FrameosCanvasState["breadcrumb"];
  }
): HistoryEntry[] {
  return [
    ...state.past.slice(-19),
    {
      nodes: state.nodes,
      edges: state.edges,
      groups: state.groups,
      canvasKey: currentCanvasKey(state.breadcrumb),
    },
  ];
}


const MOCK_CANVASES: Record<string, { nodes: FrameosNode[]; edges: Edge[] }> = {
  // Batch 164: 演示上下文对齐 2026-09-23 源站 (测试作品/测试项目/画布 1)
  "测试作品/测试项目/画布 1": {
    nodes: initialNodes,
    edges: initialEdges,
  },
  "测试作品/测试项目/画布 3": {
    nodes: [],
    edges: [],
  },
  "测试作品/测试项目/画布 2": {
    nodes: [
      {
        id: "demo-text-1",
        type: "text",
        position: { x: 200, y: 200 },
        style: { width: 300, height: 200 },
        data: { title: "文本节点1（画布 2）", content: "画布 2 的文本节点" },
      },
    ],
    edges: [],
  },
  "测试作品/备用项目/画布 1": {
    nodes: [
      {
        id: "demo-image-1",
        type: "image",
        position: { x: 300, y: 200 },
        style: { width: 300, height: 169 },
        data: { title: "海边场景", imageUrl: "/images/frameos/node-image-1.png" },
      },
    ],
    edges: [],
  },
};

// Batch 333: 画布内容跨刷新持久化。
//
// 依据（**有源站证据，非凭空发明**）：
//   - 手册 20-reference.md「持久化与历史」：刷新后内容保留；撤销/重做历史清空；
//   - Batch 251 采样记录「刷新确认持久化」—— 源站刷新后编辑仍在。
// 此前克隆只把内容放在内存，刷新即回到 MOCK_CANVASES 初值；而 Batch 208 的
// 验证器只断言**节点数**相等，恰好对「回到初值」也成立，从未真正覆盖内容持久。
//
// 实现沿用 directorStore 的既有 localStorage 模式（SSR 安全 + try/catch 降级）。
// 只持久化内容（nodes/edges/groups），**不持久化 past/future** —— 与源站
// 「内容保留、历史清空」一致。
const FRAMEOS_CANVAS_STORAGE_KEY = "frameos.canvasData.v1";

type PersistedCanvas = { nodes: FrameosNode[]; edges: Edge[]; groups?: FrameosGroup[] };

function readPersistedCanvases(): Record<string, PersistedCanvas> {
  if (typeof localStorage === "undefined") return {};
  try {
    const raw = localStorage.getItem(FRAMEOS_CANVAS_STORAGE_KEY);
    if (!raw) return {};
    const parsed: unknown = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") return {};
    const out: Record<string, PersistedCanvas> = {};
    for (const [k, v] of Object.entries(parsed as Record<string, unknown>)) {
      if (!v || typeof v !== "object") continue;
      const c = v as Partial<PersistedCanvas>;
      if (!Array.isArray(c.nodes) || !Array.isArray(c.edges)) continue;
      out[k] = { nodes: c.nodes, edges: c.edges, groups: Array.isArray(c.groups) ? c.groups : [] };
    }
    return out;
  } catch {
    return {};
  }
}

function writePersistedCanvases(data: Record<string, PersistedCanvas>): void {
  if (typeof localStorage === "undefined") return;
  try {
    localStorage.setItem(FRAMEOS_CANVAS_STORAGE_KEY, JSON.stringify(data));
  } catch {
    // 配额超限 / 隐私模式：静默降级为「仅内存」，不打断交互
  }
}

// 已保存的画布覆盖 fixture（Batch 333）
const PERSISTED_CANVASES = readPersistedCanvases();
const INITIAL_CANVAS_DATA: Record<string, PersistedCanvas> =
  Object.keys(PERSISTED_CANVASES).length > 0
    ? { ...MOCK_CANVASES, ...PERSISTED_CANVASES }
    : (MOCK_CANVASES as Record<string, PersistedCanvas>);


// Batch 333: 启动时以**已保存**的「画布 1」内容为初值。
//
// ⚠️ 关键：**不能**在模块初始化时就把持久化内容灌进 store ——
// 服务端渲染时 localStorage 不存在（SSR 拿不到），客户端 hydrate 时才有，
// 两者渲染出**不同的树** → React hydration mismatch（控制台报 pageerror，
// 且 React 会丢弃服务端 HTML 重新在客户端生成）。
// 正确做法：store 初值一律用 fixture，持久化内容在**挂载后**由
// `restorePersistedCanvas()` 应用（见文件末尾的 mount 订阅）。
//
// Batch 341: 上一行的 init 不能直接用 zustand 给的 set —— 我们在它外面套一层，
// 让「分组盒 == 存活成员包围盒 + padding」成为**所有写路径的强制不变式**。
// 见下方 enforceGraphInvariants。
export const useFrameosStore = create<FrameosCanvasState>((rawSet, get) => {
  // 显式签名而非 `(...args) => rawSet(...args)`：zustand 的 setState 是**重载**的
  // （partial / replace 两个形态），rest 展开会丢掉重载解析而报 TS2769。
  const set = (
    partial:
      | FrameosCanvasState
      | Partial<FrameosCanvasState>
      | ((state: FrameosCanvasState) => FrameosCanvasState | Partial<FrameosCanvasState>),
    replace?: false
  ) => {
    const prev = get();
    rawSet(partial, replace);
    enforceGraphInvariants(get, rawSet, prev);
  };
  return ({
  breadcrumb: { project: "测试作品", scene: "测试项目", canvas: "画布 1" },
  nodes: initialNodes,
  edges: initialEdges,
  showMinimap: true,
  minimapPinActive: true,
  promptValue: "",
  selectedNodeId: null,
  groups: [],
  selectedGroupId: null,
  nodeClipboard: null,
  isAddNodeMenuOpen: false,
  isOrganizeMenuOpen: false,
  organizeMode: "grid",
  selectedModel: "Seedream 5.0 Pro",
  isHelpOpen: false,
  isDebugMode: false,
  focusModeNodeId: null,
  isTemplatePanelOpen: false,
  isNodeSearchOpen: false,
  isProjectAssetsPanelOpen: false,
  paneMenuAt: null,
  refSelectTargetId: null,
  storyboardMode: false,
  croppingNodeId: null,
  past: [],
  future: [],
  canvasData: INITIAL_CANVAS_DATA,
  generations: [],
  currentGeneration: null,

  setBreadcrumb: (b) => {
    const state = get();
    const prevKey = currentCanvasKey(state.breadcrumb);
    const newBreadcrumb = { ...state.breadcrumb, ...b };
    const key = currentCanvasKey(newBreadcrumb);
    // Batch 332: 切走前把**当前画布的实时编辑**写回 canvasData。
    // 此前直接用 MOCK_CANVASES 覆盖 → 本地新增/移动/删除的节点在切回后
    // 全部丢失（实测：加 1 个节点 7→8，切走再切回变回 7）。
    // groups 同样属于画布，一并保存与恢复。
    const canvasData: FrameosCanvasState["canvasData"] = {
      ...state.canvasData,
      [prevKey]: { nodes: state.nodes, edges: state.edges, groups: state.groups },
    };
    // 目标画布：优先用已保存的数据（含本次切走保存的），否则回落到 fixture
    const data = canvasData[key] ?? MOCK_CANVASES[key] ?? { nodes: [], edges: [] };
    set({
      breadcrumb: newBreadcrumb,
      canvasData: { ...canvasData, [key]: data },
      // 切换画布时清除选中 (分组属于画布, 一并清空)
      selectedNodeId: null,
      selectedGroupId: null,
      groups: data.groups ?? [],
      nodes: data.nodes,
      edges: data.edges,
      // Batch 331: 撤销栈按画布隔离 —— 换画布即清空两侧栈。
      // 快照已带 canvasKey 做兜底校验，但语义上撤销本就不该跨画布生效。
      past: [],
      future: [],
    });
  },

  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),
  // Batch 175: 整理入撤销历史 (源站整理可撤销)
  organizeNodes: (laid) =>
    set((state) => ({
      past: pushHistorySnapshot(state),
      future: [],
      nodes: laid,
    })),
  // Batch 189: resize 手柄 — 按下时入历史一次, 拖动过程实时更新尺寸 (不入历史)
  beginResize: (id) =>
    set((state) => ({
      past: pushHistorySnapshot(state),
      future: [],
    })),
  resizeNode: (id, w, h) =>
    set((state) => ({
      nodes: state.nodes.map((n) =>
        n.id === id
          ? { ...n, style: { ...(n.style ?? {}), width: w, height: h } }
          : n
      ),
    })),

  addNode: (type, opts) => {
    // Batch 223: 返回新节点 id (本地上传需随即写入内容); 计数器防同毫秒多文件 id 冲突
    const id = `${type}-${Date.now()}-${++addNodeIdCounter}`;
    const typeMeta: Record<string, { title: string; w: number; h: number; emoji: string; imageUrl?: string }> = {
      text: { title: "文本", w: 300, h: 200, emoji: "T" },
      // Batch 291: 新建图片/视频为**空节点**（源站实测: 创建后自动选中并展开提示
      // 词面板, 内容经上传/素材库/生成填入）, 不再预置示例图
      image: { title: "图片", w: 300, h: 169, emoji: "🖼" },
      video: { title: "视频", w: 300, h: 169, emoji: "🎬" },
      character: { title: "角色", w: 200, h: 240, emoji: "👤" },
      scene: { title: "场景", w: 300, h: 200, emoji: "🎬" },
      audio: { title: "音频", w: 300, h: 80, emoji: "🎵" },
      style: { title: "风格", w: 200, h: 200, emoji: "🎨" },
      batch: { title: "批量", w: 240, h: 160, emoji: "📦" },
      model3d: { title: "3D模型", w: 300, h: 200, emoji: "🧊" },
      director3d: { title: "3D导演台", w: 300, h: 200, emoji: "🎛" },
      videoEdit: { title: "视频剪辑台", w: 300, h: 200, emoji: "🎞" },
    };
    const meta = typeMeta[type] ?? typeMeta.text;
    const count = get().nodes.filter((n) => n.type === type).length + 1;

    // 计算位置：显式落点 > 画布中央（如果提供了 viewport），否则随机
    let position: { x: number; y: number };
    if (opts?.position) {
      // Batch 348: 以落点为**中心**（与「视口中央」分支同一套算法）
      position = {
        x: Math.round(opts.position.x - meta.w / 2),
        y: Math.round(opts.position.y - meta.h / 2),
      };
    } else if (opts && opts.viewportWidth && opts.zoom) {
      // 视口中央在画布坐标系 = (viewportCenter - pan) / zoom
      const vw = opts.viewportWidth;
      const vh = opts.viewportHeight ?? 900;
      const z = opts.zoom;
      const px = opts.panX ?? 0;
      const py = opts.panY ?? 0;
      const centerX = (vw / 2 - px) / z;
      const centerY = (vh / 2 - py) / z;
      // 节点左上角 = 中央 - 节点尺寸的一半
      position = {
        x: Math.round(centerX - meta.w / 2),
        y: Math.round(centerY - meta.h / 2),
      };
    } else {
      position = { x: 400 + Math.random() * 200, y: 300 + Math.random() * 200 };
    }

    const newNode: FrameosNode = {
      id,
      type,
      position,
      style: { width: meta.w, height: meta.h },
      data: {
        title: `${meta.title}节点${count}`,
        content: type === "text" ? "（双击编辑文本）" : undefined,
        imageUrl: meta.imageUrl,
        description:
          type === "character" ? "角色描述" :
          type === "scene" ? "场景描述" :
          type === "style" ? "风格描述" :
          type === "audio" ? "音频描述" :
          type === "batch" ? "批量任务" :
          undefined,
        duration: type === "audio" ? 30 : undefined,
        age: type === "character" ? 25 : undefined,
        batchSize: type === "batch" ? 5 : undefined,
      },
    };
    set((state) => ({
      past: pushHistorySnapshot(state),
      future: [],
      nodes: [...state.nodes, newNode],
      isAddNodeMenuOpen: false,
      selectedNodeId: id,
    }));
    return id;
  },

  addEdge: (edge) =>
    // Batch 174: 连线创建入撤销历史 (与源站全局撤销栈一致)
    set((state) => ({
      past: pushHistorySnapshot(state),
      future: [],
      edges: [...state.edges, edge],
    })),

  removeEdge: (id) =>
    // Batch 159: 删除连线入历史栈——源站撤销可恢复被删连线
    set((state) => ({
      past: pushHistorySnapshot(state),
      future: [],
      edges: state.edges.filter((e) => e.id !== id),
    })),

  removeNode: (id) =>
    set((state) => {
      // Batch 328: 节点消失后收敛分组（剪掉悬空成员 + 重算分组盒）
      const nodes = state.nodes.filter((n) => n.id !== id);
      const groups = reconcileGroups(state.groups, nodes);
      return {
        // Batch 329: 快照带上**变更前**的 groups，撤销才能把成员放回原分组
        past: pushHistorySnapshot(state),
        future: [],
        nodes,
        edges: state.edges.filter((e) => e.source !== id && e.target !== id),
        groups,
        // 分组可能因成员删空而消失，选中态不能指向已不存在的分组
        selectedGroupId:
          state.selectedGroupId && !groups.some((g) => g.id === state.selectedGroupId)
            ? null
            : state.selectedGroupId,
        selectedNodeId: state.selectedNodeId === id ? null : state.selectedNodeId,
      };
    }),

  duplicateNode: (id) => {
    const node = get().nodes.find((n) => n.id === id);
    if (!node) return;
    // Batch 327: 计数器防同毫秒连续 ⌘D 的 id 碰撞（见 nodeCloneIdCounter 注释）
    const newId = `${node.type}-${Date.now()}-${++nodeCloneIdCounter}`;
    const newNode: FrameosNode = {
      ...node,
      id: newId,
      selected: true,
      position: { x: node.position.x + 40, y: node.position.y + 40 },
      data: {
        ...node.data,
        title: `${node.data.title} 副本`,
      },
    };
    set((state) => {
      // Batch 340: 副本若落在源节点所属分组的盒内，就必须**同时**成为该组成员 ——
      // 否则「看起来在组里、实际不是成员」，删掉其余成员后盒会缩小（Batch 328），
      // 把这个副本排除在外，组内出现一块空白，视觉与归属不一致。
      const containing = state.groups.find(
        (g) =>
          g.memberIds.includes(id) &&
          newNode.position.x >= g.x &&
          newNode.position.x <= g.x + g.w &&
          newNode.position.y >= g.y &&
          newNode.position.y <= g.y + g.h
      );
      return {
        past: pushHistorySnapshot(state),
        future: [],
        // Batch 133: 修复文档记录的缺口——副本对象此前从未加入 nodes。
        nodes: [...state.nodes.map((n) => ({ ...n, selected: false })), newNode],
        groups: containing
          ? reconcileGroups(
              state.groups.map((g) =>
                g.id === containing.id
                  ? { ...g, memberIds: [...g.memberIds, newId] }
                  : g
              ),
              [...state.nodes, newNode]
            )
          : state.groups,
        selectedNodeId: newId,
      };
    });
  },


  copyNodeToClipboard: (id) => {
    const node = get().nodes.find((n) => n.id === id);
    if (!node) return;
    set({ nodeClipboard: { ...node, selected: false } });
  },

  // Batch 257: ⌥拖拽复制 — 原节点留在拖拽落点, 同题副本偏移 (+20,+15) (源站实测)
  duplicateNodeAt: (id, position) => {
    const node = get().nodes.find((n) => n.id === id);
    if (!node) return null;
    // Batch 327: 同 duplicateNode — ⌥ 拖拽与 ⌘D 可能在同一毫秒触发
    const newId = `${node.type}-${Date.now()}-alt-${++nodeCloneIdCounter}`;
    const newNode: FrameosNode = {
      ...node,
      id: newId,
      selected: true,
      position,
      data: { ...node.data },
    };
    set((state) => ({
      past: pushHistorySnapshot(state),
      future: [],
      nodes: [...state.nodes.map((n) => ({ ...n, selected: false })), newNode],
      selectedNodeId: newId,
    }));
    return newId;
  },

  pasteNodeFromClipboard: () => {
    const clip = get().nodeClipboard;
    if (!clip) return;
    // Batch 327: 计数器防同毫秒连续 ⌘V 的 id 碰撞
    const newId = `${clip.type}-${Date.now()}-${++nodeCloneIdCounter}`;
    const newNode: FrameosNode = {
      ...clip,
      id: newId,
      selected: true,
      position: { x: clip.position.x + 40, y: clip.position.y + 40 },
      data: { ...clip.data },
    };
    set((state) => ({
      past: pushHistorySnapshot(state),
      future: [],
      nodes: [...state.nodes.map((n) => ({ ...n, selected: false })), newNode],
      selectedNodeId: newId,
    }));
  },

  updateNodeData: (id, patch) => {
    // Batch 203: 内容修改入撤销历史 (文本编辑提交/图片替换等, 每次提交一条)
    set((state) => ({
      past: pushHistorySnapshot(state),
      future: [],
      nodes: state.nodes.map((n) =>
        n.id === id
          ? { ...n, data: { ...n.data, ...patch } }
          : n
      ),
    }));
  },

  toggleMinimap: () =>
    set((state) => ({ showMinimap: !state.showMinimap })),
  setPromptValue: (v) => set({ promptValue: v }),

  selectNode: (id) => {
    set((state) => ({
      selectedNodeId: id,
      // Batch 251: 节点选择与分组选择互斥
      selectedGroupId: null,
      // 同步给 xyflow 的 selected 字段 (让 xyflow 的 selected prop 传到节点组件)
      nodes: state.nodes.map((n) => ({
        ...n,
        selected: n.id === id,
      })),
    }));
  },

  // Batch 251: 成组 — 分组盒 = 成员 bbox + 28 (源站实测), 名称「组N」自动编号
  createGroup: (memberIds) => {
    const members = get().nodes.filter((n) => memberIds.includes(n.id));
    if (members.length < 2) return null;
    const minX = Math.min(...members.map((n) => n.position.x));
    const minY = Math.min(...members.map((n) => n.position.y));
    const maxX = Math.max(
      ...members.map((n) => n.position.x + ((n.style?.width as number) ?? 300))
    );
    const maxY = Math.max(
      ...members.map((n) => n.position.y + ((n.style?.height as number) ?? 200))
    );
    const id = `group-${Date.now()}-${++groupIdCounter}`;
    const group: FrameosGroup = {
      id,
      name: `组${get().groups.length + 1}`,
      color: FRAMEOS_GROUP_COLORS[0],
      memberIds: members.map((n) => n.id),
      x: minX - FRAMEOS_GROUP_PADDING,
      y: minY - FRAMEOS_GROUP_PADDING,
      w: maxX - minX + FRAMEOS_GROUP_PADDING * 2,
      h: maxY - minY + FRAMEOS_GROUP_PADDING * 2,
    };
    set((state) => ({
      // Batch 329: 成组入撤销历史 — 此前不入栈，撤销无法撤销「成组」动作
      past: pushHistorySnapshot(state),
      future: [],
      groups: [...state.groups, group],
      selectedGroupId: id,
      selectedNodeId: null,
      nodes: state.nodes.map((n) => ({ ...n, selected: false })),
    }));
    return id;
  },

  selectGroup: (id) =>
    set((state) => ({
      selectedGroupId: id,
      selectedNodeId: null,
      nodes: state.nodes.map((n) => ({ ...n, selected: false })),
    })),

  // 解组: 分组移除, 成员位置保持 (源站实测); 无 toast
  // Batch 329: 解组入撤销历史
  ungroup: (id) =>
    set((state) => ({
      past: pushHistorySnapshot(state),
      future: [],
      groups: state.groups.filter((g) => g.id !== id),
      selectedGroupId:
        state.selectedGroupId === id ? null : state.selectedGroupId,
    })),

  // Batch 262: 组重命名 (源站: 双击标签 → 内联输入 → Enter 提交)
  // Batch 330: 组重命名 / 改色 / 整组拖拽入撤销历史。
  // 此前三者只改 state 不入栈 → 动作**不可撤销**（探针实测 pushed:false、
  // undoRestores:false），与「整理可撤销」「连线可撤销」的既有语义不一致。
  // CLONE_DECISION：源站分组重命名/改色/拖拽是否可撤销**未采样**（源站阻塞，
  // 见 SOURCE_ACCESS_BLOCKED_2026-10-01.md）。此处按克隆内部一致性补齐
  // —— 用户已能撤销成组/解组/排列，撤销同层级的组操作更可预期。
  renameGroup: (id, name) =>
    set((state) => {
      const target = state.groups.find((g) => g.id === id);
      const next = name.trim();
      // 空名/与原名相同 = 无净变化，不入栈（否则一次空提交会占掉一格撤销，
      // 用户按撤销却看不到任何变化）。
      if (!target || !next || next === target.name) return state;
      return {
        past: pushHistorySnapshot(state),
        future: [],
        groups: state.groups.map((g) => (g.id === id ? { ...g, name: next } : g)),
      };
    }),

  setGroupColor: (id, color) =>
    set((state) => {
      const target = state.groups.find((g) => g.id === id);
      // 同色 = 无净变化，不入栈（同上）
      if (!target || target.color === color) return state;
      return {
        past: pushHistorySnapshot(state),
        future: [],
        groups: state.groups.map((g) => (g.id === id ? { ...g, color } : g)),
      };
    }),

  // 排列: 均按原 Y 排序 (Batch 252 源站实测: 垂直排列同样按 Y 而非 X)。
  // 水平 = 一行排开; 垂直 = 单列; 宫格 = ceil(√n) 列行优先 (源站 4 成员采样 2×2 确认)。
  // 间距 40 (行距按行内最高成员), 内容对齐分组左上 + 28, 分组盒重算 = 新内容 bbox + 28。
  arrangeGroup: (id, mode) => {
    const group = get().groups.find((g) => g.id === id);
    if (!group) return;
    const members = get().nodes.filter((n) => group.memberIds.includes(n.id));
    if (members.length === 0) return;
    const sizeOf = (n: FrameosNode) => ({
      w: ((n.style?.width as number | undefined) ?? 300),
      h: ((n.style?.height as number | undefined) ?? 200),
    });
    const sorted = [...members].sort(
      (a, b) =>
        a.position.y - b.position.y || a.position.x - b.position.x
    );
    const cols =
      mode === "horizontal"
        ? sorted.length
        : mode === "vertical"
        ? 1
        : Math.ceil(Math.sqrt(sorted.length));
    const originX = group.x + FRAMEOS_GROUP_PADDING;
    const originY = group.y + FRAMEOS_GROUP_PADDING;
    const positions = new Map<string, { x: number; y: number }>();
    let cursorX = originX;
    let cursorY = originY;
    let rowH = 0;
    sorted.forEach((n, i) => {
      const s = sizeOf(n);
      if (mode === "vertical") {
        positions.set(n.id, { x: originX, y: cursorY });
        cursorY += s.h + FRAMEOS_GROUP_ARRANGE_GAP;
      } else {
        if (i > 0 && i % cols === 0) {
          cursorX = originX;
          cursorY += rowH + FRAMEOS_GROUP_ARRANGE_GAP;
          rowH = 0;
        }
        positions.set(n.id, { x: cursorX, y: cursorY });
        cursorX += s.w + FRAMEOS_GROUP_ARRANGE_GAP;
        rowH = Math.max(rowH, s.h);
      }
    });
    const minX = Math.min(...sorted.map((n) => (positions.get(n.id) ?? n.position).x));
    const minY = Math.min(...sorted.map((n) => (positions.get(n.id) ?? n.position).y));
    const maxX = Math.max(
      ...sorted.map((n) => (positions.get(n.id) ?? n.position).x + sizeOf(n).w)
    );
    const maxY = Math.max(
      ...sorted.map((n) => (positions.get(n.id) ?? n.position).y + sizeOf(n).h)
    );
    set((state) => ({
      past: pushHistorySnapshot(state),
      future: [],
      nodes: state.nodes.map((n) => {
        const p = positions.get(n.id);
        return p ? { ...n, position: p } : n;
      }),
      groups: state.groups.map((g) =>
        g.id === id
          ? {
              ...g,
              x: minX - FRAMEOS_GROUP_PADDING,
              y: minY - FRAMEOS_GROUP_PADDING,
              w: maxX - minX + FRAMEOS_GROUP_PADDING * 2,
              h: maxY - minY + FRAMEOS_GROUP_PADDING * 2,
            }
          : g
      ),
    }));
  },

  // 分组拖拽: 分组矩形与全部成员同步位移 (源站实测 +60,+40 一致)
  moveGroup: (id, dx, dy) =>
    set((state) => {
      const group = state.groups.find((g) => g.id === id);
      if (!group) return state;
      return {
        groups: state.groups.map((g) =>
          g.id === id ? { ...g, x: g.x + dx, y: g.y + dy } : g
        ),
        nodes: state.nodes.map((n) =>
          group.memberIds.includes(n.id)
            ? { ...n, position: { x: n.position.x + dx, y: n.position.y + dy } }
            : n
        ),
      };
    }),

  // Batch 232: 节点拖动等外部手势的撤销快照 (拖动开始时调用一次)
  pushHistory: () =>
    set((state) => ({
      past: pushHistorySnapshot(state),
      future: [],
    })),

  toggleAddNodeMenu: () =>
    set((state) => ({ isAddNodeMenuOpen: !state.isAddNodeMenuOpen })),
  closeAddNodeMenu: () => set({ isAddNodeMenuOpen: false }),

  toggleOrganizeMenu: () =>
    set((state) => ({ isOrganizeMenuOpen: !state.isOrganizeMenuOpen })),
  closeOrganizeMenu: () => set({ isOrganizeMenuOpen: false }),

  setOrganizeMode: (mode) =>
    set({ organizeMode: mode, isOrganizeMenuOpen: false }),

  setSelectedModel: (model) => set({ selectedModel: model }),

  undo: () => {
    const { past, nodes, edges, groups, future, breadcrumb } = get();
    // Batch 345: 返回**是否真的撤销了**（见 redo 的同名注释）。
    if (past.length === 0) return false;
    const prev = past[past.length - 1];
    // Batch 331: 跨画布快照 —— 拒绝并丢弃整条异画布 past，
    // 否则会把上一张画布的 nodes/edges/groups 灌进当前画布。
    // 注意: 这里**没有撤销任何东西**, 只是一个防御性拒绝, 返回 false。
    const here = currentCanvasKey(breadcrumb);
    if (prev.canvasKey && prev.canvasKey !== here) {
      set({ past: [], future: [] });
      return false;
    }
    set({
      past: past.slice(0, -1),
      future: [
        { nodes, edges, groups, canvasKey: here },
        ...future,
      ].slice(0, 20),
      nodes: prev.nodes,
      edges: prev.edges,
      // Batch 329: 同步还原分组。旧快照无 groups 字段时按「分组为空」处理，
      // 再按当前 nodes 收敛，避免留下悬空成员。
      groups: reconcileGroups(prev.groups ?? [], prev.nodes),
      selectedNodeId: null,
      selectedGroupId: null,
    });
    return true;
  },
  redo: () => {
    const { future, nodes, edges, groups, past, breadcrumb } = get();
    // Batch 345: 返回**是否真的重做了**。此前是 void, 调用方无法区分
    // 「重做了」与「future 为空所以什么都没做」, 于是无条件弹「已重做」。
    if (future.length === 0) return false;
    const next = future[0];
    const here = currentCanvasKey(breadcrumb);
    // Batch 331: 同上，redo 侧同样按画布隔离
    if (next.canvasKey && next.canvasKey !== here) {
      set({ past: [], future: [] });
      return false;
    }
    set({
      past: [
        ...past,
        { nodes, edges, groups, canvasKey: here },
      ].slice(-20),
      future: future.slice(1),
      nodes: next.nodes,
      edges: next.edges,
      groups: reconcileGroups(next.groups ?? [], next.nodes),
      selectedNodeId: null,
      selectedGroupId: null,
    });
    return true;
  },

  toggleHelp: () => set((state) => ({ isHelpOpen: !state.isHelpOpen })),
  closeHelp: () => set({ isHelpOpen: false }),

  toggleDebugMode: () => set((state) => ({ isDebugMode: !state.isDebugMode })),
  setFocusModeNodeId: (id) => set({ focusModeNodeId: id }),
  toggleTemplatePanel: () => set((state) => ({ isTemplatePanelOpen: !state.isTemplatePanelOpen })),
  toggleProjectAssetsPanel: () => set((state) => ({ isProjectAssetsPanelOpen: !state.isProjectAssetsPanelOpen })),
  setPaneMenuAt: (at) => set({ paneMenuAt: at }),
  setRefSelectTargetId: (id) => set({ refSelectTargetId: id }),
  toggleStoryboardMode: () => set((state) => ({ storyboardMode: !state.storyboardMode })),
  setCroppingNode: (id) => set({ croppingNodeId: id }),
  toggleNodeSearch: () => set((state) => ({ isNodeSearchOpen: !state.isNodeSearchOpen })),
  closeNodeSearch: () => set({ isNodeSearchOpen: false }),

  startGeneration: (opts) => {
    const id = `gen-${Date.now()}`;
    const durationMs = 30000; // 30 秒 mock
    const gen: Generation = {
      id,
      startedAt: Date.now(),
      durationMs,
      edgeIds: opts.edgeIds,
      nodeIds: opts.nodeIds,
      status: "running",
      progress: 0,
      prompt: opts.prompt,
    };
    set({ currentGeneration: gen });
    return id;
  },
  cancelGeneration: () => set({ currentGeneration: null }),

  // Batch 333: 挂载后应用持久化内容（SSR 安全的关键 —— 见初值处注释）
  restorePersistedCanvas: () => {
    const persisted = readPersistedCanvases();
    const key = currentCanvasKey(get().breadcrumb);
    const saved = persisted[key];
    set({
      canvasData: { ...MOCK_CANVASES, ...persisted } as FrameosCanvasState["canvasData"],
      // 无保存记录时保持 fixture 原样（不触发无谓的重渲染）
      ...(saved
        ? { nodes: saved.nodes, edges: saved.edges, groups: saved.groups ?? [] }
        : {}),
    });
  },
  });
});

// 暴露到 window 用于 e2e 测试
if (typeof window !== "undefined") {
  (window as unknown as { __frameos_store: typeof useFrameosStore }).__frameos_store = useFrameosStore;
}

// Batch 333: 内容变更即持久化。
// 用订阅而不是在 13 个写入点各加一行 —— 漏一处就丢一次数据，
// 这正是 Batch 329「13 处各自手写快照」的教训反过来用：
// 集中到唯一出口，天然不会漏。
//
// 关键：nodes/edges/groups 的实时编辑**不会**改动 canvasData（它只在
// setBreadcrumb 时更新），所以不能只监听 canvasData —— 必须把「当前画布的
// 实时状态」一并写进当前 breadcrumb 对应的条目。
// past/future 变更不写 —— 与源站「内容保留、历史清空」一致。
if (typeof window !== "undefined") {
  let lastNodes: FrameosNode[] | null = null;
  let lastEdges: Edge[] | null = null;
  let lastGroups: FrameosGroup[] | null = null;
  let lastKey: string | null = null;
  useFrameosStore.subscribe((state) => {
    const key = currentCanvasKey(state.breadcrumb);
    const contentChanged =
      state.nodes !== lastNodes || state.edges !== lastEdges || state.groups !== lastGroups;
    if (!contentChanged && key === lastKey) return;
    lastNodes = state.nodes;
    lastEdges = state.edges;
    lastGroups = state.groups;
    lastKey = key;
    writePersistedCanvases({
      ...(state.canvasData as Record<string, PersistedCanvas>),
      [key]: { nodes: state.nodes, edges: state.edges, groups: state.groups },
    });
  });
}
