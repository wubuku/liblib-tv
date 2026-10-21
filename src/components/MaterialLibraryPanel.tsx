"use client";

import { Aperture, Box, GitFork } from "lucide-react";
import type { PrimaryPanel } from "@/store/uiStore";

interface MaterialLibraryPanelProps {
  onOpenLibrary: (
    panel: Extract<PrimaryPanel, "style-library" | "effects-library" | "toolbox">,
  ) => void;
}

// Batch 529: 2026-09-27 源站采样——两入口分别打开风格库/特效库大版面浮层
// （liblib-source-exploration-2026-09-25 NOTES §108/§132/§137）。
//
// ★★ Batch 826（源站 2026-10-21 运行时实测 + 源站 bundle 交叉核对）：
// 源站的素材库 popover 里是**三枚**，不是两枚 ——
//   ① 风格库（副标「新增风格节点」，右侧 NEW 徽章）
//   ② 特效库（副标「新增特效节点」，右侧 NEW 徽章）
//   ③ **打开工具箱**（**无**副标、**无** NEW 徽章）
// 而源站的**底部工具条那一簇里没有「打开工具箱」**（`data-sidebar-btn`
// 逐枚枚举：add-node / tool-mode / open-asset / character-library /
// history / keyboard / contact —— 共 7 枚）。
// ⟹ ★★ 「打开工具箱」此前被 clone 错放在底部工具条上 ⟹ 本批**归位**：
//   从 rail 移除、放进这个面板 ⟹ ★★ clone 的簇于是与源站**逐枚同构**。
// ★ 源站 bundle 里这一枚的 key 是 `workflow`、图标 `G.p.GitForkN`
// ⟹ 这里用 lucide 的 `GitFork`（同族图形）。
const entries = [
  { label: "风格库", description: "新增风格节点", icon: Box, target: "style-library" },
  { label: "特效库", description: "新增特效节点", icon: Aperture, target: "effects-library" },
  { label: "打开工具箱", description: "", icon: GitFork, target: "toolbox" },
] as const;

export function MaterialLibraryPanel({ onOpenLibrary }: MaterialLibraryPanelProps) {
  return (
    <section
      aria-label="素材库"
      data-liblib-overlay="primary:material"
      // ★★ Batch 826：源站这个 popover 实测 **240×220**（`fixed z-20`，底边
      // 恰好贴在 rail 上沿），clone 此前是 240×163（**只有两枚**时的高度）⟹
      // ★ 补上第三枚「打开工具箱」后，高度改成 220 与源站对齐。
      // ★★ 高度走 **inline style**（不是 `h-[220px]`）⟹ ★ 对 4317 上那个
      // **冻结的 Tailwind 扫描器**免疫：新增的任意值类在 dev 上会被整个丢掉
      // （见 batch 824 的工具链发现）⟹ dev 与 prod 必须一致，故走 inline。
      style={{ height: 220 }}
      className="fixed bottom-[73px] left-[calc(50%-24px)] z-[62] w-[240px] -translate-x-1/2 rounded-xl border border-[#363636] bg-[#262626] p-2 shadow-[0_18px_48px_rgba(0,0,0,0.5)] max-sm:bottom-[109px] max-sm:left-1/2"
    >
      <h2 className="px-2 py-1 text-sm font-medium text-[#929292]">素材库</h2>
      <div className="mt-[9px] space-y-1">
        {entries.map((entry) => {
          const Icon = entry.icon;
          return (
            <button
              key={entry.label}
              type="button"
              data-material-entry={entry.label}
              onClick={() => onOpenLibrary(entry.target)}
              className="flex h-[52px] w-full items-center gap-2 rounded-xl px-2 text-left hover:bg-white/[0.06]"
            >
              <span className="flex size-8 shrink-0 items-center justify-center text-[#ededed]">
                <Icon size={20} strokeWidth={1.6} />
              </span>
              <span className="min-w-0 flex-1">
                <span className="block text-sm text-[#eeeeee]">{entry.label}</span>
                {entry.description && (
                  <span className="block text-[11px] text-[#777]">{entry.description}</span>
                )}
              </span>
              {/* ★★ 源站实测：只有「风格库」「特效库」两枚带 NEW 徽章，
                  「打开工具箱」**不带** ⟹ 这里按 entry 逐枚决定。 */}
              {entry.description && (
                <span className="rounded-full bg-white/[0.06] px-2 py-1 text-[10px] text-[#777]">NEW</span>
              )}
            </button>
          );
        })}
      </div>
    </section>
  );
}
