import { create } from "zustand";
import type { Node, Edge } from "@xyflow/react";

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
  selectedNodeId: string | null;

  // Canvas actions
  addCanvas: (name?: string) => void;
  removeCanvas: (id: string) => void;
  renameCanvas: (id: string, name: string) => void;
  setActiveCanvas: (id: string) => void;
  duplicateCanvas: (id: string) => void;

  // Node actions
  addNode: (type: string, data?: Record<string, unknown>) => void;
  addDerivedNode: (sourceId: string, type: string, data?: Record<string, unknown>) => void;
  removeNode: (nodeId: string) => void;
  updateNodeData: (nodeId: string, data: Record<string, unknown>) => void;
  setNodes: (nodes: Node[]) => void;
  setEdges: (edges: Edge[]) => void;
  selectNode: (nodeId: string | null) => void;

  // Edge actions
  addEdge: (edge: Edge) => void;
  removeEdge: (edgeId: string) => void;

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
        prompt:
          "道具名称：冷掉的黑咖啡；外观特征：一杯装在白色粗陶马克杯中的美式咖啡，杯口无任何热气，深黑色的咖啡液面平静无波，马克杯底部垫着一个同材质的白色粗陶托盘；材质细节：粗糙的哑光陶瓷质感，表面有微小的窑变颗粒；关键细节：杯子边缘有一道极其细微的缺口，暗示使用的年头。高质量写实道具多角度展示图，横向构图，以 2 行 3 列的干净网格整齐排版，展示道具的六个极正视角。纯白色纯净背景，专业产品影棚摄影。",
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
        prompt:
          "近景镜头。陈默面容冷峻，他身穿黑色高领毛衣和极简羊绒大衣，三七分微卷的黑发整齐，侧脸面对镜头。他目光始终凝视着窗外街道，下颌线紧绷。侧逆光勾勒出他冷白皮的质感与深棕色的瞳孔。浅景深背景，店内陈设模糊，整体基调冰冷且充满孤立感。[视觉风格：现代都市·电影级写实。冷暖对比色调，以低饱和度冷蓝灰为主调，点缀暖橙色咖啡馆灯光。柔和的侧逆光，强调人物面部轮廓与眼神光。高清电影感，35mm胶片颗粒质感。真人媒介。]",
        references: ["/images/scene-coffee-1.png", "/images/scene-coffee-2.png"],
        generationSettings: "16:9 · 低画质 · 1K · 1张",
      },
    },
    {
      id: "v-UGQZzZOpbv",
      type: "video",
      position: { x: 2436, y: 50 },
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
  selectedNodeId: null,

  addCanvas: (name?: string) => {
    canvasCounter++;
    const newCanvas = defaultCanvas(
      `canvas-${canvasCounter}`,
      name || `画布 ${canvasCounter}`
    );
    set((state) => ({
      canvases: [...state.canvases, newCanvas],
      activeCanvasId: newCanvas.id,
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
    set({ activeCanvasId: id, selectedNodeId: null });
  },

  duplicateCanvas: (id: string) => {
    const { canvases } = get();
    const source = canvases.find((c) => c.id === id);
    if (!source) return;
    canvasCounter++;
    const newCanvas: CanvasData = {
      ...source,
      id: `canvas-${canvasCounter}`,
      name: `${source.name} (副本)`,
      nodes: source.nodes.map((n) => ({ ...n, id: `${n.id}-copy-${Date.now()}` })),
      edges: [],
    };
    set((state) => ({
      canvases: [...state.canvases, newCanvas],
      activeCanvasId: newCanvas.id,
    }));
  },

  addNode: (type: string, data?: Record<string, unknown>) => {
    const { activeCanvasId } = get();
    const activeCanvas = get().canvases.find((canvas) => canvas.id === activeCanvasId);
    const dimensions = getDefaultNodeDimensions(type);
    const position = getViewportCenterPosition(activeCanvas, dimensions);
    const newNode: Node = {
      id: `node-${Date.now()}`,
      type,
      position,
      width: dimensions.width,
      height: dimensions.height,
      style: dimensions,
      data: { ...getDefaultNodeData(type), ...data },
    };
    set((state) => ({
      canvases: state.canvases.map((c) =>
        c.id === activeCanvasId
          ? { ...c, nodes: [...c.nodes, newNode] }
          : c
      ),
      selectedNodeId: newNode.id,
    }));
  },

  addDerivedNode: (sourceId: string, type: string, data?: Record<string, unknown>) => {
    const { activeCanvasId } = get();
    const canvas = get().canvases.find((item) => item.id === activeCanvasId);
    const source = canvas?.nodes.find((node) => node.id === sourceId);
    if (!canvas || !source) return;

    const dimensions = getDefaultNodeDimensions(type);
    const sourceWidth = source.width ?? (Number(source.style?.width) || 350);
    const nodeId = `${type}-${Date.now()}`;
    const newNode: Node = {
      id: nodeId,
      type,
      position: { x: source.position.x + sourceWidth + 120, y: source.position.y },
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

    set((state) => ({
      canvases: state.canvases.map((item) =>
        item.id === activeCanvasId
          ? { ...item, nodes: [...item.nodes, newNode], edges: [...item.edges, newEdge] }
          : item,
      ),
      selectedNodeId: nodeId,
    }));
  },

  removeNode: (nodeId: string) => {
    const { activeCanvasId } = get();
    set((state) => ({
      canvases: state.canvases.map((c) =>
        c.id === activeCanvasId
          ? {
              ...c,
              nodes: c.nodes.filter((n) => n.id !== nodeId),
              edges: c.edges.filter(
                (e) => e.source !== nodeId && e.target !== nodeId
              ),
            }
          : c
      ),
      selectedNodeId: null,
    }));
  },

  updateNodeData: (nodeId: string, data: Record<string, unknown>) => {
    const { activeCanvasId } = get();
    set((state) => ({
      canvases: state.canvases.map((c) =>
        c.id === activeCanvasId
          ? {
              ...c,
              nodes: c.nodes.map((n) =>
                n.id === nodeId ? { ...n, data: { ...n.data, ...data } } : n
              ),
            }
          : c
      ),
    }));
  },

  setNodes: (nodes: Node[]) => {
    const { activeCanvasId } = get();
    set((state) => ({
      canvases: state.canvases.map((c) =>
        c.id === activeCanvasId ? { ...c, nodes } : c
      ),
    }));
  },

  setEdges: (edges: Edge[]) => {
    const { activeCanvasId } = get();
    set((state) => ({
      canvases: state.canvases.map((c) =>
        c.id === activeCanvasId ? { ...c, edges } : c
      ),
    }));
  },

  selectNode: (nodeId: string | null) => {
    set({ selectedNodeId: nodeId });
  },

  addEdge: (edge: Edge) => {
    const { activeCanvasId } = get();
    set((state) => ({
      canvases: state.canvases.map((c) =>
        c.id === activeCanvasId
          ? { ...c, edges: [...c.edges, edge] }
          : c
      ),
    }));
  },

  removeEdge: (edgeId: string) => {
    const { activeCanvasId } = get();
    set((state) => ({
      canvases: state.canvases.map((c) =>
        c.id === activeCanvasId
          ? { ...c, edges: c.edges.filter((e) => e.id !== edgeId) }
          : c
      ),
    }));
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
