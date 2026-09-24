"use client";

import type { NodeProps } from "@xyflow/react";
import { FrameosNodeShell } from "./FrameosNodeShell";
import { LayoutGridIcon } from "../icons";
import type { FrameosNode } from "@/types/frameos";

/**
 * FrameOS 3D模型节点 (Batch 216, 源站采样对齐):
 * - 空态: 居中 3D 立方体图标卡片 (300x200), 左右 handle
 * - 选中: 下方 3D 面板 (帧界 3D 1.0 模型 + 标准 下拉 + 积分 750 + ↑ 按钮)
 */
export function Frameos3DModelNode({ id, data, selected }: NodeProps<FrameosNode>) {
  const { title } = data;

  return (
    <FrameosNodeShell
      kind="model3d"
      title={title}
      titleIcon={<LayoutGridIcon size={12} />}
      selected={selected}
      showLeftHandle
      showRightHandle
      nodeProps={{ id, data } as unknown as NodeProps<FrameosNode>}
      width={300}
      height={200}
    >
      <div
        className="card-body"
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
        <LayoutGridIcon size={24} color="#8C8C8C" />
      </div>
    </FrameosNodeShell>
  );
}
