"use client";

// Batch 831（源站 2026-10-21 实测 + 源站组件代码 `0fmehki05gkzw.js.js`）：
// 导演台的「快捷键」对话框。源站没有这层，clone 只有一枚点了没反应的「帮助」圆钮
// （DirectorIconRail.tsx 的 data-director-rail-entry="help"）。
//
// ★ 源站实测（raw/source-831-help-geometry.json）：
//   对话框 480×314 @(297,60) / role=dialog / aria-modal=true / aria-label=快捷键
//   标题「快捷键」48×22 @(322,81)，16px、weight 500、#F7F7F7
//   两列各 192×228 @(322,123) 与 @(563,123)，中间 1px 竖线（左右各 24px）
//   12 行：每行 h-7，标签 14px/20px，键帽 28×28（rounded-lg / bg-white/3 /
//        border-white/12 / 14px 文字），「WASDQE」那枚宽 74
//   ⌘ 徽标是 **16×16 的 SVG**（batch 830 的教训：纯文本读数器读不到它）
//
// ★ 源站代码（同一 chunk 的 mI/mM/mk/mS 组件）：
//   <div role="dialog" aria-modal="true" aria-label="快捷键"
//        class="relative h-[314px] w-[480px] rounded-2xl border border-white/10
//               bg-[#1f1f1f]/95 p-6 text-neutral-50 backdrop-blur-[32px] …">
//     <div class="flex h-[22px] items-center justify-between">
//       <h2 class="text-base font-medium leading-[22px] text-neutral-50">快捷键</h2>
//     <div class="mt-4 flex h-[228px] w-[432px] items-stretch">
//       <div class="flex w-[192px] flex-col justify-between">…6 行…</div>
//       <div class="mx-6 w-px shrink-0 bg-white/10"/>
//       <div class="flex w-[192px] flex-col justify-between">…6 行…</div>
//
// ★ ★ 为什么尺寸/颜色/阴影走 **inline style** 而不是 Tailwind 任意值类：
//   4317 的 Tailwind 扫描是**冻结**的（batch 824 实测：dev 进程与磁盘上的 CSS
//   chunk 都是旧的）⟹ 新加的 `h-[314px]` / `w-[480px]` / `left-[297px]` /
//   `bg-[#1f1f1f]/95` 这些**在 dev 上不会生成** ⟹ 同一个组件在 dev 上「没样式」、
//   在 prod 上「有样式」。本组件实测过：dev CSS 里 `h-[314px]`、`w-[480px]`、
//   `left-[297px]`、`h-[228px]`、`w-[432px]`、`mx-6`、`bg-[#1f1f1f]/95`、
//   `shadow-[0_2px_4px_…]` **全部缺失** ⟹ 全部改 inline style ⟹ dev 与 prod 一致。

import { useEffect } from "react";

type KeyBadge = {
  id: string;
  /** 徽标上的文字（⌘ / ⌫ 用 SVG 图标代替） */
  label?: string;
  /** 图标型徽标 */
  icon?: "command" | "delete";
};

type ShortcutRow = {
  label: string;
  keys: KeyBadge[];
};

// 源站面板左列（源码 mI 里的第一组）
const LEFT_COLUMN: ShortcutRow[] = [
  { label: "俯视视角", keys: [{ id: "top-view", label: "T" }] },
  { label: "重置视角", keys: [{ id: "reset-view", label: "H" }] },
  { label: "移动", keys: [{ id: "transform-move", label: "V" }] },
  { label: "旋转", keys: [{ id: "transform-rotate", label: "R" }] },
  { label: "缩放", keys: [{ id: "transform-scale", label: "F" }] },
  { label: "移动当前视角", keys: [{ id: "move-current-view", label: "WASDQE" }] },
];

// 源站面板右列（源码 mI 里的第二组）
const RIGHT_COLUMN: ShortcutRow[] = [
  { label: "正面视角", keys: [{ id: "front-view", label: "Y" }] },
  { label: "网格吸附", keys: [{ id: "snap-grid", label: "X" }] },
  {
    label: "打组",
    keys: [
      { id: "group-command", icon: "command" },
      { id: "group-key", label: "G" },
    ],
  },
  {
    label: "解组",
    keys: [
      { id: "ungroup-command", icon: "command" },
      { id: "ungroup-shift", label: "⇧" },
      { id: "ungroup-key", label: "D" },
    ],
  },
  {
    label: "撤销",
    keys: [
      { id: "undo-command", icon: "command" },
      { id: "undo-key", label: "Z" },
    ],
  },
  { label: "删除", keys: [{ id: "delete-key", icon: "delete" }] },
];

/** 源站的 ⌘ 符号（16×16 SVG，源码 mC 组件的 path 原文） */
function CommandGlyph() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      aria-hidden="true"
      data-director-shortcut-command-glyph
    >
      <path
        d="M5.25 5.25H10.75V10.75H5.25V5.25ZM5.25 5.25H4.25C3.42157 5.25 2.75 4.57843 2.75 3.75C2.75 2.92157 3.42157 2.25 4.25 2.25C5.07843 2.25 5.75 2.92157 5.75 3.75V4.25M10.75 5.25H11.75C12.5784 5.25 13.25 4.57843 13.25 3.75C13.25 2.92157 12.5784 2.25 11.75 2.25C10.9216 2.25 10.25 2.92157 10.25 3.75V4.25M5.25 10.75H4.25C3.42157 10.75 2.75 11.4216 2.75 12.25C2.75 13.0784 3.42157 13.75 4.25 13.75C5.07843 13.75 5.75 13.0784 5.75 12.25V11.75M10.75 10.75H11.75C12.5784 10.75 13.25 11.4216 13.25 12.25C13.25 13.0784 12.5784 13.75 11.75 13.75C10.9216 13.75 10.25 13.0784 10.25 12.25V11.75"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.15"
      />
    </svg>
  );
}

/** 源站的「删除」键帽图标（16×16 SVG，源码 mA 组件的 path 原文） */
function DeleteGlyph() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      aria-hidden="true"
      data-director-shortcut-delete-glyph
    >
      <path
        d="M6 5.75L10 9.75M10 5.75L6 9.75M5.05 12.25H11.75C12.5784 12.25 13.25 11.5784 13.25 10.75V4.75C13.25 3.92157 12.5784 3.25 11.75 3.25H5.05C4.65218 3.25 4.27064 3.40804 3.98934 3.68934L1.75 5.92868C1.16421 6.51447 1.16421 7.46421 1.75 8.05L3.98934 10.2893C4.27064 10.5706 4.65218 10.7287 5.05 10.7287"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.2"
      />
    </svg>
  );
}

function KeyBadgeView({ badge }: { badge: KeyBadge }) {
  return (
    <span
      data-director-shortcut-badge={badge.id}
      className="flex h-7 min-w-7 shrink-0 items-center justify-center rounded-lg border border-white/12 bg-white/3 px-1.5 text-sm leading-5 text-white/90"
    >
      {badge.icon === "command" ? <CommandGlyph /> : null}
      {badge.icon === "delete" ? <DeleteGlyph /> : null}
      {badge.label ? <span data-director-shortcut-badge-text>{badge.label}</span> : null}
    </span>
  );
}

function ShortcutRowView({ row }: { row: ShortcutRow }) {
  return (
    <div
      data-director-shortcut-row={row.label}
      className="flex h-7 items-center justify-between gap-2"
    >
      <span className="min-w-0 text-sm leading-5 text-white/80">{row.label}</span>
      <span className="flex shrink-0 items-center gap-2">
        {row.keys.map((badge) => (
          <KeyBadgeView key={badge.id} badge={badge} />
        ))}
      </span>
    </div>
  );
}

export function DirectorShortcutsDialog({ onClose }: { onClose: () => void }) {
  // 源站：Esc 关掉快捷键面板（源码 `if(tN){"escape"===n&&tL(!1);return}`）。
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.stopPropagation();
        onClose();
      }
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [onClose]);

  return (
    <div
      data-director-shortcuts-overlay
      role="presentation"
      className="absolute inset-0 z-40"
      onMouseDown={onClose}
    >
      {/* 源站把这个对话框钉在 `left-[297px] top-[60px]`（**绝对偏移**，不是居中），
          且点击它不会冒泡到遮罩（源站 `onMouseDown={e=>e.stopPropagation()}`）。 */}
      <div
        className="absolute"
        style={{ left: 297, top: 60 }}
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div
          role="dialog"
          aria-modal="true"
          aria-label="快捷键"
          data-director-shortcuts-dialog
          className="relative border border-white/10 p-6 text-neutral-50 backdrop-blur-[32px]"
          style={{
            width: 480,
            height: 314,
            borderRadius: 16,
            background: "rgba(31,31,31,0.95)",
            boxShadow:
              "0 2px 4px rgba(0,0,0,0.04), 0 4px 10px rgba(0,0,0,0.10)",
          }}
        >
          <div className="flex items-center justify-between" style={{ height: 22 }}>
            <h2
              data-director-shortcuts-title
              className="text-base font-medium text-neutral-50"
              // ★ 源站那个 4px 的来源：源站的 CSS **没有**重置标题的下外边距
              //   ⟹ h2 带 UA 默认的 `margin-bottom: 8px` ⟹ 在 22px 高的 flex 行里
              //   （items-center）它的**外边距盒**（30px）居中 ⟹ 边框盒被抬到
              //   行顶之上 4px ⟹ 标题落在 **81** 而不是 **85**（行顶 85）。
              //   clone 的 Tailwind preflight 把标题 margin 清零了 ⟹ 直接照抄这个
              //   行为，否则标题会比源站低 4px（实测：源站 81，clone 85）。
              style={{ lineHeight: "22px", marginBottom: 8 }}
            >
              快捷键
            </h2>
          </div>
          <div
            className="mt-4 flex items-stretch"
            style={{ height: 228, width: 432 }}
          >
            <div
              data-director-shortcuts-column="left"
              className="flex flex-col justify-between"
              style={{ width: 192 }}
            >
              {LEFT_COLUMN.map((row) => (
                <ShortcutRowView key={row.label} row={row} />
              ))}
            </div>
            <div
              aria-hidden="true"
              className="w-px shrink-0 bg-white/10"
              style={{ margin: "0 24px" }}
            />
            <div
              data-director-shortcuts-column="right"
              className="flex flex-col justify-between"
              style={{ width: 192 }}
            >
              {RIGHT_COLUMN.map((row) => (
                <ShortcutRowView key={row.label} row={row} />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export { LEFT_COLUMN, RIGHT_COLUMN };
