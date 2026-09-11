"use client";

import { useEffect, useRef } from "react";
import {
  BookOpen,
  CircleHelp,
  Command,
  Stamp,
  Terminal,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

/**
 * 顶栏帮助下拉 (Batch 7)。
 *
 * 证据 (SOURCE_FACT): 点击顶栏 ? 图标弹出 240×272 rgb(34,34,34) r12 菜单:
 * 帮助中心 / 使用手册 / 快捷键 / AI生成水印设置 / 即梦CLI（每行 16px 图标）。
 * 顶部还展示租户名 — 复刻用静态「个人空间」占位 (mock)。
 * CLONE_DECISION: 行距与图标为近似 (截图读取)。
 */
const HELP_ITEMS: { icon: LucideIcon; label: string }[] = [
  { icon: CircleHelp, label: "帮助中心" },
  { icon: BookOpen, label: "使用手册" },
  { icon: Command, label: "快捷键" },
  { icon: Stamp, label: "AI生成水印设置" },
  { icon: Terminal, label: "即梦CLI" },
];

export function JimengHelpMenu({ onClose }: { onClose: () => void }) {
  const ref = useRef<HTMLDivElement>(null);

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
      className="absolute right-0 top-[calc(100%+8px)] w-[240px] rounded-xl p-2"
      style={{ background: "rgb(34,34,34)" }}
    >
      <p className="px-2 pb-1 pt-1 text-[12px] leading-6 text-white/45">个人空间</p>
      {HELP_ITEMS.map(({ icon: Icon, label }) => (
        <button
          key={label}
          type="button"
          role="menuitem"
          className="flex h-11 w-full items-center gap-2.5 rounded-lg px-2.5 text-[13px] text-white/85 hover:bg-white/10"
        >
          <Icon size={16} className="shrink-0 text-white/70" />
          {label}
        </button>
      ))}
    </div>
  );
}
