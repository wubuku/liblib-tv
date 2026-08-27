"use client";

import { useEffect, useRef } from "react";
import { LayoutGrid, Link2, Magnet, Map, PanelLeft } from "lucide-react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/store/uiStore";

interface BottomToolbarProps {
  onToggleAssetPanel: () => void;
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

export function BottomToolbar({
  onToggleAssetPanel,
  onOrganize,
  onFitView,
  onZoomBy,
  onZoomTo,
}: BottomToolbarProps) {
  const zoomMenuRef = useRef<HTMLDivElement>(null);
  const {
    isAssetPanelOpen,
    showMinimap,
    toggleMinimap,
    showEdges,
    toggleEdges,
    snapToGrid,
    toggleSnapToGrid,
    zoomLevel,
    isZoomMenuOpen,
    toggleZoomMenu,
    closeZoomMenu,
  } = useUIStore();

  useEffect(() => {
    if (!isZoomMenuOpen) return;
    const handlePointerDown = (event: PointerEvent) => {
      if (zoomMenuRef.current && !zoomMenuRef.current.contains(event.target as Node)) {
        closeZoomMenu();
      }
    };
    document.addEventListener("pointerdown", handlePointerDown, true);
    return () => document.removeEventListener("pointerdown", handlePointerDown, true);
  }, [closeZoomMenu, isZoomMenuOpen]);

  return (
    <div
      className={cn(
        "fixed bottom-3 z-[60] flex h-10 items-center gap-1 p-1.5 transition-[left]",
        isAssetPanelOpen ? "left-64 max-sm:left-4" : "left-4",
      )}
    >
      <button
        type="button"
        aria-label="资产管理"
        aria-pressed={isAssetPanelOpen}
        onClick={onToggleAssetPanel}
        className={cn(
          "flex h-7 items-center gap-2 rounded-md px-2 text-xs text-[#bcbcbc] hover:bg-white/[0.08] hover:text-white",
          isAssetPanelOpen && "bg-white/10 text-white",
        )}
      >
        <PanelLeft size={15} />
        <span className={cn(isAssetPanelOpen && "sm:max-[1100px]:hidden")}>
          资产管理
        </span>
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
      <span
        className={cn(
          "contents sm:max-[850px]:hidden",
          isAssetPanelOpen && "sm:max-[1100px]:hidden",
        )}
      >
        <IconButton label="吸附到网格" active={snapToGrid} onClick={toggleSnapToGrid}>
          <Magnet size={15} />
        </IconButton>
      </span>
      <div
        ref={zoomMenuRef}
        className={cn(
          "relative sm:max-[850px]:hidden",
          isAssetPanelOpen && "sm:max-[1100px]:hidden",
        )}
      >
        <button
          type="button"
          data-viewport-menu-trigger="zoom"
          aria-label="缩放选项"
          aria-expanded={isZoomMenuOpen}
          onClick={toggleZoomMenu}
          className="flex h-7 min-w-10 items-center justify-center rounded-md px-1.5 text-xs tabular-nums text-[#d7d7d7] hover:bg-white/[0.08]"
        >
          {zoomLevel}%
        </button>
        {isZoomMenuOpen && (
          <div data-liblib-overlay="zoom-menu" className="absolute bottom-9 right-0 w-[188px] rounded-xl border border-white/10 bg-[#262626] p-1.5 shadow-[0_18px_44px_rgba(0,0,0,0.5)]">
            <div data-zoom-current className="mb-1 flex h-9 items-center justify-between rounded-lg bg-white/[0.06] px-3 text-xs tabular-nums text-[#d7d7d7]">
              <span>{zoomLevel}</span>
              <span className="text-[#747474]">%</span>
            </div>
            <button type="button" data-zoom-action="in" onClick={() => onZoomBy(0.1)} className="flex h-9 w-full items-center justify-between rounded-lg px-3 text-xs text-[#e7e7e7] hover:bg-white/[0.07]">
              <span>放大</span>
              <span className="text-[#777]">⌘ +</span>
            </button>
            <button type="button" data-zoom-action="out" onClick={() => onZoomBy(-0.1)} className="flex h-9 w-full items-center justify-between rounded-lg px-3 text-xs text-[#e7e7e7] hover:bg-white/[0.07]">
              <span>缩小</span>
              <span className="text-[#777]">⌘ -</span>
            </button>
            <button type="button" data-zoom-action="fit" onClick={onFitView} className="flex h-9 w-full items-center justify-between rounded-lg px-3 text-xs text-[#e7e7e7] hover:bg-white/[0.07]">
              <span>适合屏幕</span>
              <span className="text-[#777]">⌘ 0</span>
            </button>
            <div className="my-1 h-px bg-white/[0.08]" />
            {[
              { zoom: 0.5, value: "50" },
              { zoom: 1, value: "100" },
              { zoom: 8, value: "800" },
            ].map((option) => (
              <button
                key={option.value}
                type="button"
                data-zoom-action={option.value}
                onClick={() => onZoomTo(option.zoom)}
                className="h-9 w-full rounded-lg px-3 text-left text-xs text-[#e7e7e7] hover:bg-white/[0.07]"
              >
                缩放至{option.value}%
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
