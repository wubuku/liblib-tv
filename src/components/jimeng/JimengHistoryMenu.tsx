"use client";

import { useEffect, useRef, useState } from "react";
import { useTakeFocusAtOpen } from "@/components/jimeng/jimengMenuChrome";

/**
 * 顶栏 ⌕ 按钮 → 「生成历史」下拉 (Batch 13)。
 *
 * 证据 (SOURCE_FACT): 点击后搜索图标下方弹出 ≈380px 面板 rgb(38,38,38):
 * 标题「生成历史」+ tabs 全部(选中下划线)/图片/视频/音频 + 空态「暂无生成历史」。
 *
 * 批 855 SOURCE_FACT（探针 855a/855b 实测，登录态视口 1512×1200）：
 * 源站这一层是 **320×211 `role=dialog` `canvas-feature-panel`**，四项行为 ——
 *   · **开层即接管焦点**（焦点落在顶部 tab 按钮上）
 *   · **不困 Tab**（第 2 次逃出，层还在）
 *   · 方向键 **不动**（4 次 ArrowDown 全停在同一个 tab 按钮上 ——
 *     源站**没接**方向键漫游，不是「内容只有 1 项」）
 *   · **Esc 归位**（焦点回 `生成历史` 触发器）
 * ⚠️ 源站层内还有第二个 tab「积分明细」+ 筛选行
 *   `全部 图片 视频 音频 文本`。**847c/847d 当年点「第 2 个 launcher」
 *   开出来的就是它，于是认不出层 ⇒ 记成「前置态没成立」。**
 */
const TABS = ["全部", "图片", "视频", "音频"] as const;

export function JimengHistoryMenu({ onClose }: { onClose: () => void }) {
  const ref = useRef<HTMLDivElement>(null);
  const [tab, setTab] = useState<(typeof TABS)[number]>("全部");
  /* 批 855：源站开层即接管焦点（实测焦点落在顶部 tab 按钮上）⇒ 接上。
     ⚠️ **刻意不接 `useArrowKeys`**：源站这一层方向键**不动**
     （4 次 ArrowDown 轨迹全是同一个 tab 按钮）—— 源站没接方向键漫游，
     接了就是照抄一个源站没有的行为。 */
  useTakeFocusAtOpen(ref, true);

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
      /* Batch 823 SOURCE_FACT 缺口：批 816 做过一轮「可访问名 + 自动化锚点」
         收口，这块浮层只拿到了可访问名、**没拿到 testid** ——
         于是它是全画布唯二「自动化摸不到」的浮层之一（另一个是快捷键面板）。
         怎么发现的：batch 822 的 fixed 普查用「冒出新 testid」当到达信号，
         这一态死活到不了。**信号失明本身就是发现** ——
         摸不到的东西和不存在的东西，在报告里长得一模一样。 */
      data-testid="topbar-history-menu"
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
