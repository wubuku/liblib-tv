"use client";

import { useState } from "react";
import {
  CircleHelp,
  Hand,
  History,
  Keyboard,
  MousePointer2,
  Plus,
  Shapes,
  UserRound,
  WandSparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/store/uiStore";
import { AddNodePanel } from "./AddNodePanel";
import { MaterialLibraryPanel } from "./MaterialLibraryPanel";
import { ToolboxPanel } from "./ToolboxPanel";
import { CharacterLibraryPanel } from "./CharacterLibraryPanel";
import { HistoryPanel } from "./HistoryPanel";

type PanelName = "move" | "toolbox" | "material" | "character" | "history" | "tutorial";

interface ToolButtonProps {
  label: string;
  active?: boolean;
  prominent?: boolean;
  onClick: () => void;
  children: React.ReactNode;
}

function ToolButton({ label, active, prominent, onClick, children }: ToolButtonProps) {
  return (
    <button
      type="button"
      title={label}
      aria-label={label}
      aria-pressed={active}
      onClick={onClick}
      className={cn(
        "relative flex shrink-0 items-center justify-center rounded-lg transition-colors",
        prominent ? "h-10 w-10 bg-[#edf0f5] text-[#171717] hover:bg-white" : "h-8 w-8 text-[#d4d4d4] hover:bg-white/10",
        active && !prominent && "bg-white/10 text-white",
      )}
    >
      {children}
    </button>
  );
}

function MoveMenu({ onSelect }: { onSelect: (tool: "select" | "pan") => void }) {
  const canvasTool = useUIStore((state) => state.canvasTool);

  return (
    <div className="fixed bottom-[68px] left-1/2 z-[61] w-40 -translate-x-[126px] rounded-xl border border-white/10 bg-[#262626] p-1.5 shadow-[0_16px_40px_rgba(0,0,0,0.45)] max-sm:bottom-[108px]">
      <button onClick={() => onSelect("select")} className="flex h-9 w-full items-center gap-3 rounded-lg px-3 text-sm text-[#ededed] hover:bg-white/[0.07]">
        <MousePointer2 size={16} />
        <span className="flex-1 text-left">移动</span>
        <span className="text-xs text-[#777]">V</span>
        {canvasTool === "select" && <span className="h-1.5 w-1.5 rounded-full bg-[#09caf5]" />}
      </button>
      <button onClick={() => onSelect("pan")} className="flex h-9 w-full items-center gap-3 rounded-lg px-3 text-sm text-[#ededed] hover:bg-white/[0.07]">
        <Hand size={16} />
        <span className="flex-1 text-left">抓手工具</span>
        <span className="text-xs text-[#777]">H</span>
        {canvasTool === "pan" && <span className="h-1.5 w-1.5 rounded-full bg-[#09caf5]" />}
      </button>
    </div>
  );
}

function TutorialMenu() {
  return (
    <div className="fixed bottom-[68px] left-[calc(50%+90px)] z-[61] w-[104px] rounded-xl border border-white/10 bg-[#262626] p-1.5 shadow-[0_16px_40px_rgba(0,0,0,0.45)] max-sm:bottom-[108px] max-sm:left-auto max-sm:right-6">
      {["使用教程", "联系客服", "联系销售", "关注公众号"].map((label) => (
        <button key={label} className="h-9 w-full rounded-lg px-2 text-left text-xs text-[#d8d8d8] hover:bg-white/[0.07]">
          {label}
        </button>
      ))}
    </div>
  );
}

export function LeftSidebar() {
  const [activePanel, setActivePanel] = useState<PanelName | null>(null);
  const {
    toggleShortcutsPanel,
    toggleAddNodePanel,
    isAddNodePanelOpen,
    canvasTool,
    setCanvasTool,
  } = useUIStore();

  const togglePanel = (panel: PanelName) => {
    setActivePanel((current) => (current === panel ? null : panel));
  };

  const selectTool = (tool: "select" | "pan") => {
    setCanvasTool(tool);
    setActivePanel(null);
  };

  return (
    <>
      <div className="fixed bottom-3 left-1/2 z-[60] flex h-[49px] -translate-x-1/2 items-center gap-2 rounded-xl border border-[#363636] bg-[#262626] p-2 shadow-[0_8px_30px_rgba(0,0,0,0.4)] max-sm:bottom-[52px]">
        <ToolButton label="添加节点" prominent active={isAddNodePanelOpen} onClick={toggleAddNodePanel}>
          <Plus size={22} />
        </ToolButton>
        <ToolButton label={canvasTool === "pan" ? "抓手工具" : "移动"} active={activePanel === "move"} onClick={() => togglePanel("move")}>
          {canvasTool === "pan" ? <Hand size={17} /> : <MousePointer2 size={17} />}
        </ToolButton>
        <ToolButton label="打开工具箱" active={activePanel === "toolbox"} onClick={() => togglePanel("toolbox")}>
          <WandSparkles size={17} />
        </ToolButton>
        <ToolButton label="素材库" active={activePanel === "material"} onClick={() => togglePanel("material")}>
          <Shapes size={17} />
        </ToolButton>
        <ToolButton label="角色库" active={activePanel === "character"} onClick={() => togglePanel("character")}>
          <UserRound size={17} />
        </ToolButton>
        <ToolButton label="历史记录" active={activePanel === "history"} onClick={() => togglePanel("history")}>
          <History size={17} />
        </ToolButton>
        <ToolButton label="快捷键" onClick={toggleShortcutsPanel}>
          <Keyboard size={17} />
        </ToolButton>
        <ToolButton label="教程与帮助" active={activePanel === "tutorial"} onClick={() => togglePanel("tutorial")}>
          <CircleHelp size={17} />
        </ToolButton>
      </div>

      {isAddNodePanelOpen && <AddNodePanel />}
      {activePanel === "move" && <MoveMenu onSelect={selectTool} />}
      {activePanel === "toolbox" && <ToolboxPanel onClose={() => setActivePanel(null)} />}
      {activePanel === "material" && <MaterialLibraryPanel />}
      {activePanel === "character" && <CharacterLibraryPanel onClose={() => setActivePanel(null)} />}
      {activePanel === "history" && <HistoryPanel onClose={() => setActivePanel(null)} />}
      {activePanel === "tutorial" && <TutorialMenu />}
    </>
  );
}
