"use client";

import Image from "next/image";
import { memo, useEffect, useRef, useState } from "react";
import { AlertTriangle, Camera, CaptionsOff, Play, ScanLine, Volume2, VolumeX } from "lucide-react";
import {
  Handle,
  Position,
  useInternalNode,
  useReactFlow,
  useViewport,
  type Node,
  type NodeProps,
} from "@xyflow/react";
import { cn } from "@/lib/utils";
import {
  useCanvasStore,
  type AudioSplitMetadata,
  type AudioSplitMode,
  type PictureEditAction,
  type SmartMattingMetadata,
  type SubtitleEraseMetadata,
  type SubtitleEraseMode,
  type SubtitleEraseRegion,
  type VideoFrameCaptureKind,
  type VideoContinuationMetadata,
} from "@/store/canvasStore";
import { SegmentReshootPanel } from "@/components/SegmentReshootPanel";
import { SmartMattingPanel } from "@/components/SmartMattingPanel";
import { SubtitleErasePanel } from "@/components/SubtitleErasePanel";
import { VideoContinuationSelector } from "@/components/VideoContinuationSelector";
import { VideoGenerationPanel } from "@/components/VideoGenerationPanel";
import { VideoProcessingToolbar } from "@/components/VideoProcessingToolbar";

export interface VideoNodeData extends Record<string, unknown> {
  filename?: string;
  model?: string;
  status?: "empty" | "failed" | "ready" | "pending";
  durationSeconds?: number;
  resolution?: string;
  posterUrl?: string;
  prompt?: string;
  continuation?: VideoContinuationMetadata;
  subtitleErase?: SubtitleEraseMetadata;
  audioSplit?: AudioSplitMetadata;
  smartMatting?: SmartMattingMetadata;
}

export type VideoNodeType = Node<VideoNodeData, "video">;

function VideoNodeComponent({ id, data, selected }: NodeProps<VideoNodeType>) {
  const { filename = "分镜视频-#9", model = "vip专属模型-会员", status = "failed", posterUrl, durationSeconds = 30, resolution = "1280 × 720", prompt, continuation, subtitleErase, audioSplit, smartMatting } = data;
  const { zoom } = useViewport();
  const internalNode = useInternalNode(id);
  const { setCenter } = useReactFlow();
  const addDerivedNode = useCanvasStore((state) => state.addDerivedNode);
  const createVideoContinuation = useCanvasStore((state) => state.createVideoContinuation);
  const createSubtitleErase = useCanvasStore((state) => state.createSubtitleErase);
  const createAudioSplit = useCanvasStore((state) => state.createAudioSplit);
  const createVideoFrameCapture = useCanvasStore(
    (state) => state.createVideoFrameCapture,
  );
  const createSmartMatting = useCanvasStore(
    (state) => state.createSmartMatting,
  );
  const clearVideoContinuation = useCanvasStore((state) => state.clearVideoContinuation);
  const selectedNodeCount = useCanvasStore((state) => state.selectedNodeIds.length);
  const showSingleNodeEditor = selected && selectedNodeCount <= 1;
  const [activeTool, setActiveTool] = useState<
    | "generator"
    | "reshoot"
    | "continue"
    | "subtitle-smart"
    | "subtitle-region"
    | "matting"
  >("generator");
  const [enhanced, setEnhanced] = useState(false);
  const [audioSplittingMode, setAudioSplittingMode] =
    useState<AudioSplitMode | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [frameFeedback, setFrameFeedback] = useState<string | null>(null);
  const [pictureEditFeedback, setPictureEditFeedback] = useState<string | null>(
    null,
  );
  const [mattingSubmitting, setMattingSubmitting] = useState(false);
  const audioSplitTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const frameFeedbackTimerRef = useRef<ReturnType<typeof setTimeout> | null>(
    null,
  );
  const pictureEditFeedbackTimerRef =
    useRef<ReturnType<typeof setTimeout> | null>(null);
  const mattingTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const subtitleMode: SubtitleEraseMode | null =
    activeTool === "subtitle-smart"
      ? "smart"
      : activeTool === "subtitle-region"
        ? "region"
        : null;

  useEffect(() => {
    return () => {
      if (audioSplitTimerRef.current) {
        clearTimeout(audioSplitTimerRef.current);
      }
      if (frameFeedbackTimerRef.current) {
        clearTimeout(frameFeedbackTimerRef.current);
      }
      if (pictureEditFeedbackTimerRef.current) {
        clearTimeout(pictureEditFeedbackTimerRef.current);
      }
      if (mattingTimerRef.current) {
        clearTimeout(mattingTimerRef.current);
      }
    };
  }, []);

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

  const confirmSubtitleErase = (
    mode: SubtitleEraseMode,
    regions: SubtitleEraseRegion[],
  ) => {
    setActiveTool("generator");
    createSubtitleErase(id, mode, regions);
  };

  const selectSubtitleMode = (mode: SubtitleEraseMode) => {
    setActiveTool(mode === "smart" ? "subtitle-smart" : "subtitle-region");
    if (mode !== "region" || !internalNode) return;
    const position = internalNode.internals.positionAbsolute;
    const width = internalNode.measured.width ?? internalNode.width ?? 512;
    const height = internalNode.measured.height ?? internalNode.height ?? 288;
    void setCenter(position.x + width / 2, position.y + height / 2, {
      zoom: Math.max(zoom, 1),
      duration: 220,
    });
  };

  const startAudioSplit = (mode: AudioSplitMode) => {
    if (audioSplittingMode || audioSplitTimerRef.current) return;
    setAudioSplittingMode(mode);
    audioSplitTimerRef.current = setTimeout(() => {
      audioSplitTimerRef.current = null;
      createAudioSplit(id, mode);
      setAudioSplittingMode(null);
    }, 600);
  };

  const captureFrame = (kind: VideoFrameCaptureKind) => {
    const resultId = createVideoFrameCapture(id, kind, currentTime);
    if (!resultId) {
      if (kind === "last") {
        setFrameFeedback("视频尚未加载完成，暂时无法截取尾帧");
      }
      return;
    }
    const nameByKind: Record<VideoFrameCaptureKind, string> = {
      first: "首帧",
      last: "尾帧",
      current: "截图",
    };
    setFrameFeedback(`${nameByKind[kind]}已截取，并添加到画布`);
    if (frameFeedbackTimerRef.current) {
      clearTimeout(frameFeedbackTimerRef.current);
    }
    frameFeedbackTimerRef.current = setTimeout(() => {
      frameFeedbackTimerRef.current = null;
      setFrameFeedback(null);
    }, 1400);
  };

  const showPictureEditFeedback = (message: string) => {
    setPictureEditFeedback(message);
    if (pictureEditFeedbackTimerRef.current) {
      clearTimeout(pictureEditFeedbackTimerRef.current);
    }
    pictureEditFeedbackTimerRef.current = setTimeout(() => {
      pictureEditFeedbackTimerRef.current = null;
      setPictureEditFeedback(null);
    }, 1800);
  };

  const selectPictureEdit = (action: PictureEditAction) => {
    void action;
    if (durationSeconds > 15) {
      showPictureEditFeedback("视频大于15秒，暂不支持该功能");
      return;
    }
    if (durationSeconds < 2.5) {
      showPictureEditFeedback(
        `源视频时长需在 3~15 秒之间（当前 ${durationSeconds} 秒）`,
      );
    }
  };

  const openSmartMatting = () => {
    if (mattingSubmitting) return;
    setActiveTool("matting");
  };

  const submitSmartMatting = () => {
    if (mattingSubmitting || mattingTimerRef.current) return;
    setMattingSubmitting(true);
    mattingTimerRef.current = setTimeout(() => {
      mattingTimerRef.current = null;
      createSmartMatting(id);
      setMattingSubmitting(false);
      setActiveTool("generator");
    }, 480);
  };

  return (
    <div
      className={cn(
        "group relative flex h-full w-full flex-col overflow-visible rounded-[3px] border bg-[#242424]",
        selected ? "border-[#09caf5] shadow-[0_0_0_2px_rgba(9,202,245,0.22)]" : "border-white/[0.07]",
      )}
    >
      {showSingleNodeEditor && status === "ready" && !subtitleMode && (
        <VideoProcessingToolbar
          activeTool={
            activeTool === "reshoot" || activeTool === "continue"
              ? activeTool
              : "generator"
          }
          enhanced={enhanced}
          posterUrl={posterUrl}
          onSelectTool={setActiveTool}
          onToggleEnhanced={() => setEnhanced((value) => !value)}
          onCreateBreakdown={createBreakdown}
          onSelectSubtitleMode={selectSubtitleMode}
          onAudioSplit={startAudioSplit}
          onPictureEdit={selectPictureEdit}
          onSmartMatting={openSmartMatting}
          onCaptureFrame={captureFrame}
          audioSplittingMode={audioSplittingMode}
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
            {frameFeedback && (
              <span
                data-video-frame-feedback
                className="absolute left-1/2 top-3 z-20 -translate-x-1/2 whitespace-nowrap rounded-lg bg-black/70 px-3 py-1.5 text-[11px] text-white shadow-lg backdrop-blur-md"
              >
                {frameFeedback}
              </span>
            )}
            {pictureEditFeedback && (
              <span
                data-video-picture-edit-feedback
                className="absolute left-1/2 top-3 z-20 -translate-x-1/2 whitespace-nowrap rounded-lg bg-black/70 px-3 py-1.5 text-[11px] text-white shadow-lg backdrop-blur-md"
              >
                {pictureEditFeedback}
              </span>
            )}
            <div
              className="absolute bottom-0 left-0 right-0 z-10 flex items-center gap-2 bg-gradient-to-b from-transparent via-black/25 to-black/55 px-3 pb-2.5 pt-8 text-[11px] text-white"
              onPointerDown={(event) => event.stopPropagation()}
              onClick={(event) => event.stopPropagation()}
            >
              <Play size={12} fill="currentColor" />
              <span>{formatVideoTime(currentTime)}</span>
              <input
                data-video-playhead
                aria-label="视频播放进度"
                type="range"
                min={0}
                max={durationSeconds}
                step={0.05}
                value={currentTime}
                onChange={(event) => setCurrentTime(Number(event.target.value))}
                className="h-1 min-w-0 flex-1 cursor-pointer accent-white"
              />
              <span>00:{String(durationSeconds).padStart(2, "0")}</span>
              <Volume2 size={13} />
              <PlayerFrameCaptureMenu onCapture={captureFrame} />
            </div>
          </>
        ) : status === "empty" ? (
          <div data-video-continuation-empty className="flex flex-col items-center gap-2 text-center">
            <span className="flex size-14 items-center justify-center rounded-full bg-white/[0.05] text-[#777]">
              <Play size={22} fill="currentColor" className="ml-1" />
            </span>
            <span className="text-xs text-[#777]">等待续写内容</span>
          </div>
        ) : smartMatting ? (
          <div
            data-smart-matting-output
            data-smart-matting-source-id={smartMatting.sourceNodeId}
            data-smart-matting-edge-id={smartMatting.edgeId}
            data-smart-matting-provider={smartMatting.provider}
            data-smart-matting-model={smartMatting.model}
            data-smart-matting-format={smartMatting.format}
            data-smart-matting-width={smartMatting.width}
            data-smart-matting-height={smartMatting.height}
            data-smart-matting-duration={smartMatting.duration}
            className="flex flex-col items-center gap-2 px-6 text-center"
          >
            <span className="flex size-12 items-center justify-center rounded-full bg-white/[0.05] text-[#858585]">
              <ScanLine size={23} strokeWidth={1.5} />
            </span>
            <span className="text-xs text-[#a0a0a0]">智能抠像结果</span>
            <span className="text-[10px] text-[#626262]">
              智能抠像 · 等待媒体资源
            </span>
          </div>
        ) : audioSplit ? (
          <div
            data-audio-split-output
            data-audio-split-mode={audioSplit.mode}
            data-audio-split-output-kind={audioSplit.outputKind}
            data-audio-split-source-id={audioSplit.sourceNodeId}
            data-audio-split-edge-id={audioSplit.edgeId}
            className="flex flex-col items-center gap-2 px-6 text-center"
          >
            <span className="flex size-12 items-center justify-center rounded-full bg-white/[0.05] text-[#858585]">
              <VolumeX size={23} strokeWidth={1.5} />
            </span>
            <span className="text-xs text-[#a0a0a0]">无声视频结果</span>
            <span className="text-[10px] text-[#626262]">
              音视频分离 · 等待媒体资源
            </span>
          </div>
        ) : (
          <div
            data-subtitle-erase-target
            data-subtitle-erase-target-mode={subtitleErase?.mode}
            data-subtitle-erase-request-mode={subtitleErase?.requestMode}
            data-subtitle-erase-model={subtitleErase?.model}
            className="flex flex-col items-center gap-2 px-6 text-center"
          >
            <CaptionsOff size={28} strokeWidth={1.4} className="text-[#777]" />
            <span
              data-subtitle-erase-pending-copy
              className="text-xs leading-5 text-[#777]"
            >
              {subtitleErase?.mode === "region"
                ? "框选区域生成去字幕视频"
                : "点击生成自动去除字幕"}
            </span>
          </div>
        )}
      </div>

      {showSingleNodeEditor && activeTool === "generator" && status !== "pending" && (
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
      {showSingleNodeEditor && status === "ready" && subtitleMode && (
        <SubtitleErasePanel
          zoom={zoom}
          mode={subtitleMode}
          onCancel={() => setActiveTool("generator")}
          onConfirm={confirmSubtitleErase}
        />
      )}
      {showSingleNodeEditor && status === "ready" && activeTool === "matting" && (
        <SmartMattingPanel
          nodeWidth={
            internalNode?.measured.width ?? internalNode?.width ?? 512
          }
          submitting={mattingSubmitting}
          onCancel={() => setActiveTool("generator")}
          onGenerate={submitSmartMatting}
        />
      )}
    </div>
  );
}

export const VideoNode = memo(VideoNodeComponent);

function PlayerFrameCaptureMenu({
  onCapture,
}: {
  onCapture: (kind: VideoFrameCaptureKind) => void;
}) {
  const [open, setOpen] = useState(false);
  const items: Array<{ kind: VideoFrameCaptureKind; label: string }> = [
    { kind: "first", label: "截取首帧" },
    { kind: "last", label: "截取尾帧" },
    { kind: "current", label: "截取当前帧" },
  ];

  return (
    <div
      className="relative shrink-0"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <div
        data-video-player-frame-menu
        data-state={open ? "open" : "closed"}
        className={cn(
          "absolute bottom-full right-0 z-30 flex justify-end pb-2 transition-opacity",
          open ? "pointer-events-auto opacity-100" : "pointer-events-none opacity-0",
        )}
      >
        <div className="flex flex-col gap-1 overflow-hidden rounded-xl border border-white/10 bg-[rgba(26,26,26,0.95)] p-1 shadow-[0_4px_10px_rgba(0,0,0,0.25),0_2px_4px_rgba(0,0,0,0.1)] backdrop-blur-lg">
          {items.map((item) => (
            <button
              key={item.kind}
              data-video-player-frame-kind={item.kind}
              type="button"
              onClick={() => onCapture(item.kind)}
              className="flex h-8 w-full items-center whitespace-nowrap rounded-lg px-2 text-left text-[13px] text-white/90 transition-colors hover:bg-white/10"
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>
      <button
        data-video-player-camera
        type="button"
        aria-label="截取当前帧"
        onClick={() => onCapture("current")}
        className="flex size-7 shrink-0 items-center justify-center rounded-full transition-colors hover:bg-black/50"
      >
        <Camera size={16} />
      </button>
    </div>
  );
}

function formatVideoTime(seconds: number): string {
  const safeSeconds = Math.max(0, Math.floor(seconds));
  const minutes = Math.floor(safeSeconds / 60);
  const remainder = safeSeconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`;
}
