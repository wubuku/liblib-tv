"use client";

import { ArrowUp, LoaderCircle, Sparkles, X } from "lucide-react";
import { NodeToolbar, Position } from "@xyflow/react";

interface SmartMattingPanelProps {
  nodeWidth: number;
  submitting: boolean;
  onCancel: () => void;
  onGenerate: () => void;
}

export function SmartMattingPanel({
  nodeWidth,
  submitting,
  onCancel,
  onGenerate,
}: SmartMattingPanelProps) {
  const panelWidth = Math.min(560, Math.max(360, Math.round(nodeWidth)));

  return (
    <NodeToolbar
      position={Position.Bottom}
      offset={16}
      align="center"
      className="nodrag nopan z-[1001]"
    >
      <div
        data-smart-matting-panel
        className="flex h-12 items-center justify-between gap-8 rounded-xl border border-[#363636] bg-[#262626] p-2 shadow-[0_8px_30px_rgba(0,0,0,0.38)]"
        // The source clamps the compact panel to the selected node's measured width.
        style={{ width: panelWidth }}
        onPointerDown={(event) => event.stopPropagation()}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex min-w-0 items-center gap-3">
          <button
            data-smart-matting-close
            type="button"
            aria-label="关闭智能抠像"
            disabled={submitting}
            onClick={onCancel}
            className="flex size-8 shrink-0 items-center justify-center rounded-lg text-[#8f8f8f] transition-colors hover:bg-white/[0.07] hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            <X size={14} />
          </button>
          <span className="truncate text-[13px] text-[#ededed]">智能抠像</span>
        </div>

        <div className="flex shrink-0 items-center gap-3">
          <span
            data-smart-matting-power
            className="flex items-center gap-1.5 text-xs text-[#8d8d8d]"
          >
            <Sparkles size={14} />
            <span>--</span>
          </span>
          <button
            data-smart-matting-generate
            type="button"
            aria-label="生成智能抠像"
            disabled={submitting}
            onClick={onGenerate}
            className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-[#ededed] text-[#292929] transition-[filter,opacity] hover:brightness-110 active:brightness-95 disabled:cursor-wait disabled:opacity-60"
          >
            {submitting ? (
              <LoaderCircle
                data-smart-matting-submitting
                size={15}
                className="animate-spin"
              />
            ) : (
              <ArrowUp size={15} />
            )}
          </button>
        </div>
      </div>
    </NodeToolbar>
  );
}
