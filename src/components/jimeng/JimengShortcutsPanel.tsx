"use client";

import { useEffect, useRef } from "react";
import { X } from "lucide-react";

/**
 * 快捷键面板 (Batch 18)。
 *
 * 证据 (SOURCE_FACT): 帮助菜单「快捷键」打开右侧面板 (≈242px 宽，可滚动):
 * 分区 通用操作 / 视图 / 时间线；行 = 功能名 + 右侧快捷键。
 * 复刻收录 通用操作 + 视图 两组 (时间线分区源站被截断，BLOCKED_BY_FIXTURE)。
 * mock: 编组/全屏/移动工具为展示项，未接行为 (⌘0 适配画布已接)。
 */
const SECTIONS: {
  title: string;
  rows: { label: string; keys: string }[];
}[] = [
  {
    title: "通用操作",
    rows: [
      { label: "打开/关闭 Agent", keys: "⌘ /" },
      { label: "撤销", keys: "⌘ Z" },
      { label: "还原", keys: "⌘ ⇧ Z | ⌘ Y" },
      { label: "移动工具", keys: "V" },
      { label: "全屏", keys: "F" },
      { label: "创建编组", keys: "⌘ G" },
      { label: "取消编组", keys: "⌘ ⇧ G" },
    ],
  },
  {
    title: "视图",
    rows: [
      { label: "放大视图", keys: "⌘ +" },
      { label: "缩小视图", keys: "⌘ -" },
      { label: "适配画布", keys: "⇧ 1 | ⌘ 0" },
      { label: "缩放至 100%", keys: "⌘ 1" },
      { label: "缩放至选中项", keys: "⇧ 2" },
      { label: "缩放画布", keys: "⌘ scroll" },
    ],
  },
];

export function JimengShortcutsPanel({ onClose }: { onClose: () => void }) {
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
      role="dialog"
      aria-label="快捷键"
      className="fixed right-3 top-16 z-[220] flex max-h-[calc(100vh-90px)] w-[242px] flex-col rounded-xl p-4"
      style={{ background: "rgb(38,38,38)" }}
    >
      <div className="mb-2 flex items-center justify-between">
        <p className="text-[14px] text-white/90">快捷键</p>
        <button
          type="button"
          aria-label="关闭快捷键面板"
          onClick={onClose}
          className="flex size-6 items-center justify-center rounded-md text-white/60 hover:bg-white/10 hover:text-white"
        >
          <X size={14} />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto">
        {SECTIONS.map((section) => (
          <div key={section.title} className="mb-2">
            <p className="pt-2 text-[12px] text-white/40">{section.title}</p>
            {section.rows.map((row) => (
              <div
                key={row.label}
                className="flex h-9 items-center justify-between rounded-md px-1 hover:bg-white/[0.06]"
              >
                <span className="text-[13px] text-white/85">{row.label}</span>
                <span className="text-[12px] text-white/45">{row.keys}</span>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
