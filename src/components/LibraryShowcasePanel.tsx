"use client";

import { useMemo, useState } from "react";
import { BadgeCheck, Search, SlidersHorizontal, Star, X } from "lucide-react";
import { cn } from "@/lib/utils";

// Batch 529: 2026-09-27 第六/七/八轮源站采样
// （liblib-source-exploration-2026-09-25/NOTES.md §132-145 + 截图 31/32/34/35）——
// 素材库两入口各自打开一个大版面浮层：三页签（广场/我的收藏/最近使用）、
// 搜索框、分类/筛选行、8 列卡片网格；我的收藏/最近使用 新账号为空态「暂无素材」。
// 卡片缩略图为 CLONE_DECISION 渐变占位（源站缩略图不可下载、禁止外链热链）；
// 标题/作者/热度为截图转录，低分辨率字段在数据行内标注。

export type LibraryVariant = "style" | "effects";

interface LibraryCard {
  title: string;
  author: string;
  likes: string;
  /** 截图 32 第一行前 7 张为已加载封面，其余为源站本身的灰色未加载块。 */
  loaded?: boolean;
}

interface LibraryShowcasePanelProps {
  variant: LibraryVariant;
  onClose: () => void;
}

const styleConfig = {
  plazaTab: "风格广场",
  searchPlaceholder: "搜索风格名称、作者",
} as const;

const effectsConfig = {
  plazaTab: "特效广场",
  searchPlaceholder: "搜索特效名称、作者",
} as const;

const tabs = ["我的收藏", "最近使用"] as const;

// 风格库卡片（截图 31 前两行转录；标题以源站截断样式「…」结尾的按原样保留；
// 分类页签 推荐/摄影写真/电商营销/动漫游戏/风格插画/平面设计/建筑及室内设计/
// 创意玩法/文创周边/小说推文，无逐卡分类映射采样——页签仅本地图形态）。
const styleCategories = [
  "推荐",
  "摄影写真",
  "电商营销",
  "动漫游戏",
  "风格插画",
  "平面设计",
  "建筑及室内设计",
  "创意玩法",
  "文创周边",
  "小说推文",
] as const;
const styleCards: LibraryCard[] = [
  { title: "Seedream 5.0 pro", author: "热成纯有壹", likes: "500.7k" },
  { title: "J-漫剧素材三视…", author: "JM32", likes: "9800" },
  { title: "【照顾设计】短剧…", author: "照顾设计", likes: "83" },
  { title: "Qwen-群体风格", author: "uulovelyly", likes: "3900" },
  { title: "Z-Image-Turbo…", author: "卷卷妈咪", likes: "3900" },
  { title: "Qwen-国风 3D…", author: "AI作转目", likes: "91" },
  { title: "Qwen-3D都市AI…", author: "Rojer", likes: "431" },
  { title: "一键生成人物多…", author: "柚子酸奶", likes: "1.8k" },
  { title: "真人角色三视图设计", author: "JUCE_萌", likes: "5100" },
  { title: "Qwen-Q版卡通…", author: "Inga", likes: "431" },
  { title: "古风-淡彩定普查…", author: "Nvi", likes: "1900" },
  { title: "电商首页头图商…", author: "夏至", likes: "3900" },
  { title: "音频类硬件产品…", author: "睡晒", likes: "5800" },
  { title: "分镜剧本故事版…", author: "YOU S", likes: "2700" },
  { title: "毛昵黏土微缩梦境…", author: "夏至", likes: "5000" },
  { title: "【摸鱼】3D电商…", author: "未来主义", likes: "1.2k" },
];

// 特效库卡片（截图 32 三行转录；loaded = 源站已加载封面，未标注为灰色未加载块）。
const effectsCards: LibraryCard[] = [
  { title: "小蜜蜂运镜", author: "vibe fckung", likes: "3400", loaded: true },
  { title: "穿云而入", author: "商务工作台", likes: "1500", loaded: true },
  { title: "飞跃地平线", author: "vibe fckung", likes: "2700", loaded: true },
  { title: "逆转引力", author: "omcom", likes: "533", loaded: true },
  { title: "地球缩放", author: "孤独的白日梦", likes: "502", loaded: true },
  { title: "环球缩放", author: "苏打绿豆", likes: "529", loaded: true },
  { title: "瞳孔推镜", author: "消息免打扰", likes: "982", loaded: true },
  { title: "俯冲地球", author: "没有工作的天", likes: "722" },
  { title: "产品扫光", author: "鲸鱼chill", likes: "3000" },
  { title: "普拉达换装", author: "omcom", likes: "198" },
  { title: "多角度定点", author: "AI萨大法官", likes: "1800" },
  { title: "水下慢镜头", author: "AI萨大法官", likes: "599" },
  { title: "试妆特写", author: "捏提AI", likes: "205" },
  { title: "悬浮深入", author: "捏提AI", likes: "430" },
  { title: "微距推镜", author: "可可大王", likes: "719" },
  { title: "直升机揭幕", author: "汪汪旺", likes: "151" },
  { title: "山路追击", author: "AI萨大法官", likes: "482" },
  { title: "雪地赛车", author: "可可大王", likes: "269" },
  { title: "City Drive", author: "捏提AI", likes: "188" },
  { title: "3D解构", author: "大葱同学", likes: "851" },
  { title: "面部环拍", author: "苏打绿豆", likes: "482" },
  { title: "Showroom", author: "可可大王", likes: "184" },
  { title: "饰品特写", author: "江户川柯伟", likes: "141" },
  { title: "巨人俯瞰", author: "大葱同学", likes: "222" },
];

// CLONE_DECISION：源站缩略图不可下载且禁止热链，用标题哈希确定性渐变占位。
function thumbGradient(title: string) {
  let hash = 0;
  for (const ch of title) hash = (hash * 31 + ch.codePointAt(0)!) % 360;
  return `linear-gradient(160deg, hsl(${hash} 32% 26%), hsl(${(hash + 48) % 360} 28% 15%))`;
}

function LibraryCardView({ card, variant }: { card: LibraryCard; variant: LibraryVariant }) {
  const unloaded = variant === "effects" && !card.loaded;
  return (
    <div data-library-card className="group" data-library-card-title={card.title}>
      <div
        className={cn(
          "relative w-full overflow-hidden rounded-lg",
          variant === "style" ? "aspect-[4/5]" : "aspect-square",
          unloaded && "bg-[#2a2a2a]",
        )}
        style={unloaded ? undefined : { background: thumbGradient(card.title) }}
      >
        <span className="absolute left-1.5 top-1.5 rounded-md bg-black/45 px-1.5 py-0.5 text-[10px] leading-4 text-[#d0d0d0]">
          ···
        </span>
        {/* Batch 358: 收藏按钮此前**完全没有 onClick**, 却用
            `group-hover:opacity-100` 在悬停卡片时整个显形 —— 风格库/特效库里
            一次扫出 40 多个这样的按钮, 全部点了没反应。收藏列表本身是空态
            (「我的收藏/最近使用 新账号为空态」, 见文件头), 没有可写的存储,
            不发明收藏功能。保留卡片与几何, 改成不悬停不显形 + title 说明。 */}
        <button
          type="button"
          aria-label={`收藏 ${card.title}`}
          title="收藏在克隆侧尚未接入"
          data-inert="true"
          className="pointer-events-none absolute right-1.5 top-1.5 rounded-full bg-black/45 p-1 text-[#6f6f6f] opacity-0"
        >
          <Star size={12} />
        </button>
      </div>
      <div className="mt-1.5 flex items-center gap-1">
        <span className="min-w-0 flex-1 truncate text-xs text-[#e6e6e6]">{card.title}</span>
        <span className="flex shrink-0 items-center gap-0.5 text-[10px] text-[#8c8c8c]">
          <BadgeCheck size={10} />
          商用
        </span>
      </div>
      <div className="mt-1 flex items-center gap-1">
        <span className="flex size-4 shrink-0 items-center justify-center rounded-full bg-white/10 text-[8px] text-[#c0c0c0]">
          {card.author.slice(0, 1)}
        </span>
        <span className="min-w-0 flex-1 truncate text-[10px] text-[#8c8c8c]">{card.author}</span>
        <span className="shrink-0 text-[10px] text-[#8c8c8c]">▽ {card.likes}</span>
      </div>
    </div>
  );
}

export function LibraryShowcasePanel({ variant, onClose }: LibraryShowcasePanelProps) {
  const config = variant === "style" ? styleConfig : effectsConfig;
  const cards = variant === "style" ? styleCards : effectsCards;
  const [plazaTab, setPlazaTab] = useState(true);
  const [activeTab, setActiveTab] = useState<(typeof tabs)[number] | null>(null);
  const [category, setCategory] = useState("推荐");
  const [commercialOnly, setCommercialOnly] = useState(false);
  const [query, setQuery] = useState("");

  const visibleCards = useMemo(
    () =>
      cards.filter(
        (card) =>
          !query.trim() ||
          card.title.includes(query.trim()) ||
          card.author.includes(query.trim()),
      ),
    [cards, query],
  );

  return (
    <section
      aria-label={variant === "style" ? "风格库" : "特效库"}
      data-liblib-overlay={`primary:${variant}-library`}
      data-library-variant={variant}
      className="fixed bottom-[76px] left-1/2 top-[64px] z-[62] flex w-[min(1200px,94vw)] -translate-x-1/2 flex-col rounded-2xl border border-white/10 bg-[#161616] shadow-[0_24px_80px_rgba(0,0,0,0.6)]"
    >
      <div className="flex items-center gap-3 px-5 pt-4">
        <div className="flex items-center gap-1">
          <button
            type="button"
            data-library-plaza-tab
            aria-pressed={plazaTab}
            onClick={() => {
              setPlazaTab(true);
              setActiveTab(null);
            }}
            className={cn(
              "rounded-lg px-3 py-1.5 text-sm",
              plazaTab ? "bg-white/10 text-white" : "text-[#9a9a9a] hover:bg-white/[0.06]",
            )}
          >
            {config.plazaTab}
          </button>
          {tabs.map((tab) => (
            <button
              key={tab}
              type="button"
              data-library-empty-tab={tab}
              aria-pressed={!plazaTab && activeTab === tab}
              onClick={() => {
                setPlazaTab(false);
                setActiveTab(tab);
              }}
              className={cn(
                "rounded-lg px-3 py-1.5 text-sm",
                !plazaTab && activeTab === tab
                  ? "bg-white/10 text-white"
                  : "text-[#9a9a9a] hover:bg-white/[0.06]",
              )}
            >
              {tab}
            </button>
          ))}
        </div>
        <div className="flex h-9 w-[300px] items-center gap-2 rounded-lg bg-white/[0.06] px-3">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder={config.searchPlaceholder}
            aria-label={config.searchPlaceholder}
            className="min-w-0 flex-1 bg-transparent text-xs text-[#e0e0e0] outline-none placeholder:text-[#666]"
          />
          <Search size={14} className="shrink-0 text-[#8c8c8c]" />
        </div>
        <div className="ml-auto flex items-center gap-2">
          {/* Batch 358: 此前启用、无 handler、带 hover 底色。分类行已经是真的
              (data-library-category), 唯独这个筛选按钮点了没反应。 */}
          <button type="button" aria-label="筛选" title="筛选在克隆侧尚未接入" data-inert="true" className="cursor-default rounded-lg p-2 text-[#6f6f6f]">
            <SlidersHorizontal size={16} />
          </button>
          <button
            type="button"
            data-library-close
            aria-label="关闭"
            onClick={onClose}
            className="rounded-lg p-2 text-[#c0c0c0] hover:bg-white/[0.06]"
          >
            <X size={18} />
          </button>
        </div>
      </div>

      {plazaTab ? (
        <>
          <div className="flex items-center gap-1.5 overflow-x-auto px-5 pt-3">
            {variant === "style" &&
              styleCategories.map((item) => (
                <button
                  key={item}
                  type="button"
                  data-library-category={item}
                  aria-pressed={category === item}
                  onClick={() => setCategory(item)}
                  className={cn(
                    "shrink-0 rounded-lg px-2.5 py-1 text-xs",
                    category === item
                      ? "bg-white/10 text-white"
                      : "text-[#9a9a9a] hover:bg-white/[0.06]",
                  )}
                >
                  {item}
                </button>
              ))}
            {variant === "effects" && (
              <span
                data-library-category="推荐"
                className="rounded-lg bg-white/10 px-2.5 py-1 text-xs text-white"
              >
                推荐
              </span>
            )}
            {variant === "style" && (
              <label className="ml-auto flex shrink-0 cursor-pointer items-center gap-1.5 text-[11px] text-[#9a9a9a]">
                <input
                  type="checkbox"
                  checked={commercialOnly}
                  onChange={(event) => setCommercialOnly(event.target.checked)}
                  className="size-3 accent-[#09caf5]"
                />
                仅看可商用
              </label>
            )}
            <span className="shrink-0 rounded-lg bg-white/[0.06] px-2.5 py-1 text-[11px] text-[#c0c0c0]">
              全部
            </span>
          </div>
          <div className="mt-3 flex-1 overflow-y-auto px-5 pb-5">
            <div className="grid grid-cols-[repeat(auto-fill,minmax(124px,1fr))] gap-x-3 gap-y-4">
              {visibleCards.map((card) => (
                <LibraryCardView key={card.title} card={card} variant={variant} />
              ))}
            </div>
          </div>
        </>
      ) : (
        <div
          data-library-empty
          className="flex flex-1 items-center justify-center text-sm text-[#777]"
        >
          暂无素材
        </div>
      )}
    </section>
  );
}
