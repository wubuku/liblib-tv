"use client";

import { create } from "zustand";
import type { Edge } from "@xyflow/react";
import type { FrameosNode } from "@/types/frameos";

interface FrameosCanvasState {
  // 画布名（顶部 breadcrumb 显示）
  breadcrumb: { project: string; scene: string; canvas: string };

  // 节点 + 边
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

  // ───── Actions ─────
  setBreadcrumb: (b: Partial<FrameosCanvasState["breadcrumb"]>) => void;
  setNodes: (nodes: FrameosNode[]) => void;
  setEdges: (edges: Edge[]) => void;
  addNode: (type: "text" | "image" | "video") => void;
  addEdge: (edge: Edge) => void;
  removeEdge: (id: string) => void;
  removeNode: (id: string) => void;
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
  },
  {
    id: "e-video1-image1",
    source: "video-1",
    target: "image-1",
    type: "default",
    sourceHandle: "right",
    targetHandle: "left",
  },
  {
    id: "e-video1-text1",
    source: "video-1",
    target: "text-1",
    type: "default",
    sourceHandle: "right",
    targetHandle: "left",
  },
  {
    id: "e-text2-image1",
    source: "text-2",
    target: "image-1",
    type: "default",
    sourceHandle: "right",
    targetHandle: "left",
  },
  {
    id: "e-video1-video3",
    source: "video-1",
    target: "video-3",
    type: "default",
    sourceHandle: "right",
    targetHandle: "left",
  },
];

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
  past: [],
  future: [],

  setBreadcrumb: (b) =>
    set((state) => ({ breadcrumb: { ...state.breadcrumb, ...b } })),

  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),

  addNode: (type) => {
    const id = `${type}-${Date.now()}`;
    const titlePrefix = type === "text" ? "文本" : type === "image" ? "图片" : "视频";
    const newNode: FrameosNode = {
      id,
      type,
      position: { x: 400 + Math.random() * 200, y: 300 + Math.random() * 200 },
      style: type === "text" ? { width: 300, height: 200 } : { width: 300, height: 169 },
      data: {
        title: `${titlePrefix}节点${get().nodes.filter((n) => n.type === type).length + 1}`,
        content: type === "text" ? "（双击编辑文本）" : undefined,
        imageUrl: type === "text" ? undefined : "/images/frameos/node-image-1.png",
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
      position: { x: node.position.x + 40, y: node.position.y + 40 },
      data: {
        ...node.data,
        title: `${node.data.title} 副本`,
      },
    };
    set((state) => ({
      past: [...state.past.slice(-19), { nodes: state.nodes, edges: state.edges }],
      future: [],
      nodes: [...state.nodes, newNode],
      selectedNodeId: newId,
    }));
  },

  setZoomPercent: (v) => set({ zoomPercent: v }),
  toggleMinimap: () =>
    set((state) => ({ showMinimap: !state.showMinimap })),
  setPromptValue: (v) => set({ promptValue: v }),

  selectNode: (id) => set({ selectedNodeId: id }),

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
}));

// 暴露到 window 用于 e2e 测试
if (typeof window !== "undefined") {
  (window as unknown as { __frameos_store: typeof useFrameosStore }).__frameos_store = useFrameosStore;
}
