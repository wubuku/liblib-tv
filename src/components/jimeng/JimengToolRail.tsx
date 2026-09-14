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
import { useRef } from "react";
import { useReactFlow } from "@xyflow/react";

import { useJimengStore } from "@/store/jimengStore";

/**
 * 左侧插入工具栏 — aside 绝对 bottom-4 left-4 top-[72px] 垂直居中 (SOURCE_FACT)。
 * 9 个 20×20 图标，垂直间距 42px；第 7 个 (导演台) 挂 Beta 徽标。
 * hover 高亮 rgba(255,255,255,0.12) (SOURCE_FACT)；点击 文本/图片/视频/音频
 * 在画布中央插入对应节点 (Batch 17/68)，其余项 mock no-op。
 * Batch 73 (SOURCE_FACT): 悬停左栏时图标右侧显示标签飞出层
 * (73-upload-panel.png)；上传 打开多选文件选择器，选中文件作为
 * 本地上传视频节点落入画布中央 (filechooser multiple 实证)。
 */
const RAIL_ITEMS: {
  icon: LucideIcon;
  label: string;
  beta?: boolean;
  insert?: "video" | "image" | "text" | "audio";
}[] = [
  // Batch 68 (SOURCE_FACT): 标签对齐源站 aria-label 提取
  // (68-rail.json: 文本/图片/视频/音频/时间线/主体/导演台/资产库/上传)
  { icon: Type, label: "文本", insert: "text" },
  { icon: Image, label: "图片", insert: "image" },
  { icon: SquarePlay, label: "视频", insert: "video" },
  { icon: AudioLines, label: "音频", insert: "audio" },
  { icon: LayoutTemplate, label: "时间线" },
  { icon: SquareUser, label: "主体" },
  { icon: Bot, label: "导演台", beta: true },
  { icon: Folder, label: "资产库" },
  { icon: Upload, label: "上传" },
];

export function JimengToolRail() {
  const addNodeAt = useJimengStore((s) => s.addNodeAt);
  const setAssetsOpen = useJimengStore((s) => s.setAssetsOpen);
  const addLocalUpload = useJimengStore((s) => s.addLocalUpload);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { screenToFlowPosition } = useReactFlow();

  // Batch 68: 按节点默认尺寸的一半回退，保证插入点为视口中心
  // (SOURCE_FACT 68-newnode-selected.png: 文本节点创建于视口中心)
  const HALF_SIZE: Record<
    "video" | "image" | "text" | "audio",
    { w: number; h: number }
  > = {
    video: { w: 284.5, h: 160 },
    image: { w: 240, h: 180 },
    text: { w: 164, h: 170 },
    audio: { w: 200, h: 60 },
  };

  const insertAtCenter = (kind: "video" | "image" | "text" | "audio") => {
    const el = document.querySelector(".jimeng-canvas");
    const position = screenToFlowPosition({
      x: el ? el.clientWidth / 2 : window.innerWidth / 2,
      y: el ? el.clientHeight / 2 : window.innerHeight / 2,
    });
    addNodeAt(kind, {
      x: position.x - HALF_SIZE[kind].w,
      y: position.y - HALF_SIZE[kind].h,
    });
  };

  return (
    <aside className="pointer-events-none absolute bottom-4 left-4 top-[72px] z-30 flex items-center">
      <div className="jimeng-chrome-pill group pointer-events-auto flex flex-col items-center gap-1 !rounded-2xl px-2 py-2.5">
        {RAIL_ITEMS.map(({ icon: Icon, label, beta, insert }) => (
          <button
            key={label}
            type="button"
            aria-label={label}
            onClick={() => {
              if (insert) insertAtCenter(insert);
              // Batch 72 (SOURCE_FACT): 资产库 打开模态
              if (label === "资产库") setAssetsOpen(true);
              // Batch 73 (SOURCE_FACT): 上传 打开多选文件选择器
              if (label === "上传") fileInputRef.current?.click();
            }}
            className="relative flex size-8 items-center justify-center rounded-lg text-white/85 hover:bg-white/[0.12]"
          >
            <Icon size={20} />
            {beta ? (
              <span className="absolute -top-0.5 left-1/2 text-[7px] font-semibold italic leading-none text-[#009EFA] [transform:translateX(-50%)_translateY(-2px)]">
                Beta
              </span>
            ) : null}
            {/* Batch 73 (SOURCE_FACT): 悬停左栏时图标右侧的标签飞出层 */}
            <span
              className="pointer-events-none absolute left-10 whitespace-nowrap text-[13px] leading-none text-white/85 opacity-0 transition-opacity duration-150 group-hover:opacity-100"
              data-rail-label={label}
            >
              {label}
            </span>
          </button>
        ))}
      </div>
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept="video/*,image/*"
        className="hidden"
        data-testid="rail-upload-input"
        onChange={(e) => {
          const files = Array.from(e.target.files ?? []);
          if (files.length) {
            const el = document.querySelector(".jimeng-canvas");
            const center = screenToFlowPosition({
              x: el ? el.clientWidth / 2 : window.innerWidth / 2,
              y: el ? el.clientHeight / 2 : window.innerHeight / 2,
            });
            files.forEach((file, i) => {
              addLocalUpload(file.name, {
                x: center.x - 284.5 + i * 40,
                y: center.y - 160 + i * 40,
              });
            });
          }
          e.target.value = "";
        }}
      />
    </aside>
  );
}
