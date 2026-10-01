"use client";

import { useEffect, useRef } from "react";

/**
 * 顶栏「分享」→ 分享画布面板 (Batch 794)。
 *
 * 证据 (SOURCE_FACT 2026-10-01 @1680×826): 400×251 @[1268,56]，右缘与顶栏
 * 右内边距齐平 (1680-12-400=1268)，纵向 +2px 落在顶栏下沿。面板纵向 flex：
 *   分享画布 → 画布链接 → 复制链接 → 权限行「仅自己可访问」+ 说明
 *   → 「创建团队，与成员在画布实时协作」+ 创建团队
 * 文案逐字取自源站 innerText；链接里的 project id 为 mock。
 */
export function JimengSharePanel({
  canvasUrl,
  onClose,
  onCopy,
}: {
  canvasUrl: string;
  onClose: () => void;
  onCopy?: () => void;
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
      aria-label="分享画布"
      data-testid="topbar-share-panel"
      className="absolute right-0 top-[46px] z-[120] flex h-[251px] w-[400px] flex-col overflow-hidden rounded-xl p-4"
      style={{ background: "rgb(38,38,38)" }}
    >
      <p className="text-[14px] font-medium text-white/90">分享画布</p>
      <p className="mt-2 break-all text-[12px] leading-[18px] text-white/45">
        {canvasUrl}
      </p>
      <button
        type="button"
        onClick={onCopy}
        className="mt-3 h-8 w-fit rounded-lg bg-white/10 px-3 text-[13px] text-white/90 hover:bg-white/[0.16]"
      >
        复制链接
      </button>
      <p className="mt-4 text-[13px] text-white/80">仅自己可访问</p>
      <p className="mt-1 text-[12px] leading-[18px] text-white/45">
        只有你可以通过此链接访问画布
      </p>
      <p className="mt-4 text-[13px] text-white/80">
        创建团队，与成员在画布实时协作
      </p>
      <button
        type="button"
        className="mt-2 h-8 w-fit rounded-lg border border-white/10 px-3 text-[13px] text-white/90 hover:bg-white/10"
      >
        创建团队
      </button>
    </div>
  );
}
