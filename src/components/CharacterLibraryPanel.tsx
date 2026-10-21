"use client";

import Image from "next/image";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  Check,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Grid2x2,
  Image as ImageIcon,
  List,
  Plus,
  Search,
  SlidersHorizontal,
  UserPlus,
  X,
} from "lucide-react";
import "./character-studio.css";

interface CharacterLibraryPanelProps {
  onAddNode: (type: string, data?: Record<string, unknown>) => void;
  onClose: () => void;
}

// ★★ Batch 827（源站 2026-10-21 活体读数 + 源站 bundle 交叉核对）：
// ★★ 源站**当前**构建里这个面板已经不是「公共角色库」了，而是「**角色造型室**」：
//   源站 i18n 的新一套是 `characterStudioTitle`=角色造型室、
//   `characterStudioMyLibrary`=我的角色库、`characterStudioOfficialLibrary`=官方角色库、
//   `characterStudioAddToCanvas`=添加到画布；
//   旧一套（`characterLibraryTitle`=角色库、`publicCharacterLibrary`=公共角色库、
//   `characterApplyToCanvas`=应用至画布、`seedanceComplianceLibrary`=合规素材库）
//   在**当前**页面上逐字搜索 **0 命中** ⟹ ⟹ 那是 2026-09-07 的旧形态。
// ⟹ ★★ 本组件按**源站当前形态**重建。
// ★ 文件名/导出名沿用旧名，是为了不打脸 batch 63/729 的历史文档 ⟹ ★ 这一点
//   在 batch 827 README 里标注（组件名与内容不符是已知的历史遗留）。
//
// ★★ 几何一律走**普通 CSS**（`character-studio.css`）⟹ ★ 因为 4317 的 dev server
//   的 Tailwind 扫描自 2026-10-07 起冻结 ⟹ 新增的任意值类在 dev 上不生成
//   ⟹ 判据会在 dev 上量到一个不存在的面板 ⟹ 详见该 CSS 文件头的说明。
//
// ★★★ 源站组件本体（bundle 主 chunk `93fb61aec8_…`）给出的结构，逐条照抄：
//   header  h-[70px] px-6 pr-14 gap-4  ⟹ 页签 18px/600/26px，未选中 `text-fg-muted`（60% 白）
//   toolbar h-8 px-5  ⟹ 三枚原生 `<details>` 胶囊 + 搜索 + 多选 + 视图切换药丸
//   内容区  mt-4 flex-1 ⟹ carousel 视口 top-[42px] h-[434px]，track `left-1/2`（整条居中）
//           名字组 `absolute left-1/2 top-[504px]`，滚动条 `bottom-0 left-5 right-5`
//   footer  h-[88px] border-t justify-center ⟹ 三种形态（见下）
//   ★ 视图切换是一个药丸容器：px-[3px] gap-[3px] + 两条 26×26 按钮 + 一条 1px 竖线
//   ★ 选项行 h-9（36）+ 复选框是 **sr-only**（1×1）+ 选中态是**右侧 18px Checkmark**
//   ★ 「查看角色资产」在源站是 **opacity-0 + group-hover 才显形**，且居中于卡片
//   ★ 底部 CTA 有**三种**形态：
//       ① 多选态：左侧「全选」＋ 居中红色「删除角色」
//       ② 选中了一个角色：左侧「创建新角色」（ghost）＋ 居中一组
//          [「添加到画布」(ghost) + 「编辑角色」(白底 primary)]（间隙 8px，整组居中）
//       ③ 没选中角色：居中单枚白底「创建新角色」（min-w-80，gap 4）
const characterNames = [
  "甜妹/清新少女",
  "霸总/精英大佬",
  "温柔熟男/理想男友",
  "清冷千金/白切黑女主",
  "古风男主",
  "古风女主",
  "恶毒女配/白莲花",
  "正派长辈/父",
  "正派长辈/母",
  "反派长辈/势利亲戚",
  "生活方式普通人",
  "时尚感亚洲男生",
  "时尚感亚洲女生",
  "时尚感欧美男生",
  "时尚感欧美女生",
  "小男孩",
  "小女孩",
] as const;

const characters = characterNames.map((name, index) => ({
  id: `character-${index + 1}`,
  name,
  imageUrl: `/images/liblib-panels/character-thumb-${String(index + 1).padStart(2, "0")}.webp`,
}));

// ★★ 源站当前形态的**三个**筛选组（选项逐字来自源站实测，batch 827 raw）：
//   性别：男 / 女 / 中性
//   年龄段：儿童 / 少年 / 青年 / 中年 / 老年
//   文化区域：**我的角色库** 是 东亚 / 欧美 / 中东 / 非洲 / 其他；
//              **官方角色库** 是 东亚 / 欧美 / 中东 / 非洲 / **奇幻**
// ★★ 为什么两个页签不一样（源站 bundle 实证）：
//   bundle 里文化区域这组在「我的角色库」页签下走的是**写死的**本地表
//   （`lq` 映射：east_asia / europe / middle_east / africa / other），
//   在「官方角色库」页签下走的是**服务端下发的**筛选配置（`eg`），
//   而那份配置的第 5 项是「奇幻」（服务端数据，i18n 里**没有**这个键）。
//   ⟹ 官方页签那一组是**会被服务端改的**，这里照抄 2026-10-21 的实测值。
// ★★ 此前 clone 那一套是「性别／年龄段／种族／时代／文化区域」五组
//   （且文化区域是 clone 自己编的「华语/日韩/欧美/东南亚」）⟹ 本批按源站改成三组。
const GENDER_OPTIONS = ["男", "女", "中性"];
const AGE_OPTIONS = ["儿童", "少年", "青年", "中年", "老年"];
const CULTURE_OPTIONS_MINE = ["东亚", "欧美", "中东", "非洲", "其他"];
const CULTURE_OPTIONS_OFFICIAL = ["东亚", "欧美", "中东", "非洲", "奇幻"];

// ★ 角色名 → 筛选标签（本地 mock；★ 非源站采样 ⟹ 只用于让筛选**真的能筛出东西**）
const tagsFor = (name: string) => {
  const gender = /女|母|千金|少女/.test(name)
    ? "女"
    : /男|父|大佬/.test(name)
      ? "男"
      : "中性";
  const age = /男孩|女孩/.test(name)
    ? "儿童"
    : /霸总|精英/.test(name)
      ? "中年"
      : /古风|长辈/.test(name)
        ? "老年"
        : "青年";
  const region = /欧美/.test(name)
    ? "欧美"
    : /古风/.test(name)
      ? "奇幻"
      : /亚洲/.test(name)
        ? "东亚"
        : "其他";
  return [gender, age, region];
};

const CREATE_SLOT = "__create__";
const CARD_WIDTH = 244;
const CARD_PITCH = 246;

export function CharacterLibraryPanel({
  onAddNode,
  onClose,
}: CharacterLibraryPanelProps) {
  // ★★ Batch 827：页签从旧的「公共角色库 / 合规素材库」改成源站当前的
  //   「**我的角色库**」/「**官方角色库**」。
  // ★★ 旧的第二页签（Seedance 合规素材库 ＋ 承诺书门）在源站**当前**构建里
  //   已经没有对应物 ⟹ ⟹ 本批**撤掉**（理由与影响见 batch 827 README）：
  //   ★ 承诺书门在源站 i18n 里是 `seedancePromise*`（《Seedance模型使用承诺书》）⟹
  //   ★ 它属于 **Seedance 生成流**，不属于角色库 ⟹ 归属问题单独记，不在面板里发明。
  const [tab, setTab] = useState<"mine" | "official">("mine");
  const [activeFilters, setActiveFilters] = useState<Record<string, string[]>>({});
  const [currentId, setCurrentId] = useState<string>(CREATE_SLOT);
  const [multiSelect, setMultiSelect] = useState(false);
  const [picked, setPicked] = useState<string[]>([]);
  const [view, setView] = useState<"carousel" | "grid">("carousel");
  const [searching, setSearching] = useState(false);
  const [keyword, setKeyword] = useState("");

  const viewportRef = useRef<HTMLDivElement | null>(null);
  // ★ 源站的 track 是 `absolute left-1/2` ⟹ **当前项永远居中**。
  //   这里用「左右对称 padding + 原生滚动」等价实现：
  //   padding = (视口宽 − 卡片宽) / 2 ⟹ scrollLeft = index × 246 时当前项正好居中
  //   （实测：源站官方页签「甜妹/清新少女」当前居中于 x=960，即 838..1082）。
  const [edgePad, setEdgePad] = useState(0);

  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport) return;
    const sync = () => {
      const pad = Math.max(0, (viewport.clientWidth - CARD_WIDTH) / 2);
      setEdgePad(pad);
    };
    sync();
    const observer = new ResizeObserver(sync);
    observer.observe(viewport);
    return () => observer.disconnect();
  }, [view]);

  const cultureOptions =
    tab === "mine" ? CULTURE_OPTIONS_MINE : CULTURE_OPTIONS_OFFICIAL;

  const filterGroups = useMemo(
    () => [
      { key: "性别", options: GENDER_OPTIONS },
      { key: "年龄段", options: AGE_OPTIONS },
      { key: "文化区域", options: cultureOptions },
    ],
    [cultureOptions],
  );

  const matches = (name: string) => {
    const tags = tagsFor(name);
    const byFilter = Object.entries(activeFilters).every(([, list]) =>
      list.length === 0 ? true : list.some((chip) => tags.includes(chip)),
    );
    const byKeyword =
      keyword.trim() === "" ? true : name.includes(keyword.trim());
    return byFilter && byKeyword;
  };

  const visible = characters.filter((character) => matches(character.name));

  // ★ 源站的 carousel 轨道是 `left-1/2` 整体居中，当前项被推到视口正中 ⟹
  //   这里用原生滚动 + `margin:0 auto` 等价实现：当前项居中、左右箭头翻页、
  //   底部滚动条驱动同一个 index。
  const items = useMemo(
    () => [
      { id: CREATE_SLOT, name: "创建新角色", imageUrl: null as string | null },
      ...visible.map((character) => ({
        id: character.id,
        name: character.name,
        imageUrl: character.imageUrl,
      })),
    ],
    [visible],
  );

  const currentIndex = Math.max(
    0,
    items.findIndex((item) => item.id === currentId),
  );
  const current = items[currentIndex];
  const isRealRole = Boolean(current && current.id !== CREATE_SLOT);

  // ★ 当前项改变 ⟹ 把它滚到视口正中（源站是 transform，这里是 scrollLeft）
  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport) return;
    viewport.scrollTo({
      left: Math.max(0, currentIndex * CARD_PITCH),
      behavior: "smooth",
    });
  }, [currentIndex, view, edgePad]);

  const toggleFilter = (group: string, option: string) => {
    setActiveFilters((current) => {
      const next = { ...current };
      const list = next[group] ?? [];
      next[group] = list.includes(option)
        ? list.filter((item) => item !== option)
        : [...list, option];
      return next;
    });
  };

  const clearFilter = (group: string) => {
    setActiveFilters((current) => ({ ...current, [group]: [] }));
  };

  const moveBy = (delta: number) => {
    const next = Math.min(items.length - 1, Math.max(0, currentIndex + delta));
    setCurrentId(items[next].id);
  };

  const switchTab = (next: "mine" | "official") => {
    setTab(next);
    setSearching(false);
    setKeyword("");
    setMultiSelect(false);
    setPicked([]);
    // ★ 源站切页签会把 carousel 移到对应列表的第一项 ⟹
    //   「我的角色库」落在「创建新角色」占位上、「官方角色库」落在第一个角色上
    setCurrentId(next === "mine" ? CREATE_SLOT : characters[0].id);
  };

  const addToCanvas = () => {
    if (!current || current.id === CREATE_SLOT) return;
    const character = characters.find((item) => item.id === current.id);
    if (!character) return;
    onAddNode("image", {
      filename: character.name,
      width: 568,
      height: 761,
      imageUrl: character.imageUrl,
      watermarkUrl: "/images/watermark.png",
    });
    onClose();
  };

  const togglePicked = (id: string) => {
    setPicked((current) =>
      current.includes(id)
        ? current.filter((item) => item !== id)
        : [...current, id],
    );
  };

  const allPicked =
    visible.length > 0 && visible.every((character) => picked.includes(character.id));

  return (
    <div className="cs-overlay">
      <section
        aria-label="角色造型室"
        data-liblib-overlay="primary:character"
        data-character-studio
        className="cs-modal"
        onMouseDown={(event) => event.stopPropagation()}
      >
        {/* ── 头部：两个页签 ＋ 关闭 ──
            ★ 源站实测：我的角色库 90×26 @385,183（18px/600 白）、
            官方角色库 90×26 @508,183（18px/600 白 60%）⟹ 未选中是 60% 白。
            ★ 两个页签之间有一条 1×12 的竖线（源站 `h-3 w-px`）。 */}
        <header className="cs-head">
          <button
            type="button"
            data-character-studio-tab="mine"
            onClick={() => switchTab("mine")}
            className={`cs-tab${tab === "mine" ? " is-active" : ""}`}
          >
            我的角色库
          </button>
          <span aria-hidden="true" className="cs-divider" />
          <button
            type="button"
            data-character-studio-tab="official"
            onClick={() => switchTab("official")}
            className={`cs-tab${tab === "official" ? " is-active" : ""}`}
          >
            官方角色库
          </button>
          <button
            type="button"
            onClick={onClose}
            aria-label="关闭角色造型室"
            className="cs-close"
          >
            <X size={16} />
          </button>
        </header>

        {/* ── 工具条 ──
            ★ 源站实测：性别 66×32 @381,231、年龄段 79×32 @453,231、
            文化区域 92×32 @538,231（间隙 6px）＋ 搜索按钮 32×32 @636,231；
            右侧 多选 32×32 @1438,231、列表模式 26×26 @1477,234、宫格模式 26×26 @1510,234。 */}
        <div className="cs-toolbar">
          <div className="cs-filters-left">
            {filterGroups.map((group) => {
              const pickedOptions = activeFilters[group.key] ?? [];
              const isActive = pickedOptions.length > 0;
              const pickedNames = group.options
                .filter((option) => pickedOptions.includes(option))
                .join("、");
              return (
                <details
                  key={group.key}
                  className="cs-pill"
                  data-character-filter={group.key}
                >
                  <summary
                    data-character-filter-summary={group.key}
                    className={`cs-summary${isActive ? " is-active" : ""}`}
                  >
                    {isActive ? (
                      <>
                        <span
                          role="button"
                          tabIndex={0}
                          aria-label="清除筛选"
                          data-character-filter-clear={group.key}
                          className="cs-summary-clear"
                          onClick={(event) => {
                            event.preventDefault();
                            event.stopPropagation();
                            clearFilter(group.key);
                          }}
                          onKeyDown={(event) => {
                            if (event.key === "Enter" || event.key === " ") {
                              event.preventDefault();
                              clearFilter(group.key);
                            }
                          }}
                        >
                          <X size={16} />
                        </span>
                        <span>{group.key}</span>
                        <span className="cs-summary-divider" />
                        <span>{pickedNames || pickedOptions.length}</span>
                      </>
                    ) : (
                      <>
                        <span>{group.key}</span>
                        <ChevronDown size={12} className="cs-chevron" />
                      </>
                    )}
                  </summary>
                  <div className="cs-panel" data-character-filter-panel={group.key}>
                    {group.options.map((option) => {
                      const on = pickedOptions.includes(option);
                      return (
                        <label
                          key={option}
                          data-character-filter-chip={option}
                          className="cs-opt"
                        >
                          <input
                            type="checkbox"
                            checked={on}
                            onChange={() => toggleFilter(group.key, option)}
                            className="cs-checkbox"
                          />
                          <span>{option}</span>
                          {on && <Check size={18} className="cs-check" />}
                        </label>
                      );
                    })}
                  </div>
                </details>
              );
            })}
            {searching ? (
              <label className="cs-search-field">
                <Search size={16} />
                <input
                  autoFocus
                  value={keyword}
                  onChange={(event) => setKeyword(event.target.value)}
                  onBlur={() => {
                    if (keyword === "") setSearching(false);
                  }}
                  placeholder="搜索角色名称或描述"
                  aria-label="搜索角色名称或描述"
                  className="cs-search-input"
                />
              </label>
            ) : (
              <button
                type="button"
                aria-label="搜索角色名称或描述"
                onClick={() => setSearching(true)}
                className="cs-icon-btn"
              >
                <Search size={16} />
              </button>
            )}
          </div>
          <div className="cs-toolbar-right">
            <button
              type="button"
              aria-label={multiSelect ? "退出多选" : "多选"}
              aria-pressed={multiSelect}
              onClick={() => {
                setMultiSelect((value) => !value);
                setPicked([]);
              }}
              className="cs-icon-btn"
            >
              <SlidersHorizontal size={16} />
            </button>
            <div className="cs-segment">
              <button
                type="button"
                aria-label="列表模式"
                aria-pressed={view === "carousel"}
                onClick={() => setView("carousel")}
                className={`cs-seg-btn${view === "carousel" ? " is-active" : ""}`}
              >
                <List size={16} />
              </button>
              <span aria-hidden="true" className="cs-seg-div" />
              <button
                type="button"
                aria-label="宫格模式"
                aria-pressed={view === "grid"}
                onClick={() => setView("grid")}
                className={`cs-seg-btn${view === "grid" ? " is-active" : ""}`}
              >
                <Grid2x2 size={16} />
              </button>
            </div>
          </div>
        </div>

        {/* ── 内容区 ──
            ★ 源站实测：卡片图 244×434 @y=321（轨道 pitch 246）；
            ★ 选中的角色名**居中**在轨道下方 @y=783（名字 + 一枚 26×26 快捷操作）。 */}
        <div className="cs-content">
          {view === "carousel" ? (
            <>
              <div className="cs-viewport" ref={viewportRef}>
                <div
                  className="cs-track"
                  data-character-strip
                  style={{
                    paddingLeft: edgePad,
                    paddingRight: edgePad,
                  }}
                >
                  <button
                    type="button"
                    data-character-studio-create
                    onClick={() => setCurrentId(CREATE_SLOT)}
                    className="cs-create-card"
                  >
                    <UserPlus size={42} strokeWidth={1.2} />
                    <span>创建新角色</span>
                  </button>
                  {visible.map((character) => {
                    const on = current.id === character.id;
                    return (
                      <button
                        key={character.id}
                        type="button"
                        data-character-strip-card={character.name}
                        onClick={() => {
                          if (multiSelect) {
                            togglePicked(character.id);
                            return;
                          }
                          setCurrentId(character.id);
                        }}
                        className="cs-card"
                      >
                        <span className="cs-card-img">
                          <Image
                            src={character.imageUrl}
                            alt={character.name}
                            fill
                            sizes="244px"
                            className="cs-img"
                            unoptimized
                          />
                          {multiSelect && (
                            <span
                              className={`cs-pick${picked.includes(character.id) ? " is-on" : ""}`}
                            >
                              <Check size={14} />
                            </span>
                          )}
                          {on && !multiSelect && (
                            <span
                              data-character-studio-view-assets
                              className="cs-assets"
                            >
                              <ImageIcon size={16} />
                              查看角色资产
                            </span>
                          )}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
              <div className="cs-name-group">
                <span className="cs-name" data-character-studio-name>
                  {current?.name ?? ""}
                </span>
                {isRealRole && (
                  <button
                    type="button"
                    aria-label="生成其他年龄版本"
                    data-character-studio-quick
                    className="cs-quick"
                  >
                    <UserPlus size={16} />
                  </button>
                )}
              </div>
              <button
                type="button"
                aria-label="上一组角色"
                disabled={currentIndex <= 0}
                onClick={() => moveBy(-1)}
                className="cs-arrow cs-arrow-left"
              >
                <ChevronLeft size={18} />
              </button>
              <button
                type="button"
                aria-label="下一组角色"
                disabled={currentIndex >= items.length - 1}
                onClick={() => moveBy(1)}
                className="cs-arrow cs-arrow-right"
              >
                <ChevronRight size={18} />
              </button>
              <input
                type="range"
                aria-label="角色列表"
                min={0}
                max={Math.max(0, items.length - 1)}
                step={1}
                value={currentIndex}
                onChange={(event) => {
                  const next = Number(event.target.value);
                  setCurrentId(items[next]?.id ?? CREATE_SLOT);
                }}
                className="cs-range"
              />
            </>
          ) : (
            <div className="cs-grid">
              <section className="cs-grid-section">
                <h2 className="cs-grid-title">我的角色库</h2>
                <div className="cs-grid-row">
                  {visible.map((character) => (
                    <button
                      key={character.id}
                      type="button"
                      data-character-grid-card={character.name}
                      onClick={() => {
                        if (multiSelect) {
                          togglePicked(character.id);
                          return;
                        }
                        setCurrentId(character.id);
                      }}
                      className="cs-grid-card"
                    >
                      <span className="cs-card-img">
                        <Image
                          src={character.imageUrl}
                          alt={character.name}
                          fill
                          sizes="172px"
                          className="cs-img"
                          unoptimized
                        />
                      </span>
                      <span className="cs-card-name">{character.name}</span>
                    </button>
                  ))}
                </div>
              </section>
            </div>
          )}
        </div>

        {/* ── 底部：三种形态 ──
            ★ 源站实测（我的角色库页签）：居中单枚白底「创建新角色」116×40 @902,856；
            ★ 源站实测（官方角色库页签）：左侧「创建新角色」120×40 @385,856（ghost）
            ★ ＋ 居中一组 [「添加到画布」120×40 @843,856（ghost），
            ★ 「编辑角色」106×40 @971,856（白底 primary）]，两枚之间间隙 8px。 */}
        <footer className="cs-footer">
          {multiSelect ? (
            <>
              <button
                type="button"
                role="checkbox"
                aria-checked={allPicked}
                aria-label="全选"
                onClick={() =>
                  setPicked(allPicked ? [] : visible.map((item) => item.id))
                }
                className="cs-selectall"
              >
                <span className={`cs-selectall-box${allPicked ? " is-on" : ""}`}>
                  <Check size={14} />
                </span>
                {picked.length > 0
                  ? `已选中 ${picked.length} 位角色`
                  : `全选共 ${visible.length} 位角色`}
              </button>
              <button
                type="button"
                disabled={picked.length === 0}
                onClick={() => {
                  setPicked([]);
                  setMultiSelect(false);
                }}
                className="cs-cta is-danger"
              >
                删除角色
              </button>
            </>
          ) : isRealRole ? (
            <>
              <button
                type="button"
                data-character-studio-cta="create"
                onClick={() => setCurrentId(CREATE_SLOT)}
                className="cs-cta is-ghost cs-cta-left"
              >
                <Plus size={18} />
                创建新角色
              </button>
              <div className="cs-cta-group">
                <button
                  type="button"
                  data-character-studio-cta="add-to-canvas"
                  onClick={addToCanvas}
                  className="cs-cta is-soft"
                >
                  <ImageIcon size={18} />
                  添加到画布
                </button>
                <button
                  type="button"
                  data-character-studio-cta="edit"
                  onClick={() => undefined}
                  className="cs-cta is-primary"
                >
                  <UserPlus size={18} />
                  编辑角色
                </button>
              </div>
            </>
          ) : (
            <button
              type="button"
              data-character-studio-cta="create"
              onClick={() => setCurrentId(CREATE_SLOT)}
              className="cs-cta is-primary is-solo"
            >
              <UserPlus size={18} />
              创建新角色
            </button>
          )}
        </footer>
      </section>
    </div>
  );
}
