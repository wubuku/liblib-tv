"use client";

import Image from "next/image";
import { memo, useEffect, useRef, useState } from "react";
import { Film, Images, Link2, LoaderCircle, Music2, Upload } from "lucide-react";
import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import { cn } from "@/lib/utils";
import { useCanvasStore } from "@/store/canvasStore";
import type { ShotBreakdownDimension } from "@/lib/shotBreakdownResults";

type BreakdownStatus = "empty" | "ready" | "running" | "complete" | "failed";

export interface ShotBreakdownNodeData extends Record<string, unknown> {
  title?: string;
  status?: BreakdownStatus;
  sourceName?: string;
  sourceDuration?: number;
  sourcePosterUrl?: string;
  sourceResolution?: string;
  dimensions?: ShotBreakdownDimension[];
  resultNodeIds?: string[];
}

export type ShotBreakdownNodeType = Node<ShotBreakdownNodeData, "shot-breakdown">;

const dimensions: Array<{ id: ShotBreakdownDimension; label: string; icon: typeof Images }> = [
  { id: "storyboard", label: "分镜", icon: Images },
  { id: "motion", label: "动态", icon: Film },
  { id: "music", label: "音乐", icon: Music2 },
];

function ShotBreakdownNodeComponent({ id, data, selected }: NodeProps<ShotBreakdownNodeType>) {
  const updateNodeData = useCanvasStore((state) => state.updateNodeData);
  const completeShotBreakdown = useCanvasStore((state) => state.completeShotBreakdown);
  const [sourceMenuOpen, setSourceMenuOpen] = useState(false);
  const [localPreviewUrl, setLocalPreviewUrl] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const status = data.status ?? "empty";
  const activeDimensions = data.dimensions ?? ["storyboard", "motion", "music"];
  const posterUrl = localPreviewUrl ?? data.sourcePosterUrl;

  useEffect(() => () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    if (localPreviewUrl) URL.revokeObjectURL(localPreviewUrl);
  }, [localPreviewUrl]);

  const chooseCanvasVideo = () => {
    updateNodeData(id, {
      status: "ready",
      sourceName: "咖啡馆漫步",
      sourceDuration: 30,
      sourcePosterUrl: "/images/scene-coffee-4.png",
      sourceResolution: "1280×720",
    });
    setSourceMenuOpen(false);
  };

  const toggleDimension = (dimension: ShotBreakdownDimension) => {
    const next = activeDimensions.includes(dimension)
      ? activeDimensions.filter((item) => item !== dimension)
      : [...activeDimensions, dimension];
    updateNodeData(id, { dimensions: next });
  };

  const startBreakdown = () => {
    if (
      status === "empty" ||
      status === "complete" ||
      isRunning ||
      activeDimensions.length === 0
    ) {
      return;
    }
    setIsRunning(true);
    timerRef.current = setTimeout(() => {
      completeShotBreakdown(id, activeDimensions);
      setIsRunning(false);
    }, 700);
  };

  return (
    <div
      data-shot-breakdown-node
      className={cn(
        "node-shell relative flex h-full w-full flex-col overflow-visible rounded-2xl border bg-[#242424] p-3",
        selected ? "border-[#09caf5] shadow-[0_0_0_2px_rgba(9,202,245,0.18)]" : "border-white/10",
      )}
    >
      <Handle type="target" position={Position.Left} id="target" style={{ width: 20, height: 20 }} />
      <Handle type="source" position={Position.Right} id="source" style={{ width: 20, height: 20 }} />

      <div className="pointer-events-none absolute -top-8 left-0 flex items-center gap-2 whitespace-nowrap text-sm text-[#858585]">
        <Film size={14} />
        <span>{data.title ?? "逐帧拉片"}</span>
      </div>

      <div className="mb-3 flex h-7 items-center gap-2 text-sm font-semibold text-[#f1f1f1]">
        <Film size={17} />
        <span>逐帧拉片</span>
        <span className="rounded bg-[#0e5560] px-1.5 py-0.5 text-[10px] font-medium text-[#36d4ed]">SD 2.5</span>
      </div>

      <div className="mb-2 flex items-center text-xs text-[#858585]">
        <span>视频素材</span>
        {posterUrl && (
          <span
            data-shot-breakdown-source-meta
            className="ml-auto tabular-nums text-[#6f6f6f]"
          >
            00:{String(data.sourceDuration ?? 30).padStart(2, "0")} ·{" "}
            {data.sourceResolution ?? "1280×720"}
          </span>
        )}
      </div>
      <div className="relative">
        <button
          type="button"
          data-shot-breakdown-media
          onClick={() => setSourceMenuOpen((open) => !open)}
          className="nodrag nopan relative flex aspect-[294/165] w-full flex-col items-center justify-center gap-3 overflow-hidden rounded-xl border border-dashed border-[#363636] bg-[#1f1f1f] text-sm text-[#8f8f8f] transition-colors hover:bg-white/[0.04] hover:text-white"
        >
          {posterUrl ? (
            <Image src={posterUrl} alt="拉片视频素材" fill sizes="294px" className="object-cover" unoptimized />
          ) : (
            <>
              <Upload size={24} strokeWidth={1.5} />
              <span>上传视频后开始</span>
            </>
          )}
        </button>

        {sourceMenuOpen && (
          <div className="nodrag nopan absolute left-1/2 top-1/2 z-30 w-44 -translate-x-1/2 -translate-y-1/2 rounded-xl border border-white/10 bg-[#2a2a2a] p-1.5 text-xs shadow-2xl">
            <button type="button" onClick={() => fileRef.current?.click()} className="flex h-9 w-full items-center gap-2 rounded-lg px-2 text-[#e8e8e8] hover:bg-white/[0.07]">
              <Upload size={14} /> 上传视频
            </button>
            <button type="button" onClick={chooseCanvasVideo} className="flex h-9 w-full items-center gap-2 rounded-lg px-2 text-[#e8e8e8] hover:bg-white/[0.07]">
              <Link2 size={14} /> 从画布选择
            </button>
          </div>
        )}
        <input
          ref={fileRef}
          type="file"
          accept="video/*"
          className="hidden"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (!file) return;
            if (localPreviewUrl) URL.revokeObjectURL(localPreviewUrl);
            setLocalPreviewUrl(URL.createObjectURL(file));
            updateNodeData(id, { status: "ready", sourceName: file.name, sourceDuration: 30 });
            setSourceMenuOpen(false);
          }}
        />
      </div>

      <p className="mb-2 mt-3 text-xs text-[#858585]">拆解维度</p>
      <div className="flex gap-2">
        {dimensions.map((dimension) => {
          const Icon = dimension.icon;
          const active = activeDimensions.includes(dimension.id);
          return (
            <button
              key={dimension.id}
              type="button"
              data-shot-breakdown-dimension={dimension.id}
              onClick={() => toggleDimension(dimension.id)}
              aria-pressed={active}
              className={cn(
                "nodrag nopan flex h-8 min-w-0 flex-1 items-center justify-center gap-1.5 rounded-full border px-2 text-[13px]",
                active ? "border-[#5ddcff]/20 bg-[#09caf5]/10 text-[#09caf5]" : "border-white/10 text-[#777] hover:text-white",
              )}
            >
              <Icon size={14} />
              <span>{dimension.label}</span>
            </button>
          );
        })}
      </div>

      <button
        type="button"
        data-shot-breakdown-start
        onClick={startBreakdown}
        disabled={
          status === "empty" ||
          status === "complete" ||
          isRunning ||
          activeDimensions.length === 0
        }
        className="nodrag nopan mt-3 flex h-9 w-full items-center justify-center gap-2 rounded-[10px] bg-white text-sm font-medium text-[#202020] transition-colors hover:bg-[#ededed] disabled:cursor-not-allowed disabled:bg-white/[0.08] disabled:text-[#525252]"
      >
        {isRunning && <LoaderCircle size={15} className="animate-spin" />}
        {isRunning ? "拉片中" : status === "complete" ? "拉片完成" : "开始拉片"}
      </button>
    </div>
  );
}

export const ShotBreakdownNode = memo(ShotBreakdownNodeComponent);
