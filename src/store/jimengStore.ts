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
}));
