"use client";

import { Check, FileVideo2, LoaderCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import type {
  DirectorAspectRatio,
} from "@/store/directorStore";

export type DirectorExportStatus =
  | "idle"
  | "exporting"
  | "success"
  | "error";

export function DirectorExportPanel({
  open,
  status,
  durationSeconds,
  maxDurationSeconds,
  aspectRatio,
  progress,
  error,
  onDurationChange,
  onAspectRatioChange,
  onSubmit,
}: {
  open: boolean;
  status: DirectorExportStatus;
  durationSeconds: number;
  maxDurationSeconds: number;
  aspectRatio: DirectorAspectRatio;
  progress: number;
  error: string | null;
  onDurationChange: (duration: number) => void;
  onAspectRatioChange: (ratio: DirectorAspectRatio) => void;
  onSubmit: () => void;
}) {
  if (!open) return null;
  const exporting = status === "exporting";

  return (
    <section
      data-director-export-panel
      data-director-export-status={status}
      className="absolute right-2 top-11 z-50 w-[286px] max-w-[calc(100vw-24px)] border border-white/[0.1] bg-[#242424] p-3 shadow-[0_14px_36px_rgba(0,0,0,0.48)]"
    >
      <div className="mb-3 flex items-center gap-2">
        <FileVideo2 size={14} className="text-[#5ddcff]" />
        <h2 className="text-xs font-medium text-[#e4e4e4]">导出设置</h2>
      </div>

      <label className="block">
        <span className="mb-1.5 block text-[11px] text-[#777]">时长</span>
        <span className="flex h-8 items-center rounded border border-white/[0.08] bg-[#1d1d1d] px-2 focus-within:border-[#09caf5]/60">
          <input
            type="number"
            min={1}
            max={maxDurationSeconds}
            step={0.5}
            value={durationSeconds}
            disabled={exporting}
            data-director-export-duration
            onChange={(event) =>
              onDurationChange(Number(event.currentTarget.value))
            }
            className="min-w-0 flex-1 bg-transparent text-right text-[11px] tabular-nums text-[#dedede] outline-none"
          />
          <span className="ml-1 text-[10px] text-[#666]">秒</span>
        </span>
      </label>

      <fieldset className="mt-3 border-0 p-0">
        <legend className="mb-1.5 text-[11px] text-[#777]">比例</legend>
        <div className="grid grid-cols-3 gap-1">
          {(["16:9", "9:16", "1:1"] as const).map((ratio) => (
            <button
              key={ratio}
              type="button"
              disabled={exporting}
              aria-pressed={aspectRatio === ratio}
              data-director-export-aspect={ratio}
              onClick={() => onAspectRatioChange(ratio)}
              className={cn(
                "h-8 rounded border border-white/[0.07] bg-[#1d1d1d] text-[11px] tabular-nums text-[#7d7d7d] hover:text-white disabled:text-[#555]",
                aspectRatio === ratio &&
                  "border-[#09caf5]/40 bg-[#09caf5]/10 text-[#5ddcff]",
              )}
            >
              {ratio}
            </button>
          ))}
        </div>
      </fieldset>

      <div
        data-director-export-progress={Math.round(progress * 100)}
        className="mt-3 h-1 overflow-hidden bg-white/[0.06]"
      >
        <span
          className="block h-full bg-[#09caf5] transition-[width] duration-100"
          style={{ width: `${Math.round(progress * 100)}%` }}
        />
      </div>

      <div className="mt-2 min-h-8">
        {status === "exporting" ? (
          <p className="flex items-center gap-1.5 text-[11px] text-[#a7a7a7]">
            <LoaderCircle size={12} className="animate-spin text-[#5ddcff]" />
            正在导出动画视频... {Math.round(progress * 100)}%
          </p>
        ) : status === "success" ? (
          <p className="flex items-center gap-1.5 text-[11px] text-[#9ddbb9]">
            <Check size={12} />
            动画视频已导出到画布
          </p>
        ) : status === "error" ? (
          <p className="text-[11px] leading-4 text-[#ef9292]">
            {error ?? "动画视频导出失败"}
          </p>
        ) : (
          <p className="text-[10px] leading-4 text-[#626262]">
            输出为当前浏览器支持的视频格式
          </p>
        )}
      </div>

      <button
        type="button"
        data-director-export-submit
        disabled={exporting}
        onClick={onSubmit}
        className="mt-1 flex h-8 w-full items-center justify-center gap-1.5 rounded bg-[#e8e8e8] text-[11px] text-[#202020] hover:bg-white disabled:bg-[#4b4b4b] disabled:text-[#898989]"
      >
        {exporting ? (
          <LoaderCircle size={13} className="animate-spin" />
        ) : (
          <FileVideo2 size={13} />
        )}
        {exporting ? "导出中" : "导出视频到画布"}
      </button>
    </section>
  );
}
