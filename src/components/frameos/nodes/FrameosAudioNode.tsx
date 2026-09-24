"use client";

import { useState } from "react";
import type { NodeProps } from "@xyflow/react";
import { FrameosNodeShell } from "./FrameosNodeShell";
import { AudioIcon } from "../icons";
import type { FrameosNode } from "@/types/frameos";

/**
 * FrameOS 音频节点 (Batch 213, 源站采样对齐):
 * - 空态: 居中音乐图标卡片 (260x160), 左右 handle, 无 resize 手柄
 * - 选中: 蓝框 + 下方音频面板 (占位 描述音乐 / 配音 / 音效, BGM S6 模型,
 *   参数 下拉, 积分 100, ↑ 生成按钮; 参考 按钮)
 */
export function FrameosAudioNode({ id, data, selected }: NodeProps<FrameosNode>) {
  const { title } = data;
  const [, setIsHovered] = useState(false);

  return (
    <FrameosNodeShell
      kind="audio"
      title={title}
      titleIcon={<AudioIcon size={12} />}
      selected={selected}
      showLeftHandle
      showRightHandle
      showResizeHandle={false}
      nodeProps={{ id, data } as unknown as NodeProps<FrameosNode>}
      width={260}
      height={160}
    >
      <div
        className="card-body"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#1C1C1C",
          borderRadius: 10,
          overflow: "hidden",
        }}
      >
        <AudioIcon size={24} color="#8C8C8C" />
      </div>
    </FrameosNodeShell>
  );
}
