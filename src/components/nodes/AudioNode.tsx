"use client";

import { memo } from "react";
import { AudioLines, Play } from "lucide-react";
import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import { cn } from "@/lib/utils";
import type {
  AudioSplitMetadata,
  AudioSplitMode,
} from "@/store/canvasStore";

export interface AudioNodeData extends Record<string, unknown> {
  filename?: string;
  duration?: string;
  audioSplit?: AudioSplitMetadata;
}

export type AudioNodeType = Node<AudioNodeData, "audio">;

function AudioNodeComponent({ data, selected }: NodeProps<AudioNodeType>) {
  const filename = data.filename ?? "新音频";
  const duration = data.duration ?? "00:00";
  const audioSplit = data.audioSplit;
  const resultLabelByMode: Record<AudioSplitMode, string> = {
    av: "独立音轨",
    vocals: "人声",
    background: "背景音",
  };

  return (
    <div
      {...(audioSplit
        ? {
            "data-audio-split-output": true,
            "data-audio-split-mode": audioSplit.mode,
            "data-audio-split-output-kind": audioSplit.outputKind,
            "data-audio-split-source-id": audioSplit.sourceNodeId,
            "data-audio-split-edge-id": audioSplit.edgeId,
          }
        : {})}
      className={cn(
        "group relative flex h-full w-full flex-col overflow-visible rounded-xl border bg-[#242424] p-3",
        selected ? "border-[#09caf5] shadow-[0_0_0_2px_rgba(9,202,245,0.22)]" : "border-white/10",
      )}
    >
      <Handle type="target" position={Position.Left} id="target" style={{ width: 20, height: 20 }} />
      <Handle type="source" position={Position.Right} id="source" style={{ width: 20, height: 20 }} />

      <div className="pointer-events-none absolute -top-8 left-0 flex items-center gap-2 text-sm text-[#858585]">
        <AudioLines size={14} />
        <span>{filename}</span>
      </div>

      <div className="flex items-center gap-2 text-sm font-medium text-[#ededed]">
        <AudioLines size={16} />
        {audioSplit ? `${resultLabelByMode[audioSplit.mode]}结果` : "音频"}
      </div>
      <div className="mt-3 flex items-center gap-3 rounded-lg bg-[#1d1d1d] px-3 py-2.5">
        <button type="button" aria-label="播放音频" className="flex size-8 shrink-0 items-center justify-center rounded-full bg-white text-[#202020] hover:bg-[#ededed]">
          <Play size={13} fill="currentColor" className="ml-0.5" />
        </button>
        <div className="flex h-7 flex-1 items-center gap-1 overflow-hidden">
          {Array.from({ length: 28 }, (_, index) => (
            <span
              key={index}
              className="w-1 shrink-0 rounded-full bg-[#6e747d]"
              style={{ height: `${8 + ((index * 13) % 18)}px` }}
            />
          ))}
        </div>
        <span className="text-[10px] tabular-nums text-[#8b8b8b]">{duration}</span>
      </div>
      <p className="mt-2 truncate text-[10px] text-[#666]">
        {audioSplit ? `来自 ${audioSplit.sourceLabel}` : "本地音频节点预览"}
      </p>
    </div>
  );
}

export const AudioNode = memo(AudioNodeComponent);
