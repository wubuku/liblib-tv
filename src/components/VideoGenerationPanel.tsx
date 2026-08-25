"use client";

import Image from "next/image";
import { useMemo, useState } from "react";
import {
  ArrowRight,
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
  Search,
  Settings2,
  ShieldCheck,
  Sparkles,
  Volume2,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";

type MenuName = "model" | "mode" | "params" | "advanced" | null;
type VideoMode = "omnireference" | "image-reference" | "long-video";

interface VideoGenerationPanelProps {
  zoom: number;
  initialModel?: string;
  initialPrompt?: string;
}

const defaultPrompt = "起始状态：@陈默（图片 1）充满杀伤力的眼神锁定镜头。动作过程：镜头平滑而缓慢地向他冷厉的双眼推移。他在第1秒开始说出如刀刃般的台词。对白（@陈默，冷酷且有力）：‘当初你离开的时候，怎么没想过我会担心？’结束状态：镜头停止在他充满恨意的双眸。音效：环境音完全静默，只余沉重的台词回响。";

const references = [
  { id: 1, name: "陈默", image: "/images/scene-coffee-1.png" },
  { id: 2, name: "咖啡", image: "/images/scene-coffee-2.png" },
  { id: 3, name: "分镜", image: "/images/storyboard-2.png" },
];

const modelItems = [
  {
    id: "2.5",
    title: "Seedance 2.5",
    estimate: "2min",
    premium: true,
    family: "seedance",
    description: "最强视频模型，全能参考，30s音画同步",
  },
  {
    id: "2.0 VIP",
    title: "Seedance 2.0 VIP",
    estimate: "2min",
    premium: true,
    family: "seedance",
  },
  {
    id: "Minimax H3",
    title: "Minimax H3",
    estimate: "2min",
    premium: true,
    family: "minimax",
  },
  {
    id: "2.0 Fast VIP",
    title: "Seedance 2.0 Fast VIP",
    estimate: "2min",
    premium: true,
    family: "seedance",
    description: "最强视频模型快速版，会员专属通道，15s音画同步",
  },
  {
    id: "2.0 Mini",
    title: "Seedance 2.0 Mini",
    estimate: "2min",
    premium: true,
    family: "seedance",
  },
  {
    id: "Wan 3.0 Prime",
    title: "Wan 3.0 Prime",
    estimate: "1min",
    premium: false,
    family: "wan",
  },
  {
    id: "Wan 3.0",
    title: "Wan 3.0",
    estimate: "3min",
    premium: false,
    family: "wan",
  },
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

export function VideoGenerationPanel({ zoom, initialModel, initialPrompt }: VideoGenerationPanelProps) {
  const [menu, setMenu] = useState<MenuName>(null);
  const [model, setModel] = useState(initialModel?.includes("2.0") ? "2.0 VIP" : "2.5");
  const [mode, setMode] = useState<VideoMode>("omnireference");
  const [ratio, setRatio] = useState("16:9");
  const [resolution, setResolution] = useState("720P");
  const [duration, setDuration] = useState(6);
  const [audio, setAudio] = useState(true);
  const [count, setCount] = useState(1);
  const [autoLink, setAutoLink] = useState(true);
  const [networkSearch, setNetworkSearch] = useState(true);
  const [materialCheck, setMaterialCheck] = useState(true);
  const [prompt, setPrompt] = useState(initialPrompt ?? defaultPrompt);
  const [showProcess, setShowProcess] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const isLongVideo = mode === "long-video";
  const durationMin = isLongVideo ? 30 : 4;
  const durationMax = isLongVideo ? 300 : 30;
  const credits = isLongVideo ? duration * 49 : duration * 46 * count;
  const modeLabel = modeItems.find((item) => item.id === mode)?.label ?? "全能参考";
  const settingsLabel = `${ratio} · ${resolution} · ${duration}s · ${count}个 ·`;
  const referenceSummary = useMemo(() => references.map((item) => `${item.name}（图片 ${item.id}）`).join("、"), []);

  const selectMode = (nextMode: VideoMode) => {
    setMode(nextMode);
    setDuration(nextMode === "long-video" ? 30 : Math.min(30, Math.max(4, duration)));
    setShowProcess(false);
    setMenu(null);
  };

  return (
    <div
      data-video-generation-panel
      className="nodrag nowheel nopan absolute -bottom-[17px] left-1/2 z-20 w-[660px] -translate-x-1/2 translate-y-full origin-top"
      // The bordered node is the containing block, so 17 flow units produce the source's 16-unit outer gap.
      style={{ transform: `scale(${1 / zoom})` }}
    >
      <section className="relative flex h-[274px] flex-col rounded-2xl border border-[#363636] bg-[#262626] p-2 shadow-[0_22px_60px_rgba(0,0,0,0.52)]">
        <div className="flex h-8 shrink-0 items-center gap-1">
          {[{ label: "参考", icon: Images }, { label: "标记", icon: AtSign }, { label: "特效", icon: Sparkles }, { label: "角色库", icon: Box }, { label: "运镜", icon: Film }].map((item) => {
            const Icon = item.icon;
            return <button key={item.label} type="button" className="flex h-7 items-center gap-1.5 rounded-full bg-white/[0.05] px-2.5 text-xs text-[#aaa] hover:bg-white/[0.09] hover:text-white"><Icon size={12} />{item.label}</button>;
          })}
          {autoLink && <button type="button" onClick={() => setMenu(menu === "advanced" ? null : "advanced")} className="ml-auto flex h-7 items-center gap-1.5 rounded-full bg-[#09caf5]/10 px-2.5 text-xs text-[#09caf5]"><Link2 size={12} />3 个匹配</button>}
        </div>

        {showProcess ? (
          <LongVideoProcess onBack={() => setShowProcess(false)} />
        ) : (
          <>
            <div className="mt-1 flex h-12 shrink-0 items-center gap-2">
              {references.map((reference) => (
                <div key={reference.id} className="relative size-12 overflow-hidden rounded-lg border border-white/10">
                  <Image src={reference.image} alt={`${reference.name}参考`} fill sizes="48px" className="object-cover" unoptimized />
                  <span className="absolute left-0.5 top-0.5 flex size-4 items-center justify-center rounded-full bg-black/70 text-[9px] text-white">{reference.id}</span>
                </div>
              ))}
              <p className="ml-1 truncate text-xs text-[#757575]">Auto Link：{referenceSummary}</p>
            </div>
            <textarea
              value={prompt}
              onChange={(event) => { setPrompt(event.target.value); setSubmitted(false); }}
              aria-label="视频生成提示词"
              className="mt-1 min-h-0 flex-1 resize-none rounded-xl bg-black/10 p-2 text-sm leading-6 text-[#ededed] outline-none selection:bg-[#09caf5]/30"
            />
          </>
        )}

        <footer className="mt-1 flex h-9 shrink-0 items-center gap-1 border-t border-white/[0.07] pt-1 text-xs text-[#dfdfdf]">
          <div className="relative">
            <button data-video-model-trigger type="button" onClick={() => setMenu(menu === "model" ? null : "model")} className="flex h-8 items-center gap-1.5 rounded-lg px-2 hover:bg-white/[0.06]">
              <span className="font-semibold">{model === "2.5" ? "2.5" : model}</span><ChevronDown size={12} className="text-[#777]" />
            </button>
            {menu === "model" && <ModelMenu model={model} onSelect={(value) => { setModel(value); setMenu(null); }} />}
          </div>
          <div className="relative">
            <button data-video-mode-trigger type="button" onClick={() => setMenu(menu === "mode" ? null : "mode")} className="flex h-8 items-center gap-1 rounded-lg px-2 hover:bg-white/[0.06]">{modeLabel}<ChevronDown size={12} className="text-[#777]" /></button>
            {menu === "mode" && <ModeMenu mode={mode} onSelect={selectMode} />}
          </div>
          <div className="relative min-w-0">
            <button data-video-params-trigger type="button" onClick={() => setMenu(menu === "params" ? null : "params")} className="flex h-8 max-w-[205px] items-center gap-1 rounded-lg px-2 hover:bg-white/[0.06]"><span className="truncate">{settingsLabel}</span><ChevronDown size={12} className="shrink-0 text-[#777]" /></button>
            {menu === "params" && (
              <ParamsMenu ratio={ratio} resolution={resolution} duration={duration} durationMin={durationMin} durationMax={durationMax} audio={audio} count={count} isLongVideo={isLongVideo} onRatio={setRatio} onResolution={setResolution} onDuration={setDuration} onAudio={setAudio} onCount={setCount} />
            )}
          </div>
          <button data-video-advanced-trigger type="button" onClick={() => setMenu(menu === "advanced" ? null : "advanced")} aria-label="高级设置" className="flex size-8 shrink-0 items-center justify-center rounded-lg text-[#aaa] hover:bg-white/[0.06]"><Settings2 size={14} /></button>
          {menu === "advanced" && (
            <AdvancedMenu networkSearch={networkSearch} materialCheck={materialCheck} autoLink={autoLink} onNetworkSearch={setNetworkSearch} onMaterialCheck={setMaterialCheck} onAutoLink={setAutoLink} />
          )}
          {isLongVideo && <button type="button" onClick={() => setShowProcess((show) => !show)} className="h-8 shrink-0 rounded-lg px-2 text-[#09caf5] hover:bg-[#09caf5]/10">{showProcess ? "返回编辑" : "查看过程"}</button>}
          <span data-video-credits className="ml-auto flex shrink-0 items-center gap-1 text-[#d6a233]"><Zap size={12} fill="currentColor" />{credits}</span>
          <button type="button" aria-label="翻译视频提示词" className="flex size-8 shrink-0 items-center justify-center rounded-lg text-[#aaa] hover:bg-white/[0.06]"><Languages size={14} /></button>
          <button type="button" onClick={() => setSubmitted(true)} aria-label="生成视频" className={cn("flex size-8 shrink-0 items-center justify-center rounded-xl bg-white text-[#202020]", submitted && "bg-[#09caf5]")} title={submitted ? "已加入本地任务" : "生成视频"}>{submitted ? <Check size={15} /> : <ArrowUp size={15} />}</button>
        </footer>
      </section>
    </div>
  );
}

function ModelMenu({ model, onSelect }: { model: string; onSelect: (model: string) => void }) {
  return (
    <div
      data-video-model-menu
      className="absolute bottom-8 -left-[9px] z-50 flex h-[410px] w-[380px] flex-col gap-1 rounded-xl border border-white/10 bg-[#292929] p-2 shadow-2xl"
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

function AdvancedMenu({ networkSearch, materialCheck, autoLink, onNetworkSearch, onMaterialCheck, onAutoLink }: { networkSearch: boolean; materialCheck: boolean; autoLink: boolean; onNetworkSearch: (value: boolean) => void; onMaterialCheck: (value: boolean) => void; onAutoLink: (value: boolean) => void }) {
  return <div className="absolute bottom-12 right-10 z-50 w-56 rounded-xl border border-white/10 bg-[#292929] p-2 shadow-2xl"><p className="px-2 pb-1 text-[11px] text-[#777]">高级设置</p><SwitchRow label="联网搜索" icon={<Search size={13} />} checked={networkSearch} onChange={onNetworkSearch} /><SwitchRow label="自动校验素材" icon={<ShieldCheck size={13} />} checked={materialCheck} onChange={onMaterialCheck} /><SwitchRow label="智能引用 AutoLink" icon={<Link2 size={13} />} checked={autoLink} onChange={onAutoLink} /></div>;
}

function SwitchRow({ label, icon, checked, onChange }: { label: string; icon: React.ReactNode; checked: boolean; onChange: (value: boolean) => void }) {
  return <label className="flex h-9 cursor-pointer items-center gap-2 rounded-lg px-2 text-xs text-[#ccc] hover:bg-white/[0.05]">{icon}<span className="flex-1">{label}</span><input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} className="sr-only" /><span className={cn("relative h-5 w-9 rounded-full", checked ? "bg-[#09caf5]" : "bg-[#4a4a4a]")}><span className={cn("absolute top-0.5 size-4 rounded-full bg-white transition-transform", checked ? "translate-x-[18px]" : "translate-x-0.5")} /></span></label>;
}

function LongVideoProcess({ onBack }: { onBack: () => void }) {
  const stages = [
    { label: "输入素材", detail: "3 个引用", icon: Images },
    { label: "镜头计划", detail: "10 段 · 300s", icon: Film },
    { label: "生成批次", detail: "3/10 待确认", icon: Sparkles },
    { label: "最终成片", detail: "等待拼接", icon: Volume2 },
  ];
  return <div className="mt-1 flex min-h-0 flex-1 flex-col rounded-xl bg-[#1d1d1d] p-3"><div className="mb-3 flex items-center"><span className="text-xs font-medium text-white">超长视频生成过程</span><span className="ml-2 rounded bg-[#0d5964] px-1.5 py-0.5 text-[9px] text-[#4de1f4]">Beta · 本地预览</span><button type="button" onClick={onBack} className="ml-auto text-xs text-[#888] hover:text-white">返回 Prompt</button></div><div className="flex flex-1 items-center justify-center">{stages.map((stage, index) => {const Icon=stage.icon;return <div key={stage.label} className="flex items-center"><div className="flex h-20 w-[125px] flex-col items-center justify-center rounded-xl border border-white/[0.08] bg-[#252525]"><Icon size={18} className="mb-2 text-[#09caf5]" /><span className="text-xs text-white">{stage.label}</span><span className="mt-1 text-[10px] text-[#777]">{stage.detail}</span></div>{index<stages.length-1&&<ArrowRight size={16} className="mx-2 text-[#555]" />}</div>})}</div></div>;
}
