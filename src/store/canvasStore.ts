import { create } from "zustand";
import type { Node, Edge } from "@xyflow/react";
import {
  SHOT_BREAKDOWN_RESULT_DEFINITIONS,
  type ShotBreakdownDimension,
} from "@/lib/shotBreakdownResults";
import {
  proposedLibTVConnectionFromEdge,
  validateLibTVGraphConnection,
  type LibTVConnectionValidationResult,
  type ProposedLibTVConnection,
} from "@/lib/libtvGraphConnection";
import {
  planLibTVReactFlowChanges,
  type LibTVReactFlowChangeRoutingRequest,
  type LibTVReactFlowChangeRoutingResult,
} from "@/lib/libtvReactFlowChangeRouting";

export interface GraphSnapshot {
  nodes: Node[];
  edges: Edge[];
}

export interface DerivedNodeOptions {
  dimensions?: { width: number; height: number };
  offset?: { x: number; y: number };
}

export interface VideoContinuationMetadata {
  sourceNodeId: string;
  sourceLabel: string;
  sourcePosterUrl?: string;
  startSeconds: number;
  endSeconds: number;
  edgeId: string;
}

export type SubtitleEraseMode = "smart" | "region";

export interface SubtitleEraseRegion {
  id: string;
  relX: number;
  relY: number;
  width: number;
  height: number;
}

export interface SubtitleEraseMetadata {
  sourceNodeId: string;
  sourceLabel: string;
  sourcePosterUrl?: string;
  mode: SubtitleEraseMode;
  regions: SubtitleEraseRegion[];
  edgeId: string;
  model: "volcano-subtitle-eraser";
  requestMode: "Subtitle" | "Text";
}

export type AudioSplitMode = "av" | "vocals" | "background";

export type AudioSplitOutputKind = "audio" | "silent-video";

export interface AudioSplitMetadata {
  sourceNodeId: string;
  sourceLabel: string;
  mode: AudioSplitMode;
  outputKind: AudioSplitOutputKind;
  edgeId: string;
}

export type VideoFrameCaptureKind = "first" | "last" | "current";

export interface VideoFrameCaptureMetadata {
  sourceNodeId: string;
  sourceLabel: string;
  kind: VideoFrameCaptureKind;
  captureSeconds: number;
  name: "首帧" | "尾帧" | "截图";
  alt: "视频首帧" | "视频尾帧" | "视频截图";
  edgeId: string;
}

export type DepthMotionCaptureResolution = "720P" | "1080P";

export interface DepthMotionCaptureMetadata {
  sourceNodeId: string;
  sourceLabel: string;
  resolution: DepthMotionCaptureResolution;
  durationSeconds: number;
  edgeId: string;
  model: "depth-motion-reference";
  requestMode: "DepthMap";
}

export type LongVideoProcessStage =
  | "material"
  | "shot"
  | "candidate"
  | "assembly"
  | "final";

export interface LongVideoProcessInput {
  prompt: string;
  model: string;
  ratio: string;
  resolution: string;
  durationSeconds: number;
  audio: boolean;
  credits: number;
  referenceCount: number;
}

export interface LongVideoProcessMetadata extends LongVideoProcessInput {
  sourceNodeId: string;
  sourceLabel: string;
  processId: string;
  stage: LongVideoProcessStage;
  stageIndex: number;
  batchIndex?: number;
  status: "pending";
}

export type PictureEditAction =
  | "subjectRemove"
  | "subjectModify"
  | "subjectReplace";

export type PictureEditTool = "point" | "box" | "brush" | "eraser";

export interface PictureEditReplacement {
  source: "upload" | "history";
  label: string;
}

export interface PictureEditMark {
  id: string;
  tool: Exclude<PictureEditTool, "eraser">;
  frameSeconds: number;
  relX: number;
  relY: number;
  width: number;
  height: number;
  points?: Array<{ x: number; y: number }>;
  candidate: string;
  description?: string;
  replacement?: PictureEditReplacement;
}

export interface PictureEditMetadata {
  sourceNodeId: string;
  sourceLabel: string;
  sourcePosterUrl?: string;
  mode: PictureEditAction;
  marks: PictureEditMark[];
  edgeId: string;
  model: "volcano-picture-editor";
  requestMode: "Remove" | "Modify" | "Replace";
}

export interface SmartMattingMetadata {
  sourceNodeId: string;
  sourceLabel: string;
  sourcePosterUrl?: string;
  edgeId: string;
  provider: "volcano";
  taskType: "video";
  model: "volcano-portrait-matting";
  format: "WEBM";
  width: number;
  height: number;
  duration: number;
  generatorType: "PICTURE_EDIT";
  isSmartMattingOutput: true;
}

export interface DirectorCaptureMetadata {
  sourceNodeId: string;
  captureId: string;
  cameraId: string | null;
  cameraName: string;
  aspectRatio: "16:9" | "9:16" | "1:1";
  width: number;
  height: number;
  createdAt: string;
  edgeId: string;
}

export interface DirectorAnimationExportMetadata {
  sourceNodeId: string;
  exportId: string;
  sceneName: string;
  cameraId: string | null;
  cameraName: string;
  aspectRatio: "16:9" | "9:16" | "1:1";
  width: number;
  height: number;
  durationSeconds: number;
  mimeType: string;
  sizeBytes: number;
  createdAt: string;
  edgeId: string;
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
  projectName: string;
  canvases: CanvasData[];
  activeCanvasId: string;
  selectedNodeIds: string[];
  selectedNodeId: string | null;
  selectedEdgeIds: string[];
  historyByCanvas: Record<string, HistoryStack>;

  // Canvas actions
  setProjectName: (name: string) => void;
  addCanvas: (name?: string) => void;
  removeCanvas: (id: string) => void;
  renameCanvas: (id: string, name: string) => void;
  setActiveCanvas: (id: string) => void;
  duplicateCanvas: (id: string) => void;

  // Node actions
  addNode: (type: string, data?: Record<string, unknown>) => void;
  addNodeAtPosition: (type: string, position: { x: number; y: number }, data?: Record<string, unknown>) => void;
  addDerivedNode: (
    sourceId: string,
    type: string,
    data?: Record<string, unknown>,
    options?: DerivedNodeOptions,
  ) => void;
  createVideoContinuation: (
    sourceId: string,
    startSeconds: number,
    endSeconds: number,
  ) => string | null;
  createSubtitleErase: (
    sourceId: string,
    mode: SubtitleEraseMode,
    regions: SubtitleEraseRegion[],
  ) => string | null;
  createAudioSplit: (
    sourceId: string,
    mode: AudioSplitMode,
  ) => { audioNodeId: string; silentVideoNodeId: string } | null;
  createVideoFrameCapture: (
    sourceId: string,
    kind: VideoFrameCaptureKind,
    captureSeconds?: number,
  ) => string | null;
  createDepthMotionCapture: (
    sourceId: string,
    resolution: DepthMotionCaptureResolution,
    durationSeconds: number,
  ) => string | null;
  createLongVideoProcess: (
    sourceId: string,
    input: LongVideoProcessInput,
  ) => string | null;
  createSmartMatting: (sourceId: string) => string | null;
  createPictureEdit: (
    sourceId: string,
    mode: PictureEditAction,
    marks: PictureEditMark[],
  ) => string | null;
  createDirectorCapture: (
    sourceNodeId: string,
    capture: Omit<DirectorCaptureMetadata, "sourceNodeId" | "edgeId"> & {
      dataUrl: string;
    },
  ) => string | null;
  createDirectorAnimationExport: (
    sourceNodeId: string,
    animation: Omit<
      DirectorAnimationExportMetadata,
      "sourceNodeId" | "edgeId"
    > & {
      videoUrl: string;
      posterDataUrl: string;
    },
  ) => string | null;
  clearVideoContinuation: (targetId: string) => void;
  completeShotBreakdown: (
    sourceId: string,
    dimensions: ShotBreakdownDimension[],
  ) => void;
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
  selectEdges: (edgeIds: string[]) => void;
  selectElements: (selection: {
    nodeIds: string[];
    edgeIds: string[];
  }) => void;
  routeReactFlowChanges: (
    request: LibTVReactFlowChangeRoutingRequest,
  ) => LibTVReactFlowChangeRoutingResult;

  // Edge actions
  addEdge: (edge: Edge) => LibTVConnectionValidationResult;
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
    nodes: nodes.map(cloneSemanticNode),
    edges: edges.map(cloneSemanticEdge),
  };
}

function cloneSemanticNode(node: Node): Node {
  const clonedNode: Node = {
    ...node,
    position: { ...node.position },
    style: node.style ? { ...node.style } : node.style,
    data: { ...node.data },
  };
  delete clonedNode.selected;
  delete clonedNode.measured;
  delete clonedNode.dragging;
  delete clonedNode.resizing;
  return clonedNode;
}

function cloneSemanticEdge(edge: Edge): Edge {
  const clonedEdge = { ...edge };
  delete clonedEdge.selected;
  return clonedEdge;
}

function withoutStoredNodeSelection(node: Node): Node {
  if (node.selected === undefined) return node;
  const storedNode = { ...node };
  delete storedNode.selected;
  return storedNode;
}

function withoutStoredEdgeSelection(edge: Edge): Edge {
  if (edge.selected === undefined) return edge;
  const storedEdge = { ...edge };
  delete storedEdge.selected;
  return storedEdge;
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
      past: [
        ...current.past,
        snapshot
          ? cloneGraphSnapshot(snapshot.nodes, snapshot.edges)
          : cloneGraphSnapshot(canvas.nodes, canvas.edges),
      ].slice(-MAX_HISTORY),
      future: [],
    },
  };
}

function createNodeId(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function isVideoContinuationMetadata(
  value: unknown,
): value is VideoContinuationMetadata {
  if (!value || typeof value !== "object") return false;
  return (
    "sourceNodeId" in value &&
    typeof value.sourceNodeId === "string" &&
    "sourceLabel" in value &&
    typeof value.sourceLabel === "string" &&
    "startSeconds" in value &&
    typeof value.startSeconds === "number" &&
    "endSeconds" in value &&
    typeof value.endSeconds === "number" &&
    "edgeId" in value &&
    typeof value.edgeId === "string"
  );
}

function nodeWidth(node: Node): number {
  return (node.width ?? Number(node.style?.width)) || 350;
}

function nodeHeight(node: Node): number {
  return (node.height ?? Number(node.style?.height)) || 180;
}

function rectanglesOverlap(
  a: { x: number; y: number; width: number; height: number },
  b: { x: number; y: number; width: number; height: number },
): boolean {
  return (
    a.x < b.x + b.width &&
    a.x + a.width > b.x &&
    a.y < b.y + b.height &&
    a.y + a.height > b.y
  );
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

function findAvailableRightSlot(
  source: Node,
  nodes: Node[],
  dimensions: { width: number; height: number },
  horizontalGap: number,
): { x: number; y: number } {
  const nodesById = new Map(nodes.map((node) => [node.id, node]));
  const sourcePosition = getAbsoluteNodePosition(source, nodesById);
  const x = sourcePosition.x + nodeWidth(source) + horizontalGap;
  let y = sourcePosition.y;

  for (let attempt = 0; attempt < nodes.length + 1; attempt++) {
    const candidate = { x, y, ...dimensions };
    const collides = nodes.some((node) => {
      const position = getAbsoluteNodePosition(node, nodesById);
      return rectanglesOverlap(candidate, {
        ...position,
        width: nodeWidth(node),
        height: nodeHeight(node),
      });
    });
    if (!collides) return { x, y };
    y += dimensions.height + 48;
  }

  return { x, y };
}

const LONG_VIDEO_PROCESS_BOUNDS = { width: 1890, height: 456 };

function findAvailableLongVideoOrigin(
  source: Node,
  nodes: Node[],
): { x: number; y: number } {
  const nodesById = new Map(nodes.map((node) => [node.id, node]));
  const sourcePosition = getAbsoluteNodePosition(source, nodesById);
  const x = sourcePosition.x + nodeWidth(source) + 140;
  let y =
    sourcePosition.y +
    (nodeHeight(source) - LONG_VIDEO_PROCESS_BOUNDS.height) / 2;

  for (let attempt = 0; attempt < nodes.length + 1; attempt++) {
    const candidate = { x, y, ...LONG_VIDEO_PROCESS_BOUNDS };
    const collides = nodes.some((node) => {
      const position = getAbsoluteNodePosition(node, nodesById);
      return rectanglesOverlap(candidate, {
        ...position,
        width: nodeWidth(node),
        height: nodeHeight(node),
      });
    });
    if (!collides) return { x, y };
    y += LONG_VIDEO_PROCESS_BOUNDS.height + 140;
  }

  return { x, y };
}

function parseVideoResolution(value: unknown): { width: number; height: number } {
  if (typeof value === "string") {
    const match = value.match(/(\d+)\s*[x×]\s*(\d+)/i);
    if (match) {
      return {
        width: Number(match[1]),
        height: Number(match[2]),
      };
    }
  }
  return { width: 1280, height: 720 };
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
      delete copiedNode.measured;
      delete copiedNode.dragging;
      delete copiedNode.resizing;

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
    .map((edge) => {
      const copiedEdge = cloneSemanticEdge(edge);
      return {
        ...copiedEdge,
        id: `${edge.id}-copy-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
        source: idMap.get(edge.source) ?? edge.source,
        target: idMap.get(edge.target) ?? edge.target,
      };
    });

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
  projectName: "未命名项目",
  canvases: [defaultCanvas("canvas-1", "画布 1"), initialCanvas2],
  activeCanvasId: "canvas-2",
  selectedNodeIds: [],
  selectedNodeId: null,
  selectedEdgeIds: [],
  historyByCanvas: {},

  setProjectName: (name: string) => {
    const trimmedName = name.trim();
    if (!trimmedName) return;
    set({ projectName: trimmedName });
  },

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
      selectedEdgeIds: [],
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
      selectedEdgeIds: activeCanvasId === id ? [] : get().selectedEdgeIds,
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
    set({
      activeCanvasId: id,
      selectedNodeIds: [],
      selectedNodeId: null,
      selectedEdgeIds: [],
    });
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
      nodes: source.nodes.map((node) => {
        const copiedNode = cloneSemanticNode(node);
        return {
          ...copiedNode,
          id: nodeIdMap.get(node.id) ?? node.id,
          parentId: node.parentId ? nodeIdMap.get(node.parentId) : undefined,
        };
      }),
      edges: source.edges.map((edge) => ({
        ...cloneSemanticEdge(edge),
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
      selectedEdgeIds: [],
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
        selectedEdgeIds: [],
        historyByCanvas: pushHistory(state.historyByCanvas, currentCanvas),
      };
    });
  },

  addDerivedNode: (
    sourceId: string,
    type: string,
    data?: Record<string, unknown>,
    options?: DerivedNodeOptions,
  ) => {
    const { activeCanvasId } = get();
    const canvas = get().canvases.find((item) => item.id === activeCanvasId);
    const source = canvas?.nodes.find((node) => node.id === sourceId);
    if (!canvas || !source) return;

    const dimensions = options?.dimensions ?? getDefaultNodeDimensions(type);
    const offset = options?.offset ?? { x: 120, y: 0 };
    const sourceWidth = source.width ?? (Number(source.style?.width) || 350);
    const nodesById = new Map(canvas.nodes.map((node) => [node.id, node]));
    const sourcePosition = getAbsoluteNodePosition(source, nodesById);
    const nodeId = `${type}-${Date.now()}`;
    const newNode: Node = {
      id: nodeId,
      type,
      position: {
        x: sourcePosition.x + sourceWidth + offset.x,
        y: sourcePosition.y + offset.y,
      },
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
        selectedEdgeIds: [],
        historyByCanvas: pushHistory(state.historyByCanvas, currentCanvas),
      };
    });
  },

  createVideoContinuation: (
    sourceId: string,
    startSeconds: number,
    endSeconds: number,
  ) => {
    const { activeCanvasId } = get();
    const canvas = get().canvases.find((item) => item.id === activeCanvasId);
    const source = canvas?.nodes.find((node) => node.id === sourceId);
    if (!canvas || !source) return null;

    const sourceDuration =
      typeof source.data.durationSeconds === "number"
        ? source.data.durationSeconds
        : 30;
    const normalizedStart = clampNumber(
      startSeconds,
      0,
      Math.max(0, sourceDuration - 4),
    );
    const normalizedEnd = clampNumber(
      endSeconds,
      normalizedStart + 4,
      Math.min(sourceDuration, normalizedStart + 30),
    );
    if (normalizedEnd - normalizedStart < 4) return null;

    const sourceLabel =
      typeof source.data.filename === "string"
        ? source.data.filename
        : typeof source.data.title === "string"
          ? source.data.title
          : "视频";
    const sourcePosterUrl =
      typeof source.data.posterUrl === "string"
        ? source.data.posterUrl
        : undefined;
    const dimensions = getDefaultNodeDimensions("video");
    const nodesById = new Map(canvas.nodes.map((node) => [node.id, node]));
    const sourcePosition = getAbsoluteNodePosition(source, nodesById);
    const targetId = createNodeId("video-continuation");
    const edgeId = `e-${sourceId}-${targetId}`;
    const continuation: VideoContinuationMetadata = {
      sourceNodeId: sourceId,
      sourceLabel,
      sourcePosterUrl,
      startSeconds: normalizedStart,
      endSeconds: normalizedEnd,
      edgeId,
    };
    const targetNode: Node = {
      id: targetId,
      type: "video",
      position: {
        x: sourcePosition.x + nodeWidth(source) + 120,
        y: sourcePosition.y,
      },
      width: dimensions.width,
      height: dimensions.height,
      style: dimensions,
      data: {
        filename: `续写 ${sourceLabel}`,
        model: "Seedance 2.5",
        status: "empty",
        durationSeconds: 6,
        resolution: "1280 × 720",
        prompt: "",
        generationMode: "omnireference",
        generationCount: 1,
        continuation,
      },
    };
    const continuationEdge: Edge = {
      id: edgeId,
      source: sourceId,
      target: targetId,
      type: "default",
    };

    set((state) => {
      const currentCanvas = state.canvases.find(
        (item) => item.id === activeCanvasId,
      );
      if (!currentCanvas) return state;
      return {
        canvases: state.canvases.map((item) =>
          item.id === activeCanvasId
            ? {
                ...item,
                nodes: [...item.nodes, targetNode],
                edges: [...item.edges, continuationEdge],
              }
            : item,
        ),
        selectedNodeIds: [targetId],
        selectedNodeId: targetId,
        selectedEdgeIds: [],
        historyByCanvas: pushHistory(state.historyByCanvas, currentCanvas),
      };
    });

    return targetId;
  },

  createSubtitleErase: (
    sourceId: string,
    mode: SubtitleEraseMode,
    regions: SubtitleEraseRegion[],
  ) => {
    const { activeCanvasId } = get();
    const canvas = get().canvases.find((item) => item.id === activeCanvasId);
    const source = canvas?.nodes.find((node) => node.id === sourceId);
    if (!canvas || !source || (mode === "region" && regions.length === 0)) {
      return null;
    }

    const sourceLabel =
      typeof source.data.filename === "string"
        ? source.data.filename
        : typeof source.data.title === "string"
          ? source.data.title
          : "视频";
    const sourcePosterUrl =
      typeof source.data.posterUrl === "string"
        ? source.data.posterUrl
        : undefined;
    const sourceDuration =
      typeof source.data.durationSeconds === "number"
        ? source.data.durationSeconds
        : 30;
    const dimensions = getDefaultNodeDimensions("video");
    const nodesById = new Map(canvas.nodes.map((node) => [node.id, node]));
    const sourcePosition = getAbsoluteNodePosition(source, nodesById);
    const targetId = createNodeId("subtitle-erase");
    const edgeId = `e-${sourceId}-${targetId}`;
    const normalizedRegions = regions.map((region) => {
      const relX = clampNumber(region.relX, 0, 1);
      const relY = clampNumber(region.relY, 0, 1);
      return {
        id: region.id,
        relX,
        relY,
        width: clampNumber(region.width, 0, 1 - relX),
        height: clampNumber(region.height, 0, 1 - relY),
      };
    });
    const subtitleErase: SubtitleEraseMetadata = {
      sourceNodeId: sourceId,
      sourceLabel,
      sourcePosterUrl,
      mode,
      regions: normalizedRegions,
      edgeId,
      model: "volcano-subtitle-eraser",
      requestMode: mode === "smart" ? "Subtitle" : "Text",
    };
    const targetNode: Node = {
      id: targetId,
      type: "video",
      position: {
        x: sourcePosition.x + nodeWidth(source) + 120,
        y: sourcePosition.y,
      },
      width: dimensions.width,
      height: dimensions.height,
      style: dimensions,
      data: {
        filename: `视频一键去字幕-${sourceLabel}`,
        model: "volcano-subtitle-eraser",
        status: "pending",
        durationSeconds: sourceDuration,
        resolution:
          typeof source.data.resolution === "string"
            ? source.data.resolution
            : "1280 × 720",
        generatorType: "SUBTITLE_ERASE",
        subtitleErase,
      },
    };
    const subtitleEdge: Edge = {
      id: edgeId,
      source: sourceId,
      target: targetId,
      type: "default",
    };

    set((state) => {
      const currentCanvas = state.canvases.find(
        (item) => item.id === activeCanvasId,
      );
      if (!currentCanvas) return state;
      return {
        canvases: state.canvases.map((item) =>
          item.id === activeCanvasId
            ? {
                ...item,
                nodes: [...item.nodes, targetNode],
                edges: [...item.edges, subtitleEdge],
              }
            : item,
        ),
        selectedNodeIds: [targetId],
        selectedNodeId: targetId,
        selectedEdgeIds: [],
        historyByCanvas: pushHistory(state.historyByCanvas, currentCanvas),
      };
    });

    return targetId;
  },

  createAudioSplit: (sourceId: string, mode: AudioSplitMode) => {
    const { activeCanvasId } = get();
    const canvas = get().canvases.find((item) => item.id === activeCanvasId);
    const source = canvas?.nodes.find((node) => node.id === sourceId);
    if (!canvas || !source) return null;

    const sourceLabel =
      typeof source.data.filename === "string"
        ? source.data.filename
        : typeof source.data.title === "string"
          ? source.data.title
          : "视频";
    const sourceDuration =
      typeof source.data.durationSeconds === "number"
        ? source.data.durationSeconds
        : 30;
    const sourceResolution =
      typeof source.data.resolution === "string"
        ? source.data.resolution
        : "1280 × 720";
    const audioLabelByMode: Record<AudioSplitMode, string> = {
      av: "音轨",
      vocals: "人声",
      background: "背景音",
    };
    const audioDimensions = getDefaultNodeDimensions("audio");
    const videoDimensions = getDefaultNodeDimensions("video");
    const nodesById = new Map(canvas.nodes.map((node) => [node.id, node]));
    const sourcePosition = getAbsoluteNodePosition(source, nodesById);
    const audioNodeId = createNodeId("audio-split");
    const silentVideoNodeId = createNodeId("silent-video");
    const audioEdgeId = `e-${sourceId}-${audioNodeId}`;
    const silentVideoEdgeId = `e-${sourceId}-${silentVideoNodeId}`;
    const audioSplit: AudioSplitMetadata = {
      sourceNodeId: sourceId,
      sourceLabel,
      mode,
      outputKind: "audio",
      edgeId: audioEdgeId,
    };
    const silentVideoSplit: AudioSplitMetadata = {
      sourceNodeId: sourceId,
      sourceLabel,
      mode,
      outputKind: "silent-video",
      edgeId: silentVideoEdgeId,
    };
    const audioNode: Node = {
      id: audioNodeId,
      type: "audio",
      position: {
        x: sourcePosition.x + nodeWidth(source) + 120,
        y: sourcePosition.y,
      },
      width: audioDimensions.width,
      height: audioDimensions.height,
      style: audioDimensions,
      data: {
        filename: `${sourceLabel}_${audioLabelByMode[mode]}`,
        duration: formatDuration(sourceDuration),
        durationSeconds: sourceDuration,
        audioSplit,
      },
    };
    const silentVideoNode: Node = {
      id: silentVideoNodeId,
      type: "video",
      position: {
        x: audioNode.position.x + audioDimensions.width + 120,
        y: sourcePosition.y,
      },
      width: videoDimensions.width,
      height: videoDimensions.height,
      style: videoDimensions,
      data: {
        filename: `${sourceLabel}_无声`,
        model: "音视频分离",
        status: "pending",
        durationSeconds: sourceDuration,
        resolution: sourceResolution,
        generatorType: "AUDIO_SPLIT",
        audioSplit: silentVideoSplit,
      },
    };
    const outputEdges: Edge[] = [
      {
        id: audioEdgeId,
        source: sourceId,
        target: audioNodeId,
        type: "default",
      },
      {
        id: silentVideoEdgeId,
        source: sourceId,
        target: silentVideoNodeId,
        type: "default",
      },
    ];

    set((state) => {
      const currentCanvas = state.canvases.find(
        (item) => item.id === activeCanvasId,
      );
      if (!currentCanvas) return state;
      return {
        canvases: state.canvases.map((item) =>
          item.id === activeCanvasId
            ? {
                ...item,
                nodes: [...item.nodes, audioNode, silentVideoNode],
                edges: [...item.edges, ...outputEdges],
              }
            : item,
        ),
        selectedNodeIds: [silentVideoNodeId],
        selectedNodeId: silentVideoNodeId,
        selectedEdgeIds: [],
        historyByCanvas: pushHistory(state.historyByCanvas, currentCanvas),
      };
    });

    return { audioNodeId, silentVideoNodeId };
  },

  createVideoFrameCapture: (
    sourceId: string,
    kind: VideoFrameCaptureKind,
    captureSeconds = 0,
  ) => {
    const { activeCanvasId } = get();
    const canvas = get().canvases.find((item) => item.id === activeCanvasId);
    const source = canvas?.nodes.find((node) => node.id === sourceId);
    if (!canvas || !source) return null;

    const sourceLabel =
      typeof source.data.filename === "string"
        ? source.data.filename
        : typeof source.data.title === "string"
          ? source.data.title
          : "视频";
    const sourcePosterUrl =
      typeof source.data.posterUrl === "string"
        ? source.data.posterUrl
        : "/images/scene-coffee-4.png";
    const durationSeconds =
      typeof source.data.durationSeconds === "number"
        ? Math.max(0, source.data.durationSeconds)
        : 0;
    if (kind === "last" && durationSeconds <= 0) return null;

    const captureDefinition = {
      first: { name: "首帧", alt: "视频首帧" },
      last: { name: "尾帧", alt: "视频尾帧" },
      current: { name: "截图", alt: "视频截图" },
    } as const;
    const definition = captureDefinition[kind];
    const normalizedSeconds =
      kind === "first"
        ? 0
        : kind === "last"
          ? Math.max(durationSeconds - 0.05, 0)
          : clampNumber(
              captureSeconds,
              0,
              durationSeconds > 0 ? durationSeconds : Math.max(0, captureSeconds),
            );
    const dimensions = getDefaultNodeDimensions("image");
    const position = findAvailableRightSlot(
      source,
      canvas.nodes,
      dimensions,
      100,
    );
    const imageDimensions = parseVideoResolution(source.data.resolution);
    const targetId = createNodeId("video-frame");
    const edgeId = `e-${sourceId}-${targetId}`;
    const frameCapture: VideoFrameCaptureMetadata = {
      sourceNodeId: sourceId,
      sourceLabel,
      kind,
      captureSeconds: normalizedSeconds,
      name: definition.name,
      alt: definition.alt,
      edgeId,
    };
    const targetNode: Node = {
      id: targetId,
      type: "image",
      position,
      width: dimensions.width,
      height: dimensions.height,
      style: dimensions,
      data: {
        filename: definition.name,
        width: imageDimensions.width,
        height: imageDimensions.height,
        imageUrl: sourcePosterUrl,
        editorVariant: "empty",
        editorHeight: 191,
        generationSettings: "16:9 · 标准画质 · 2K · 1张",
        frameCapture,
      },
    };
    const frameEdge: Edge = {
      id: edgeId,
      source: sourceId,
      target: targetId,
      type: "default",
    };

    set((state) => {
      const currentCanvas = state.canvases.find(
        (item) => item.id === activeCanvasId,
      );
      if (!currentCanvas) return state;
      return {
        canvases: state.canvases.map((item) =>
          item.id === activeCanvasId
            ? {
                ...item,
                nodes: [...item.nodes, targetNode],
                edges: [...item.edges, frameEdge],
              }
            : item,
        ),
        selectedNodeIds: [sourceId],
        selectedNodeId: sourceId,
        selectedEdgeIds: [],
        historyByCanvas: pushHistory(state.historyByCanvas, currentCanvas),
      };
    });

    return targetId;
  },

  createDepthMotionCapture: (
    sourceId: string,
    resolution: DepthMotionCaptureResolution,
    requestedDurationSeconds: number,
  ) => {
    const { activeCanvasId } = get();
    const canvas = get().canvases.find((item) => item.id === activeCanvasId);
    const source = canvas?.nodes.find((node) => node.id === sourceId);
    if (!canvas || !source) return null;

    const sourceLabel =
      typeof source.data.filename === "string"
        ? source.data.filename
        : typeof source.data.title === "string"
          ? source.data.title
          : "视频";
    const durationSeconds =
      Number.isFinite(requestedDurationSeconds) && requestedDurationSeconds >= 0
        ? requestedDurationSeconds
        : typeof source.data.durationSeconds === "number"
          ? Math.max(0, source.data.durationSeconds)
          : 0;
    const sourceResolution =
      typeof source.data.resolution === "string"
        ? source.data.resolution
        : "1280 × 720";
    const dimensions = getDefaultNodeDimensions("video");
    const position = findAvailableRightSlot(
      source,
      canvas.nodes,
      dimensions,
      100,
    );
    const targetId = createNodeId("depth-motion");
    const edgeId = `e-${sourceId}-${targetId}`;
    const depthMotionCapture: DepthMotionCaptureMetadata = {
      sourceNodeId: sourceId,
      sourceLabel,
      resolution,
      durationSeconds,
      edgeId,
      model: "depth-motion-reference",
      requestMode: "DepthMap",
    };
    const targetNode: Node = {
      id: targetId,
      type: "video",
      position,
      width: dimensions.width,
      height: dimensions.height,
      style: dimensions,
      data: {
        filename: `深度动作捕捉-${sourceLabel}`,
        model: "depth-motion-reference",
        status: "pending",
        durationSeconds,
        resolution: sourceResolution,
        generatorType: "DEPTH_MOTION_CAPTURE",
        depthMotionCapture,
      },
    };
    const depthMotionEdge: Edge = {
      id: edgeId,
      source: sourceId,
      target: targetId,
      type: "default",
    };

    set((state) => {
      const currentCanvas = state.canvases.find(
        (item) => item.id === activeCanvasId,
      );
      if (!currentCanvas) return state;
      return {
        canvases: state.canvases.map((item) =>
          item.id === activeCanvasId
            ? {
                ...item,
                nodes: [...item.nodes, targetNode],
                edges: [...item.edges, depthMotionEdge],
              }
            : item,
        ),
        selectedNodeIds: [sourceId],
        selectedNodeId: sourceId,
        selectedEdgeIds: [],
        historyByCanvas: pushHistory(state.historyByCanvas, currentCanvas),
      };
    });

    return targetId;
  },

  createLongVideoProcess: (
    sourceId: string,
    input: LongVideoProcessInput,
  ) => {
    const { activeCanvasId } = get();
    const canvas = get().canvases.find((item) => item.id === activeCanvasId);
    const source = canvas?.nodes.find((node) => node.id === sourceId);
    if (!canvas || !source) return null;

    const sourceLabel =
      typeof source.data.filename === "string"
        ? source.data.filename
        : typeof source.data.title === "string"
          ? source.data.title
          : "视频";
    const processId = createNodeId("long-video");
    const origin = findAvailableLongVideoOrigin(source, canvas.nodes);
    const normalizedInput: LongVideoProcessInput = {
      prompt: input.prompt.trim(),
      model: input.model,
      ratio: input.ratio,
      resolution: input.resolution,
      durationSeconds: clampNumber(input.durationSeconds, 30, 300),
      audio: input.audio,
      credits: Math.max(0, Math.round(input.credits)),
      referenceCount: clampNumber(
        Math.round(input.referenceCount),
        0,
        20,
      ),
    };
    const dimensionsByStage: Record<
      LongVideoProcessStage,
      { width: number; height: number }
    > = {
      material: { width: 220, height: 128 },
      shot: { width: 236, height: 128 },
      candidate: { width: 236, height: 132 },
      assembly: { width: 210, height: 116 },
      final: { width: 300, height: 169 },
    };
    const makeProcessNode = ({
      stage,
      stageIndex,
      x,
      y,
      title,
      subtitle,
      imageUrl,
      batchIndex,
    }: {
      stage: LongVideoProcessStage;
      stageIndex: number;
      x: number;
      y: number;
      title: string;
      subtitle: string;
      imageUrl?: string;
      batchIndex?: number;
    }): Node => {
      const dimensions = dimensionsByStage[stage];
      const longVideoProcess: LongVideoProcessMetadata = {
        ...normalizedInput,
        sourceNodeId: sourceId,
        sourceLabel,
        processId,
        stage,
        stageIndex,
        batchIndex,
        status: "pending",
      };
      return {
        id: `${processId}-${stage}-${stageIndex}`,
        type: "long-video-process",
        position: { x: origin.x + x, y: origin.y + y },
        width: dimensions.width,
        height: dimensions.height,
        style: dimensions,
        data: {
          title,
          subtitle,
          imageUrl,
          longVideoProcess,
        },
      };
    };

    const materialNodes = [
      makeProcessNode({
        stage: "material",
        stageIndex: 1,
        x: 0,
        y: 0,
        title: "角色参考",
        subtitle: "陈默 · 图片 1",
        imageUrl: "/images/scene-coffee-1.png",
      }),
      makeProcessNode({
        stage: "material",
        stageIndex: 2,
        x: 0,
        y: 164,
        title: "道具参考",
        subtitle: "咖啡 · 图片 2",
        imageUrl: "/images/scene-coffee-2.png",
      }),
      makeProcessNode({
        stage: "material",
        stageIndex: 3,
        x: 0,
        y: 328,
        title: "场景参考",
        subtitle: "咖啡馆 · 图片 3",
        imageUrl: "/images/scene-coffee-4.png",
      }),
    ];
    const shotNodes = [
      makeProcessNode({
        stage: "shot",
        stageIndex: 1,
        x: 320,
        y: 0,
        title: "S01 · 对峙开场",
        subtitle: "镜头计划 · 等待生成",
        imageUrl: "/images/storyboard-2.png",
      }),
      makeProcessNode({
        stage: "shot",
        stageIndex: 2,
        x: 320,
        y: 164,
        title: "S02 · 情绪推进",
        subtitle: "镜头计划 · 等待生成",
        imageUrl: "/images/scene-coffee-3.png",
      }),
      makeProcessNode({
        stage: "shot",
        stageIndex: 3,
        x: 320,
        y: 328,
        title: "S03 · 结尾特写",
        subtitle: "镜头计划 · 等待生成",
        imageUrl: "/images/scene-coffee-1.png",
      }),
    ];
    const candidateNodes = [
      makeProcessNode({
        stage: "candidate",
        stageIndex: 1,
        batchIndex: 1,
        x: 700,
        y: 76,
        title: "候选 A1",
        subtitle: "批次 1 · 等待生成",
        imageUrl: "/images/scene-coffee-4.png",
      }),
      makeProcessNode({
        stage: "candidate",
        stageIndex: 2,
        batchIndex: 1,
        x: 700,
        y: 276,
        title: "候选 A2",
        subtitle: "批次 1 · 等待生成",
        imageUrl: "/images/scene-coffee-3.png",
      }),
      makeProcessNode({
        stage: "candidate",
        stageIndex: 3,
        batchIndex: 2,
        x: 986,
        y: 76,
        title: "候选 B1",
        subtitle: "批次 2 · 等待生成",
        imageUrl: "/images/scene-coffee-1.png",
      }),
      makeProcessNode({
        stage: "candidate",
        stageIndex: 4,
        batchIndex: 2,
        x: 986,
        y: 276,
        title: "候选 B2",
        subtitle: "批次 2 · 等待生成",
        imageUrl: "/images/storyboard-2.png",
      }),
    ];
    const assemblyNode = makeProcessNode({
      stage: "assembly",
      stageIndex: 1,
      x: 1280,
      y: 170,
      title: "候选汇聚",
      subtitle: "等待镜头选择与拼接",
    });
    const finalNode = makeProcessNode({
      stage: "final",
      stageIndex: 1,
      x: 1590,
      y: 144,
      title: "最终成片",
      subtitle: `${normalizedInput.durationSeconds}s · 等待拼接`,
      imageUrl: "/images/scene-coffee-4.png",
    });
    const processNodes = [
      ...materialNodes,
      ...shotNodes,
      ...candidateNodes,
      assemblyNode,
      finalNode,
    ];
    const makeEdge = (edgeSource: string, target: string): Edge => ({
      id: `e-${processId}-${edgeSource}-${target}`,
      source: edgeSource,
      target,
      type: "default",
    });
    const processEdges: Edge[] = [
      ...shotNodes.map((shot) => makeEdge(sourceId, shot.id)),
      makeEdge(materialNodes[0].id, shotNodes[0].id),
      makeEdge(materialNodes[0].id, shotNodes[1].id),
      makeEdge(materialNodes[1].id, shotNodes[0].id),
      makeEdge(materialNodes[1].id, shotNodes[2].id),
      makeEdge(materialNodes[2].id, shotNodes[1].id),
      makeEdge(materialNodes[2].id, shotNodes[2].id),
      makeEdge(shotNodes[0].id, candidateNodes[0].id),
      makeEdge(shotNodes[0].id, candidateNodes[2].id),
      makeEdge(shotNodes[1].id, candidateNodes[0].id),
      makeEdge(shotNodes[1].id, candidateNodes[1].id),
      makeEdge(shotNodes[1].id, candidateNodes[2].id),
      makeEdge(shotNodes[1].id, candidateNodes[3].id),
      makeEdge(shotNodes[2].id, candidateNodes[1].id),
      makeEdge(shotNodes[2].id, candidateNodes[3].id),
      ...candidateNodes.map((candidate) =>
        makeEdge(candidate.id, assemblyNode.id),
      ),
      makeEdge(assemblyNode.id, finalNode.id),
    ];

    set((state) => {
      const currentCanvas = state.canvases.find(
        (item) => item.id === activeCanvasId,
      );
      if (!currentCanvas) return state;
      return {
        canvases: state.canvases.map((item) =>
          item.id === activeCanvasId
            ? {
                ...item,
                nodes: [...item.nodes, ...processNodes],
                edges: [...item.edges, ...processEdges],
              }
            : item,
        ),
        selectedNodeIds: [sourceId],
        selectedNodeId: sourceId,
        selectedEdgeIds: [],
        historyByCanvas: pushHistory(state.historyByCanvas, currentCanvas),
      };
    });

    return processId;
  },

  createSmartMatting: (sourceId: string) => {
    const { activeCanvasId } = get();
    const canvas = get().canvases.find((item) => item.id === activeCanvasId);
    const source = canvas?.nodes.find((node) => node.id === sourceId);
    if (!canvas || !source) return null;

    const sourceLabel =
      typeof source.data.filename === "string"
        ? source.data.filename
        : typeof source.data.title === "string"
          ? source.data.title
          : "视频";
    const sourcePosterUrl =
      typeof source.data.posterUrl === "string"
        ? source.data.posterUrl
        : undefined;
    const duration =
      typeof source.data.durationSeconds === "number"
        ? Math.max(0, source.data.durationSeconds)
        : 0;
    const resolution =
      typeof source.data.resolution === "string"
        ? source.data.resolution
        : "1280 × 720";
    const mediaDimensions = parseVideoResolution(resolution);
    const dimensions = getDefaultNodeDimensions("video");
    const position = findAvailableRightSlot(
      source,
      canvas.nodes,
      dimensions,
      100,
    );
    const targetId = createNodeId("smart-matting");
    const edgeId = `e-${sourceId}-${targetId}`;
    const smartMatting: SmartMattingMetadata = {
      sourceNodeId: sourceId,
      sourceLabel,
      sourcePosterUrl,
      edgeId,
      provider: "volcano",
      taskType: "video",
      model: "volcano-portrait-matting",
      format: "WEBM",
      width: mediaDimensions.width,
      height: mediaDimensions.height,
      duration,
      generatorType: "PICTURE_EDIT",
      isSmartMattingOutput: true,
    };
    const targetNode: Node = {
      id: targetId,
      type: "video",
      position,
      width: dimensions.width,
      height: dimensions.height,
      style: dimensions,
      data: {
        filename: `${sourceLabel}-智能抠像`,
        model: "volcano-portrait-matting",
        status: "pending",
        durationSeconds: duration,
        resolution,
        generatorType: "PICTURE_EDIT",
        isSmartMattingOutput: true,
        smartMatting,
      },
    };
    const mattingEdge: Edge = {
      id: edgeId,
      source: sourceId,
      target: targetId,
      type: "default",
    };

    set((state) => {
      const currentCanvas = state.canvases.find(
        (item) => item.id === activeCanvasId,
      );
      if (!currentCanvas) return state;
      return {
        canvases: state.canvases.map((item) =>
          item.id === activeCanvasId
            ? {
                ...item,
                nodes: [...item.nodes, targetNode],
                edges: [...item.edges, mattingEdge],
              }
            : item,
        ),
        selectedNodeIds: [sourceId],
        selectedNodeId: sourceId,
        selectedEdgeIds: [],
        historyByCanvas: pushHistory(state.historyByCanvas, currentCanvas),
      };
    });

    return targetId;
  },

  createPictureEdit: (
    sourceId: string,
    mode: PictureEditAction,
    marks: PictureEditMark[],
  ) => {
    const { activeCanvasId } = get();
    const canvas = get().canvases.find((item) => item.id === activeCanvasId);
    const source = canvas?.nodes.find((node) => node.id === sourceId);
    if (!canvas || !source || marks.length === 0) return null;

    const sourceLabel =
      typeof source.data.filename === "string"
        ? source.data.filename
        : typeof source.data.title === "string"
          ? source.data.title
          : "视频";
    const sourcePosterUrl =
      typeof source.data.posterUrl === "string"
        ? source.data.posterUrl
        : undefined;
    const duration =
      typeof source.data.durationSeconds === "number"
        ? Math.max(0, source.data.durationSeconds)
        : 0;
    const resolution =
      typeof source.data.resolution === "string"
        ? source.data.resolution
        : "1280 × 720";
    const mediaDimensions = parseVideoResolution(resolution);
    const dimensions = getDefaultNodeDimensions("video");
    const position = findAvailableRightSlot(
      source,
      canvas.nodes,
      dimensions,
      100,
    );
    const targetId = createNodeId("picture-edit");
    const edgeId = `e-${sourceId}-${targetId}`;
    const normalizedMarks = marks.map((mark) => ({
      ...mark,
      relX: clampNumber(mark.relX, 0, 1),
      relY: clampNumber(mark.relY, 0, 1),
      width: clampNumber(mark.width, 0, 1),
      height: clampNumber(mark.height, 0, 1),
      points: mark.points?.map((point) => ({
        x: clampNumber(point.x, 0, 1),
        y: clampNumber(point.y, 0, 1),
      })),
      replacement: mark.replacement
        ? { ...mark.replacement }
        : undefined,
    }));
    const pictureEdit: PictureEditMetadata = {
      sourceNodeId: sourceId,
      sourceLabel,
      sourcePosterUrl,
      mode,
      marks: normalizedMarks,
      edgeId,
      model: "volcano-picture-editor",
      requestMode:
        mode === "subjectRemove"
          ? "Remove"
          : mode === "subjectModify"
            ? "Modify"
            : "Replace",
    };
    const modeLabel =
      mode === "subjectRemove"
        ? "主体消除"
        : mode === "subjectModify"
          ? "主体修改"
          : "主体替换";
    const targetNode: Node = {
      id: targetId,
      type: "video",
      position,
      width: dimensions.width,
      height: dimensions.height,
      style: dimensions,
      data: {
        filename: `${modeLabel}-${sourceLabel}`,
        model: "volcano-picture-editor",
        status: "pending",
        durationSeconds: duration,
        resolution,
        generatorType: "PICTURE_EDIT",
        isPictureEditOutput: true,
        pictureEdit,
        sourceWidth: mediaDimensions.width,
        sourceHeight: mediaDimensions.height,
      },
    };
    const pictureEditEdge: Edge = {
      id: edgeId,
      source: sourceId,
      target: targetId,
      type: "default",
    };

    set((state) => {
      const currentCanvas = state.canvases.find(
        (item) => item.id === activeCanvasId,
      );
      if (!currentCanvas) return state;
      return {
        canvases: state.canvases.map((item) =>
          item.id === activeCanvasId
            ? {
                ...item,
                nodes: [...item.nodes, targetNode],
                edges: [...item.edges, pictureEditEdge],
              }
            : item,
        ),
        selectedNodeIds: [sourceId],
        selectedNodeId: sourceId,
        selectedEdgeIds: [],
        historyByCanvas: pushHistory(state.historyByCanvas, currentCanvas),
      };
    });

    return targetId;
  },

  createDirectorCapture: (
    sourceId: string,
    capture: Omit<DirectorCaptureMetadata, "sourceNodeId" | "edgeId"> & {
      dataUrl: string;
    },
  ) => {
    const { activeCanvasId } = get();
    const canvas = get().canvases.find((item) => item.id === activeCanvasId);
    const source = canvas?.nodes.find((node) => node.id === sourceId);
    if (!canvas || !source || !capture.dataUrl) return null;

    const dimensions = getDefaultNodeDimensions("image");
    const position = findAvailableRightSlot(source, canvas.nodes, dimensions, 100);
    const targetId = createNodeId("director-capture");
    const edgeId = `e-${sourceId}-${targetId}`;
    const directorCapture: DirectorCaptureMetadata = {
      sourceNodeId: sourceId,
      captureId: capture.captureId,
      cameraId: capture.cameraId,
      cameraName: capture.cameraName,
      aspectRatio: capture.aspectRatio,
      width: capture.width,
      height: capture.height,
      createdAt: capture.createdAt,
      edgeId,
    };
    const targetNode: Node = {
      id: targetId,
      type: "image",
      position,
      width: dimensions.width,
      height: dimensions.height,
      style: dimensions,
      data: {
        filename: `导演台截图-${capture.cameraName}`,
        width: capture.width,
        height: capture.height,
        imageUrl: capture.dataUrl,
        editorVariant: "empty",
        editorHeight: 191,
        generationSettings: `${capture.aspectRatio} · 导演台构图参考`,
        directorCapture,
      },
    };
    const edge: Edge = {
      id: edgeId,
      source: sourceId,
      target: targetId,
      type: "default",
    };

    set((state) => {
      const currentCanvas = state.canvases.find((item) => item.id === activeCanvasId);
      if (!currentCanvas) return state;
      return {
        canvases: state.canvases.map((item) =>
          item.id === activeCanvasId
            ? { ...item, nodes: [...item.nodes, targetNode], edges: [...item.edges, edge] }
            : item,
        ),
        selectedNodeIds: [targetId],
        selectedNodeId: targetId,
        selectedEdgeIds: [],
        historyByCanvas: pushHistory(state.historyByCanvas, currentCanvas),
      };
    });

    return targetId;
  },

  createDirectorAnimationExport: (
    sourceId: string,
    animation: Omit<
      DirectorAnimationExportMetadata,
      "sourceNodeId" | "edgeId"
    > & {
      videoUrl: string;
      posterDataUrl: string;
    },
  ) => {
    const { activeCanvasId } = get();
    const canvas = get().canvases.find((item) => item.id === activeCanvasId);
    const source = canvas?.nodes.find((node) => node.id === sourceId);
    if (
      !canvas ||
      !source ||
      !animation.videoUrl ||
      animation.sizeBytes <= 0
    ) {
      return null;
    }

    const dimensions = getDirectorAnimationExportNodeDimensions(
      animation.aspectRatio,
    );
    const position = findAvailableRightSlot(
      source,
      canvas.nodes,
      dimensions,
      100,
    );
    const targetId = createNodeId("director-animation-export");
    const edgeId = `e-${sourceId}-${targetId}`;
    const directorAnimationExport: DirectorAnimationExportMetadata = {
      sourceNodeId: sourceId,
      exportId: animation.exportId,
      sceneName: animation.sceneName,
      cameraId: animation.cameraId,
      cameraName: animation.cameraName,
      aspectRatio: animation.aspectRatio,
      width: animation.width,
      height: animation.height,
      durationSeconds: animation.durationSeconds,
      mimeType: animation.mimeType,
      sizeBytes: animation.sizeBytes,
      createdAt: animation.createdAt,
      edgeId,
    };
    const targetNode: Node = {
      id: targetId,
      type: "video",
      position,
      width: dimensions.width,
      height: dimensions.height,
      style: dimensions,
      data: {
        filename: `${animation.sceneName} 动画导出`,
        model: "3D导演台",
        status: "ready",
        durationSeconds: animation.durationSeconds,
        resolution: `${animation.width} × ${animation.height}`,
        posterUrl: animation.posterDataUrl,
        videoUrl: animation.videoUrl,
        directorAnimationExport,
      },
    };
    const edge: Edge = {
      id: edgeId,
      source: sourceId,
      target: targetId,
      type: "default",
    };

    set((state) => {
      const currentCanvas = state.canvases.find(
        (item) => item.id === activeCanvasId,
      );
      if (!currentCanvas) return state;
      return {
        canvases: state.canvases.map((item) =>
          item.id === activeCanvasId
            ? {
                ...item,
                nodes: [...item.nodes, targetNode],
                edges: [...item.edges, edge],
              }
            : item,
        ),
        selectedNodeIds: [targetId],
        selectedNodeId: targetId,
        selectedEdgeIds: [],
        historyByCanvas: pushHistory(state.historyByCanvas, currentCanvas),
      };
    });

    return targetId;
  },

  clearVideoContinuation: (targetId: string) => {
    const { activeCanvasId } = get();
    set((state) => {
      const currentCanvas = state.canvases.find(
        (canvas) => canvas.id === activeCanvasId,
      );
      const target = currentCanvas?.nodes.find((node) => node.id === targetId);
      const continuation = target?.data.continuation;
      if (
        !currentCanvas ||
        !target ||
        !isVideoContinuationMetadata(continuation)
      ) {
        return state;
      }

      return {
        canvases: state.canvases.map((canvas) =>
          canvas.id === activeCanvasId
            ? {
                ...canvas,
                nodes: canvas.nodes.map((node) => {
                  if (node.id !== targetId) return node;
                  const nextData = { ...node.data };
                  delete nextData.continuation;
                  return { ...node, data: nextData };
                }),
                edges: canvas.edges.filter(
                  (edge) => edge.id !== continuation.edgeId,
                ),
              }
            : canvas,
        ),
        historyByCanvas: pushHistory(state.historyByCanvas, currentCanvas),
      };
    });
  },

  completeShotBreakdown: (
    sourceId: string,
    dimensions: ShotBreakdownDimension[],
  ) => {
    const { activeCanvasId } = get();
    set((state) => {
      const currentCanvas = state.canvases.find(
        (canvas) => canvas.id === activeCanvasId,
      );
      const source = currentCanvas?.nodes.find((node) => node.id === sourceId);
      if (!currentCanvas || !source) return state;

      const existingResults = currentCanvas.nodes.filter(
        (node) =>
          node.type === "shot-breakdown-result" &&
          node.data.sourceBreakdownId === sourceId,
      );
      if (existingResults.length > 0) return state;

      const activeDimensions = new Set(dimensions);
      const definitions = SHOT_BREAKDOWN_RESULT_DEFINITIONS.filter(
        (definition) => activeDimensions.has(definition.category),
      );
      if (definitions.length === 0) return state;

      const nodesById = new Map(
        currentCanvas.nodes.map((node) => [node.id, node]),
      );
      const sourcePosition = getAbsoluteNodePosition(source, nodesById);
      const resultX = sourcePosition.x + nodeWidth(source) + 120;
      let resultY = sourcePosition.y - 80;

      const resultNodes = definitions.map((definition) => {
        const nodeId = createNodeId("shot-breakdown-result");
        const node: Node = {
          id: nodeId,
          type: "shot-breakdown-result",
          position: { x: resultX, y: resultY },
          width: definition.dimensions.width,
          height: definition.dimensions.height,
          style: { ...definition.dimensions },
          data: {
            resultKey: definition.key,
            category: definition.category,
            title: definition.title,
            items: definition.items,
            sourceBreakdownId: sourceId,
          },
        };
        resultY += definition.dimensions.height + 48;
        return node;
      });
      const resultIds = resultNodes.map((node) => node.id);
      const resultEdges: Edge[] = resultNodes.map((node) => ({
        id: `e-${sourceId}-${node.id}`,
        source: sourceId,
        target: node.id,
        type: "default",
      }));
      const nextNodes = currentCanvas.nodes
        .map((node) =>
          node.id === sourceId
            ? {
                ...node,
                data: {
                  ...node.data,
                  status: "complete",
                  resultNodeIds: resultIds,
                },
              }
            : node,
        )
        .concat(resultNodes);

      return {
        canvases: state.canvases.map((canvas) =>
          canvas.id === activeCanvasId
            ? {
                ...canvas,
                nodes: nextNodes,
                edges: [...canvas.edges, ...resultEdges],
              }
            : canvas,
        ),
        selectedNodeIds: [resultIds[0]],
        selectedNodeId: resultIds[0],
        selectedEdgeIds: [],
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
        selectedEdgeIds: [],
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
        selectedEdgeIds: [],
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
      const nextEdges = currentCanvas.edges.filter(
        (edge) => !removedIds.has(edge.source) && !removedIds.has(edge.target),
      );
      const nextEdgeIds = new Set(nextEdges.map((edge) => edge.id));
      return {
        canvases: state.canvases.map((canvas) =>
          canvas.id === activeCanvasId
            ? {
                ...canvas,
                nodes: canvas.nodes.filter((node) => !removedIds.has(node.id)),
                edges: nextEdges,
              }
            : canvas,
        ),
        selectedNodeIds: nextSelectedNodeIds,
        selectedNodeId: nextSelectedNodeIds.at(-1) ?? null,
        selectedEdgeIds: state.selectedEdgeIds.filter((id) => nextEdgeIds.has(id)),
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
        selectedEdgeIds: [],
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
        selectedEdgeIds: [],
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
        selectedEdgeIds: [],
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
      const storedNodes = nodes.map(withoutStoredNodeSelection);
      const availableIds = new Set(storedNodes.map((node) => node.id));
      const nextSelectedNodeIds = state.selectedNodeIds.filter((id) =>
        availableIds.has(id),
      );
      return {
        canvases: state.canvases.map((canvas) =>
          canvas.id === activeCanvasId
            ? { ...canvas, nodes: storedNodes }
            : canvas,
        ),
        selectedNodeIds: nextSelectedNodeIds,
        selectedNodeId: nextSelectedNodeIds.at(-1) ?? null,
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
      const storedEdges = edges.map(withoutStoredEdgeSelection);
      const availableIds = new Set(storedEdges.map((edge) => edge.id));
      return {
        canvases: state.canvases.map((canvas) =>
          canvas.id === activeCanvasId
            ? { ...canvas, edges: storedEdges }
            : canvas,
        ),
        selectedEdgeIds: state.selectedEdgeIds.filter((id) =>
          availableIds.has(id),
        ),
        historyByCanvas:
          options?.recordHistory
            ? pushHistory(state.historyByCanvas, currentCanvas, options.historySnapshot)
            : state.historyByCanvas,
      };
    });
  },

  selectNode: (nodeId: string | null) => {
    const currentState = get();
    const activeCanvas = currentState.getActiveCanvas();
    const validNodeId =
      nodeId && activeCanvas?.nodes.some((node) => node.id === nodeId)
        ? nodeId
        : null;
    const nextSelectedNodeIds = validNodeId ? [validNodeId] : [];
    if (
      currentState.selectedNodeId === validNodeId &&
      currentState.selectedNodeIds.length === nextSelectedNodeIds.length &&
      currentState.selectedNodeIds.every(
        (id, index) => id === nextSelectedNodeIds[index],
      ) &&
      currentState.selectedEdgeIds.length === 0
    ) {
      return;
    }
    set({
      selectedNodeIds: nextSelectedNodeIds,
      selectedNodeId: validNodeId,
      selectedEdgeIds: [],
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
      currentState.selectedNodeId === (uniqueIds.at(-1) ?? null) &&
      currentState.selectedEdgeIds.length === 0
    ) {
      return;
    }
    set({
      selectedNodeIds: uniqueIds,
      selectedNodeId: uniqueIds.at(-1) ?? null,
      selectedEdgeIds: [],
    });
  },

  selectEdges: (edgeIds: string[]) => {
    const activeCanvas = get().getActiveCanvas();
    const availableIds = new Set(activeCanvas?.edges.map((edge) => edge.id) ?? []);
    const uniqueIds = Array.from(new Set(edgeIds)).filter((id) =>
      availableIds.has(id),
    );
    const currentState = get();
    if (
      currentState.selectedEdgeIds.length === uniqueIds.length &&
      currentState.selectedEdgeIds.every((id, index) => id === uniqueIds[index])
    ) {
      return;
    }
    set({ selectedEdgeIds: uniqueIds });
  },

  selectElements: ({ nodeIds, edgeIds }) => {
    const currentState = get();
    const activeCanvas = currentState.getActiveCanvas();
    const availableNodeIds = new Set(
      activeCanvas?.nodes.map((node) => node.id) ?? [],
    );
    const availableEdgeIds = new Set(
      activeCanvas?.edges.map((edge) => edge.id) ?? [],
    );
    const nextSelectedNodeIds = Array.from(new Set(nodeIds)).filter((id) =>
      availableNodeIds.has(id),
    );
    const nextSelectedEdgeIds = Array.from(new Set(edgeIds)).filter((id) =>
      availableEdgeIds.has(id),
    );
    if (
      currentState.selectedNodeIds.length === nextSelectedNodeIds.length &&
      currentState.selectedNodeIds.every(
        (id, index) => id === nextSelectedNodeIds[index],
      ) &&
      currentState.selectedEdgeIds.length === nextSelectedEdgeIds.length &&
      currentState.selectedEdgeIds.every(
        (id, index) => id === nextSelectedEdgeIds[index],
      ) &&
      currentState.selectedNodeId === (nextSelectedNodeIds.at(-1) ?? null)
    ) {
      return;
    }
    set({
      selectedNodeIds: nextSelectedNodeIds,
      selectedNodeId: nextSelectedNodeIds.at(-1) ?? null,
      selectedEdgeIds: nextSelectedEdgeIds,
    });
  },

  routeReactFlowChanges: (request) => {
    const nodeChangeCount = request.nodeChanges?.length ?? 0;
    const edgeChangeCount = request.edgeChanges?.length ?? 0;
    let result: LibTVReactFlowChangeRoutingResult = {
      status: "rejected",
      code: "ACTIVE_CANVAS_CHANGED",
      expectedActiveCanvasId: request.expectedActiveCanvasId,
      activeCanvasId: get().activeCanvasId,
      nodeChangeCount,
      edgeChangeCount,
    };

    set((state) => {
      if (state.activeCanvasId !== request.expectedActiveCanvasId) {
        result = {
          ...result,
          activeCanvasId: state.activeCanvasId,
        };
        return state;
      }

      const currentCanvas = state.canvases.find(
        (canvas) => canvas.id === state.activeCanvasId,
      );
      if (!currentCanvas) return state;

      const plan = planLibTVReactFlowChanges(
        {
          activeCanvasId: state.activeCanvasId,
          nodes: currentCanvas.nodes,
          edges: currentCanvas.edges,
          selectedNodeIds: state.selectedNodeIds,
          selectedEdgeIds: state.selectedEdgeIds,
        },
        request,
      );

      if (plan.status === "reject") {
        result = {
          status: "rejected",
          code: plan.code,
          expectedActiveCanvasId: request.expectedActiveCanvasId,
          activeCanvasId: state.activeCanvasId,
          nodeChangeCount,
          edgeChangeCount,
          changeIndex: plan.changeIndex,
          elementId: plan.elementId,
        };
        return state;
      }

      result = {
        status: "applied",
        code: plan.code,
        expectedActiveCanvasId: request.expectedActiveCanvasId,
        activeCanvasId: state.activeCanvasId,
        nodeChangeCount,
        edgeChangeCount,
      };
      return {
        canvases: plan.hasTransport
          ? state.canvases.map((canvas) =>
              canvas.id === state.activeCanvasId
                ? {
                    ...canvas,
                    nodes: plan.nextNodes.map(withoutStoredNodeSelection),
                  }
                : canvas,
            )
          : state.canvases,
        selectedNodeIds: plan.nextSelectedNodeIds,
        selectedNodeId: plan.nextSelectedNodeIds.at(-1) ?? null,
        selectedEdgeIds: plan.nextSelectedEdgeIds,
      };
    });

    if (typeof window !== "undefined") {
      window.__libtv_react_flow_change_log = [
        ...window.__libtv_react_flow_change_log,
        { request, result },
      ].slice(-100);
    }
    return result;
  },

  addEdge: (edge: Edge) => {
    let result: LibTVConnectionValidationResult = {
      status: "reject",
      reason: "DANGLING_ENDPOINT",
    };
    set((state) => {
      const currentCanvas = state.canvases.find(
        (canvas) => canvas.id === state.activeCanvasId,
      );
      if (!currentCanvas) return state;
      result = validateLibTVGraphConnection(
        proposedLibTVConnectionFromEdge(edge, "programmatic"),
        currentCanvas.nodes,
        currentCanvas.edges,
      );
      if (result.status === "reject") return state;

      const normalizedEdge = withoutStoredEdgeSelection({
        ...edge,
        source: result.connection.sourceNodeId,
        sourceHandle: result.connection.sourceHandleId,
        target: result.connection.targetNodeId,
        targetHandle: result.connection.targetHandleId,
      });
      return {
        canvases: state.canvases.map((canvas) =>
          canvas.id === state.activeCanvasId
            ? { ...canvas, edges: [...canvas.edges, normalizedEdge] }
            : canvas,
        ),
        historyByCanvas: pushHistory(state.historyByCanvas, currentCanvas),
      };
    });
    return result;
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
        selectedEdgeIds: state.selectedEdgeIds.filter((id) => id !== edgeId),
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
        selectedEdgeIds: [],
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
        selectedEdgeIds: [],
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

declare global {
  interface Window {
    __libtv_store: typeof useCanvasStore;
    __libtv_validate_connection: (
      proposal: ProposedLibTVConnection,
    ) => LibTVConnectionValidationResult;
    __libtv_route_react_flow_changes: (
      request: LibTVReactFlowChangeRoutingRequest,
    ) => LibTVReactFlowChangeRoutingResult;
    __libtv_react_flow_change_log: Array<{
      request: LibTVReactFlowChangeRoutingRequest;
      result: LibTVReactFlowChangeRoutingResult;
    }>;
  }
}

if (typeof window !== "undefined") {
  window.__libtv_store = useCanvasStore;
  window.__libtv_react_flow_change_log = [];
  window.__libtv_route_react_flow_changes = (request) =>
    useCanvasStore.getState().routeReactFlowChanges(request);
  window.__libtv_validate_connection = (proposal) => {
    const canvas = useCanvasStore.getState().getActiveCanvas();
    return validateLibTVGraphConnection(
      proposal,
      canvas?.nodes ?? [],
      canvas?.edges ?? [],
    );
  };
}

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
    case "shot-breakdown-result":
      return { width: 1040, height: 680 };
    case "video-clip":
      return { width: 350, height: 350 };
    case "audio":
      return { width: 350, height: 140 };
    case "long-video-process":
      return { width: 236, height: 132 };
    default:
      return { width: 350, height: 180 };
  }
}

function getDirectorAnimationExportNodeDimensions(
  aspectRatio: DirectorAnimationExportMetadata["aspectRatio"],
): { width: number; height: number } {
  if (aspectRatio === "9:16") return { width: 324, height: 576 };
  if (aspectRatio === "1:1") return { width: 420, height: 420 };
  return { width: 512, height: 288 };
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

function clampNumber(value: number, minimum: number, maximum: number) {
  return Math.min(maximum, Math.max(minimum, value));
}

function formatDuration(durationSeconds: number) {
  const totalSeconds = Math.max(0, Math.round(durationSeconds));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
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
