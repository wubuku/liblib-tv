"use client";

import { useState } from "react";
import { LayoutGrid, Link2, Magnet, Map, PanelLeft, Scan, ZoomIn, ZoomOut } from "lucide-react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/store/uiStore";

interface BottomToolbarProps {
  onOrganize: () => void;
  onFitView: () => void;
  onZoomBy: (delta: number) => void;
  onZoomTo: (zoom: number) => void;
}

interface IconButtonProps {
  label: string;
  active?: boolean;
  onClick: () => void;
  children: React.ReactNode;
}

function IconButton({ label, active, onClick, children }: IconButtonProps) {
  return (
    <button
      type="button"
      title={label}
      aria-label={label}
      aria-pressed={active}
      onClick={onClick}
      className={cn(
        "flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-[#bdbdbd] transition-colors hover:bg-white/[0.08] hover:text-white",
        active && "bg-white/10 text-[#f7f7f7]",
      )}
    >
      {children}
    </button>
  );
}

export function BottomToolbar({ onOrganize, onFitView, onZoomBy, onZoomTo }: BottomToolbarProps) {
  const [isZoomOpen, setIsZoomOpen] = useState(false);
  const {
    isAssetPanelOpen,
    toggleAssetPanel,
    showMinimap,
    toggleMinimap,
    showEdges,
    toggleEdges,
    showGrid,
    toggleGrid,
    snapToGrid,
    toggleSnapToGrid,
    zoomLevel,
  } = useUIStore();

  return (
    <div
      className={cn(
        "fixed bottom-3 z-[60] flex h-10 items-center gap-1 p-1.5 transition-[left]",
        isAssetPanelOpen ? "left-64 max-sm:left-4" : "left-4",
      )}
    >
      <button
        type="button"
        aria-pressed={isAssetPanelOpen}
        onClick={toggleAssetPanel}
        className={cn(
          "flex h-7 items-center gap-2 rounded-md px-2 text-xs text-[#bcbcbc] hover:bg-white/[0.08] hover:text-white",
          isAssetPanelOpen && "bg-white/10 text-white",
        )}
      >
        <PanelLeft size={15} />
        <span>资产管理</span>
      </button>
      <IconButton label="整理画布，Option+Shift+F" onClick={onOrganize}>
        <LayoutGrid size={15} />
      </IconButton>
      <IconButton label="显示缩略图" active={showMinimap} onClick={toggleMinimap}>
        <Map size={15} />
      </IconButton>
      <IconButton label={showEdges ? "隐藏节点连线" : "显示节点连线"} active={showEdges} onClick={toggleEdges}>
        <Link2 size={15} />
      </IconButton>
      <span className="contents sm:max-[850px]:hidden">
        <IconButton label="吸附到网格" active={snapToGrid} onClick={toggleSnapToGrid}>
          <Magnet size={15} />
        </IconButton>
      </span>
      <div className="relative sm:max-[850px]:hidden">
        <button
          type="button"
          aria-label="缩放选项"
          aria-expanded={isZoomOpen}
          onClick={() => setIsZoomOpen((open) => !open)}
          className="flex h-7 min-w-10 items-center justify-center rounded-md px-1.5 text-xs tabular-nums text-[#d7d7d7] hover:bg-white/[0.08]"
        >
          {zoomLevel}%
        </button>
        {isZoomOpen && (
          <div className="absolute bottom-9 right-0 w-[196px] rounded-xl border border-white/10 bg-[#262626] p-1.5 shadow-[0_18px_44px_rgba(0,0,0,0.5)]">
            <div className="mb-1 flex items-center gap-1 rounded-lg bg-[#1b1b1b] p-1">
              <button onClick={() => onZoomBy(-0.1)} className="flex h-7 w-7 items-center justify-center rounded-md text-[#bcbcbc] hover:bg-white/10" aria-label="缩小">
                <ZoomOut size={14} />
              </button>
              <span className="flex-1 text-center text-xs tabular-nums text-white">{zoomLevel}%</span>
              <button onClick={() => onZoomBy(0.1)} className="flex h-7 w-7 items-center justify-center rounded-md text-[#bcbcbc] hover:bg-white/10" aria-label="放大">
                <ZoomIn size={14} />
              </button>
            </div>
            <button onClick={onFitView} className="flex h-8 w-full items-center gap-2 rounded-lg px-2 text-xs text-[#e7e7e7] hover:bg-white/[0.07]">
              <Scan size={14} />
              <span className="flex-1 text-left">适合屏幕</span>
              <span className="text-[#777]">⌘0</span>
            </button>
            {[0.5, 1, 8].map((zoom) => (
              <button key={zoom} onClick={() => onZoomTo(zoom)} className="h-8 w-full rounded-lg px-2 text-left text-xs text-[#e7e7e7] hover:bg-white/[0.07]">
                缩放至 {Math.round(zoom * 100)}%
              </button>
            ))}
            <button onClick={toggleGrid} className="flex h-8 w-full items-center justify-between rounded-lg px-2 text-xs text-[#e7e7e7] hover:bg-white/[0.07]">
              <span>点阵网格</span>
              <span className={showGrid ? "text-[#09caf5]" : "text-[#777]"}>{showGrid ? "开启" : "关闭"}</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
