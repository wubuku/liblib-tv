"use client";

// ★★★ Batch 859（源站逐字）：导演台左侧的「**选择画幅比例**」**侧栏面板模式**。
//
// ★ ★★ 与「全景图」同源（= batch 858 登记的 D8）：源站左侧那个 232px 面板
//   是**五模式互斥容器**，「选择画幅比例」是其中一个模式，**不是** rail 浮层。
//   clone 此前把它做成 **portal 浮层**（`data-director-aspect-flyout`）⟹ ⟹ 本批改掉。
//
// ★ 源站逐字（`"aspect"===z` 那段）：
//     标题条 `aO`，文本 `D("canvas:directorSelectAspectRatioHint")`（「选择画幅比例」）
//     内容容器 `className:"grid grid-cols-2 gap-2 px-2 pb-3"`
//     每一格：
//       `className: clsx("hover:bg-white/8 flex h-[72px] flex-col items-center
//         justify-center gap-2 rounded-xl border text-[12px] text-white/90
//         transition-colors disabled:cursor-not-allowed disabled:opacity-35",
//         t ? "border-white/85" : "border-white/10")`
//       其中 `t` ＝「这一项是不是当前选中」
//         （`null===e.value||null===l ? e.value===l : .001>Math.abs(e.value-l)`）
//       格内：比例字形 `aN` ＋ 文本 `e.label ?? D("canvas:ratioOptionsText07c60b")`
//
// ★ 源站的选项表（chunk 里的 `aj`，逐字）：
//     `[{label:null,value:null},{label:"21:9",value:21/9},{label:"16:9",value:16/9},
//       {label:"4:3",value:4/3},{label:"1:1",value:1},{label:"3:4",value:.75},
//       {label:"9:16",value:9/16}]`
//   ⟹ ⟹ 第一项 `label:null` ⟹ ⟹ 文本走 i18n 兜底（源站实测显示「自适应」）。
//
// ★ 源站实测（`docs/research/liblib-canvas-batch859-2026-10-01/raw/source-859-panels.json`）：
//     面板 @(48,52) 232 宽、标题条 @(48,52) 232×48 / 12px、
//     网格 @(48,100) 232×324、`grid-template-columns: 104px 104px`、gap **8px**、
//     padding `0px 8px 12px`
//     七格各 **104×72**：自适应 @(56,100)／21:9 @(168,100)／16:9 @(56,180)／
//     4:3 @(168,180)／1:1 @(56,260)／3:4 @(168,260)／9:16 @(56,340)
//     字号 **12px**、圆角 **12px**、边框 **1px**
//     （选中 `rgba(255,255,255,0.85)`／未选 `rgba(255,255,255,0.1)`）
//     ★ **场景树不在场**（模式互斥被实测确认）
//
// ★ ★ **功能缺口（如实登记，不假装已对齐）**：源站选比例会**改画布的宽高比**
//   （`aj` 的 value 是**数值比例**，`d(e.value)` 写进画布状态）⟹ ⟹
//   clone 的 store 里那个 `aspectRatio` 是**截图/导出**用的三值
//   （`"16:9"|"9:16"|"1:1"`），**与画布宽高比不是一回事** ⟹ ⟹
//   本组件的选择**只改面板里的高亮**，**不改画布** ⟹ ⟹ 登记为 **D11**。
import { useState } from "react";
import { cn } from "@/lib/utils";

// ★ 源站逐字（`aO`）：标题条。
const TITLE_CLASS =
  "flex h-12 shrink-0 items-center px-3 text-[12px] leading-5 text-white/90";

// ★ 源站逐字：`grid grid-cols-2 gap-2 px-2 pb-3`
const GRID_CLASS = "grid grid-cols-2 gap-2 px-2 pb-3";

// ★ 源站逐字（逐字照抄，含 `hover:bg-white/8` / `transition-colors` / `disabled:*`）
const CELL_CLASS =
  "hover:bg-white/8 flex h-[72px] flex-col items-center justify-center gap-2 rounded-xl border text-[12px] text-white/90 transition-colors disabled:cursor-not-allowed disabled:opacity-35";

// ★ 源站的七个选项（逐字顺序 ＋ 逐字文本；第一项文本来自 i18n 兜底）
const aspectRatios = [
  "自适应",
  "21:9",
  "16:9",
  "4:3",
  "1:1",
  "3:4",
  "9:16",
] as const;

// ★ Batch 590（源站 2026-10-01 实测）：七张卡的示意框尺寸逐项对齐。
//   注意源站 `3:4` 与 `9:16` 实测**同为 8×16**（看起来是源站自身的取整
//   结果），clone 按实测照抄，不按比例自行「修正」。
const ASPECT_GLYPH: Record<(typeof aspectRatios)[number], string> = {
  自适应: "h-[11px] w-4",
  "21:9": "h-[7px] w-4",
  "16:9": "h-[9px] w-4",
  "4:3": "h-3 w-4",
  "1:1": "h-[14px] w-[14px]",
  "3:4": "h-4 w-2",
  "9:16": "h-4 w-2",
};

export function DirectorAspectPanel({ active }: { active: boolean }) {
  // ★ 选择状态留在本组件里（组件**常驻挂载** ⟹ 切到别的模式再切回来，
  //   选中项还在）⟹ ⟹ 与源站「切 `z` 会重置子菜单、但比例是画布状态」的
  //   区别见 D11。
  const [aspectRatio, setAspectRatio] = useState<string>("自适应");
  // ★ 源站逐字：`"aspect"===z?(…):null` ⟹ ⟹ **条件渲染**（不是 `hidden`）
  //   ⟹ ⟹ 与 batch 858 的「添加角色」面板同一写法。
  // ★ ★ 组件**本身**常驻（`useState` 的选中项因此跨模式保留），
  //   只有 DOM 子树按模式在/不在 ⟹ ⟹ 两者不冲突。
  if (!active) return null;
  return (
    <div
      data-director-aspect-panel
      aria-label="选择画幅比例"
      className="flex h-full min-h-0 w-full flex-col bg-[#171717]"
    >
      <div data-director-panel-title="aspect" className={TITLE_CLASS}>
        <span className="truncate">选择画幅比例</span>
      </div>
      <div data-director-aspect-grid className={GRID_CLASS}>
        {aspectRatios.map((ratio) => (
          <button
            key={ratio}
            type="button"
            data-director-aspect-option={ratio}
            // ★ 源站按钮**没有** `aria-pressed` ⟹ ⟹ clone 保留作 a11y 超集
            //   （batch 590 已登记：源站选中/未选两态**文字色相同**，
            //   唯一差别是按钮描边 0.85 / 0.1、背景两态皆透明）。
            aria-pressed={aspectRatio === ratio}
            onClick={() => setAspectRatio(ratio)}
            className={cn(
              CELL_CLASS,
              aspectRatio === ratio ? "border-white/85" : "border-white/10",
            )}
          >
            <span
              aria-hidden="true"
              data-director-aspect-glyph
              className={cn("block rounded-sm border border-white/90", ASPECT_GLYPH[ratio])}
            />
            {ratio}
          </button>
        ))}
      </div>
    </div>
  );
}
