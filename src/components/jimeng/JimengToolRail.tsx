"use client";

import {
  AudioLines,
  Box,
  Film,
  Folder,
  Image,
  SquarePlay,
  SquareUser,
  Type,
  Upload,
} from "lucide-react";
import { Fragment, useRef } from "react";
import type { ComponentType } from "react";
import { useReactFlow } from "@xyflow/react";

import { useJimengStore } from "@/store/jimengStore";

/**
 * 导演台图标 (Batch 808)。
 *
 * 源站这个图标**不在 DOM 里**——按钮内只有一个空的 `<span class="contents">`
 * （实测三个按钮都是），图形既不是 `<svg>` 也不是背景图/遮罩，所以只能靠
 * 像素辨认。7× 放大后（807-rail-sbs.png 的导演台段）看清是：
 *   上半 = 一个**等轴测立方体**（六边形外框 + 三条棱交于中心）
 *   顶左 = 一小段弧形箭头
 *   下半 = 绕着立方体底部的**双向弧形箭头**（旋转/环绕的暗示）
 *
 * 复刻此前用的是 lucide `Bot`（机器人头），与源站毫无相似之处。
 * 这里用 lucide `Box` 的立方体路径（等轴测，与源站中心图形一致），
 * 缩放后放在上方，下方补一段双向弧形箭头去对应源站的环绕箭头。
 * 20px 下笔画已接近 1px，弧形箭头是**近似**而非逐像素复刻——
 * 源站字形无法从 DOM 取得，弧段的曲率/箭头角度没有可量测的证据。
 */
function DirectorGlyph({ size = 20 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      {/* 立方体：lucide Box 的三条路径。变换要**先定目标中心**再缩放：
          `translate(12 10) scale(.68) translate(-12 -12)` 把立方体自身的
          中心 (12,12) 映射到 (12,10)，于是缩放后它落在 y 3.9~16.8，
          正好给下方的弧段（y 19~22）让出位置。写成 translate(12 1.6)
          会把立方体顶到 y=-4.5 直接被 viewBox 裁掉——第一版就踩了这个。 */}
      <g transform="translate(12 10) scale(0.68) translate(-12 -12)">
        <path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z" />
        <path d="m3.3 7 8.7 5 8.7-5" />
        <path d="M12 22V12" />
      </g>
      {/* 底部环绕箭头：左半弧 + 右半弧，两端各一个箭头 */}
      <path d="M4.6 20.1a7.4 3 0 0 0 14.8 0" />
      <path d="M4.6 20.1 3.2 18.4M4.6 20.1l2 .3" />
      <path d="M19.4 20.1l1.4-1.7M19.4 20.1l-2 .3" />
    </svg>
  );
}

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
  icon: ComponentType<{ size?: number }>;
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
  { icon: Film, label: "时间线", insert: "timeline" },
  { icon: SquareUser, label: "主体", insert: "subject" },
  { icon: DirectorGlyph, label: "导演台", beta: true, insert: "director" },
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
              {/* Batch 808 (SOURCE_FACT, 2026-10-03 像素实测):
                  源站 Beta 是一枚**胶囊**，不是纯文字。
                  逐像素定位：@[34,559] **23×14**，圆角 ≈3px
                  （y=559 那一行只占 19px，y=561 起满宽 23px），
                  底色是竖向渐变 rgb(29,46,57) → rgb(33,50,61)，
                  文字 #009EFA、**非斜体**（放大后源站的 B 是直的，
                  复刻此前写的 italic 明显右倾）。
                  落位：相对 40×40 按钮 left 18px / top -1px
                  （即压在图标 20×20 的右上角，图标 @[26,570]）。 */}
              {beta ? (
                <span
                  data-testid="rail-beta-badge"
                  className="absolute left-[18px] top-[-1px] flex h-[14px] w-[23px] items-center justify-center rounded-[3px] text-[7px] font-semibold leading-none text-[#009EFA] [background:linear-gradient(180deg,rgb(29,46,57),rgb(33,50,61))]"
                >
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
