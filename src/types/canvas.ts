export interface CanvasNode {
  id: string;
  type: CanvasNodeType;
  position: { x: number; y: number };
  data: Record<string, unknown>;
  width?: number;
  height?: number;
}

export type CanvasNodeType =
  | "script"
  | "image"
  | "storyboard"
  | "scriptExecution"
  | "text";

export interface ScriptNodeData {
  title: string;
  content: string;
  characterCount?: number;
}

export interface ImageNodeData {
  filename: string;
  src: string;
  alt: string;
  width: number;
  height: number;
  hasWatermark?: boolean;
}

export interface StoryboardGroupData {
  label: string;
  images: ImageNodeData[];
  episode?: string;
}

export interface ScriptExecutionStep {
  id: string;
  label: string;
  icon?: string;
  status: "pending" | "active" | "completed";
}

export interface ScriptExecutionNodeData {
  title: string;
  steps: ScriptExecutionStep[];
  actionLabel?: string;
}

export interface CanvasEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  type?: "default" | "smoothstep" | "bezier";
  animated?: boolean;
  label?: string;
}

export interface Project {
  id: string;
  name: string;
  spaceId: string;
  canvases: Canvas[];
}

export interface Canvas {
  id: string;
  name: string;
  nodes: CanvasNode[];
  edges: CanvasEdge[];
  viewport: {
    x: number;
    y: number;
    zoom: number;
  };
}

export interface UserProfile {
  id: string;
  name: string;
  avatar: string;
  credits: number;
  isVip: boolean;
  vipLevel?: number;
}

export interface NavItem {
  id: string;
  label: string;
  icon: string;
  shortcut?: string;
  action: () => void;
}

export interface ToolbarItem {
  id: string;
  label: string;
  icon: string;
  shortcut?: string;
  isActive?: boolean;
  action: () => void;
}
