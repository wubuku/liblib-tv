"use client";

import {
  ArrowUpRight,
  AtSign,
  Eraser,
  Lasso,
  MapPin,
  Pencil,
  Redo2,
  Square,
  Type,
  Undo2,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { VipDiamond } from "@/components/jimeng/icons";

/**
 * 视频编辑（局部编辑）模式 (Batch 6)。
 *
 * 证据 (SOURCE_FACT, docs/design-references/jimeng/jimeng-clone-batch6-*.png):
 * 点击工具条「视频编辑」后: 节点标题行与工具条隐藏，节点下方出现
 * 1) 编辑工具药丸: 框选/套索/箭头/文字/橡皮/定位/撤销/重做 8 个 16px 图标钮；
 * 2) 编辑提示条: 铅笔图标 + 占位「描述你如何调整视频」+ @ + ✦120/260 + 禁用发送钮。
 * 源站同时放大节点 (zoom 145%) — 复刻暂不自动缩放 (CLONE_DECISION)。
 */
const EDIT_TOOLS: { icon: LucideIcon; label: string }[] = [
  { icon: Square, label: "框选" },
  { icon: Lasso, label: "套索" },
  { icon: ArrowUpRight, label: "箭头" },
  { icon: Type, label: "文字" },
  { icon: Eraser, label: "橡皮擦" },
  { icon: MapPin, label: "定位" },
  { icon: Undo2, label: "撤销" },
  { icon: Redo2, label: "重做" },
];

export function JimengVideoEditMode({ onSubmit }: { onSubmit: () => void }) {
  return (
    <div className="absolute top-full left-1/2 z-20 mt-3 flex -translate-x-1/2 flex-col items-center gap-3">
      {/* 编辑工具药丸 */}
      <div className="jimeng-chrome-pill flex h-10 items-center gap-0.5 px-1.5">
        {EDIT_TOOLS.map(({ icon: Icon, label }, i) => (
          <span key={label} className="flex items-center">
            <button
              type="button"
              aria-label={label}
              className="flex size-8 items-center justify-center rounded-lg text-white/85 hover:bg-white/10"
            >
              <Icon size={16} />
            </button>
            {i === 5 ? <span className="mx-1 h-4 w-px bg-white/10" /> : null}
          </span>
        ))}
      </div>

      {/* 编辑提示条 */}
      <form
        className="flex h-[52px] w-[520px] items-center gap-2.5 rounded-2xl bg-[#202020] px-4 shadow-[0_4px_16px_rgba(0,0,0,0.32)]"
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit();
        }}
      >
        <Pencil size={15} className="shrink-0 text-white/60" />
        <span className="flex-1 text-[13px] text-white/35">
          描述你如何调整视频
        </span>
        <button
          type="button"
          aria-label="提及主体"
          className="flex size-7 items-center justify-center rounded-lg text-white/80 hover:bg-white/[0.08]"
        >
          <AtSign size={15} />
        </button>
        <span className="inline-flex items-center gap-1 text-[12px] font-medium text-white/70">
          <VipDiamond size={12} />
          120<span className="text-white/40">/260</span>
          <VipDiamond size={12} />
        </span>
        <button
          type="submit"
          aria-label="生成"
          disabled
          className="flex size-8 items-center justify-center rounded-full bg-white/[0.16] text-white/25"
        />
      </form>
    </div>
  );
}
