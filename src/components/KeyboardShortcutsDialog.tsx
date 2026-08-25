"use client";

import { Command, Hand, Mouse, MousePointer2, X } from "lucide-react";

interface KeyboardShortcutsDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

interface ShortcutItem {
  label: string;
  keys: string[];
  suffix?: string;
  visual?: "mouse" | "hand";
}

const sections: Array<{ title: string; items: ShortcutItem[] }> = [
  {
    title: "创作",
    items: [
      { label: "成组", keys: ["G"] },
      { label: "解组", keys: ["⇧", "G"] },
      { label: "复制节点和连线", keys: ["cmd", "D"] },
      { label: "新建节点", keys: ["Tab"] },
      { label: "删除", keys: ["Delete"] },
    ],
  },
  {
    title: "缩放",
    items: [
      { label: "放大", keys: ["cmd", "+"] },
      { label: "缩小", keys: ["cmd", "−"] },
      { label: "适应画布", keys: ["cmd", "0"] },
      { label: "触控板", keys: [], visual: "hand" },
      { label: "鼠标", keys: ["cmd"], visual: "mouse" },
    ],
  },
  {
    title: "移动画布",
    items: [
      { label: "键盘", keys: ["Space"], visual: "mouse" },
      { label: "触控板", keys: [], visual: "hand" },
      { label: "鼠标", keys: [], visual: "mouse" },
      { label: "移动", keys: ["V"] },
      { label: "抓手工具", keys: ["H"] },
      { label: "整理画布", keys: ["⌥", "⇧", "F"] },
    ],
  },
  {
    title: "其他",
    items: [
      { label: "撤销", keys: ["cmd", "Z"] },
      { label: "重做", keys: ["cmd", "⇧", "Z"] },
      { label: "重做（Windows）", keys: ["ctrl", "Y"] },
    ],
  },
];

function Key({ value }: { value: string }) {
  return (
    <kbd className="flex min-h-7 min-w-7 items-center justify-center rounded-lg border border-white/[0.06] bg-[#1d1d1d] px-1.5 text-sm font-normal text-[#dedede] shadow-[inset_0_-1px_rgba(255,255,255,0.04)]">
      {value === "cmd" || value === "ctrl" ? <Command size={15} /> : value}
    </kbd>
  );
}

export function KeyboardShortcutsDialog({ isOpen, onClose }: KeyboardShortcutsDialogProps) {
  if (!isOpen) return null;

  return (
    <section
      aria-label="快捷键面板"
      data-liblib-overlay="shortcuts"
      className="fixed bottom-[73px] left-1/2 z-[62] h-[447px] w-[905px] max-w-[calc(100vw-24px)] -translate-x-1/2 rounded-2xl border border-[#363636] bg-[#262626]/95 p-6 shadow-[0_20px_54px_rgba(0,0,0,0.55)] backdrop-blur-lg max-md:max-h-[calc(100vh-130px)] max-md:overflow-y-auto max-md:p-4 max-sm:bottom-[109px]"
    >
      <button type="button" onClick={onClose} aria-label="关闭快捷键面板" className="absolute right-3 top-3 z-10 flex size-7 items-center justify-center rounded-lg text-[#aaa] hover:bg-white/[0.07] hover:text-white">
        <X size={20} />
      </button>
      <span className="absolute -bottom-1.5 left-[calc(50%+104px)] size-3 rotate-45 border-b border-r border-[#363636] bg-[#262626]" />

      <div className="grid h-full grid-cols-[229px_230px_228px_minmax(0,1fr)] gap-5 max-md:grid-cols-2 max-md:gap-y-8 max-sm:grid-cols-1">
        {sections.map((section, sectionIndex) => (
          <div key={section.title} className={sectionIndex < sections.length - 1 ? "border-r border-white/[0.07] pr-5 max-sm:border-r-0 max-sm:pr-0" : ""}>
            <h2 className="mb-3 text-sm font-medium text-[#12cce8]">{section.title}</h2>
            <div className="space-y-1.5">
              {section.items.map((item) => (
                <div key={item.label} className="flex min-h-8 items-center gap-2 text-sm">
                  <span className="min-w-0 flex-1 whitespace-nowrap text-[#8f8f8f]">{item.label}</span>
                  <span className="flex shrink-0 items-center gap-1">
                    {item.keys.map((key, index) => <Key key={`${item.label}-${key}-${index}`} value={key} />)}
                    {item.visual === "hand" && <span className="flex size-7 items-center justify-center text-[#31c8df]"><Hand size={18} /></span>}
                    {item.visual === "mouse" && <span className="flex size-7 items-center justify-center text-[#31c8df]">{item.label === "键盘" ? <MousePointer2 size={17} /> : <Mouse size={18} />}</span>}
                    {item.suffix && <span className="text-xs text-[#c7c7c7]">{item.suffix}</span>}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
