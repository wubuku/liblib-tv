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
          data-inert="true"
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
    toggleAgent,
    isAgentOpen,
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

        {/* ★★ Batch 824（源站 2026-10-21 实测，DOM 读数 + 计算样式 + 截图放大）：
            源站画布**底部工具条右端**还有一枚入口，它**不在药丸里**——
            药丸（添加节点／移动／素材库／角色造型室／生成历史｜分隔线｜快捷键／教程）
            结束**之后**，隔 **14px** 单独挂一枚 **48×48 的圆钮**。

            ★★ 那枚圆钮的源站计算样式（recon824d 实测，逐字）：
              bg `rgb(38,38,38)`、border `1px solid rgb(54,54,54)`、
              borderRadius `9999px`（正圆）、padding `0 9px`、
              内含一个 **28×28** 的液态青球
              （`--liquid-state-color:#00e5ff`、highlight `#a4fff3`），
              外面**再套一层** 28×28 的 DIV（`relative z-[2] size-7`）。
            ★★ 圆钮里还有一段文字「TV Director」，但它是
              **`width:0` + `opacity:0`** 的 ⟹ **视觉上没有文字**
              （源站截图放大核对：只有一颗球，**旁边是空的**），
              而 textContent 仍逐字是「TV Director」⟹
              可及名靠 aria-label，视觉只出图标。

            ★★ 点它打开的是**右侧「新对话」AI 抽屉**
            （标题「新对话」、「让 TV Director 辅助你的无限创意」、
            4 个引导入口：感知画布开始创作／从爆款预设开始剧本原创／
            上传故事来改编／批量优化提示词）——
            ★★ **不是导演台**（点它 URL 不变、画布节点数不变）。

            ⟹ ★ 那正是 clone 的 `AgentDrawer`（其标题逐字就是「新对话」）。
            ⟹ ★★ 所以 clone **不是缺这个面板**，而是**缺这个入口按钮**：
            clone 的入口在**顶部导航**（文案「Agent」），
            而源站在**画布底部**。⟹ ★★ 这是「有功能、用户找不到」的典型形态。

            ★ 顶部那枚「Agent」按钮**不能删** —— 它被历史门禁钉住
            （batch723/737/649/280 的 runtime-audit 都记着它）⟹
            ★ 这里**增量**补一枚与源站同位同形的入口，不动顶部。
            ★ 抽屉开着时源站这枚圆钮**消失**（截图实测：底部工具条只剩
            7 枚）⟹ 这里照做。
            ★ 定位用 `absolute left-full` ⟹ 它**不吃药丸的流式布局**，
            药丸的圆角/背景/宽度**不会**被它撑大（源站就是这样：
            药丸在 x=909..941 结束，球在 955）。 */}
        {!isAgentOpen ? (
          <button
            type="button"
            aria-label="TV Director"
            data-guide-target="agent-entry"
            data-tv-director-trigger
            onClick={toggleAgent}
            className="absolute left-full ml-[6px] top-1/2 flex h-12 w-12 min-w-12 -translate-y-1/2 cursor-pointer items-center justify-center rounded-full border border-[#363636] bg-[#262626] px-[9px] transition-colors hover:bg-[#383838]"
          >
            <span
              aria-hidden="true"
              data-testid="canvas-agent-orb-entry"
              className="relative z-[2] size-7 shrink-0"
            >
              {/* ★★ 渐变与光晕走 **inline style**，不用 Tailwind 任意值。
                  理由（2026-10-21 实测，4317 上）：
                  ★★ **dev server 的 Tailwind 扫描是冻结的** —— 4317 那个
                  `next dev` 进程从 **2026-10-07** 起就没重扫过（磁盘上的
                  CSS chunk 还是 10/07 的）⟹ ★★ **任何新加的 Tailwind 类
                  在 4317 上都不生效**，而 prod 构建照常生成 ⟹ 同一个组件
                  在 dev 上「没颜色」、在 prod 上「有颜色」。
                  ★ 实测：`bg-[radial-gradient(circle_at_36%_28%,#d8fffb_0%,…)]`
                  与 `bg-radial from-[#d8fffb] …` **dev CSS 里一条都没有**
                  （连标准类 `bg-radial` 都没有）⟹ 球在 dev 上 computed
                  backgroundColor = rgba(0,0,0,0)，截图里那颗球是**空的**。
                  ★ 同族：`top-[23.5px]` 这种**带小数**的任意值在 dev 也被丢。
                  ⟹ ★★ 结论：★ **inline style 对这个扫描器免疫**，
                  ★ 且仓库里已有先例（frameos 画布的渐变就是 inline 的）。
                  ★ 所以本批**一个新增 Tailwind 类都不引入** ⟹
                  ★ dev 与 prod 渲染**完全一致**。 */}
              <span
                className="block size-7 rounded-full"
                style={{
                  backgroundImage:
                    "radial-gradient(circle at 36% 28%, #d8fffb 0%, "
                    + "#a4fff3 12%, #00e5ff 38%, #0a7ef0 72%, #0646c9 100%)",
                  boxShadow: "0 0 10px rgba(0, 229, 255, 0.55)",
                }}
              />
            </span>
            {/* ★ 源站的文字是 `width:0 + opacity:0` ⟹ 视觉上没有字，
                但 textContent 逐字是「TV Director」⟹ 这里照抄这个做法。
                ★ 源站那个 span 的**矩形宽读数是 0**（外层 w-0，内层再套一层
                带 padding 的 span）⟹ 这里不写 padding，矩形宽就正好是 0。 */}
            <span className="block w-0 overflow-hidden whitespace-nowrap text-sm font-medium opacity-0">
              TV Director
            </span>          </button>
        ) : null}
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
