"use client";

import { useEffect, useRef } from "react";

import { useLayerFocus } from "@/hooks/useLayerFocus";

/**
 * 顶栏「节点 N」→ 节点摘要弹层 (Batch 794)。
 *
 * 证据 (SOURCE_FACT 2026-10-01 @1680×826):
 *   role=dialog，**水平以触发钮居中**（200 宽，中心 = 触发钮中心），
 *   纵向落在触发钮下沿 +3px。z-50。内含节点条目 + 底部「查看项目信息」。
 *
 * Batch 804 补测（画布节点数变化时复测，推翻 batch 795 的定高假设）:
 *   内部 padding **4px**、圆角 **12px**、条目行高 **36px**、条目间 **4px**、
 *   分隔块 **4px**（内含 1px 线，上下各留 4px）、底部按钮 **36px**。
 *   高度是**内容驱动**的：
 *     H = 4 + (36N + 4(N-1)) + 4 + 4 + 4 + 36 + 4 = **40N + 52**
 *   实测吻合：N=1 → 92px（batch 795 读到的值，当时画布只有 1 个节点）、
 *   N=2 → 132px。故**不能**把高度写死 92px —— 节点一多就会失配。
 */
export function JimengNodeSummaryPopover({
  nodeLabels,
  onClose,
  onOpenProjectInfo,
  onSelectNode,
}: {
  nodeLabels: string[];
  onClose: () => void;
  onOpenProjectInfo?: () => void;
  onSelectNode?: (label: string) => void;
}) {
  const ref = useRef<HTMLDivElement>(null);

  // Batch 811 SOURCE_FACT: 源站这一层是**唯一**把焦点管对了的浮层 ——
  // 打开焦点进浮层、Tab 焦点陷阱（10/10 不逃出）、关闭归还触发器。
  // 分享/更多/项目面板源站并没有陷阱，别顺手给它们也加上（那是擅自改进）。
  useLayerFocus(ref, true, { trap: true, returnTo: true });

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    };
    // 捕获阶段：工作区有全局 Escape 处理器会在冒泡阶段 stopPropagation，
    // 冒泡监听收不到事件，浮层就关不掉。
    window.addEventListener("keydown", onKey, true);
    window.addEventListener("mousedown", onDown, true);
    return () => {
      window.removeEventListener("keydown", onKey, true);
      window.removeEventListener("mousedown", onDown, true);
    };
  }, [onClose]);

  return (
    <div
      ref={ref}
      role="dialog"
      aria-label="节点摘要"
      data-testid="topbar-node-summary"
      // SOURCE_FACT: 水平以触发钮居中，纵向 +3px；高度内容驱动 H=40N+52
      className="absolute left-1/2 top-[31px] z-50 flex w-[200px] -translate-x-1/2 flex-col overflow-hidden rounded-xl p-1"
      style={{ background: "rgb(38,38,38)" }}
    >
      {/* 条目区：行高 36px、行间 4px（SOURCE_FACT batch 804） */}
      <div className="flex flex-col gap-1 overflow-y-auto">
        {nodeLabels.map((label) => (
          <button
            key={label}
            type="button"
            onClick={() => {
              onSelectNode?.(label);
              onClose();
            }}
            className="flex h-9 w-full items-center rounded-md px-2 text-left text-[13px] text-white/80 hover:bg-white/10"
          >
            {label}
          </button>
        ))}
      </div>
      {/* 分隔：4px 块内含 1px 线，上下各 4px（SOURCE_FACT batch 804） */}
      <div className="my-1 flex h-1 items-center">
        <div className="h-px w-full bg-white/[0.06]" />
      </div>
      <button
        type="button"
        onClick={() => {
          onOpenProjectInfo?.();
          onClose();
        }}
        className="flex h-9 w-full items-center rounded-md px-2 text-left text-[13px] text-white/55 hover:bg-white/10"
      >
        查看项目信息
      </button>
    </div>
  );
}
