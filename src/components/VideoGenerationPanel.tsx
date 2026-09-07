"use client";

import Image from "next/image";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowUp,
  AtSign,
  Box,
  Check,
  ChevronDown,
  Film,
  Gem,
  Images,
  Languages,
  Link2,
  LoaderCircle,
  Search,
  ShieldCheck,
  Sparkles,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type {
  LongVideoProcessInput,
  VideoContinuationMetadata,
} from "@/store/canvasStore";

type MenuName = "model" | "mode" | "params" | "advanced" | null;
type VideoMode = "omnireference" | "image-reference" | "long-video";

interface VideoGenerationPanelProps {
  zoom: number;
  attempt: string | null;
  initialPrompt?: string;
  continuation?: VideoContinuationMetadata;
  onCreateLongVideoProcess?: (input: LongVideoProcessInput) => string | null;
  onClearContinuation?: () => void;
}

const defaultPrompt = "起始状态：@陈默（图片 1）充满杀伤力的眼神锁定镜头。动作过程：镜头平滑而缓慢地向他冷厉的双眼推移。他在第1秒开始说出如刀刃般的台词。对白（@陈默，冷酷且有力）：‘当初你离开的时候，怎么没想过我会担心？’结束状态：镜头停止在他充满恨意的双眸。音效：环境音完全静默，只余沉重的台词回响。";

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

const modeItems = [
  { id: "text", label: "文生视频", disabled: true },
  { id: "omnireference", label: "全能参考", disabled: false },
  { id: "image", label: "图生视频", disabled: true },
  { id: "first-last", label: "首尾帧", disabled: true },
  { id: "image-reference", label: "图片参考", disabled: false },
  { id: "video-edit", label: "视频编辑", disabled: true },
  { id: "long-video", label: "超长视频", disabled: false, badge: "Beta" },
] as const;

export function VideoGenerationPanel({
  zoom,
  attempt,
  initialPrompt,
  continuation,
  onCreateLongVideoProcess,
  onClearContinuation,
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
  const [yunjingSelection, setYunjingSelection] = useState<string | null>(null);
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
  // Batch 155: 5分钟超长视频芯片将时长范围切到 30..300（否则 300s 在 4..30 滑杆上半态）。
  const isLongRange = isLongVideo || attempt === "5分钟超长视频";
  const durationMin = isLongRange ? 30 : 4;
  const durationMax = isLongRange ? 300 : 30;
  // Batch 131: 源站 2026-09-06 数据点——16:9·5s·1个=135、Auto·5s·1个=230，
  // 比例影响积分；未采样比例沿用 46/s（CLONE_DECISION）。
  const credits = isLongVideo
    ? duration * 49
    : duration * count * (ratio === "16:9" ? 27 : 46);
  // Batch 145: 源站默认模式显示 文生视频（ omnireference 内部 id 映射到源站 文生视频 显示）。
  // Batch 149: 续写面板锁定的是全能参考（提示文案「仅支持 Seedance 2.5 的全能参考模式」），触发器保留 全能参考。
  const modeLabel = isContinuation
    ? "全能参考"
    : mode === "omnireference"
      ? "文生视频"
      : modeItems.find((item) => item.id === mode)?.label ?? "全能参考";
  const settingsLabel = `${ratio} · ${resolution} · ${duration}s · ${count}个 ·`;
  const referenceSummary = useMemo(() => references.map((item) => `${item.name}（图片 ${item.id}）`).join("、"), []);

  // Batch 159: 尝试芯片移入节点卡内，状态由 VideoNode 持有；联动用「渲染期调整」
  // （React 官方 prop 变更派生状态模式，避免 effect 内同步 setState）。
  const [prevAttempt, setPrevAttempt] = useState(attempt);
  if (attempt !== prevAttempt) {
    setPrevAttempt(attempt);
    // Batch 128+160: 源站尝试芯片驱动设置联动——5分钟超长视频整组切换：
    // mode=超长视频（长视频公式 49/s，页脚实拍 14700）+ Auto+300s；首尾帧/首帧 → Auto+5s。
    if (attempt === "5分钟超长视频") {
      setMode("long-video");
      setRatio("Auto");
      setDuration(300);
    } else if (attempt !== null) {
      setRatio("Auto");
      setDuration(5);
    } else if (prevAttempt === "5分钟超长视频") {
      // Batch 155/160: 取消 5 分钟芯片回到常规模式并钳制时长（CLONE_DECISION，源站未采样取消）。
      setMode("omnireference");
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
    setMode(nextMode);
    setDuration(nextMode === "long-video" ? 30 : Math.min(30, Math.max(4, duration)));
    setShowProcess(false);
    setSubmitted(false);
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
          {[{ label: "参考", icon: Images }, { label: "标记", icon: AtSign }, { label: "特效", icon: Sparkles }, { label: "角色库", icon: Box }, { label: "运镜", icon: Film, hasMenu: true }].map((item) => {
            const Icon = item.icon;
            if ("hasMenu" in item && item.hasMenu) {
              return (
                <div key={item.label} className="relative">
                  <button
                    type="button"
                    data-yunjing-trigger
                    onClick={() => setYunjingOpen(!yunjingOpen)}
                    className="flex h-[26px] items-center gap-1.5 rounded-full bg-white/[0.05] px-2 py-1 text-xs text-[#aaa] hover:bg-white/[0.09] hover:text-white"
                  >
                    <Icon size={12} />
                    {item.label}
                  </button>
                  {yunjingOpen && (
                    <div data-yunjing-menu className="absolute bottom-10 left-0 z-50 w-[280px] rounded-xl border border-white/10 bg-[#292929] p-1.5 shadow-2xl">
                      <p className="px-2 py-1 text-[11px] text-[#777]">运镜方式</p>
                      {[
                        { id: "push-in", label: "推镜", desc: "镜头向主体推进" },
                        { id: "pull-out", label: "拉镜", desc: "镜头远离主体拉出" },
                        { id: "pan-left", label: "左摇", desc: "镜头水平向左旋转" },
                        { id: "pan-right", label: "右摇", desc: "镜头水平向右旋转" },
                        { id: "tilt-up", label: "上仰", desc: "镜头垂直向上仰视" },
                        { id: "tilt-down", label: "下俯", desc: "镜头垂直向下俯视" },
                        { id: "tracking", label: "跟拍", desc: "镜头跟随主体移动" },
                        { id: "crane", label: "升降", desc: "镜头垂直升降运动" },
                        { id: "orbit", label: "环绕", desc: "镜头围绕主体环绕" },
                        { id: "zoom-in", label: "推进", desc: "焦距推近放大主体" },
                        { id: "zoom-out", label: "拉远", desc: "焦距拉远缩小主体" },
                        { id: "static", label: "固定", desc: "镜头固定不动" },
                      ].map((m) => (
                        <button
                          key={m.id}
                          type="button"
                          data-yunjing-option={m.id}
                          aria-pressed={yunjingSelection === m.id}
                          onClick={() => {
                            setYunjingSelection(yunjingSelection === m.id ? null : m.id);
                            setYunjingOpen(false);
                          }}
                          className={cn(
                            "flex w-full items-center justify-between rounded-lg px-2 py-1.5 text-left text-xs transition-colors",
                            yunjingSelection === m.id ? "bg-[#09caf5]/15 text-[#09caf5]" : "text-[#ccc] hover:bg-white/[0.06]",
                          )}
                        >
                          <span className="font-medium">{m.label}</span>
                          {yunjingSelection === m.id && <span className="text-[10px]">✓</span>}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              );
            }
            return <button key={item.label} type="button" className="flex h-[26px] items-center gap-1.5 rounded-full bg-white/[0.05] px-2 py-1 text-xs text-[#aaa] hover:bg-white/[0.09] hover:text-white"><Icon size={12} />{item.label}</button>;
          })}
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
          {!isContinuation && autoLink && <button type="button" onClick={() => setMenu(menu === "advanced" ? null : "advanced")} className="ml-auto flex h-7 items-center gap-1.5 rounded-full bg-[#09caf5]/10 px-2.5 text-xs text-[#09caf5]"><Link2 size={12} />3 个匹配</button>}
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
            ) : (
              <>
                {/* Batch 160: 源站新建节点无引用时不渲染槽行（工具行直连提示词）。 */}
                {references.length > 0 && (
                <div className="mt-1 flex h-12 shrink-0 items-center gap-2">
                  {references.map((reference) => (
                    // Batch 149: 源站引用槽 48×55 cursor-grab（2026-09-07 实拍）。
                    <div key={reference.id} className="relative h-[55px] w-12 cursor-grab overflow-hidden rounded-lg border border-white/10 active:cursor-grabbing">
                      <Image src={reference.image} alt={`${reference.name}参考`} fill sizes="48px" className="object-cover" unoptimized />
                      <span className="absolute left-0.5 top-0.5 flex size-4 items-center justify-center rounded-full bg-black/70 text-[9px] text-white">{reference.id}</span>
                    </div>
                  ))}
                  <p className="ml-1 truncate text-xs text-[#757575]">Auto Link：{referenceSummary}</p>
                </div>
                )}
                <textarea
                  value={prompt}
                  onChange={(event) => { setPrompt(event.target.value); setSubmitted(false); }}
                  aria-label="视频生成提示词"
                  placeholder="描述你想要生成的画面内容，@引用素材"
                  className="mt-1 min-h-0 flex-1 resize-none rounded-xl bg-black/10 p-2 text-sm leading-6 text-[#ededed] outline-none selection:bg-[#09caf5]/30"
                />
              </>
            )}
          </>
        )}

        <footer className="mt-1 flex h-9 shrink-0 items-center gap-1 border-t border-white/[0.07] pt-1 text-xs text-[#dfdfdf]">
          <div className="relative">
            <button data-video-model-trigger data-video-continuation-locked={isContinuation || undefined} type="button" disabled={isContinuation} onClick={() => setMenu(menu === "model" ? null : "model")} className="flex h-8 items-center gap-1.5 rounded-lg px-2 hover:bg-white/[0.06] disabled:cursor-default disabled:hover:bg-transparent">
              {/* Batch 149: 源站触发器显示缩写名（Seedance 2.0 VIP → 2.0，2026-09-07 实拍）。 */}
              <span className="font-semibold">{model.replace(/ VIP$/, "")}</span><ChevronDown size={12} className="text-[#777]" />
            </button>
            {menu === "model" && <ModelMenu model={model} onSelect={(value) => { setModel(value); setMenu(null); }} />}
          </div>
          <div className="relative">
            <button data-video-mode-trigger data-video-continuation-locked={isContinuation || undefined} type="button" disabled={isContinuation} onClick={() => setMenu(menu === "mode" ? null : "mode")} className="flex h-8 items-center gap-1 rounded-lg px-2 hover:bg-white/[0.06] disabled:cursor-default disabled:hover:bg-transparent">{modeLabel}<ChevronDown size={12} className="text-[#777]" /></button>
            {menu === "mode" && <ModeMenu mode={mode} onSelect={selectMode} />}
          </div>
          <div className="relative min-w-0">
            <button data-video-params-trigger type="button" onClick={() => setMenu(menu === "params" ? null : "params")} className="flex h-8 max-w-[205px] items-center gap-1 rounded-lg px-2 hover:bg-white/[0.06]"><span className="truncate">{settingsLabel}</span><ChevronDown size={12} className="shrink-0 text-[#777]" /></button>
            {menu === "params" && (
              <ParamsMenu ratio={ratio} resolution={resolution} duration={duration} durationMin={durationMin} durationMax={durationMax} audio={audio} count={count} isLongVideo={isLongRange} onRatio={setRatio} onResolution={setResolution} onDuration={setDuration} onAudio={setAudio} onCount={setCount} />
            )}
          </div>

          {isLongVideo && <button type="button" onClick={() => setShowProcess((show) => !show)} className="h-8 shrink-0 rounded-lg px-2 text-[#09caf5] hover:bg-[#09caf5]/10">{showProcess ? "返回编辑" : "查看过程"}</button>}
          {/* Batch 151: 源站积分块 min-w-[85px] justify-end、fg-muted 灰调、数值 12px/15px（2026-09-07 实拍）。 */}
          <span data-video-credits className="ml-auto flex h-8 min-w-[85px] shrink-0 items-center justify-end gap-1.5 text-[#9a9a9a]"><Zap size={12} fill="currentColor" /><span className="text-[12px] leading-[15px]">{credits}</span></span>
          <button type="button" aria-label="翻译视频提示词" className="flex size-8 shrink-0 items-center justify-center rounded-lg text-[#aaa] hover:bg-white/[0.06]"><Languages size={14} /></button>
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
            {longVideoSubmitting ? (
              <LoaderCircle
                data-video-long-submit-spinner
                size={15}
                className="animate-spin"
              />
            ) : submitted ? (
              <Check size={15} />
            ) : (
              <ArrowUp size={15} />
            )}
          </button>
        </footer>

        {/* Batch 126: 源站高级设置内联可见（联网搜索/自动校验素材/智能引用 AutoLink）。
            Batch 149: 源站 2026-09-07 实拍为「高级设置」标题 + 纵向开关列（行高 36，开关右对齐）；
            查看过程态隐藏（过程视图独占面板，避免挤压，batch33 契约）。 */}
        {!showProcess && (
          <div data-video-advanced-inline className="shrink-0 px-2">
            <p data-video-advanced-label className="mx-2 pt-3 text-xs font-bold text-neutral-500">高级设置</p>
            <div className="flex flex-col gap-1 pb-2 pt-1">
              <SwitchRow label="联网搜索" icon={<Search size={13} />} checked={networkSearch} onChange={setNetworkSearch} />
              <SwitchRow label="自动校验素材" icon={<ShieldCheck size={13} />} checked={materialCheck} onChange={setMaterialCheck} />
              <SwitchRow label="智能引用 AutoLink" icon={<Link2 size={13} />} checked={autoLink} onChange={setAutoLink} />
            </div>
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
            onClick={() => onSelect(item.id)}
            className={cn(
              "flex w-full shrink-0 items-center gap-2 rounded-xl border border-transparent px-2 text-left hover:bg-white/[0.055]",
              selected && "min-h-[58px] border-[#4a4a4a] bg-white/[0.1]",
              !selected && "min-h-[48px]",
            )}
          >
            <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-white/[0.06] text-[#d9d9d9]">
              <ModelIcon size={15} />
            </span>
            <span className="min-w-0 flex-1">
              <span className="flex items-center gap-1.5">
                <span className="truncate text-sm text-[#efefef]">{item.title}</span>
                {item.premium && (
                  <Gem data-video-model-premium size={11} fill="currentColor" className="shrink-0 text-[#f3b74c]" />
                )}
              </span>
              {selected && item.description && (
                <span data-video-model-description className="mt-0.5 block truncate text-[11px] text-[#818181]">
                  {item.description}
                </span>
              )}
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
    <div className="absolute bottom-10 left-0 z-50 w-52 rounded-xl border border-white/10 bg-[#292929] p-1.5 shadow-2xl">
      <p className="px-2 py-1 text-[11px] text-[#777]">视频生成模式</p>
      {modeItems.map((item) => <button key={item.id} data-video-mode-option={item.id} type="button" disabled={item.disabled} onClick={() => onSelect(item.id as VideoMode)} className={cn("flex h-9 w-full items-center rounded-lg px-2 text-left text-sm", item.disabled ? "cursor-not-allowed text-[#555]" : "text-[#ddd] hover:bg-white/[0.06]", mode === item.id && "bg-white/[0.08] text-white")}><Film size={14} className="mr-2" />{item.label}{"badge" in item && item.badge && <span className="ml-auto rounded bg-[#0d5964] px-1.5 py-0.5 text-[9px] text-[#4de1f4]">{item.badge}</span>}</button>)}
    </div>
  );
}

interface ParamsMenuProps {
  ratio: string; resolution: string; duration: number; durationMin: number; durationMax: number; audio: boolean; count: number; isLongVideo: boolean;
  onRatio: (value: string) => void; onResolution: (value: string) => void; onDuration: (value: number) => void; onAudio: (value: boolean) => void; onCount: (value: number) => void;
}

function ParamsMenu({ ratio, resolution, duration, durationMin, durationMax, audio, count, isLongVideo, onRatio, onResolution, onDuration, onAudio, onCount }: ParamsMenuProps) {
  const ratios = ["Auto", "16:9", "4:3", "1:1", "3:4", "9:16", "21:9"];
  const resolutions = ["480P", "720P", "1080P"];

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
        <div className="grid grid-cols-5 gap-1.5">
          {ratios.map((item) => (
            <button
              key={item}
              data-video-ratio-option={item}
              type="button"
              aria-pressed={ratio === item}
              onClick={() => onRatio(item)}
              className={cn(
                "flex h-[52px] min-w-0 flex-col items-center justify-center gap-1 rounded-lg border text-[11px]",
                ratio === item
                  ? "border-[#7d7d7d] bg-white/[0.1] text-white"
                  : "border-white/[0.07] bg-white/[0.025] text-[#777] hover:border-white/[0.16] hover:text-[#ddd]",
              )}
            >
              <AspectRatioGlyph ratio={item} active={ratio === item} />
              <span>{item}</span>
            </button>
          ))}
        </div>
      </section>

      <section className="mt-3">
        <p className="mb-2 text-xs text-[#8a8a8a]">清晰度</p>
        <div className="grid grid-cols-3 gap-1 rounded-lg bg-black/20 p-0.5">
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
            围绕视频画面设计，支持更长时长的连续场景
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

function AspectRatioGlyph({ ratio, active }: { ratio: string; active: boolean }) {
  const dimensions: Record<string, string> = {
    Auto: "h-3.5 w-4",
    "16:9": "h-3 w-5",
    "4:3": "h-3.5 w-[18px]",
    "1:1": "size-3.5",
    "3:4": "h-[18px] w-3.5",
    "9:16": "h-5 w-3",
    "21:9": "h-2.5 w-5",
  };

  return (
    <span
      aria-hidden="true"
      className={cn(
        "block rounded-[2px] border",
        dimensions[ratio],
        active ? "border-[#d4d4d4]" : "border-[#6b6b6b]",
      )}
    />
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
