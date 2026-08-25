"use client";

import { memo } from "react";
import { AlertTriangle, Play } from "lucide-react";
import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import { cn } from "@/lib/utils";

export interface VideoNodeData extends Record<string, unknown> {
  filename?: string;
  model?: string;
  status?: "failed" | "ready";
}

export type VideoNodeType = Node<VideoNodeData, "video">;

function VideoNodeComponent({ data, selected }: NodeProps<VideoNodeType>) {
  const { filename = "分镜视频-#9", model = "vip专属模型-会员", status = "failed" } = data;

  return (
    <div
      className={cn(
        "group relative flex h-full w-full flex-col overflow-visible rounded-[3px] border bg-[#242424]",
        selected ? "border-[#09caf5] shadow-[0_0_0_2px_rgba(9,202,245,0.22)]" : "border-white/[0.07]",
      )}
    >
      <Handle type="target" position={Position.Left} id="target" style={{ width: 20, height: 20 }} />
      <Handle type="source" position={Position.Right} id="source" style={{ width: 20, height: 20 }} />

      <div className="flex h-12 items-center gap-2 border-b border-white/[0.06] px-4 text-xs text-[#858585]">
        <Play size={13} />
        <span>{filename}</span>
      </div>
      <div className="flex min-h-0 flex-1 items-center justify-center bg-[#202020]">
        {status === "failed" ? (
          <div className="flex flex-col items-center gap-2 text-center">
            <AlertTriangle size={27} strokeWidth={1.4} className="text-[#e65d67]" />
            <span className="text-xs text-[#e65d67]">生成失败</span>
            <span className="text-[10px] text-[#626262]">{model}</span>
          </div>
        ) : (
          <Play size={34} className="text-[#777]" />
        )}
      </div>
    </div>
  );
}

export const VideoNode = memo(VideoNodeComponent);
