"use client";

import { memo } from "react";
import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import { cn } from "@/lib/utils";

export interface StoryboardGroupData extends Record<string, unknown> {
  title?: string;
  variant?: "image" | "video";
}

export type StoryboardGroupType = Node<StoryboardGroupData, "storyboard-group">;

function StoryboardGroupNodeComponent({ data, selected }: NodeProps<StoryboardGroupType>) {
  const title = data.title || "分镜图 · 第一集：咖啡馆对峙-图片组";
  const isVideo = data.variant === "video";

  return (
    <div
      className={cn(
        "relative h-full w-full overflow-visible border",
        isVideo ? "rounded-[4px] border-white/10 bg-[#212121]" : "rounded-[20px] border-white/10 bg-white/10",
        selected && "border-[#09caf5] shadow-[0_0_0_2px_rgba(9,202,245,0.18)]",
      )}
    >
      <Handle type="target" position={Position.Left} id="target" style={{ width: 20, height: 20 }} />
      <Handle type="source" position={Position.Right} id="source" style={{ width: 20, height: 20 }} />
      <div className="pointer-events-none absolute -top-8 left-0 whitespace-nowrap text-sm text-[#777]">{title}</div>
    </div>
  );
}

export const StoryboardGroupNode = memo(StoryboardGroupNodeComponent);
