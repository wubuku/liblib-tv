import type { Node } from "@xyflow/react";

export type FrameosNodeKind =
  | "text"
  | "image"
  | "video"
  | "character"
  | "scene"
  | "audio"
  | "style"
  | "batch";

export interface FrameosNodeData extends Record<string, unknown> {
  title: string;             // "文本节点1" / "视频节点1" / ...
  content?: string;          // 文本节点显示文本
  imageUrl?: string;         // 图片/视频封面 URL
  reviewFailed?: boolean;    // 视频节点显示 "审核未通过" 徽章
  // 类型专属
  age?: number;              // character: 角色年龄
  description?: string;      // character / scene / style: 描述
  duration?: number;         // audio: 时长 (秒)
  batchSize?: number;        // batch: 批量数量
}

export type FrameosNode = Node<FrameosNodeData, FrameosNodeKind>;
