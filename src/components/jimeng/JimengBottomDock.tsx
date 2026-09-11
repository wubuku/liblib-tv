"use client";

import { Columns2, MousePointer2, RefreshCw } from "lucide-react";

import { useJimengStore } from "@/store/jimengStore";

/**
 * 左下角画布导航 dock — 16,774 164×36 (SOURCE_FACT)。
 * [选择][布局][同步] | 缩放百分比；缩放值来自 store (与 xyflow viewport 同步)。
 */
export function JimengBottomDock() {
  const zoomPercent = useJimengStore((s) => s.zoomPercent);

  return (
    <div className="absolute bottom-4 left-4 z-30">
      <div className="jimeng-bottom-dock flex h-9 w-[164px] items-center gap-1 p-1">
        <button
          type="button"
          aria-label="选择工具"
          className="flex size-7 items-center justify-center rounded-md text-white/85 hover:bg-white/10"
        >
          <MousePointer2 size={16} />
        </button>
        <button
          type="button"
          aria-label="布局"
          className="flex size-7 items-center justify-center rounded-md text-white/85 hover:bg-white/10"
        >
          <Columns2 size={16} />
        </button>
        <button
          type="button"
          aria-label="同步"
          className="flex size-7 items-center justify-center rounded-md bg-white/10 text-white"
        >
          <RefreshCw size={16} />
        </button>
        <span className="mx-1 h-3 w-px shrink-0 bg-white/10" />
        <button
          type="button"
          aria-label="缩放"
          className="flex h-7 w-12 items-center justify-center rounded-md text-[13px] text-white/85 hover:bg-white/10"
        >
          {zoomPercent}%
        </button>
      </div>
    </div>
  );
}
