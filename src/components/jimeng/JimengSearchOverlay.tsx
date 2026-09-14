"use client";

import { useEffect, useRef, useState } from "react";

/**
 * 顶栏搜索覆盖层 (Batch 96)。
 *
 * SOURCE_FACT: 源站顶栏 搜索 (canvas-search) 存在 (96 顶栏 dump)，但其
 * 覆盖层内容从未被捕获 (33-search-overlay.png 实为 生成历史 面板)。
 * CLONE_DECISION: 复刻为最小搜索面板 — 输入框 + 「暂无搜索结果」空态，
 * 380px rgb(38,38,38) 与生成历史面板同族；点击外部/Escape 关闭。
 */
export function JimengSearchOverlay({ onClose }: { onClose: () => void }) {
  const ref = useRef<HTMLDivElement>(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    };
    window.addEventListener("keydown", onKey);
    window.addEventListener("mousedown", onDown, true);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("mousedown", onDown, true);
    };
  }, [onClose]);

  return (
    <div
      ref={ref}
      className="absolute right-0 top-[calc(100%+8px)] w-[380px] rounded-xl p-4"
      style={{ background: "rgb(38,38,38)" }}
      role="dialog"
      aria-label="搜索"
      data-testid="jimeng-search-overlay"
    >
      <input
        autoFocus
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="搜索"
        data-testid="jimeng-search-input"
        className="w-full rounded-lg bg-white/[0.06] px-3 py-2 text-[13px] text-white placeholder:text-white/40 outline-none"
      />
      <p className="mt-6 mb-2 text-center text-[13px] text-white/35" data-testid="search-empty">
        暂无搜索结果
      </p>
    </div>
  );
}
