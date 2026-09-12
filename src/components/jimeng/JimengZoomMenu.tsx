"use client";

import { useEffect, useRef } from "react";
import { useReactFlow } from "@xyflow/react";

import { useJimengStore } from "@/store/jimengStore";

/**
 * 缩放百分比菜单 (Batch 7)。
 *
 * 证据 (SOURCE_FACT): 点击底栏缩放块弹出上方菜单 200×292 rgb(38,38,38) r12:
 * 放大视图⌘+ / 缩小视图⌘− / 适配画布⇧1 / 缩放至选中项⇧2 (无选中禁用) ｜分隔｜
 * 缩放至50% / 缩放至100%⌘1 / 缩放至200%。
 * 功能接 xyflow: zoomIn/zoomOut/fitView/setViewport。
 * CLONE_DECISION: 源站缩放值为可编辑输入框，复刻先只读显示。
 */
export function JimengZoomMenu({ onClose }: { onClose: () => void }) {
  const ref = useRef<HTMLDivElement>(null);
  const selectedNodeId = useJimengStore((s) => s.selectedNodeId);
  const {
    zoomIn,
    zoomOut,
    fitView,
    setViewport,
    getViewport,
  } = useReactFlow();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    };
    window.addEventListener("keydown", onKey);
    window.addEventListener("mousedown", onDown, true);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("mousedown", onDown, true);
    };
  }, [onClose]);

  const setZoom = (zoom: number) => {
    const vp = getViewport();
    // 以视口中心为缩放中心
    const el = document.querySelector(".jimeng-canvas");
    const w = el ? el.clientWidth / 2 : 0;
    const h = el ? el.clientHeight / 2 : 0;
    setViewport({ x: w - (w - vp.x) * (zoom / vp.zoom), y: h - (h - vp.y) * (zoom / vp.zoom), zoom });
    onClose();
  };

  const rows: {
    label: string;
    shortcut?: string;
    disabled?: boolean;
    run: () => void;
  }[] = [
    { label: "放大视图", shortcut: "⌘ +", run: () => void zoomIn() },
    { label: "缩小视图", shortcut: "⌘ -", run: () => void zoomOut() },
    { label: "适配画布", shortcut: "⇧ 1", run: () => void fitView({ duration: 300 }) },
    {
      label: "缩放至选中项",
      shortcut: "⇧ 2",
      disabled: !selectedNodeId,
      run: () => void fitView({ duration: 300, maxZoom: 1 }),
    },
    { label: "缩放至50%", run: () => setZoom(0.5) },
    { label: "缩放至100%", shortcut: "⌘ 1", run: () => setZoom(1) },
    { label: "缩放至200%", run: () => setZoom(2) },
  ];

  return (
    <div
      ref={ref}
      role="menu"
      className="absolute bottom-[calc(100%+8px)] left-0 w-[200px] rounded-xl p-2"
      style={{ background: "rgb(38,38,38)" }}
    >
      {rows.map((row, i) => (
        <div key={row.label}>
          {i === 4 ? <div className="mx-2 my-1 h-px bg-white/[0.08]" /> : null}
          <button
            type="button"
            role="menuitem"
            disabled={row.disabled}
            onClick={() => {
              if (row.disabled) return;
              row.run();
              onClose();
            }}
            className={`flex h-10 w-full items-center justify-between rounded-lg px-2.5 text-[13px] ${
              row.disabled ? "cursor-default text-white/30" : "text-white/85 hover:bg-white/10"
            }`}
          >
            {row.label}
            {row.shortcut ? (
              <span className="text-[12px] text-white/45">{row.shortcut}</span>
            ) : null}
          </button>
        </div>
      ))}
    </div>
  );
}
