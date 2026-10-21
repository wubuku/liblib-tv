"use client";

// Batch 832（源站 2026-10-21 活体实测 + 源码）：导演台 rail「添加机位」打开的
// **机位预设面板**（源站左侧资源栏的一个视图，不是浮层）。
//
// ★ 源站实测（raw/source-832-camera-presets.json，由 probes/camera832b.py 活体采、
//   probes/mk832raw.py 程序化整理）：
//   面板本体   232×1028 @(48,52)   `flex w-[232px] min-w-0 flex-col bg-[#171717]`
//   标题条     232×48  @(48,52)    文案「添加机位」12px/leading-5/white/90
//   网格       232×980  @(48,100)   `grid … auto-rows-[72px] grid-cols-2
//                                        content-start gap-2 overflow-y-auto px-2 pb-3`
//              gridTemplateColumns = **104px 104px**（2 列）
//   15 枚预设   每枚 104×72 @(56,100)/(168,100) …，列步长 112、行步长 80
//              盒内：20×20 的 SVG 图标 @(98,115)（viewBox 0 0 16 16，iconify libtv）
//                    + 文字 span（12px，`max-w-full truncate px-1`）
//   ★ 15 枚**共用同一枚图标**（path 逐字相同）⟹ 源站那枚图标是「机位」的通用符号
//   ★ 第 0 枚「当前视角」的边框**更亮**：`border-white/85`（其余 `border-white/10`）
//
// ★ 源站代码（chunk 0fmehki05gkzw.js.js 的 rail 组件）：
//   "camera"===z?(0,i.jsxs)(i.Fragment,{children:[
//     (0,i.jsx)(aO,{children:D("canvas:directorAddCamera")}),
//     (0,i.jsxs)("div",{className:"grid min-h-0 flex-1 auto-rows-[72px] grid-cols-2
//        content-start gap-2 overflow-y-auto px-2 pb-3",children:[
//        (0,i.jsxs)("button",{type:"button",className:"hover:bg-white/8 flex h-[72px]
//           flex-col items-center justify-center gap-1 rounded-xl border border-white/85
//           text-[12px] text-white/90 transition-colors",onClick:A,children:[
//           (0,i.jsx)(aL,{}),(0,i.jsx)("span",{children:D("canvas:directorCurrentViewAngle")})]}),
//        eo.map(e=>(0,i.jsxs)("button",{type:"button",className:"hover:bg-white/8 flex h-[72px]
//           flex-col items-center justify-center gap-1 rounded-xl border border-white/10
//           text-[12px] text-white/90 transition-colors",onClick:()=>w(tA(e)),children:[
//           (0,i.jsx)(aL,{}),(0,i.jsx)("span",{className:"max-w-full truncate px-1", …})]}))]})}):null
//
// ★ ★ 为什么尺寸走 inline style（不是 Tailwind 任意值类）：
//   4317 的 Tailwind 扫描是**冻结**的（batch 824 实测）⟹ 新增任意值类在 dev 上
//   不生成、在 prod 上照常生成 ⟹ 同一个组件在 dev 上「没样式」⟹ 必须走 inline style。
//   （`grid-cols-2` / `gap-2` / `px-2` / `pb-3` / `h-[72px]` 等**仓库里已存在**的类
//   可以直接用；`auto-rows-[72px]` 与 `w-[232px]` 同理已存在 ⟹ 见文件末尾的实测说明。）

import { useEffect, useRef } from "react";

/** 源站那枚「机位」图标（15 枚共用）——path 原文取自活体 DOM */
const SOURCE_CAMERA_PATH =
  "M8.52 1.23q.2.02.34.18l1.3 1.56h1.5a1.7 1.7 0 0 1 1.7 1.7v6.41a1.7 1.7 0 0 1-1.7 1.7H2.34a1.7 1.7 0 0 1-1.69-1.7V4.67a1.7 1.7 0 0 1 1.7-1.7h1.5l1.3-1.56.04-.04q.16-.15.36-.15h2.98M4.5 3.82a.5.5 0 0 1-.4.2H2.32a.64.64 0 0 0-.64.64v6.41a.64.64 0 0 0 .64.64h9.34a.64.64 0 0 0 .64-.64v-6.4a.64.64 0 0 0-.64-.64H9.92a.5.5 0 0 1-.4-.2l-1.3-1.55H5.78zM7 5.32a2.28 2.28 0 1 1 0 4.55A2.28 2.28 0 0 1 7 5.3m0 1.05A1.22 1.22 0 1 0 7 8.8a1.22 1.22 0 0 0 0-2.45";

/**
 * 15 枚机位预设。
 *
 * ★ 标签与顺序**逐字取自源站活体读数**（raw/source-832-camera-presets.json 的
 *   `预设[].label`）⟹ 不手打 ⟹ 门禁按 raw 核验。
 * ★ `current: true` 的是源站第 0 枚「当前视角」⟹ 它的边框更亮（`border-white/85`）。
 * ★ `semantics` 字段留空的地方见文件末尾「★ 不声称」——**还没逐枚实测**的，
 *   本批**不编**。
 */
export const DIRECTOR_CAMERA_PRESET_LABELS = [
  "当前视角",
  "正面中景",
  "正面特写",
  "正面全景",
  "侧面跟拍",
  "侧面近景",
  "背面中景",
  "俯拍全景",
  "45° 俯拍",
  "低角度仰拍",
  "低角度广角",
  "过肩镜头",
  "过肩镜头（右）",
  "鸟瞰",
  "荷兰角",
] as const;

export type DirectorCameraPresetLabel =
  (typeof DIRECTOR_CAMERA_PRESET_LABELS)[number];

function CameraGlyph() {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 16 16"
      fill="none"
      aria-hidden="true"
      className="size-5 shrink-0"
      data-director-camera-preset-glyph
    >
      <path
        d={SOURCE_CAMERA_PATH}
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.2"
      />
    </svg>
  );
}

export function DirectorCameraPresetPanel({
  onPick,
  onClose,
}: {
  /** 点了某枚预设（传标签） */
  onPick?: (label: DirectorCameraPresetLabel) => void;
  /** 源站点完预设后**面板不关**（实测：点「正面中景」面板仍在）⟹ 默认不关 */
  onClose?: () => void;
}) {
  const firstRef = useRef<HTMLButtonElement | null>(null);

  // ★ 面板打开后焦点落在第 0 枚上（源站是按钮列表；clone 至少别把焦点丢到 body）
  useEffect(() => {
    firstRef.current?.focus();
  }, []);

  return (
    <section
      data-director-camera-preset-panel
      aria-label="添加机位"
      // 源站：`flex w-[232px] min-w-0 flex-col bg-[#171717]`
      // ★ `h-full`：源站面板**通到视口底**（实测 232×1028 @(48,52)）⟹
      //   左栏 aside 是 1028 高，而面板必须撑满它。
      //   ★ 而 `min-h-0` **不能**要：它会把 flex 子项的高度压成内容高
      //   （实测去掉 `h-full` 时面板只有 692 高 ⟹ 底部空出 336px）。
      className="flex h-full min-w-0 flex-col bg-[#171717]"
      style={{ width: 232 }}
    >
      {/* 标题条：源站 `flex h-12 shrink-0 items-center px-3 text-[12px]
          leading-5 text-white/90` ⟹ 232×48 @(48,52) */}
      <div className="flex h-12 shrink-0 items-center px-3 text-[12px] leading-5 text-white/90">
        添加机位
      </div>

      {/* 网格：源站 `grid min-h-0 flex-1 auto-rows-[72px] grid-cols-2
          content-start gap-2 overflow-y-auto px-2 pb-3`
          ⟹ 232×980 @(48,100)、2 列 104px、列步长 112、行步长 80
          ★ `min-h-0` 要保留（源站原文有）：它让 grid 能滚动而不撑破父级。 */}
      <div
        className="grid min-h-0 flex-1 content-start gap-2 overflow-y-auto px-2 pb-3"
        style={{ gridTemplateColumns: "104px 104px", gridAutoRows: "72px" }}
      >
        {DIRECTOR_CAMERA_PRESET_LABELS.map((label, index) => (
          <button
            key={label}
            ref={index === 0 ? firstRef : undefined}
            type="button"
            data-director-camera-preset={label}
            onClick={() => {
              onPick?.(label);
              onClose?.();
            }}
            // 源站逐字：`hover:bg-white/8 flex h-[72px] flex-col items-center
            // justify-center gap-1 rounded-xl border text-[12px] text-white/90
            // transition-colors`；★ 第 0 枚的边框更亮（border-white/85），
            // 其余是 border-white/10。
            className={
              "flex h-[72px] flex-col items-center justify-center gap-1 rounded-xl " +
              "border text-[12px] text-white/90 transition-colors hover:bg-white/8 " +
              (index === 0 ? "border-white/85" : "border-white/10")
            }
          >
            <CameraGlyph />
            <span className="max-w-full truncate px-1">{label}</span>
          </button>
        ))}
      </div>
    </section>
  );
}
