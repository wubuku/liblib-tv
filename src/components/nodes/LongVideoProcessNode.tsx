"use client";

import Image from "next/image";
import { memo } from "react";
import { Film, GitMerge, Images, Layers3, Sparkles } from "lucide-react";
import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import { cn } from "@/lib/utils";
import type {
  LongVideoProcessMetadata,
  LongVideoProcessStage,
} from "@/store/canvasStore";

export interface LongVideoProcessNodeData extends Record<string, unknown> {
  title: string;
  subtitle: string;
  imageUrl?: string;
  longVideoProcess: LongVideoProcessMetadata;
}

export type LongVideoProcessNodeType = Node<
  LongVideoProcessNodeData,
  "long-video-process"
>;

const stageLabels: Record<LongVideoProcessStage, string> = {
  material: "输入素材",
  shot: "镜头计划",
  candidate: "候选批次",
  assembly: "处理节点",
  final: "最终成片",
};

const stageIcons: Record<LongVideoProcessStage, typeof Film> = {
  material: Images,
  shot: Film,
  candidate: Sparkles,
  assembly: GitMerge,
  final: Layers3,
};

function LongVideoProcessNodeComponent({
  data,
  selected,
}: NodeProps<LongVideoProcessNodeType>) {
  const metadata = data.longVideoProcess;
  const stage = metadata.stage;
  const StageIcon = stageIcons[stage];
  const showTarget = stage !== "material";
  const showSource = stage !== "final";
  const showImage = Boolean(data.imageUrl) && stage !== "assembly";
  const isPendingMedia = stage === "candidate" || stage === "final";

  return (
    <div
      data-long-video-process-node
      data-long-video-process-id={metadata.processId}
      data-long-video-process-stage={stage}
      data-long-video-process-stage-index={metadata.stageIndex}
      data-long-video-process-batch-index={metadata.batchIndex}
      data-long-video-process-source-id={metadata.sourceNodeId}
      data-long-video-process-status={metadata.status}
      data-long-video-process-model={metadata.model}
      data-long-video-process-ratio={metadata.ratio}
      data-long-video-process-resolution={metadata.resolution}
      data-long-video-process-duration={metadata.durationSeconds}
      data-long-video-process-audio={String(metadata.audio)}
      data-long-video-process-credits={metadata.credits}
      data-long-video-process-reference-count={metadata.referenceCount}
      data-long-video-process-prompt-length={metadata.prompt.length}
      className={cn(
        "group relative flex h-full w-full flex-col overflow-visible rounded-[6px] border bg-[#242424]",
        selected
          ? "border-[#09caf5] shadow-[0_0_0_2px_rgba(9,202,245,0.2)]"
          : "border-white/[0.09]",
      )}
    >
      {showTarget && (
        <Handle
          type="target"
          position={Position.Left}
          id="target"
          style={{ width: 20, height: 20 }}
        />
      )}
      {showSource && (
        <Handle
          type="source"
          position={Position.Right}
          id="source"
          style={{ width: 20, height: 20 }}
        />
      )}

      <header className="flex h-8 shrink-0 items-center gap-2 border-b border-white/[0.06] px-2.5">
        <StageIcon size={13} className="shrink-0 text-[#8c939d]" />
        <span className="min-w-0 flex-1 truncate text-[10px] text-[#8c939d]">
          {stageLabels[stage]}
        </span>
        <span className="rounded-[4px] bg-white/[0.05] px-1.5 py-0.5 text-[9px] tabular-nums text-[#6f747b]">
          {stage === "candidate" && metadata.batchIndex
            ? `B${metadata.batchIndex}`
            : String(metadata.stageIndex).padStart(2, "0")}
        </span>
      </header>

      {stage === "assembly" ? (
        <div className="flex min-h-0 flex-1 items-center gap-3 px-3">
          <span className="flex size-10 shrink-0 items-center justify-center rounded-[6px] bg-[#1c3034] text-[#35cbe7]">
            <GitMerge size={20} />
          </span>
          <div className="min-w-0">
            <p className="truncate text-xs font-medium text-[#e2e2e2]">
              {data.title}
            </p>
            <p className="mt-1 truncate text-[10px] text-[#747474]">
              {data.subtitle}
            </p>
          </div>
        </div>
      ) : (
        <div className="flex min-h-0 flex-1 gap-2 p-2">
          {showImage && (
            <div className="relative h-full w-[44%] shrink-0 overflow-hidden rounded-[4px] bg-[#1b1b1b]">
              <Image
                src={data.imageUrl ?? "/images/scene-coffee-4.png"}
                alt={data.title}
                fill
                sizes="160px"
                className={cn(
                  "object-cover",
                  isPendingMedia && "opacity-35 saturate-50",
                )}
                unoptimized
              />
              {isPendingMedia && (
                <span className="absolute inset-0 flex items-center justify-center bg-black/35 text-[9px] text-[#d3d3d3]">
                  {stage === "final" ? "等待拼接" : "等待生成"}
                </span>
              )}
            </div>
          )}
          <div className="flex min-w-0 flex-1 flex-col justify-center">
            <p className="line-clamp-2 text-xs font-medium leading-4 text-[#e2e2e2]">
              {data.title}
            </p>
            <p className="mt-1 line-clamp-2 text-[10px] leading-4 text-[#747474]">
              {data.subtitle}
            </p>
            {stage === "final" && (
              <span className="mt-2 w-fit rounded-[4px] bg-[#17343a] px-1.5 py-0.5 text-[9px] text-[#3bd5ef]">
                Beta · 本地流程
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export const LongVideoProcessNode = memo(LongVideoProcessNodeComponent);
