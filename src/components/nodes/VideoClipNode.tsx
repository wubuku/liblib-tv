"use client";

import { memo, useState } from "react";
import { ArrowUp, ChevronDown, Film, Link2 } from "lucide-react";
import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import { cn } from "@/lib/utils";

export interface VideoClipNodeData extends Record<string, unknown> {
  title?: string;
  status?: "empty" | "ready";
}

export type VideoClipNodeType = Node<VideoClipNodeData, "video-clip">;

const modes = ["讲解视频", "批量广告", "口播视频", "素材混剪"];

function VideoClipNodeComponent({ data, selected }: NodeProps<VideoClipNodeType>) {
  const [mode, setMode] = useState(modes[0]);
  const [prompt, setPrompt] = useState("");

  return (
    <div className={cn("relative flex h-full w-full flex-col overflow-visible rounded-2xl border bg-[#242424] p-3", selected ? "border-[#09caf5] shadow-[0_0_0_2px_rgba(9,202,245,0.18)]" : "border-white/10")}>
      <Handle type="target" position={Position.Left} id="target" style={{ width: 20, height: 20 }} />
      <Handle type="source" position={Position.Right} id="source" style={{ width: 20, height: 20 }} />
      <div className="pointer-events-none absolute -top-8 left-0 flex items-center gap-2 text-sm text-[#858585]"><Film size={14} />{data.title ?? "智能剪辑 1"}</div>

      <div className="mb-3 flex items-center gap-2 text-sm font-semibold"><Film size={16} />智能剪辑 <span className="rounded bg-[#393939] px-1.5 py-0.5 text-[9px] text-[#aaa]">Beta</span></div>
      <div className="grid grid-cols-2 gap-1.5">
        {modes.map((item) => <button key={item} type="button" onClick={() => setMode(item)} className={cn("h-8 rounded-lg text-xs", mode === item ? "bg-white/[0.11] text-white" : "bg-white/[0.04] text-[#888] hover:text-white")}>{item}</button>)}
      </div>
      <button type="button" className="mt-3 flex h-9 items-center gap-2 rounded-lg border border-dashed border-white/10 px-3 text-xs text-[#888] hover:text-white"><Link2 size={14} />参考</button>
      <textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="描述想剪成什么效果" className="mt-2 min-h-0 flex-1 resize-none rounded-lg bg-black/15 p-3 text-sm text-white outline-none placeholder:text-[#5f5f5f]" />
      <div className="mt-2 flex items-center gap-1 text-xs text-[#b5b5b5]">
        <button type="button" className="flex h-8 items-center gap-1 rounded-lg px-2 hover:bg-white/[0.06]">默认模式 <ChevronDown size={12} /></button>
        <button type="button" className="flex h-8 items-center gap-1 rounded-lg px-2 hover:bg-white/[0.06]">16:9 · 720P · 30s <ChevronDown size={12} /></button>
        <button type="button" aria-label="发送" disabled={!prompt.trim()} className="ml-auto flex size-8 items-center justify-center rounded-xl bg-white text-[#202020] disabled:bg-white/[0.08] disabled:text-[#555]"><ArrowUp size={15} /></button>
      </div>
    </div>
  );
}

export const VideoClipNode = memo(VideoClipNodeComponent);
