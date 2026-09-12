"use client";

import { useEffect, useRef, useState } from "react";
import { ChevronRight } from "lucide-react";
import { AudioLines, Image, SquarePlay, Type } from "lucide-react";
import type { LucideIcon } from "lucide-react";

/**
 * 画布空白右键菜单 (Batch 25)。
 *
 * 证据 (SOURCE_FACT): 空白画布右键弹出菜单: 新建节点 > (子菜单)、
 * 粘贴 ⌘V、重做 ⌘⇧Z (无历史禁用)、撤销 ⌘Z；样式与节点右键菜单同族
 * (rgb(38,38,38) r12)。「新建节点」子菜单项: 文本/图片/视频/音频
 * (hover 展开，CLONE_DECISION: 源站子菜单未展开提取)。
 */
const INSERT_ITEMS: { icon: LucideIcon; label: string; kind: "video" | "image" | "text" | "audio" }[] = [
  { icon: Type, label: "文本", kind: "text" },
  { icon: Image, label: "图片", kind: "image" },
  { icon: SquarePlay, label: "视频", kind: "video" },
  { icon: AudioLines, label: "音频", kind: "audio" },
];

export interface JimengPaneMenuState {
  x: number;
  y: number;
}

export function JimengPaneContextMenu({
  state,
  canUndo,
  canRedo,
  clipboard,
  onClose,
  onInsert,
  onPaste,
  onUndo,
  onRedo,
}: {
  state: JimengPaneMenuState;
  canUndo: boolean;
  canRedo: boolean;
  clipboard: boolean;
  onClose: () => void;
  onInsert: (kind: "video" | "image" | "text" | "audio") => void;
  onPaste: () => void;
  onUndo: () => void;
  onRedo: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [submenuOpen, setSubmenuOpen] = useState(false);

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

  return (
    <div
      ref={ref}
      role="menu"
      className="fixed z-[200] w-44 rounded-xl p-2"
      style={{
        left: state.x,
        top: state.y,
        background: "rgb(38,38,38)",
      }}
    >
      {/* 新建节点 (hover 展开子菜单) */}
      <div
        className="relative"
        onMouseEnter={() => setSubmenuOpen(true)}
        onMouseLeave={() => setSubmenuOpen(false)}
      >
        <button
          type="button"
          role="menuitem"
          onClick={() => setSubmenuOpen((v) => !v)}
          className="flex h-11 w-full items-center justify-between rounded-lg px-2.5 text-[13px] text-white/85 hover:bg-white/10"
        >
          新建节点
          <ChevronRight size={13} className="text-white/45" />
        </button>
        {submenuOpen ? (
          <div
            className="absolute left-full top-0 ml-1 w-40 rounded-xl p-2"
            style={{ background: "rgb(38,38,38)" }}
            role="menu"
          >
            {INSERT_ITEMS.map(({ icon: Icon, label, kind }) => (
              <button
                key={label}
                type="button"
                role="menuitem"
                onClick={() => {
                  onInsert(kind);
                  onClose();
                }}
                className="flex h-11 w-full items-center gap-2.5 rounded-lg px-2.5 text-[13px] text-white/85 hover:bg-white/10"
              >
                <Icon size={16} className="shrink-0 text-white/70" />
                {label}
              </button>
            ))}
          </div>
        ) : null}
      </div>

      <button
        type="button"
        role="menuitem"
        disabled={!clipboard}
        onClick={() => {
          onPaste();
          onClose();
        }}
        className={`flex h-11 w-full items-center justify-between rounded-lg px-2.5 text-[13px] ${
          clipboard ? "text-white/85 hover:bg-white/10" : "cursor-default text-white/30"
        }`}
      >
        粘贴
        <span className="text-[12px] text-white/45">⌘ V</span>
      </button>
      <div className="mx-2 my-1 h-px bg-white/[0.08]" />
      <button
        type="button"
        role="menuitem"
        disabled={!canRedo}
        onClick={() => {
          onRedo();
          onClose();
        }}
        className={`flex h-11 w-full items-center justify-between rounded-lg px-2.5 text-[13px] ${
          canRedo ? "text-white/85 hover:bg-white/10" : "cursor-default text-white/30"
        }`}
      >
        重做
        <span className="text-[12px] text-white/45">⌘ ⇧ Z</span>
      </button>
      <button
        type="button"
        role="menuitem"
        disabled={!canUndo}
        onClick={() => {
          onUndo();
          onClose();
        }}
        className={`flex h-11 w-full items-center justify-between rounded-lg px-2.5 text-[13px] ${
          canUndo ? "text-white/85 hover:bg-white/10" : "cursor-default text-white/30"
        }`}
      >
        撤销
        <span className="text-[12px] text-white/45">⌘ Z</span>
      </button>
    </div>
  );
}
