"use client";

import { useState } from "react";
import { X } from "lucide-react";

/**
 * 资产库模态框 (Batch 72)。
 *
 * 证据 (SOURCE_FACT, docs/design-references/jimeng/72-assets-panel.png +
 * 72-assets.json computed style):
 * - 左栏 资产库 点击打开居中模态: 801×620, bg rgb(26,26,26), r20
 * - 顶部 tab: 资产 (active bg white/8%) | 主体；右上 × 关闭
 * - 筛选行: 图片(active) 视频 音频 文档 (58×36, inactive white/70) +
 *   搜索输入 (200×36) + 时间/筛选 图标钮 (28×28)
 * - 空态: 「暂无图片素材」 white/35 居中 + 网格骨架格
 * - 底栏: 「已选择 0 个素材」 white/60 + 确认钮 (80×36, bg white/16%
 *   text white/20 禁用)
 * CLONE_DECISION: 骨架格为空态近似 (源站截取时处于加载/空态叠加)；
 * 主体 tab 与其它筛选的空态文案外推 (暂无主体素材/暂无视频素材…)。
 */
const FILTERS = ["图片", "视频", "音频", "文档"] as const;

// Batch 75 (SOURCE_FACT 75-assets-deep.json): 空态文案跟随筛选切换
// (图片/视频/音频 实证「暂无X素材」；文档 同模式)。
// Batch 76 (SOURCE_FACT 76-subject-deep.json): 主体 tab 筛选行为单个
// 「全部」，空态为「没有可用主体」(此前「暂无主体素材」外推修正)。

export function JimengAssetsModal({ onClose }: { onClose: () => void }) {
  const [tab, setTab] = useState<"资产" | "主体">("资产");
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>("图片");
  // Escape 关闭走 workspace 统一 Escape 分支 (Batch 57 先例)

  const isSubject = tab === "主体";
  const activeFilter = isSubject ? "全部" : filter;
  const filters: string[] = isSubject ? ["全部"] : [...FILTERS];
  const emptyText = isSubject ? "没有可用主体" : `暂无${filter}素材`;

  return (
    <div className="fixed inset-0 z-[210] flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
        aria-hidden
      />
      <div
        role="dialog"
        aria-label="资产库"
        data-testid="jimeng-assets-modal"
        className="relative flex h-[620px] w-[800px] flex-col rounded-[20px] p-6"
        style={{ background: "rgb(26,26,26)" }}
      >
        {/* 顶部 tab + 关闭 */}
        <div className="flex items-center">
          <div className="flex items-center gap-1">
            {(["资产", "主体"] as const).map((t) => (
              <button
                key={t}
                type="button"
                data-testid={`assets-tab-${t}`}
                onClick={() => setTab(t)}
                className={`flex h-9 items-center rounded-lg px-3.5 text-[13px] font-medium ${
                  tab === t
                    ? "bg-white/[0.08] text-white"
                    : "text-white/70 hover:text-white"
                }`}
              >
                {t}
              </button>
            ))}
          </div>
          <span className="flex-1" />
          <button
            type="button"
            aria-label="关闭"
            data-testid="assets-close"
            onClick={onClose}
            className="flex size-8 items-center justify-center rounded-lg text-white/70 hover:bg-white/[0.08] hover:text-white"
          >
            <X size={16} />
          </button>
        </div>

        {/* 筛选行 */}
        <div className="mt-3 flex items-center">
          <div className="flex items-center gap-1">
            {(filters as string[]).map((f) => (
              <button
                key={f}
                type="button"
                data-testid={`assets-filter-${f}`}
                onClick={() => !isSubject && setFilter(f as (typeof FILTERS)[number])}
                className={`relative flex h-9 items-center rounded-lg px-3.5 text-[13px] font-medium ${
                  activeFilter === f
                    ? "text-white"
                    : "text-white/70 hover:text-white"
                }`}
              >
                {f}
                {activeFilter === f ? (
                  <span className="absolute inset-x-3.5 bottom-0.5 h-[2px] rounded-full bg-white" />
                ) : null}
              </button>
            ))}
          </div>
          <span className="flex-1" />
          <div
            className="flex h-9 w-[200px] items-center gap-2 rounded-lg bg-white/[0.06] px-3"
            data-testid="assets-search"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden>
              <circle cx="6" cy="6" r="4.4" stroke="currentColor" strokeWidth="1.2" className="text-white/40" />
              <path d="m9.4 9.4 2.8 2.8" stroke="currentColor" strokeWidth="1.2" className="text-white/40" />
            </svg>
            <span className="text-[13px] text-white/40">搜索</span>
          </div>
          {/* Batch 78 (SOURCE_FACT): hover 显示 radix 式 tooltip 药丸 (按钮下方) */}
          {(["时间", "筛选"] as const).map((label, i) => (
            <div key={label} className={`group/tip relative ${i === 0 ? "ml-2" : "ml-1"}`}>
              <button
                type="button"
                aria-label={label}
                title={label}
                className="flex size-9 items-center justify-center rounded-lg text-white/85 hover:bg-white/[0.08]"
              >
                {label === "时间" ? (
                  <svg width="15" height="15" viewBox="0 0 16 16" fill="none" aria-hidden>
                    <rect x="2" y="3" width="12" height="11" rx="2" stroke="currentColor" strokeWidth="1.2" />
                    <path d="M2 6.5h12M5.5 2v2M10.5 2v2" stroke="currentColor" strokeWidth="1.2" />
                  </svg>
                ) : (
                  <svg width="15" height="15" viewBox="0 0 16 16" fill="none" aria-hidden>
                    <path d="M2.5 4h11M4.5 8h7M6.5 12h3" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
                  </svg>
                )}
              </button>
              <span
                data-testid={`assets-tip-${label}`}
                className="pointer-events-none absolute left-1/2 top-full z-[130] mt-1 flex h-9 w-14 -translate-x-1/2 items-center justify-center rounded-lg text-[13px] text-white opacity-0 transition-opacity duration-100 group-hover/tip:opacity-100"
                style={{ background: "rgb(38,38,38)" }}
              >
                {label}
              </span>
            </div>
          ))}
        </div>

        {/* 素材网格骨架 + 空态 */}
        <div className="relative mt-3 flex-1 overflow-hidden rounded-xl">
          {/* Batch 78 (SOURCE_FACT): 骨架格 124×124、5 列、间距 2px、
              bg white/4%、r2 */}
          <div className="ml-auto grid h-full w-[630px] grid-cols-5 gap-[2px] overflow-hidden">
            {Array.from({ length: 20 }).map((_, i) => (
              <div
                key={i}
                className="aspect-square rounded-[2px] bg-white/[0.04]"
              />
            ))}
          </div>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-[14px] text-white/35" data-testid="assets-empty">
              {emptyText}
            </span>
          </div>
        </div>

        {/* 底栏 */}
        <div className="mt-3 flex items-center">
          <span className="text-[13px] text-white/60" data-testid="assets-selected">
            已选择 0 个素材
          </span>
          <span className="flex-1" />
          <button
            type="button"
            disabled
            data-testid="assets-confirm"
            className="flex h-9 w-20 cursor-not-allowed items-center justify-center rounded-lg bg-white/[0.16] text-[13px] font-medium text-white/20"
          >
            确认
          </button>
        </div>
      </div>
    </div>
  );
}
