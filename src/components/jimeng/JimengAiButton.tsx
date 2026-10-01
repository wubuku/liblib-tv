"use client";

import { Waves } from "lucide-react";

import { useJimengStore } from "@/store/jimengStore";

/**
 * 右下角「与 AI 对话」触发钮 — Batch 797 SOURCE_FACT 2026-10-01 实测。
 *
 * 结构是**两层**，别只量内层按钮（此前两次都栽在这）：
 *   定位层  `absolute bottom-3 right-3 flex flex-col items-end`（12px 内缩）
 *   药丸层  @[1548,778] **120×36**，bg rgba(39,39,39,0.72)、radius **20px**、
 *           backdrop-filter **blur(40px)**
 *   按钮层  @[1549,779] **118×34**，自身**透明**、radius 20px、13px 文字
 * 内层按钮比药丸四周各内缩 1px，所以「按钮距右缘 13px」是 12 + 1 的结果，
 * 定位层仍是 12px —— 不要据内层矩形去改 bottom/right。
 *
 * 渐变高光叠加仍是 CLONE_DECISION 近似（源站渐变值提取时截断）。
 * 点击展开 AI 对话抽屉 (Batch 12)。
 */
export function JimengAiButton() {
  const setAiDrawerOpen = useJimengStore((s) => s.setAiDrawerOpen);

  return (
    <div className="absolute bottom-3 right-3 z-30 flex flex-col items-end">
      <div
        className="relative inline-flex h-9 w-[120px] items-center justify-center overflow-hidden rounded-[20px] bg-[rgba(39,39,39,0.72)] backdrop-blur-[40px]"
        data-testid="ai-trigger-pill"
      >
        <span
          aria-hidden
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              "linear-gradient(180deg, rgba(138,196,220,0.18) 0%, rgba(138,196,220,0.02) 100%)",
          }}
        />
        <button
          type="button"
          aria-label="与 AI 对话"
          // Batch 816 SOURCE_FACT: testid `canvas-sidecar-launcher`
          data-testid="canvas-sidecar-launcher"
          onClick={() => setAiDrawerOpen(true)}
          className="relative z-[1] inline-flex h-[34px] w-[118px] items-center justify-center gap-1 whitespace-nowrap rounded-[20px] text-[13px] font-medium text-white"
        >
          <Waves size={16} className="text-[#7FD8C9]" />
          与 AI 对话
        </button>
      </div>
    </div>
  );
}
