import type { Node } from "@xyflow/react";

/**
 * 即梦 (jimeng.jianying.com) AI 画布复刻的节点类型。
 *
 * 证据: docs/research/jimeng-canvas/README.md
 * 源站画布为 React Flow (xyflow v12)，节点类型名 "video" 等；
 * 本文件是复刻侧的类型契约（CLONE_DECISION 命名加 Jimeng 前缀）。
 */

export type JimengNodeKind = "video" | "image" | "text";

export interface JimengVideoNodeData extends Record<string, unknown> {
  /** 节点标题 (源站: 文件名 / "视频 1") */
  title: string;
  /** 内容来源: local-upload = 本地上传视频 (本 batch 的复刻重点) */
  source: "local-upload" | "generated" | "empty";
  /** 是否已有媒体内容；false 时渲染空占位卡 (源站 "视频 1" 状态) */
  hasMedia: boolean;
  /** mock 海报 (合成占位图 data URI，非源站资产) */
  poster?: string;
  /** 视频时长 (秒)，mock 数据 */
  duration?: number;
  /** 当前播放进度 (秒)，mock 数据 */
  currentTime?: number;
  /** 世界尺寸 (源站 video 节点 ≈ 569×320，16:9) */
  width: number;
  height: number;
}

export type JimengNode = Node<JimengVideoNodeData, JimengNodeKind>;
