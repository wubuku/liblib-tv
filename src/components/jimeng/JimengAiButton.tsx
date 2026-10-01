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
 *
 * ── Batch 835 查过「它是不是一枚死按钮」：不是，**而且不该改成开关** ──
 * 本地死按钮普查报它 DEAD，理由是复刻自己写的（「单独跑时 testid 集合会变」
 * +「前一轮把抽屉打开了，抽屉正好盖住按钮」）。批 826 照抄批 820 的措辞、
 * 批 827 撤回过一次 —— **照抄自己写的豁免同样不算证据**，所以本批去源站
 * 量了四刀（`scripts/jimeng_835_*.py`，证据在
 * `docs/research/jimeng-canvas-batch835-2026-10-04/`）：
 *
 *   关闭态  button 118×34  药丸 120×36  `aria-expanded="false"`  面板关着
 *   点一下  面板开，同一枚按钮仍在 DOM，`aria-expanded="true"`
 *           但它缩成 **59×17**、药丸缩成 **60×18**（正好一半）并挪到
 *           面板右下角 —— 0.6/1.2/2.5/5s 四采样一致，不是过渡中态
 *   再点    面板关，回 118×34 / `aria-expanded="false"`
 *
 * 结论：**源站确实是开关**，但它的「开态药丸」是个退化的残影 —— 60×18 的
 * 20px 圆角药丸，截图（`source-panel-open.png`）里在面板打开时**根本看不见**。
 * 复刻则在面板打开时**卸载**这枚钮（`JimengWorkspace.tsx` 的
 * `{aiDrawerOpen ? null : <JimengAiButton />}`），面板的关闭路径是它自己的
 * 「收起」钮。两者对用户**不可区分**，而复刻这样还少一个压在面板底缘上的
 * 隐形热区。所以这里保持 `setAiDrawerOpen(true)`，**不**改成 toggle。
 * ⚠ 更正一笔我自己写错的东西：以为那枚 59×17 会「压在发送钮上」——
 *   不对。源站发送钮 @[1446,884,32,32]（y 884..916），残影 @[1440,920,60,18]
 *   （y 920..938），中间**差 4px**，不重叠。反推出来的结论也得连同前提复核。
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
