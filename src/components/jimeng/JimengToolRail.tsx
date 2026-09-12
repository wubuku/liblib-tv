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
import { useReactFlow } from "@xyflow/react";

import { useJimengStore } from "@/store/jimengStore";

/**
 * 左侧插入工具栏 — aside 绝对 bottom-4 left-4 top-[72px] 垂直居中 (SOURCE_FACT)。
 * 9 个 20×20 图标，垂直间距 42px；第 7 个 (智能体) 挂 Beta 徽标。
 * hover 高亮 rgba(255,255,255,0.12) (SOURCE_FACT)；点击 文字/图片/视频 在画布
 * 中央插入对应节点 (Batch 17)，其余项 mock no-op。
 */
const RAIL_ITEMS: {
  icon: LucideIcon;
  label: string;
  beta?: boolean;
  insert?: "video" | "image" | "text";
}[] = [
  { icon: Type, label: "文字", insert: "text" },
  { icon: Image, label: "图片", insert: "image" },
  { icon: SquarePlay, label: "视频", insert: "video" },
  { icon: AudioLines, label: "音频" },
  { icon: LayoutTemplate, label: "分镜" },
  { icon: SquareUser, label: "数字人" },
  { icon: Bot, label: "智能体", beta: true },
  { icon: Folder, label: "素材库" },
  { icon: Upload, label: "上传" },
];

export function JimengToolRail() {
  const addNodeAt = useJimengStore((s) => s.addNodeAt);
  const { screenToFlowPosition } = useReactFlow();

  const insertAtCenter = (kind: "video" | "image" | "text") => {
    const el = document.querySelector(".jimeng-canvas");
    const position = screenToFlowPosition({
      x: el ? el.clientWidth / 2 : window.innerWidth / 2,
      y: el ? el.clientHeight / 2 : window.innerHeight / 2,
    });
    addNodeAt(kind, {
      x: position.x - 280,
      y: position.y - 160,
    });
  };

  return (
    <aside className="pointer-events-none absolute bottom-4 left-4 top-[72px] z-30 flex items-center">
      <div className="jimeng-chrome-pill pointer-events-auto flex flex-col items-center gap-1 !rounded-2xl px-2 py-2.5">
        {RAIL_ITEMS.map(({ icon: Icon, label, beta, insert }) => (
          <button
            key={label}
            type="button"
            aria-label={label}
            onClick={() => {
              if (insert) insertAtCenter(insert);
            }}
            className="relative flex size-8 items-center justify-center rounded-lg text-white/85 hover:bg-white/[0.12]"
          >
            <Icon size={20} />
            {beta ? (
              <span className="absolute -top-0.5 left-1/2 text-[7px] font-semibold italic leading-none text-[#009EFA] [transform:translateX(-50%)_translateY(-2px)]">
                Beta
              </span>
            ) : null}
          </button>
        ))}
      </div>
    </aside>
  );
}
