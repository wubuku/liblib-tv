"use client";

import { useCallback, useEffect, useId, useRef, useState } from "react";
import type { ReactNode, RefObject } from "react";

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
  /** Batch 846：漫游 tabindex（ARIA menu 模式）。**不给**就是原生 button 的
   *  行为（tab 序里一站）—— 那正是源站**不**做的，见 JimengPaneContextMenu
   *  里 846 的 SOURCE_FACT。所有既有调用方不传，行为不变。 */
  tabIndex,
  /** Batch 846：方向键漫游时要按索引把焦点落回来 */
  itemRef,
  onFocus,
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
  tabIndex?: number;
  itemRef?: (el: HTMLButtonElement | null) => void;
  onFocus?: () => void;
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
      tabIndex={tabIndex}
      ref={itemRef}
      onFocus={onFocus}
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

/* ══════════════════════════════════════════════════════════════════════
 * Batch 847：浮层的键盘模式 —— **一个共享实现**。
 *
 * 为什么不各写各的：批 828 留下过一句「两处是同一段代码的两个拷贝，只修一处
 * 等于没修」，批 846 又踩了一次 —— 改右键菜单改到了另一个组件上，而共用
 * testid 让这件事**不报错**。所以这次把模式收成 hook，三处一起接。
 *
 * 源站实测（登录态 1512×950，探针 846b / 847d，**每个测量从重开的层起手**），
 * 分档**散得很开**，不是一条统一判据：
 *
 *   层                 开层接管焦点   层内 Tab   方向键
 *   canvas-context-menu      是         **不困**   动且环绕   （菜单：方向键是主路径）
 *   jimeng-search-overlay    是         **不困**   不消费     （dialog，不是菜单）
 *   topbar-more-menu         是         **困**     动
 *   canvas-user-menu         是         **困**     动
 *   canvas-zoom-menu         **否**     **困**     动
 *   topbar-share-panel       **否**     **不困**   不动
 *
 * 所以两个开关都**按实测逐层传进来**，不在 hook 里猜：
 *   takeFocusAtOpen / trapTab
 *
 * 两条踩过的坑，都写在实现里：
 *   ① **disabled 按钮不能接收焦点** —— `focus()` 静默失败而 tabindex 正确推进，
 *      表面症状是「方向键一顿一顿还跳格」。所以漫游只走**可用项**。
 *   ② **不要在 setState 的 updater 里做副作用**，也别用 `requestAnimationFrame`
 *      等 tabindex 更新：`tabindex="-1"` 本来就可编程聚焦，同步落焦点即可
 *      （rAF 在 headless 里不合成就不触发，判据量出来的轨迹会是错的）。
 * ══════════════════════════════════════════════════════════════════════ */

export interface MenuKeyboardOpts {
  /** 层里**顶层**可聚焦项的选择器。子菜单项要排除时用更窄的选择器。 */
  itemSelector?: string;
  /** 开层时把焦点移进层里。源站实测：菜单/搜索/更多/账号 = 是；分享/缩放 = 否 */
  takeFocusAtOpen?: boolean;
  /** Tab 困在层内。源站实测：更多/账号/缩放/时间线全屏 = 困；菜单/搜索/分享 = 不困 */
  trapTab?: boolean;
  onClose?: () => void;
  /** Esc 时要不要把焦点接回触发器（源站：搜索/更多/账号/缩放 = 会，菜单/全屏 = 不会） */
  returnFocusRef?: RefObject<HTMLElement | null>;
}

/**
 * 层**挂载即接管焦点**（batch 850）。
 *
 * 源站实测（探针 850，登录态，视口 1512×1200）：生成面板那 4 个下拉
 * —— `gen-model-listbox` / `gen-video-size-listbox` / `gen-mode-listbox` /
 * `gen-duration-listbox` —— **开层全部立刻把焦点移进层里**（分别落在
 * 第一个 option 的 BUTTON、`16:9`、唯一项、以及滑块 thumb）。焦点**留在触发器上**
 * 是不符合源站的：键盘用户点开下拉之后按方向键/Enter，事件还挂在触发器上，
 * 第一下键盘多半什么也没发生。
 *
 * 为什么不给 `useMenuKeyboard` 加个开关、而是单开一个 hook：这 4 个下拉
 * **没有**用 `useMenuKeyboard`（它们是一次性的 `open === "…"` 条件渲染，
 * 方向键那项源站**至今没取到样**，所以不接漫游 tabindex 那一套）。
 * 给它们硬接整只 hook 会顺手引入一堆**没有源站依据**的行为。
 *
 * 依赖用 `[active]` 而不是 `[]`：层是条件渲染的，挂载那一刻 `active`
 * 刚从 false 翻成 true，此时 `ref.current` 已经指向真实的层节点；用 `[]`
 * 的话首次渲染时层还没挂载，focus 会落空。
 */
export function useTakeFocusAtOpen(
  ref: RefObject<HTMLElement | null>,
  active: boolean,
  itemSelector = 'button:not([disabled]),[role="option"],[role="menuitem"],'
    + '[tabindex]:not([tabindex="-1"]),input:not([disabled])',
) {
  useEffect(() => {
    if (!active) return;
    const el = ref.current?.querySelector<HTMLElement>(itemSelector);
    /* 层里没有可聚焦项时**不动**焦点：留在触发器上好过把焦点丢给 body ——
       后者会让键盘用户彻底不知道自己在哪。 */
    if (el) el.focus();
  }, [active, itemSelector, ref]);
}

export function useMenuKeyboard<T extends HTMLElement = HTMLDivElement>(
  opts: MenuKeyboardOpts = {},
) {
  const {
    itemSelector = '[role="menuitem"],button:not([disabled]),a[href],input',
    takeFocusAtOpen = true,
    trapTab = false,
    onClose,
    returnFocusRef,
  } = opts;
  const ref = useRef<T>(null);
  const [activeIdx, setActiveIdx] = useState(0);
  /* 当前项的**镜像**。方向键靠它算 next：把计算塞进 setState 的 updater 等于在
     渲染期做副作用（还可能被 StrictMode 双调用），实测会一顿一顿。 */
  const activeRef = useRef(0);

  /** 层内的可用项（DOM 顺序，跳过 disabled —— 见文件头①） */
  const items = useCallback((): HTMLElement[] => {
    if (!ref.current) return [];
    return Array.from(ref.current.querySelectorAll<HTMLElement>(itemSelector))
      .filter((el) => {
        if (el.hasAttribute('disabled')) return false;
        if (el.getAttribute('aria-disabled') === 'true') return false;
        const r = el.getBoundingClientRect();
        return r.width >= 1 && r.height >= 1;
      });
  }, [itemSelector]);

  const focusIdx = (i: number) => {
    const list = items();
    const el = list[i];
    if (el) el.focus();
  };

  const step = (dir: 1 | -1) => {
    const list = items();
    if (list.length === 0) return;
    const pos = list.indexOf(
      // 用 DOM 位置反查当前项的序号：activeRef 记的是 items() 的下标
      (document.activeElement as HTMLElement | null) ?? (list[0] as HTMLElement),
    );
    const from = pos === -1 ? activeRef.current : pos;
    const next = (from + dir + list.length) % list.length;
    activeRef.current = next;
    setActiveIdx(next);
    focusIdx(next);   // 同步落，见文件头②
  };

  /* 漫游 tabindex：只有**当前项**和**首个可用项**在 tab 序里
     （源站右键菜单实测 8 项里 2 项 = 0，其余 -1）。
     在 effect 里写 DOM 属性而不是让调用方逐项传 —— 三个调用方都不自己设
     tabIndex（已 grep 确认 0 处），所以这个属性归本 hook 独占，React 不会碰。 */
  useEffect(() => {
    const list = items();
    if (list.length === 0) return;
    const cur = list[activeIdx] ? activeIdx : 0;
    list.forEach((el, i) => {
      el.setAttribute('tabindex', i === cur || i === 0 ? '0' : '-1');
    });
  });

  /* 开层即接管焦点（源站实测 takeFocusAtOpen=true 的那些）。同步落，不等下一帧。 */
  useEffect(() => {
    if (!takeFocusAtOpen) return;
    const list = items();
    if (list.length) {
      list[0].focus();
      activeRef.current = 0;
    }
    /* 刻意只跑一次（[]）：这个菜单是一次性浮层，重渲染时重挂监听会把焦点抢回
       第一项（方向键走到第 3 项就弹回去）。
       ⚠️ 这里**不需要** eslint-disable：eslint 对 `[]` 里引用的闭包变量本来就
       报 exhaustive-deps，而批 847 门禁抓到过一条
       `Unused eslint-disable directive` —— 留一条用不上的豁免比不留更坏，
       它会让下一个人以为这里确实有必要豁免。 */
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose?.();
        /* Esc 归位：**同步**接回触发器（源站：搜索/更多/账号/缩放都回）。
           不用 rAF —— 批 846 刚在方向键那条上踩过它在 headless 里不触发的坑。 */
        returnFocusRef?.current?.focus();
        return;
      }
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        /* 必须 preventDefault：不拦的话画布会跟着平移（画布自己监听方向键），
           用户按 ↑ 菜单动了、画布也动了。 */
        e.preventDefault();
        e.stopPropagation();
        step(e.key === "ArrowDown" ? 1 : -1);
        return;
      }
      if (e.key === "Home" || e.key === "End") {
        e.preventDefault();
        e.stopPropagation();
        const list = items();
        if (!list.length) return;
        const next = e.key === "Home" ? 0 : list.length - 1;
        activeRef.current = next;
        setActiveIdx(next);
        focusIdx(next);
        return;
      }
      if (e.key === "Tab" && trapTab) {
        /* 焦点陷阱：Tab / Shift+Tab 在层内**环绕**，不跑到层外去。
           源站实测困住的那些层（更多/账号/缩放/时间线全屏）都是这个行为。 */
        const list = items();
        if (list.length === 0) return;
        e.preventDefault();
        e.stopPropagation();
        const cur = list.indexOf(document.activeElement as HTMLElement);
        const dir = e.shiftKey ? -1 : 1;
        const next = ((cur === -1 ? 0 : cur) + dir + list.length) % list.length;
        activeRef.current = next;
        setActiveIdx(next);
        focusIdx(next);
      }
    };
    window.addEventListener('keydown', onKey, true);
    return () => window.removeEventListener('keydown', onKey, true);
  });

  return { ref, activeIdx, items, focusIdx, step };
}
