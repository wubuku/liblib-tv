"use client";

import {
  ArrowUpRight,
  AtSign,
  Eraser,
  MapPin,
  Paperclip,
  PenLine,
  Quote,
  Redo2,
  Sparkle,
  Square,
  Type,
  Undo2,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { VipDiamond } from "@/components/jimeng/icons";

/**
 * 视频编辑（局部编辑）模式 (Batch 6/215；批 373 源站再采样保真修正)。
 *
 * 证据 (SOURCE_FACT 373-video-edit.png / 373b-edit-anatomy.json):
 * 点击工具条「视频编辑」后进入画布内联编辑模式——画布自动 zoom 176%
 * 聚焦节点（世界尺寸不变），标题行保持可见，工具条隐藏；节点下方出现
 * 1) 编辑工具药丸: [矩形][画笔][箭头][文字][橡皮擦]｜[标记]｜[撤销][重做]
 *    8 个 32×32 图标钮（aria 实测），分隔线在 橡皮擦 后与 标记 后；
 * 2) 编辑提示条: 上传参考内容(36×36) + 占位「描述你如何调整视频」+
 *    引用参考(32×32) + @ + 「✦ 144 分/次」价格签（蓝钻，动态值）+
 *    蓝色 ✦ 装饰 + 生成钮(36×36，空文案禁用)。
 * Escape 退出、无历史入栈（373b: prompt_gone + 0 undo）。
 * 卡片控件简化（仅 ⏸ 0:04/0:06 药丸 + 底部进度条）为批 373 采样所见，
 * clone 暂保留标准卡控件 (CLONE_DECISION，待后续批次对齐)。
 */
const EDIT_TOOLS: { icon: LucideIcon; label: string }[] = [
  { icon: Square, label: "矩形" },
  { icon: PenLine, label: "画笔" },
  { icon: ArrowUpRight, label: "箭头" },
  { icon: Type, label: "文字" },
  { icon: Eraser, label: "橡皮擦" },
  { icon: MapPin, label: "标记" },
  { icon: Undo2, label: "撤销" },
  { icon: Redo2, label: "重做" },
];

export function JimengVideoEditMode({ onSubmit }: { onSubmit: () => void }) {
  return (
    <div className="absolute top-full left-1/2 z-20 mt-3 flex -translate-x-1/2 flex-col items-center gap-3">
      {/* 编辑工具药丸 (批 373: 双分隔线——橡皮擦 后、标记 后) */}
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
            {i === 4 || i === 5 ? (
              <span className="mx-1 h-4 w-px bg-white/10" />
            ) : null}
          </span>
        ))}
      </div>

      {/* 编辑提示条 (批 373: 上传参考内容 / 引用参考 / ✦ 144 分/次) */}
      <form
        className="flex h-[52px] w-[700px] items-center gap-2.5 rounded-2xl bg-[#202020] px-3 shadow-[0_4px_16px_rgba(0,0,0,0.32)]"
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit();
        }}
      >
        <button
          type="button"
          aria-label="上传参考内容"
          className="flex size-9 shrink-0 items-center justify-center rounded-lg text-white/80 hover:bg-white/[0.08]"
        >
          <Paperclip size={15} />
        </button>
        <span className="flex-1 text-[13px] text-white/35">
          描述你如何调整视频
        </span>
        <button
          type="button"
          aria-label="引用参考"
          className="flex size-8 shrink-0 items-center justify-center rounded-lg text-white/80 hover:bg-white/[0.08]"
        >
          <Quote size={14} />
        </button>
        <button
          type="button"
          aria-label="提及主体"
          className="flex size-8 shrink-0 items-center justify-center rounded-lg text-white/80 hover:bg-white/[0.08]"
        >
          <AtSign size={15} />
        </button>
        <span className="inline-flex shrink-0 items-center gap-1 text-[12px] font-medium text-white/80">
          <VipDiamond size={12} />
          144 <span className="text-white/50">分/次</span>
        </span>
        <Sparkle size={14} className="shrink-0 fill-[#2E6BE6] text-[#2E6BE6]" />
        <button
          type="submit"
          aria-label="生成"
          disabled
          className="flex size-9 shrink-0 items-center justify-center rounded-full bg-white/[0.16] text-white/25"
        >
          <ArrowUpRight size={15} className="-rotate-45" />
        </button>
      </form>
    </div>
  );
}
