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

interface PendingConfirm {
  kind: "node" | "edge";
  id: string;
  name: string;
}

interface FrameosCanvasState {
  // 待确认操作 (删除节点/边时弹窗)
  pendingConfirm: PendingConfirm | null;

  // 画布名（顶部 breadcrumb 显示）
  breadcrumb: { project: string; scene: string; canvas: string };

  // 多画布场景数据（key: project/scene/canvas）
  // 每个 canvas 包含自己的 nodes/edges
  canvasData: Record<string, { nodes: FrameosNode[]; edges: Edge[] }>;

  // 当前激活的 canvas 数据（nodes/edges 派生自 canvasData[breadcrumbKey]）
  nodes: FrameosNode[];
  edges: Edge[];

  // 历史栈（用于撤销/重做）
  past: { nodes: FrameosNode[]; edges: Edge[] }[];
  future: { nodes: FrameosNode[]; edges: Edge[] }[];

  // 缩放 (dock-bar 中间显示)
  zoomPercent: number;

  // minimap 是否显示 (canvas-map-dock 第一个按钮的 is-active 切换)
  showMinimap: boolean;

  // dock 中"画布小地图"按钮的 active 状态
  minimapPinActive: boolean;

  // prompt bar 输入（受控）
  promptValue: string;

  // 当前选中的节点（控制 prompt bar 显示 + 节点高亮）
  selectedNodeId: string | null;

  // 添加节点菜单（点击 + 号弹出）
  isAddNodeMenuOpen: boolean;

  // 整理方式菜单（点击一键整理的下拉箭头）
  isOrganizeMenuOpen: boolean;
  organizeMode: "horizontal" | "vertical" | "grid";

  // 模型下拉
  selectedModel: string;

  // PromptBar 全屏编辑
  isPromptFullscreen: boolean;

  // 帮助面板
  isHelpOpen: boolean;

  // 调试模式（开启后节点点击会弹出右侧"节点详情"面板）
  isDebugMode: boolean;

  // 生成任务: { id, startedAt, durationMs, edgeIds, nodeIds, status }
  generations: Generation[];
  currentGeneration: Generation | null;

  // ───── Actions ─────
  setBreadcrumb: (b: Partial<FrameosCanvasState["breadcrumb"]>) => void;
  setNodes: (nodes: FrameosNode[]) => void;
  setEdges: (edges: Edge[]) => void;
  addNode: (type: "text" | "image" | "video" | "character" | "scene" | "audio" | "style" | "batch", opts?: AddNodeOpts) => void;
  addEdge: (edge: Edge) => void;
  updateEdgeData: (id: string, patch: Record<string, unknown>) => void;
  removeEdge: (id: string) => void;
  removeNode: (id: string) => void;
  updateNodeData: (id: string, patch: Record<string, unknown>) => void;
  duplicateNode: (id: string) => void;
  setZoomPercent: (v: number) => void;
  toggleMinimap: () => void;
  setPromptValue: (v: string) => void;
  selectNode: (id: string | null) => void;
  toggleAddNodeMenu: () => void;
  closeAddNodeMenu: () => void;
  toggleOrganizeMenu: () => void;
  closeOrganizeMenu: () => void;
  setOrganizeMode: (mode: FrameosCanvasState["organizeMode"]) => void;
  setSelectedModel: (model: string) => void;
  togglePromptFullscreen: () => void;
  setPromptFullscreen: (v: boolean) => void;
  undo: () => void;
  redo: () => void;
  toggleHelp: () => void;
  closeHelp: () => void;
  toggleDebugMode: () => void;
  requestConfirm: (c: PendingConfirm | null) => void;

  startGeneration: (opts: {
    prompt: string;
    edgeIds: string[];
    nodeIds: string[];
  }) => string;
  cancelGeneration: () => void;
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

// 几个 mock canvas 用于 breadcrumb 切换演示
const MOCK_CANVASES: Record<string, { nodes: FrameosNode[]; edges: Edge[] }> = {
  "默认作品/咖啡馆对峙/画布 1": {
    nodes: initialNodes,
    edges: initialEdges,
  },
  "默认作品/咖啡馆对峙/画布 2": {
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
  "默认作品/海边告白/画布 1": {
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

export const useFrameosStore = create<FrameosCanvasState>((set, get) => ({
  breadcrumb: { project: "默认作品", scene: "咖啡馆对峙", canvas: "画布 1" },
  nodes: initialNodes,
  edges: initialEdges,
  zoomPercent: 100,
  showMinimap: true,
  minimapPinActive: true,
  promptValue: "",
  selectedNodeId: null,
  isAddNodeMenuOpen: false,
  isOrganizeMenuOpen: false,
  organizeMode: "grid",
  selectedModel: "帧界 O2",
  isPromptFullscreen: false,
  isHelpOpen: false,
  isDebugMode: false,
  pendingConfirm: null,
  past: [],
  future: [],
  canvasData: MOCK_CANVASES,
  generations: [],
  currentGeneration: null,

  setBreadcrumb: (b) => {
    const newBreadcrumb = { ...get().breadcrumb, ...b };
    const key = `${newBreadcrumb.project}/${newBreadcrumb.scene}/${newBreadcrumb.canvas}`;
    const data = MOCK_CANVASES[key] ?? { nodes: [], edges: [] };
    set((state) => ({
      breadcrumb: newBreadcrumb,
      canvasData: { ...state.canvasData, [key]: data },
      // 切换画布时清除选中
      selectedNodeId: null,
      nodes: data.nodes,
      edges: data.edges,
    }));
  },

  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),

  addNode: (type, opts) => {
    const id = `${type}-${Date.now()}`;
    const typeMeta: Record<string, { title: string; w: number; h: number; emoji: string; imageUrl?: string }> = {
      text: { title: "文本", w: 300, h: 200, emoji: "T" },
      image: { title: "图片", w: 300, h: 169, emoji: "🖼", imageUrl: "/images/frameos/node-image-1.png" },
      video: { title: "视频", w: 300, h: 169, emoji: "🎬", imageUrl: "/images/frameos/node-vid-cover-1.jpg" },
      character: { title: "角色", w: 200, h: 240, emoji: "👤" },
      scene: { title: "场景", w: 300, h: 200, emoji: "🎬" },
      audio: { title: "音频", w: 300, h: 80, emoji: "🎵" },
      style: { title: "风格", w: 200, h: 200, emoji: "🎨" },
      batch: { title: "批量", w: 240, h: 160, emoji: "📦" },
    };
    const meta = typeMeta[type] ?? typeMeta.text;
    const count = get().nodes.filter((n) => n.type === type).length + 1;

    // 计算位置：画布中央（如果提供了 viewport），否则随机
    let position: { x: number; y: number };
    if (opts && opts.viewportWidth && opts.zoom) {
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
      past: [...state.past.slice(-19), { nodes: state.nodes, edges: state.edges }],
      future: [],
      nodes: [...state.nodes, newNode],
      isAddNodeMenuOpen: false,
      selectedNodeId: id,
    }));
  },

  addEdge: (edge) =>
    set((state) => ({ edges: [...state.edges, edge] })),

  removeEdge: (id) =>
    set((state) => ({ edges: state.edges.filter((e) => e.id !== id) })),

  removeNode: (id) =>
    set((state) => ({
      past: [...state.past.slice(-19), { nodes: state.nodes, edges: state.edges }],
      future: [],
      nodes: state.nodes.filter((n) => n.id !== id),
      edges: state.edges.filter((e) => e.source !== id && e.target !== id),
      selectedNodeId: state.selectedNodeId === id ? null : state.selectedNodeId,
    })),

  duplicateNode: (id) => {
    const node = get().nodes.find((n) => n.id === id);
    if (!node) return;
    const newId = `${node.type}-${Date.now()}`;
    const newNode: FrameosNode = {
      ...node,
      id: newId,
      selected: false,
      position: { x: node.position.x + 40, y: node.position.y + 40 },
      data: {
        ...node.data,
        title: `${node.data.title} 副本`,
      },
    };
    set((state) => ({
      past: [...state.past.slice(-19), { nodes: state.nodes, edges: state.edges }],
      future: [],
      nodes: state.nodes.map((n) => ({ ...n, selected: n.id === newId })),
      selectedNodeId: newId,
    }));
  },

  updateNodeData: (id, patch) => {
    set((state) => ({
      nodes: state.nodes.map((n) =>
        n.id === id
          ? { ...n, data: { ...n.data, ...patch } }
          : n
      ),
    }));
  },

  updateEdgeData: (id, patch) => {
    set((state) => ({
      edges: state.edges.map((e) =>
        e.id === id
          ? { ...e, data: { ...(e.data ?? {}), ...patch } }
          : e
      ),
    }));
  },

  setZoomPercent: (v) => set({ zoomPercent: v }),
  toggleMinimap: () =>
    set((state) => ({ showMinimap: !state.showMinimap })),
  setPromptValue: (v) => set({ promptValue: v }),

  selectNode: (id) => {
    set((state) => ({
      selectedNodeId: id,
      // 同步给 xyflow 的 selected 字段 (让 xyflow 的 selected prop 传到节点组件)
      nodes: state.nodes.map((n) => ({
        ...n,
        selected: n.id === id,
      })),
    }));
  },

  toggleAddNodeMenu: () =>
    set((state) => ({ isAddNodeMenuOpen: !state.isAddNodeMenuOpen })),
  closeAddNodeMenu: () => set({ isAddNodeMenuOpen: false }),

  toggleOrganizeMenu: () =>
    set((state) => ({ isOrganizeMenuOpen: !state.isOrganizeMenuOpen })),
  closeOrganizeMenu: () => set({ isOrganizeMenuOpen: false }),

  setOrganizeMode: (mode) =>
    set({ organizeMode: mode, isOrganizeMenuOpen: false }),

  setSelectedModel: (model) => set({ selectedModel: model }),

  togglePromptFullscreen: () =>
    set((state) => ({ isPromptFullscreen: !state.isPromptFullscreen })),
  setPromptFullscreen: (v) => set({ isPromptFullscreen: v }),

  undo: () => {
    const { past, nodes, edges, future } = get();
    if (past.length === 0) return;
    const prev = past[past.length - 1];
    set({
      past: past.slice(0, -1),
      future: [{ nodes, edges }, ...future].slice(0, 20),
      nodes: prev.nodes,
      edges: prev.edges,
      selectedNodeId: null,
    });
  },
  redo: () => {
    const { future, nodes, edges, past } = get();
    if (future.length === 0) return;
    const next = future[0];
    set({
      past: [...past, { nodes, edges }].slice(-20),
      future: future.slice(1),
      nodes: next.nodes,
      edges: next.edges,
      selectedNodeId: null,
    });
  },

  toggleHelp: () => set((state) => ({ isHelpOpen: !state.isHelpOpen })),
  closeHelp: () => set({ isHelpOpen: false }),

  toggleDebugMode: () => set((state) => ({ isDebugMode: !state.isDebugMode })),

  requestConfirm: (c: PendingConfirm | null) => set({ pendingConfirm: c }),

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
}));

// 暴露到 window 用于 e2e 测试
if (typeof window !== "undefined") {
  (window as unknown as { __frameos_store: typeof useFrameosStore }).__frameos_store = useFrameosStore;
}
