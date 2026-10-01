"use client";

import { useId } from "react";
import type { ReactNode } from "react";

/**
 * 浮层菜单的共享外观 (Batch 814)。
 *
 * 缩放菜单（batch 811 已逐项对齐）与画布右键菜单（batch 814）**是同一套设计系统**：
 * 200 宽、rounded-xl(12)、bg rgb(38,38,38)、**padding 4px**、行高 36、行间隙 4、
 * 文案 13px 纯白 / 禁用 white/20、快捷键 13px white/60 右缘 184、hover white/8、
 * 分隔线 4px 盒内居中 1px white/4。
 *
 * 竖向账（两处菜单**同款**，292 = 7 项 + 1 分隔线时）：
 *   4(上边距) + 7×36 + 4(分隔线) + 7×4(间隙) + 4(下边距) = 292 ✓
 *
 * 为什么抽出来：batch 812 的教训是"同一套值散在 7 个文件里各写一份字面量"，
 * 改一处漏六处。这里是同一类风险的前兆 —— 两处菜单已经各自漂移过一次
 * （右键菜单还是 192 宽 / p-2 / 行高 44 / 禁用原因内联），
 * 所以在**第二次**漂移发生前收口。
 *
 * SOURCE_FACT batch 814 (2026-10-03 @1512×950 源站右键菜单逐元素实测)：
 * - 行 192×36 @x=4、`padding 9px 12px`、圆角 8
 * - 文案 span 13px/22px，启用 `rgb(255,255,255)`，禁用 **`rgba(255,255,255,0.2)`**
 * - 快捷键 span 13px/22px `rgba(255,255,255,0.6)`，右缘 184
 * - `aria` = 文案本身；`title` = 启用时 `{文案} ({快捷键})`、
 *   禁用时**直接是禁用原因**
 * - 禁用原因另有一个 **1×1、position:absolute** 的隐藏 span（实测 @x=100，
 *   即行盒水平中心），由 `aria-describedby` 指过去 —— 它**不在** flex 流里，
 *   所以不影响右对齐。复刻此前把「无需重做操作」当**正文**内联渲染，
 *   把快捷键顶得左移并溢出，是布局 bug。
 */

/** 菜单壳：200 宽、圆角 12、padding 4、flex 列 + 4px 间隙。 */
export const MENU_PANEL_CLASS =
  "flex w-[200px] flex-col gap-1 rounded-xl p-1";

/** 菜单底色（两处菜单实测一致）。 */
export const MENU_PANEL_BG = "rgb(38,38,38)";

/**
 * 分隔线：**盒高 4px**、左右 margin 12 → 宽 168，1px 线在盒内垂直居中。
 * 注意不是 `h-px` —— 做成 1px 元素会让总高短 3px（batch 811 踩过）。
 */
export function MenuSeparator() {
  return (
    <div role="separator" className="mx-3 flex h-1 shrink-0 items-center">
      <div className="h-px w-full bg-white/[0.04]" />
    </div>
  );
}

export function MenuItem({
  label,
  shortcut,
  icon,
  disabled,
  /** 禁用原因：进 `title`，同时渲染成 1×1 隐藏 span 供 aria-describedby */
  disabledReason,
  onSelect,
  testId,
  submenuAffordance,
}: {
  label: string;
  shortcut?: string;
  icon?: ReactNode;
  disabled?: boolean;
  disabledReason?: string;
  onSelect?: () => void;
  testId?: string;
  /** 子菜单箭头等右侧装饰（不是快捷键，不参与右对齐语义） */
  submenuAffordance?: ReactNode;
}) {
  const reasonId = useId();

  return (
    <button
      type="button"
      role="menuitem"
      // 源站每一项的 aria 就是文案本身（实测 aria='复制' / aria='Add tags'…）。
      // 按钮文本已经能提供可及名，但补上 aria 与源站逐字一致，也让
      // 验收脚本能按源站实名稳定选择。
      aria-label={label}
      disabled={disabled}
      data-testid={testId}
      // 源站 title：启用时 `{文案} ({快捷键})`；禁用时直接是禁用原因
      title={
        disabled
          ? disabledReason
          : shortcut
            ? `${label} (${shortcut})`
            : undefined
      }
      aria-describedby={disabled && disabledReason ? reasonId : undefined}
      onClick={() => {
        if (disabled) return;
        onSelect?.();
      }}
      className={`relative flex h-9 w-full shrink-0 items-center justify-between rounded-lg px-3 text-[13px] leading-5 ${
        disabled
          ? "cursor-default text-white/20"
          : "text-white hover:bg-white/[0.08]"
      }`}
    >
      {icon ? (
        <span className="flex min-w-0 items-center gap-2">{icon}{label}</span>
      ) : (
        <span className="min-w-0 truncate">{label}</span>
      )}
      {submenuAffordance ?? (
        // 快捷键 span **始终渲染**（源站无快捷键时是 0 宽空 span，右缘仍停在 184）
        <span className="shrink-0 text-white/60">{shortcut ?? ""}</span>
      )}
      {disabled && disabledReason ? (
        // 1×1 绝对定位：实测源站在行盒水平中心（x=100），不参与 flex 流，
        // 所以不会把快捷键顶偏
        <span
          id={reasonId}
          aria-hidden
          className="pointer-events-none absolute left-1/2 top-1/2 h-px w-px overflow-hidden whitespace-nowrap"
        >
          {disabledReason}
        </span>
      ) : null}
    </button>
  );
}
