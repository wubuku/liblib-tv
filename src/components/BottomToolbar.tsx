"use client";

import { Tooltip } from "@base-ui/react/tooltip";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/store/uiStore";

// SVG Icons matching original LibTV bottom toolbar
function AssetIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <rect x="2" y="2" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5" />
      <rect x="9" y="2" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5" />
      <rect x="2" y="9" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5" />
      <rect x="9" y="9" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  );
}

function ArrangeIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <circle cx="5" cy="5" r="2" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="11" cy="11" r="2" stroke="currentColor" strokeWidth="1.5" />
      <path d="M5 7v3a2 2 0 002 2h2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function CharacterIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <circle cx="8" cy="5" r="3" stroke="currentColor" strokeWidth="1.5" />
      <path d="M2 14c0-3.3 2.7-6 6-6s6 2.7 6 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function AddIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
      <path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

function ArrangeNodesIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <circle cx="5" cy="5" r="2" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="15" cy="5" r="2" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="5" cy="15" r="2" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="15" cy="15" r="2" stroke="currentColor" strokeWidth="1.5" />
      <path d="M7 5h6M5 7v6M15 7v6M7 15h6" stroke="currentColor" strokeWidth="1.2" />
    </svg>
  );
}

function StarIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <path
        d="M10 2l2.5 5.5L18 8l-4 4 1 6-5-3-5 3 1-6-4-4 5.5-.5L10 2z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function HistoryIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <path d="M3 10a7 7 0 1114 0 7 7 0 01-14 0z" stroke="currentColor" strokeWidth="1.5" />
      <path d="M10 6v4l3 2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function ImageIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <rect x="2.5" y="3.5" width="15" height="13" rx="2" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="7" cy="8" r="1.5" fill="currentColor" />
      <path d="M2.5 14L6 10.5L9 13.5L12.5 11L17.5 14.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function HelpIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <circle cx="10" cy="10" r="7" stroke="currentColor" strokeWidth="1.5" />
      <path d="M8 7.5a2 2 0 114 0c0 1.5-2 1.5-2 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="10" cy="14" r="0.75" fill="currentColor" />
    </svg>
  );
}

interface ToolbarButtonProps {
  children: React.ReactNode;
  tooltip?: string;
  className?: string;
  onClick?: () => void;
  isActive?: boolean;
}

function ToolbarButton({
  children,
  tooltip,
  className,
  onClick,
  isActive,
}: ToolbarButtonProps) {
  const button = (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "inline-flex items-center justify-center rounded-lg text-[#f7f7f7] transition-colors duration-150 ease-in-out hover:bg-[#353639]",
        isActive ? "bg-[#353639]" : "bg-transparent",
        className
      )}
    >
      {children}
    </button>
  );

  if (!tooltip) {
    return button;
  }

  return (
    <Tooltip.Provider delay={300}>
      <Tooltip.Root>
        <Tooltip.Trigger render={button} />
        <Tooltip.Portal>
          <Tooltip.Positioner side="top" sideOffset={8}>
            <Tooltip.Popup className="rounded-lg bg-[#1c1d29] px-3 py-1.5 text-xs text-[#f7f7f7] shadow-lg border border-[#525252]">
              {tooltip}
            </Tooltip.Popup>
          </Tooltip.Positioner>
        </Tooltip.Portal>
      </Tooltip.Root>
    </Tooltip.Provider>
  );
}

export function BottomToolbar() {
  const {
    toggleAssetPanel,
    toggleGrid,
    toggleMinimap,
    showGrid,
    showMinimap,
    zoomLevel,
    toggleShortcutsPanel,
  } = useUIStore();

  return (
    <div
      className="fixed bottom-4 left-1/2 -translate-x-1/2 flex flex-row items-center gap-1 p-1.5 bg-[rgba(20,20,20,0.7)] backdrop-blur-md border border-[#363636] rounded-xl z-40"
      style={{ boxShadow: "0 4px 24px rgba(0,0,0,0.4)" }}
    >
      {/* Asset Management - text button on the far left */}
      <ToolbarButton
        className="h-8 w-auto gap-1.5 px-3 text-sm font-normal"
        onClick={toggleAssetPanel}
      >
        <AssetIcon />
        <span>资产管理</span>
      </ToolbarButton>

      <div className="w-px h-5 bg-[#363636] mx-1" />

      {/* Arrange Canvas icon button */}
      <ToolbarButton className="h-8 w-8" tooltip="整理画布，Option+Shift+F">
        <ArrangeIcon />
      </ToolbarButton>

      {/* Character icon button */}
      <ToolbarButton className="h-8 w-8" tooltip="角色">
        <CharacterIcon />
      </ToolbarButton>

      {/* Main Big "+" button - highlighted (large, cyan) */}
      <button
        type="button"
        className="inline-flex items-center justify-center h-10 w-10 rounded-full bg-[#09caf5] text-[#171717] hover:bg-[#5ddcff] transition-colors mx-1"
        aria-label="添加节点"
      >
        <AddIcon />
      </button>

      {/* Three round action icons */}
      <ToolbarButton className="h-8 w-8" tooltip="整理节点">
        <ArrangeNodesIcon />
      </ToolbarButton>

      <ToolbarButton className="h-8 w-8" tooltip="收藏">
        <StarIcon />
      </ToolbarButton>

      <ToolbarButton className="h-8 w-8" tooltip="历史记录">
        <HistoryIcon />
      </ToolbarButton>

      {/* Image/Storyboard icon */}
      <ToolbarButton className="h-8 w-8" tooltip="分镜">
        <ImageIcon />
      </ToolbarButton>

      {/* Help icon */}
      <ToolbarButton className="h-8 w-8" tooltip="帮助" onClick={toggleShortcutsPanel}>
        <HelpIcon />
      </ToolbarButton>

      <div className="w-px h-5 bg-[#363636] mx-1" />

      {/* Zoom percentage */}
      <ToolbarButton className="h-8 w-auto px-3">
        <span className="text-xs text-[#f7f7f7]">{zoomLevel}%</span>
      </ToolbarButton>
    </div>
  );
}