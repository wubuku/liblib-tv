"use client";

import { memo } from "react";
import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import { cn } from "@/lib/utils";

export interface ScriptV2NodeData extends Record<string, unknown> {
  title?: string;
}

export type ScriptV2NodeType = Node<ScriptV2NodeData, "script-v2">;

// Batch 207: 源站 script-v2 节点（350×350，标题「脚本生成器」）——
// 2026-09-08 丢弃式采样（空画布芯片成对创建的成对节点）；
// 内部编辑器/面板未采样，卡片主体为 clone 最小占位。
function ScriptV2NodeInner({ data }: NodeProps<ScriptV2NodeType>) {
  return (
    <div
      className={cn(
        "relative flex h-[350px] w-[350px] flex-col overflow-hidden rounded-[10px] border bg-[#242424] px-4 py-3",
        "border-[#363636]",
      )}
    >
      <Handle type="target" position={Position.Left} isConnectable />
      <Handle type="source" position={Position.Right} isConnectable />
      <span className="text-sm font-medium text-[#ededed]">
        {data.title ?? "脚本生成器"}
      </span>
    </div>
  );
}

export const ScriptV2Node = memo(ScriptV2NodeInner);
