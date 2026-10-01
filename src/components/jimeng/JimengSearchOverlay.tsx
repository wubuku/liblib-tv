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
export function JimengSearchOverlay({
  onClose,
}: {
  /** Batch 846 (SOURCE_FACT): 带上**关闭原因**。源站实测 Esc 关掉搜索面板后，
   *  焦点**回到触发器** `canvas-panel-launcher`（探针
   *  `jimeng_probe846_focustrap2.py`：Esc 前 `ASIDE/canvas-feature-panel`
   *  → Esc 后 `BUTTON/canvas-panel-launcher` aria-label=搜索）。
   *  而复刻此前 Esc 之后焦点掉到 **body** —— 键盘用户按完 Esc 就"丢失"了
   *  位置，下一次 Tab 从文档开头重新走。
   *  触发器**只在 Escape 关闭时**接回去：点外面关闭时用户的注意力在鼠标
   *  指着的地方，抢回触发器是错的。所以这里传原因，不传就分不出来。 */
  onClose: (reason: "escape" | "outside") => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose("escape");
    };
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose("outside");
    };
        // 捕获阶段（batch 794 实测踩坑）：JimengFlow 的全局 Escape 监听注册更早，
    // 会先触发同步重渲染；重渲染使本 effect 清理并重新注册监听，
    // removeEventListener 会把该 listener 标记为 removed，浏览器在**同一次
    // 事件派发中**跳过它 → 冒泡监听收不到 Escape，浮层关不掉。
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
      className="absolute right-0 top-[calc(100%+8px)] w-[242px] rounded-xl p-2"
      style={{ background: "rgb(38,38,38)" }}
      role="dialog"
      aria-label="搜索"
      data-testid="jimeng-search-overlay"
    >
      <input
        autoFocus
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="搜索节点..."
        data-testid="jimeng-search-input"
        className="w-full rounded-lg bg-white/[0.06] px-3 py-1 text-[13px] text-white placeholder:text-white/40 outline-none"
      />
      <p className="mt-6 mb-2 text-center text-[13px] text-white/35" data-testid="search-empty">
        暂无搜索结果
      </p>
    </div>
  );
}
