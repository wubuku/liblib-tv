"use client";

import { memo, useState } from "react";
import {
  Clapperboard,
  Megaphone,
  Mic2,
  Scissors,
  Shuffle,
} from "lucide-react";
import {
  Handle,
  Position,
  useViewport,
  type Node,
  type NodeProps,
} from "@xyflow/react";
import { cn } from "@/lib/utils";
import { useCanvasStore } from "@/store/canvasStore";
import {
  VideoClipEditPanel,
  type VideoClipMode,
} from "@/components/VideoClipEditPanel";

export interface VideoClipNodeData extends Record<string, unknown> {
  title?: string;
  status?: "empty" | "ready";
}

export type VideoClipNodeType = Node<VideoClipNodeData, "video-clip">;

const modes: Array<{
  label: VideoClipMode;
  icon: typeof Clapperboard;
}> = [
  { label: "讲解视频", icon: Clapperboard },
  { label: "批量广告", icon: Megaphone },
  { label: "口播视频", icon: Mic2 },
  { label: "素材混剪", icon: Shuffle },
];

function VideoClipNodeComponent({
  data,
  selected,
}: NodeProps<VideoClipNodeType>) {
  const { zoom } = useViewport();
  const selectedNodeCount = useCanvasStore(
    (state) => state.selectedNodeIds.length,
  );
  const [mode, setMode] = useState<VideoClipMode | null>(null);
  const showSingleNodeEditor = selected && selectedNodeCount <= 1;

  return (
    <div
      data-video-clip-node
      className={cn(
        "relative flex h-full w-full flex-col overflow-visible rounded-[10px] border bg-[#242424] px-8 py-7",
        selected
          ? "border-[#09caf5] shadow-[0_0_0_2px_rgba(9,202,245,0.18)]"
          : "border-white/10",
      )}
    >
      <Handle type="target" position={Position.Left} id="target" style={{ width: 20, height: 20 }} />
      <Handle type="source" position={Position.Right} id="source" style={{ width: 20, height: 20 }} />
      <div className="pointer-events-none absolute -top-8 left-0 flex items-center gap-2 text-sm text-[#858585]">
        <Scissors size={14} />
        {data.title ?? "智能剪辑 1"}
      </div>

      <div
        data-video-clip-empty
        className="flex min-h-0 flex-1 flex-col items-center"
      >
        <Scissors
          size={46}
          strokeWidth={1.25}
          className="mt-2 text-[#5c5c5c]"
        />
        <p className="mt-4 text-center text-sm text-[#686868]">
          空空如也，请连接视频节点后操作
        </p>
        <div className="mt-5 w-[164px]">
          <p className="mb-1.5 text-xs text-[#666]">尝试：</p>
          <div className="flex flex-col gap-1">
            {modes.map((item) => {
              const Icon = item.icon;
              const active = mode === item.label;
              return (
                <button
                  key={item.label}
                  type="button"
                  data-video-clip-mode={item.label}
                  aria-pressed={active}
                  onClick={() =>
                    setMode((current) =>
                      current === item.label ? null : item.label,
                    )
                  }
                  className={cn(
                    "nodrag nopan flex h-8 items-center gap-2 rounded-md px-2 text-left text-xs transition-colors",
                    active
                      ? "bg-white/[0.08] text-[#d9d9d9]"
                      : "text-[#888] hover:bg-white/[0.05] hover:text-[#d0d0d0]",
                  )}
                >
                  <Icon size={13} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {showSingleNodeEditor && (
        <VideoClipEditPanel zoom={zoom} mode={mode} />
      )}
    </div>
  );
}

export const VideoClipNode = memo(VideoClipNodeComponent);
