"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/store/uiStore";
import { AddNodePanel } from "./AddNodePanel";
import { MaterialLibraryPanel } from "./MaterialLibraryPanel";
import { ToolboxPanel } from "./ToolboxPanel";
import { CharacterLibraryPanel } from "./CharacterLibraryPanel";
import { HistoryPanel } from "./HistoryPanel";

// SVG Icons for sidebar buttons
function AddNodeIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M8 2v12M2 8h12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

function ToolboxIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <rect x="1" y="5" width="14" height="10" rx="2" stroke="currentColor" strokeWidth="1.5" />
      <path d="M5 5V3a3 3 0 016 0v2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function MaterialIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <rect x="2" y="2" width="12" height="12" rx="2" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="6" cy="6" r="1.5" fill="currentColor" />
      <path d="M2 11l3-3 2 2 3-4 4 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
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

function HistoryIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M2 8a6 6 0 1111.3-2.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M14 2v4h-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M8 4v4l3 2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function KeyboardIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <rect x="1" y="3" width="14" height="10" rx="2" stroke="currentColor" strokeWidth="1.5" />
      <rect x="4" y="6" width="2" height="1.5" rx="0.5" fill="currentColor" />
      <rect x="7" y="6" width="2" height="1.5" rx="0.5" fill="currentColor" />
      <rect x="10" y="6" width="2" height="1.5" rx="0.5" fill="currentColor" />
      <rect x="4" y="9" width="8" height="1.5" rx="0.5" fill="currentColor" />
    </svg>
  );
}

function TutorialIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.5" />
      <path d="M6 6a2 2 0 114 0c0 1.5-2 1.5-2 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="8" cy="12" r="0.75" fill="currentColor" />
    </svg>
  );
}

interface SidebarButtonProps {
  icon: React.ReactNode;
  label: string;
  isActive?: boolean;
  onClick?: () => void;
  badge?: string;
}

function SidebarButton({ icon, label, isActive, onClick, badge }: SidebarButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "relative flex items-center justify-center rounded-lg transition-colors h-8 w-8 cursor-pointer",
        isActive ? "bg-[rgba(255,255,255,0.15)]" : "hover:bg-[rgba(255,255,255,0.08)]"
      )}
      title={label}
    >
      <span className="text-[#f7f7f7]">{icon}</span>
      {badge && (
        <span className="absolute -right-1 -top-1 flex h-4 items-center rounded bg-[#09caf5] px-1 text-[10px] font-medium text-black">
          {badge}
        </span>
      )}
    </button>
  );
}

export function LeftSidebar() {
  const [activePanel, setActivePanel] = useState<string | null>(null);
  const { toggleShortcutsPanel, toggleAddNodePanel, isAddNodePanelOpen } = useUIStore();

  const togglePanel = (panel: string) => {
    setActivePanel((prev) => (prev === panel ? null : panel));
  };

  return (
    <>
      <div
        className="absolute left-0 top-1/2 -translate-y-1/2 flex flex-col items-center gap-1 p-1 bg-[#171717] border-r border-[#363636]"
        style={{ zIndex: 40 }}
      >
        <SidebarButton
          icon={<AddNodeIcon />}
          label="添加节点"
          isActive={isAddNodePanelOpen}
          onClick={toggleAddNodePanel}
        />
        <SidebarButton
          icon={<ToolboxIcon />}
          label="打开工具箱"
          isActive={activePanel === "toolbox"}
          onClick={() => togglePanel("toolbox")}
        />
        <SidebarButton
          icon={<MaterialIcon />}
          label="素材库"
          isActive={activePanel === "material"}
          onClick={() => togglePanel("material")}
        />
        <SidebarButton
          icon={<CharacterIcon />}
          label="角色库"
          isActive={activePanel === "character"}
          onClick={() => togglePanel("character")}
        />
        <SidebarButton
          icon={<HistoryIcon />}
          label="历史记录"
          isActive={activePanel === "history"}
          onClick={() => togglePanel("history")}
        />
        <SidebarButton
          icon={<KeyboardIcon />}
          label="快捷键"
          onClick={toggleShortcutsPanel}
        />
        <SidebarButton
          icon={<TutorialIcon />}
          label="教程"
          isActive={activePanel === "tutorial"}
          onClick={() => togglePanel("tutorial")}
        />
      </div>

      {/* Panels */}
      {isAddNodePanelOpen && <AddNodePanel />}
      {activePanel === "toolbox" && (
        <ToolboxPanel onClose={() => setActivePanel(null)} />
      )}
      {activePanel === "material" && <MaterialLibraryPanel />}
      {activePanel === "character" && (
        <CharacterLibraryPanel onClose={() => setActivePanel(null)} />
      )}
      {activePanel === "history" && (
        <HistoryPanel onClose={() => setActivePanel(null)} />
      )}
    </>
  );
}
