"use client";

import { create } from "zustand";
import { applyEdgeChanges, applyNodeChanges } from "@xyflow/react";
import type { Edge, EdgeChange, NodeChange } from "@xyflow/react";

import type {
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

  /** 全局 toast 文本 (Batch 40: 生成面板发送等 mock 反馈) */
  toast: string | null;
  pushToast: (text: string) => void;
  clearToast: () => void;

  // ───── Actions ─────
  onNodesChange: (changes: NodeChange<JimengNode>[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  selectNode: (id: string | null) => void;
  setZoomPercent: (z: number) => void;
  /** "+" 手柄菜单 → 新建视频节点 (右侧 160 间距) 并连线 (Batch 4) */
  addVideoNodeAfter: (sourceId: string) => void;
  removeNode: (id: string) => void;
  /** 批量删除选中节点 (Batch 38 多选深化)，单条历史记录 */
  removeNodes: (ids: string[]) => void;
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
  /** 顶部项目名行内重命名 (Batch 29, SOURCE_FACT) */
  renameProject: (name: string) => void;
  /** 底部 dock 工具态 (Batch 20): V 切换移动工具 */
  toolActive: "select" | "move";
  setToolActive: (tool: "select" | "move") => void;
  /** 播放交互 (Batch 15/24): 切换播放态 / mock 时间走动 / 双击从头重播 */
  togglePlay: (id: string) => void;
  restartPlay: (id: string) => void;
  tickPlay: (id: string, delta: number) => void;
  /** 编组 (Batch 39): ⌘G 创建编组 / ⌘⇧G 取消编组 (快捷键面板 SOURCE_FACT) */
  groupSelected: () => void;
  ungroupSelected: () => void;
  /** 静音切换 (Batch 29) */
  toggleMute: (id: string) => void;
  /** 进度条点击 seek (Batch 32)，fraction ∈ [0,1] */
  seek: (id: string, fraction: number) => void;
  /** 修剪确认 (Batch 33): 裁剪后的时长写回节点并入撤销栈 (mock: 只改时长数据) */
  applyTrim: (id: string, trimmedDuration: number) => void;
  /** 节点数据 patch (Batch 31 颜色标记；Batch 38 泛化为任意节点) */
  updateNodeData: (id: string, patch: Record<string, unknown>) => void;
  /** 插入节点 (Batch 17/19): 左栏 / + 菜单 */
  addNodeAt: (
    kind: "video" | "image" | "text" | "audio",
    position: { x: number; y: number },
  ) => void;
  /** 撤销/重做历史栈 (Batch 14)；仅记录图结构变更，不含选中态 */
  past: { nodes: JimengNode[]; edges: Edge[] }[];
  future: { nodes: JimengNode[]; edges: Edge[] }[];
  undo: () => void;
  redo: () => void;
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
      muted: true,
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
      // xyflow applyNodeChanges 会重写 selected 标志 (AGENTS.md 约束)。
      // 有 select change 时忠实应用 xyflow 的选择结果 (支持 shift 多选，
      // Batch 16)；selectedNodeId 仅记录主选节点。无 select change 时
      // (拖拽等) 以 selectedNodeId 回填单选标志 (多选拖拽折叠为主选，
      // 原型可接受)。
      const selectChanges = changes.filter(
        (c): c is Extract<NodeChange<JimengNode>, { type: "select" }> =>
          c.type === "select",
      );

      // 编组联动 (Batch 39): 拖拽编组内节点时，同组节点跟随相同位移
      const expanded: NodeChange<JimengNode>[] = [...changes];
      const byId = new Map(state.nodes.map((n) => [n.id, n]));
      for (const c of changes) {
        if (c.type !== "position" || !c.position) continue;
        const src = byId.get(c.id);
        const gid = src?.groupId;
        if (!gid || !src) continue;
        const dx = c.position.x - src.position.x;
        const dy = c.position.y - src.position.y;
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
      const all = expanded as NodeChange<JimengNode>[];

      const nodes = applyNodeChanges(all, state.nodes);
      if (selectChanges.length > 0) {
        const lastSelected = [...selectChanges]
          .reverse()
          .find((c) => c.selected);
        return { nodes, selectedNodeId: lastSelected ? lastSelected.id : null };
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

  toast: null,

  pushToast: (text) => set({ toast: text }),

  clearToast: () => set({ toast: null }),

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
          },
        ],
      };
    }),

  removeNode: (id) =>
    set((state) => ({
      past: [...state.past, { nodes: state.nodes, edges: state.edges }],
      future: [],
      nodes: state.nodes.filter((n) => n.id !== id),
      edges: state.edges.filter((e) => e.source !== id && e.target !== id),
      selectedNodeId: state.selectedNodeId === id ? null : state.selectedNodeId,
    })),

  // 批量删除选中节点 (Batch 38 多选深化)，单条历史记录
  removeNodes: (ids) =>
    set((state) => {
      if (!ids.length) return state;
      return {
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
        data: { ...src.data },
      };
      return {
        past: [...state.past, { nodes: state.nodes, edges: state.edges }],
        future: [],
        nodes: [...state.nodes, copy],
      };
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
      return {
        past: [...state.past, { nodes: state.nodes, edges: state.edges }],
        future: [],
        nodes: [...state.nodes, copy],
      };
    }),

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

  startTask: (nodeId, kind) =>
    set((state) => ({
      tasks: [
        ...state.tasks,
        { id: `task-${Date.now()}`, nodeId, kind },
      ],
    })),

  aiDrawerOpen: false,

  setAiDrawerOpen: (open) => set({ aiDrawerOpen: open }),

  renameProject: (name) =>
    set((state) => ({
      project: { ...state.project, name },
    })),

  toolActive: "select",

  setToolActive: (tool) => set({ toolActive: tool }),

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

  groupSelected: () =>
    set((state) => {
      const ids = state.nodes.filter((n) => n.selected).map((n) => n.id);
      if (ids.length < 2) return state;
      const gid = `group-${Date.now()}`;
      return {
        nodes: state.nodes.map((n) =>
          ids.includes(n.id) ? { ...n, groupId: gid } : n,
        ),
      };
    }),

  ungroupSelected: () =>
    // CLONE_DECISION: 清除画布上全部编组（源站语义为取消选中组的编组）
    set((state) => ({
      nodes: state.nodes.map((n) =>
        n.groupId ? { ...n, groupId: undefined } : n,
      ),
    })),

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

  applyTrim: (id, trimmedDuration) =>
    set((state) => ({
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
            currentTime: 0,
            playing: false,
          },
        };
      }),
    })),

  updateNodeData: (id, patch) =>
    set((state) => ({
      nodes: state.nodes.map((n) => {
        if (n.id !== id) return n;
        return { ...n, data: { ...n.data, ...patch } };
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
      const base = {
        id,
        position,
        selected: false,
      } as const;
      if (kind === "video") {
        return {
          past: [...state.past, { nodes: state.nodes, edges: state.edges }],
          future: [],
          nodes: [
            ...state.nodes,
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
          past: [...state.past, { nodes: state.nodes, edges: state.edges }],
          future: [],
          nodes: [
            ...state.nodes,
            {
              ...base,
              type: "image" as const,
              data: { title: `图片 ${seq}`, width: 480, height: 360 },
            },
          ],
        };
      }
      if (kind === "audio") {
        return {
          past: [...state.past, { nodes: state.nodes, edges: state.edges }],
          future: [],
          nodes: [
            ...state.nodes,
            {
              ...base,
              type: "audio" as const,
              data: { title: `音频 ${seq}`, duration: 15, width: 400, height: 120 },
            },
          ],
        };
      }
      return {
        past: [...state.past, { nodes: state.nodes, edges: state.edges }],
        future: [],
        nodes: [
          ...state.nodes,
          {
            ...base,
            type: "text" as const,
            data: {
              title: `文本 ${seq}`,
              text: "双击编辑文字（mock 占位）",
              width: 320,
              height: 200,
            },
          },
        ],
      };
    }),
}));
