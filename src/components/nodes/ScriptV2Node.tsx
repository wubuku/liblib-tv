"use client";

import { memo } from "react";
import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import { cn } from "@/lib/utils";

export interface ScriptV2NodeData extends Record<string, unknown> {
  title?: string;
}

export type ScriptV2NodeType = Node<ScriptV2NodeData, "script-v2">;

/* 源站节点头部文档图标（0 0 20 20，四行文档，Batch 208 采样）。 */
function DocGlyph() {
  return (
    <svg aria-hidden="true" width="14" height="14" viewBox="0 0 20 20" fill="none">
      <path
        d="M17.4 0A2.6 2.6 0 0 1 20 2.6v14.8a2.6 2.6 0 0 1-2.6 2.6H2.6A2.6 2.6 0 0 1 0 17.4V2.6A2.6 2.6 0 0 1 2.6 0zM4 16.26h8v-1.8H4zm0-3.57h12V7.3H4zm0-3.57h12v-1.8H4z"
        fill="currentColor"
      />
    </svg>
  );
}

// Batch 207/208: 源站 script-v2 节点（350×350，标题「脚本生成器」）——
// 卡壳 rounded-xl / #171717（Surface-Panel-background）/ 选中描边
// canvas-node-border-selected；标题条悬浮于卡片上方 -28px（随流缩放）。
// 内部编辑器/面板未采样，卡体为最小占位。
function ScriptV2NodeInner({ data }: NodeProps<ScriptV2NodeType>) {
  return (
    <div className="relative" style={{ width: 350 }}>
      <div className="absolute left-0 top-[-28px] flex w-full items-center gap-1 text-[#8f8f8f]">
        <DocGlyph />
        <span className="truncate text-[13px]">{data.title ?? "脚本生成器"}</span>
      </div>
      <div
        className={cn(
          "node-shell relative flex h-[350px] w-full flex-col overflow-hidden rounded-xl border border-[#363636] bg-[#171717]",
        )}
      >
        <Handle type="target" position={Position.Left} isConnectable />
        <Handle type="source" position={Position.Right} isConnectable />
      </div>
    </div>
  );
}

export const ScriptV2Node = memo(ScriptV2NodeInner);
