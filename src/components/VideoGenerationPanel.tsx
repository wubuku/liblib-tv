"use client";

import { createPortal } from "react-dom";

import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import {
  Check,
  ChevronDown,
  Film,
  Gem,
  Settings2,
  Link2,
  LoaderCircle,
  Search,
  ShieldCheck,
  Sparkles,
  Zap,
} from "lucide-react";
import { useUIStore } from "@/store/uiStore";
import { PillIcon } from "@/components/nodes/ToolbarPillIcons";
import { cn } from "@/lib/utils";
import type {
  LongVideoProcessInput,
  VideoContinuationMetadata,
} from "@/store/canvasStore";

type MenuName = "model" | "mode" | "params" | "advanced" | null;
type VideoMode = "omnireference" | "image-reference" | "long-video" | "first-frame";

interface VideoGenerationPanelProps {
  zoom: number;
  attempt: string | null;
  onAttemptChange?: (value: string | null) => void;
  /** Batch 215: 源站直证——特效应用后特效 pill 文案变为「替换」。 */
  effectApplied?: boolean;
  onEffectApplied?: () => void;
  onSelectEffect?: (name: string) => void;
  initialPrompt?: string;
  continuation?: VideoContinuationMetadata;
  onCreateLongVideoProcess?: (input: LongVideoProcessInput) => string | null;
  onClearContinuation?: () => void;
  onDestroyFirstFrame?: () => void;
}

const defaultPrompt = "起始状态：@陈默（图片 1）充满杀伤力的眼神锁定镜头。动作过程：镜头平滑而缓慢地向他冷厉的双眼推移。他在第1秒开始说出如刀刃般的台词。对白（@陈默，冷酷且有力）：‘当初你离开的时候，怎么没想过我会担心？’结束状态：镜头停止在他充满恨意的双眸。音效：环境音完全静默，只余沉重的台词回响。";

// Batch 252: 源站 2026-09-09 直采——首尾帧芯片自动预填的 AI 过渡文案
// （原样存档作为 clone 的预填样例）。
const FIRST_LAST_PROMPT =
  "手从白帆布包中取出青柠气泡水罐的特写，过渡到短发女生在户外草地仰头喝同款气泡水的中景，日系清新治愈风格，明亮自然光，柔和暖调，胶片质感，动作流畅自然";

const references = [
  { id: 1, name: "陈默", image: "/images/scene-coffee-1.png" },
  { id: 2, name: "咖啡", image: "/images/scene-coffee-2.png" },
  { id: 3, name: "分镜", image: "/images/storyboard-2.png" },
];

const modelItems = [
  // Batch 141: 2026-09-07 源站模型菜单全量采样（35 项,顺序/文案/生成时长对齐）。
  { id: "2.5", title: "Seedance 2.5", estimate: "2min", premium: true, family: "seedance", description: "最强视频模型，全能参考，30s音画同步" },
  { id: "2.0 VIP", title: "Seedance 2.0 VIP", estimate: "2min", premium: true, family: "seedance", description: "最强视频模型，会员专属通道，15s音画同步" },
  { id: "Minimax H3 Max", title: "Minimax H3 Max", estimate: "30s", premium: false, family: "minimax", description: "后训练极速视频生成，支持文生、图生及首尾帧控制" },
  { id: "Minimax H3", title: "Minimax H3", estimate: "2min", premium: true, family: "minimax", description: "全模态输入，多参数控制，多场景商用级生成" },
  { id: "2.0 Fast VIP", title: "Seedance 2.0 Fast VIP", estimate: "2min", premium: true, family: "seedance", description: "最强视频模型快速版，会员专属通道，15s音画同步" },
  { id: "2.0 Mini", title: "Seedance 2.0 Mini", estimate: "2min", premium: true, family: "seedance", description: "最强视频模型mini版，高性价比生成，15s音画同步" },
  { id: "Wan 3.0 Prime", title: "Wan 3.0 Prime", estimate: "1min", premium: false, family: "wan", description: "超快速生成，全模态参考，超写实高一致性" },
  { id: "Wan 3.0", title: "Wan 3.0", estimate: "3min", premium: false, family: "wan", description: "全模态参考，支持文档与网页输入，超写实高一致性生成" },
  { id: "Happy Horse 1.1", title: "Happy Horse 1.1", estimate: "3min", premium: false, family: "happyhorse", description: "阿里最新视频模型，一致性与视听质量更可控" },
  { id: "Happy Horse 1.0", title: "Happy Horse 1.0", estimate: "3min", premium: false, family: "happyhorse", description: "阿里视频模型，支持多参生成" },
  { id: "Kling O3", title: "Kling O3", estimate: "3min", premium: false, family: "kling", description: "视频编辑模型、参考一致性、音画同出、多镜头" },
  { id: "Kling 3.0 Turbo", title: "Kling 3.0 Turbo", estimate: "3min", premium: false, family: "kling", description: "视频生成模型，高质感、支持多镜头" },
  { id: "Kling 3.0", title: "Kling 3.0", estimate: "3min", premium: false, family: "kling", description: "视频生成模型，高质感、支持多镜头" },
  { id: "Wan 2.7", title: "Wan 2.7", estimate: "3min", premium: false, family: "wan", description: "全能参考，支持修改视频画面、剧情、环境" },
  { id: "Kling O1", title: "Kling O1", estimate: "3min", premium: false, family: "kling", description: "可灵一代编辑模型、支持多模态输入" },
  { id: "Wan 2.6", title: "Wan 2.6", estimate: "3min", premium: false, family: "wan", description: "音画同步，支持多机位镜头，最长可生15秒视频" },
  { id: "Hailuo 2.3", title: "Hailuo 2.3", estimate: "2min", premium: false, family: "hailuo", description: "善于表达动作、表情、镜头，更高质感" },
  { id: "Seedance 1.5 Pro", title: "Seedance1.5 Pro", estimate: "2min", premium: false, family: "seedance", description: "音画同步，支持多机位镜头，最长可生12秒视频" },
  { id: "Seedance 1.0 Pro", title: "Seedance 1.0 Pro", estimate: "2min", premium: false, family: "seedance", description: "高精度提示词理解，40秒生成1080P视频" },
  { id: "Seedance 1.0 Lite", title: "Seedance 1.0 Lite", estimate: "1min", premium: false, family: "seedance", description: "轻量快速，一键进行日常视频生成" },
  { id: "Kling 2.6", title: "Kling 2.6", estimate: "2min", premium: false, family: "kling", description: "视频生成模型、直出音画同步" },
  { id: "Hailuo 02", title: "Hailuo 02", estimate: "2min", premium: false, family: "hailuo", description: "画质稳定，适合打造运动特效场景" },
  { id: "Vidu Q2", title: "Vidu Q2", estimate: "3min", premium: false, family: "vidu", description: "多图主体参考，精确控制效果佳" },
  { id: "Vidu Q2 Pro", title: "Vidu Q2 Pro", estimate: "", premium: false, family: "vidu" },
  { id: "Vidu Q2 Turbo", title: "Vidu Q2 Turbo", estimate: "", premium: false, family: "vidu" },
  { id: "Vidu Q3 Pro", title: "Vidu Q3 Pro", estimate: "2min", premium: false, family: "vidu", description: "支持主体参考，精确控制效果佳" },
  { id: "OmniHuman 1.5", title: "OmniHuman 1.5", estimate: "3min", premium: false, family: "omnihuman", description: "多模态数字人视频生成" },
  { id: "Kling 2.5", title: "Kling 2.5", estimate: "2min", premium: false, family: "kling", description: "速度快、效果稳定、性价比高" },
  { id: "Wan 2.2", title: "Wan 2.2", estimate: "3min", premium: false, family: "wan", description: "支持特效、玩法千变万化" },
  { id: "Wan 2.5", title: "Wan 2.5", estimate: "3min", premium: false, family: "wan", description: "支持特效、直出音画同步" },
  { id: "Pixverse V5.5", title: "Pixverse V5.5", estimate: "3min", premium: false, family: "pixverse", description: "支持特效、玩法丰富" },
  { id: "Pixverse V5", title: "Pixverse V5", estimate: "3min", premium: false, family: "pixverse", description: "支持特效、玩法丰富" },
  { id: "Hailuo 2.3 Fast", title: "Hailuo 2.3 Fast", estimate: "1min", premium: false, family: "hailuo", description: "善于表达动作、表情、镜头，更快速" },
  { id: "Kling 3.0 Motion", title: "Kling3.0 动作迁移", estimate: "8min", premium: false, family: "kling", description: "动作控制模型，需输入1张图片、1条视频" },
  { id: "Style Video", title: "Style Video", estimate: "2min", premium: false, family: "style", description: "图生视频效果稳定，画面表现力强" },
];

/* Batch 175: 源站模式菜单实采（2026-09-07，空节点）——仅 5 项入菜单，
   空节点下只有 文生视频 可用；超长视频/视频编辑不再出现在菜单中，
   仅作为 mode 标签查找项保留（长视频入口走节点卡尝试芯片）。
   Batch 237: 首帧生成视频芯片 → 面板模式触发器显示 全能参考（源站
   2026-09-09 直采），以 inMenu:false 的 first-frame 查找项承载。 */
const modeItems = [
  { id: "text", label: "文生视频", disabled: false },
  { id: "omnireference", label: "全能参考", disabled: true },
  { id: "image", label: "图生视频", disabled: true },
  { id: "first-last", label: "首尾帧", disabled: true },
  { id: "image-reference", label: "图片参考", disabled: true },
  { id: "video-edit", label: "视频编辑", disabled: true, inMenu: false },
  { id: "long-video", label: "超长视频", disabled: true, inMenu: false, badge: "Beta" },
  { id: "first-frame", label: "全能参考", disabled: true, inMenu: false },
] as const;

export function VideoGenerationPanel({
  zoom,
  attempt,
  onAttemptChange,
  effectApplied,
  onEffectApplied,
  onSelectEffect,
  initialPrompt,
  continuation,
  onCreateLongVideoProcess,
  onClearContinuation,
  onDestroyFirstFrame,
}: VideoGenerationPanelProps) {
  const isContinuation = Boolean(continuation);
  const [menu, setMenu] = useState<MenuName>(null);
  // Batch 158: 默认模型回落 2.5 —— 新建节点（2.5）与尝试已选节点（2.5）两个直接样本
  // 对阵预设承载节点单个 2.0 样本；2.0 为预设专属配置，非常规默认。
  const [model, setModel] = useState(
    isContinuation ? "2.5" : "2.5",
  );
  const [mode, setMode] = useState<VideoMode>("omnireference");
  const [ratio, setRatio] = useState("16:9");
  const [resolution, setResolution] = useState("720P");
  const [duration, setDuration] = useState(5);
  const [audio, setAudio] = useState(true);
  const [count, setCount] = useState(1);
  const [autoLink, setAutoLink] = useState(true);
  // Batch 146: 运镜按钮下拉菜单（CLONE_DECISION：通用影视运镜术语，源站交互未采样）。
  const [yunjingOpen, setYunjingOpen] = useState(false);
  // Batch 191: 特效库横排（源站 2026-09-08 采样）。
  const [effectsOpen, setEffectsOpen] = useState(false);
  // Batch 216: 源站直证——参考 pill 进入「选择参考」模式，顶部横幅引导。
  const [refSelectMode, setRefSelectMode] = useState(false);
  // Batch 217: 标记 pill 同为选择模式横幅（源站 JS 点击直采）。
  const [markSelectMode, setMarkSelectMode] = useState(false);
  // Batch 191: 特效库展开时覆盖触发器（源站同构）——外部 mousedown 关闭。
  useEffect(() => {
    if (!effectsOpen) return;
    const handleMouseDown = (event: MouseEvent) => {
      const target = event.target as HTMLElement | null;
      if (target?.closest("[data-effects-gallery]") || target?.closest("[data-effects-trigger]")) return;
      setEffectsOpen(false);
    };
    document.addEventListener("mousedown", handleMouseDown);
    return () => document.removeEventListener("mousedown", handleMouseDown);
  }, [effectsOpen]);
  const [yunjingSelection, setYunjingSelection] = useState<string | null>(null);
  const [fastMode, setFastMode] = useState(false);
  const [networkSearch, setNetworkSearch] = useState(true);
  const [materialCheck, setMaterialCheck] = useState(true);
  const [prompt, setPrompt] = useState(
    initialPrompt ?? (isContinuation ? "" : defaultPrompt),
  );
  const [showProcess, setShowProcess] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [longVideoSubmitting, setLongVideoSubmitting] = useState(false);
  const longVideoSubmitTimerRef =
    useRef<ReturnType<typeof setTimeout> | null>(null);
  const isLongVideo = mode === "long-video";
  // Batch 249: 源站 2026-09-09 直采——OmniHuman 1.5 为特殊双输入面板：
  // 无 pill/提示词（需求槽 图片1/1+音频0/1 替代）、模式触发器=模型名、
  // 设置芯片「自适应 · 1个」（无比例/清晰度/时长段）、积分 28、
  // 高级区为 快速模式 + AutoLink。
  const isOmniHuman = model === "OmniHuman 1.5";
  // Batch 155: 5分钟超长视频芯片将时长范围切到 30..300（否则 300s 在 4..30 滑杆上半态）。
  const isLongRange = isLongVideo || attempt === "5分钟超长视频";
  const durationMin = isLongRange ? 30 : 4;
  const durationMax = isLongRange ? 300 : 30;
  // Batch 236/237/238: 源站 2026-09-09 决定性 A/B（t4 截图）——2.5·16:9·5s = 230
  // = 2.5·Auto·5s：模型内比例不改变单价，定价为**模型平价率 × 时长 × 数量**：
  // 2.5→46/s、2.0 VIP→27/s（405/15s）、2.0 Fast VIP→22/s（110/5s 双比例）、
  // 2.0 Mini→16/s（80/5s）；长视频管线恒 49/s（14700/300s）。Batch 130 的
  // 16:9·5s=135 归属 2.0 VIP 态（27×5 精确吻合）——「比例影响积分」结论废止，
  // 该读数是模型混淆。其余模型族未采样（SOURCE_UNKNOWN），按 27/s 缺省。
  const credits = isLongVideo
    ? duration * 49
    : isOmniHuman
      ? 28
      : Math.round(
        duration
        * count
          * (resolution === "1080P"
            ? (MODEL_RATES_1080P[model] ?? MODEL_RATES[model] ?? 27)
            : resolution === "480P"
              ? (MODEL_RATES_480P[model] ?? MODEL_RATES[model] ?? 27)
              : (MODEL_RATES[model] ?? 27)),
        );
  // Batch 145: 源站默认模式显示 文生视频（ omnireference 内部 id 映射到源站 文生视频 显示）。
  // Batch 149: 续写面板锁定的是全能参考（提示文案「仅支持 Seedance 2.5 的全能参考模式」），触发器保留 全能参考。
  const modeLabel = isContinuation
    ? "全能参考"
    : isOmniHuman
      ? "OmniHuman 1.5"
      : mode === "omnireference"
        ? "文生视频"
        : modeItems.find((item) => item.id === mode)?.label ?? "全能参考";
  // Batch 249: OmniHuman 设置芯片为「自适应 · 1个」（无比例/清晰度/时长段）。
  const settingsLabel = isOmniHuman
    ? "自适应 · 1个"
    : `${ratio} · ${resolution} · ${duration}s · ${count}个 ·`;

  // Batch 159: 尝试芯片移入节点卡内，状态由 VideoNode 持有；联动用「渲染期调整」
  // （React 官方 prop 变更派生状态模式，避免 effect 内同步 setState）。
  // Batch 177: prevAttempt 以 null 起步——面板重挂载（选择丢失/undo）后
  // attempt 仍在节点上时，挂载即重放联动（芯片非 toggle，无法靠再点触发）。
  const [prevAttempt, setPrevAttempt] = useState<string | null>(null);
  if (attempt !== prevAttempt) {
    setPrevAttempt(attempt);
    // Batch 128+160: 源站尝试芯片驱动设置联动——5分钟超长视频整组切换：
    // mode=超长视频（长视频公式 49/s，页脚实拍 14700）+ Auto+300s；
    // Batch 176: 源站页脚直证长芯片同时把模型切到 2.5（长视频管线模型）。
    if (attempt === "5分钟超长视频") {
      setMode("long-video");
      setModel("2.5");
      setRatio("Auto");
      setDuration(300);
    } else if (attempt === "首帧生成视频") {
      // Batch 237: 源站 2026-09-09 直采——首帧芯片后模式触发器显示 全能参考、
      // Auto·720P·5s·1个、积分 230（2.5·Auto·5s）。
      setMode("first-frame");
      setRatio("Auto");
      setDuration(5);
    } else if (attempt === "首尾帧生成视频") {
      // Batch 252: 源站直采——首尾帧芯片：模型切 2.0、全能参考、
      // 16:9·720P·5s·1个、提示词预填过渡文案（积分源站 155，clone 公式
      // 27/s×5=135，漂移记录于 batch 251 README）。
      setMode("first-frame");
      setModel("2.0");
      setRatio("16:9");
      setDuration(5);
      setPrompt(FIRST_LAST_PROMPT);
    } else if (attempt !== null) {
      setRatio("Auto");
      setDuration(5);
    } else if (prevAttempt === "5分钟超长视频") {
      // Batch 155/160: 取消 5 分钟芯片回到常规模式并钳制时长（CLONE_DECISION，源站未采样取消）。
      // Batch 178: 功能式守卫——若用户已通过模式菜单另选模式，保留用户选择。
      setMode((current) => (current === "long-video" ? "omnireference" : current));
      setDuration((value) => Math.min(value, 30));
    }
  }

  useEffect(() => {
    return () => {
      if (longVideoSubmitTimerRef.current) {
        clearTimeout(longVideoSubmitTimerRef.current);
      }
    };
  }, []);

  const selectMode = (nextMode: VideoMode) => {
    if (isContinuation) return;
    // Batch 178: 源站直证——模式菜单切出超长视频即清除尝试芯片（时长 ≤30 由
    // 下方钳制与联动分支共同保证）。
    if (attempt === "5分钟超长视频" && nextMode !== "long-video") {
      onAttemptChange?.(null);
    }
    setMode(nextMode);
    setDuration(nextMode === "long-video" ? 30 : Math.min(30, Math.max(4, duration)));
    setShowProcess(false);
    setSubmitted(false);
    setMenu(null);
  };

  const selectModel = (nextModel: string) => {
    // Batch 236: 源站 2026-09-09 双向直采——2.5 长视频态下切换模型（2.0 VIP）：
    // 模式重置 文生视频、时长 300→15、尝试芯片高亮清除；切回 2.5 不恢复长模式。
    if (isLongVideo && nextModel !== "2.5") {
      if (attempt === "5分钟超长视频") onAttemptChange?.(null);
      setMode("omnireference");
      setDuration(15);
      setShowProcess(false);
      setSubmitted(false);
    }
    // Batch 236/237: 清晰度列表随模型（4K 仅 2.0 VIP；Fast VIP 仅 480P/720P）。
    // 目标列表不含当前清晰度时钳制到不高于原选择的最高项（CLONE_DECISION，
    // 源站仅直证列表差异，未采样切换时的钳制行为）。
    const nextResolutions = MODEL_RESOLUTIONS[nextModel] ?? DEFAULT_RESOLUTIONS;
    if (!nextResolutions.includes(resolution)) {
      const rank = (value: string) => RESOLUTION_ORDER.indexOf(value);
      const current = rank(resolution);
      const candidates = nextResolutions.filter((value) => rank(value) <= current);
      setResolution(candidates[candidates.length - 1] ?? nextResolutions[0]);
    }
    // Batch 240: 模型默认清晰度——切入 Seedance 1.5 Pro 即切 1080P（源站
    // 观察值）；其余模型无缺省定义时保持当前清晰度（钳制规则见上）。
    const defaultResolution = MODEL_DEFAULT_RESOLUTIONS[nextModel];
    if (defaultResolution !== undefined && nextResolutions.includes(defaultResolution)) {
      setResolution(defaultResolution);
    }
    setModel(nextModel);
    setMenu(null);
  };

  const submitVideo = () => {
    if (!isLongVideo) {
      setSubmitted(true);
      return;
    }
    if (
      longVideoSubmitting ||
      longVideoSubmitTimerRef.current ||
      !onCreateLongVideoProcess
    ) {
      return;
    }
    setLongVideoSubmitting(true);
    setSubmitted(false);
    longVideoSubmitTimerRef.current = setTimeout(() => {
      longVideoSubmitTimerRef.current = null;
      const processId = onCreateLongVideoProcess({
        prompt,
        model,
        ratio,
        resolution,
        durationSeconds: duration,
        audio,
        credits,
        referenceCount: references.length,
      });
      setLongVideoSubmitting(false);
      setSubmitted(Boolean(processId));
      setShowProcess(Boolean(processId));
    }, 520);
  };

  return (
    <div
      data-video-generation-panel
      className="nodrag nowheel nopan absolute -bottom-[17px] left-1/2 z-20 w-[660px] -translate-x-1/2 translate-y-full origin-top"
      // The bordered node is the containing block, so 17 flow units produce the source's 16-unit outer gap.
      style={{ transform: `scale(${1 / zoom})` }}
    >
      {/* Batch 161: 面板增高至 397px —— Batch 149 纵向开关列后原 274px 已溢出（提示词被压到 16px、高级设置越界 35px）；
          源站提示词区实测 96px（2026-09-07）。 */}
      <section className="relative flex h-[397px] flex-col rounded-2xl border border-[#363636] bg-[#262626] p-2 shadow-[0_22px_60px_rgba(0,0,0,0.52)]">
        <div data-video-toolbar className="flex h-8 shrink-0 items-center gap-1">
          {/* Batch 188: pill 图标为源站 iconify (libtv) 原字形直采。
              Batch 212: 角色库 pill 打开左侧栏角色库面板（对齐源站行为）。 */}
          {/* Batch 215: 源站直证——特效应用后特效 pill 文案变「替换」。 */}
          {/* Batch 249: OmniHuman 面板无工具行——需求槽行替代。 */}
          {!isOmniHuman && [
            { label: "参考" },
            { label: "标记" },
            { label: effectApplied ? "替换" : "特效", hasMenu: true },
            { label: "角色库", hasMenu: true },
            { label: "运镜", hasMenu: true },
          ]
            .filter(
              (item) =>
                !attempt ||
                MODEL_PILL_SETS[model] === undefined ||
                MODEL_PILL_SETS[model].includes(item.label.replace(/^替换$/, "特效")),
            )
            .map((item) => {
            if ("hasMenu" in item && item.hasMenu) {
              if (item.label === "角色库") {
                return (
                  <div key={item.label} className="relative">
                    <button
                      type="button"
                      data-clib-trigger
                      onClick={() => {
                        // Batch 212: 角色库 pill 打开左侧栏角色库面板。
                        useUIStore.getState().setPrimaryPanel("character");
                      }}
                      className="flex h-[26px] items-center gap-1.5 rounded-full bg-white/[0.05] px-2 py-1 text-xs text-[#aaa] hover:bg-white/[0.09] hover:text-white"
                    >
                      <PillIcon label={item.label} />
                      {item.label}
                    </button>
                  </div>
                );
              }
              if (item.label === "特效") {
                return (
                  <div key={item.label} className="relative">
                    <button
                      type="button"
                      data-effects-trigger
                      onClick={() => setEffectsOpen(!effectsOpen)}
                      className={cn(
                        "flex h-[26px] items-center gap-1.5 rounded-full bg-white/[0.05] px-2 py-1 text-xs text-[#aaa] hover:bg-white/[0.09] hover:text-white",
                        effectsOpen && "bg-white/[0.1] text-white",
                      )}
                    >
                      <PillIcon label={item.label} />
                      {item.label}
                    </button>
                  </div>
                );
              }
              return (
                <div key={item.label} className="relative">
                  <button
                    type="button"
                    data-yunjing-trigger
                    onClick={() => setYunjingOpen(!yunjingOpen)}
                    className="flex h-[26px] items-center gap-1.5 rounded-full bg-white/[0.05] px-2 py-1 text-xs text-[#aaa] hover:bg-white/[0.09] hover:text-white"
                  >
                    <PillIcon label={item.label} />
                    {item.label}
                  </button>
                  {yunjingOpen && (
                    /* Batch 213: 源站运镜菜单直采——23 运动卡片画廊（189×208，
                       远端 webp 缩略图按 tool/movement/N.webp 顺序、悬停收藏、
                       名称居中），替代 clone-shaped 12 项文本菜单。 */
                    <div data-yunjing-menu className="absolute bottom-10 right-0 z-50 grid max-h-[560px] w-[799px] grid-cols-4 gap-2 overflow-y-auto rounded-xl border border-white/10 bg-[#292929] p-2 shadow-2xl">
                      {[
    { id: "movement-01", name: "固定镜头", image: `https://libtv-res.liblib.art/tool/movement/1.webp` },
    { id: "movement-02", name: "跟随拍摄", image: `https://libtv-res.liblib.art/tool/movement/2.webp` },
    { id: "movement-03", name: "盘旋抬升", image: `https://libtv-res.liblib.art/tool/movement/3.webp` },
    { id: "movement-04", name: "盘旋下降", image: `https://libtv-res.liblib.art/tool/movement/4.webp` },
    { id: "movement-05", name: "镜头上摇", image: `https://libtv-res.liblib.art/tool/movement/5.webp` },
    { id: "movement-06", name: "镜头下摇", image: `https://libtv-res.liblib.art/tool/movement/6.webp` },
    { id: "movement-07", name: "镜头左摇", image: `https://libtv-res.liblib.art/tool/movement/7.webp` },
    { id: "movement-08", name: "镜头右摇", image: `https://libtv-res.liblib.art/tool/movement/8.webp` },
    { id: "movement-09", name: "镜头上升", image: `https://libtv-res.liblib.art/tool/movement/9.webp` },
    { id: "movement-10", name: "镜头下降", image: `https://libtv-res.liblib.art/tool/movement/10.webp` },
    { id: "movement-11", name: "镜头左移", image: `https://libtv-res.liblib.art/tool/movement/11.webp` },
    { id: "movement-12", name: "镜头右移", image: `https://libtv-res.liblib.art/tool/movement/12.webp` },
    { id: "movement-13", name: "镜头前推", image: `https://libtv-res.liblib.art/tool/movement/13.webp` },
    { id: "movement-14", name: "镜头后移", image: `https://libtv-res.liblib.art/tool/movement/14.webp` },
    { id: "movement-15", name: "变焦推进", image: `https://libtv-res.liblib.art/tool/movement/15.webp` },
    { id: "movement-16", name: "变焦拉远", image: `https://libtv-res.liblib.art/tool/movement/16.webp` },
    { id: "movement-17", name: "柯克变焦", image: `https://libtv-res.liblib.art/tool/movement/17.webp` },
    { id: "movement-18", name: "环绕拍摄", image: `https://libtv-res.liblib.art/tool/movement/18.webp` },
    { id: "movement-19", name: "滚筒旋转", image: `https://libtv-res.liblib.art/tool/movement/19.webp` },
    { id: "movement-20", name: "第一视角", image: `https://libtv-res.liblib.art/tool/movement/20.webp` },
    { id: "movement-21", name: "无人机", image: `https://libtv-res.liblib.art/tool/movement/21.webp` },
    { id: "movement-22", name: "高空航拍", image: `https://libtv-res.liblib.art/tool/movement/22.webp` },
    { id: "movement-23", name: "手持拍摄", image: `https://libtv-res.liblib.art/tool/movement/23.webp` },
                      ].map((m) => (
                        <button
                          key={m.id}
                          type="button"
                          data-yunjing-option={m.id}
                          aria-pressed={yunjingSelection === m.name}
                          onClick={() => {
                            setYunjingSelection(yunjingSelection === m.name ? null : m.name);
                            setYunjingOpen(false);
                          }}
                          className="group flex w-full cursor-pointer flex-col items-center gap-0.5 rounded p-1 transition-colors hover:bg-white/[0.06]"
                        >
                          <div className="relative aspect-square w-full overflow-hidden rounded-[3px] bg-neutral-700">
                            {/* Batch 213: 源站远端 webp 缩略图（tool/movement/N.webp），保持原生 img。 */}
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img alt={m.name} className="size-full object-cover" loading="lazy" src={m.image} />
                          </div>
                          <span className="h-[17px] w-full truncate text-center text-xs text-[#ededed]">{m.name}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              );
            }
            if (item.label === "标记") {
              return (
                <button
                  key={item.label}
                  type="button"
                  data-mark-select-trigger
                  onClick={() => setMarkSelectMode(true)}
                  className="flex h-[26px] items-center gap-1.5 rounded-full bg-white/[0.05] px-2 py-1 text-xs text-[#aaa] hover:bg-white/[0.09] hover:text-white"
                >
                  <PillIcon label={item.label} />
                  {item.label}
                </button>
              );
            }
            if (item.label === "参考") {
              return (
                <button
                  key={item.label}
                  type="button"
                  data-reference-select-trigger
                  onClick={() => setRefSelectMode(true)}
                  className="flex h-[26px] items-center gap-1.5 rounded-full bg-white/[0.05] px-2 py-1 text-xs text-[#aaa] hover:bg-white/[0.09] hover:text-white"
                >
                  <PillIcon label={item.label} />
                  {item.label}
                </button>
              );
            }
            return <button key={item.label} type="button" className="flex h-[26px] items-center gap-1.5 rounded-full bg-white/[0.05] px-2 py-1 text-xs text-[#aaa] hover:bg-white/[0.09] hover:text-white"><PillIcon label={item.label} />{item.label}</button>;
          })}
          {/* Batch 249: OmniHuman 需求槽行——图片 1/1（已满足）+ 音频 0/1
              （缺失）+ 警示「请提供音频」（源站 omnihuman.png 直采）。 */}
          {isOmniHuman && (
            <div data-omnihuman-requirements className="mt-1 flex w-full min-w-0 shrink-0 flex-wrap items-start gap-2 pl-1">
              <div data-omnihuman-image-slot className="relative h-[55px] w-12 overflow-hidden rounded-lg border border-white/10">
                <Image src="/images/storyboard-2.png" alt="图片 1/1" fill sizes="48px" className="object-cover" unoptimized />
                <span className="absolute left-0.5 top-0.5 flex size-4 items-center justify-center rounded-full bg-black/70 text-[9px] text-white">1</span>
              </div>
              <div data-omnihuman-audio-slot className="flex h-[55px] w-12 items-center justify-center rounded-lg border border-dashed border-white/[0.16] text-[10px] text-[#666]">
                音频
              </div>
              <p data-omnihuman-audio-warning className="self-center text-xs text-[#f0f0f0]">请提供音频</p>
            </div>
          )}
          {effectsOpen && (
            /* Batch 191: 特效库横排（源站 2026-09-08 采样）——屏幕居中悬浮、
               8 卡横排（clone 渲染已采样的 4 张）；卡片 185×235，图区 178×178
               （clone 用渐变占位——源图为远端 webp，仅采到一张 URL）。 */
            createPortal(
              <div
                data-effects-gallery
                className="fixed left-1/2 top-[444px] z-[70] flex -translate-x-1/2 gap-2 overflow-x-auto"
              >
              {[
                { name: "试妆特写", author: "捏捏AI", credits: 185, gradient: "from-[#5a4a3f] to-[#2b2320]" },
                { name: "悬浮缓入", author: "捏捏AI", credits: 377, gradient: "from-[#3f4a5a] to-[#20262b]" },
                { name: "微距推镜", author: "可可大王", credits: 659, gradient: "from-[#4a5a3f] to-[#232b20]" },
                { name: "直升机揭幕", author: "汪往旺", credits: 144, gradient: "from-[#5a3f4a] to-[#2b2026]" },
              ].map((effect) => (
                <div
                  key={effect.name}
                  data-effects-card={effect.name}
                  onClick={() => {
                    onSelectEffect?.(effect.name);
                    // Batch 215: 特效选用后「特效」pill 文案变「替换」。
                    onEffectApplied?.();
                    setEffectsOpen(false);
                  }}
                  className="group w-[185px] shrink-0 cursor-pointer rounded-lg border border-transparent transition-colors hover:bg-canvas-controls-hover"
                >
                  <div className={cn("relative aspect-square w-full overflow-hidden rounded-lg bg-gradient-to-b", effect.gradient)}>
                    <div className="absolute inset-x-0 top-0 flex h-8 items-center justify-end p-1.5 opacity-0 transition-opacity group-hover:opacity-100">
                      <button type="button" aria-label="收藏" className="flex size-6 items-center justify-center rounded-lg bg-black/65 text-white hover:bg-black/80">
                        <svg aria-hidden="true" width="14" height="13" viewBox="0 0 22.13 20.8" fill="none">
                          <path d="M9.65.87a1.58 1.58 0 0 1 2.83 0l2.57 5.14 5.72.8c1.27.18 1.78 1.74.86 2.63l-4.14 4.03.98 5.69c.22 1.26-1.11 2.22-2.24 1.63l-5.11-2.69-5.11 2.69c-1.13.59-2.46-.37-2.24-1.63l.98-5.69L.55 8.44c-1.03-1-.46-2.45 1.1-2.63l5.72-.8L9.65.87z" fill="currentColor" />
                        </svg>
                      </button>
                    </div>
                  </div>
                  <div className="flex items-center justify-between px-1 pt-1.5">
                    <span className="text-[13px] text-[#eeeeee]">{effect.name}</span>
                    <span className="rounded bg-white/[0.06] px-1 py-0.5 text-[10px] text-[#9a9a9a]">商用</span>
                  </div>
                  <div className="flex items-center justify-between px-1 pt-0.5 text-[11px] text-[#8a8a8a]">
                    <span>{effect.author}</span>
                    <span className="text-[#c8a86b]">{effect.credits}</span>
                  </div>
                </div>
              ))}
              </div>,
              document.body,
            )
          )}
          {markSelectMode && (
            /* Batch 217: 源站直采——标记选择模式横幅（316×56，顶部居中）。 */
            createPortal(
              <div
                data-mark-select-banner
                className="fixed left-1/2 top-3 z-[80] flex w-[316px] -translate-x-1/2 items-center gap-4 rounded-2xl bg-[#1F6DFF] p-3 text-white shadow-[var(--canvas-shadow-panel)]"
              >
                {/* Batch 218: 源站横幅样式直采——蓝底圆角 + 魔棒图标 + 标题/副题
                    + 返回节点按钮 + × 关闭。 */}
                <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-white/20">
                  <svg aria-hidden="true" width="16" height="16" viewBox="0 0 20.6 20.6" fill="none">
                    <path
                      d="M7.93 6.82q.41-.07.8.08l11 4.5a1.4 1.4 0 0 1 .53 2.2q-.3.36-.74.46l-4.34 1.04-.05.03-.03.05-1.04 4.34a1.4 1.4 0 0 1-2.66.2L6.9 8.74a1.4 1.4 0 0 1 1.03-1.9M12.6 17.9l.75-3.14a1.9 1.9 0 0 1 1.28-1.37l.13-.04 3.14-.75-8.97-3.67zm-8.55-7.82a.9.9 0 0 1 1.3 1.24l-1.9 2a.9.9 0 0 1-1.3-1.24zM.03 5.66a.9.9 0 0 1 1.1-.63l2.9.8a.9.9 0 0 1-.47 1.74l-2.9-.8a.9.9 0 0 1-.63-1.1m12.05-3.51a.9.9 0 0 1 1.24 1.3l-2 1.9a.9.9 0 0 1-1.24-1.3zM5.66.03a.9.9 0 0 1 1.1.63l.8 2.9a.9.9 0 0 1-1.73.48l-.8-2.9a.9.9 0 0 1 .63-1.1"
                      fill="currentColor"
                    />
                  </svg>
                </div>
                <div className="flex min-w-0 flex-1 flex-col gap-0.5">
                  <span className="text-[13px] font-medium">元素选择模式</span>
                  <span className="text-[11px] opacity-90">点击图片选择局部元素</span>
                </div>
                <button
                  type="button"
                  data-mark-select-return
                  className="shrink-0 rounded-lg bg-white/20 px-2.5 py-1 text-[11px] text-white hover:bg-white/30"
                >
                  返回节点
                </button>
                <button
                  type="button"
                  aria-label="关闭"
                  className="shrink-0 text-white/80 hover:text-white"
                >
                  ×
                </button>
              </div>,
              document.body,
            )
          )}
          {refSelectMode && (
            /* Batch 216: 源站直采——参考 pill 进入选择模式，顶部横幅引导
               「从画布或资产管理选择参考返回节点」（364×56，屏幕顶居中）。 */
            createPortal(
              <div
                data-reference-select-banner
                className="fixed left-1/2 top-3 z-[80] flex w-[364px] -translate-x-1/2 items-center justify-center rounded-lg bg-[#1d1d1d] px-4 py-3 text-xs text-[#ededed] shadow-[0_10px_28px_rgba(0,0,0,0.45)]"
              >
                从画布或资产管理选择参考返回节点
              </div>,
              document.body,
            )
          )}
          {isContinuation && onClearContinuation && (
            <button
              data-video-continuation-exit
              type="button"
              onClick={onClearContinuation}
              className="ml-auto h-7 rounded-lg px-2.5 text-xs text-[#9a9a9a] hover:bg-white/[0.07] hover:text-white"
            >
              退出续写模式
            </button>
          )}
          {/* Batch 166: 「3 个匹配」AutoLink 芯片移除 —— 2026-09-07 两种面板状态的工具行均只有 5 个 pill，
              且其打开的 advanced 弹窗已被 Batch 149 内联列取代。 */}
        </div>

        {/* Batch 160: 源站 2026-09-07 新建节点整面板实拍无「新功能」条，原 Batch 125 条目移除。 */}

        {showProcess ? (
          <LongVideoProcessInfo
            created={submitted}
            duration={duration}
            onBack={() => setShowProcess(false)}
          />
        ) : (
          <>
            {continuation ? (
              <>
                <div
                  data-video-continuation-source
                  className="mt-1 flex h-12 shrink-0 items-center gap-2"
                >
                  <div className="relative size-12 overflow-hidden rounded-lg border border-white/10">
                    <Image
                      src={continuation.sourcePosterUrl ?? "/images/scene-coffee-4.png"}
                      alt={continuation.sourceLabel}
                      fill
                      sizes="48px"
                      className="object-cover"
                      unoptimized
                    />
                    <span className="absolute left-0.5 top-0.5 flex size-4 items-center justify-center rounded-full bg-black/70 text-[9px] text-white">1</span>
                  </div>
                  <p className="min-w-0 truncate text-xs text-[#757575]">
                    智能续写仅支持 Seedance 2.5 的全能参考模式
                  </p>
                </div>
                <div
                  data-video-continuation-context
                  className="mt-1 flex min-h-0 flex-1 flex-col rounded-xl bg-black/10 px-2 py-1.5"
                >
                  <p className="shrink-0 truncate text-xs leading-5 text-[#d8d8d8]">
                    对 <span className="text-white">{continuation.sourceLabel}</span> 的{" "}
                    <span data-video-continuation-range className="tabular-nums text-[#09caf5]">
                      {continuation.startSeconds.toFixed(2)}s-{continuation.endSeconds.toFixed(2)}s
                    </span>{" "}
                    片段进行续写：
                  </p>
                  <textarea
                    value={prompt}
                    onChange={(event) => { setPrompt(event.target.value); setSubmitted(false); }}
                    placeholder="请输入需要续写的内容"
                    aria-label="视频生成提示词"
                    className="min-h-0 flex-1 resize-none bg-transparent text-sm leading-6 text-[#ededed] outline-none placeholder:text-[#595959] selection:bg-[#09caf5]/30"
                  />
                </div>
              </>
            ) : isOmniHuman ? (
              <>
                {/* Batch 249: OmniHuman 内容区由需求槽行占据（上方），无提示词
                    输入框；模式=模型名、芯片=自适应 · 1个（见 footer 标签）。 */}
                <div className="min-h-0 flex-1" />
              </>
            ) : attempt === "首尾帧生成视频" ? (
              <>
                {/* Batch 252: 源站直采——首尾帧面板为双参考槽（首帧/尾帧）+
                    预填 AI 过渡文案的提示词框。 */}
                <div data-video-firstlast-slots className="mt-1 flex w-full min-w-0 shrink-0 flex-wrap items-start gap-2 pl-1">
                  <div className="relative h-[55px] w-12 overflow-hidden rounded-lg border border-white/10">
                    <Image src="/images/storyboard-2.png" alt="首帧参考" fill sizes="48px" className="object-cover" unoptimized />
                    <span className="absolute left-0.5 top-0.5 flex size-4 items-center justify-center rounded-full bg-black/70 text-[9px] text-white">1</span>
                  </div>
                  <div className="relative h-[55px] w-12 overflow-hidden rounded-lg border border-white/10">
                    <Image src="/images/scene-coffee-2.png" alt="尾帧参考" fill sizes="48px" className="object-cover" unoptimized />
                    <span className="absolute left-0.5 top-0.5 flex size-4 items-center justify-center rounded-full bg-black/70 text-[9px] text-white">2</span>
                  </div>
                </div>
                <textarea
                  value={prompt}
                  onChange={(event) => { setPrompt(event.target.value); setSubmitted(false); }}
                  aria-label="视频生成提示词"
                  className="mt-1 min-h-0 flex-1 resize-none p-2 text-sm leading-6 text-[#ededed] outline-none selection:bg-[#09caf5]/30"
                />
              </>
            ) : attempt === "首帧生成视频" ? (
              <>
                {/* Batch 239: 源站 2026-09-09 直采——首帧态面板为 参考槽（角标 1）
                    + 说明文案，无提示词输入框（a1 截图）。槽图为本地图（源站为
                    自动创建图片节点的示例图内容，CLONE_DECISION）。 */}
                <div data-video-firstframe-slot className="group mt-1 flex w-full min-w-0 shrink-0 flex-wrap items-start gap-2 pl-1">
                  <div className="relative h-[55px] w-12 cursor-grab overflow-hidden rounded-lg border border-white/10 active:cursor-grabbing">
                    <Image src="/images/storyboard-2.png" alt="首帧参考" fill sizes="48px" className="object-cover" unoptimized />
                    <span className="absolute left-0.5 top-0.5 flex size-4 items-center justify-center rounded-full bg-black/70 text-[9px] text-white">1</span>
                    {/* Batch 244: 源站 2026-09-09 截图——槽悬停出现「销毁」按钮；
                        点击行为（移除自动创建的图片节点与连线）为 CLONE_DECISION。 */}
                    {onDestroyFirstFrame && (
                      <button
                        type="button"
                        data-video-firstframe-destroy
                        onClick={onDestroyFirstFrame}
                        className="absolute inset-0 hidden items-center justify-center bg-black/70 text-[10px] text-white group-hover:flex"
                      >
                        销毁
                      </button>
                    )}
                  </div>
                </div>
                <p data-video-firstframe-hint className="mt-3 shrink-0 px-2 text-[15px] leading-6 text-[#f0f0f0]">
                  以当前图为首帧生成视频。
                </p>
              </>
            ) : (
              <>
                {/* Batch 160: 源站新建节点无引用时不渲染槽行（工具行直连提示词）。
                    Batch 165: 源站槽行类 flex-wrap items-start pl-1、无固定高度（h-12 曾裁切 55px 槽）。 */}
                {references.length > 0 && (
                <div className="mt-1 flex w-full min-w-0 shrink-0 flex-wrap items-start gap-2 pl-1">
                  {references.map((reference) => (
                    // Batch 149: 源站引用槽 48×55 cursor-grab（2026-09-07 实拍）。
                    <div key={reference.id} className="relative h-[55px] w-12 cursor-grab overflow-hidden rounded-lg border border-white/10 active:cursor-grabbing">
                      <Image src={reference.image} alt={`${reference.name}参考`} fill sizes="48px" className="object-cover" unoptimized />
                      <span className="absolute left-0.5 top-0.5 flex size-4 items-center justify-center rounded-full bg-black/70 text-[9px] text-white">{reference.id}</span>
                    </div>
                  ))}
                </div>
                )}
                <textarea
                  value={prompt}
                  onChange={(event) => { setPrompt(event.target.value); setSubmitted(false); }}
                  aria-label="视频生成提示词"
                  placeholder="描述你想要生成的画面内容，@引用素材"
                  className="mt-1 min-h-0 flex-1 resize-none p-2 text-sm leading-6 text-[#ededed] outline-none selection:bg-[#09caf5]/30"
                />
              </>
            )}
          </>
        )}

        <footer className="mt-1 flex h-8 shrink-0 items-center gap-1 text-xs text-[#dfdfdf]">
          <div className="relative">
            <button data-video-model-trigger data-video-continuation-locked={isContinuation || undefined} type="button" disabled={isContinuation} onClick={() => setMenu(menu === "model" ? null : "model")} className="flex h-8 w-auto min-w-[88px] shrink-0 items-center justify-between gap-1 rounded-lg px-2 py-1 hover:bg-white/[0.06] disabled:cursor-default disabled:hover:bg-transparent">
              {/* Batch 149: 源站触发器显示缩写名（Seedance 2.0 VIP → 2.0）。 */}
              {/* Batch 164: 源站触发器类 min-w-[88px] justify-between、13px 常规字重（2026-09-07 链采样）。 */}
              <span className="truncate text-[13px]">{MODEL_TRIGGER_LABELS[model] ?? model.replace(/ VIP$/, "")}</span><ChevronDown size={12} className="shrink-0 text-[#777]" />
            </button>
            {menu === "model" && <ModelMenu model={model} onSelect={selectModel} />}
          </div>
          <div className="relative">
            <button data-video-mode-trigger data-video-continuation-locked={isContinuation || undefined} type="button" disabled={isContinuation} onClick={() => setMenu(menu === "mode" ? null : "mode")} className="flex h-8 shrink-0 items-center justify-center gap-1 rounded-lg py-1 pl-2 pr-2.5 hover:bg-white/[0.06] disabled:cursor-default disabled:hover:bg-transparent">{modeLabel}<ChevronDown size={12} className="text-[#777]" /></button>
            {menu === "mode" && <ModeMenu mode={mode} onSelect={selectMode} />}
          </div>
          <div className="relative min-w-0">
            <button data-video-params-trigger type="button" onClick={() => setMenu(menu === "params" ? null : "params")} className="flex h-8 min-w-0 max-w-[205px] shrink items-center justify-between gap-1 rounded-lg px-2 hover:bg-white/[0.06]"><span className="truncate">{settingsLabel}</span><ChevronDown size={12} className="shrink-0 text-[#777]" /></button>
            {menu === "params" && (
              <ParamsMenu model={model} ratio={ratio} resolution={resolution} duration={duration} durationMin={durationMin} durationMax={durationMax} audio={audio} count={count} isLongVideo={isLongRange} onRatio={setRatio} onResolution={setResolution} onDuration={setDuration} onAudio={setAudio} onCount={setCount} />
            )}
          </div>

          {isLongVideo && <button type="button" onClick={() => setShowProcess((show) => !show)} className="h-8 shrink-0 rounded-lg px-2 text-[#09caf5] hover:bg-[#09caf5]/10">{showProcess ? "返回编辑" : "查看过程"}</button>}
          {/* Batch 151: 源站积分块 min-w-[85px] justify-end、fg-muted 灰调、数值 12px/15px（2026-09-07 实拍）。 */}
          {/* Batch 186: footer 图标按钮组按源站顺序与字形直采对齐
              （doc-sparkle / 文A 翻译 / lucide settings2 / credits / 生成上箭头；
                源站按钮无 aria/title，点击语义未采样——保持占位）。 */}
          <button type="button" data-footer-icon="doc-sparkle" className="flex size-8 shrink-0 items-center justify-center rounded-lg text-[#aaa] hover:bg-white/[0.06]">
            <svg aria-hidden="true" width="16" height="16" viewBox="0 0 20 20" fill="none">
              <path
                d="M10.26 1.67c.32 0 .57.25.57.57v.35c0 .32-.25.58-.57.58h-6.1a1 1 0 0 0-1 1v11.66a1 1 0 0 0 1 1h11.67a1 1 0 0 0 1-1v-6.1c0-.3.26-.56.58-.56h.35c.32 0 .57.25.57.57v6.1a2.5 2.5 0 0 1-2.37 2.49H3.97a2.44 2.44 0 0 1-2.3-2.37V4.17a2.5 2.5 0 0 1 2.5-2.5zm3.9 10.91a.75.75 0 0 1 0 1.5H5.84a.75.75 0 0 1 0-1.5zm-2.5-3.33a.75.75 0 0 1 0 1.5H5.84a.75.75 0 0 1 0-1.5zm3.86-8.4c.1-.3.52-.3.63 0l.76 2.05q.05.14.2.2l2.05.75c.29.11.29.52 0 .63l-2.06.76q-.14.05-.2.2l-.75 2.05a.33.33 0 0 1-.63 0l-.76-2.05a.3.3 0 0 0-.2-.2l-2.05-.76a.33.33 0 0 1 0-.63l2.05-.75q.15-.06.2-.2zM10 5.92a.75.75 0 0 1 0 1.5H5.83a.75.75 0 0 1 0-1.5z"
                fill="currentColor"
              />
            </svg>
          </button>
          <button type="button" aria-label="翻译视频提示词" className="flex size-8 shrink-0 items-center justify-center rounded-lg text-[#aaa] hover:bg-white/[0.06]">
            <svg aria-hidden="true" width="15" height="14" viewBox="0 0 19.71 18" fill="none">
              <path
                d="M15.52 7.2c.16 0 .31.1.37.26l3.8 10a.4.4 0 0 1-.38.54h-1.03a.4.4 0 0 1-.37-.27l-.88-2.48h-4.36l-.88 2.48a.4.4 0 0 1-.37.27h-1.03a.4.4 0 0 1-.37-.54l3.79-10a.4.4 0 0 1 .37-.26zM7.7 0c.22 0 .4.18.4.4v1.4H14c.22 0 .4.18.4.4v1a.4.4 0 0 1-.4.4h-2.21a16 16 0 0 1-1.42 3.33A11 11 0 0 1 8.5 9.54l1.99 2.02c.1.11.14.28.09.42l-.43 1.16a.3.3 0 0 1-.5.1l-2.4-2.46-4.27 4.24a.4.4 0 0 1-.56 0l-.7-.7a.4.4 0 0 1 0-.56L6 9.5q-.79-.8-1.43-1.8-.55-.85-1-1.89a.3.3 0 0 1 .27-.41h1.2a.4.4 0 0 1 .35.22q.39.74.79 1.31.45.65 1.08 1.3.73-.73 1.54-2.08.8-1.33 1.2-2.55H.4a.4.4 0 0 1-.4-.4v-1c0-.22.18-.4.4-.4h5.9V.4c0-.22.18-.4.4-.4zm5.53 13.68h3.24l-1.62-4.59z"
                fill="currentColor"
              />
            </svg>
          </button>
          <button type="button" data-footer-icon="settings2" className="flex size-8 shrink-0 items-center justify-center rounded-lg text-[#aaa] hover:bg-white/[0.06]">
            <Settings2 size={16} />
          </button>
          <span data-video-credits className="ml-auto flex h-8 min-w-[85px] shrink-0 items-center justify-end gap-1.5 text-[#9a9a9a]"><Zap size={12} fill="currentColor" /><span className="text-[12px] leading-[15px]">{credits}</span></span>
          <button
            data-video-generate-submit
            data-video-long-submit-state={
              isLongVideo
                ? longVideoSubmitting
                  ? "submitting"
                  : submitted
                    ? "created"
                    : "idle"
                : undefined
            }
            type="button"
            disabled={longVideoSubmitting}
            onClick={submitVideo}
            aria-label="生成视频"
            className={cn(
              "flex size-8 shrink-0 items-center justify-center rounded-xl bg-white text-[#202020]",
              submitted && "bg-[#09caf5]",
              longVideoSubmitting && "cursor-wait bg-[#09caf5]/70 text-white",
            )}
            title={
              longVideoSubmitting
                ? "正在创建本地过程"
                : submitted
                  ? "已加入本地任务"
                  : "生成视频"
            }
          >
            {/* Batch 186: 源站生成按钮上箭头（libtv 字形直采）。 */}
            {longVideoSubmitting ? (
              <LoaderCircle
                data-video-long-submit-spinner
                size={15}
                className="animate-spin"
              />
            ) : submitted ? (
              <Check size={15} />
            ) : (
              <svg aria-hidden="true" width="15" height="15" viewBox="0 0 18 18" fill="none">
                <path
                  d="M8.3.3a1 1 0 0 1 1.4 0l8 8a1 1 0 0 1-1.4 1.4L10 3.42V17a1 1 0 1 1-2 0V3.41l-6.3 6.3A1 1 0 0 1 .3 8.29z"
                  fill="currentColor"
                />
              </svg>
            )}
          </button>
        </footer>

        {/* Batch 126: 源站高级设置内联可见（联网搜索/自动校验素材/智能引用 AutoLink）。
            Batch 149: 源站 2026-09-07 实拍为「高级设置」标题 + 纵向开关列（行高 36，开关右对齐）；
            查看过程态隐藏（过程视图独占面板，避免挤压，batch33 契约）。 */}
        {!showProcess && (
          <div data-video-advanced-inline className="shrink-0 px-2">
            {isOmniHuman ? (
              <div data-omnihuman-advanced className="flex flex-col gap-1 pb-2 pt-1">
                <SwitchRow label="快速模式" icon={<Zap size={13} />} checked={fastMode} onChange={setFastMode} />
                <SwitchRow label="智能引用 AutoLink" icon={<Link2 size={13} />} checked={autoLink} onChange={setAutoLink} />
              </div>
            ) : (
              <>
                <p data-video-advanced-label className="mx-2 pt-3 text-xs font-bold text-neutral-500">高级设置</p>
                <div className="flex flex-col gap-1 pb-2 pt-1">
                  <SwitchRow label="联网搜索" icon={<Search size={13} />} checked={networkSearch} onChange={setNetworkSearch} />
                  <SwitchRow label="自动校验素材" icon={<ShieldCheck size={13} />} checked={materialCheck} onChange={setMaterialCheck} />
                  <SwitchRow label="智能引用 AutoLink" icon={<Link2 size={13} />} checked={autoLink} onChange={setAutoLink} />
                </div>
              </>
            )}
          </div>
        )}
      </section>
    </div>
  );
}

function ModelMenu({ model, onSelect }: { model: string; onSelect: (model: string) => void }) {
  return (
    <div
      data-video-model-menu
      className="absolute bottom-8 -left-[9px] z-50 flex h-[410px] w-[380px] flex-col gap-1 overflow-y-auto rounded-xl border border-white/10 bg-[#292929] p-2 shadow-2xl"
    >
      {modelItems.map((item) => {
        const selected = model === item.id;
        const ModelIcon = item.family === "seedance" ? Film : Sparkles;
        return (
          <button
            key={item.id}
            data-video-model-option={item.id}
            type="button"
            aria-pressed={selected}
            data-selected={selected ? "true" : "false"}
            onClick={() => onSelect(item.id)}
            className={cn(
              /* Batch 174/177: 源站行系统实测——所有行固定 h-52（选中/hover 都
                 不增高），选中背景 white/15%、hover 白 10%；描述常驻 36px 列内，
                 默认下移 8px 只露 8px，hover 或选中时上滑归位（见下方注释）。 */
              "group flex h-[52px] w-full shrink-0 items-center gap-2 rounded-xl px-2 text-left transition-colors hover:bg-white/[0.1]",
              selected && "bg-white/[0.15]",
            )}
          >
            <span className="flex h-[34px] w-[34px] shrink-0 items-center justify-center rounded-lg bg-white/[0.06] text-[#d9d9d9]">
              <ModelIcon size={15} />
            </span>
            <span className="h-9 min-w-0 flex-1 overflow-hidden pr-1">
              {/* Batch 177: 源站行内滑层直采——`translate-y-2 group-hover:translate-y-0
                  group-data-[selected=true]:translate-y-0` + 200ms 过渡。 */}
              <span className="flex h-full translate-y-2 flex-col justify-start transition-transform duration-200 group-hover:translate-y-0 group-data-[selected=true]:translate-y-0">
                <span className="flex items-center gap-1.5">
                  <span className="truncate text-sm text-[#efefef]">{item.title}</span>
                  {item.premium && (
                    <Gem data-video-model-premium size={11} fill="currentColor" className="shrink-0 text-[#f3b74c]" />
                  )}
                </span>
                {item.description && (
                  <span data-video-model-description className="mt-0.5 block truncate text-[11px] leading-[14px] text-[#818181]">
                    {item.description}
                  </span>
                )}
              </span>
            </span>
            <span className="shrink-0 rounded-full bg-white/[0.06] px-2 py-1 text-[10px] text-[#8a8a8a]">
              {item.estimate}
            </span>
          </button>
        );
      })}
    </div>
  );
}

function ModeMenu({ mode, onSelect }: { mode: VideoMode; onSelect: (mode: VideoMode) => void }) {
  return (
    /* Batch 175: 源站容器 161 宽 / radius 16 / 锚在触发器上方；行 h-8、
       选中 bg-white/15（同模型菜单体系）。 */
    <div className="absolute bottom-8 left-0 z-50 flex w-[161px] flex-col rounded-2xl border border-white/10 bg-[#292929] p-2 shadow-2xl">
      <p className="px-2 pb-1.5 pt-0.5 text-xs text-[#777]">视频生成模式</p>
      {modeItems
        .filter((item) => !("inMenu" in item && item.inMenu === false))
        .map((item) => (
          <button
            key={item.id}
            data-video-mode-option={item.id}
            type="button"
            disabled={item.disabled}
            onClick={() => onSelect(item.id as VideoMode)}
            className={cn(
              "flex h-8 w-full shrink-0 items-center gap-2 rounded-lg px-2 text-left text-sm transition-colors",
              item.disabled ? "cursor-not-allowed text-[#555]" : "text-[#ddd] hover:bg-white/[0.06]",
              mode === item.id && "bg-white/[0.15] text-white",
            )}
          >
            <Film size={14} className="mr-2" />
            {item.label}
            {"badge" in item && item.badge && (
              <span className="ml-auto rounded bg-[#0d5964] px-1.5 py-0.5 text-[9px] text-[#4de1f4]">{item.badge}</span>
            )}
          </button>
        ))}
    </div>
  );
}

// Batch 236/237/238: 源站 2026-09-09 同轮对照——清晰度列表随模型：
// 2.0 VIP 4 项含 4K（p3）、2.5 3 项（p6）、2.0 Fast VIP 仅 480P/720P 2 项、
// 2.0 Mini 仅 480P/720P 2 项；其它模型族未采样（SOURCE_UNKNOWN），按 3 项缺省。
const MODEL_RESOLUTIONS: Record<string, string[]> = {
  "2.5": ["480P", "720P", "1080P"],
  "2.0 VIP": ["480P", "720P", "1080P", "4K"],
  "2.0 Fast VIP": ["480P", "720P"],
  "2.0 Mini": ["480P", "720P"],
};
const DEFAULT_RESOLUTIONS = ["480P", "720P", "1080P"];
const RESOLUTION_ORDER = ["480P", "720P", "1080P", "4K"];

// Batch 238/240: 源站 2026-09-09 直采——模型平价率（积分/s/个，720P 基准）：
// 2.5→46（230/5s，16:9 与 Auto 同价）、2.0 VIP→27（405/15s）、
// 2.0 Fast VIP→22（110/5s 双比例）、2.0 Mini→16（80/5s）；长视频恒 49。
// Batch 240 补采（同轮 16:9·720P·5s·1个 受控读数）：Minimax H3 Max→12、
// Wan 3.0 Prime→9、Wan 2.7→13、Kling O3→11、Kling 3.0 Turbo→12、
// Vidu Q2→8、Vidu Q3 Pro→10、Hailuo 2.3 Fast→4.8（24/5s）、Hailuo 02→7.2（36/5s）、
// Pixverse V5.5→12（60/5s，截图芯片直证）、Pixverse V5→9（45/5s，同流程）。
// Batch 332 复测（源站 2026-09-11，受控单变量：逐模型显式归一化 16:9·720P·5s·1个
// 后读数，双读稳定）改写/补全：
// - Wan 3.0 Prime 9→18：batch 240 的 45 实为 480P 态（同会话 A/B：480P=45、
//   720P=90，清晰度决定积分）；
// - Wan 2.7 13→10：13 为其 1080P 态费率（78/6s=13/s），720P=50（10/s）；
// - Vidu Q2 8→9：720P=45（旧 40 为低清晰度态读数）；1080p=50（10/s）；
// - 新入表：Wan 3.0→10（50/5s；2K 态 132/6s=22/s）、Wan 2.6→10（50/5s）、
//   Wan 2.2/Wan 2.5→8（各 40/5s）、Minimax H3→22（110/5s 与 132/6s@2K 双源一致）、
//   Kling 3.0→11（55/5s 标准）、Kling 2.6→10（50/5s）、Kling 2.5→5（高品质 25/5s，
//   标准档 15/5s=3/s 为会话态数据点）、Kling O1→7（35/5s 标准）、
//   Vidu Q2 Pro→9（45/5s；其 1080p=110/5s=22/s）、Vidu Q2 Turbo→16（80/5s，
//   1080p 档直证，720P 未采样）、Happy Horse 1.1→15（75/5s；120 为 1080P 态）、
//   Happy Horse 1.0→16（80/5s；192 为 1080P 态）、Hailuo 2.3→7.2（36/5s，
//   与 Hailuo 02 同价；直采 36/6s@1080P=6/s 为并列数据点）；
// - Pixverse V5.5 维持 12：60/5s 复测再证（batch 291/330 的 135 系陈旧读数，
//   恰为默认模型 2.0 的积分）；Hailuo 2.3 Fast 维持 4.8：batch 330 的 56 与
//   本轮复测冲突，且其菜单行经三种点击机制均选中相邻模型（源站虚拟化列表
//   疑似行错位 bug），无法受控采样，维持 batch 240 值并记 SOURCE_UNKNOWN。
// 未采样模型族按 27/s 缺省（SOURCE_UNKNOWN）。费率随时点可能变化（源站
// 调价），以 docs/research/liblib-canvas-batch332-2026-09-11/ 证据为准。
const MODEL_RATES: Record<string, number> = {
  "2.5": 46,
  "2.0 VIP": 27,
  "2.0 Fast VIP": 22,
  "2.0 Mini": 16,
  "Minimax H3 Max": 12,
  "Minimax H3": 22,
  "Wan 3.0 Prime": 18,
  "Wan 3.0": 10,
  "Wan 2.7": 10,
  "Wan 2.6": 10,
  "Wan 2.2": 8,
  "Wan 2.5": 8,
  "Kling O3": 11,
  "Kling 3.0 Turbo": 12,
  "Kling 3.0": 11,
  "Kling 2.6": 10,
  "Kling 2.5": 5,
  "Kling O1": 7,
  "Vidu Q2": 9,
  "Vidu Q2 Pro": 9,
  "Vidu Q2 Turbo": 16,
  "Vidu Q3 Pro": 10,
  "Hailuo 2.3": 7.2,
  "Hailuo 2.3 Fast": 4.8,
  "Hailuo 02": 7.2,
  "Seedance 1.5 Pro": 8,
  "Pixverse V5.5": 12,
  "Pixverse V5": 9,
  "Happy Horse 1.1": 15,
  "Happy Horse 1.0": 16,
};
// Batch 240: 分辨率影响积分（Seedance 1.5 Pro 同会话 A/B：720P=40 vs
// 1080P=90，切回可逆）——1080P 受控读数单列表；480P 及其它模型×分辨率
// 组合未采样（SOURCE_UNKNOWN）。
const MODEL_RATES_1080P: Record<string, number> = {
  "Seedance 1.5 Pro": 18,
  "Seedance 1.0 Pro": 15,
  "Seedance 1.0 Lite": 6,
};
// Batch 333: 480P 档费率（源站 2026-09-11 同会话 A/B 直证 Wan 3.0 Prime
// 480P=45 → 9/s，720P=90）。仅此一模型有受控读数，其余未采样
// （SOURCE_UNKNOWN）暂回退 720P 表。扩展采样因源站画布模型菜单交互
// 失效受阻，见 docs/research/liblib-canvas-batch333-2026-09-11/。
const MODEL_RATES_480P: Record<string, number> = {
  "Wan 3.0 Prime": 9,
};
// Batch 240: 模型默认清晰度——切入 Seedance 1.5 Pro 即 1080P（观察值）；
// 其余模型切换保持当前清晰度（2.0 系多轮直证）。
const MODEL_DEFAULT_RESOLUTIONS: Record<string, string> = {
  "Seedance 1.5 Pro": "1080P",
};
// Batch 240: 触发器缩写特例——Seedance 1.5 Pro 显示「Seedance1.5」
// （无空格无 Pro）；其余模型显示全名（Minimax H3 Max 等直证），
// 2.0 系沿用 replace(/ VIP$/) 缩写。
const MODEL_TRIGGER_LABELS: Record<string, string> = {
  "Seedance 1.5 Pro": "Seedance1.5",
};

// Batch 248: 源站 2026-09-09 首帧附着态逐模型采样——工具行 pill 集随模型
// 变化：Happy Horse 系仅 [参考]、Wan 2.6 为 [参考,标记,特效]（模式均为
// 首帧）；2.5 同态为全 5 pill。Wan 2.2 图生视频态为 [标记,特效,运镜]
// （clone 无该状态，仅记录）。其余模型缺省全 5（SOURCE_UNKNOWN 分布）。
const MODEL_PILL_SETS: Record<string, string[]> = {
  "Happy Horse 1.1": ["参考"],
  "Happy Horse 1.0": ["参考"],
  "Wan 2.6": ["参考", "标记", "特效"],
};

interface ParamsMenuProps {
  model: string; ratio: string; resolution: string; duration: number; durationMin: number; durationMax: number; audio: boolean; count: number; isLongVideo: boolean;
  onRatio: (value: string) => void; onResolution: (value: string) => void; onDuration: (value: number) => void; onAudio: (value: boolean) => void; onCount: (value: number) => void;
}

function ParamsMenu({ model, ratio, resolution, duration, durationMin, durationMax, audio, count, isLongVideo, onRatio, onResolution, onDuration, onAudio, onCount }: ParamsMenuProps) {
  /* Batch 190: 模型切换复测（2.5→2.0 双向直采）——普通/长模式均为 7 格含
     Auto（5 列），Batch 176 的「长 7/普 6」分割废止；Auto 仅在长模式选中。 */
  const ratios = ["Auto", "16:9", "4:3", "1:1", "3:4", "9:16", "21:9"];
  const resolutions = MODEL_RESOLUTIONS[model] ?? DEFAULT_RESOLUTIONS;

  return (
    <div
      data-video-params-menu
      data-video-params-mode={isLongVideo ? "long" : "normal"}
      className={cn(
        "absolute bottom-8 z-50 flex w-[341px] flex-col rounded-xl border border-white/10 bg-[#292929] p-3 shadow-2xl",
        isLongVideo ? "-left-[60px] h-[397px]" : "-left-[68px] h-[445px]",
      )}
    >
      <section>
        <p className="mb-2 text-xs text-[#8a8a8a]">比例</p>
        <div className="grid grid-cols-5 gap-2">
          {ratios.map((item) => (
            <button
              key={item}
              data-video-ratio-option={item}
              type="button"
              aria-pressed={ratio === item}
              onClick={() => onRatio(item)}
              className={cn(
                "flex h-[62px] min-w-0 flex-col items-center justify-center gap-1 rounded-lg border text-[11px]",
                ratio === item
                  ? "border-[#7d7d7d] bg-white/[0.1] text-white"
                  : "border-white/[0.07] bg-white/[0.025] text-[#777] hover:border-white/[0.16] hover:text-[#ddd]",
              )}
            >
              <AspectRatioGlyph ratio={item} />
              <span>{item}</span>
            </button>
          ))}
        </div>
      </section>

      <section className="mt-3">
        <p className="mb-2 text-xs text-[#8a8a8a]">清晰度</p>
        <div className={cn("grid grid-cols-3 gap-1 rounded-lg bg-black/20 p-0.5", resolutions.length >= 4 && "grid-cols-4")}>
          {resolutions.map((item) => (
            <button
              key={item}
              data-video-resolution-option={item}
              type="button"
              aria-pressed={resolution === item}
              onClick={() => onResolution(item)}
              className={cn(
                "h-8 rounded-md text-xs",
                resolution === item
                  ? "border border-[#777] bg-white/[0.12] text-white"
                  : "border border-transparent text-[#666] hover:text-[#ddd]",
              )}
            >
              {item}
            </button>
          ))}
        </div>
      </section>

      <section className="mt-3">
        <div className="flex h-7 items-center justify-between">
          <span className="text-xs text-[#8a8a8a]">视频时长</span>
          <span data-video-duration-value className="flex h-7 min-w-12 items-center justify-end gap-1 rounded-md bg-white/[0.05] px-2 text-xs text-[#d8d8d8]">
            <span>{duration}</span><span className="text-[#777]">s</span>
          </span>
        </div>
        <input
          data-video-duration
          aria-label={isLongVideo ? "超长视频时长" : "视频时长"}
          type="range"
          min={durationMin}
          max={durationMax}
          value={duration}
          onInput={(event) => onDuration(Number(event.currentTarget.value))}
          className="mt-2 h-1 w-full cursor-pointer accent-[#09caf5]"
        />
        <div className="mt-1 flex justify-between text-[10px] text-[#606060]"><span>{durationMin}s</span><span>{durationMax}s</span></div>
        {isLongVideo && (
          <p data-video-long-hint className="mt-2 text-[11px] leading-4 text-[#676767]">
            {/* Batch 176: 源站长模式提示文案直采（2026-09-08）。 */}
            因剧情和画面设计，实际时长可能略有差异
          </p>
        )}
      </section>

      <ParameterSegment
        label="生成音频"
        values={["开启", "关闭"]}
        value={audio ? "开启" : "关闭"}
        dataAttribute="audio"
        onSelect={(value) => onAudio(value === "开启")}
      />

      {!isLongVideo && (
        <ParameterSegment
          label="生成数量"
          values={["1个", "2个", "4个"]}
          value={`${count}个`}
          dataAttribute="count"
          onSelect={(value) => onCount(Number(value[0]))}
        />
      )}
    </div>
  );
}

/* Batch 189: 源站比例瓦片字形直采（2026-09-08）——17px 居中盒 + 1.5px
   border-current 内框，逐比例精确 px（Auto 12×9 / 16:9 16×9 / 4:3 12×9 /
   1:1 12×12 / 3:4 9×12 / 9:16 9×16 / 21:9 16×7）；颜色随瓦片文字色。 */
const GLYPH_DIMENSIONS: Record<string, [number, number]> = {
  Auto: [12, 9],
  "16:9": [16, 9],
  "4:3": [12, 9],
  "1:1": [12, 12],
  "3:4": [9, 12],
  "9:16": [9, 16],
  "21:9": [16, 7],
};

function AspectRatioGlyph({ ratio }: { ratio: string }) {
  const [width, height] = GLYPH_DIMENSIONS[ratio] ?? [12, 9];
  return (
    <span aria-hidden="true" className="flex size-[17px] items-center justify-center">
      <span
        className="flex-none rounded-[2px] border-[1.5px] border-current"
        style={{ width, height }}
      />
    </span>
  );
}

function ParameterSegment({
  label,
  values,
  value,
  dataAttribute,
  onSelect,
}: {
  label: string;
  values: string[];
  value: string;
  dataAttribute: "audio" | "count";
  onSelect: (value: string) => void;
}) {
  return (
    <section className="mt-3">
      <p className="mb-2 text-xs text-[#8a8a8a]">{label}</p>
      <div className="grid grid-flow-col auto-cols-fr gap-1 rounded-lg bg-black/20 p-0.5">
        {values.map((item) => (
          <button
            key={item}
            {...(dataAttribute === "audio"
              ? { "data-video-audio-option": item }
              : { "data-video-count-option": item })}
            type="button"
            aria-pressed={value === item}
            onClick={() => onSelect(item)}
            className={cn(
              "h-8 rounded-md border text-xs",
              value === item
                ? "border-[#777] bg-white/[0.12] text-white"
                : "border-transparent text-[#666] hover:text-[#ddd]",
            )}
          >
            {item}
          </button>
        ))}
      </div>
    </section>
  );
}


// Batch 149: 源站 2026-09-07 高级设置行为整行 36px（label 左 / 开关右，宽约 38×20）。
function SwitchRow({ label, icon, checked, onChange }: { label: string; icon: React.ReactNode; checked: boolean; onChange: (value: boolean) => void }) {
  return (
    <label className="flex h-9 cursor-pointer items-center justify-between gap-2 rounded-lg px-2 text-[13px] text-[#ccc] hover:bg-white/[0.05]">
      <span className="flex items-center gap-1.5">{icon}<span className="truncate">{label}</span></span>
      <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} className="sr-only" />
      <span className={cn("relative h-5 w-[38px] shrink-0 rounded-full transition-colors", checked ? "bg-[#09caf5]" : "bg-[#4a4a4a]")}>
        <span className={cn("absolute top-0.5 size-4 rounded-full bg-white transition-transform", checked ? "translate-x-[18px]" : "translate-x-0.5")} />
      </span>
    </label>
  );
}

function LongVideoProcessInfo({
  created,
  duration,
  onBack,
}: {
  created: boolean;
  duration: number;
  onBack: () => void;
}) {
  return (
    <div
      data-video-long-process-info
      className="mt-1 flex min-h-0 flex-1 flex-col items-center justify-center rounded-xl bg-[#1d1d1d] px-6 text-center"
    >
      <span className="flex size-11 items-center justify-center rounded-[8px] bg-[#17343a] text-[#3bd5ef]">
        <Film size={20} />
      </span>
      <p className="mt-3 text-sm font-medium text-[#ededed]">
        {created ? "画布过程已创建" : "过程将在提交后创建"}
      </p>
      <p className="mt-1 text-[11px] text-[#757575]">
        素材 · 镜头 · 候选批次 · {duration}s 成片
      </p>
      <button
        type="button"
        onClick={onBack}
        className="mt-3 h-7 rounded-[6px] px-2.5 text-xs text-[#9a9a9a] hover:bg-white/[0.06] hover:text-white"
      >
        返回 Prompt
      </button>
    </div>
  );
}
