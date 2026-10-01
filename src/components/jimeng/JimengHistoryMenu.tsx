"use client";

import { useEffect, useRef, useState } from "react";

/**
 * 顶栏 ⌕ 按钮 → 「生成历史」下拉 (Batch 13)。
 *
 * 证据 (SOURCE_FACT): 点击后搜索图标下方弹出 ≈380px 面板 rgb(38,38,38):
 * 标题「生成历史」+ tabs 全部(选中下划线)/图片/视频/音频 + 空态「暂无生成历史」。
 */
const TABS = ["全部", "图片", "视频", "音频"] as const;

export function JimengHistoryMenu({ onClose }: { onClose: () => void }) {
  const ref = useRef<HTMLDivElement>(null);
  const [tab, setTab] = useState<(typeof TABS)[number]>("全部");

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
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
      className="absolute right-0 top-[calc(100%+8px)] w-[380px] rounded-xl p-4"
      style={{ background: "rgb(38,38,38)" }}
      role="dialog"
      aria-label="生成历史"
    >
      <p className="text-[14px] text-white/90">生成历史</p>
      <div className="mt-3 flex items-center gap-4 border-b border-white/[0.06] pb-2">
        {TABS.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`relative pb-1.5 text-[13px] ${
              tab === t ? "text-white" : "text-white/50 hover:text-white/80"
            }`}
          >
            {t}
            {tab === t ? (
              <span className="absolute inset-x-1 -bottom-[9px] h-[2px] rounded bg-white" />
            ) : null}
          </button>
        ))}
      </div>
      <p className="py-10 text-center text-[13px] text-white/35">暂无生成历史</p>
    </div>
  );
}
