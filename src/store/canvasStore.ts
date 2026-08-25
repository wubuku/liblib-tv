import { create } from "zustand";
import type { Node, Edge } from "@xyflow/react";

export interface GraphSnapshot {
  nodes: Node[];
  edges: Edge[];
}

interface HistoryStack {
  past: GraphSnapshot[];
  future: GraphSnapshot[];
}

interface SetGraphOptions {
  recordHistory?: boolean;
  historySnapshot?: GraphSnapshot;
}

export interface CanvasData {
  id: string;
  name: string;
  nodes: Node[];
  edges: Edge[];
  viewport: { x: number; y: number; zoom: number };
}

interface CanvasState {
  canvases: CanvasData[];
  activeCanvasId: string;
  selectedNodeIds: string[];
  selectedNodeId: string | null;
  historyByCanvas: Record<string, HistoryStack>;

  // Canvas actions
  addCanvas: (name?: string) => void;
  removeCanvas: (id: string) => void;
  renameCanvas: (id: string, name: string) => void;
  setActiveCanvas: (id: string) => void;
  duplicateCanvas: (id: string) => void;

  // Node actions
  addNode: (type: string, data?: Record<string, unknown>) => void;
  addNodeAtPosition: (type: string, position: { x: number; y: number }, data?: Record<string, unknown>) => void;
  addDerivedNode: (sourceId: string, type: string, data?: Record<string, unknown>) => void;
  duplicateNode: (nodeId: string, includeEdges?: boolean) => void;
  duplicateSelectedNodes: () => void;
  removeNode: (nodeId: string) => void;
  removeSelectedNodes: () => void;
  groupSelectedNodes: () => void;
  ungroupSelectedNodes: () => void;
  updateNodeData: (nodeId: string, data: Record<string, unknown>) => void;
  setNodes: (nodes: Node[], options?: SetGraphOptions) => void;
  setEdges: (edges: Edge[], options?: SetGraphOptions) => void;
  selectNode: (nodeId: string | null) => void;
  selectNodes: (nodeIds: string[]) => void;

  // Edge actions
  addEdge: (edge: Edge) => void;
  removeEdge: (edgeId: string) => void;

  // History actions
  undo: () => void;
  redo: () => void;

  // Viewport actions
  setViewport: (viewport: { x: number; y: number; zoom: number }) => void;

  // Getters
  getActiveCanvas: () => CanvasData | undefined;
}

const defaultCanvas = (id: string, name: string): CanvasData => ({
  id,
  name,
  nodes: [],
  edges: [],
  viewport: { x: 0, y: 0, zoom: 1 },
});

const MAX_HISTORY = 50;

function cloneGraphSnapshot(nodes: Node[], edges: Edge[]): GraphSnapshot {
  return {
    nodes: nodes.map((node) => ({
      ...node,
      position: { ...node.position },
      style: node.style ? { ...node.style } : node.style,
      data: { ...node.data },
    })),
    edges: edges.map((edge) => ({ ...edge })),
  };
}

function pushHistory(
  historyByCanvas: Record<string, HistoryStack>,
  canvas: CanvasData,
  snapshot?: GraphSnapshot,
): Record<string, HistoryStack> {
  const current = historyByCanvas[canvas.id] ?? { past: [], future: [] };
  return {
    ...historyByCanvas,
    [canvas.id]: {
      past: [...current.past, snapshot ?? cloneGraphSnapshot(canvas.nodes, canvas.edges)].slice(-MAX_HISTORY),
      future: [],
    },
  };
}

function createNodeId(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function nodeWidth(node: Node): number {
  return (node.width ?? Number(node.style?.width)) || 350;
}

function nodeHeight(node: Node): number {
  return (node.height ?? Number(node.style?.height)) || 180;
}

function getAbsoluteNodePosition(node: Node, nodesById: Map<string, Node>): { x: number; y: number } {
  let x = node.position.x;
  let y = node.position.y;
  let parentId = node.parentId;
  const visited = new Set<string>([node.id]);

  while (parentId && !visited.has(parentId)) {
    visited.add(parentId);
    const parent = nodesById.get(parentId);
    if (!parent) break;
    x += parent.position.x;
    y += parent.position.y;
    parentId = parent.parentId;
  }

  return { x, y };
}

function withDescendantIds(nodes: Node[], requestedIds: Iterable<string>): Set<string> {
  const result = new Set(requestedIds);
  let expanded = true;

  while (expanded) {
    expanded = false;
    for (const node of nodes) {
      if (node.parentId && result.has(node.parentId) && !result.has(node.id)) {
        result.add(node.id);
        expanded = true;
      }
    }
  }

  return result;
}

function withoutParent(node: Node, position: { x: number; y: number }): Node {
  const nextNode = { ...node, position };
  delete nextNode.parentId;
  delete nextNode.extent;
  return nextNode;
}

const GROUP_PADDING = 32;

interface DuplicateGraphResult {
  copiedNodes: Node[];
  copiedEdges: Edge[];
  selectedCopyIds: string[];
}

function duplicateGraphSelection(
  canvas: CanvasData,
  requestedIds: string[],
  includeExternalEdges: boolean,
): DuplicateGraphResult | null {
  const nodesById = new Map(canvas.nodes.map((node) => [node.id, node]));
  const requested = Array.from(new Set(requestedIds)).filter((id) => nodesById.has(id));
  if (requested.length === 0) return null;

  const copyIds = new Set(requested);
  let expanded = true;
  while (expanded) {
    expanded = false;
    for (const node of canvas.nodes) {
      if (node.parentId && copyIds.has(node.parentId) && !copyIds.has(node.id)) {
        copyIds.add(node.id);
        expanded = true;
      }
    }
  }

  const idMap = new Map<string, string>();
  for (const node of canvas.nodes) {
    if (copyIds.has(node.id)) idMap.set(node.id, createNodeId(node.type ?? "node"));
  }

  const copiedNodes = canvas.nodes
    .filter((node) => copyIds.has(node.id))
    .map((node) => {
      const copiedNode: Node = {
        ...node,
        id: idMap.get(node.id) ?? createNodeId(node.type ?? "node"),
        position: { x: node.position.x + 40, y: node.position.y + 40 },
        style: node.style ? { ...node.style } : node.style,
        data: {
          ...node.data,
          ...(typeof node.data.title === "string" ? { title: `${node.data.title} 副本` } : {}),
        },
      };
      delete copiedNode.selected;

      const copiedParentId = node.parentId ? idMap.get(node.parentId) : undefined;
      if (copiedParentId) {
        copiedNode.parentId = copiedParentId;
        copiedNode.position = { ...node.position };
      } else if (node.parentId) {
        const absolutePosition = getAbsoluteNodePosition(node, nodesById);
        copiedNode.position = {
          x: absolutePosition.x + 40,
          y: absolutePosition.y + 40,
        };
        delete copiedNode.parentId;
        delete copiedNode.extent;
      }
      return copiedNode;
    });

  const copiedEdges = canvas.edges
    .filter((edge) => {
      const sourceCopied = copyIds.has(edge.source);
      const targetCopied = copyIds.has(edge.target);
      return includeExternalEdges
        ? sourceCopied || targetCopied
        : sourceCopied && targetCopied;
    })
    .map((edge) => ({
      ...edge,
      id: `${edge.id}-copy-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      source: idMap.get(edge.source) ?? edge.source,
      target: idMap.get(edge.target) ?? edge.target,
    }));

  return {
    copiedNodes,
    copiedEdges,
    selectedCopyIds: requested
      .map((id) => idMap.get(id))
      .filter((id): id is string => Boolean(id)),
  };
}

const initialCanvas2: CanvasData = {
  id: "canvas-2",
  name: "画布 2",
  nodes: [
    {
      id: "g-245IDFh8sB",
      type: "storyboard-group",
      position: { x: 2112, y: 656 },
      width: 430,
      height: 452,
      style: { width: 430, height: 452, zIndex: -1001 },
      data: {
        title: "分镜图 · 第一集：咖啡馆对峙-图片组",
        variant: "image",
      },
    },
    {
      id: "g-EFbbHpwq5w",
      type: "storyboard-group",
      position: { x: 2374, y: -12 },
      width: 722,
      height: 460,
      style: { width: 722, height: 460, zIndex: -1001 },
      data: {
        title: "视频组 · 第一集：咖啡馆对峙-视频组",
        variant: "video",
      },
    },
    {
      id: "t-9j2MoccxBj",
      type: "script",
      position: { x: 108, y: -125 },
      width: 350,
      height: 200,
      style: { width: 350, height: 200 },
      data: {
        title: "剧本",
        content:
          '第一集：咖啡馆对峙\n角色：陈默(男主,面容冷峻)、林小婉(女主,眼神忧郁)\n场景1：咖啡馆\n陈默坐在窗边，咖啡已凉。林小婉走进来，走到他对面坐下。\n林小婉提高音量说："你到底还要躲我到什么时候？"\n陈默不正眼看她，声音低沉："我没有躲你。"\n林小婉眼眶红了，说："你知道我有多担心吗？"\n陈默转过头，无声地冷笑了一下，说："当初你离开的时候，怎么没想过我会担心？"',
      },
    },
    {
      id: "i-1FQ9tErTcC",
      type: "image",
      position: { x: 132, y: 273 },
      width: 618,
      height: 350,
      style: { width: 618, height: 350 },
      data: {
        filename: "image_2026-06-15T11-22-00",
        width: 1808,
        height: 1024,
        imageUrl: "/images/scene-coffee-1.png",
        watermarkUrl: "/images/watermark.png",
        editorVariant: "empty",
        editorHeight: 191,
        generationSettings: "16:9 · 标准画质 · 2K · 1张",
      },
    },
    {
      id: "i-lBzmo67AHv",
      type: "image",
      position: { x: 410, y: 932 },
      width: 618,
      height: 350,
      style: { width: 618, height: 350 },
      data: {
        filename: "image_2026-06-15T11-22-15",
        width: 1808,
        height: 1024,
        imageUrl: "/images/scene-coffee-3.png",
        watermarkUrl: "/images/watermark.png",
        editorVariant: "empty",
        editorHeight: 191,
        generationSettings: "16:9 · 标准画质 · 2K · 1张",
      },
    },
    {
      id: "i-dnwoZQ7jsG",
      type: "image",
      position: { x: 410, y: 1332 },
      width: 700,
      height: 350,
      style: { width: 700, height: 350 },
      data: {
        filename: "咖啡",
        width: 1152,
        height: 576,
        imageUrl: "/images/scene-coffee-2.png",
        watermarkUrl: "/images/watermark.png",
        editorVariant: "prompt",
        editorHeight: 211,
        prompt:
          "道具名称：冷掉的黑咖啡；外观特征：一杯装在白色粗陶马克杯中的美式咖啡，杯口无任何热气，深黑色的咖啡液面平静无波，马克杯底部垫着一个同材质的白色粗陶托盘；材质细节：粗糙的哑光陶瓷质感，表面有微小的窑变颗粒；关键细节：杯子边缘有一道极其细微的缺口，暗示使用的年头。高质量写实道具多角度展示图，横向构图，以 2 行 3 列的干净网格整齐排版，展示道具的六个极正视角。纯白色纯净背景，专业产品影棚摄影，标准六视图参考。六视图包括：绝对正前方视图、绝对正后方视图、绝对左侧视图、绝对右侧视图、绝对正上方俯拍视图、绝对正下方仰拍视图。所有视图必须是同一件道具，材质、颜色、比例、结构完全一致。使用超长焦镜头或移轴镜头效果，将透视变形降到最低，物体所有本该平行的边缘在画面中保持平行，接近正交投影。每个视图都像在专业产品影棚中用三脚架精密校准拍摄，构图绝对端正，物体在每个格子中居中，无任何倾斜、旋转或透视畸变。画面出不得出现任何人物、角色、人群、人影等；不得出现手、脚、人脸、场景、建筑、自然景观；无其他道具；无文字、无水印、无 logo、无 UI 元素，不要任何剧情事件，保持道具本体清晰、保持完整轮廓、保持所有角度的材质和结构一致。[视觉风格：现代都市·电影级写实。冷暖对比色调，以低饱和度冷蓝灰为主调，点缀暖橙色咖啡馆灯光。柔和的侧逆光，强调人物面部轮廓与眼神光。高清电影感，35mm胶片颗粒质感。真人媒介。]",
        generationSettings: "2:1 · 低画质 · 1K · 1张",
      },
    },
    {
      id: "i-vxeeCnxySa",
      type: "image",
      position: { x: 410, y: 1732 },
      width: 700,
      height: 350,
      style: { width: 700, height: 350 },
      data: {
        filename: "图片4",
        width: 1152,
        height: 576,
        imageUrl: "/images/scene-coffee-4.png",
        watermarkUrl: "/images/watermark.png",
        editorVariant: "prompt",
        editorHeight: 191,
        prompt: "咖啡馆室内场景",
        generationSettings: "2:1 · 低画质 · 1K · 1张",
      },
    },
    {
      id: "b-bTLLuU4w5q",
      type: "script-execution",
      position: { x: 1068, y: -187 },
      width: 350,
      height: 350,
      style: { width: 350, height: 350 },
      data: {
        title: "第一集：咖啡馆对峙",
        steps: [
          { label: "确认镜头", completed: true },
          { label: "准备资产", completed: true },
          { label: "合成提示词", completed: true },
        ],
      },
    },
    {
      id: "i-YDfWhFlthe",
      type: "image",
      position: { x: 1580, y: -300 },
      width: 622,
      height: 350,
      style: { width: 622, height: 350 },
      data: {
        filename: "分镜 #2",
        width: 1280,
        height: 720,
        imageUrl: "/images/storyboard-2.png",
        watermarkUrl: "/images/watermark.png",
        editorVariant: "referenced",
        editorHeight: 274,
        prompt:
          "近景镜头。陈默面容冷峻，他身穿黑色高领毛衣和极简羊绒大衣，三七分微卷的黑发整齐，侧脸面对镜头。他目光始终凝视着窗外街道，下颌线紧绷。侧逆光勾勒出他冷白皮的质感与深棕色的瞳孔。浅景深背景，店内陈设模糊，整体基调冰冷且充满孤立感。 [视觉风格：现代都市·电影级写实。冷暖对比色调，以低饱和度冷蓝灰为主调，点缀暖橙色咖啡馆灯光。柔和的侧逆光，强调人物面部轮廓与眼神光。高清电影感，35mm胶片颗粒质感。真人媒介。]",
        references: ["/images/scene-coffee-1.png", "/images/scene-coffee-2.png"],
        generationSettings: "16:9 · 低画质 · 1K · 1张",
      },
    },
    {
      id: "v-UGQZzZOpbv",
      type: "video",
      parentId: "g-EFbbHpwq5w",
      position: { x: 62, y: 62 },
      width: 622,
      height: 350,
      style: { width: 622, height: 350 },
      data: {
        filename: "分镜视频-#9",
        model: "vip专属模型-会员",
        status: "failed",
        durationSeconds: 30,
        resolution: "1280 × 720",
      },
    },
  ],
  edges: [
    {
      id: "e-8IgMkf6Vbj",
      source: "i-1FQ9tErTcC",
      target: "b-bTLLuU4w5q",
      type: "default",
    },
    {
      id: "e-abKze5c8Ug",
      source: "i-1FQ9tErTcC",
      target: "i-YDfWhFlthe",
      type: "default",
    },
    {
      id: "e-AQmdIgKtl2",
      source: "b-bTLLuU4w5q",
      target: "g-245IDFh8sB",
      type: "default",
    },
    {
      id: "e-m2wWA2wIBA",
      source: "i-dnwoZQ7jsG",
      target: "b-bTLLuU4w5q",
      type: "default",
    },
    {
      id: "e-nlMX3rEjwN",
      source: "i-vxeeCnxySa",
      target: "b-bTLLuU4w5q",
      type: "default",
    },
    {
      id: "e-OwhsBRzrTz",
      source: "i-1FQ9tErTcC",
      target: "v-UGQZzZOpbv",
      type: "default",
    },
    {
      id: "e-QzX895ot0u",
      source: "i-lBzmo67AHv",
      target: "b-bTLLuU4w5q",
      type: "default",
    },
    {
      id: "e-VQACH36eJC",
      source: "i-dnwoZQ7jsG",
      target: "v-UGQZzZOpbv",
      type: "default",
    },
    {
      id: "e-XmiJkHfFAL",
      source: "i-YDfWhFlthe",
      target: "v-UGQZzZOpbv",
      type: "default",
    },
    {
      id: "e-xNVTHNFZZl",
      source: "i-dnwoZQ7jsG",
      target: "i-YDfWhFlthe",
      type: "default",
    },
    {
      id: "e-yEqrTOR2Ya",
      source: "b-bTLLuU4w5q",
      target: "g-EFbbHpwq5w",
      type: "default",
    },
  ],
  viewport: { x: -583.8, y: 260.8, zoom: 0.526 },
};

let canvasCounter = 2;

export const useCanvasStore = create<CanvasState>((set, get) => ({
  canvases: [defaultCanvas("canvas-1", "画布 1"), initialCanvas2],
  activeCanvasId: "canvas-2",
  selectedNodeIds: [],
  selectedNodeId: null,
  historyByCanvas: {},

  addCanvas: (name?: string) => {
    canvasCounter++;
    const newCanvas = defaultCanvas(
      `canvas-${canvasCounter}`,
      name || `画布 ${canvasCounter}`
    );
    set((state) => ({
      canvases: [...state.canvases, newCanvas],
      activeCanvasId: newCanvas.id,
      selectedNodeIds: [],
      selectedNodeId: null,
    }));
  },

  removeCanvas: (id: string) => {
    const { canvases, activeCanvasId } = get();
    if (canvases.length <= 1) return;
    const filtered = canvases.filter((c) => c.id !== id);
    set({
      canvases: filtered,
      activeCanvasId:
        activeCanvasId === id ? filtered[0].id : activeCanvasId,
      selectedNodeIds: activeCanvasId === id ? [] : get().selectedNodeIds,
      selectedNodeId: activeCanvasId === id ? null : get().selectedNodeId,
      historyByCanvas: Object.fromEntries(
        Object.entries(get().historyByCanvas).filter(([canvasId]) => canvasId !== id),
      ),
    });
  },

  renameCanvas: (id: string, name: string) => {
    set((state) => ({
      canvases: state.canvases.map((c) =>
        c.id === id ? { ...c, name } : c
      ),
    }));
  },

  setActiveCanvas: (id: string) => {
    set({ activeCanvasId: id, selectedNodeIds: [], selectedNodeId: null });
  },

  duplicateCanvas: (id: string) => {
    const { canvases } = get();
    const source = canvases.find((c) => c.id === id);
    if (!source) return;
    canvasCounter++;
    const copySuffix = `${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
    const nodeIdMap = new Map(source.nodes.map((node) => [node.id, `${node.id}-copy-${copySuffix}`]));
    const newCanvas: CanvasData = {
      ...source,
      id: `canvas-${canvasCounter}`,
      name: `${source.name} (副本)`,
      nodes: source.nodes.map((node) => ({
        ...node,
        id: nodeIdMap.get(node.id) ?? node.id,
        parentId: node.parentId ? nodeIdMap.get(node.parentId) : undefined,
        position: { ...node.position },
        style: node.style ? { ...node.style } : node.style,
        data: { ...node.data },
      })),
      edges: source.edges.map((edge) => ({
        ...edge,
        id: `${edge.id}-copy-${copySuffix}`,
        source: nodeIdMap.get(edge.source) ?? edge.source,
        target: nodeIdMap.get(edge.target) ?? edge.target,
      })),
    };
    set((state) => ({
      canvases: [...state.canvases, newCanvas],
      activeCanvasId: newCanvas.id,
      selectedNodeIds: [],
      selectedNodeId: null,
      historyByCanvas: {
        ...state.historyByCanvas,
        [newCanvas.id]: { past: [], future: [] },
      },
    }));
  },

  addNode: (type: string, data?: Record<string, unknown>) => {
    const activeCanvas = get().getActiveCanvas();
    if (!activeCanvas) return;
    const dimensions = getDefaultNodeDimensions(type);
    const position = getViewportCenterPosition(activeCanvas, dimensions);
    get().addNodeAtPosition(type, position, data);
  },

  addNodeAtPosition: (type: string, position: { x: number; y: number }, data?: Record<string, unknown>) => {
    const { activeCanvasId } = get();
    const activeCanvas = get().canvases.find((canvas) => canvas.id === activeCanvasId);
    if (!activeCanvas) return;
    const dimensions = getDefaultNodeDimensions(type);
    const newNode: Node = {
      id: createNodeId(type),
      type,
      position,
      width: dimensions.width,
      height: dimensions.height,
      style: dimensions,
      data: { ...getDefaultNodeData(type), ...data },
    };
    set((state) => {
      const currentCanvas = state.canvases.find((canvas) => canvas.id === activeCanvasId);
      if (!currentCanvas) return state;
      return {
        canvases: state.canvases.map((canvas) =>
          canvas.id === activeCanvasId
            ? { ...canvas, nodes: [...canvas.nodes, newNode] }
            : canvas,
        ),
        selectedNodeIds: [newNode.id],
        selectedNodeId: newNode.id,
        historyByCanvas: pushHistory(state.historyByCanvas, currentCanvas),
      };
    });
  },

  addDerivedNode: (sourceId: string, type: string, data?: Record<string, unknown>) => {
    const { activeCanvasId } = get();
    const canvas = get().canvases.find((item) => item.id === activeCanvasId);
    const source = canvas?.nodes.find((node) => node.id === sourceId);
    if (!canvas || !source) return;

    const dimensions = getDefaultNodeDimensions(type);
    const sourceWidth = source.width ?? (Number(source.style?.width) || 350);
    const nodesById = new Map(canvas.nodes.map((node) => [node.id, node]));
    const sourcePosition = getAbsoluteNodePosition(source, nodesById);
    const nodeId = `${type}-${Date.now()}`;
    const newNode: Node = {
      id: nodeId,
      type,
      position: { x: sourcePosition.x + sourceWidth + 120, y: sourcePosition.y },
      width: dimensions.width,
      height: dimensions.height,
      style: dimensions,
      data: { ...getDefaultNodeData(type), ...data },
    };
    const newEdge: Edge = {
      id: `e-${sourceId}-${nodeId}`,
      source: sourceId,
      target: nodeId,
      type: "default",
    };

    set((state) => {
      const currentCanvas = state.canvases.find((item) => item.id === activeCanvasId);
      if (!currentCanvas) return state;
      return {
        canvases: state.canvases.map((item) =>
          item.id === activeCanvasId
            ? { ...item, nodes: [...item.nodes, newNode], edges: [...item.edges, newEdge] }
            : item,
        ),
        selectedNodeIds: [nodeId],
        selectedNodeId: nodeId,
        historyByCanvas: pushHistory(state.historyByCanvas, currentCanvas),
      };
    });
  },

  duplicateNode: (nodeId: string, includeEdges = true) => {
    const { activeCanvasId } = get();
    const activeCanvas = get().canvases.find((canvas) => canvas.id === activeCanvasId);
    const source = activeCanvas?.nodes.find((node) => node.id === nodeId);
    if (!activeCanvas || !source) return;

    const newNodeId = createNodeId(source.type ?? "node");
    const copySuffix = `${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
    const copiedNode: Node = {
      ...source,
      id: newNodeId,
      position: { x: source.position.x + 40, y: source.position.y + 40 },
      style: source.style ? { ...source.style } : source.style,
      data: {
        ...source.data,
        ...(typeof source.data.title === "string" ? { title: `${source.data.title} 副本` } : {}),
      },
    };
    const copiedEdges = includeEdges
      ? activeCanvas.edges
          .filter((edge) => edge.source === nodeId || edge.target === nodeId)
          .map((edge) => ({
            ...edge,
            id: `${edge.id}-copy-${copySuffix}`,
            source: edge.source === nodeId ? newNodeId : edge.source,
            target: edge.target === nodeId ? newNodeId : edge.target,
          }))
      : [];

    set((state) => {
      const currentCanvas = state.canvases.find((canvas) => canvas.id === activeCanvasId);
      if (!currentCanvas) return state;
      return {
        canvases: state.canvases.map((canvas) =>
          canvas.id === activeCanvasId
            ? { ...canvas, nodes: [...canvas.nodes, copiedNode], edges: [...canvas.edges, ...copiedEdges] }
            : canvas,
        ),
        selectedNodeIds: [newNodeId],
        selectedNodeId: newNodeId,
        historyByCanvas: pushHistory(state.historyByCanvas, currentCanvas),
      };
    });
  },

  duplicateSelectedNodes: () => {
    const { activeCanvasId } = get();
    set((state) => {
      const currentCanvas = state.canvases.find((canvas) => canvas.id === activeCanvasId);
      if (!currentCanvas) return state;
      const requestedIds =
        state.selectedNodeIds.length > 0
          ? state.selectedNodeIds
          : state.selectedNodeId
            ? [state.selectedNodeId]
            : [];
      const includesGroup = requestedIds.some(
        (id) => currentCanvas.nodes.find((node) => node.id === id)?.type === "storyboard-group",
      );
      const result = duplicateGraphSelection(currentCanvas, requestedIds, requestedIds.length === 1 && !includesGroup);
      if (!result) return state;

      return {
        canvases: state.canvases.map((canvas) =>
          canvas.id === activeCanvasId
            ? {
                ...canvas,
                nodes: [...canvas.nodes, ...result.copiedNodes],
                edges: [...canvas.edges, ...result.copiedEdges],
              }
            : canvas,
        ),
        selectedNodeIds: result.selectedCopyIds,
        selectedNodeId: result.selectedCopyIds.at(-1) ?? null,
        historyByCanvas: pushHistory(state.historyByCanvas, currentCanvas),
      };
    });
  },

  removeNode: (nodeId: string) => {
    const { activeCanvasId } = get();
    set((state) => {
      const currentCanvas = state.canvases.find((canvas) => canvas.id === activeCanvasId);
      if (!currentCanvas || !currentCanvas.nodes.some((node) => node.id === nodeId)) return state;
      const removedIds = withDescendantIds(currentCanvas.nodes, [nodeId]);
      const nextSelectedNodeIds = state.selectedNodeIds.filter((id) => !removedIds.has(id));
      return {
        canvases: state.canvases.map((canvas) =>
          canvas.id === activeCanvasId
            ? {
                ...canvas,
                nodes: canvas.nodes.filter((node) => !removedIds.has(node.id)),
                edges: canvas.edges.filter(
                  (edge) => !removedIds.has(edge.source) && !removedIds.has(edge.target),
                ),
              }
            : canvas,
        ),
        selectedNodeIds: nextSelectedNodeIds,
        selectedNodeId: nextSelectedNodeIds.at(-1) ?? null,
        historyByCanvas: pushHistory(state.historyByCanvas, currentCanvas),
      };
    });
  },

  removeSelectedNodes: () => {
    const { activeCanvasId } = get();
    set((state) => {
      const currentCanvas = state.canvases.find((canvas) => canvas.id === activeCanvasId);
      const requestedIds = new Set(
        state.selectedNodeIds.length > 0
          ? state.selectedNodeIds
          : state.selectedNodeId
            ? [state.selectedNodeId]
            : [],
      );
      if (!currentCanvas || requestedIds.size === 0) return state;
      const hasSelectedNode = currentCanvas.nodes.some((node) => requestedIds.has(node.id));
      if (!hasSelectedNode) return state;
      const removedIds = withDescendantIds(currentCanvas.nodes, requestedIds);
      return {
        canvases: state.canvases.map((canvas) =>
          canvas.id === activeCanvasId
            ? {
                ...canvas,
                nodes: canvas.nodes.filter((node) => !removedIds.has(node.id)),
                edges: canvas.edges.filter(
                  (edge) => !removedIds.has(edge.source) && !removedIds.has(edge.target),
                ),
              }
            : canvas,
        ),
        selectedNodeIds: [],
        selectedNodeId: null,
        historyByCanvas: pushHistory(state.historyByCanvas, currentCanvas),
      };
    });
  },

  groupSelectedNodes: () => {
    const { activeCanvasId } = get();
    set((state) => {
      const currentCanvas = state.canvases.find((canvas) => canvas.id === activeCanvasId);
      if (!currentCanvas) return state;
      const selectedIds = new Set(state.selectedNodeIds);
      const nodesById = new Map(currentCanvas.nodes.map((node) => [node.id, node]));
      const children = currentCanvas.nodes.filter(
        (node) => selectedIds.has(node.id) && node.type !== "storyboard-group",
      );
      if (children.length < 2) return state;

      const absolutePositions = new Map(
        children.map((node) => [node.id, getAbsoluteNodePosition(node, nodesById)]),
      );
      const minX = Math.min(...children.map((node) => absolutePositions.get(node.id)?.x ?? node.position.x));
      const minY = Math.min(...children.map((node) => absolutePositions.get(node.id)?.y ?? node.position.y));
      const maxX = Math.max(
        ...children.map((node) => (absolutePositions.get(node.id)?.x ?? node.position.x) + nodeWidth(node)),
      );
      const maxY = Math.max(
        ...children.map((node) => (absolutePositions.get(node.id)?.y ?? node.position.y) + nodeHeight(node)),
      );
      const groupId = createNodeId("group");
      const groupNode: Node = {
        id: groupId,
        type: "storyboard-group",
        position: { x: minX - GROUP_PADDING, y: minY - GROUP_PADDING },
        width: maxX - minX + GROUP_PADDING * 2,
        height: maxY - minY + GROUP_PADDING * 2,
        zIndex: -1001,
        style: {
          width: maxX - minX + GROUP_PADDING * 2,
          height: maxY - minY + GROUP_PADDING * 2,
          zIndex: -1001,
        },
        data: {
          title: "组合节点",
          variant: "image",
          groupKind: "selection",
        },
      };
      const nextNodes = currentCanvas.nodes.map((node) =>
        absolutePositions.has(node.id)
          ? {
              ...node,
              parentId: groupId,
              position: {
                x: (absolutePositions.get(node.id)?.x ?? node.position.x) - groupNode.position.x,
                y: (absolutePositions.get(node.id)?.y ?? node.position.y) - groupNode.position.y,
              },
            }
          : node,
      );

      return {
        canvases: state.canvases.map((canvas) =>
          canvas.id === activeCanvasId
            ? { ...canvas, nodes: [groupNode, ...nextNodes] }
            : canvas,
        ),
        selectedNodeIds: [groupId],
        selectedNodeId: groupId,
        historyByCanvas: pushHistory(state.historyByCanvas, currentCanvas),
      };
    });
  },

  ungroupSelectedNodes: () => {
    const { activeCanvasId } = get();
    set((state) => {
      const currentCanvas = state.canvases.find((canvas) => canvas.id === activeCanvasId);
      if (!currentCanvas) return state;
      const selectedIds = new Set(state.selectedNodeIds);
      const selectedNodes = currentCanvas.nodes.filter((node) => selectedIds.has(node.id));
      const groupId =
        selectedNodes.find((node) => node.type === "storyboard-group")?.id ??
        selectedNodes.find((node) => node.parentId)?.parentId;
      if (!groupId) return state;

      const group = currentCanvas.nodes.find((node) => node.id === groupId);
      const children = currentCanvas.nodes.filter((node) => node.parentId === groupId);
      if (!group || children.length === 0) return state;

      const childIds = children.map((node) => node.id);
      const nextNodes = currentCanvas.nodes
        .filter((node) => node.id !== groupId)
        .map((node) =>
          node.parentId === groupId
            ? withoutParent(node, {
                x: group.position.x + node.position.x,
                y: group.position.y + node.position.y,
              })
            : node,
        );

      return {
        canvases: state.canvases.map((canvas) =>
          canvas.id === activeCanvasId ? { ...canvas, nodes: nextNodes } : canvas,
        ),
        selectedNodeIds: childIds,
        selectedNodeId: childIds[0] ?? null,
        historyByCanvas: pushHistory(state.historyByCanvas, currentCanvas),
      };
    });
  },

  updateNodeData: (nodeId: string, data: Record<string, unknown>) => {
    const { activeCanvasId } = get();
    set((state) => {
      const currentCanvas = state.canvases.find((canvas) => canvas.id === activeCanvasId);
      if (!currentCanvas || !currentCanvas.nodes.some((node) => node.id === nodeId)) return state;
      return {
        canvases: state.canvases.map((canvas) =>
          canvas.id === activeCanvasId
            ? {
                ...canvas,
                nodes: canvas.nodes.map((node) =>
                  node.id === nodeId ? { ...node, data: { ...node.data, ...data } } : node,
                ),
              }
            : canvas,
        ),
        historyByCanvas: pushHistory(state.historyByCanvas, currentCanvas),
      };
    });
  },

  setNodes: (nodes: Node[], options?: SetGraphOptions) => {
    const { activeCanvasId } = get();
    set((state) => {
      const currentCanvas = state.canvases.find((canvas) => canvas.id === activeCanvasId);
      if (!currentCanvas) return state;
      return {
        canvases: state.canvases.map((canvas) =>
          canvas.id === activeCanvasId ? { ...canvas, nodes } : canvas,
        ),
        historyByCanvas:
          options?.recordHistory
            ? pushHistory(state.historyByCanvas, currentCanvas, options.historySnapshot)
            : state.historyByCanvas,
      };
    });
  },

  setEdges: (edges: Edge[], options?: SetGraphOptions) => {
    const { activeCanvasId } = get();
    set((state) => {
      const currentCanvas = state.canvases.find((canvas) => canvas.id === activeCanvasId);
      if (!currentCanvas) return state;
      return {
        canvases: state.canvases.map((canvas) =>
          canvas.id === activeCanvasId ? { ...canvas, edges } : canvas,
        ),
        historyByCanvas:
          options?.recordHistory
            ? pushHistory(state.historyByCanvas, currentCanvas, options.historySnapshot)
            : state.historyByCanvas,
      };
    });
  },

  selectNode: (nodeId: string | null) => {
    const nextSelectedNodeIds = nodeId ? [nodeId] : [];
    const currentState = get();
    if (
      currentState.selectedNodeId === nodeId &&
      currentState.selectedNodeIds.length === nextSelectedNodeIds.length &&
      currentState.selectedNodeIds.every((id, index) => id === nextSelectedNodeIds[index])
    ) {
      return;
    }
    set({
      selectedNodeIds: nextSelectedNodeIds,
      selectedNodeId: nodeId,
    });
  },

  selectNodes: (nodeIds: string[]) => {
    const activeCanvas = get().getActiveCanvas();
    const availableIds = new Set(activeCanvas?.nodes.map((node) => node.id) ?? []);
    const uniqueIds = Array.from(new Set(nodeIds)).filter((id) => availableIds.has(id));
    const currentState = get();
    if (
      currentState.selectedNodeIds.length === uniqueIds.length &&
      currentState.selectedNodeIds.every((id, index) => id === uniqueIds[index]) &&
      currentState.selectedNodeId === (uniqueIds.at(-1) ?? null)
    ) {
      return;
    }
    set({
      selectedNodeIds: uniqueIds,
      selectedNodeId: uniqueIds.at(-1) ?? null,
    });
  },

  addEdge: (edge: Edge) => {
    const { activeCanvasId } = get();
    set((state) => {
      const currentCanvas = state.canvases.find((canvas) => canvas.id === activeCanvasId);
      if (!currentCanvas) return state;
      return {
        canvases: state.canvases.map((canvas) =>
          canvas.id === activeCanvasId ? { ...canvas, edges: [...canvas.edges, edge] } : canvas,
        ),
        historyByCanvas: pushHistory(state.historyByCanvas, currentCanvas),
      };
    });
  },

  removeEdge: (edgeId: string) => {
    const { activeCanvasId } = get();
    set((state) => {
      const currentCanvas = state.canvases.find((canvas) => canvas.id === activeCanvasId);
      if (!currentCanvas || !currentCanvas.edges.some((edge) => edge.id === edgeId)) return state;
      return {
        canvases: state.canvases.map((canvas) =>
          canvas.id === activeCanvasId
            ? { ...canvas, edges: canvas.edges.filter((edge) => edge.id !== edgeId) }
            : canvas,
        ),
        historyByCanvas: pushHistory(state.historyByCanvas, currentCanvas),
      };
    });
  },

  undo: () => {
    const { activeCanvasId } = get();
    set((state) => {
      const currentCanvas = state.canvases.find((canvas) => canvas.id === activeCanvasId);
      const history = state.historyByCanvas[activeCanvasId] ?? { past: [], future: [] };
      const previous = history.past.at(-1);
      if (!currentCanvas || !previous) return state;
      return {
        canvases: state.canvases.map((canvas) =>
          canvas.id === activeCanvasId
            ? { ...canvas, nodes: previous.nodes, edges: previous.edges }
            : canvas,
        ),
        historyByCanvas: {
          ...state.historyByCanvas,
          [activeCanvasId]: {
            past: history.past.slice(0, -1),
            future: [cloneGraphSnapshot(currentCanvas.nodes, currentCanvas.edges), ...history.future].slice(0, MAX_HISTORY),
          },
        },
        selectedNodeIds: [],
        selectedNodeId: null,
      };
    });
  },

  redo: () => {
    const { activeCanvasId } = get();
    set((state) => {
      const currentCanvas = state.canvases.find((canvas) => canvas.id === activeCanvasId);
      const history = state.historyByCanvas[activeCanvasId] ?? { past: [], future: [] };
      const next = history.future[0];
      if (!currentCanvas || !next) return state;
      return {
        canvases: state.canvases.map((canvas) =>
          canvas.id === activeCanvasId
            ? { ...canvas, nodes: next.nodes, edges: next.edges }
            : canvas,
        ),
        historyByCanvas: {
          ...state.historyByCanvas,
          [activeCanvasId]: {
            past: [...history.past, cloneGraphSnapshot(currentCanvas.nodes, currentCanvas.edges)].slice(-MAX_HISTORY),
            future: history.future.slice(1),
          },
        },
        selectedNodeIds: [],
        selectedNodeId: null,
      };
    });
  },

  setViewport: (viewport: { x: number; y: number; zoom: number }) => {
    const { activeCanvasId } = get();
    set((state) => ({
      canvases: state.canvases.map((c) =>
        c.id === activeCanvasId ? { ...c, viewport } : c
      ),
    }));
  },

  getActiveCanvas: () => {
    const { canvases, activeCanvasId } = get();
    return canvases.find((c) => c.id === activeCanvasId);
  },
}));

function getDefaultNodeDimensions(type: string) {
  switch (type) {
    case "image":
    case "video":
      return { width: 512, height: 288 };
    case "script-execution":
      return { width: 350, height: 350 };
    case "script":
      return { width: 350, height: 200 };
    case "storyboard-group":
      return { width: 430, height: 452 };
    case "shot-breakdown":
      return { width: 320, height: 389 };
    case "video-clip":
      return { width: 350, height: 350 };
    case "audio":
      return { width: 350, height: 140 };
    default:
      return { width: 350, height: 180 };
  }
}

function getDefaultNodeData(type: string): Record<string, unknown> {
  switch (type) {
    case "text":
      return { content: "新文本节点" };
    case "image":
      return {
        filename: "新图片",
        width: 512,
        height: 512,
        imageUrl: "/images/scene-coffee-1.png",
        watermarkUrl: "/images/watermark.png",
        editorVariant: "empty",
        editorHeight: 191,
        generationSettings: "1:1 · 标准画质 · 2K · 1张",
      };
    case "video":
      return {
        filename: "视频节点 5-片段重拍",
        durationSeconds: 30,
        resolution: "1280 × 720",
        posterUrl: "/images/scene-coffee-4.png",
        model: "Seedance 2.5",
        status: "ready",
      };
    case "shot-breakdown":
      return {
        title: "逐帧拉片",
        status: "empty",
        dimensions: ["storyboard", "motion", "music"],
      };
    case "video-clip":
      return { title: "智能剪辑 1", status: "empty" };
    case "script":
      return { title: "新剧本", content: "在此输入剧本内容..." };
    case "audio":
      return { filename: "新音频", duration: "00:00" };
    case "style":
      return { title: "风格节点", content: "自定义风格设置", styleType: "default" };
    case "effect":
      return { title: "特效节点", content: "自定义特效设置", effectType: "default" };
    default:
      return {};
  }
}

function getViewportCenterPosition(
  canvas: CanvasData | undefined,
  dimensions: { width: number; height: number },
) {
  const viewport = canvas?.viewport ?? { x: 0, y: 0, zoom: 1 };
  const viewportWidth = typeof window === "undefined" ? 929 : window.innerWidth;
  const viewportHeight = typeof window === "undefined" ? 874 : window.innerHeight;
  return {
    x: (viewportWidth / 2 - viewport.x) / viewport.zoom - dimensions.width / 2,
    y: (viewportHeight / 2 - viewport.y) / viewport.zoom - dimensions.height / 2,
  };
}
