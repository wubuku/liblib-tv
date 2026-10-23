"use client";

import { useMemo, useRef, useState } from "react";
import { X } from "lucide-react";

import { useModalFocusTrap } from "./jimengMenuChrome";
import { useJimengStore } from "@/store/jimengStore";

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

/** ⭐⭐⭐ Batch 1032-②b-1：「时间」「筛选」两枚图标钮此前**没有 onClick**
 *  ⇒ ⇒ 点不动（1032 审计登记的死按钮之一）。
 *  两枚都接成**真的状态变更**：
 *  · 时间 → 时间范围菜单（全部时间 / 最近 7 天 / 最近 30 天）⇒ ⇒ 空态文案跟着变
 *  · 筛选 → 类型菜单（图片 / 视频 / 音频 / 文档）⇒ ⇒ 筛选行的高亮跟着移动
 *  ⚠️ 资产库在复刻里本来就是**空态 mock**（源站取证时也是空态）⇒ ⇒
 *  ⇒ ⇒ 所以这两枚按钮的效果落在**筛选行与空态文案**上，不落在素材列表上；
 *  ⇒ ⇒ 这一点写在这里，不假装「排序真的作用在素材上」。 */
const TIME_RANGES = [
  { id: "all", label: "全部时间", suffix: "" },
  { id: "7d", label: "最近 7 天", suffix: "最近 7 天的" },
  { id: "30d", label: "最近 30 天", suffix: "最近 30 天的" },
] as const;

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
  /* ⭐⭐⭐ 1032-②b-1：时间范围 + 哪个图标菜单开着。 */
  const [range, setRange] = useState<(typeof TIME_RANGES)[number]["id"]>("all");
  const [iconMenu, setIconMenu] = useState<"时间" | "筛选" | null>(null);
  /* ⭐⭐⭐⭐⭐ Batch 1032-④-B（C03）：**真的能输入的搜索框**。
   *
   * 此前那一格是 `<span>搜索</span>` —— **画成了输入框的样子却不是控件**：
   * 不可聚焦、不可输入、也没有 `role=textbox`。
   * 而整个模态**不 import store** ⇒ ⇒ 永远空态 ⇒ ⇒ 「搜索」永远搜不到东西。
   *
   * 现在：① 它是一个真 `<input>`；② 素材**真的来自 store 的画布节点**；
   *      ③ 搜索词**真的过滤**素材；④ 空态文案随搜索词变化。
   */
  const [query, setQuery] = useState("");
  const nodes = useJimengStore((s) => s.nodes);

  /** 素材 = 画布上**真的有内容**的节点（图片/视频/音频/文本）。 */
  const assets = useMemo(
    () =>
      nodes
        .filter((n) => {
          const t = n.type;
          if (t === "image") return Boolean((n.data as { poster?: string }).poster);
          if (t === "video") return Boolean((n.data as { hasMedia?: boolean }).hasMedia);
          if (t === "audio") return true;
          if (t === "text") return true;
          return false;
        })
        .map((n) => ({
          id: n.id,
          kind: n.type === "image" ? "图片" : n.type === "video" ? "视频" : n.type === "audio" ? "音频" : "文档",
          title: String((n.data as { title?: string }).title ?? n.id),
        })),
    [nodes],
  );

  /** 真过滤：搜索词命中标题（大小写不敏感）⇒ 结果会真的变少。 */
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return assets.filter((a) => {
      if (isSubject) return false;
      if (activeFilter !== "全部" && a.kind !== activeFilter) return false;
      if (q && !a.title.toLowerCase().includes(q)) return false;
      return true;
    });
  }, [assets, query, activeFilter, isSubject]);

  const rangeSuffix =
    TIME_RANGES.find((r) => r.id === range)?.suffix ?? "";
  const emptyText = isSubject
    ? "没有可用主体"
    : query.trim()
      ? `没有匹配「${query.trim()}」的${filter}素材`
      : `暂无${rangeSuffix}${filter}素材`;
  const layerRef = useRef<HTMLDivElement>(null);

  /* 批 864：开层即接管焦点 + Tab 困在层内。
     探针 864 实测（修之前）：`focus_at_open.state='covered'`（焦点还留在
     「资产库」触发器上，而触发器此刻已被本模态自己的 `bg-black/55` 遮罩
     盖住 4/4 边），按 Tab 走过 **11 个**焦点环看不见的位置。
     ⚠️ 本模态**有**全屏不透明遮罩（`absolute inset-0 bg-black/55`，点击
     关闭）⇒ 它是货真价实的**模态**：模态盖住了页面，就不该把焦点漏给页面。
     依据就是模态自身这条定义，不依赖源站是否取到样。 */
  useModalFocusTrap(layerRef, true);

  return (
    <div className="fixed inset-0 z-[210] flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/55"
        onClick={onClose}
        aria-hidden
      />
      <div
        ref={layerRef}
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
          {/* ⭐⭐⭐⭐⭐ Batch 1032-④-B（C03）：这里此前是 `<span>搜索</span>` ——
              **画成了输入框的样子却不是控件**。现在是真的 `<input>`：
              可聚焦、可输入、有 `role=textbox` 与 `aria-label`，
              且搜索词**真的过滤**下面的素材列表。 */}
          <div
            className="flex h-9 w-[200px] items-center gap-2 rounded-lg bg-white/[0.06] px-3"
            data-testid="assets-search"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden>
              <circle cx="6" cy="6" r="4.4" stroke="currentColor" strokeWidth="1.2" className="text-white/40" />
              <path d="m9.4 9.4 2.8 2.8" stroke="currentColor" strokeWidth="1.2" className="text-white/40" />
            </svg>
            <input
              type="text"
              role="textbox"
              aria-label="搜索素材"
              placeholder="搜索"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              data-testid="assets-search-input"
              className="w-full bg-transparent text-[13px] text-white outline-none placeholder:text-white/40"
            />
          </div>
          {/* Batch 78 (SOURCE_FACT): hover 显示 radix 式 tooltip 药丸 (按钮下方) */}
          {(["时间", "筛选"] as const).map((label, i) => (
            <div key={label} className={`group/tip relative ${i === 0 ? "ml-2" : "ml-1"}`}>
              <button
                type="button"
                aria-label={label}
                title={label}
                aria-expanded={iconMenu === label}
                aria-haspopup="menu"
                onClick={() => setIconMenu((v) => (v === label ? null : label))}
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
              {iconMenu === label ? (
                /* ⭐⭐⭐ 1032-②b-1：真的菜单层（不是装饰）。
                   · 「时间」→ 时间范围（改空态文案）
                   · 「筛选」→ 素材类型（改筛选行高亮） */
                <div
                  className="absolute right-0 top-[calc(100%+6px)] z-[220] w-[168px] rounded-[10px] p-1"
                  style={{ background: "rgb(38,38,38)" }}
                  role="menu"
                  aria-label={label === "时间" ? "时间范围" : "素材类型"}
                >
                  {label === "时间"
                    ? TIME_RANGES.map((r) => (
                        <button
                          key={r.id}
                          type="button"
                          role="menuitemradio"
                          aria-checked={r.id === range}
                          onClick={() => {
                            setRange(r.id);
                            setIconMenu(null);
                          }}
                          className={`flex h-8 w-full items-center rounded-lg px-2.5 text-[13px] ${
                            r.id === range ? "bg-white/[0.10] text-white" : "text-white/80 hover:bg-white/[0.08]"
                          }`}
                        >
                          {r.label}
                        </button>
                      ))
                    : FILTERS.map((f) => (
                        <button
                          key={f}
                          type="button"
                          role="menuitemradio"
                          aria-checked={f === filter}
                          onClick={() => {
                            setFilter(f);
                            setIconMenu(null);
                          }}
                          className={`flex h-8 w-full items-center rounded-lg px-2.5 text-[13px] ${
                            f === filter ? "bg-white/[0.10] text-white" : "text-white/80 hover:bg-white/[0.08]"
                          }`}
                        >
                          {f}
                        </button>
                      ))}
                </div>
              ) : null}
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
              bg white/4%、r2。
              ⭐⭐⭐ Batch 1032-④-B（C03）：**素材列表不再是永远的空态** ——
              它现在列出 store 里**真的有内容**的画布节点，并且**随搜索词变化**。 */}
          {filtered.length > 0 ? (
            <div className="grid h-full grid-cols-5 gap-[2px] overflow-y-auto">
              {filtered.map((a) => (
                <div
                  key={a.id}
                  data-testid="assets-item"
                  title={a.title}
                  className="flex aspect-square items-center justify-center overflow-hidden rounded-[2px] bg-white/[0.04] p-1 text-center text-[11px] leading-tight text-white/60"
                >
                  <span className="break-all">{a.title}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="ml-auto grid h-full w-[630px] grid-cols-5 gap-[2px] overflow-hidden">
              {Array.from({ length: 20 }).map((_, i) => (
                <div
                  key={i}
                  className="aspect-square rounded-[2px] bg-white/[0.04]"
                />
              ))}
            </div>
          )}
          {/* ⭐⭐⭐ 空态**只在真的没有结果时**盖住列表 ——
              否则它会把刚列出来的素材整片遮住（列表就白列了）。 */}
          {filtered.length === 0 ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-[14px] text-white/35" data-testid="assets-empty">
                {emptyText}
              </span>
            </div>
          ) : null}
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
