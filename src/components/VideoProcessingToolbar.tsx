"use client";

import { useEffect, useRef, useState } from "react";
import {
  AudioLines,
  Camera,
  CaptionsOff,
  ChevronDown,
  Crop,
  Download,
  Expand,
  Film,
  Highlighter,
  LoaderCircle,
  PanelsTopLeft,
  Redo2,
  Scissors,
  Sparkles,
  TimerReset,
  Undo2,
} from "lucide-react";
import { NodeToolbar, Position } from "@xyflow/react";
import { cn } from "@/lib/utils";
import type {
  AudioSplitMode,
  PictureEditAction,
  SubtitleEraseMode,
  VideoFrameCaptureKind,
} from "@/store/canvasStore";

type ToolbarMenu = "subtitle" | "audio" | "picture-edit" | "frame" | null;
type PictureEditMenuAction = PictureEditAction | "matting";

interface VideoProcessingToolbarProps {
  activeTool: "generator" | "reshoot" | "continue";
  enhanced: boolean;
  posterUrl?: string;
  onSelectTool: (tool: "generator" | "reshoot" | "continue") => void;
  onToggleEnhanced: () => void;
  onCreateBreakdown: () => void;
  onSelectSubtitleMode: (mode: SubtitleEraseMode) => void;
  onAudioSplit: (mode: AudioSplitMode) => void;
  onPictureEdit: (action: PictureEditAction) => void;
  onSmartMatting: () => void;
  onCaptureFrame: (kind: VideoFrameCaptureKind) => void;
  audioSplittingMode: AudioSplitMode | null;
}

export function VideoProcessingToolbar({ activeTool, enhanced, posterUrl, onSelectTool, onToggleEnhanced, onCreateBreakdown, onSelectSubtitleMode, onAudioSplit, onPictureEdit, onSmartMatting, onCaptureFrame, audioSplittingMode }: VideoProcessingToolbarProps) {
  const [menu, setMenu] = useState<ToolbarMenu>(null);
  const [lastAction, setLastAction] = useState<string | null>(null);
  const openTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const closeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (openTimerRef.current) clearTimeout(openTimerRef.current);
      if (closeTimerRef.current) clearTimeout(closeTimerRef.current);
    };
  }, []);

  const clearMenuTimers = () => {
    if (openTimerRef.current) {
      clearTimeout(openTimerRef.current);
      openTimerRef.current = null;
    }
    if (closeTimerRef.current) {
      clearTimeout(closeTimerRef.current);
      closeTimerRef.current = null;
    }
  };

  const openMenuOnHover = (nextMenu: Exclude<ToolbarMenu, null>) => {
    clearMenuTimers();
    openTimerRef.current = setTimeout(() => {
      openTimerRef.current = null;
      setMenu(nextMenu);
    }, 100);
  };

  const closeMenuOnHover = (targetMenu: Exclude<ToolbarMenu, null>) => {
    clearMenuTimers();
    closeTimerRef.current = setTimeout(() => {
      closeTimerRef.current = null;
      setMenu((current) => (current === targetMenu ? null : current));
    }, 120);
  };

  const toggleMenu = (targetMenu: Exclude<ToolbarMenu, null>) => {
    clearMenuTimers();
    setMenu((current) => (current === targetMenu ? null : targetMenu));
  };

  const closeMenu = () => {
    clearMenuTimers();
    setMenu(null);
  };

  const selectSubtitleMode = (mode: SubtitleEraseMode) => {
    closeMenu();
    setLastAction(null);
    onSelectSubtitleMode(mode);
  };

  const selectAudioMode = (mode: AudioSplitMode) => {
    closeMenu();
    setLastAction(null);
    onAudioSplit(mode);
  };

  const selectPictureEditAction = (action: PictureEditMenuAction) => {
    closeMenu();
    setLastAction(null);
    if (action === "matting") {
      onSmartMatting();
      return;
    }
    onPictureEdit(action);
  };

  return (
    <NodeToolbar position={Position.Top} offset={16} align="center" className="nodrag nopan z-[1001]">
      <div
        onPointerDown={(event) => event.stopPropagation()}
        onClick={(event) => event.stopPropagation()}
        className="relative flex h-[49px] w-max items-center gap-1 rounded-xl border border-[#363636] bg-[#262626] p-2 shadow-[0_8px_30px_rgba(0,0,0,0.38)]"
      >
        <ToolbarButton label={enhanced ? "高清已开启" : "高清"} active={enhanced} onClick={onToggleEnhanced}><Highlighter size={16} /></ToolbarButton>
        <ToolbarButton label="片段重拍" active={activeTool === "reshoot"} onClick={() => onSelectTool(activeTool === "reshoot" ? "generator" : "reshoot")}><Scissors size={16} /></ToolbarButton>
        <ToolbarButton label="逐帧拉片" onClick={onCreateBreakdown}><Film size={16} /></ToolbarButton>
        <ToolbarButton label="智能续写" active={activeTool === "continue"} onClick={() => onSelectTool(activeTool === "continue" ? "generator" : "continue")}><TimerReset size={16} /></ToolbarButton>
        <div
          className="relative shrink-0"
          onMouseEnter={() => openMenuOnHover("subtitle")}
          onMouseLeave={() => closeMenuOnHover("subtitle")}
        >
          <ToolbarButton dataAttribute="data-video-subtitle-menu-trigger" label="智能去字幕" title="AI一键去除视频字幕，仅支持中英文字幕" active={menu === "subtitle"} onClick={() => toggleMenu("subtitle")}><CaptionsOff size={16} /></ToolbarButton>
          {menu === "subtitle" && (
            <ToolbarMenu menu="subtitle">
              <MenuItem subtitleMode="smart" label="智能去字幕" icon={<Sparkles size={14} />} onClick={() => selectSubtitleMode("smart")} />
              <MenuItem subtitleMode="region" label="框选去字幕" icon={<Crop size={14} />} onClick={() => selectSubtitleMode("region")} />
            </ToolbarMenu>
          )}
        </div>
        <div
          className="relative shrink-0"
          onMouseEnter={() => openMenuOnHover("audio")}
          onMouseLeave={() => closeMenuOnHover("audio")}
        >
          <ToolbarButton
            dataAttribute="data-video-audio-menu-trigger"
            label={audioSplittingMode ? "分离中" : "音视频分离"}
            active={menu === "audio"}
            disabled={audioSplittingMode !== null}
            onClick={() => toggleMenu("audio")}
            trailing={!audioSplittingMode ? <ChevronDown size={12} /> : undefined}
          >
            {audioSplittingMode ? (
              <LoaderCircle
                data-video-audio-busy
                data-video-audio-busy-mode={audioSplittingMode}
                size={16}
                className="animate-spin"
              />
            ) : (
              <AudioLines size={16} />
            )}
          </ToolbarButton>
          {menu === "audio" && (
            <ToolbarMenu menu="audio">
              <MenuItem audioMode="av" label="音视频分离" title="分离内嵌音轨为独立音频节点" icon={<AudioLines size={14} />} onClick={() => selectAudioMode("av")} />
              <MenuItem audioMode="vocals" label="人声提取" icon={<AudioLines size={14} />} onClick={() => selectAudioMode("vocals")} />
              <MenuItem audioMode="background" label="背景音提取" icon={<AudioLines size={14} />} onClick={() => selectAudioMode("background")} />
            </ToolbarMenu>
          )}
        </div>
        <div
          className="relative shrink-0"
          onMouseEnter={() => openMenuOnHover("picture-edit")}
          onMouseLeave={() => closeMenuOnHover("picture-edit")}
        >
          <ToolbarButton
            dataAttribute="data-video-picture-edit-menu-trigger"
            label="主体消除"
            active={menu === "picture-edit"}
            onClick={() => toggleMenu("picture-edit")}
            trailing={<ChevronDown size={12} />}
          >
            <Crop size={16} />
          </ToolbarButton>
          {menu === "picture-edit" && (
            <ToolbarMenu menu="picture-edit">
              <MenuItem pictureEditAction="subjectRemove" label="主体消除" icon={<Sparkles size={14} />} onClick={() => selectPictureEditAction("subjectRemove")} />
              <MenuItem pictureEditAction="subjectModify" label="主体修改" icon={<Crop size={14} />} onClick={() => selectPictureEditAction("subjectModify")} />
              <MenuItem pictureEditAction="subjectReplace" label="主体替换" icon={<PanelsTopLeft size={14} />} onClick={() => selectPictureEditAction("subjectReplace")} />
              <MenuItem pictureEditAction="matting" label="智能抠像" icon={<Scissors size={14} />} onClick={() => selectPictureEditAction("matting")} />
            </ToolbarMenu>
          )}
        </div>
        <div
          className="relative shrink-0"
          onMouseEnter={() => openMenuOnHover("frame")}
          onMouseLeave={() => closeMenuOnHover("frame")}
        >
          <ToolbarButton
            dataAttribute="data-video-frame-menu-trigger"
            label="截取首帧"
            active={menu === "frame"}
            onClick={() => toggleMenu("frame")}
            trailing={<ChevronDown size={12} />}
          >
            <PanelsTopLeft size={16} />
          </ToolbarButton>
          {menu === "frame" && (
            <ToolbarMenu menu="frame">
              <MenuItem frameKind="first" label="截取首帧" icon={<PanelsTopLeft size={14} />} onClick={() => { closeMenu(); onCaptureFrame("first"); }} />
              <MenuItem frameKind="last" label="截取尾帧" icon={<PanelsTopLeft size={14} />} onClick={() => { closeMenu(); onCaptureFrame("last"); }} />
              <MenuItem frameKind="current" label="截取当前帧" icon={<Camera size={14} />} onClick={() => { closeMenu(); onCaptureFrame("current"); }} />
            </ToolbarMenu>
          )}
        </div>

        <span className="min-w-1" />
        {lastAction && <span className="max-w-28 truncate text-[11px] text-[#777]">{lastAction}</span>}
        <span className="h-5 w-px shrink-0 bg-white/10" />
        <a href={posterUrl ?? "/images/scene-coffee-4.png"} download className="flex size-8 shrink-0 items-center justify-center rounded-lg text-[#a8a8a8] hover:bg-white/[0.07] hover:text-white" aria-label="下载视频封面"><Download size={16} /></a>
        <button type="button" onClick={() => setLastAction("已打开预览")} className="flex size-8 shrink-0 items-center justify-center rounded-lg text-[#a8a8a8] hover:bg-white/[0.07] hover:text-white" aria-label="展开视频"><Expand size={16} /></button>
        <button type="button" className="flex size-8 shrink-0 items-center justify-center rounded-lg text-[#777] hover:bg-white/[0.07] hover:text-white" aria-label="撤销视频处理"><Undo2 size={15} /></button>
        <button type="button" className="flex size-8 shrink-0 items-center justify-center rounded-lg text-[#777] hover:bg-white/[0.07] hover:text-white" aria-label="重做视频处理"><Redo2 size={15} /></button>

      </div>
    </NodeToolbar>
  );
}

function ToolbarMenu({ menu, children }: { menu: Exclude<ToolbarMenu, null>; children: React.ReactNode }) {
  return <div data-video-toolbar-menu={menu} className="absolute left-1/2 top-[39px] z-40 w-40 -translate-x-1/2 rounded-xl border border-white/10 bg-[#292929] p-1.5 text-xs shadow-2xl">{children}</div>;
}

function ToolbarButton({ dataAttribute, label, title, active = false, disabled = false, onClick, children, trailing }: { dataAttribute?: "data-video-subtitle-menu-trigger" | "data-video-audio-menu-trigger" | "data-video-picture-edit-menu-trigger" | "data-video-frame-menu-trigger"; label: string; title?: string; active?: boolean; disabled?: boolean; onClick: () => void; children: React.ReactNode; trailing?: React.ReactNode }) {
  return <button {...(dataAttribute ? { [dataAttribute]: true } : {})} type="button" title={title} disabled={disabled} onClick={onClick} className={cn("flex h-8 shrink-0 items-center gap-1.5 rounded-lg px-2 text-sm text-[#e5e5e5] hover:bg-white/[0.07] disabled:cursor-wait disabled:text-[#9a9a9a] disabled:hover:bg-transparent", active && "bg-white/[0.1] text-white")}>{children}<span>{label}</span>{trailing}</button>;
}

function MenuItem({ subtitleMode, audioMode, pictureEditAction, frameKind, label, title, icon, onClick }: { subtitleMode?: SubtitleEraseMode; audioMode?: AudioSplitMode; pictureEditAction?: PictureEditMenuAction; frameKind?: VideoFrameCaptureKind; label: string; title?: string; icon: React.ReactNode; onClick: () => void }) {
  return <button data-video-subtitle-mode={subtitleMode} data-video-audio-mode={audioMode} data-video-picture-edit-action={pictureEditAction} data-video-frame-kind={frameKind} type="button" title={title} onClick={onClick} className="flex h-9 w-full items-center gap-2 rounded-lg px-2 text-[#ddd] hover:bg-white/[0.07]">{icon}{label}</button>;
}
