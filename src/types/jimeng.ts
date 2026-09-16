import type { Node } from "@xyflow/react";

/**
 * 即梦 (jimeng.jianying.com) AI 画布复刻的节点类型。
 *
 * 证据: docs/research/jimeng-canvas/README.md
 * 源站画布为 React Flow (xyflow v12)，节点类型名 "video" 等；
 * 本文件是复刻侧的类型契约（CLONE_DECISION 命名加 Jimeng 前缀）。
 */

export type JimengNodeKind = "video" | "image" | "text" | "audio";

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
  /** 是否播放中 (mock 初始为暂停态，与源站提取一致) */
  playing?: boolean;
  /** 是否静音 (Batch 29；源站卡片默认显示静音图标) */
  muted?: boolean;
  /** 节点颜色标记 (Batch 31；源站标题 Tag 图标点击弹出五色选择器) */
  tagColor?: string | null;
  /** 生成中 (Batch 50)：发送生成任务后的处理态 (mock) */
  generating?: boolean;
  /** 生成时的提示词 (Batch 50 mock) */
  prompt?: string;
  /** 媒体加载失败态 (Batch 67, SOURCE_FACT 67-cap-state.png): 资源失效后
      显示 视频播放失败 + 重试播放视频；复刻侧无自然失效路径，
      由 setMediaError 驱动 (测试经 dev window hook) */
  mediaError?: boolean;
  /** 世界尺寸 (源站 video 节点 ≈ 569×320，16:9) */
  width: number;
  height: number;
}

/** 图片节点 (Batch 17；尺寸 CLONE_DECISION 480×360) */
export interface JimengImageNodeData extends Record<string, unknown> {
  title: string;
  /** 截取帧落图 (Batch 62)：源站 首帧/尾帧 直接产出带画面的图片节点 */
  poster?: string;
  width: number;
  height: number;
  /**
   * 截取帧产出后的瞬态上传进度 (Batch 197 SOURCE_FACT: 源站产出瞬间
   * 节点呈现「正在上传图片 0%」，约 1-2s 内完成转常规态)。
   * 缺省 = 非上传态；100 = 完成（组件按 <100 判定显隐）。
   */
  uploadProgress?: number;
}

/** 文字节点 (Batch 17；尺寸 CLONE_DECISION 320×200) */
export interface JimengTextNodeData extends Record<string, unknown> {
  title: string;
  text: string;
  width: number;
  height: number;
  /** 卡片背景色 (批 241 SOURCE_FACT: 文本节点选中工具条含「背景色」
   *  调色板——无 + 青绿/靛蓝/紫/橙/黄 六格)；null = 默认深色 */
  bgColor?: string | null;
}

/** 音频节点 (Batch 19；样式 CLONE_DECISION 波形 mock 400×120) */
export interface JimengAudioNodeData extends Record<string, unknown> {
  title: string;
  duration: number;
  width: number;
  height: number;
}

export type JimengNode = Node<
  | JimengVideoNodeData
  | JimengImageNodeData
  | JimengTextNodeData
  | JimengAudioNodeData,
  JimengNodeKind
> & {
  /** 编组 id (Batch 39；同组节点拖拽联动，⌘G/⌘⇧G) */
  groupId?: string;
};
