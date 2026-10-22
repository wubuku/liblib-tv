"use client";

import {
  Ban,
  Check,
  ChevronDown,
  ChevronLeft,
  CircleDot,
  Columns2,
  Eye,
  ImagePlus,
  Music,
  Package,
  Palette,
  PersonStanding,
  Play,
  Plus,
  Redo2,
  Search,
  Shirt,
  SlidersHorizontal,
  Smile,
  Sparkles,
  Undo2,
  User,
  Wand2,
  Zap,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { CSSProperties } from "react";
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
  // ★★ Batch 845：源站有 **5 条**滑杆的量程是 **−100..100**（其余 13 条是 0..100）
  //   ⟹ ⟹ 不写死 0..100 ⟹ ⟹ 滑杆的 min/max 必须**逐条**照抄源站实测值
  min?: number;
  max?: number;
  // ★★ Batch 845：源站每条滑杆的 `step` 都是 **1**（实测）⟹ ⟹ 也进数据表
  //   ⟹ ⟹ 不在 JSX 里写死 ⟹ ⟹ 判据才能逐条比
  step?: number;
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

// ★★ Batch 843：「妆造」页的 **11 个分类** ＋ 每个分类的**卡片清单**
//   （源站**只读**实测，raw 入库在
//    `docs/research/liblib-canvas-batch843-2026-10-01/raw/source-843-makeup.json`）
//
// ★★ **每个分类的第一张都是「无」**（**没有缩略图** —— 源站是一枚图标）⟹ ⟹ clone 同款。
// ★ 卡片名**逐条照抄**源站的**可见**文案（源站的 aria 是「分类 ＋ 名字」，可见的是名字）。
// ★★ 源站的 `眼影` 分类里「自然」**出现两次**（第 2 张与第 6 张）⟹ ⟹ 照抄，不去重。
const MAKEUP_CATEGORIES: { id: string; label: string; cards: string[] }[] = [
  { id: "brow", label: "眉毛", cards: ["自然", "直眉", "英气", "弯月", "高挑", "浓密", "小挑眉", "野生", "原生", "古典", "丝雾", "棕雾", "毛绒"] },
  { id: "contact", label: "美瞳", cards: ["琥珀", "橄榄绿", "混血灰", "灰粉", "烟花紫", "摩卡棕", "亚麻灰", "金星棕", "黑瞳", "黑边", "红宝石", "深棕", "金珀"] },
  { id: "wochan", label: "卧蚕", cards: ["素颜", "自然", "妈生感", "可爱", "无辜", "月牙", "减龄", "亮片"] },
  { id: "yanying", label: "眼影", cards: ["裸杏", "自然", "无辜眼", "元气", "泪痣", "自然", "猫眼", "闪片", "派对", "糖果", "大地色", "消肿", "海棠"] },
  { id: "jielan", label: "睫毛", cards: ["自然", "纯欲", "甜妹", "翘睫", "仙女", "短睫", "鱼尾", "漫画", "下睫", "倒置", "上睫", "浓密", "太阳花", "卷翘"] },
  { id: "xiurong", label: "修容", cards: ["立体", "自然", "V脸", "气质", "塑造", "欧美", "笔挺", "古铜", "混血", "盒鼻", "短鼻"] },
  { id: "saihong", label: "腮红", cards: ["元气", "眼下", "法式", "氛围", "高原", "面颊", "微醺", "冻伤", "晒伤", "红润", "桃粉", "减龄"] },
  { id: "runcai", label: "唇彩", cards: ["珊瑚粉", "裸粉", "蜜桃", "樱桃", "南瓜", "亮橘", "正红", "西柚", "浆果", "豆沙粉", "玫瑰", "火龙果", "果冻", "裸棕", "砖红", "车厘子", "玫红"] },
  { id: "zhuangshi", label: "妆饰", cards: ["眼下钻石", "雀斑", "度假雀斑", "慵懒雀斑", "野生雀斑", "美式雀斑"] },
  { id: "yanxian", label: "眼线", cards: ["自然系", "深邃", "甜酷", "韩系", "狗狗眼", "古典", "全包", "开口下至", "淡颜", "上扬", "刀锋"] },
  { id: "gaoguang", label: "高光", cards: ["眼下提亮", "丰润", "平整", "盈润", "丰盈", "笔挺", "透亮", "水光", "小灯泡"] },
];

// ★★ Batch 845：左列第三段「身材塑形」的 **18 条**滑杆
//   （源站**只读**实测；raw 入库在
//    `docs/research/liblib-canvas-batch845-2026-10-01/raw/source-845-body.json`
//    ＋ 像素证据 `raw/source-845-pixels.json`）
//
// ★★ **结构**（源站实测）：
//   · 右栏**没有标题行** ⟹ ⟹ 右栏**第一层就是滚动区**（`pt-3`）
//     ⟹ ⟹ 内容起点 ＝ 右栏顶 + 12（与第二段同 ⟹ ⟹ 同样比「脸部精修」段高 48px）
//   · **18 条**滑杆，每条＝ LABEL(240×55)：
//     ├ 标签行 240×22（名字 14px／22px／**纯白** ＋ 可选的「i」＋ 右端数值 11px／16px）
//     └ 轨道 240×12（= 标签 +36）＋ 一枚 **14×14 的白色圆钮** ＋ 圆心 **2×2 深点**
//   · 标签行 top ＝ 段内 **12 + 74.8·i**（★ 与页签滑杆**同一个步进**）
//
// ★★ **量程**（源站实测，逐条）：有 **5 条**是 **−100..100**
//   （丰胸／瘦身／瘦手臂／美臀／肩膀宽度），其余 **13 条**是 0..100；step 全是 1、初值全 0。
//
// ★★ **带「i」标记**的有 **6 条**（驼背／瘦脖子-左／瘦脖子-右／天鹅颈-左／天鹅颈-右／全身美型）。
//
// ★★ **外观**（★ 由**像素**实测，不是推理 —— 见 `raw/source-845-pixels.json`）：
//   轨道 **2px**；已填充段**纯白 #fff**；未填充段 ≈ rgba(255,255,255,.08)（面板底 #242424 上是 53）；
//   圆钮 **14×14 纯白**、圆心 **2×2 = #464646**；
//   圆钮中心 ＝ 轨道左端 + **7** + ratio·**226**（★ 由两条滑杆**解**出来的 ⟹ ⟹ 不是手打常数）
const BODY_SLIDERS: Slider[] = [
  { id: "body-breast", label: "丰胸", info: false, min: -100, max: 100, step: 1 },
  { id: "body-height", label: "AI 增高", info: false, step: 1 },
  { id: "body-hunchback", label: "驼背", info: true, step: 1 },
  { id: "body-long-leg", label: "长腿", info: false, step: 1 },
  { id: "body-square-shoulder", label: "直角肩", info: false, step: 1 },
  { id: "body-small-head", label: "小头", info: false, step: 1 },
  { id: "body-slim", label: "瘦身", info: false, min: -100, max: 100, step: 1 },
  { id: "body-slim-belly", label: "瘦肚子", info: false, step: 1 },
  { id: "body-slim-arms", label: "瘦手臂", info: false, min: -100, max: 100, step: 1 },
  { id: "body-hip", label: "美臀", info: false, min: -100, max: 100, step: 1 },
  { id: "body-slim-legs", label: "瘦腿", info: false, step: 1 },
  { id: "body-slim-neck-l", label: "瘦脖子-左", info: true, step: 1 },
  { id: "body-slim-neck-r", label: "瘦脖子-右", info: true, step: 1 },
  { id: "body-waist", label: "美腰", info: false, step: 1 },
  { id: "body-swan-neck-l", label: "天鹅颈-左", info: true, step: 1 },
  { id: "body-swan-neck-r", label: "天鹅颈-右", info: true, step: 1 },
  { id: "body-shoulder-width", label: "肩膀宽度", info: false, min: -100, max: 100, step: 1 },
  { id: "body-beauty-all", label: "全身美型", info: true, step: 1 },
];

// ★★ Batch 846：左列第四段「服装造型」
//   （源站**只读**实测；raw 入库在
//    `docs/research/liblib-canvas-batch846-2026-10-01/raw/source-846-outfit.json`
//    ⟹ ⟹ 下面的清单由 `probes/gen846_data.py` **机器提取** ⟹ ⟹ 不手抄）
//
// ★★ **这一段的结构与前两段不同**（★ 源站实测）：
//   · 这一段**有标题行** ⟹ ⟹ 右栏第一层是**子页签行**（40 高）：
//     「造型」（56 宽，**带文字**）＋「服装」＋「AI 生成」（各 24 宽，只有图标）
//     ⟹ ⟹ 内容起点 ＝ 列顶 + 40 + 16(pt-4) ＝ **rel 56**
//   · 内容 ＝ 四个小节（各是一个 SECTION）：
//     「发型」＝ H3 ＋ 7 枚 chip ＋ **12 张** 76×96 的卡
//     「发色」＝ H3 ＋ **11 枚** 35×35 的色块（10 色 ＋ 1 枚「自定义颜色」）
//     「妆容」＝ H3 ＋ 7 枚 chip（**宽度随文案变**）＋ **7 张** 76×96 的卡
//     「口红」＝ H3 ＋ **10 枚** 35×35 的色块
//   · 滚动区高 **1312**
//   · ★ 这一段的底部生成遮罩只有**一枚整宽 240×36 的「确认生成」**
//     ⟹ ⟹ 与「脸部精修」段那枚 196×36 ＋ 36×36「智能调整」**不一样**
//
// ★★ **卡片与色块的图**：卡片图是**引用**源站 CDN 的真实图（与 batch 844 的贴纸同一做法）
//   ⟹ ⟹ 那是**引用**不是复刻 ⟹ ⟹ 不声称这些资产归本仓库所有。

// ★★ Batch 846：左列第四段「服装造型」的四个小节标题（★ 源站实测）
const OUTFIT_SECTION_TITLES: { title: string; top: number }[] = [
  { title: "发型", top: 16 },
  { title: "发色", top: 544 },
  { title: "妆容", top: 670 },
  { title: "口红", top: 1126 },
];

// ★★ 发型的 chip 行（★ 7 枚 50×26；**「现代」初始选中** ⟹ 白底黑字）
const OUTFIT_HAIR_CHIPS: { label: string; x: number; y: number; w: number; sel: boolean }[] = [
  { label: "现代", x: 24, y: 46, w: 50, sel: true },
  { label: "古风", x: 80, y: 46, w: 50, sel: false },
  { label: "民国", x: 136, y: 46, w: 50, sel: false },
  { label: "仙侠", x: 192, y: 46, w: 50, sel: false },
  { label: "科幻", x: 24, y: 78, w: 50, sel: false },
  { label: "民族", x: 80, y: 78, w: 50, sel: false },
  { label: "儿童", x: 136, y: 78, w: 50, sel: false },
];

// ★★ 妆容的 chip 行（★ 7 枚，**宽度随文案变**（「欧美时尚」74 ⟹ 4 个字））
const OUTFIT_MAKEUP_CHIPS: { label: string; x: number; y: number; w: number; sel: boolean }[] = [
  { label: "现代", x: 24, y: 700, w: 50, sel: true },
  { label: "古代", x: 80, y: 700, w: 50, sel: false },
  { label: "民国", x: 136, y: 700, w: 50, sel: false },
  { label: "欧美时尚", x: 24, y: 732, w: 74, sel: false },
  { label: "国潮", x: 104, y: 732, w: 50, sel: false },
  { label: "特效", x: 160, y: 732, w: 50, sel: false },
  { label: "儿童", x: 24, y: 764, w: 50, sel: false },
];

// ★★ 发色的色块（★ 10 枚颜色 ＋ 1 枚「自定义颜色」⟹ 初始选中**第一枚**）
const OUTFIT_HAIR_COLORS: { color: string; x: number; y: number; sel: boolean; custom: boolean }[] = [
  { color: "rgb(11, 11, 11)", x: 24, y: 574, sel: true, custom: false },
  { color: "rgb(35, 23, 11)", x: 65, y: 574, sel: false, custom: false },
  { color: "rgb(92, 53, 24)", x: 106, y: 574, sel: false, custom: false },
  { color: "rgb(128, 81, 45)", x: 147, y: 574, sel: false, custom: false },
  { color: "rgb(172, 118, 80)", x: 188, y: 574, sel: false, custom: false },
  { color: "rgb(210, 162, 125)", x: 229, y: 574, sel: false, custom: false },
  { color: "rgb(108, 90, 78)", x: 24, y: 615, sel: false, custom: false },
  { color: "rgb(129, 129, 129)", x: 65, y: 615, sel: false, custom: false },
  { color: "rgb(216, 208, 196)", x: 106, y: 615, sel: false, custom: false },
  { color: "rgb(240, 226, 200)", x: 147, y: 615, sel: false, custom: false },
  { color: "rgba(0, 0, 0, 0)", x: 188, y: 615, sel: false, custom: true },
];

// ★★ 口红的色块（★ 10 枚；★ 「口红」那节**没有**「自定义颜色」）
const OUTFIT_LIP_COLORS: { color: string; x: number; y: number; sel: boolean; custom: boolean }[] = [
  { color: "rgb(102, 38, 48)", x: 24, y: 1156, sel: false, custom: false },
  { color: "rgb(143, 51, 65)", x: 65, y: 1156, sel: true, custom: false },
  { color: "rgb(178, 68, 84)", x: 106, y: 1156, sel: false, custom: false },
  { color: "rgb(200, 95, 106)", x: 147, y: 1156, sel: false, custom: false },
  { color: "rgb(142, 59, 82)", x: 188, y: 1156, sel: false, custom: false },
  { color: "rgb(157, 82, 102)", x: 229, y: 1156, sel: false, custom: false },
  { color: "rgb(181, 111, 113)", x: 24, y: 1197, sel: false, custom: false },
  { color: "rgb(210, 139, 138)", x: 65, y: 1197, sel: false, custom: false },
  { color: "rgb(111, 53, 65)", x: 106, y: 1197, sel: false, custom: false },
  { color: "rgb(211, 162, 159)", x: 147, y: 1197, sel: false, custom: false },
];

// ★★ 发型的卡片（★ 12 张 76×96；★ 图是**引用**源站 CDN 的真实图）
const OUTFIT_HAIR_CARDS: { label: string; img: string; x: number; y: number }[] = [
  { label: "长直发", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_changzhifa.jpg", x: 24, y: 116 },
  { label: "大波浪", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_male_dabolang.jpg", x: 106, y: 116 },
  { label: "波波头", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_male_bobotou.jpg", x: 188, y: 116 },
  { label: "齐肩中短发", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_male_qijianduanfa.jpg", x: 24, y: 220 },
  { label: "高马尾", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_male_gaomawei.jpg", x: 106, y: 220 },
  { label: "低马尾", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_male_dimawei.jpg", x: 188, y: 220 },
  { label: "双马尾", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_male_shuangmawei.jpg", x: 24, y: 324 },
  { label: "丸子头", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_male_wanzitou.jpg", x: 106, y: 324 },
  { label: "半扎发", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_male_banzha.jpg", x: 188, y: 324 },
  { label: "编发", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_male_bianfa.jpg", x: 24, y: 428 },
  { label: "空气刘海", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_male_kongqiliuhai.jpg", x: 106, y: 428 },
  { label: "齐刘海", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_male_qiliuhai.jpg", x: 188, y: 428 },
];

// ★★ 妆容的卡片（★ 7 张 76×96；★ 图是**引用**源站 CDN 的真实图）
const OUTFIT_MAKEUP_CARDS: { label: string; img: string; x: number; y: number }[] = [
  { label: "素颜", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_suyan.jpg", x: 24, y: 802 },
  { label: "裸妆", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_luozhuang.jpg", x: 106, y: 802 },
  { label: "桃花氛围妆", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_taohuafenweizhuang.jpg", x: 188, y: 802 },
  { label: "日常淡妆", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_richangdanzhuang.jpg", x: 24, y: 906 },
  { label: "冷艳妆", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_lengyanzhuang.jpg", x: 106, y: 906 },
  { label: "甜美妆", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_tianmeizhuang.jpg", x: 188, y: 906 },
  { label: "韩系妆", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_hanxizhuang.jpg", x: 24, y: 1010 },
];


// ★★ Batch 844：左列第二段「脸部 & 身体特征」的**纹身 & 疤痕**卡
//   （源站**只读**实测；raw 入库在
//    `docs/research/liblib-canvas-batch844-2026-10-01/raw/source-844-traits.json`）
//
// ★★ **这一段的结构**（源站实测，**不是**「一列控件」）：
//   · 右栏**没有标题行** ⟹ ⟹ 右栏**第一层就是滚动区**（`pt-3`）
//     ⟹ ⟹ 内容起点比「脸部精修」段**高 48px**（★ 由两批 raw 机械算出 ⟹ ⟹ 不是手打常数）
//   · H3「纹身 & 疤痕」240×22（**14px／400／纯白**）
//     ⟹ ⟹ 与眉眼页的 H3（13px／500／白 30%）**不是**一个样式 ⟹ ⟹ 单开一个类
//   · 网格 3 列 × 2 行（列距 6、行距 8）⟹ ⟹ 6 张 **76×54** 的卡
//     └ 缩略图 **76×32 的圆形**（`rounded-full`，白 5% 底 ＋ 白 8% 边）
//       ⟹ ⟹ 与妆造页的 76×76 **方形**缩略图**不是**一回事
//     └ 名字 11px／16px（`px-1` ⟹ 左右各 4px ⟹ 「痣」19px、「全脸雀斑」52px）
//     └ 第 6 张「自定义」**没有图** ⟹ ⟹ 是一枚 16×16 的图标
//       ⟹ ⟹ 且它**没有** `aria-pressed`（前 5 张都是 `aria-pressed="false"`）
//
// ★ **缩略图用的是源站 CDN 的真实贴纸图**（★ 与 `VideoGenerationPanel` 同一做法）
//   ⟹ ⟹ 那是**引用**不是复刻 ⟹ ⟹ 不声称这些资产归本仓库所有。
const TRAIT_CARDS: { name: string; img: string | null }[] = [
  {
    name: "痣",
    img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/features/sticker_mole.png",
  },
  {
    name: "疤痕_深",
    img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/features/sticker_scar_1.png",
  },
  {
    name: "疤痕_浅",
    img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/features/sticker_scar_2.png",
  },
  {
    name: "全脸雀斑",
    img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/features/sticker_facefreckles.png",
  },
  {
    name: "脸颊雀斑",
    img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/features/sticker_cheekfreckles.png",
  },
  { name: "自定义", img: null },
];

// ★ 一页右栏的**块序列**（绝对定位；top 相对滚动区内容起点）
type PanelBlock =
  | { kind: "h3"; text: string; top: number }
  | { kind: "h4"; text: string; top: number }
  | { kind: "sliders"; top: number; items: Slider[] }
  | { kind: "cards"; top: number; names: string[] }
  // ★★ Batch 843：妆造页（**自带状态**：分类 chip ＋ 随分类切换的卡片网格）
  | { kind: "makeup"; h4Top: number; chipTop: number; cardTop: number };

const TAB_BLOCKS: Record<string, PanelBlock[]> = {
  "brow-eye": [
    { kind: "h3", text: "眼睛", top: 20 },
    { kind: "sliders", top: 60, items: BROW_EYE_EYE_SLIDERS },
    { kind: "h4", text: "眼神光", top: 1481 },
    { kind: "cards", top: 1511, names: BROW_EYE_CARD_NAMES },
    { kind: "h3", text: "眉毛", top: 1947 },
    { kind: "sliders", top: 1987, items: BROW_EYE_BROW_SLIDERS },
  ],
  makeup: [
    // ★ 源站实测：H4「妆容素材」240×22 @top 20（带一枚「i」）
    //   分类 chip 50×26：4 列 × 3 行，步进 56／32（top = 50 + 32·row，left = 24 + 56·col）
    //   卡片 76×96：3 列，步进 82／104（top = 152 + 104·row，left = 24 + 82·col）
    { kind: "makeup", h4Top: 20, chipTop: 50, cardTop: 152 },
  ],
};

// ★ 滑杆六行的**纵向偏移**（源站实测的标签盒 top，相对右栏滚动区内容起点）
const SLIDER_STEP = 74.8;

// ★★ Batch 845：这一段的**内容起点**（相对段顶）＝ 12（源站 `pt-3` ⟹ ⟹ 与第二段同）
const BODY_SLIDERS_TOP = 12;

// ★★ Batch 845：**圆钮中心的行程**（★ 由 `raw/source-845-pixels.json` 的两条滑杆**解**出来）
//   圆钮中心 x ＝ 轨道左端 + 7 + ratio·226
//   ⟹ ⟹ 14px 的圆钮 ⟹ ⟹ 原生 range 的 thumb 行程**正好**是 7..233 ⟹ ⟹ 与源站一致
const SLIDER_THUMB_INSET = 7;
const SLIDER_TRAVEL = 226;

// ★★ Batch 845：这一段的**滚动区高度**（源站实测 scrollHeight ＝ 1418）
//   ＝ 12(pt-3) + 18×54.8(块高) + 17×20(space-y-5) + 80(pb-20)
//   ⟹ ⟹ **不是手打常数** ⟹ ⟹ 由上面的块数与步进**算**出来
const BODY_SCROLL_HEIGHT =
  BODY_SLIDERS_TOP +
  BODY_SLIDERS.length * 54.8 +
  (BODY_SLIDERS.length - 1) * 20 +
  80;

// ★★ 所有滑杆的 id（值表的初值）—— **分页签的** ＋ **分块的** ＋ **身材塑形的**
const ALL_SLIDERS: Slider[] = [
  ...Object.values(TAB_SLIDERS).flat(),
  ...Object.values(TAB_BLOCKS).flatMap((blocks) =>
    blocks.flatMap((b) => (b.kind === "sliders" ? b.items : [])),
  ),
  ...BODY_SLIDERS,
];

// ★★ **未实现**页签的空态说明（**逐页**写，别用一句通用文案）
//   ★★ **batch 843 起**：妆造页**已实现**（11 枚分类 chip ＋ 138 张卡）⟹ ⟹ 它**不再**走这条路
//   ⟹ ⟹ 原来那条 makeup 的说明里「13 张妆容预设卡」是**错的**（实为 138 张）⟹ ⟹ **删掉**
//   ⟹ ⟹ （★ 留着就是一条**假陈述**：既说「13 张」又说「属后续批次」⟹ 而它早已实现）
const EMPTY_NOTE: Record<string, string> = {};

// ★★ Batch 843：左列**其余四段**的空态说明（**逐段**写）
//   ★ 源站四段的结构**各不相同**（batch 841 raw 机器提取）⟹ ⟹ 一句通用文案就是**假陈述**
//   ★ 措辞里的每个数字/条目名都来自 raw ⟹ ⟹ 不手打不存在的结构
// ★★ Batch 844 起：**「脸部 & 身体特征」段已实现**（纹身 & 疤痕 ＋ 6 张贴纸卡）
//   ⟹ ⟹ 它**不再**走这条路 ⟹ ⟹ 那条说明（写着「属后续批次」）**已是假陈述** ⟹ ⟹ **删掉**。
// ★★ Batch 845 起：**「身材塑形」段也已实现**（18 条滑杆）
//   ⟹ ⟹ 它**不再**走这条路 ⟹ ⟹ 那条说明**也是假陈述** ⟹ ⟹ **删掉**。
//   ★★ 并且那条说明里写的「17 条滑杆」**本身就是错的**（源站实测是 **18** 条，
//      且**第一条是「丰胸」**，不是「丰胸数值 ＋ 17 条」）⟹ ⟹ 留着就是一条假陈述。
// ★ 措辞里的每个数字/条目名都来自 raw ⟹ ⟹ 不手打不存在的结构
// ★★ Batch 847：**`SEGMENT_NOTE` 整张表已删除**。
//   ⟹ ⟹ 原来那两条（outfit／voice）写的都是「属后续批次 ⟹ ⟹ 这里不编造控件」
//   ⟹ ⟹ 而 846 已实现「服装造型」、**847 已实现「音色音调」**
//   ⟹ ⟹ 两条**都成了假陈述** ⟹ ⟹ 留着比删掉更坏 ⟹ ⟹ **整张表删掉**。
//   ★ 「未实测/未实现的控件只显示如实说明」这条**纪律没有变**
//   ⟹ ⟹ 它现在由**更细的粒度**承载（见右栏 JSX 里各段的分支）：
//     · 第四段「服装造型」的「服装」「AI 生成」两枚子页签 ⟹ ⟹ 如实说明
//     · 第五段「音色音调」的「我的音色」「AI 生成」两枚页签 ⟹ ⟹ 如实说明
//     · 脸部精修段「妆造」页（843 已实现）以外的其余页 ⟹ ⟹ 见 `EMPTY_NOTE`
// ───────────────────────────────────────────────────────────────────

// ═══════════════════════════════════════════════════════════════════
// ★★ Batch 847：左列第五段「音色音调」
// ───────────────────────────────────────────────────────────────────
// ★★ **这一段的结构与前四段都不一样**（★ 源站实测，batch 847 raw）：
//   右栏内层 288 宽 @1273 是 `flex min-h-0 flex-1 flex-col px-6` ⟹ ⟹ **三块**
//     ① 标题行 240×40 @rel(24,0)  ＝ **三枚页签**（音色库／我的音色／AI 生成）
//     ② 工具行 240×32 @rel(24,48) ＝ 两枚 32×32（搜索／筛选音色），间隙 2
//     ③ 滚动区 240×514 @rel(24,88) ＝ 20 张音色卡，滚动高 1192
//   ★★ 而**前四段的内层没有 px-6** ⟹ ⟹ 这一段的子块**整体右移 24px**
//   ★★ **这一段没有底部生成行**（★ batch 841 raw：右栏底部**无任何按钮**）
//
// ★★ 下面的数据块是**机器提取**的（`probes/gen847_data.py` 从入库 raw 里抽的）
//   ⟹ ⟹ 名字与副标**不是手打** ⟹ ⟹ 门禁会逐条与 raw 比对
// ───────────────────────────────────────────────────────────────────
// ── 标题行页签（★ 源站实测：**宽度随选中态变** ⟹ ⟹ 两套宽度）──
//   选中态：28 ＋ 文字宽（3 边距 ＋ 18 图标 ＋ 4 间隙 ＋ 文字 ＋ 3 边距）
//   未选中：24（★ 源站把文字盒裁成 0 宽 ⟹ ⟹ 只剩图标）
// ★ 三份 raw 交叉校验（847 音色库／848-p3 我的音色／848-p4 AI 生成）
const VOICE_TABS: { id: string; label: string; wOn: number; wOff: number; icon: typeof Music }[] = [
  { id: "library", label: "音色库", wOn: 70, wOff: 24, icon: Music },
  { id: "mine", label: "我的音色", wOn: 84, wOff: 24, icon: User },
  { id: "ai", label: "AI 生成", wOn: 73, wOff: 24, icon: Sparkles },
];

// ── P3「我的音色」页（★ 源站实测）──
// ★ **这一页也有工具行**（搜索／筛选音色）⟹ ⟹ 与「音色库」页同构
//   工具0 32×32 @(1297,279)
//   工具1 32×32 @(1331,279)
// ★ 空态：240×96 @(1297,319)  文案「暂无音色数据」
const VOICE_MINE_EMPTY = {
  text: "暂无音色数据",
  w: 240,
  h: 96,
  fontSize: "12px",
  lineHeight: "16px",
  color: "rgba(255, 255, 255, 0.6)",
};

// ── P4「AI 生成」页（★ 源站实测）──
// ★ **这一页没有工具行**⟹ ⟹ 内容区直接从标题行下方开始
// ★ 输入框 240×120 @(1297,283)，占位文案「默认基于当前人设生成，可以补充输入音色特征...」
// ★ 「生成音色」按钮 240×36 @(1297,422)，右侧角标 36×16（图标 ＋ 数字「21」）
// ★ 「生成历史」小标题 240×16 @(1297,482) ＋ 空态「暂无历史记录」240×64 @(1297,506)
// ★ **两处间隙也是从 raw 的盒算出来的**（⟹ ⟹ 不是手打）：
//   输入框底 403 → 按钮顶 422 ⟹ 间隙 **19**（space-y-3 之外还有一段）
//   按钮底 458 → 历史区顶 470 ⟹ 间隙 **12**（＝ space-y-3）
const VOICE_AI = {
  content: { w: 240, h: 562, padTop: 12, padBottom: 24, genGap: 19, historyGap: 12 },
  textarea: {
    w: 240,
    h: 120,
    radius: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.08)",
    fontSize: "12px",
    lineHeight: "20px",
    color: "rgb(255, 255, 255)",
    background: "rgba(255, 255, 255, 0.06)",
    ariaLabel: "AI 音色描述",
    placeholder: "默认基于当前人设生成，可以补充输入音色特征...",
  },
  generate: {
    w: 240,
    h: 36,
    radius: 10,
    gap: 4,
    fontSize: "14px",
    lineHeight: "20px",
    color: "rgb(0, 0, 0)",
    background: "rgb(255, 255, 255)",
    label: "生成音色",
  },
  badge: {
    w: 36,
    h: 16,
    gap: 4,
    opacity: 0.4,
    number: "21",
    numberW: 16,
    numberH: 16,
    numberFontSize: "12px",
  },
  history: {
    title: "生成历史",
    titleW: 240,
    titleH: 16,
    titleFontSize: "11px",
    titleLineHeight: "16px",
    titleFontWeight: 500,
    titleColor: "rgba(255, 255, 255, 0.6)",
    empty: "暂无历史记录",
    emptyW: 240,
    emptyH: 64,
    emptyFontSize: "12px",
    emptyLineHeight: "16px",
    emptyColor: "rgba(255, 255, 255, 0.6)",
    emptyPadY: 24,
  },
};

// ── 工具行两枚按钮（源站实测 32×32，间隙 2）──
// ★「筛选音色」那枚的源站 cls 里带 `relative`（可能挂角标）⟹ ⟹ 未复刻
//   搜索 32×32，图标 16×16 @(1305,287)
//   搜索 32×32，图标 16×16 @(1339,287)

// ── 20 条音色（名字 ＋ 副标）──
// ★ 逐条出自 raw 的「名字」「副标」字段 ⟹ ⟹ 不是手打
const VOICES: { name: string; sub: string }[] = [
  { name: "青涩青年音色", sub: "中文(普通话) · 男" },
  { name: "精英青年音色", sub: "中文(普通话) · 男" },
  { name: "霸道青年音色", sub: "中文(普通话) · 男" },
  { name: "青年大学生音色", sub: "中文(普通话) · 男" },
  { name: "少女音色", sub: "中文(普通话) · 女" },
  { name: "御姐音色", sub: "中文(普通话) · 女" },
  { name: "成熟女性音色", sub: "中文(普通话) · 女" },
  { name: "甜美女性音色", sub: "中文(普通话) · 女" },
  { name: "青涩青年音色-beta", sub: "中文(普通话) · 男" },
  { name: "精英青年音色-beta", sub: "中文(普通话) · 男" },
  { name: "霸道青年音色-beta", sub: "中文(普通话) · 男" },
  { name: "青年大学生音色-beta", sub: "中文(普通话) · 男" },
  { name: "少女音色-beta", sub: "中文(普通话) · 女" },
  { name: "御姐音色-beta", sub: "中文(普通话) · 女" },
  { name: "成熟女性音色-beta", sub: "中文(普通话) · 女" },
  { name: "甜美女性音色-beta", sub: "中文(普通话) · 女" },
  { name: "聪明男童", sub: "中文(普通话) · 男" },
  { name: "可爱男童", sub: "中文(普通话) · 男" },
  { name: "萌萌女童", sub: "中文(普通话) · 女" },
  { name: "卡通猪小琪", sub: "中文(普通话) · Character" },
];

// ── 由 raw **算**出来的量（★ 不是手打常数）──
// ★ 音色卡高 48，步进 56 ⟹ ⟹ 间隙 8（space-y-2）
// ★ 滚动区高 1192 ＝ 20×48 ＋ 19×8 ＋ 80(pb-20) ⟹ ⟹ 与 raw 的 scrollHeight 一致
const VOICE_CARD_HEIGHT = 48;
const VOICE_CARD_GAP = 8;
const VOICE_SCROLL_HEIGHT = 1192;

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
  // ★★ Batch 843：妆造页的**当前分类**
  const [makeupCat, setMakeupCat] = useState(MAKEUP_CATEGORIES[0].id);
  // ★★ Batch 843：**选中态按分类各存一份**（源站实测：★ **每个**分类的第一张「无」
  //   都是 `aria-pressed=true` ⟹ ⟹ 源站的选中态**不是**一个全局单值，而是**每分类一份**）
  //   ⟹ ⟹ clone 之前用单一 `makeupCard` ⟹ ⟹ 切到别的分类时那张「无」**不是**选中态
  //   ⟹ ⟹ 与源站不符 ⟹ ⟹ 本批改正。
  //   ★ 未实测：点过一张卡之后**切走再切回**是否仍保持选中 ⟹ ⟹ 源站那趟只点了分类 chip
  //   ⟹ ⟹ 这里按「每分类各存一份」实现 ⟹ ⟹ 但那一条**不声称**与源站一致。
  const [makeupSel, setMakeupSel] = useState<Record<string, string>>({});
  // ★★ Batch 844：纹身 & 疤痕卡的**选中态**（源站实测：六张卡的 `aria-pressed`
  //   **默认都是 false** ⟹ ⟹ 源站确实有选中态，只是**初始一个都没选中**）
  //   ★ 「自定义」那枚**没有** `aria-pressed` ⟹ ⟹ 它不是「可选中的卡」，是上传入口。
  //   ★ 未实测：点卡片之后源站会发生什么（会不会改角色）⟹ ⟹
  //   ⟹ ⟹ clone 只切换**本地选中态**，**不声称**与源站同构。
  const [traitSel, setTraitSel] = useState<string | null>(null);
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
  // ★★ Batch 846：左列第四段「服装造型」的**各类选中态**
  //   （★ 源站实测的**初始态**：发型的「现代」chip 选中／妆容的「现代」chip 选中／
  //     发色的**第一枚**色块选中／口红的**第二枚**色块选中／19 张卡**全部未选中**）
  const [outfitTab, setOutfitTab] = useState("style");
  const [outfitHairChip, setOutfitHairChip] = useState("现代");
  const [outfitMakeupChip, setOutfitMakeupChip] = useState("现代");
  const [outfitHairColor, setOutfitHairColor] = useState(0);
  const [outfitLipColor, setOutfitLipColor] = useState(1);
  // ★ 卡片选中态**按小节各存一份**（源站实测：初始一个都没选中）
  const [outfitCardSel, setOutfitCardSel] = useState<Record<string, string>>({});
  // ★★ Batch 849：P1「服装」页的**分类 chip**当前项（★ 源站实测：初始「现代」选中）
  const [outfitClothesChip, setOutfitClothesChip] = useState("现代");
  // ★★ Batch 849：P1「服装」页的**服装卡选中态**（★ 源站实测：初始一个都没选中）
  const [outfitClothesCardSel, setOutfitClothesCardSel] = useState<Record<string, string>>({});
  // ★★ Batch 849：P2「AI 生成」页的**输入内容**
  //   ★ 源站实测：输入框**为空**时，那枚「确认生成」是**禁用态**
  //     （★ 计算样式：文字 `rgba(255,255,255,0.3)`、底 `rgba(255,255,255,0.08)`）
  //   ⟹ ⟹ clone 照抄这个语义：★ **空 ⟹ disabled；有内容 ⟹ 可点**
  const [outfitAiText, setOutfitAiText] = useState("");

  // ★★ Batch 847：左列第五段「音色音调」的**标题行页签**当前项
  //   （★ 源站实测：标题行**就是**三枚页签「音色库／我的音色／AI 生成」⟹ ⟹ 初始第一枚）
  const [voiceTab, setVoiceTab] = useState("library");
  // ★★ Batch 847：**音色卡的选中态**
  //   ★ 源站实测的**初始态**：**第一张**「青涩青年音色」是选中态
  //   （白 1px 边框 ＋ 透明底）⟹ ⟹ 其余 19 张是透明边框 ＋ 白 6% 底
  const [voiceSel, setVoiceSel] = useState<string | null>(VOICES[0].name);

  const tagText = `· ${age} · ${region} · 现代`;

  // ★★ Batch 841：当前页签的**实测滑杆清单**（没有 ⟹ 显示空态说明）
  const currentSliders = TAB_SLIDERS[tab] ?? null;

  // ★★ Batch 842：当前页签的**块序列**（眉眼页是分块布局 ⟹ 走这条）
  const currentBlocks = TAB_BLOCKS[tab] ?? null;

  // ★ 一条滑杆行（标签 ＋ 轨道 ＋ 数值）—— 各页签**共用同一套**几何规则：
  //   标签 top = 20 + i·74.8（相对右栏内容区 ⟹ 绝对 rel 130 + 74.8·i）
  //   轨道 = 标签 +36（240×12）｜ 数值 = 标签 +3（7×16，右端对齐到 1176）
  // ★ `baseTop` 给的是**绝对** top（眉眼页的分段布局：源站逐段实测各不相同）
  //
  // ★★ Batch 845：**量程逐条照抄**（源站有 5 条是 −100..100）＋ **填充段** ＋ **圆心点**
  const renderSlider = (item: Slider, index: number, baseTop?: number) => {
    const top = baseTop ?? 20 + index * SLIDER_STEP;
    const min = item.min ?? 0;
    const max = item.max ?? 100;
    const value = values[item.id] ?? 0;
    // ★ 圆钮中心相对轨道左端的偏移（源站：**7 + ratio·226**，由像素实测解出）
    const ratio = max === min ? 0 : (value - min) / (max - min);
    const thumbX = SLIDER_THUMB_INSET + ratio * SLIDER_TRAVEL;
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
          // ★ `--ce-fill` ＝ 已填充段的终点（= 圆钮中心）⟹ ⟹ 轨道的渐变靠它画
          style={
            {
              top: `${top + 36}px`,
              "--ce-fill": `${thumbX}px`,
            } as CSSProperties
          }
          min={min}
          max={max}
          step={item.step ?? 1}
          value={value}
          data-character-editor-slider={item.id}
          aria-label={item.label}
          onChange={(event) =>
            setValues((prev) => ({
              ...prev,
              [item.id]: Number(event.target.value),
            }))
          }
        />
        {/* ★★ Batch 845：源站那枚 **2×2 的深色圆心点**（`studioRangeThumbDot`）
            ⟹ ⟹ 它在**圆钮正中** ⟹ ⟹ 位置 ＝ 圆钮中心 − 1
            ⟹ ⟹ 纵向：轨道容器高 **24.8**（源站实测）⟹ ⟹ 2px 的点在 24.8 里居中
            ⟹ ⟹   ⟹ 点顶 ＝ 标签 + 30 + (24.8 − 2)/2 ＝ **标签 + 41.4**
            ⟹ ⟹   （★ 用 41 会与源站差 1px ⟹ ⟹ 那 6 条「小数部分进位」的滑杆就红） */}
        <span
          className="ce-slider-dot"
          style={{ left: `${24 + thumbX - 1}px`, top: `${top + 41.4}px` }}
          data-character-editor-slider-dot={item.id}
        />
        <span
          className="ce-slider-value"
          style={{ top: `${top + 3}px` }}
          data-character-editor-slider-value={item.id}
        >
          {value}
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

  // ★★ Batch 843：**妆造页**（H4「妆容素材」＋ 11 枚分类 chip ＋ 随分类切换的卡片网格）
  //   ★ 源站实测：chip 是 `role=tab`，选中那枚**白底黑字**；卡片首张恒为「无」
  const renderMakeup = (block: { h4Top: number; chipTop: number; cardTop: number }) => {
    const cat = MAKEUP_CATEGORIES.find((c) => c.id === makeupCat) ?? MAKEUP_CATEGORIES[0];
    // ★ 源站每个分类的**第一张**都是「无」（无缩略图 ⟹ 一枚 18×18 图标）
    const names = ["无", ...cat.cards];
    return (
      <div key="makeup">
        <h4
          className="ce-h4"
          style={{ top: `${block.h4Top}px` }}
          data-character-editor-h4="妆容素材"
        >
          <span>妆容素材</span>
          <span
            className="ce-info"
            role="img"
            aria-label="该调整不支持预览，需要生成后生效"
          >
            i
          </span>
        </h4>
        {MAKEUP_CATEGORIES.map((item, ci) => {
          const on = item.id === makeupCat;
          return (
            <button
              key={item.id}
              type="button"
              role="tab"
              aria-selected={on}
              aria-label={item.label}
              className={`ce-chip${on ? " is-on" : ""}`}
              style={{
                top: `${block.chipTop + Math.floor(ci / 4) * 32}px`,
                left: `${24 + (ci % 4) * 56}px`,
              }}
              data-character-editor-chip={item.id}
              onClick={() => setMakeupCat(item.id)}
            >
              {item.label}
            </button>
          );
        })}
        {names.map((name, i) => {
          const key = `${cat.id}/${name}`;
          // ★ 选中态按**分类**取（每分类一份，缺省「无」⟹ 与源站每分类第一张「无」pressed=true 一致）
          const on = (makeupSel[cat.id] ?? "无") === name;
          return (
            <button
              key={`${cat.id}-${i}`}
              type="button"
              aria-label={name === "无" ? "无" : `${cat.label} ${name}`}
              aria-pressed={on}
              className={`ce-card${on ? " is-on" : ""}`}
              style={{
                top: `${block.cardTop + Math.floor(i / 3) * 104}px`,
                left: `${24 + (i % 3) * 82}px`,
              }}
              // ★ **带序号** ⟹ DOM 里**唯一**（★ 源站「眼影」分类里有两个同名「自然」⟹
              //   只用「分类/名字」当属性值 ⟹ **两个元素同值** ⟹ 选择器会挑错一张卡）
              data-character-editor-makeup-card={`${cat.id}/${i}`}
              data-character-editor-makeup-name={name}
              onClick={() =>
                setMakeupSel((prev) => ({ ...prev, [cat.id]: name }))
              }
            >
              <span className="ce-card-media">
                {name === "无" ? (
                  <span className="ce-card-none" aria-hidden="true">
                    <Ban size={18} />
                  </span>
                ) : (
                  <span
                    className="ce-card-thumb"
                    data-character-editor-card-thumb={key}
                  />
                )}
              </span>
              <span
                className="ce-card-name"
                data-character-editor-card-name={key}
              >
                {name}
              </span>
            </button>
          );
        })}
      </div>
    );
  };

  // ★★ Batch 844：左列第二段「脸部 & 身体特征」
  //   ⟹ ⟹ 源站实测这一段**没有标题行** ⟹ ⟹ 右栏**第一层就是滚动区**
  //   ⟹ ⟹ 故用 `.ce-panel--seg`（top: 0 ＋ 满高）⟹ ⟹ 内容起点比「脸部精修」段**高 28px**
  //
  // ★★ **坐标**（相对模态；源站实测值）：
  //   H3「纹身 & 疤痕」 rel (936, 82) ⟹ 段内 top = 12
  //   卡片 76×54：rel (936/1018/1100, 112/174) ⟹ 段内 top = 42 + 62·行、left = 24 + 82·列
  const renderTraits = () => (
    <div className="ce-panel ce-panel--seg">
      <div className="ce-section">
        <h3
          className="ce-h3 ce-h3--section"
          style={{ top: 12 }}
          data-character-editor-h3="纹身 & 疤痕"
        >
          纹身 &amp; 疤痕
        </h3>
        {TRAIT_CARDS.map((card, i) => {
          const on = traitSel === card.name;
          return (
            <button
              key={card.name}
              type="button"
              // ★ 「自定义」那枚**没有** aria-pressed（源站实测）⟹ ⟹ 不给
              aria-pressed={card.img ? on : undefined}
              className={`ce-trait-card${on ? " is-on" : ""}`}
              style={{
                top: `${42 + Math.floor(i / 3) * 62}px`,
                left: `${24 + (i % 3) * 82}px`,
              }}
              data-character-editor-trait={card.name}
              onClick={() =>
                card.img
                  ? setTraitSel(card.name)
                  : flash("clone mock：自定义贴纸未接上传")
              }
            >
              <span
                className={`ce-trait-thumb${card.img ? "" : " ce-trait-thumb--custom"}`}
              >
                {card.img ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={card.img} alt="" />
                ) : (
                  <Plus size={16} />
                )}
              </span>
              <span className="ce-trait-name">{card.name}</span>
            </button>
          );
        })}
      </div>
    </div>
  );

  // ★★ Batch 845：左列第三段「身材塑形」—— **18 条**滑杆
  //   ⟹ ⟹ 源站实测这一段**也没有标题行** ⟹ ⟹ 右栏**第一层就是滚动区**
  //   ⟹ ⟹ 内容起点 ＝ 段顶 + 12（与第二段同）
  //
  // ★★ **坐标**（相对段顶；源站实测值）：
  //   标签行 top = 12 + 74.8·i（高 22；名字 14px／22px／纯白）
  //   轨道 = 标签 +36（240×12）｜ 数值 = 标签 +3（7×16，右端对齐）
  //   圆心点 = 标签 +41（2×2，左端 = 24 + 7 + ratio·226 − 1）
  const renderBody = () => (
    <div className="ce-panel ce-panel--seg">
      <div
        className="ce-section"
        // ★ 源站这一段的滚动区高 1418（★ 由块数与步进**算**出来 ⟹ ⟹ 不是手打常数）
        style={{ minHeight: `${BODY_SCROLL_HEIGHT}px` }}
      >
        {BODY_SLIDERS.map((item, i) =>
          renderSlider(item, i, BODY_SLIDERS_TOP + i * SLIDER_STEP),
        )}
      </div>
    </div>
  );

// ★★ Batch 846：这一段的**子页签**（★ 源站实测：右栏第一层就是它 ⟹ ⟹ **有标题行**）
//   「造型」（56 宽，**带文字** ＋ 前置图标）＋「服装」＋「AI 生成」（各 24 宽，只有图标）
//   ★ 与「脸部精修」段的六枚页签**同一个组件**（★ 文字页签跟着选中项移动）
//   ★ 图标**字形未采集**（源站是 iconify SVG）⟹ ⟹ 这里用 lucide 占位。
//
// ★★ Batch 849：**宽度随选中态变**（★ 与第五段「音色音调」**同一个规律**）
//   源站实测三份 raw 交叉校验（846 造型／848-p1 服装／848-p2 AI 生成）：
//     选中：造型 **56**／服装 **56**／AI 生成 **73**（28 ＋ 文字宽）
//     未选中：一律 **24**（★ 源站把文字盒裁成 0 宽 ⟹ ⟹ 只剩图标）
//   ⟹ ⟹ 下面这段由 `probes/gen849_data.py` **机器提取**（见
//      `docs/research/liblib-canvas-batch849-2026-10-01/probes/outfit-849-data.ts.txt`）
const OUTFIT_TABS: { id: string; label: string; wOn: number; wOff: number; icon: typeof Shirt }[] = [
  { id: "style", label: "造型", wOn: 56, wOff: 24, icon: Shirt },
  { id: "clothes", label: "服装", wOn: 56, wOff: 24, icon: Package },
  { id: "ai", label: "AI 生成", wOn: 73, wOff: 24, icon: Sparkles },
];

// ★★ Batch 849：P1「服装」页（★ 源站实测；raw ＝ 848 的 `source-848-p1.json`）
//   · 小标题「服装」240×22 @rel(24,16)
//   · 7 枚分类 chip（50×26，★ **「现代」初始选中** ⟹ 白底黑字）
//   · 24 张服装卡（3 列网格，76×155：图 74×133 ＋ 名字 16 高）
//   · ★ 这一页**有**底部生成遮罩（「确认生成」240×36）
// ★ 坐标口径：相对**右栏列**（源站 abs 1273,271）⟹ ⟹ 与 846 同一个原点
const OUTFIT_CLOTHES_CHIPS: { label: string; x: number; y: number; w: number; sel: boolean }[] = [
  { label: "现代", x: 24, y: 46, w: 50, sel: true },
  { label: "古风", x: 80, y: 46, w: 50, sel: false },
  { label: "仙侠", x: 136, y: 46, w: 50, sel: false },
  { label: "民国", x: 192, y: 46, w: 50, sel: false },
  { label: "科幻", x: 24, y: 78, w: 50, sel: false },
  { label: "礼服", x: 80, y: 78, w: 50, sel: false },
  { label: "民族", x: 136, y: 78, w: 50, sel: false },
];

// ★ 24 张服装卡（★ 图是**引用**源站 CDN 的真实图 ⟹ ⟹ 那是引用不是复刻）
const OUTFIT_CLOTHES_CARDS: { label: string; img: string; x: number; y: number }[] = [
  { label: "便装", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_bianzhuang_1.jpg", x: 24, y: 116 },
  { label: "便装", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_bianzhuang_2.jpg", x: 106, y: 116 },
  { label: "便装", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_bianzhuang_3.jpg", x: 188, y: 116 },
  { label: "连衣裙", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_lianyiqun_1.jpg", x: 24, y: 279 },
  { label: "连衣裙", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_lianyiqun_2.jpg", x: 106, y: 279 },
  { label: "连衣裙", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_lianyiqun_3.jpg", x: 188, y: 279 },
  { label: "连衣裙", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_lianyiqun_4.jpg", x: 24, y: 442 },
  { label: "职业西装", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_zhiyexizhuang_1.jpg", x: 106, y: 442 },
  { label: "职业西装", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_zhiyexizhuang_2.jpg", x: 188, y: 442 },
  { label: "通勤", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_tongqin.jpg", x: 24, y: 605 },
  { label: "运动", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_yundong_1.jpg", x: 106, y: 605 },
  { label: "运动", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_yundong_2.jpg", x: 188, y: 605 },
  { label: "运动", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_yundong_3.jpg", x: 24, y: 768 },
  { label: "运动", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_yundong_4.jpg", x: 106, y: 768 },
  { label: "JK制服", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_JKzhifu_1.jpg", x: 188, y: 768 },
  { label: "JK制服", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_JKzhifu_2.jpg", x: 24, y: 932 },
  { label: "校服", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_xiaofu_1.jpg", x: 106, y: 932 },
  { label: "校服", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_xiaofu_2.jpg", x: 188, y: 932 },
  { label: "校服", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_xiaofu_3.jpg", x: 24, y: 1095 },
  { label: "街头", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_jietou_1.jpg", x: 106, y: 1095 },
  { label: "街头", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_jietou_2.jpg", x: 188, y: 1095 },
  { label: "家居", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_jiaju_1.jpg", x: 24, y: 1258 },
  { label: "家居", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_jiaju_2.jpg", x: 106, y: 1258 },
  { label: "家居", img: "https://libtv-res.liblib.art/character-studio/liblibtv-character-studio-cdn-2026-09-21/styling/catalog/morden_female_jiaju_3.jpg", x: 188, y: 1258 },
];

// ★ 这一页的滚动区高度（★ 由上面的数据**算**出来 ⟹ ⟹ 不是手打常数）
const OUTFIT_CLOTHES_SCROLL_HEIGHT =
  Math.max(...OUTFIT_CLOTHES_CARDS.map((c) => c.y + 155)) + 80;

// ★★ Batch 849：P2「AI 生成」页（★ 源站实测；raw ＝ 848 的 `source-848-p2.json`）
//   ★ ★ 这一页**没有**底部生成遮罩 ⟹ ⟹「确认生成」在**内容流**里（★ 与 P1 **不同**）
//   · 卡片 240×168 @rel(24,8)（圆角 16、白 6% 底）
//   · 输入框 240×140 @rel(24,8)（13px／20px）
//   · 底部行 240×28 @rel(24,148)：① 一枚**圆按钮**（aria「选择参考图」，28×28，**没有文字**）
//                              ② 一枚**胶囊**（aria「造型技能」，119×28，文字「人设定制造型」）
//   · 「确认生成」240×36 @rel(24,192)（★ 在内容流里 ⟹ ⟹ 距卡片底 16）
// ★ ★ 那枚胶囊的文案是**一个字符串**「人设定制造型」
//   ⟹ ⟹ **不是**两枚胶囊「人设定」＋「造型」⟹ ⟹ 手打必错
const OUTFIT_AI_CARD = { w: 240, h: 168 };
const OUTFIT_AI_TEXTAREA = {
  w: 240,
  h: 140,
  placeholder: "描述或上传参考图，复刻发型 / 妆造 / 服装",
};
const OUTFIT_AI_ROUND_BTN = { aria: "选择参考图", w: 28, h: 28 };
const OUTFIT_AI_PILL = {
  aria: "造型技能",
  label: "人设定制造型",
  w: 119,
  h: 28,
};
const OUTFIT_AI_UPLOAD_ARIA = "上传造型参考图";
const OUTFIT_AI_GENERATE = { w: 240, h: 36 };
// ★ 这一页的内容底（「确认生成」的底）＝ 8(内容起点) ＋ 168(卡) ＋ 16(间距) ＋ 36(按钮)
const OUTFIT_AI_CONTENT_BOTTOM = 8 + OUTFIT_AI_CARD.h + 16 + OUTFIT_AI_GENERATE.h;

// ★★ Batch 846：这一段的**滚动区高度**（源站实测 1312）
//   ＝ 内容底（最后一个色块的底）＋ 80(pb-20) ⟹ ⟹ 由上面的数据**算**出来 ⟹ ⟹ 不是手打常数
const OUTFIT_CONTENT_BOTTOM = Math.max(
  ...OUTFIT_LIP_COLORS.map((c) => c.y + 35),
  ...OUTFIT_MAKEUP_CARDS.map((c) => c.y + 96),
);
const OUTFIT_SCROLL_HEIGHT = OUTFIT_CONTENT_BOTTOM + 80;

// ★★ Batch 846：左列第四段「服装造型」
//   ⟹ ⟹ 源站实测这一段**有标题行** ⟹ ⟹ 右栏第一层是**子页签行**（40 高）
//   ⟹ ⟹ 内容起点 ＝ 列顶 + 40 + 16(pt-4) ⟹ ⟹ 比「脸部精修」段**低 40px**
//   ⟹ ⟹ 「服装」「AI 生成」两枚子页签的**内容未实测** ⟹ ⟹ 点它们显示如实说明
  const renderOutfit = () => (
    <div className="ce-panel ce-panel--outfit">
      <div
        className="ce-section"
        style={{ minHeight: `${OUTFIT_SCROLL_HEIGHT}px` }}
      >
        {OUTFIT_SECTION_TITLES.map((t) => (
          <h3
            key={t.title}
            className="ce-h3 ce-h3--section"
            style={{ top: `${t.top}px` }}
            data-character-editor-outfit-title={t.title}
          >
            {t.title}
          </h3>
        ))}

        {/* ★ 发型：7 枚 chip（★「现代」初始选中）＋ 12 张卡 */}
        {OUTFIT_HAIR_CHIPS.map((c) => {
          const on = outfitHairChip === c.label;
          return (
            <button
              key={`hair-chip-${c.label}`}
              type="button"
              aria-pressed={on}
              className={`ce-chip${on ? " is-on" : ""}`}
              style={{ top: `${c.y}px`, left: `${c.x}px`, width: `${c.w}px` }}
              data-character-editor-outfit-chip={`发型-${c.label}`}
              onClick={() => setOutfitHairChip(c.label)}
            >
              {c.label}
            </button>
          );
        })}
        {OUTFIT_HAIR_CARDS.map((c) => {
          const key = `发型-${c.label}`;
          const on = outfitCardSel[key] === c.label;
          return (
            <button
              key={`hair-card-${c.label}`}
              type="button"
              aria-label={c.label}
              aria-pressed={on}
              className={`ce-card ce-card--outfit${on ? " is-on" : ""}`}
              style={{ top: `${c.y}px`, left: `${c.x}px` }}
              data-character-editor-outfit-card={key}
              onClick={() =>
                setOutfitCardSel((prev) => ({ ...prev, [key]: on ? "" : c.label }))
              }
            >
              <span className="ce-card-media">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={c.img} alt="" />
              </span>
              <span className="ce-card-name">{c.label}</span>
            </button>
          );
        })}

        {/* ★ 发色：11 枚色块（10 色 ＋ 1 枚「自定义颜色」；★ 初始选中**第一枚**） */}
        {OUTFIT_HAIR_COLORS.map((c, i) => {
          const on = outfitHairColor === i;
          return (
            <button
              key={`hair-color-${i}`}
              type="button"
              aria-label={c.custom ? "自定义颜色" : "选择发色"}
              aria-pressed={on}
              className={`ce-swatch${on ? " is-on" : ""}${
                c.custom ? " ce-swatch--custom" : ""
              }`}
              style={{ top: `${c.y}px`, left: `${c.x}px`, background: c.color }}
              data-character-editor-outfit-swatch={`发色-${i}`}
              onClick={() =>
                c.custom
                  ? flash("clone mock：自定义颜色未接取色器")
                  : setOutfitHairColor(i)
              }
            >
              {c.custom ? (
                <span className="ce-swatch-icon">
                  <Plus size={18} />
                </span>
              ) : null}
            </button>
          );
        })}

        {/* ★ 妆容：7 枚 chip（★ 宽度随文案变）＋ 7 张卡 */}
        {OUTFIT_MAKEUP_CHIPS.map((c) => {
          const on = outfitMakeupChip === c.label;
          return (
            <button
              key={`makeup-chip-${c.label}`}
              type="button"
              aria-pressed={on}
              className={`ce-chip${on ? " is-on" : ""}`}
              style={{ top: `${c.y}px`, left: `${c.x}px`, width: `${c.w}px` }}
              data-character-editor-outfit-chip={`妆容-${c.label}`}
              onClick={() => setOutfitMakeupChip(c.label)}
            >
              {c.label}
            </button>
          );
        })}
        {OUTFIT_MAKEUP_CARDS.map((c) => {
          const key = `妆容-${c.label}`;
          const on = outfitCardSel[key] === c.label;
          return (
            <button
              key={`makeup-card-${c.label}`}
              type="button"
              aria-label={c.label}
              aria-pressed={on}
              className={`ce-card ce-card--outfit${on ? " is-on" : ""}`}
              style={{ top: `${c.y}px`, left: `${c.x}px` }}
              data-character-editor-outfit-card={key}
              onClick={() =>
                setOutfitCardSel((prev) => ({ ...prev, [key]: on ? "" : c.label }))
              }
            >
              <span className="ce-card-media">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={c.img} alt="" />
              </span>
              <span className="ce-card-name">{c.label}</span>
            </button>
          );
        })}

        {/* ★ 口红：10 枚色块（★ 初始选中**第二枚**） */}
        {OUTFIT_LIP_COLORS.map((c, i) => {
          const on = outfitLipColor === i;
          return (
            <button
              key={`lip-color-${i}`}
              type="button"
              aria-label="选择口红颜色"
              aria-pressed={on}
              className={`ce-swatch${on ? " is-on" : ""}`}
              style={{ top: `${c.y}px`, left: `${c.x}px`, background: c.color }}
              data-character-editor-outfit-swatch={`口红-${i}`}
              onClick={() => setOutfitLipColor(i)}
            />
          );
        })}
      </div>
    </div>
  );

  // ★★ Batch 849：P1「服装」页（★ 源站实测；raw ＝ 848 的 `source-848-p1.json`）
  //   · 小标题「服装」240×22 @rel(24,16)
  //   · 7 枚分类 chip（50×26，★ 初始「现代」选中 ⟹ 白底黑字）
  //   · 24 张服装卡（76×155：图 74×133 ＋ 名字 16 高）
  //   · ★ 这一页**有**底部生成遮罩（「确认生成」240×36）⟹ ⟹ 与 P2 **不同**
  const renderOutfitClothes = () => (
    <div className="ce-panel ce-panel--outfit">
      <div
        className="ce-section"
        style={{ minHeight: `${OUTFIT_CLOTHES_SCROLL_HEIGHT}px` }}
      >
        <h3
          className="ce-h3 ce-h3--section"
          style={{ top: "16px" }}
          data-character-editor-outfit-clothes-title="服装"
        >
          服装
        </h3>

        {/* ★ 7 枚分类 chip（★ 「现代」初始选中 ⟹ 白底黑字） */}
        {OUTFIT_CLOTHES_CHIPS.map((c) => {
          const on = outfitClothesChip === c.label;
          return (
            <button
              key={`clothes-chip-${c.label}`}
              type="button"
              aria-pressed={on}
              className={`ce-chip ce-chip--clothes${on ? " is-on" : ""}`}
              style={{ top: `${c.y}px`, left: `${c.x}px`, width: `${c.w}px` }}
              data-character-editor-outfit-clothes-chip={c.label}
              onClick={() => setOutfitClothesChip(c.label)}
            >
              {c.label}
            </button>
          );
        })}

        {/* ★ 24 张服装卡（★ 图是**引用**源站 CDN 的真实图） */}
        {OUTFIT_CLOTHES_CARDS.map((c, i) => {
          const on = outfitClothesCardSel[c.img] === c.img;
          return (
            <button
              key={`clothes-card-${i}`}
              type="button"
              aria-label={c.label}
              aria-pressed={on}
              className={`ce-card ce-card--clothes${on ? " is-on" : ""}`}
              style={{ top: `${c.y}px`, left: `${c.x}px` }}
              data-character-editor-outfit-clothes-card={c.img}
              onClick={() =>
                setOutfitClothesCardSel((prev) => ({
                  ...prev,
                  [c.img]: on ? "" : c.img,
                }))
              }
            >
              <span className="ce-card-media">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={c.img} alt="" />
              </span>
              <span className="ce-card-name">{c.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );

  // ★★ Batch 849：P2「AI 生成」页（★ 源站实测；raw ＝ 848 的 `source-848-p2.json`）
  //   ★ ★ 这一页**没有**底部生成遮罩 ⟹ ⟹「确认生成」在**内容流**里（★ 与 P1 **不同**）
  //   · 卡片 240×168 @rel(24,8)（圆角 16、白 6% 底）
  //   · 输入框 240×140（13px／20px）
  //   · 底部行 240×28：① 圆按钮（aria「选择参考图」，28×28）② 胶囊（aria「造型技能」，119×28）
  //   · 「确认生成」240×36 @rel(24,192)
  const renderOutfitAi = () => (
    <div className="ce-panel ce-panel--outfit">
      <div
        className="ce-section ce-section--outfit-ai"
        style={{ minHeight: `${OUTFIT_AI_CONTENT_BOTTOM + 16}px` }}
      >
        <div
          className="ce-outfit-ai-card"
          style={{
            top: "8px",
            left: "24px",
            width: `${OUTFIT_AI_CARD.w}px`,
            height: `${OUTFIT_AI_CARD.h}px`,
          }}
          data-character-editor-outfit-ai-card="1"
        >
          <textarea
            className="ce-outfit-ai-textarea"
            aria-label={OUTFIT_AI_TEXTAREA.placeholder}
            placeholder={OUTFIT_AI_TEXTAREA.placeholder}
            value={outfitAiText}
            onChange={(e) => setOutfitAiText(e.target.value)}
            style={{
              width: `${OUTFIT_AI_TEXTAREA.w}px`,
              height: `${OUTFIT_AI_TEXTAREA.h}px`,
            }}
            data-character-editor-outfit-ai-textarea="1"
          />
          <div className="ce-outfit-ai-row">
            <span className="ce-outfit-ai-round-wrap">
              <input
                type="file"
                className="ce-sr-only"
                aria-label={OUTFIT_AI_UPLOAD_ARIA}
                data-character-editor-outfit-ai-upload="1"
              />
              <button
                type="button"
                aria-label={OUTFIT_AI_ROUND_BTN.aria}
                className="ce-outfit-ai-round"
                style={{
                  width: `${OUTFIT_AI_ROUND_BTN.w}px`,
                  height: `${OUTFIT_AI_ROUND_BTN.h}px`,
                }}
                data-character-editor-outfit-ai-round="1"
                onClick={() =>
                  flash("clone mock：参考图上传未接真实上传")
                }
              >
                <ImagePlus size={16} />
              </button>
            </span>
            <span className="ce-outfit-ai-pill-wrap">
              <button
                type="button"
                aria-label={OUTFIT_AI_PILL.aria}
                className="ce-outfit-ai-pill"
                style={{
                  width: `${OUTFIT_AI_PILL.w}px`,
                  height: `${OUTFIT_AI_PILL.h}px`,
                }}
                data-character-editor-outfit-ai-pill={OUTFIT_AI_PILL.label}
                onClick={() =>
                  flash(`clone mock：「${OUTFIT_AI_PILL.label}」未接真实技能`)
                }
              >
                <span className="ce-outfit-ai-pill-inner">
                  <Shirt size={16} />
                  <span className="ce-outfit-ai-pill-text">
                    {OUTFIT_AI_PILL.label}
                  </span>
                </span>
                <ChevronDown size={14} />
              </button>
            </span>
          </div>
        </div>

        {/* ★ 「确认生成」在**内容流**里（★ 这一页**没有**底部生成遮罩）
            ★ 源站实测：输入框**为空**时它是**禁用态** ⟹ ⟹ clone 照抄 */}
        <button
          type="button"
          className="ce-outfit-ai-generate"
          disabled={!outfitAiText.trim()}
          style={{
            top: `${OUTFIT_AI_CARD.h + 24}px`,
            left: "24px",
            width: `${OUTFIT_AI_GENERATE.w}px`,
            height: `${OUTFIT_AI_GENERATE.h}px`,
          }}
          data-character-editor-outfit-ai-generate="1"
          onClick={() =>
            flash("clone mock：确认生成不消耗积分，也不产出真实资产")
          }
        >
          <Sparkles size={18} />
          <span>确认生成</span>
        </button>
      </div>
    </div>
  );

  // ★★ Batch 846：这一段的**子页签行**（★ 与「脸部精修」段的页签行**同一个组件**）
  //   ★ 「服装」「AI 生成」两枚的**内容未实测** ⟹ ⟹ 显示如实说明，不编造控件
  const renderOutfitTabs = () => (
    // ★★ 「服装造型」段的子页签行**不是**脸部段那一行（★ 源站实测：那边 `justify-between`
    //   ⟹ ⟹ 这边 `gap-3` 靠左）⟹ ⟹ 故另开 `.ce-tabs--sub`
    <div className="ce-tabs ce-tabs--sub" role="tablist">
      {OUTFIT_TABS.map((item) => {
        const on = outfitTab === item.id;
        return (
          <button
            key={item.id}
            type="button"
            role="tab"
            aria-selected={on}
            aria-label={item.label}
            className={`ce-tab ${on ? "is-text" : "is-icon"}${on ? " is-on" : ""}`}
            style={{ width: `${on ? item.wOn : item.wOff}px` }}
            data-character-editor-outfit-tab={item.id}
            onClick={() => setOutfitTab(item.id)}
          >
            <span className="ce-tab-icon" aria-hidden="true">
              <item.icon size={18} />
            </span>
            {on ? <span className="ce-tab-text">{item.label}</span> : null}
          </button>
        );
      })}
    </div>
  );

  // ★★ Batch 847：左列第五段「音色音调」的**标题行页签**
  //   ★ 源站实测：这一段的**标题行就是页签行**（三枚：音色库／我的音色／AI 生成）
  //   ⟹ ⟹ 与脸部段的页签行**同一个组件**（`.ce-tabs` ＋ `.ce-tab`）⟹ ⟹ 文字页签跟着选中项移动
  //   ★ 但**排布不同**：脸部段是 `space-between`（均分）⟹ ⟹ 这边是 `gap-5`（20px）⟹ ⟹ 另开修饰类
  // ★★ Batch 848：**宽度随选中态变** —— 源站实测三份 raw 交叉校验：
  //   选中：音色库 70／我的音色 84／AI 生成 73；未选中：一律 24（文字盒被裁成 0 宽）
  //   ⟹ ⟹ 宽度由 `VOICE_TABS[i].wOn`（选中）／`.wOff`（未选中）给出 ⟹ ⟹ **不是手打常数**
  const renderVoiceTabs = () => (
    <div className="ce-tabs ce-voice-tabs" role="tablist">
      {VOICE_TABS.map((item) => {
        const on = voiceTab === item.id;
        return (
          <button
            key={item.id}
            type="button"
            role="tab"
            aria-selected={on}
            aria-label={item.label}
            className={`ce-tab ${on ? "is-text" : "is-icon"}${on ? " is-on" : ""}`}
            style={{ width: `${on ? item.wOn : item.wOff}px` }}
            data-character-editor-voice-tab={item.id}
            onClick={() => setVoiceTab(item.id)}
          >
            <span className="ce-tab-icon" aria-hidden="true">
              <item.icon size={18} />
            </span>
            {on ? <span className="ce-tab-text">{item.label}</span> : null}
          </button>
        );
      })}
    </div>
  );

  // ★★ Batch 847：第五段的**工具行**（★ 源站实测：两枚 32×32，间隙 2px）
  //   「搜索」＋「筛选音色」⟹ ⟹ 这两个 aria 是**实测**的（batch 841 raw），不是手打
  //   ★ 图标**字形未采集**（源站是 iconify SVG）⟹ ⟹ 用 lucide 占位
  //   ★ 源站这两枚的**行为未实测**（那趟只点了分段）⟹ ⟹ 点击是 mock，不假装
  const renderVoiceTools = () => (
    <div className="ce-voice-tools">
      <button
        type="button"
        className="ce-voice-tool"
        aria-label="搜索"
        data-character-editor-voice-tool="search"
        onClick={() => flash("clone mock：音色搜索未接真实接口")}
      >
        <Search size={16} />
      </button>
      <button
        type="button"
        className="ce-voice-tool"
        aria-label="筛选音色"
        data-character-editor-voice-tool="filter"
        onClick={() => flash("clone mock：音色筛选未接真实接口")}
      >
        <SlidersHorizontal size={16} />
      </button>
    </div>
  );

  // ★★ Batch 847：第五段的**音色卡列表**（★ 源站实测：20 张 240×48，步进 56）
  //   ★ 卡的结构：主按钮 198×40（图标区 40×40 ＋ 文字区 158×36）＋ 播放按钮 32×32
  //   ★ 选中态：**第一张**是白 1px 边框 ＋ 透明底；其余是透明边框 ＋ 白 6% 底
  const renderVoiceList = () => (
    <div
      className="ce-voice-list"
      data-character-editor-voice-list
      style={
        {
          "--voice-card-h": `${VOICE_CARD_HEIGHT}px`,
          "--voice-card-gap": `${VOICE_CARD_GAP}px`,
          "--voice-scroll-h": `${VOICE_SCROLL_HEIGHT}px`,
        } as CSSProperties
      }
    >
      <div className="ce-voice-cards">
        {VOICES.map((v) => {
          const on = voiceSel === v.name;
          return (
            <div
              key={v.name}
              className={`ce-voice-card${on ? " is-on" : ""}`}
              data-character-editor-voice-card={v.name}
            >
              <button
                type="button"
                className="ce-voice-main"
                aria-label={v.name}
                aria-pressed={on}
                data-character-editor-voice-main={v.name}
                onClick={() => setVoiceSel(v.name)}
              >
                <span className="ce-voice-icon" aria-hidden="true">
                  <User size={16} />
                </span>
                <span className="ce-voice-text">
                  <span className="ce-voice-name">{v.name}</span>
                  <span className="ce-voice-sub">{v.sub}</span>
                </span>
              </button>
              <button
                type="button"
                className="ce-voice-play"
                aria-label="播放"
                data-character-editor-voice-play={v.name}
                onClick={() => flash("clone mock：音色试听未接真实音频")}
              >
                <Play size={14} />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );

  // ★★ Batch 848：**P3「我的音色」页**（★ 源站实测，raw/source-848-p3.json）
  //   ★ 这一页**也有工具行**（搜索／筛选音色）⟹ ⟹ 与「音色库」页同构
  //     ⟹ ⟹ ★ 这是 clone 的一处**既存偏差**：batch 847 时这一页显示的是「未实测」说明，
  //     ⟹ ⟹ 说明里还写着「0 枚工具」⟹ ⟹ 而源站**确实有**那两枚 ⟹ ⟹ 本批改正。
  //   ★ 内容是**空态**：「暂无音色数据」240×96（★ 该账号没有自己的音色）
  const renderVoiceMine = () => (
    <>
      {renderVoiceTools()}
      <div
        className="ce-voice-list ce-voice-list--mine"
        data-character-editor-voice-list="mine"
      >
        <p
          className="ce-voice-empty"
          data-character-editor-voice-empty="mine"
          style={{
            width: `${VOICE_MINE_EMPTY.w}px`,
            height: `${VOICE_MINE_EMPTY.h}px`,
            fontSize: VOICE_MINE_EMPTY.fontSize,
            lineHeight: VOICE_MINE_EMPTY.lineHeight,
            color: VOICE_MINE_EMPTY.color,
          }}
        >
          {VOICE_MINE_EMPTY.text}
        </p>
      </div>
    </>
  );

  // ★★ Batch 848：**P4「AI 生成」页**（★ 源站实测，raw/source-848-p4.json）
  //   ★ 这一页**没有工具行**⟹ ⟹ 内容区直接从标题行下方开始
  //   ★ 结构：输入框 240×120 ＋「生成音色」按钮 240×36（右侧角标「21」）
  //          ＋「生成历史」小标题 ＋ 空态「暂无历史记录」240×64
  //   ★ 「生成音色」点了会真的产出资产 ⟹ ⟹ clone 只弹提示，**不消耗** ⚡44
  const renderVoiceAi = () => (
    <div
      className="ce-voice-ai"
      data-character-editor-voice-ai
      style={{
        width: `${VOICE_AI.content.w}px`,
        height: `${VOICE_AI.content.h}px`,
        paddingTop: `${VOICE_AI.content.padTop}px`,
        paddingBottom: `${VOICE_AI.content.padBottom}px`,
      }}
    >
      <textarea
        className="ce-voice-ai-textarea"
        aria-label={VOICE_AI.textarea.ariaLabel}
        placeholder={VOICE_AI.textarea.placeholder}
        data-character-editor-voice-textarea
        style={{
          width: `${VOICE_AI.textarea.w}px`,
          height: `${VOICE_AI.textarea.h}px`,
          borderRadius: `${VOICE_AI.textarea.radius}px`,
          padding: `${VOICE_AI.textarea.padding}px`,
          borderWidth: `${VOICE_AI.textarea.borderWidth}px`,
          borderColor: VOICE_AI.textarea.borderColor,
          fontSize: VOICE_AI.textarea.fontSize,
          lineHeight: VOICE_AI.textarea.lineHeight,
          color: VOICE_AI.textarea.color,
          background: VOICE_AI.textarea.background,
        }}
      />
      <button
        type="button"
        className="ce-voice-ai-gen"
        aria-label={VOICE_AI.generate.label}
        data-character-editor-voice-generate
        onClick={() => flash("clone mock：生成音色未接真实接口（不消耗 ⚡44）")}
        style={{
          width: `${VOICE_AI.generate.w}px`,
          height: `${VOICE_AI.generate.h}px`,
          borderRadius: `${VOICE_AI.generate.radius}px`,
          gap: `${VOICE_AI.generate.gap}px`,
          fontSize: VOICE_AI.generate.fontSize,
          lineHeight: VOICE_AI.generate.lineHeight,
          color: VOICE_AI.generate.color,
          background: VOICE_AI.generate.background,
          marginTop: `${VOICE_AI.content.genGap}px`,
        }}
      >
        <Sparkles size={18} aria-hidden="true" />
        {VOICE_AI.generate.label}
        <span
          className="ce-voice-ai-badge"
          data-character-editor-voice-badge
          style={{
            width: `${VOICE_AI.badge.w}px`,
            height: `${VOICE_AI.badge.h}px`,
            gap: `${VOICE_AI.badge.gap}px`,
            opacity: VOICE_AI.badge.opacity,
          }}
        >
          <Zap size={16} aria-hidden="true" />
          <span
            className="ce-voice-ai-badge-num"
            style={{
              width: `${VOICE_AI.badge.numberW}px`,
              height: `${VOICE_AI.badge.numberH}px`,
              fontSize: VOICE_AI.badge.numberFontSize,
            }}
          >
            {VOICE_AI.badge.number}
          </span>
        </span>
      </button>
      <section
        className="ce-voice-ai-history"
        data-character-editor-voice-history
        style={{ marginTop: `${VOICE_AI.content.historyGap}px` }}
      >
        <h3
          className="ce-voice-ai-history-title"
          style={{
            width: `${VOICE_AI.history.titleW}px`,
            height: `${VOICE_AI.history.titleH}px`,
            fontSize: VOICE_AI.history.titleFontSize,
            lineHeight: VOICE_AI.history.titleLineHeight,
            fontWeight: VOICE_AI.history.titleFontWeight,
            color: VOICE_AI.history.titleColor,
          }}
        >
          {VOICE_AI.history.title}
        </h3>
        <p
          className="ce-voice-ai-history-empty"
          data-character-editor-voice-history-empty
          style={{
            width: `${VOICE_AI.history.emptyW}px`,
            height: `${VOICE_AI.history.emptyH}px`,
            fontSize: VOICE_AI.history.emptyFontSize,
            lineHeight: VOICE_AI.history.emptyLineHeight,
            color: VOICE_AI.history.emptyColor,
            paddingTop: `${VOICE_AI.history.emptyPadY}px`,
            paddingBottom: `${VOICE_AI.history.emptyPadY}px`,
          }}
        >
          {VOICE_AI.history.empty}
        </p>
      </section>
    </div>
  );

  // ★★ 页签行（★ 源站实测：**只在「脸部精修」段存在** ⟹ ⟹ 别的段**不显示**它）
  //   ★ 抽成函数（★ batch 844）：⟹ ⟹ 阴性臂 N6 可以注入「页签行在不该出现的段也出现」
  //   这条**真实**缺陷 ⟹ ⟹ 而不必塞一个假的标记元素。
  const renderTabs = () => (
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
          {tab === item.id ? <span className="ce-tab-text">{item.label}</span> : null}
        </button>
      ))}
    </div>
  );

  // ★★ 一个**块**（标题／预设卡组／滑杆组）
  const renderBlock = (block: PanelBlock, index: number) => {    if (block.kind === "h3") {
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
    if (block.kind === "makeup") {
      return renderMakeup(block);
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
            {/* ★★ Batch 843：**页签行只在「脸部精修」段存在**（源站实测，batch 841 raw）
                ⟹ ⟹ 切到别的段 ⟹ 右栏**不显示页签行**，而是那一段自己的内容
                ⟹ ⟹ clone 之前**每段都显示页签行** ⟹ ⟹ 那是**结构上的假象** ⟹ ⟹ 本批改正。 */}
            {segment === "face" ? renderTabs() : null}

            {segment === "face" ? (
              <>
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
              </>
            ) : segment === "traits" ? (
              // ★★ Batch 844：左列第二段「脸部 & 身体特征」**已实现**
              //   ⟹ ⟹ 源站实测这一段：H3「纹身 & 疤痕」＋ 6 张 76×54 的贴纸卡
              //   ⟹ ⟹ 且这一段**没有标题行** ⟹ ⟹ 右栏**第一层就是滚动区**
              renderTraits()
            ) : segment === "body" ? (
              // ★★ Batch 845：左列第三段「身材塑形」**已实现**
              //   ⟹ ⟹ 源站实测这一段：**18 条**滑杆（5 条量程 −100..100、6 条带「i」）
              //   ⟹ ⟹ 且这一段**也没有标题行** ⟹ ⟹ 右栏**第一层就是滚动区**
              renderBody()
            ) : segment === "outfit" ? (
              // ★★ Batch 846：左列第四段「服装造型」**已实现**
              //   ⟹ ⟹ 源站实测这一段**有标题行** ⟹ ⟹ 右栏第一层是**子页签行**
              //   ⟹ ⟹ 「造型」这一页 ＝ 四个小节（发型／发色／妆容／口红）
              // ★★ Batch 849：三枚子页签**全部实测并实现**
              //   ① 「造型」：四个小节（batch 846）
              //   ② 「服装」：小标题 ＋ 7 枚分类 chip ＋ **24 张**服装卡（★ **有**底部生成遮罩）
              //   ③ 「AI 生成」：一张卡（输入框 ＋ 圆按钮 ＋ 胶囊）＋「确认生成」
              //      ⟹ ⟹ ★ 这一页**没有**底部生成遮罩 ⟹ ⟹「确认生成」在**内容流**里
              <>
                {renderOutfitTabs()}
                {outfitTab === "style" ? (
                  renderOutfit()
                ) : outfitTab === "clothes" ? (
                  renderOutfitClothes()
                ) : (
                  renderOutfitAi()
                )}
              </>
            ) : segment === "voice" ? (
              // ★★ Batch 847：左列第五段「音色音调」**已实现**
              //   ⟹ ⟹ 源站实测这一段**有标题行**（三枚页签）⟹ ⟹ 下面还有一行工具 ＋ 一张滚动区
              //   ⟹ ⟹ **这一段没有底部生成行**（★ batch 841 raw ⟹ ⟹ 右栏底部无任何按钮）
              // ★★ Batch 848：**三页全部实测并实现**
              //   ① 「音色库」：工具行 ＋ 20 张音色卡（batch 847）
              //   ② 「我的音色」：**也有工具行** ＋ 空态「暂无音色数据」（★ raw p3）
              //   ③ 「AI 生成」：**没有工具行** ＋ 输入框 ＋「生成音色」＋「生成历史」（★ raw p4）
              //   ⟹ ⟹ ★ 「未实测入口只显示如实说明」这条纪律**由第四段的两枚子页签继续承载**
              <>
                {renderVoiceTabs()}
                {voiceTab === "library" ? (
                  <>
                    {renderVoiceTools()}
                    {renderVoiceList()}
                  </>
                ) : voiceTab === "mine" ? (
                  renderVoiceMine()
                ) : (
                  renderVoiceAi()
                )}
              </>
            ) : null}

            {/* ★★ Batch 847：**源站的底部生成行是按段不同的**，本批把三处偏差一次改正：
                ⟹ ⟹ ① **「脸部精修」段**：196＋gap 8＋36（「智能调整」那枚在）
                ⟹ ⟹ ② **「脸部 & 身体特征」「身材塑形」「服装造型」三段**：
                ⟹ ⟹    **整宽 240×36 的「确认生成」，没有「智能调整」**
                ⟹ ⟹    （★ batch 841 raw 实测：那三段的底部只有一个 `w-full` 按钮）
                ⟹ ⟹    ⟹ ⟹ clone 之前**这三段**（traits/body）还在显示 196＋「智能调整」
                ⟹ ⟹    ⟹ ⟹ 那是**既存偏差**，本批改正（★ 846 只改了 outfit 那一段）
                ⟹ ⟹ ③ **「音色音调」段**：**整行都不渲染**
                ⟹ ⟹    （★ batch 841 raw 实测：第五段右栏底部**没有任何按钮**
                ⟹ ⟹     ⟹ ⟹ 且 batch 847 raw 的 43 个「带文字的叶子」里
                ⟹ ⟹     ⟹ ⟹ 只有标题行 3 个 ＋ 音色卡 40 个 ⟹ ⟹ 没有「确认生成」
                ⟹ ⟹     ⟹ ⟹ ⟹ ⟹ 这两条是**互相独立**的证据）
                ⟹ ⟹ ★ 「确认生成」那枚 flex:1 ⟹ ⟹ 少一枚就正好 240
                ★★ Batch 849：**第四段的「AI 生成」子页签**也**不渲染**底部生成行
                ⟹ ⟹ （★ 源站实测：那一页的「确认生成」在**内容流**里 ⟹ ⟹ 底部**没有**遮罩）
                ⟹ ⟹ ⟹ ⟹ 而「服装」子页签**有**底部遮罩（★ 与「AI 生成」**不同**）*/}
            {(segment === "voice" ||
              (segment === "outfit" && outfitTab === "ai")) ? null : (
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
                {segment === "face" ? (
                  <button
                    type="button"
                    className="ce-smart"
                    aria-label="智能调整"
                    data-character-editor-smart
                    onClick={() => flash("clone mock：智能调整未接真实算法")}
                  >
                    <Sparkles size={18} />
                  </button>
                ) : null}
              </div>
            )}
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
