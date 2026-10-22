"use client";

import {
  Ban,
  Check,
  ChevronLeft,
  CircleDot,
  Columns2,
  Eye,
  Music,
  Palette,
  PersonStanding,
  Redo2,
  Shirt,
  Smile,
  Sparkles,
  Undo2,
  User,
  Wand2,
  Zap,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useUIStore } from "@/store/uiStore";
import "./character-studio.css";

// ═══════════════════════════════════════════════════════════════════
// ★★ Batch 840：**角色大编辑器**（源站「编辑角色」点开的那一层）
// ───────────────────────────────────────────────────────────────────
// ★★ 几何与文案**逐条照抄**源站活体实测（2026-10-22，1920×1080）：
//   模态        1198×758 @361,161（内容行 1198×602 @rel(0,70)；底栏 1198×88 @rel(0,672)）
//   左列        288×602：标题输入 216×32 ＋ 标签行 ＋ 五段（240×44）＋ 三枚 32×32 工具
//   预览区      624×602：角色图 467×550 ＋ 半身/全身（32×32）
//   右栏        288×602：页签行 288×40（首枚带文字 56 宽，余 24 宽）
//                        ＋ 皮肤页签下六条滑杆（标签 ＋ 240×12 轨道 ＋ 右端数值）
//                        ＋ 祛斑祛痘（32×18 开关）＋ 确认生成 196×36 ＋ 智能调整 36×36
//   底栏        「保存时生成角色资产 ⚡44」＋ 保存 80×40 ＋ 保存并添加到画布 144×40
//
// ★★ **哪些是实测、哪些是 clone 决策**（README 与台账如实标注）：
//   实测照抄：模态/三列/五段/页签/六滑杆/开关/按钮/底栏的**几何与文案**。
//   clone 决策：
//     ① 右栏另外五枚页签（眉眼/鼻子/嘴唇/脸部/妆造）的**控件内容未实测**
//        ⟹ ⟹ 点它们显示**空态说明**，**不编造**控件（页签本身的 24×39 盒与文案是实测）；
//     ② 那五枚页签的**图标**用 lucide 占位（源站是 iconify SVG，未采集其字形）；
//     ③ 「确认生成」「智能调整」「保存并添加到画布」是 **mock**
//        （源站的「确认生成」会**消耗 ⚡44 真实积分** ⟹ clone 不做、也不假装）；
//     ④ 「保存」是**真的**：把标题输入框里的名字改到角色身上 ＋ 关闭编辑器。
// ═══════════════════════════════════════════════════════════════════

interface Segment {
  id: string;
  label: string;
  badge: string | null;
  icon: typeof Wand2;
}

// ★★ 源站实测：每一段按钮的**文案左边有 18px 的图标**（按钮 px-3 ⟹ 内边距 12；
//   文字落在 rel 48 ⟹ 12 + 18 + gap 6 = 36 ⟹ 按钮起点 rel 12 + 36 = 48 ✓）
//   ⟹ clone 也放一枚 18×18 图标 ⟹ 文案与「限免」徽标才会落在源站的同一像素上。
//   ★ 图标**字形未采集**（源站是 iconify SVG）⟹ 这里用 lucide 占位（与右栏页签同一处理）。
const SEGMENTS: Segment[] = [
  { id: "face", label: "脸部精修", badge: "限免", icon: Wand2 },
  { id: "traits", label: "脸部 & 身体特征", badge: null, icon: User },
  { id: "body", label: "身材塑形", badge: "限免", icon: PersonStanding },
  { id: "outfit", label: "服装造型", badge: null, icon: Shirt },
  { id: "voice", label: "音色音调", badge: null, icon: Music },
];

interface Tab {
  id: string;
  label: string;
  icon: typeof Eye;
}

// ★ 源站实测：页签行里**当前选中的那枚**才是「图标 + 文字」（56 宽），
//   其余五枚**只有图标**（24 宽）⟹ ⟹ 「文字页签」会**跟着选中项移动**。
//   ★ batch 840 之前 clone 把 56 宽的**文字页签固定在首枚** ⟹ 选中别枚时几何就与源站不符 ⟹ 本批改正。
//   ★ 图标**字形未采集**（源站是 iconify SVG）⟹ 这里用 lucide 占位。
const TABS: Tab[] = [
  { id: "skin", label: "皮肤", icon: Sparkles },
  { id: "brow-eye", label: "眉眼", icon: Eye },
  { id: "nose", label: "鼻子", icon: CircleDot },
  { id: "lips", label: "嘴唇", icon: Smile },
  { id: "face", label: "脸部", icon: User },
  { id: "makeup", label: "妆造", icon: Palette },
];

interface Slider {
  id: string;
  label: string;
  info: boolean;
}

// ★★ Batch 841：各页签的**实测滑杆清单**
//   （源站 2026-10-22 **只读**探针，raw 入库在
//    `docs/research/liblib-canvas-batch841-2026-10-01/raw/source-841-tabs.json`）
//
// ★★ **几何规律**（源站实测，三枚纯滑杆页签完全一致）：
//   标签  rel y = 130 + 74.8·i（高 22，左端 rel 936）
//   轨道  = 标签 +36（240 × 12）
//   数值  = 标签 +3（7 × 16，右端对齐到 1176）
//   「i」 = 标签右端 +6、标签顶 +4（14 × 14）
//   ⟹ ⟹ clone 用同一套 `.ce-slider-*` 规则即可 ⟹ ⟹ **不需要每页单独写坐标**。
//
// ★ **哪些页签**已实现：**皮肤**（batch 840）／**鼻子**／**嘴唇**／**脸部**（本批）。
//   ★ **眉眼／妆造**仍显示空态说明 —— 它们除了滑杆，还含**预设网格**
//   （76×96 的卡片，带缩略图）⟹ ⟹ 属后续批次 ⟹ ⟹ 本批**不编造**。
const TAB_SLIDERS: Record<string, Slider[]> = {
  skin: [
    { id: "texture", label: "质感磨皮", info: false },
    { id: "beauty", label: "AI 美颜（脸部）", info: true },
    { id: "grain", label: "皮肤纹理（脸部）", info: false },
    { id: "bright", label: "皮肤透亮", info: false },
    { id: "ruddy", label: "皮肤红润", info: false },
    { id: "whiten", label: "皮肤美白", info: false },
  ],
  nose: [
    { id: "nose-root", label: "山根", info: false },
    { id: "nose-bridge", label: "鼻梁", info: false },
    { id: "nose-tip", label: "鼻尖", info: false },
    { id: "nose-length", label: "鼻子长短", info: false },
    { id: "nose-size", label: "鼻子大小", info: false },
    { id: "nose-wing", label: "鼻翼", info: false },
  ],
  lips: [
    { id: "lips-updown", label: "嘴巴上下", info: false },
    { id: "lips-lower-full", label: "丰下唇", info: false },
    { id: "lips-width", label: "嘴巴宽度", info: false },
    { id: "lips-full", label: "丰唇", info: false },
    { id: "lips-corner", label: "嘴角调整", info: false },
    { id: "lips-tilt", label: "嘴巴倾斜", info: false },
    { id: "lips-size", label: "嘴巴大小", info: false },
    { id: "lips-upper-full", label: "丰上唇", info: false },
    { id: "lips-wrinkle", label: "祛唇纹", info: true },
    { id: "lips-makeup", label: "唇妆增强", info: false },
  ],
  face: [
    { id: "face-forehead", label: "额头", info: false },
    { id: "face-v", label: "V 脸", info: false },
    { id: "face-contour", label: "脸部轮廓流畅", info: true },
    { id: "face-small", label: "小脸", info: false },
    { id: "face-width", label: "脸部宽度", info: false },
    { id: "face-chin-height", label: "下巴高度", info: false },
    { id: "face-jaw-l", label: "下颌（左）", info: false },
    { id: "face-jaw-r", label: "下颌（右）", info: false },
    { id: "face-cheekbone-l", label: "颧骨（左）", info: false },
    { id: "face-cheekbone-r", label: "颧骨（右）", info: false },
    { id: "face-temple-l", label: "太阳穴（左）", info: false },
    { id: "face-temple-r", label: "太阳穴（右）", info: false },
    { id: "face-midface", label: "中庭", info: false },
    { id: "face-lowerface", label: "下庭", info: false },
    { id: "face-philtrum", label: "人中", info: false },
  ],
};

// ★★ Batch 842：「眉眼」页 —— 它**不是**一列滑杆，而是**分块**布局
//   （源站**只读**实测；raw 在 batch 841 的 `raw/source-841-tabs.json`
//    ＋ batch 842 的 `raw/source-842-brow.json`）
//
// ★★ **结构**（源站实测；top 一律相对右栏滚动区内容起点 ＝ 源站 abs y − 271）：
//   H3「眼睛」240×20 @top 20（13px/500，色 rgba(255,255,255,0.3)）
//     └ 19 条滑杆：标签 top = 60 + 74.8·i（祛黑眼圈带「i」标记）
//   H4「眼神光」240×22 @top 1481（14px/500，白色，**带**「i」）＋ 11 张眼型预设卡
//     └ 卡片 76×96：76×76 媒体区（radius 16、底色 rgba(255,255,255,0.06)）＋ gap 4 ＋ 名字
//       （3 列 × 4 行；步进 82／104；「无」那张**没有缩略图**，只有一枚 18×18 图标）
//   H3「眉毛」240×20 @top 1947
//     └ 11 条滑杆：标签 top = 1987 + 74.8·j
//
// ★★ **更正 batch 841 的一处数字**：眉眼页是 **30 条**滑杆（19 ＋ 11），
//   而 841 的 README 写的是「32 条」⟹ ⟹ 那两个多出来的是**「角色名称」输入框**
//   与一个 1×1 的复选框（都不是滑杆）⟹ ⟹ 本批更正（详见 batch 842 的 README）。
//
// ★ **缩略图没复刻**：源站的眼型卡用的是素材库里的**真实眼型图**
//   （`libtv-res.liblib.art/.../eye-light/*.jpg`）⟹ ⟹ 仓库里没有 ⟹ ⟹
//   本批用**中性占位块**，只对齐**盒与文案**（★ 不声称缩略图复刻）。
const BROW_EYE_EYE_SLIDERS: Slider[] = [
  { id: "eye-dark-circle", label: "祛黑眼圈", info: true },
  { id: "eye-bright-l", label: "亮眼（左）", info: false },
  { id: "eye-bright-r", label: "亮眼（右）", info: false },
  { id: "eye-size-l", label: "眼睛大小（左）", info: false },
  { id: "eye-size-r", label: "眼睛大小（右）", info: false },
  { id: "eye-width-l", label: "眼宽（左）", info: false },
  { id: "eye-width-r", label: "眼宽（右）", info: false },
  { id: "eye-height-l", label: "眼高（左）", info: false },
  { id: "eye-height-r", label: "眼高（右）", info: false },
  { id: "eye-distance-l", label: "眼距（左）", info: false },
  { id: "eye-distance-r", label: "眼距（右）", info: false },
  { id: "eye-lid-l", label: "眼睑-左", info: false },
  { id: "eye-lid-r", label: "眼睑-右", info: false },
  { id: "eye-tilt-l", label: "眼睛倾斜-左", info: false },
  { id: "eye-tilt-r", label: "眼睛倾斜-右", info: false },
  { id: "eye-corner-l", label: "开眼角-左", info: false },
  { id: "eye-corner-r", label: "开眼角-右", info: false },
  { id: "eye-updown-l", label: "眼睛上下-左", info: false },
  { id: "eye-updown-r", label: "眼睛上下-右", info: false },
];

const BROW_EYE_BROW_SLIDERS: Slider[] = [
  { id: "brow-gap-l", label: "眉毛间距（左）", info: false },
  { id: "brow-gap-r", label: "眉毛间距（右）", info: false },
  { id: "brow-updown-l", label: "眉毛上下（左）", info: false },
  { id: "brow-updown-r", label: "眉毛上下（右）", info: false },
  { id: "brow-peak-l", label: "眉峰（左）", info: false },
  { id: "brow-peak-r", label: "眉峰（右）", info: false },
  { id: "brow-thick-l", label: "眉毛粗细（左）", info: false },
  { id: "brow-thick-r", label: "眉毛粗细（右）", info: false },
  { id: "brow-tilt-l", label: "眉毛倾斜（左）", info: false },
  { id: "brow-tilt-r", label: "眉毛倾斜（右）", info: false },
  { id: "brow-boost", label: "眉毛增强", info: false },
];

// ★ 眼型预设卡（源站 aria-label 逐条照抄；「无」那张**没有**缩略图）
const BROW_EYE_CARD_NAMES = [
  "无", "氧气", "清澈", "神采", "秋水", "灵动",
  "水光", "聚焦", "透亮", "星光", "通透",
];

// ★ 一页右栏的**块序列**（绝对定位；top 相对滚动区内容起点）
type PanelBlock =
  | { kind: "h3"; text: string; top: number }
  | { kind: "h4"; text: string; top: number }
  | { kind: "sliders"; top: number; items: Slider[] }
  | { kind: "cards"; top: number; names: string[] };

const TAB_BLOCKS: Record<string, PanelBlock[]> = {
  "brow-eye": [
    { kind: "h3", text: "眼睛", top: 20 },
    { kind: "sliders", top: 60, items: BROW_EYE_EYE_SLIDERS },
    { kind: "h4", text: "眼神光", top: 1481 },
    { kind: "cards", top: 1511, names: BROW_EYE_CARD_NAMES },
    { kind: "h3", text: "眉毛", top: 1947 },
    { kind: "sliders", top: 1987, items: BROW_EYE_BROW_SLIDERS },
  ],
};

// ★ 滑杆六行的**纵向偏移**（源站实测的标签盒 top，相对右栏滚动区内容起点）
const SLIDER_STEP = 74.8;

// ★★ 所有滑杆的 id（值表的初值）—— **分页签的** ＋ **分块的**
const ALL_SLIDERS: Slider[] = [
  ...Object.values(TAB_SLIDERS).flat(),
  ...Object.values(TAB_BLOCKS).flatMap((blocks) =>
    blocks.flatMap((b) => (b.kind === "sliders" ? b.items : [])),
  ),
];

// ★★ **未实现**页签的空态说明（**逐页**写，别用一句通用文案）
//   ★ 措辞必须对得上**已实测到的事实** ⟹ ⟹ 妆造页是「11 个分类 chip ＋ 13 张妆容预设卡」
//   ⟹ ⟹ 再说「除了滑杆还含预设网格」就是**假陈述**。
const EMPTY_NOTE: Record<string, string> = {
  makeup:
    "「妆造」这一页签的控件 **已实测**（源站 raw 入库在 batch 841／842），" +
    "但它是 **11 个分类 chip ＋ 13 张妆容预设卡**（76×96 的卡片，带缩略图）" +
    "⟹ ⟹ 属后续批次 ⟹ ⟹ 这里不编造控件，只如实说明。",
};

export interface CharacterEditorPanelProps {
  characterId: string;
  characterName: string;
  imageUrl: string;
  gender: string;
  age: string;
  region: string;
  onClose: () => void;
  onSave: (name: string) => void;
}

export function CharacterEditorPanel({
  characterId,
  characterName,
  imageUrl,
  gender,
  age,
  region,
  onClose,
  onSave,
}: CharacterEditorPanelProps) {
  const setCharacterEditorId = useUIStore((state) => state.setCharacterEditorId);

  const [segment, setSegment] = useState(SEGMENTS[0].id);
  const [tab, setTab] = useState(TABS[0].id);
  const [values, setValues] = useState<Record<string, number>>(
    Object.fromEntries(ALL_SLIDERS.map((s) => [s.id, 0])),
  );
  const [spot, setSpot] = useState(false);
  // ★★ Batch 842：眼型预设卡的**选中态**（源站默认选中「无」⟹ aria-pressed=true）
  const [cardSel, setCardSel] = useState("无");
  const [framing, setFraming] = useState<"half" | "full">("half");
  const [name, setName] = useState(characterName);
  const [genAssets, setGenAssets] = useState(true);
  const [notice, setNotice] = useState<string | null>(null);

  const rootRef = useRef<HTMLDivElement | null>(null);
  const noticeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ★ 把焦点收进编辑器（否则键盘事件落在画布上）
  useEffect(() => {
    rootRef.current?.focus();
  }, [characterId]);

  useEffect(() => () => {
    if (noticeTimer.current) clearTimeout(noticeTimer.current);
  }, []);

  const flash = (text: string) => {
    setNotice(text);
    if (noticeTimer.current) clearTimeout(noticeTimer.current);
    noticeTimer.current = setTimeout(() => setNotice(null), 2600);
  };

  // ★ 标签行：源站实测是「♀ · 青年 · 东亚 · 现代」（♀ 是图标，不是文本）
  const tagText = `· ${age} · ${region} · 现代`;

  // ★★ Batch 841：当前页签的**实测滑杆清单**（没有 ⟹ 显示空态说明）
  const currentSliders = TAB_SLIDERS[tab] ?? null;

  // ★★ Batch 842：当前页签的**块序列**（眉眼页是分块布局 ⟹ 走这条）
  const currentBlocks = TAB_BLOCKS[tab] ?? null;

  // ★ 一条滑杆行（标签 ＋ 轨道 ＋ 数值）—— 各页签**共用同一套**几何规则：
  //   标签 top = 20 + i·74.8（相对右栏内容区 ⟹ 绝对 rel 130 + 74.8·i）
  //   轨道 = 标签 +36（240×12）｜ 数值 = 标签 +3（7×16，右端对齐到 1176）
  // ★ `baseTop` 给的是**绝对** top（眉眼页的分段布局：源站逐段实测各不相同）
  const renderSlider = (item: Slider, index: number, baseTop?: number) => {
    const top = baseTop ?? 20 + index * SLIDER_STEP;
    return (
      <div key={item.id}>
        <label
          className="ce-slider-label"
          style={{ top: `${top}px` }}
          data-character-editor-slider-label={item.id}
        >
          <span className="ce-slider-label-text">{item.label}</span>
          {item.info ? (
            <span
              className="ce-info"
              role="img"
              aria-label="该调整不支持预览，需要生成后生效"
            >
              i
            </span>
          ) : null}
        </label>
        <input
          type="range"
          className="ce-slider"
          style={{ top: `${top + 36}px` }}
          min={0}
          max={100}
          step={1}
          value={values[item.id]}
          data-character-editor-slider={item.id}
          aria-label={item.label}
          onChange={(event) =>
            setValues((prev) => ({
              ...prev,
              [item.id]: Number(event.target.value),
            }))
          }
        />
        <span
          className="ce-slider-value"
          style={{ top: `${top + 3}px` }}
          data-character-editor-slider-value={item.id}
        >
          {values[item.id]}
        </span>
      </div>
    );
  };

  // ★★ 一张**预设卡**（源站眼型卡：76×96 ＝ 76×76 媒体区 ＋ gap 4 ＋ 名字）
  //   媒体区：radius 16、底色 rgba(255,255,255,0.06)、1px 边框（选中那枚是白边）
  //   「无」那张**没有缩略图**（源站是一枚 18×18 的图标）⟹ ⟹ 这里用 lucide 占位
  //   其余十张：源站是素材库里的**真实眼型图** ⟹ ⟹ 仓库里没有 ⟹ ⟹ **中性占位块**
  const renderCard = (name: string, index: number, baseTop: number) => {
    const col = index % 3;
    const row = Math.floor(index / 3);
    const on = cardSel === name;
    return (
      <button
        key={name}
        type="button"
        aria-label={name}
        aria-pressed={on}
        className={`ce-card${on ? " is-on" : ""}`}
        style={{ top: `${baseTop + row * 104}px`, left: `${24 + col * 82}px` }}
        data-character-editor-card={name}
        onClick={() => setCardSel((prev) => (prev === name ? "" : name))}
      >
        <span className="ce-card-media">
          {name === "无" ? (
            <span className="ce-card-none" aria-hidden="true">
              <Ban size={18} />
            </span>
          ) : (
            <span
              className="ce-card-thumb"
              data-character-editor-card-thumb={name}
            />
          )}
        </span>
        <span
          className="ce-card-name"
          data-character-editor-card-name={name}
        >
          {name}
        </span>
      </button>
    );
  };

  // ★★ 一个**块**（标题／预设卡组／滑杆组）
  const renderBlock = (block: PanelBlock, index: number) => {
    if (block.kind === "h3") {
      return (
        <h3
          key={`h3-${index}`}
          className="ce-h3"
          style={{ top: `${block.top}px` }}
          data-character-editor-h3={block.text}
        >
          {block.text}
        </h3>
      );
    }
    if (block.kind === "h4") {
      return (
        <h4
          key={`h4-${index}`}
          className="ce-h4"
          style={{ top: `${block.top}px` }}
          data-character-editor-h4={block.text}
        >
          <span>{block.text}</span>
          <span
            className="ce-info"
            role="img"
            aria-label="该调整不支持预览，需要生成后生效"
          >
            i
          </span>
        </h4>
      );
    }
    if (block.kind === "sliders") {
      return (
        <div key={`sl-${index}`}>
          {block.items.map((item, i) =>
            renderSlider(item, i, block.top + i * SLIDER_STEP),
          )}
        </div>
      );
    }
    return (
      <div key={`cd-${index}`}>
        {block.names.map((name, i) => renderCard(name, i, block.top))}
      </div>
    );
  };

  return (
    <div className="ce-overlay" data-character-editor-overlay>
      <section
        ref={rootRef}
        className="ce-modal"
        data-character-editor={characterId}
        role="dialog"
        aria-modal="true"
        aria-label="角色编辑器"
        tabIndex={-1}
        // ★★ 焦点在**标题输入框**里时，画布那套键盘契约对**可编辑目标**是**早退**的
        //   （`isLibTVEditableCommandTarget` ⟹ return）⟹ ⟹ Esc 到不了 store ⟹
        //   ⟹ 大编辑器**自己**处理 Esc（★ 这一层不与全局那层冲突：
        //   全局那层在可编辑目标上**什么都不做**）。
        onKeyDown={(event) => {
          if (event.key !== "Escape") return;
          event.preventDefault();
          event.stopPropagation();
          setCharacterEditorId(null);
        }}
      >
        {/* ── 头部：返回按钮（源站实测 26×26 @rel(16,24)，aria-label=返回） ── */}
        <button
          type="button"
          className="ce-back"
          aria-label="返回"
          onClick={onClose}
        >
          <ChevronLeft size={16} />
        </button>

        {/* ── 内容行：左列 ＋ 预览 ＋ 右栏 ───────────────────────── */}
        <div className="ce-body">
          <aside className="ce-col ce-col-left">
            <input
              className="ce-name-input"
              data-character-editor-name
              aria-label="角色名称"
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
            <div className="ce-tags" data-character-editor-tags>
              <span className="ce-tag-gender" aria-hidden="true">
                {gender === "男" ? "♂" : gender === "女" ? "♀" : "⚲"}
              </span>
              <span className="ce-tag-text" data-character-editor-tag-text>
                {tagText}
              </span>
            </div>

            {SEGMENTS.map((item, index) => (
              <button
                key={item.id}
                type="button"
                className={`ce-seg${segment === item.id ? " is-on" : ""}`}
                data-character-editor-segment={item.id}
                style={{ top: `${98 + index * 52}px` }}
                onClick={() => setSegment(item.id)}
              >
                <span className="ce-seg-icon" aria-hidden="true">
                  <item.icon size={18} />
                </span>
                <span className="ce-seg-text">{item.label}</span>
                {item.badge ? (
                  <span className="ce-badge">{item.badge}</span>
                ) : null}
              </button>
            ))}

            <button
              type="button"
              className="ce-tool"
              style={{ left: 17 }}
              aria-label="撤销"
              onClick={() => flash("clone mock：撤销未接真实历史栈")}
            >
              <Undo2 size={18} />
            </button>
            <button
              type="button"
              className="ce-tool"
              style={{ left: 49 }}
              aria-label="恢复"
              onClick={() => flash("clone mock：恢复未接真实历史栈")}
            >
              <Redo2 size={18} />
            </button>
            <button
              type="button"
              className="ce-tool"
              style={{ left: 90 }}
              aria-label="按住对比"
              onClick={() => flash("clone mock：按住对比未接真实对比图")}
            >
              <Columns2 size={18} />
            </button>
          </aside>

          <main className="ce-preview">
            <div className="ce-figure">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={imageUrl} alt={name} />
            </div>
            <div className="ce-preview-fade" />
            <div className="ce-preview-tools">
              <button
                type="button"
                className={`ce-tool${framing === "half" ? " is-on" : ""}`}
                aria-label="半身"
                onClick={() => setFraming("half")}
              >
                <User size={18} />
              </button>
              <button
                type="button"
                className={`ce-tool${framing === "full" ? " is-on" : ""}`}
                aria-label="全身"
                onClick={() => setFraming("full")}
              >
                <Sparkles size={18} />
              </button>
            </div>
          </main>

          <aside className="ce-col ce-col-right">
            <div className="ce-tabs" role="tablist">
              {TABS.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  role="tab"
                  aria-selected={tab === item.id}
                  aria-label={item.label}
                  className={`ce-tab ${tab === item.id ? "is-text" : "is-icon"}${
                    tab === item.id ? " is-on" : ""
                  }`}
                  data-character-editor-tab={item.id}
                  onClick={() => setTab(item.id)}
                >
                  <span className="ce-tab-icon" aria-hidden="true">
                    <item.icon size={18} />
                  </span>
                  {tab === item.id ? (
                    <span className="ce-tab-text">{item.label}</span>
                  ) : null}
                </button>
              ))}
            </div>

            {currentBlocks ? (
              // ★★ Batch 842：**分块**布局（眉眼页：H3 ＋ 滑杆组 ＋ H4 ＋ 卡片组 ＋ H3 ＋ 滑杆组）
              <div className="ce-panel">
                <div className="ce-section">
                  {currentBlocks.map(renderBlock)}
                </div>
              </div>
            ) : currentSliders ? (
              <div className="ce-panel">
                <div className="ce-section">
                  {currentSliders.map((item, index) => renderSlider(item, index))}

                  {tab === "skin" ? (
                    <div
                      className="ce-switch-row"
                      style={{ top: 469 }}
                      data-character-editor-switch-row="spot"
                    >
                      <span className="ce-switch-label">
                        <span className="ce-switch-label-text">祛斑祛痘</span>
                        <span
                          className="ce-info"
                          role="img"
                          aria-label="该调整不支持预览，需要生成后生效"
                        >
                          i
                        </span>
                      </span>
                      <button
                        type="button"
                        role="switch"
                        aria-checked={spot}
                        aria-label="祛斑祛痘"
                        className={`ce-switch${spot ? " is-on" : ""}`}
                        data-character-editor-switch="spot"
                        onClick={() => setSpot((prev) => !prev)}
                      >
                        <span className="ce-switch-thumb" />
                      </button>
                    </div>
                  ) : null}
                </div>
              </div>
            ) : (
              <div className="ce-panel">
                <p className="ce-empty" data-character-editor-empty>
                  {EMPTY_NOTE[tab] ??
                    `「${TABS.find((item) => item.id === tab)?.label}」这一页签的控件 ` +
                      "**已实测**（源站 raw 入库在 batch 841），但它含**预设网格**" +
                      "（76×96 的卡片，带缩略图）⟹ ⟹ 属后续批次 ⟹ ⟹ 这里不编造控件，只如实说明。"}
                </p>
              </div>
            )}

            <div className="ce-generate-row">
              <button
                type="button"
                className="ce-generate"
                data-character-editor-generate
                onClick={() =>
                  flash("clone mock：确认生成不消耗积分，也不产出真实资产")
                }
              >
                {/* ★ 源站实测：文案左侧有一枚 16×16 的图标（字形未采集）
                    ⟹ 按钮内容 = [16px 图标][gap 4][64px 文案] ⟹ 居中后文案落在 rel 1012 */}
                <Zap size={18} />
                <span className="ce-generate-text">确认生成</span>
              </button>
              <button
                type="button"
                className="ce-smart"
                aria-label="智能调整"
                data-character-editor-smart
                onClick={() => flash("clone mock：智能调整未接真实算法")}
              >
                <Sparkles size={18} />
              </button>
            </div>
          </aside>
        </div>

        {/* ── 底栏 ───────────────────────────────────────────────── */}
        <footer className="ce-footer">
          <label className="ce-gen-assets" data-character-editor-gen-assets>
            <input
              type="checkbox"
              className="sr-only"
              checked={genAssets}
              onChange={(event) => setGenAssets(event.target.checked)}
            />
            <span
              className={`ce-checkbox${genAssets ? "" : " is-off"}`}
              aria-hidden="true"
            >
              {genAssets ? <Check size={12} /> : null}
            </span>
            <span data-character-editor-gen-assets-label>保存时生成角色资产</span>
            <span className="ce-credits">
              <span
                className="ce-credit-bolt"
                data-character-editor-credit-bolt
                aria-hidden="true"
              >
                ⚡
              </span>
              <span className="ce-credit-num" data-character-editor-credit-num>
                44
              </span>
            </span>
          </label>

          <div className="ce-footer-actions">
            <button
              type="button"
              className="ce-save"
              data-character-editor-save
              onClick={() => {
                onSave(name);
                setCharacterEditorId(null);
              }}
            >
              保存
            </button>
            <button
              type="button"
              className="ce-save is-primary"
              data-character-editor-save-add
              onClick={() => flash("clone mock：未真的把角色加入画布")}
            >
              保存并添加到画布
            </button>
          </div>
        </footer>

        {notice ? (
          <div className="ce-notice" data-character-editor-notice>
            {notice}
          </div>
        ) : null}
      </section>
    </div>
  );
}
