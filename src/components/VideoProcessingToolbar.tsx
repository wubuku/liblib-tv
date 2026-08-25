"use client";

import { useState } from "react";
import {
  AudioLines,
  CaptionsOff,
  Crop,
  Download,
  Expand,
  Film,
  Highlighter,
  Redo2,
  Scissors,
  Sparkles,
  TimerReset,
  Undo2,
} from "lucide-react";
import { NodeToolbar, Position } from "@xyflow/react";
import { cn } from "@/lib/utils";

type ToolbarMenu = "subtitle" | "audio" | "edit" | null;

interface VideoProcessingToolbarProps {
  activeTool: "generator" | "reshoot" | "continue";
  enhanced: boolean;
  posterUrl?: string;
  onSelectTool: (tool: "generator" | "reshoot" | "continue") => void;
  onToggleEnhanced: () => void;
  onCreateBreakdown: () => void;
}

export function VideoProcessingToolbar({ activeTool, enhanced, posterUrl, onSelectTool, onToggleEnhanced, onCreateBreakdown }: VideoProcessingToolbarProps) {
  const [menu, setMenu] = useState<ToolbarMenu>(null);
  const [lastAction, setLastAction] = useState<string | null>(null);

  const selectMenuAction = (label: string) => {
    setLastAction(label);
    setMenu(null);
  };

  return (
    <NodeToolbar position={Position.Top} offset={16} align="center" className="nodrag nopan z-[1001]">
      <div
        onPointerDown={(event) => event.stopPropagation()}
        onClick={(event) => event.stopPropagation()}
        className="relative flex h-[49px] w-[920px] items-center gap-1 rounded-xl border border-[#363636] bg-[#262626] p-2 shadow-[0_8px_30px_rgba(0,0,0,0.38)]"
      >
        <ToolbarButton label={enhanced ? "高清已开启" : "高清"} active={enhanced} onClick={onToggleEnhanced}><Highlighter size={16} /></ToolbarButton>
        <ToolbarButton label="片段重拍" active={activeTool === "reshoot"} onClick={() => onSelectTool(activeTool === "reshoot" ? "generator" : "reshoot")}><Scissors size={16} /></ToolbarButton>
        <ToolbarButton label="逐帧拉片" onClick={onCreateBreakdown}><Film size={16} /></ToolbarButton>
        <ToolbarButton label="智能续写" active={activeTool === "continue"} onClick={() => onSelectTool(activeTool === "continue" ? "generator" : "continue")}><TimerReset size={16} /></ToolbarButton>
        <ToolbarButton label="智能去字幕" active={menu === "subtitle"} onClick={() => setMenu(menu === "subtitle" ? null : "subtitle")}><CaptionsOff size={16} /></ToolbarButton>
        <ToolbarButton label="音频分离" active={menu === "audio"} onClick={() => setMenu(menu === "audio" ? null : "audio")}><AudioLines size={16} /></ToolbarButton>
        <ToolbarButton label="画面编辑" active={menu === "edit"} onClick={() => setMenu(menu === "edit" ? null : "edit")}><Crop size={16} /></ToolbarButton>

        <span className="min-w-1 flex-1" />
        {lastAction && <span className="max-w-28 truncate text-[11px] text-[#777]">{lastAction}</span>}
        <span className="h-5 w-px shrink-0 bg-white/10" />
        <a href={posterUrl ?? "/images/scene-coffee-4.png"} download className="flex size-8 shrink-0 items-center justify-center rounded-lg text-[#a8a8a8] hover:bg-white/[0.07] hover:text-white" aria-label="下载视频封面"><Download size={16} /></a>
        <button type="button" onClick={() => setLastAction("已打开预览")} className="flex size-8 shrink-0 items-center justify-center rounded-lg text-[#a8a8a8] hover:bg-white/[0.07] hover:text-white" aria-label="展开视频"><Expand size={16} /></button>
        <button type="button" className="flex size-8 shrink-0 items-center justify-center rounded-lg text-[#777] hover:bg-white/[0.07] hover:text-white" aria-label="撤销视频处理"><Undo2 size={15} /></button>
        <button type="button" className="flex size-8 shrink-0 items-center justify-center rounded-lg text-[#777] hover:bg-white/[0.07] hover:text-white" aria-label="重做视频处理"><Redo2 size={15} /></button>

        {menu && (
          <div className="absolute right-24 top-[55px] z-40 w-44 rounded-xl border border-white/10 bg-[#292929] p-1.5 text-xs shadow-2xl">
            {menu === "subtitle" && <><MenuItem label="智能去字幕" icon={<Sparkles size={14} />} onClick={selectMenuAction} /><MenuItem label="框选去字幕" icon={<Crop size={14} />} onClick={selectMenuAction} /></>}
            {menu === "audio" && <><MenuItem label="人声提取" icon={<AudioLines size={14} />} onClick={selectMenuAction} /><MenuItem label="背景音提取" icon={<AudioLines size={14} />} onClick={selectMenuAction} /><MenuItem label="音效提取" icon={<AudioLines size={14} />} onClick={selectMenuAction} /></>}
            {menu === "edit" && <><MenuItem label="片段截取" icon={<Scissors size={14} />} onClick={selectMenuAction} /><MenuItem label="画面裁切" icon={<Crop size={14} />} onClick={selectMenuAction} /></>}
          </div>
        )}
      </div>
    </NodeToolbar>
  );
}

function ToolbarButton({ label, active = false, onClick, children }: { label: string; active?: boolean; onClick: () => void; children: React.ReactNode }) {
  return <button type="button" onClick={onClick} className={cn("flex h-8 shrink-0 items-center gap-1.5 rounded-lg px-2 text-sm text-[#e5e5e5] hover:bg-white/[0.07]", active && "bg-white/[0.1] text-white")}>{children}<span>{label}</span></button>;
}

function MenuItem({ label, icon, onClick }: { label: string; icon: React.ReactNode; onClick: (label: string) => void }) {
  return <button type="button" onClick={() => onClick(label)} className="flex h-9 w-full items-center gap-2 rounded-lg px-2 text-[#ddd] hover:bg-white/[0.07]">{icon}{label}</button>;
}
