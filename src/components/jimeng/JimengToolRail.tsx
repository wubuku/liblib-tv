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
import { Fragment, useRef } from "react";
import { useReactFlow } from "@xyflow/react";

import { useJimengStore } from "@/store/jimengStore";

/**
 * 左侧插入工具栏 — aside 绝对定位、**在 y=56 以下区域垂直居中**。
 *
 * Batch 796 (SOURCE_FACT 2026-10-01 登录态实测，1680×826 + 1280×720 +
 * 1440×900 + 1680×1000 四视口交叉验证)：
 *   外壳  @[12,242] 48×398  padding 4px  gap 2px  radius 12px
 *         bg rgb(32,32,32) **不透明**、**无 backdrop blur**
 *         （与顶部 chrome 药丸 rgba(32,32,34,.8)+blur(40px) 是两套，别混用）
 *   按钮  40×40  radius 8px  图标 20×20
 *   纵向  246 / 288 / 330 / 372 / 414 / 456 / 498 → 分隔条 → 554 / 596
 *         即常规步距 42px，导演台→资产库 56px（多出的 14px = 12px 分隔条 + 2×2px gap）
 *   居中  rail 高恒为 390px，中心 = (56 + 视口高)/2，即 railTop = 56 + (H-446)/2。
 *         四视口实测 railTop = 246/193/283/333，与该式逐一吻合 —— 说明源站是
 *         **推导**而非写死，本组件沿用同一居中模型，只在 top-[72px] bottom-4
 *         （中心同为 (H+56)/2）上改内部尺寸即可，无需改成固定 y。
 *   hover 按钮底色**不变**（源站 class 明确 hover:bg-transparent，实测 hover 前后
 *         computed backgroundColor 均为 rgba(0,0,0,0)）。此前本文件注释写的
 *         「hover 高亮 rgba(255,255,255,0.12)」是台账错误，batch 796 已订正。
 */
const RAIL_ITEMS: {
  icon: LucideIcon;
  label: string;
  beta?: boolean;
  separatorBefore?: boolean;
  insert?: "video" | "image" | "text" | "audio" | "timeline" | "subject" | "director";
}[] = [
  // Batch 68 (SOURCE_FACT): 标签对齐源站 aria-label 提取
  // (68-rail.json: 文本/图片/视频/音频/时间线/主体/导演台/资产库/上传)
  { icon: Type, label: "文本", insert: "text" },
  { icon: Image, label: "图片", insert: "image" },
  { icon: SquarePlay, label: "视频", insert: "video" },
  { icon: AudioLines, label: "音频", insert: "audio" },
  // Batch 805 SOURCE_FACT: 时间线/主体/导演台 点下去 = 在画布中心插入对应节点，
  // 不是打开浮层（源站落点 rf__node-*，在 .react-flow__viewport 内，节点计数 +1）
  { icon: LayoutTemplate, label: "时间线", insert: "timeline" },
  { icon: SquareUser, label: "主体", insert: "subject" },
  { icon: Bot, label: "导演台", beta: true, insert: "director" },
  // Batch 796 (SOURCE_FACT): 资产库 之前有一条 20×12 分隔条
  { icon: Folder, label: "资产库", separatorBefore: true },
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
    "video" | "image" | "text" | "audio" | "timeline" | "subject" | "director",
    { w: number; h: number }
  > = {
    video: { w: 284.5, h: 160 },
    image: { w: 240, h: 180 },
    text: { w: 164, h: 170 },
    audio: { w: 200, h: 60 },
    // Batch 805 SOURCE_FACT: 三种新节点按源站实测尺寸对半回退
    timeline: { w: 603, h: 106 },
    subject: { w: 176, h: 176 },
    director: { w: 160, h: 160 },
  };

  const insertAtCenter = (
    kind: "video" | "image" | "text" | "audio" | "timeline" | "subject" | "director",
  ) => {
    const el = document.querySelector(".jimeng-canvas");
    const position = screenToFlowPosition({
      x: el ? el.clientWidth / 2 : window.innerWidth / 2,
      y: el ? el.clientHeight / 2 : window.innerHeight / 2,
    });
    // Batch 807 (CLONE_DECISION，有实测依据): 节点落在视口中心
    // (SOURCE_FACT 68-newnode-selected.png)，但**当那个落点已经被占住**时
    // 逐个级联错位。不这么做的话，连点两次时间线（或先后点时间线+主体+
    // 导演台）会得到几个完全重合的节点，后一个把前一个的
    // 「添加素材到时间线」整个盖住 —— 按钮在 DOM 里、用户点不到。
    // 源站也不是精确重合：截图里 主体 1/2/3 落点互有偏移
    // (684,237)/(784,317)/(700,230)，故取级联步进。步进取 (40,32)
    // 世界像素：小于这个量级，320px 的导演台节点会把它下面的时间线节点
    // 盖得看不出错开，用户既看不见也点不到。
    const target = {
      x: position.x - HALF_SIZE[kind].w,
      y: position.y - HALF_SIZE[kind].h,
    };
    const occupied = useJimengStore.getState().nodes.filter(
      (n) => Math.abs(n.position.x - target.x) < 24 && Math.abs(n.position.y - target.y) < 24,
    ).length;
    addNodeAt(kind, {
      x: target.x + occupied * 40,
      y: target.y + occupied * 32,
    });
  };

  return (
    <aside className="pointer-events-none absolute bottom-4 left-3 top-[72px] z-30 flex items-center">
      <div
        className="jimeng-tool-rail group pointer-events-auto flex w-12 flex-col items-center gap-0.5 p-1"
        data-testid="tool-rail"
      >
        {RAIL_ITEMS.map(({ icon: Icon, label, beta, insert, separatorBefore }) => (
          <Fragment key={label}>
            {/* Batch 796 (SOURCE_FACT): 导演台与资产库之间的 20×12 分隔条 */}
            {separatorBefore ? (
              <div className="jimeng-tool-rail-separator" data-testid="tool-rail-separator" />
            ) : null}
            <button
              type="button"
              aria-label={label}
              onClick={() => {
                if (insert) insertAtCenter(insert);
                // Batch 72 (SOURCE_FACT): 资产库 打开模态
                if (label === "资产库") setAssetsOpen(true);
                // Batch 73 (SOURCE_FACT): 上传 打开多选文件选择器
                if (label === "上传") fileInputRef.current?.click();
              }}
              // Batch 796 (SOURCE_FACT): 40×40 r8；hover **不**改底色
              className="relative flex size-10 items-center justify-center rounded-lg text-white/85"
            >
              <Icon size={20} />
              {beta ? (
                <span className="absolute -top-0.5 left-1/2 text-[7px] font-semibold italic leading-none text-[#009EFA] [transform:translateX(-50%)_translateY(-2px)]">
                  Beta
                </span>
              ) : null}
              {/* Batch 73 (SOURCE_FACT): 悬停左栏时图标右侧的标签飞出层 */}
              <span
                className="pointer-events-none absolute left-12 whitespace-nowrap text-[13px] leading-none text-white/85 opacity-0 transition-opacity duration-150 group-hover:opacity-100"
                data-rail-label={label}
              >
                {label}
              </span>
            </button>
          </Fragment>
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
