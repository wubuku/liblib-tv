"use client";

import {
  AudioLines,
  Bot,
  Folder,
  Image,
  LayoutTemplate,
  SquarePlay,
  SquareUser,
  Type,
  Upload,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

/**
 * 左侧插入工具栏 — aside 绝对 bottom-4 left-4 top-[72px] 垂直居中 (SOURCE_FACT)。
 * 9 个 20×20 图标，垂直间距 42px；Beta 徽标挂在第 7 个 (机器人) 上。
 * 源站为竖向药丸底 (视觉近似 CLONE_DECISION)；hover 面板在 Batch 4。
 */
const RAIL_ITEMS: { icon: LucideIcon; label: string; beta?: boolean }[] = [
  { icon: Type, label: "文字" },
  { icon: Image, label: "图片" },
  { icon: SquarePlay, label: "视频" },
  { icon: AudioLines, label: "音频" },
  { icon: LayoutTemplate, label: "分镜" },
  { icon: SquareUser, label: "数字人" },
  { icon: Bot, label: "智能体", beta: true },
  { icon: Folder, label: "素材库" },
  { icon: Upload, label: "上传" },
];

export function JimengToolRail() {
  return (
    <aside className="pointer-events-none absolute bottom-4 left-4 top-[72px] z-30 flex items-center">
      <div className="jimeng-chrome-pill pointer-events-auto flex flex-col items-center gap-1 !rounded-2xl px-2 py-2.5">
        {RAIL_ITEMS.map(({ icon: Icon, label, beta }) => (
          <button
            key={label}
            type="button"
            aria-label={label}
            className="relative flex size-8 items-center justify-center rounded-lg text-white/85 hover:bg-white/10"
          >
            <Icon size={20} />
            {beta ? (
              <span className="absolute -top-0.5 left-1/2 -translate-x-1/2 text-[7px] font-semibold italic leading-none text-[#009EFA] [transform:translateX(-50%)_translateY(-2px)]">
                Beta
              </span>
            ) : null}
          </button>
        ))}
      </div>
    </aside>
  );
}
