"use client";

import { ArrowUp, LoaderCircle, ScanLine, X } from "lucide-react";
import { NodeToolbar, Position } from "@xyflow/react";
import { cn } from "@/lib/utils";
import type { DepthMotionCaptureResolution } from "@/store/canvasStore";

interface DepthMotionCapturePanelProps {
  nodeWidth: number;
  sourceLabel: string;
  durationSeconds: number;
  sourceResolution: string;
  resolution: DepthMotionCaptureResolution;
  submitting: boolean;
  onResolutionChange: (resolution: DepthMotionCaptureResolution) => void;
  onCancel: () => void;
  onConfirm: () => void;
}

const resolutionOptions: DepthMotionCaptureResolution[] = ["720P", "1080P"];

export function DepthMotionCapturePanel({
  nodeWidth,
  sourceLabel,
  durationSeconds,
  sourceResolution,
  resolution,
  submitting,
  onResolutionChange,
  onCancel,
  onConfirm,
}: DepthMotionCapturePanelProps) {
  const panelWidth = Math.min(660, Math.max(512, Math.round(nodeWidth)));

  return (
    <NodeToolbar
      position={Position.Bottom}
      offset={16}
      align="center"
      className="nodrag nopan z-[1001]"
    >
      <section
        data-depth-motion-panel
        className="flex flex-col gap-3 rounded-xl border border-[#363636] bg-[#262626] p-3 shadow-[0_12px_36px_rgba(0,0,0,0.42)]"
        style={{ width: panelWidth }}
        onPointerDown={(event) => event.stopPropagation()}
        onClick={(event) => event.stopPropagation()}
      >
        <header className="flex items-start gap-3">
          <button
            data-depth-motion-close
            type="button"
            aria-label="关闭深度动作捕捉"
            disabled={submitting}
            onClick={onCancel}
            className="flex size-8 shrink-0 items-center justify-center rounded-lg text-[#8f8f8f] transition-colors hover:bg-white/[0.07] hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            <X size={14} />
          </button>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <ScanLine size={15} className="shrink-0 text-[#09caf5]" />
              <span
                data-depth-motion-title
                className="text-[13px] font-medium text-[#ededed]"
              >
                深度动作捕捉
              </span>
            </div>
            <p
              data-depth-motion-intro
              className="mt-1.5 max-w-[520px] text-[11px] leading-5 text-[#999]"
            >
              提取视频深度信息，为镜头运动、人物动作和空间关系提供参考，减少原视频细节对生成结果的干扰。
            </p>
          </div>
        </header>

        <div
          data-depth-motion-source-summary
          className="flex min-w-0 items-center justify-between gap-3 rounded-lg bg-[#1d1d1d] px-3 py-2 text-[11px] text-[#999]"
        >
          <span className="min-w-0 truncate text-[#d6d6d6]">{sourceLabel}</span>
          <span className="shrink-0 tabular-nums">
            {durationSeconds}s · {sourceResolution}
          </span>
        </div>

        <div className="flex items-center gap-3">
          <span
            data-depth-motion-resolution
            className="shrink-0 text-[11px] text-[#999]"
          >
            清晰度
          </span>
          <div className="flex min-w-0 flex-1 gap-1.5">
            {resolutionOptions.map((option) => (
              <button
                key={option}
                data-depth-motion-resolution-option={option}
                type="button"
                aria-pressed={resolution === option}
                disabled={submitting}
                onClick={() => onResolutionChange(option)}
                className={cn(
                  "flex h-8 min-w-0 flex-1 items-center justify-center rounded-lg border text-xs transition-colors disabled:cursor-not-allowed disabled:opacity-60",
                  resolution === option
                    ? "border-[#09caf5]/70 bg-[#09caf5]/[0.12] text-[#e7fcff]"
                    : "border-white/[0.08] text-[#999] hover:border-white/20 hover:bg-white/[0.05] hover:text-white",
                )}
              >
                {option}
              </button>
            ))}
          </div>
          <button
            data-depth-motion-submit
            type="button"
            aria-label="确认提取深度动作捕捉"
            title="确认提取"
            disabled={submitting}
            onClick={onConfirm}
            className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-[#ededed] text-[#292929] transition-[filter,opacity] hover:brightness-110 active:brightness-95 disabled:cursor-wait disabled:opacity-60"
          >
            {submitting ? (
              <LoaderCircle
                data-depth-motion-spinner
                size={15}
                className="animate-spin"
              />
            ) : (
              <ArrowUp size={15} />
            )}
          </button>
        </div>
        <span
          data-depth-motion-submit-reason
          className="sr-only"
          aria-live="polite"
        >
          {submitting ? "提取中" : "确认提取"}
        </span>
      </section>
    </NodeToolbar>
  );
}
