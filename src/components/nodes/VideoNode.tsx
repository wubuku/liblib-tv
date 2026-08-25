"use client";

import Image from "next/image";
import { memo, useState } from "react";
import { AlertTriangle, Play, Volume2 } from "lucide-react";
import { Handle, Position, useViewport, type Node, type NodeProps } from "@xyflow/react";
import { cn } from "@/lib/utils";
import {
  useCanvasStore,
  type VideoContinuationMetadata,
} from "@/store/canvasStore";
import { SegmentReshootPanel } from "@/components/SegmentReshootPanel";
import { VideoContinuationSelector } from "@/components/VideoContinuationSelector";
import { VideoGenerationPanel } from "@/components/VideoGenerationPanel";
import { VideoProcessingToolbar } from "@/components/VideoProcessingToolbar";

export interface VideoNodeData extends Record<string, unknown> {
  filename?: string;
  model?: string;
  status?: "empty" | "failed" | "ready";
  durationSeconds?: number;
  resolution?: string;
  posterUrl?: string;
  prompt?: string;
  continuation?: VideoContinuationMetadata;
}

export type VideoNodeType = Node<VideoNodeData, "video">;

function VideoNodeComponent({ id, data, selected }: NodeProps<VideoNodeType>) {
  const { filename = "分镜视频-#9", model = "vip专属模型-会员", status = "failed", posterUrl, durationSeconds = 30, resolution = "1280 × 720", prompt, continuation } = data;
  const { zoom } = useViewport();
  const addDerivedNode = useCanvasStore((state) => state.addDerivedNode);
  const createVideoContinuation = useCanvasStore((state) => state.createVideoContinuation);
  const clearVideoContinuation = useCanvasStore((state) => state.clearVideoContinuation);
  const selectedNodeCount = useCanvasStore((state) => state.selectedNodeIds.length);
  const showSingleNodeEditor = selected && selectedNodeCount <= 1;
  const [activeTool, setActiveTool] = useState<"generator" | "reshoot" | "continue">("generator");
  const [enhanced, setEnhanced] = useState(false);

  const createBreakdown = () => {
    addDerivedNode(id, "shot-breakdown", {
      title: `逐帧拉片 · ${filename}`,
      status: "ready",
      sourceName: filename,
      sourceDuration: durationSeconds,
      sourcePosterUrl: posterUrl ?? "/images/scene-coffee-4.png",
      dimensions: ["storyboard", "motion", "music"],
    });
  };

  const confirmContinuation = (startSeconds: number, endSeconds: number) => {
    setActiveTool("generator");
    createVideoContinuation(id, startSeconds, endSeconds);
  };

  return (
    <div
      className={cn(
        "group relative flex h-full w-full flex-col overflow-visible rounded-[3px] border bg-[#242424]",
        selected ? "border-[#09caf5] shadow-[0_0_0_2px_rgba(9,202,245,0.22)]" : "border-white/[0.07]",
      )}
    >
      {showSingleNodeEditor && status === "ready" && (
        <VideoProcessingToolbar
          activeTool={activeTool}
          enhanced={enhanced}
          posterUrl={posterUrl}
          onSelectTool={setActiveTool}
          onToggleEnhanced={() => setEnhanced((value) => !value)}
          onCreateBreakdown={createBreakdown}
        />
      )}
      <Handle type="target" position={Position.Left} id="target" style={{ width: 20, height: 20 }} />
      <Handle type="source" position={Position.Right} id="source" style={{ width: 20, height: 20 }} />

      <div className="pointer-events-none absolute -top-8 left-0 flex w-full items-center gap-2 text-xs text-[#858585]">
        <Play size={13} />
        <span className="min-w-0 flex-1 truncate">{filename}</span>
        <span>{resolution}</span>
      </div>
      <div className="relative flex min-h-0 flex-1 items-center justify-center overflow-hidden rounded-[2px] bg-[#202020]">
        {status === "failed" ? (
          <div className="flex flex-col items-center gap-2 text-center">
            <AlertTriangle size={27} strokeWidth={1.4} className="text-[#e65d67]" />
            <span className="text-xs text-[#e65d67]">生成失败</span>
            <span className="text-[10px] text-[#626262]">{model}</span>
          </div>
        ) : status === "ready" ? (
          <>
            <Image src={posterUrl ?? "/images/scene-coffee-4.png"} alt={filename} fill sizes="700px" className={cn("object-cover", enhanced && "contrast-110 saturate-110")} unoptimized />
            <span className="absolute inset-0 bg-black/10" />
            <button type="button" aria-label="播放视频" className="relative flex size-14 items-center justify-center rounded-full bg-black/55 text-white backdrop-blur-sm hover:bg-black/70"><Play size={22} fill="currentColor" className="ml-1" /></button>
            <div className="absolute bottom-3 left-3 right-3 flex items-center gap-2 text-[11px] text-white">
              <Play size={12} fill="currentColor" />
              <span>00:00</span>
              <span className="h-1 flex-1 rounded-full bg-white/30"><span className="block h-full w-0 rounded-full bg-white" /></span>
              <span>00:{String(durationSeconds).padStart(2, "0")}</span>
              <Volume2 size={13} />
            </div>
          </>
        ) : (
          <div data-video-continuation-empty className="flex flex-col items-center gap-2 text-center">
            <span className="flex size-14 items-center justify-center rounded-full bg-white/[0.05] text-[#777]">
              <Play size={22} fill="currentColor" className="ml-1" />
            </span>
            <span className="text-xs text-[#777]">等待续写内容</span>
          </div>
        )}
      </div>

      {showSingleNodeEditor && activeTool === "generator" && (
        <VideoGenerationPanel
          zoom={zoom}
          initialModel={model}
          initialPrompt={prompt}
          continuation={continuation}
          onClearContinuation={
            continuation ? () => clearVideoContinuation(id) : undefined
          }
        />
      )}
      {showSingleNodeEditor && activeTool === "reshoot" && (
        <SegmentReshootPanel zoom={zoom} />
      )}
      {showSingleNodeEditor && status === "ready" && activeTool === "continue" && (
        <VideoContinuationSelector
          zoom={zoom}
          durationSeconds={durationSeconds}
          onCancel={() => setActiveTool("generator")}
          onConfirm={confirmContinuation}
        />
      )}
    </div>
  );
}

export const VideoNode = memo(VideoNodeComponent);
