"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useReactFlow } from "@xyflow/react";
import { useJimengStore } from "@/store/jimengStore";
import type { JimengNode, JimengNodeKind } from "@/types/jimeng";

/**
 * 顶栏搜索覆盖层 (Batch 96；**批 856 按源站实测重写**)。
 *
 * ⚠️⚠️ 批 856 之前，这一层是**猜的**。文件头原文：
 *   `SOURCE_FACT: 源站顶栏 搜索 (canvas-search) 存在 (96 顶栏 dump)，
 *    但其覆盖层内容**从未被捕获**。CLONE_DECISION: 复刻为最小搜索面板 ——
 *    输入框 + 「暂无搜索结果」空态，380px 与生成历史面板同族。`
 * 那个「380px 与生成历史面板同族」是**类比出来的**，不是量出来的。
 *
 * 批 856a 实测（登录态，视口 1512×1200，探针 jimeng_probe856a_search_recon.py）：
 * 源站这一层是 **ASIDE `role=dialog` `canvas-feature-panel` 320×1084
 * @[997,56]**，结构**四段**，而复刻只有第一段的一半：
 *
 *   ① 搜索框  `INPUT` 242×26 @[1050,77]，placeholder **「搜索节点...」**
 *   ② 分类 tablist `role=tablist` 320×36 @[997,112]，
 *      aria-label **「Search result categories」**，9 个 `role=tab`：
 *      `全部 20` / `图片 1` / `视频 1` / `音频 13` / `文本 3` / `主体` /
 *      `时间线 1` / `组` / `其他 1`；⚠️ **漫游 tabindex**（`全部` ti=0，其余 ti=-1）
 *      + 一个「Next search categories」右翻按钮
 *   ③ 节点清单：每项 `BUTTON` **304×64**，aria-label 形如
 *      **`音频 13, 音频`**（名称, 类型），行内含序号(1/2/3…) + 名称 + 类型
 *   ④ 分页器：4 个 `BUTTON` 28×28 —— `前往上一页` / `前往下一页` +
 *      两个 i18n 占位 aria-label（`{num, plural, other {向前 {num} 页}}`）
 *
 * ⚠️ 那个 **242** 从哪来的：它是**搜索框的宽度**，不是面板宽度。复刻把
 * 面板整块写成了 `w-[242px]` —— 数字对、**层级错**，于是一个 1084 高的
 * 节点总览面板被做成了 242 宽的小下拉。
 */

/** 分类 tab 的顺序照抄源站（探针 856a 逐个读出来的 aria-label）。 */
const CATS = [
  { key: "all", label: "全部" },
  { key: "image", label: "图片" },
  { key: "video", label: "视频" },
  { key: "audio", label: "音频" },
  { key: "text", label: "文本" },
  { key: "subject", label: "主体" },
  { key: "timeline", label: "时间线" },
  { key: "group", label: "组" },
  { key: "other", label: "其他" },
] as const;

type CatKey = (typeof CATS)[number]["key"];

/** 节点类型 → 源站分类。`组`/`其他` 在复刻里没有对应 kind，恒为 0。 */
function catOf(n: JimengNode): CatKey {
  const k = n.type as JimengNodeKind;
  if (k === "image" || k === "video" || k === "audio" || k === "text"
      || k === "subject" || k === "timeline") return k;
  return "other";
}

/** 源站每项 aria-label 是 `名称, 类型`（探针 856a 实测 `音频 13, 音频`）。 */
function nodeLabel(n: JimengNode): string {
  const title = (n.data as { title?: string }).title || n.id;
  const type = CATS.find((c) => c.key === catOf(n))?.label ?? "其他";
  return `${title}, ${type}`;
}

const PAGE = 14;   // 探针 856a：源站一页实测列出 14 项（音频 13…导演台）

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
  const [cat, setCat] = useState<CatKey>("all");
  const [page, setPage] = useState(0);
  const nodes = useJimengStore((s) => s.nodes);
  const selectNode = useJimengStore((s) => s.selectNode);
  const rf = useReactFlow();

  /* 搜完点某项 = 选中它并把画布挪过去（源站那一项 aria-label 是
     `名称, 类型`，点它显然是「跳到这个节点」）。这属于**推断**：
     ⚠️ 856a 只 dump 了结构，**没点过那一项**（点了会改变画布状态，
     且本批只做取证）。所以这里按最小语义实现，并在注释里标明未取样。 */
  const goto = (id: string) => {
    selectNode(id);
    const n = nodes.find((x) => x.id === id);
    if (n) {
      rf.setCenter(n.position.x + 280, n.position.y + 160, { zoom: 1, duration: 200 });
    }
    onClose("outside");
  };

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

  const q = query.trim();
  const matched = useMemo(
    () => (q ? nodes.filter((n) => nodeLabel(n).includes(q)
                              || (n.data as { title?: string }).title?.includes(q))
            : nodes),
    [nodes, q],
  );
  const inCat = useMemo(
    () => (cat === "all" ? matched : matched.filter((n) => catOf(n) === cat)),
    [matched, cat],
  );
  const pages = Math.max(1, Math.ceil(inCat.length / PAGE));
  const p = Math.min(page, pages - 1);
  const rows = inCat.slice(p * PAGE, p * PAGE + PAGE);

  const countOf = (k: CatKey) => (k === "all" ? matched.length
    : matched.filter((n) => catOf(n) === k).length);

  return (
    <div
      ref={ref}
      /* 批 856：320 宽是源站实测（探针 856a，**布局常量**，写死）。
       *
       * ⚠️⚠️ 批 863 修的真缺陷：高度原来写 `maxHeight: 1084px`（源站实测值）。
       * 那个 **1084 是源站那 20 个节点撑出来的**，不是「面板该有多高」——
       * 而且源站这一版画布**节点少**，1084 恰好没顶出视口，所以照抄看不出来。
       * 复刻节点一多，`top-full` 向下生长就**溢出视口**，320×1084 的面板
       * 把**右半屏整个盖住** ⇒ 顶栏其余的层（分享 / 更多 / 账号菜单 /
       * 搜索自己）**全都点不开了**：审计实测探到的层从 21 掉到 **13**，
       * 自检那一段整个没跑到（`kb_self_test` 全 `null`）。
       *
       * 正解：高度**跟着视口**，不跟源站那一版的节点数。
       * `maxHeight: calc(100vh - 72px)`（72 = top 偏移 56 + 上下留白），
       * 超出就在**清单那段**内部滚动（那一段本来就有 `overflow-y-auto`）。
       * 这样节点再多也**盖不满视口**，别的层照常点得开。 */
      className="nodrag nowheel absolute z-canvas-chrome flex w-[320px] flex-col overflow-hidden rounded-xl p-2 outline-none"
      style={{
        background: "rgb(38,38,38)",
        maxHeight: "calc(100vh - 72px)",
      }}
      role="dialog"
      aria-label="搜索"
      data-testid="jimeng-search-overlay"
    >
      {/* ① 搜索框 242×26，placeholder 逐字照抄源站 */}
      <input
        autoFocus
        value={query}
        onChange={(e) => { setQuery(e.target.value); setPage(0); }}
        placeholder="搜索节点..."
        aria-label="搜索"
        data-testid="jimeng-search-input"
        className="h-[26px] w-[242px] rounded-lg bg-white/[0.06] px-3 text-[13px] text-white placeholder:text-white/40 outline-none"
      />

      {/* ② 分类 tablist。aria-label 逐字照抄源站的英文原文
         （「Search result categories」）—— 源站是英文，不翻译。
         ⚠️⚠️ 批 857 实测修的**真缺陷**（不是 §74 猜的那个滚动容器）：
         9 个 tab 在 320px 里横向排不下，实测面板右边缘到 **x=1569 > 视口
         1512** ⇒ 「时间线」整个**掉到屏幕外**（探针 857 边采样 tops =
         `react-flow__pane selection` / `null`，皮当栈顶 0/4）。
         源站自己有解法：实测它的 tablist 带一个
         **「Next search categories」右翻按钮**（`[1277,118, 24,24]`），
         装不下的分类靠它翻。所以这里照做 —— tablist **可横向滚动**，
         再加一枚右翻按钮把滚动区露出来。
         ⚠️ §74 当时猜「`overflow-y-auto` 改了层叠上下文导致皮当不了栈顶」，
         探针 857 **证伪**了：新版皮当栈顶 **41 次**，比旧版的 4 次还多。 */}
      <div className="relative mt-2 flex h-9 shrink-0 items-center">
        <div
          role="tablist"
          aria-label="Search result categories"
          data-testid="jimeng-search-categories"
          className="flex h-9 w-full items-center gap-1 overflow-x-auto"
          /* ⚠️ 批 863：`pr-6` 给右翻按钮**让出位置**。没有它，按钮 `absolute
             right-0` 就**盖在最后一个 tab 上**，而滚动区初始停在最左 ——
             既看不到「右边还有」，也点不到被盖住的那一个。 */
          style={{ paddingRight: "1.5rem" }}
        >
        {CATS.map((c) => (
          <button
            key={c.key}
            type="button"
            role="tab"
            aria-selected={cat === c.key}
            /* 源站是**漫游 tabindex**：当前项 ti=0、其余 ti=-1（探针 856a 实测）。 */
            tabIndex={cat === c.key ? 0 : -1}
            aria-label={`${c.label} ${countOf(c.key)}`}
            onClick={() => { setCat(c.key); setPage(0); }}
            className={`h-9 shrink-0 whitespace-nowrap rounded-md px-2 text-[13px] ${
              cat === c.key ? "bg-white/[0.12] text-white" : "text-white/60"
            }`}
          >
            {c.label}
            {c.key === "group" ? "" : ` ${countOf(c.key)}`}
          </button>
        ))}
        </div>
        {/* 源站实测有这枚「Next search categories」右翻按钮（24×24）——
           9 个分类在 320px 里装不下，它就是用来翻的。照做。 */}
        <button
          type="button"
          aria-label="Next search categories"
          tabIndex={-1}
          onClick={() => {
            const el = ref.current?.querySelector<HTMLElement>(
              '[data-testid="jimeng-search-categories"]');
            if (el) el.scrollBy({ left: el.clientWidth, behavior: "smooth" });
          }}
          className="absolute right-0 top-0 flex h-9 w-6 shrink-0 items-center justify-end text-white/60"
        >
          <ChevronRight size={14} />
        </button>
      </div>

      {/* ③ 节点清单 304×64。空态文案照抄源站（探针 856a 未见空态，
         这里沿用源站搜索框 placeholder 同源的「暂无搜索结果」——
         ⚠️ 这一句**没在 856a 取到样**，属沿用旧文案，不是新事实）。
         ⚠️ `gap-1`（4px）是**源站实测**的行距：源站行 y=152/220/288…**间距
         68px**、行高 64px ⇒ 间隙 4px。行贴死会让审计的反向自检作废
         （`皮当过栈顶 0 次` ⇒ 「不多报」成恒真空话，退出码 2）。 */}
      <div className="mt-1 flex min-h-0 flex-1 flex-col gap-1 overflow-y-auto">
        {rows.length === 0 ? (
          <p className="py-10 text-center text-[13px] text-white/35" data-testid="search-empty">
            暂无搜索结果
          </p>
        ) : (
          rows.map((n, i) => (
            <button
              key={n.id}
              type="button"
              /* 源站 aria-label = `名称, 类型`（实测 `音频 13, 音频`） */
              aria-label={nodeLabel(n)}
              onClick={() => goto(n.id)}
              data-testid="jimeng-search-row"
              className="flex h-16 w-full items-center gap-3 rounded-lg px-2 text-left hover:bg-white/[0.08]"
            >
              <span className="w-3 text-center text-[12px] text-white/40">
                {p * PAGE + i + 1}
              </span>
              <span className="min-w-0 flex-1 truncate text-[13px] text-white/90">
                {(n.data as { title?: string }).title || n.id}
              </span>
              <span className="shrink-0 text-[12px] text-white/45">
                {CATS.find((c) => c.key === catOf(n))?.label ?? "其他"}
              </span>
            </button>
          ))
        )}
      </div>

      {/* ④ 分页器 28×28 四枚。aria-label 逐字照抄源站：
         「前往上一页」「前往下一页」 */}
      <div className="flex h-9 shrink-0 items-center justify-center gap-6">
        <button
          type="button"
          aria-label="前往上一页"
          disabled={p === 0}
          onClick={() => setPage(Math.max(0, p - 1))}
          className="flex h-7 w-7 items-center justify-center rounded-md text-white/70 disabled:opacity-30"
        >
          <ChevronLeft size={16} />
        </button>
        <span className="text-[12px] text-white/50">
          {p + 1} / {pages}
        </span>
        <button
          type="button"
          aria-label="前往下一页"
          disabled={p >= pages - 1}
          onClick={() => setPage(Math.min(pages - 1, p + 1))}
          className="flex h-7 w-7 items-center justify-center rounded-md text-white/70 disabled:opacity-30"
        >
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}
