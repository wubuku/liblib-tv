"use client";

import { useEffect, useRef } from "react";

/**
 * 浮层焦点管理 (Batch 811)。
 *
 * SOURCE_FACT（@1680×826 登录态，逐层实测 activeElement + Tab 序列）：
 * 源站各浮层的焦点行为**并不一致**，所以不能一刀切：
 *
 *   节点摘要弹层  打开 → 焦点进入浮层首个可聚焦项
 *                 Tab  → **焦点陷阱**，10 次 Tab 全部留在浮层内
 *                 关闭 → 焦点**回到触发器** (canvas-node-summary-trigger)
 *   AI 抽屉       打开 → 焦点进入 `aside[canvas-feature-sidecar]`
 *                 Tab  → 会逃出（源站没做陷阱）
 *                 关闭 → 停在抽屉内某项，不回触发器
 *   分享面板      打开 → 焦点**留在触发器**，不在浮层内
 *
 * 所以本 hook 提供两件**分开**的能力，按各层源站行为取用，不要全开：
 *   `trap`      焦点陷阱（仅节点摘要弹层开）
 *   `returnTo`  关闭后归还焦点给触发器（仅节点摘要弹层开）
 *
 * 全开 = 擅自"改进"源站，偏离复刻目标；全关 = 漏掉源站已做对的那一层。
 */

const FOCUSABLE = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled]):not([type=hidden])",
  "textarea:not([disabled])",
  "select:not([disabled])",
  '[tabindex]:not([tabindex="-1"])',
].join(",");

function focusablesIn(root: HTMLElement): HTMLElement[] {
  return Array.from(root.querySelectorAll<HTMLElement>(FOCUSABLE)).filter(
    (el) => el.offsetWidth > 0 || el.offsetHeight > 0 || el === document.activeElement,
  );
}

export function useLayerFocus(
  ref: React.RefObject<HTMLElement | null>,
  active: boolean,
  opts: { trap?: boolean; returnTo?: boolean } = {},
) {
  const { trap = false, returnTo = false } = opts;
  // 触发器只在**本次打开的第一次** mount 时记一次。
  // 实测存在 mount→cleanup→mount 的假卸载：第二次 mount 时 activeElement
  // 已经是浮层内的第一项，若照记就会把"触发器"记成浮层内部的节点，
  // 关闭时 document.contains(opener) 为 false → 焦点掉到 body。
  const openerRef = useRef<HTMLElement | null>(null);

  // 打开：把焦点搬进浮层；**卸载时**归还给触发器。
  // 必须写在 cleanup 里而不是「active 变 false」的分支里 ——
  // 这些浮层是条件渲染的（`open ? <Popover/> : null`），关闭走的是
  // **卸载**，active 从头到尾都是 true，那个 false 分支永远不执行。
  // 踩过：以为写了归还逻辑，实测关闭后焦点停在 body。
  useEffect(() => {
    if (!active) return;
    const root = ref.current;
    if (!root) return;

    // 搬焦点**之前**先记住当前焦点 —— 那就是触发器
    if (!openerRef.current) {
      openerRef.current = (document.activeElement as HTMLElement | null) ?? null;
    }
    const opener = openerRef.current;
    const first = focusablesIn(root)[0];
    if (first) first.focus();
    else {
      if (root.tabIndex < 0) root.tabIndex = -1;
      root.focus();
    }

    return () => {
      if (!returnTo || !opener) return;
      // 下一帧再还，**不能**用微任务：点外部关闭时 React 的卸载可能排在
      // 微任务之后，此刻 root 还 isConnected，守卫会把归还整个跳过 ——
      // 实测表现就是「点外面关掉浮层，焦点掉到 body」。
      requestAnimationFrame(() => {
        // 关键守卫：React 清理 effect 时宿主节点**还没**被移除，所以不能在
        // cleanup 里同步判断，必须推到下一帧。此时：
        //   真关闭   → 节点已 detach，root.isConnected === false → 归还焦点
        //   假卸载   → 紧接着又 mount 了一次（实测日志 mount→cleanup→mount，
        //              cleanup 时 rootConnected=true），节点还在 → 不归还，
        //              否则会把第二次 mount 刚聚焦的第一项抢回触发器。
        if (root.isConnected) return;
        if (opener && document.contains(opener)) opener.focus();
        openerRef.current = null;
      });
    };
  }, [active, returnTo, ref]);

  // 焦点陷阱（仅节点摘要弹层开）
  useEffect(() => {
    if (!active || !trap) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Tab") return;
      const root = ref.current;
      if (!root) return;
      const items = focusablesIn(root);
      if (items.length === 0) {
        e.preventDefault();
        return;
      }
      const idx = items.indexOf(document.activeElement as HTMLElement);
      const next = e.shiftKey ? idx - 1 : idx + 1;
      // 环绕：首项再 Tab 回末项，末项再 Shift+Tab 回首项
      if (idx === -1 || next < 0 || next >= items.length) {
        e.preventDefault();
        items[e.shiftKey ? items.length - 1 : 0].focus();
      }
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [active, trap, ref]);
}
