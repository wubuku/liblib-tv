"use client";

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
import { type PrimaryPanel, useUIStore } from "@/store/uiStore";
import { AddNodePanel } from "./AddNodePanel";
import { MaterialLibraryPanel } from "./MaterialLibraryPanel";
import { LibraryShowcasePanel } from "./LibraryShowcasePanel";
import { ToolboxPanel } from "./ToolboxPanel";
import { CharacterLibraryPanel } from "./CharacterLibraryPanel";
import { HistoryPanel } from "./HistoryPanel";

interface ToolButtonProps {
  label: string;
  active?: boolean;
  className?: string;
  onClick: () => void;
  children: React.ReactNode;
}

interface LeftSidebarProps {
  onAddNode: (type: string, data?: Record<string, unknown>) => void;
}

// Batch 612（源站 2026-10-01 实测 probe612c）：这一簇**每一枚都是
// 32×32 的幽灵按钮** `relative flex items-center justify-center rounded-lg
// transition-colors h-8 w-8 hover:bg-canvas-controls-hover cursor-pointer`，
// 20px 图标，**没有**「主按钮」变体。此前 clone 给「添加节点」单独做了
// 40×40 的实心浅色主按钮（`bg-[#edf0f5] text-[#171717]`），既比源站大
// 8px，又把整簇往左顶开 19.5px。
function ToolButton({ label, active, className, onClick, children }: ToolButtonProps) {
  return (
    <button
      type="button"
      title={label}
      aria-label={label}
      aria-pressed={active}
      onClick={onClick}
      className={cn(
        "relative flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-[#d4d4d4] transition-colors hover:bg-white/10",
        active && "bg-white/10 text-white",
        className,
      )}
    >
      {children}
    </button>
  );
}

function MoveMenu({ onSelect }: { onSelect: (tool: "select" | "pan") => void }) {
  const canvasTool = useUIStore((state) => state.canvasTool);

  return (
    <div data-liblib-overlay="primary:move" className="fixed bottom-[68px] left-1/2 z-[61] w-40 -translate-x-[126px] rounded-xl border border-white/10 bg-[#262626] p-1.5 shadow-[0_16px_40px_rgba(0,0,0,0.45)] max-sm:bottom-[108px]">
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
  // Batch 358: 这四项此前是**完全没有 onClick、也没 disabled** 的 <button>，
  // 却带着 `hover:bg-white/[0.07]` 的悬停反馈 —— 看着能点，点了什么也不发生。
  // 普查 (probe-liblib-batch358-fake-clickable.py) 在 tutorial 态一次扫出 4 个。
  //
  // 为什么不用 `disabled`: batch106 / batch121 断言这四项**可见**, 而菜单项在
  // 源站是存在的入口（SOURCE_FACT: 存在 + 文案 + 排列）。改 disabled 会去动
  // 已采样的形态。所以取「保留外观与可点性, 但不再用悬停反馈骗人」:
  // 去掉 hover 底色、cursor 改默认、加 title 说明为什么没反应。
  // 文案与几何一律不动。
  const inert =
    "h-9 w-full cursor-default rounded-lg px-3 text-left text-sm text-[#6f6f6f]";
  return (
    <div data-liblib-overlay="primary:tutorial" className="fixed bottom-[73px] left-[calc(50%+92px)] z-[61] w-[104px] rounded-xl border border-[#363636] bg-[#262626] p-1 shadow-[0_16px_40px_rgba(0,0,0,0.45)] max-sm:bottom-[109px] max-sm:left-auto max-sm:right-3">
      {[
        ["使用教程", "使用教程在克隆侧尚未接入"],
        ["联系客服", "联系客服在克隆侧尚未接入"],
        ["联系销售", "联系销售在克隆侧尚未接入"],
        ["关注公众号", "关注公众号在克隆侧尚未接入"],
      ].map(([label, why]) => (
        <button
          key={label}
          type="button"
          title={why}
          aria-disabled="true"
          className={inert}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

export function LeftSidebar({ onAddNode }: LeftSidebarProps) {
  const {
    toggleShortcutsPanel,
    toggleAddNodePanel,
    isAddNodePanelOpen,
    isShortcutsPanelOpen,
    isAssetPanelOpen,
    canvasTool,
    setCanvasTool,
    activePrimaryPanel,
    togglePrimaryPanel,
    setPrimaryPanel,
  } = useUIStore();

  const togglePanel = (panel: PrimaryPanel) => togglePrimaryPanel(panel);

  const toggleAddPanel = () => {
    toggleAddNodePanel();
  };

  const toggleShortcuts = () => {
    toggleShortcutsPanel();
  };

  const selectTool = (tool: "select" | "pan") => {
    setCanvasTool(tool);
    setPrimaryPanel(null);
  };

  return (
    <>
      <div
        className={cn(
          "fixed bottom-3 left-1/2 z-[60] flex h-[49px] -translate-x-1/2 items-center gap-2 rounded-xl border border-[#363636] bg-[#262626] p-2 shadow-[0_8px_30px_rgba(0,0,0,0.4)] max-sm:bottom-[52px]",
          isAssetPanelOpen &&
            "sm:left-[max(calc(50%+120px),704px)]",
        )}
      >
        <ToolButton label="添加节点" active={isAddNodePanelOpen} onClick={toggleAddPanel}>
          <Plus size={20} />
        </ToolButton>
        <ToolButton label={canvasTool === "pan" ? "抓手工具" : "移动"} active={activePrimaryPanel === "move"} onClick={() => togglePanel("move")}>
          {canvasTool === "pan" ? <Hand size={20} /> : <MousePointer2 size={20} />}
        </ToolButton>
        <ToolButton label="打开工具箱" active={activePrimaryPanel === "toolbox"} onClick={() => togglePanel("toolbox")}>
          <WandSparkles size={20} />
        </ToolButton>
        <ToolButton label="素材库" active={activePrimaryPanel === "material"} onClick={() => togglePanel("material")}>
          <Shapes size={20} />
        </ToolButton>
        <ToolButton label="角色库" active={activePrimaryPanel === "character"} onClick={() => togglePanel("character")}>
          <UserRound size={20} />
        </ToolButton>
        {/* Batch 101: 2026-09-05 源站底部工具条该入口名为「生成历史」。 */}
        <ToolButton label="生成历史" active={activePrimaryPanel === "history"} onClick={() => togglePanel("history")}>
          <History size={20} />
        </ToolButton>
        {/* 源站实测：生成历史右缘 1011.5、快捷键左缘 1028.5，间隙 17px，
            比簇内其余的 8px 宽一截——这里是一处分隔。 */}
        <ToolButton
          label="快捷键"
          className="ml-[9px]"
          active={isShortcutsPanelOpen}
          onClick={toggleShortcuts}
        >
          <Keyboard size={20} />
        </ToolButton>
        {/* Batch 121: 源站 2026-09-06 该入口名为「教程」。 */}
        <ToolButton label="教程" active={activePrimaryPanel === "tutorial"} onClick={() => togglePanel("tutorial")}>
          <CircleHelp size={20} />
        </ToolButton>
      </div>

      {isAddNodePanelOpen && <AddNodePanel onAddNode={onAddNode} />}
      {activePrimaryPanel === "move" && <MoveMenu onSelect={selectTool} />}
      {activePrimaryPanel === "toolbox" && <ToolboxPanel onClose={() => setPrimaryPanel(null)} />}
      {activePrimaryPanel === "material" && (
        <MaterialLibraryPanel onOpenLibrary={(panel) => setPrimaryPanel(panel)} />
      )}
      {activePrimaryPanel === "style-library" && (
        <LibraryShowcasePanel variant="style" onClose={() => setPrimaryPanel(null)} />
      )}
      {activePrimaryPanel === "effects-library" && (
        <LibraryShowcasePanel variant="effects" onClose={() => setPrimaryPanel(null)} />
      )}
      {activePrimaryPanel === "character" && (
        <CharacterLibraryPanel
          onAddNode={onAddNode}
          onClose={() => setPrimaryPanel(null)}
        />
      )}
      {activePrimaryPanel === "history" && <HistoryPanel onClose={() => setPrimaryPanel(null)} />}
      {activePrimaryPanel === "tutorial" && <TutorialMenu />}
    </>
  );
}
