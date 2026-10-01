"use client";

import { useEffect, useRef } from "react";
import { GridGlyph, LinkGlyph, MagnetGlyph, MapGlyph, PanelToggleGlyph } from "@/components/ChromeIcons";
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
        // Batch 612（源站实测 probe612c）：四枚图标按钮都是
        // `rounded-lg`（clone 此前是 rounded-md）。
        "flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-[#bdbdbd] transition-colors hover:bg-white/[0.08] hover:text-white",
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
        // Batch 171: 源站栏容器 items-end gap-2、无内边距盒（2026-09-07 采样 280×40）。
        // Batch 612（源站 2026-10-01 复测）逐项对齐：整簇 28 高、y=1104、
        // 起点 x=14、**簇内间隙 4px**（源站 资产管理右缘 108 → 整理画布
        // 左缘 112）。此前 clone 是 y=1110 / x=16 / gap-2(8)，逐枚累积到
        // 缩放选项时已经偏 22px。
        "fixed bottom-[18px] z-[60] flex h-10 items-end gap-1 transition-[left]",
        isAssetPanelOpen ? "left-64 max-sm:left-4" : "left-[14px]",
      )}
    >
      <button
        type="button"
        aria-label="资产管理"
        aria-pressed={isAssetPanelOpen}
        onClick={onToggleAssetPanel}
        className={cn(
          // Batch 171: 源站按钮 rounded-lg、13px（实拍 94×28）。
          // Batch 612 复测：94 宽来自 `px-3 gap-1`（此前 clone 是 px-2 gap-2，
          // 实测只有 91）。
          "flex h-7 items-center gap-1 rounded-lg px-3 text-[13px] text-[#bcbcbc] hover:bg-white/[0.08] hover:text-white",
          isAssetPanelOpen && "bg-white/10 text-white",
        )}
      >
        <PanelToggleGlyph className="size-[14px] text-current" />
        <span>资产管理</span>
      </button>
      <IconButton label="整理画布，Option+Shift+F" onClick={onOrganize}>
        <GridGlyph className="size-[14px] text-current" />
      </IconButton>
      <IconButton label="切换小地图" active={showMinimap} onClick={toggleMinimap}>
        <MapGlyph className="size-[14px] text-current" />
      </IconButton>
      <IconButton label={showEdges ? "隐藏节点连线" : "显示节点连线"} active={showEdges} onClick={toggleEdges}>
        <LinkGlyph className="size-[14px] text-current" />
      </IconButton>
      <span
        className="contents sm:max-[850px]:hidden"
      >
        <IconButton label="网格吸附" active={snapToGrid} onClick={toggleSnapToGrid}>
          <MagnetGlyph className="size-[14px] text-current" />
        </IconButton>
      </span>
      <div
        ref={zoomMenuRef}
        className="relative sm:max-[850px]:hidden"
      >
        <button
          type="button"
          data-viewport-menu-trigger="zoom"
          aria-label="缩放选项"
          aria-expanded={isZoomMenuOpen}
          onClick={toggleZoomMenu}
          // Batch 612 复测：源站 36.3 宽、`px-1`，不带 min-w / tabular-nums
          //（此前 clone 是 min-w-10 + px-1.5 + tabular-nums，实测 40.2）。
          className="flex h-7 items-center justify-center rounded-lg px-1 text-[13px] text-[#d7d7d7] hover:bg-white/[0.08]"
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
