"use client";

import { useState } from "react";
import {
  ArrowDownToLine,
  Film,
  FolderOpen,
  Layers,
  UserRound,
  Video,
} from "lucide-react";
import { cn } from "@/lib/utils";

// Batch 536: 2026-09-27 源站采样（liblib-source-exploration-2026-09-25
// NOTES §8 + 截图 18-director-console-opened.png）——3D 导演台最左窄图标栏
// （约 46px）：图层/人物/机位/帧/文件夹/导入 六入口纵排，首项（图层，
// 场景树）为激活态。仅图层面板在 clone 有实现（场景树）；其余五项的
// 面板内容未采样（SOURCE_UNCERTAIN），做视觉切换不导航（CLONE_DECISION）。
const railEntries = [
  { id: "layers", label: "图层", icon: Layers, implemented: true },
  { id: "characters", label: "人物", icon: UserRound, implemented: false },
  { id: "cameras", label: "机位", icon: Video, implemented: false },
  { id: "frames", label: "帧", icon: Film, implemented: false },
  { id: "folders", label: "文件夹", icon: FolderOpen, implemented: false },
  { id: "import", label: "导入", icon: ArrowDownToLine, implemented: false },
] as const;

export function DirectorIconRail() {
  const [active, setActive] = useState<string>("layers");

  return (
    <div
      data-director-icon-rail
      aria-label="导演台资源栏"
      className="absolute inset-y-0 left-0 z-30 flex w-[46px] flex-col items-center gap-1 border-r border-white/[0.07] bg-[#1a1a1a] py-3"
    >
      {railEntries.map((entry) => {
        const Icon = entry.icon;
        const isActive = active === entry.id;
        return (
          <button
            key={entry.id}
            type="button"
            data-director-rail-entry={entry.id}
            aria-label={entry.label}
            title={entry.implemented ? entry.label : `${entry.label}（源站面板未采样）`}
            aria-pressed={isActive}
            onClick={() => setActive(entry.id)}
            className={cn(
              "flex size-8 items-center justify-center rounded-lg text-[#a5a5a5] transition-colors",
              isActive ? "bg-white/[0.12] text-white" : "hover:bg-white/[0.06] hover:text-[#d8d8d8]",
            )}
          >
            <Icon size={16} />
          </button>
        );
      })}
    </div>
  );
}
