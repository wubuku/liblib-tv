"use client";

import { create } from "zustand";
import { applyEdgeChanges, applyNodeChanges } from "@xyflow/react";
import type { Edge, EdgeChange, NodeChange } from "@xyflow/react";

import type { JimengNode } from "@/types/jimeng";

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

export interface JimengCanvasState {
  /** 画布元信息 (顶栏) */
  project: { name: string; nodeCount: number; saved: boolean };

  nodes: JimengNode[];
  edges: Edge[];

  /** 当前选中节点 (驱动 NodeToolbar / 生成面板) */
  selectedNodeId: string | null;

  /** 底栏缩放百分比显示 */
  zoomPercent: number;

  // ───── Actions ─────
  onNodesChange: (changes: NodeChange<JimengNode>[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  selectNode: (id: string | null) => void;
  setZoomPercent: (z: number) => void;
  /** "+" 手柄菜单 → 新建视频节点 (右侧 160 间距) 并连线 (Batch 4) */
  addVideoNodeAfter: (sourceId: string) => void;
  removeNode: (id: string) => void;
  duplicateNode: (id: string) => void;
  /** 右键菜单 复制/粘贴 (Batch 4) */
  clipboard: JimengNode | null;
  copyNode: (id: string) => void;
  pasteNode: () => void;
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
  /** 「与 AI 对话」右侧抽屉 (Batch 12) */
  aiDrawerOpen: boolean;
  setAiDrawerOpen: (open: boolean) => void;
}

export interface JimengTask {
  id: string;
  nodeId: string;
  kind: "upscale" | "interpolate";
}

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
      duration: 6,
      currentTime: 2,
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
];

export const useJimengStore = create<JimengCanvasState>((set) => ({
  project: { name: "测试项目", nodeCount: 2, saved: true },

  nodes: initialNodes,
  edges: [],

  selectedNodeId: null,

  zoomPercent: 73,

  onNodesChange: (changes) =>
    set((state) => {
      // xyflow applyNodeChanges 会重写 selected 标志 (AGENTS.md 约束)；
      // 选中态以 store.selectedNodeId 为单一来源：selection change 先流入 store，
      // 其余 change 应用后再按 selectedNodeId 回填 selected 标志。
      const selectChange = changes.find(
        (c): c is Extract<NodeChange<JimengNode>, { type: "select" }> =>
          c.type === "select",
      );
      const nodes = applyNodeChanges(changes, state.nodes);
      if (selectChange) {
        const selectedNodeId = selectChange.selected
          ? selectChange.id
          : state.selectedNodeId === selectChange.id
            ? null
            : state.selectedNodeId;
        return {
          selectedNodeId,
          nodes: nodes.map((n: JimengNode) => ({
            ...n,
            selected: n.id === selectedNodeId,
          })),
        };
      }
      return {
        nodes: nodes.map((n: JimengNode) => ({
          ...n,
          selected: n.id === state.selectedNodeId,
        })),
      };
    }),

  onEdgesChange: (changes) =>
    set((state) => ({ edges: applyEdgeChanges(changes, state.edges) })),

  selectNode: (id) =>
    set((state) => ({
      selectedNodeId: id,
      nodes: state.nodes.map((n) => ({ ...n, selected: n.id === id })),
    })),

  setZoomPercent: (z) => set({ zoomPercent: Math.round(z) }),

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
        nodes: [...state.nodes, node],
        edges: [
          ...state.edges,
          {
            id: `e-${sourceId}-${id}`,
            source: sourceId,
            target: id,
          },
        ],
      };
    }),

  removeNode: (id) =>
    set((state) => ({
      nodes: state.nodes.filter((n) => n.id !== id),
      edges: state.edges.filter((e) => e.source !== id && e.target !== id),
      selectedNodeId: state.selectedNodeId === id ? null : state.selectedNodeId,
    })),

  duplicateNode: (id) =>
    set((state) => {
      const src = state.nodes.find((n) => n.id === id);
      if (!src) return state;
      const copy: JimengNode = {
        ...src,
        id: `video-${Date.now()}`,
        selected: false,
        position: { x: src.position.x + 60, y: src.position.y + 60 },
        data: { ...src.data },
      };
      return { nodes: [...state.nodes, copy] };
    }),

  clipboard: null,

  copyNode: (id) =>
    set((state) => {
      const src = state.nodes.find((n) => n.id === id);
      return src ? { clipboard: { ...src, data: { ...src.data } } } : state;
    }),

  pasteNode: () =>
    set((state) => {
      if (!state.clipboard) return state;
      const copy: JimengNode = {
        ...state.clipboard,
        id: `video-${Date.now()}`,
        selected: false,
        position: {
          x: state.clipboard.position.x + 60,
          y: state.clipboard.position.y + 60,
        },
        data: { ...state.clipboard.data },
      };
      return { nodes: [...state.nodes, copy] };
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

  startTask: (nodeId, kind) =>
    set((state) => ({
      tasks: [
        ...state.tasks,
        { id: `task-${Date.now()}`, nodeId, kind },
      ],
    })),

  aiDrawerOpen: false,

  setAiDrawerOpen: (open) => set({ aiDrawerOpen: open }),
}));
