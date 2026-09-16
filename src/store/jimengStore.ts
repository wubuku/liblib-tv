"use client";

import { create } from "zustand";
import { applyEdgeChanges, applyNodeChanges } from "@xyflow/react";
import type { Edge, EdgeChange, NodeChange } from "@xyflow/react";

import type {
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
  /** 生成面板设置 (Batch 61: 持久化到 store) */
  genModel: string;
  setGenModel: (model: string) => void;

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
  setAiDrawerDraft: (draft: string) => void;
  /** 资产库模态框 (Batch 72, SOURCE_FACT 左栏 资产库 点击打开) */
  assetsOpen: boolean;
  setAssetsOpen: (open: boolean) => void;
  /** 离线编辑冲突对话框 (Batch 82, SOURCE_FACT 81-after-reload-state.png)；
      复刻侧无真实离线态，经 dev window hook 触发 */
  offlineDialogOpen: boolean;
  setOfflineDialog: (open: boolean) => void;
  /** 小地图开关 (Batch 91, SOURCE_FACT 底部 dock 小地图按钮) */
  minimapOpen: boolean;
  setMinimapOpen: (open: boolean) => void;
  /** 连线显隐 (Batch 93, SOURCE_FACT dock 显示连线 canvas-dock-lines) */
  edgesVisible: boolean;
  setEdgesVisible: (visible: boolean) => void;
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
  /** 全选 (Batch 46): ⌘A */
  selectAll: () => void;
  /** 全屏预览 (Batch 46): store 驱动，Escape/pane 点击统一关闭 */
  previewNodeId: string | null;
  openPreview: (id: string) => void;
  closePreview: () => void;
  /** 静音切换 (Batch 29) */
  toggleMute: (id: string) => void;
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
  /** 节点数据 patch (Batch 31 颜色标记；Batch 38 泛化为任意节点) */
  updateNodeData: (id: string, patch: Record<string, unknown>) => void;
  /** 节点重命名 (Batch 87, SOURCE_FACT 标题行即 Rename 按钮)：入撤销栈 */
  renameNode: (id: string, title: string) => void;
  /** 插入节点 (Batch 17/19): 左栏 / + 菜单 */
  addNodeAt: (
    kind: "video" | "image" | "text" | "audio",
    position: { x: number; y: number },
  ) => void;
  /** 本地上传 (Batch 73, SOURCE_FACT): 上传文件 → 本地视频节点
      (标题=文件名, mock 海报)，单文件单条历史 */
  addLocalUpload: (name: string, position: { x: number; y: number }) => void;
  /** 截取帧 首帧/尾帧 (Batch 62, SOURCE_FACT): 直接产出图片节点到源节点
      右侧 (自动右移避让同行节点)，带 poster 与 lineage 连线，不打开帧选择器 */
  captureFrame: (sourceId: string, frame: "first" | "last" | "custom") => void;
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

export interface JimengTask {
  id: string;
  nodeId: string;
  kind: "upscale" | "interpolate";
}

// Batch 66 (SOURCE_FACT): 顶栏 保存中…/已保存 + 下载按钮 导出前请保存画布
// 门控 — 任何内容变更为未保存态，mock 自动保存 1.2s 后恢复已保存。
let saveTimer: number | null = null;
function markDirty(state: JimengCanvasState): {
  project: JimengCanvasState["project"];
} {
  if (saveTimer !== null) window.clearTimeout(saveTimer);
  saveTimer = window.setTimeout(() => {
    saveTimer = null;
    useJimengStore.setState((s) =>
      s.project.saved ? s : { project: { ...s.project, saved: true } },
    );
  }, 2000);
  return { project: { ...state.project, saved: false } };
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
              duration: 6,
              currentTime: 0,
              playing: false,
            },
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
  captureFrame: (sourceId, frame) =>
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
      return {
        ...markDirty(state),
        past: [...state.past, { nodes: state.nodes, edges: state.edges }],
        future: [],
        nodes: [...state.nodes, node],
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
        data: { ...src.data },
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
      data: { ...n.data },
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

  startTask: (nodeId, kind) => {
    const id = `task-${Date.now()}`;
    set((state) => ({
      tasks: [
        ...state.tasks,
        { id, nodeId, kind },
      ],
      // mock 任务提交同步 toast 反馈 (Batch 11/40)
      toast: `${kind === "upscale" ? "智能超清" : "补帧"}任务已提交（mock），处理中…`,
    }));
    // mock 生命周期 (Batch 53)：4s 后自动完成并清除任务
    window.setTimeout(() => {
      useJimengStore.setState((state) => ({
        tasks: state.tasks.filter((t) => t.id !== id),
      }));
    }, 4000);
  },

  aiDrawerOpen: false,

  aiDrawerPrefill: null,

  aiDrawerRefChip: null,

  setAiDrawerOpen: (open) =>
    set((state) => ({
      aiDrawerOpen: open,
      aiDrawerPrefill: open ? state.aiDrawerPrefill : null,
      aiDrawerRefChip: open ? state.aiDrawerRefChip : null,
    })),

  openAiDrawer: (prefill, refChip) =>
    set({ aiDrawerOpen: true, aiDrawerPrefill: prefill ?? null, aiDrawerRefChip: refChip ?? null }),

  aiDrawerDraft: "",

  setAiDrawerDraft: (draft) => set({ aiDrawerDraft: draft }),

  assetsOpen: false,

  setAssetsOpen: (open) => set({ assetsOpen: open }),

  offlineDialogOpen: false,

  setOfflineDialog: (open) => set({ offlineDialogOpen: open }),

  minimapOpen: false,

  setMinimapOpen: (open) => set({ minimapOpen: open }),

  edgesVisible: true,

  setEdgesVisible: (visible) => set({ edgesVisible: visible }),

  renameProject: (name) =>
    set((state) => ({
      ...markDirty(state),
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
          ...markDirty(state),
          past: [...state.past, { nodes: state.nodes, edges: state.edges }],
          future: [],
          nodes: [
            ...state.nodes,
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
          nodes: [
            ...state.nodes,
            {
              ...base,
              type: "audio" as const,
              data: { title: `音频 ${seq}`, duration: 15, width: 368, height: 368 },
            },
          ],
        };
      }
      return {
        ...markDirty(state),
        past: [...state.past, { nodes: state.nodes, edges: state.edges }],
        future: [],
        nodes: [
          ...state.nodes,
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
