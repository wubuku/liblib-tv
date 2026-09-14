"use client";

import { useState } from "react";
import { Map, MousePointer2, Spline } from "lucide-react";

import { JimengZoomMenu } from "@/components/jimeng/JimengZoomMenu";
import { useJimengStore } from "@/store/jimengStore";

/**
 * 左下角画布导航 dock — 16,774 164×36 (SOURCE_FACT)。
 * Batch 91 (SOURCE_FACT 91-minimap.json): dock 演进为 [选择工具][小地图] |
 * 缩放百分比 (布局 已并入多选工具条、同步 由自动保存取代——均站点演进)；
 * 小地图 点击切换左上 MiniMap 面板 (164×154 rgb(13,13,13) r8，内
 * 156×114 white/8% r6)。
 */
export function JimengBottomDock() {
  const zoomPercent = useJimengStore((s) => s.zoomPercent);
  const toolActive = useJimengStore((s) => s.toolActive);
  const setToolActive = useJimengStore((s) => s.setToolActive);
  const minimapOpen = useJimengStore((s) => s.minimapOpen);
  const setMinimapOpen = useJimengStore((s) => s.setMinimapOpen);
  const edgesVisible = useJimengStore((s) => s.edgesVisible);
  const setEdgesVisible = useJimengStore((s) => s.setEdgesVisible);
  const [zoomMenuOpen, setZoomMenuOpen] = useState(false);

  return (
    <div className="absolute bottom-4 left-4 z-30">
      <div className="jimeng-bottom-dock relative flex h-9 w-[164px] items-center gap-1 p-1">
        <button
          type="button"
          aria-label="选择工具"
          onClick={() => setToolActive("select")}
          className={`flex size-7 items-center justify-center rounded-md ${
            toolActive === "select"
              ? "bg-white/10 text-white"
              : "text-white/85 hover:bg-white/10"
          }`}
        >
          <MousePointer2 size={16} />
        </button>
        <button
          type="button"
          aria-label="小地图"
          data-testid="dock-minimap"
          onClick={() => setMinimapOpen(!minimapOpen)}
          className={`flex size-7 items-center justify-center rounded-md ${
            minimapOpen ? "bg-white/10 text-white" : "text-white/85 hover:bg-white/10"
          }`}
        >
          <Map size={16} />
        </button>
        {/* Batch 93 (SOURCE_FACT canvas-dock-lines): 连线显隐开关 */}
        <button
          type="button"
          aria-label="显示连线"
          data-testid="dock-edges"
          onClick={() => setEdgesVisible(!edgesVisible)}
          className={`flex size-7 items-center justify-center rounded-md ${
            edgesVisible ? "bg-white/10 text-white" : "text-white/85 hover:bg-white/10"
          }`}
        >
          <Spline size={16} />
        </button>
        <span className="mx-1 h-3 w-px shrink-0 bg-white/10" />
        <button
          type="button"
          aria-label="缩放"
          onClick={() => setZoomMenuOpen((v) => !v)}
          className="flex h-7 w-12 items-center justify-center rounded-md text-[13px] text-white/85 hover:bg-white/10"
        >
          {zoomPercent}%
        </button>
        {zoomMenuOpen ? <JimengZoomMenu onClose={() => setZoomMenuOpen(false)} /> : null}
      </div>
    </div>
  );
}
