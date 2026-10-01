"use client";

import { useEffect, useRef } from "react";

/**
 * 顶栏「节点 N」→ 节点摘要弹层 (Batch 794)。
 *
 * 证据 (SOURCE_FACT 2026-10-01 @1680×826): role=dialog 200×92 @[69,47]，
 * **水平以触发钮居中** (69+100=169 = 节点钮 156+28/2)，纵向落在触发钮
 * 下沿 +3px (44→47)。z-50。内含节点条目（实测「视频 1」）+ 底部
 * 「查看项目信息」入口。文案逐字。
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
      // SOURCE_FACT: 水平以触发钮居中，纵向 +3px
      className="absolute left-1/2 top-[31px] z-50 flex h-[92px] w-[200px] -translate-x-1/2 flex-col overflow-hidden rounded-lg p-1"
      style={{ background: "rgb(38,38,38)" }}
    >
      <div className="min-h-0 flex-1 overflow-y-auto">
        {nodeLabels.map((label) => (
          <button
            key={label}
            type="button"
            onClick={() => {
              onSelectNode?.(label);
              onClose();
            }}
            className="flex h-7 w-full items-center rounded px-2 text-left text-[12px] text-white/80 hover:bg-white/10"
          >
            {label}
          </button>
        ))}
      </div>
      <div className="my-1 h-px bg-white/[0.06]" />
      <button
        type="button"
        onClick={() => {
          onOpenProjectInfo?.();
          onClose();
        }}
        className="flex h-8 w-full items-center rounded px-2 text-left text-[12px] text-white/55 hover:bg-white/10"
      >
        查看项目信息
      </button>
    </div>
  );
}
