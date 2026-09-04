"use client";

import Image from "next/image";
import {
  Bookmark,
  Box,
  Check,
  ChevronRight,
  History,
  MessageSquarePlus,
  PanelRightClose,
  Plus,
  RefreshCw,
  Send,
  Settings,
  Share2,
  SlidersHorizontal,
  Sparkles,
  X,
} from "lucide-react";
import { useRef, useState } from "react";
import { useUIStore } from "@/store/uiStore";
import { cn } from "@/lib/utils";

interface Skill {
  id: string;
  title: string;
  path: string;
  image: string;
}

// Batch 97: 第一批为 2026-09-05 源站登录态复核的源站命名与 handle；
// 第二批仍是 clone-shaped 换一批填充，不代表源站目录。
const skillBatches: Skill[][] = [
  [
    { id: "pixar", title: "皮克斯动画广告", path: "/pixar-animated-ad-creator", image: "/images/scene-coffee-1.png" },
    { id: "viral", title: "爆款拉片复刻", path: "/viral-video-replicator", image: "/images/scene-coffee-2.png" },
    { id: "neo-china", title: "新中式美学TVC", path: "/neo-chinese-aesthetic-tvc", image: "/images/scene-coffee-3.png" },
    { id: "wuxia", title: "古典武侠电影全流程导演", path: "/hujinquanwuxia", image: "/images/scene-coffee-4.png" },
  ],
  [
    { id: "character", title: "角色一致性检查", path: "/character-consistency", image: "/images/liblib-panels/character-thumb-03.webp" },
    { id: "storyboard", title: "分镜节奏优化", path: "/storyboard-rhythm", image: "/images/storyboard-2.png" },
    { id: "lighting", title: "电影感打光", path: "/cinematic-lighting", image: "/images/liblib-panels/toolbox-08.webp" },
    { id: "continuity", title: "镜头连续性检查", path: "/shot-continuity", image: "/images/liblib-panels/toolbox-14.webp" },
  ],
];

type AgentModelKind = "image" | "video";

interface AgentModelOption {
  id: string;
  name: string;
  description: string;
  premium: boolean;
  kind: AgentModelKind;
}

// Batch 97: 2026-09-05 源站「选择模型」菜单完整目录（图片 7 + 视频 8），
// premium 角标分布与说明文案均为源站观察；id 为 clone 稳定 slug。
const agentModelCatalog: AgentModelOption[] = [
  { id: "lib-image", name: "Lib Image", description: "最新图片模型，长文本能力突出", premium: false, kind: "image" },
  { id: "general-image-pro", name: "General image Pro", description: "最强图片编辑模型，一致性好", premium: false, kind: "image" },
  { id: "general-image-v2", name: "General image V2", description: "支持联网搜索、文字准确、速度更快", premium: false, kind: "image" },
  { id: "seedream-5-0-pro", name: "Seedream 5.0 Pro", description: "精准交互式编辑，支持原生多语言排版", premium: false, kind: "image" },
  { id: "style-image-v8-2", name: "Style Image V8.2", description: "电影感全面升级，精准还原光影、人物与真实材质", premium: false, kind: "image" },
  { id: "style-image-v8-1", name: "Style Image V8.1", description: "生图更连贯、细节更丰富、美学水准大幅提升", premium: false, kind: "image" },
  { id: "style-image-v7", name: "Style Image V7", description: "最佳美学、电影质感、创意能力强", premium: false, kind: "image" },
  { id: "seedance-2-5", name: "Seedance 2.5", description: "最强视频模型，全能参考，30s音画同步", premium: true, kind: "video" },
  { id: "seedance-2-0-vip", name: "Seedance 2.0 VIP", description: "最强视频模型，会员专属通道，15s音画同步", premium: true, kind: "video" },
  { id: "minimax-h3", name: "Minimax H3", description: "全模态输入，多参数控制，多场景商用级生成", premium: true, kind: "video" },
  { id: "seedance-2-0-fast-vip", name: "Seedance 2.0 Fast VIP", description: "最强视频模型极速快速版，会员专属通道，15s音画同步", premium: true, kind: "video" },
  { id: "wan-3-0-prime", name: "Wan 3.0 Prime", description: "超快生成，全模态参考，超写实高一致性", premium: false, kind: "video" },
  { id: "wan-3-0", name: "Wan 3.0", description: "全模态参考，支持文档与网页输入，超写实高一致性生成", premium: false, kind: "video" },
  { id: "kling-o3", name: "Kling O3", description: "视频编辑模型、参考一致性、首尾同出、多镜头", premium: true, kind: "video" },
  { id: "kling-3-0", name: "Kling 3.0", description: "视频生成模型，高质感、支持多镜头", premium: true, kind: "video" },
];

const agentModeOptions = [
  { id: "manual", title: "手动模式", description: "Agent 在每次生成前询问" },
  { id: "auto", title: "自动模式", description: "Agent 完全自动生成" },
] as const;

type AgentModeId = (typeof agentModeOptions)[number]["id"];

function SkillCard({
  skill,
  selected,
  onSelect,
}: {
  skill: Skill;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      data-agent-skill={skill.id}
      aria-pressed={selected}
      onClick={onSelect}
      className={cn(
        "flex min-w-0 items-center gap-2 rounded-xl border px-2.5 py-2 text-left transition-colors",
        selected
          ? "border-[#09caf5]/60 bg-[#09caf5]/10"
          : "border-white/[0.07] bg-[#222] hover:border-white/[0.14] hover:bg-[#292929]",
      )}
    >
      <Image
        src={skill.image}
        alt=""
        width={40}
        height={40}
        className="size-9 shrink-0 rounded-lg object-cover"
        unoptimized
      />
      <span className="min-w-0 flex-1">
        <span className="block truncate text-xs text-[#e9e9e9]">{skill.title}</span>
        <span className="mt-1 block truncate text-[10px] text-[#777]">{skill.path}</span>
      </span>
      <ChevronRight size={13} className="shrink-0 text-[#666]" />
    </button>
  );
}

function AgentModelRow({
  model,
  selected,
  onToggle,
}: {
  model: AgentModelOption;
  selected: boolean;
  onToggle: () => void;
}) {
  return (
    <li className="flex items-center gap-2.5 rounded-lg px-2 py-2 hover:bg-white/[0.05]">
      <span className="min-w-0 flex-1">
        <span className="flex items-center gap-1.5">
          <span className="truncate text-xs font-medium text-[#e9e9e9]">{model.name}</span>
          {model.premium && (
            <span aria-label="premium" title="premium" className="shrink-0 text-[10px] leading-none">
              💎
            </span>
          )}
        </span>
        <span className="mt-0.5 block truncate text-[10px] text-[#8b8b8b]">{model.description}</span>
      </span>
      <button
        type="button"
        data-agent-model={model.id}
        aria-pressed={selected}
        aria-label={selected ? `已选 ${model.name}` : `添加 ${model.name}`}
        title={selected ? `已选 ${model.name}` : `添加 ${model.name}`}
        onClick={onToggle}
        className={cn(
          "flex size-6 shrink-0 items-center justify-center rounded-full border transition-colors",
          selected
            ? "border-[#09caf5]/70 bg-[#09caf5]/15 text-[#09caf5]"
            : "border-white/15 text-[#9a9a9a] hover:border-white/30 hover:text-white",
        )}
      >
        {selected ? <Check size={12} /> : <Plus size={12} />}
      </button>
    </li>
  );
}

export function AgentDrawer() {
  const toggleAgent = useUIStore((state) => state.toggleAgent);
  const editorMode = useUIStore((state) => state.editorMode);
  const [skillBatch, setSkillBatch] = useState(0);
  const [selectedSkillId, setSelectedSkillId] = useState<string | null>(null);
  const [prompt, setPrompt] = useState("");
  const [showNotification, setShowNotification] = useState(true);
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);
  const [status, setStatus] = useState("");
  const [openMenu, setOpenMenu] = useState<"model" | "mode" | null>(null);
  const [activeModelTab, setActiveModelTab] = useState<AgentModelKind>("image");
  const [selectedModelIds, setSelectedModelIds] = useState<string[]>([]);
  const [agentMode, setAgentMode] = useState<AgentModeId>("auto");
  const imageSectionRef = useRef<HTMLDivElement | null>(null);
  const videoSectionRef = useRef<HTMLDivElement | null>(null);
  const skills = skillBatches[skillBatch];

  const handleSkillSelect = (skill: Skill) => {
    setSelectedSkillId(skill.id);
    setPrompt(skill.title);
    setStatus("");
  };

  const handleSubmit = () => {
    if (!prompt.trim()) return;
    setStatus("本地预览已提交，未连接 Agent 服务");
  };

  const toggleModel = (modelId: string) => {
    setSelectedModelIds((ids) =>
      ids.includes(modelId) ? ids.filter((id) => id !== modelId) : [...ids, modelId],
    );
  };

  const switchModelTab = (kind: AgentModelKind) => {
    setActiveModelTab(kind);
    const section = kind === "image" ? imageSectionRef.current : videoSectionRef.current;
    section?.scrollIntoView({ block: "start", behavior: "smooth" });
  };

  const skillHeadline =
    editorMode === "storyboard" ? "让 Skill 帮你迈出第一步" : "选一个 Skill，让创作更快一步";

  return (
    <aside
      data-liblib-overlay="agent"
      data-agent-drawer
      onKeyDown={(event) => {
        if (event.key === "Escape" && openMenu) {
          event.stopPropagation();
          setOpenMenu(null);
        }
      }}
      className="relative z-50 hidden h-screen w-[340px] shrink-0 flex-col border-l border-white/[0.08] bg-[#1b1b1b] text-[#ededed] sm:flex"
    >
      <header className="flex h-14 shrink-0 items-center border-b border-white/[0.08] px-3">
        <span className="text-sm font-medium text-[#f2f2f2]">新对话</span>
        <div className="ml-auto flex items-center gap-0.5 text-[#8b8b8b]">
          <button
            type="button"
            disabled
            title="当前已是新对话"
            aria-label="当前已是新对话"
            className="flex size-7 items-center justify-center rounded-md opacity-40"
          >
            <MessageSquarePlus size={15} />
          </button>
          <button
            type="button"
            title="历史对话"
            aria-label="历史对话"
            className="flex size-7 items-center justify-center rounded-md hover:bg-white/[0.08] hover:text-white"
          >
            <History size={15} />
          </button>
          <button
            type="button"
            disabled
            title="新对话无法分享"
            aria-label="新对话无法分享"
            className="flex size-7 items-center justify-center rounded-md opacity-40"
          >
            <Share2 size={15} />
          </button>
          <button
            type="button"
            title="Agent 设置"
            aria-label="Agent 设置"
            className="flex size-7 items-center justify-center rounded-md hover:bg-white/[0.08] hover:text-white"
          >
            <Settings size={15} />
          </button>
          <button
            type="button"
            title="CLI & Skill"
            aria-label="CLI & Skill"
            className="flex size-7 items-center justify-center rounded-md hover:bg-white/[0.08] hover:text-white"
          >
            <SlidersHorizontal size={15} />
          </button>
          <button
            type="button"
            onClick={toggleAgent}
            title="关闭"
            aria-label="关闭"
            className="flex size-7 items-center justify-center rounded-md hover:bg-white/[0.08] hover:text-white"
          >
            <PanelRightClose size={15} />
          </button>
        </div>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto px-2.5 py-3">
        <div className="flex min-h-full flex-col justify-end">
          <div className="mb-2 flex items-center gap-2 px-1 text-xs text-[#d6d6d6]">
            <Sparkles size={15} className="text-[#ededed]" />
            <span className="min-w-0 flex-1 truncate">{skillHeadline}</span>
            <button
              type="button"
              data-agent-refresh
              onClick={() => {
                setSkillBatch((value) => (value + 1) % skillBatches.length);
                setSelectedSkillId(null);
                setStatus("");
              }}
              className="flex shrink-0 items-center gap-1 rounded-md px-1.5 py-1 text-[10px] text-[#888] hover:bg-white/[0.07] hover:text-white"
            >
              <RefreshCw size={11} />
              换一批
            </button>
          </div>

          <div className="grid grid-cols-2 gap-2">
            {skills.map((skill) => (
              <SkillCard
                key={skill.id}
                skill={skill}
                selected={selectedSkillId === skill.id}
                onSelect={() => handleSkillSelect(skill)}
              />
            ))}
          </div>

          {showNotification && (
            <div data-agent-notification className="mt-3 flex min-h-10 items-center gap-2 rounded-lg bg-[#2d6aef] px-3 text-[11px] text-white">
              <span className="min-w-0 flex-1 truncate">开启浏览器通知，及时获取最新消息</span>
              <button
                type="button"
                data-agent-notification-enable
                onClick={() => {
                  setNotificationsEnabled(true);
                  setShowNotification(false);
                }}
                className="shrink-0 font-medium hover:text-white/80"
              >
                {notificationsEnabled ? "已开启" : "开启"}
              </button>
              <button
                type="button"
                data-agent-notification-close
                onClick={() => setShowNotification(false)}
                aria-label="关闭浏览器通知提示"
                className="flex size-5 shrink-0 items-center justify-center rounded hover:bg-white/10"
              >
                <X size={13} />
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="shrink-0 border-t border-white/[0.08] p-2.5">
        <div data-agent-composer className="relative rounded-xl border border-white/[0.1] bg-[#242424] p-2 focus-within:border-white/20">
          {openMenu === "model" && (
            <div
              data-agent-model-menu
              className="absolute bottom-full left-0 mb-2 w-[288px] rounded-xl border border-white/[0.1] bg-[#242424] p-2 shadow-2xl"
            >
              <p className="px-1 pb-1.5 text-xs font-medium text-[#ededed]">选择模型</p>
              <div className="flex gap-1 pb-1.5" role="tablist" aria-label="模型分区">
                <button
                  type="button"
                  role="tab"
                  data-agent-model-tab="image"
                  aria-pressed={activeModelTab === "image"}
                  onClick={() => switchModelTab("image")}
                  className="flex-1 rounded-md px-2 py-1 text-[11px] text-[#d6d6d6] hover:bg-white/[0.07] aria-pressed:bg-white/[0.12] aria-pressed:text-white"
                >
                  图片
                </button>
                <button
                  type="button"
                  role="tab"
                  data-agent-model-tab="video"
                  aria-pressed={activeModelTab === "video"}
                  onClick={() => switchModelTab("video")}
                  className="flex-1 rounded-md px-2 py-1 text-[11px] text-[#d6d6d6] hover:bg-white/[0.07] aria-pressed:bg-white/[0.12] aria-pressed:text-white"
                >
                  视频
                </button>
              </div>
              <div className="max-h-[300px] overflow-y-auto">
                <div ref={imageSectionRef}>
                  <p className="px-2 pb-1 pt-1 text-[10px] text-[#8b8b8b]">图片</p>
                  <ul>
                    {agentModelCatalog
                      .filter((model) => model.kind === "image")
                      .map((model) => (
                        <AgentModelRow
                          key={model.id}
                          model={model}
                          selected={selectedModelIds.includes(model.id)}
                          onToggle={() => toggleModel(model.id)}
                        />
                      ))}
                  </ul>
                </div>
                <div ref={videoSectionRef}>
                  <p className="px-2 pb-1 pt-2 text-[10px] text-[#8b8b8b]">视频</p>
                  <ul>
                    {agentModelCatalog
                      .filter((model) => model.kind === "video")
                      .map((model) => (
                        <AgentModelRow
                          key={model.id}
                          model={model}
                          selected={selectedModelIds.includes(model.id)}
                          onToggle={() => toggleModel(model.id)}
                        />
                      ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {openMenu === "mode" && (
            <div
              data-agent-mode-menu
              className="absolute bottom-full left-0 mb-2 w-[248px] rounded-xl border border-white/[0.1] bg-[#242424] p-1.5 shadow-2xl"
            >
              {agentModeOptions.map((option) => (
                <button
                  key={option.id}
                  type="button"
                  role="menuitemradio"
                  data-agent-mode={option.id}
                  aria-checked={agentMode === option.id}
                  onClick={() => setAgentMode(option.id)}
                  className="flex w-full items-start gap-2 rounded-lg px-2 py-2 text-left hover:bg-white/[0.06]"
                >
                  <span className="min-w-0 flex-1">
                    <span className="block text-xs text-[#e9e9e9]">{option.title}</span>
                    <span className="mt-0.5 block text-[10px] text-[#8b8b8b]">{option.description}</span>
                  </span>
                  {agentMode === option.id && (
                    <Check size={14} className="mt-0.5 shrink-0 text-[#09caf5]" aria-label={`${option.title}已选中`} />
                  )}
                </button>
              ))}
            </div>
          )}

          <textarea
            value={prompt}
            onChange={(event) => {
              setPrompt(event.target.value);
              setStatus("");
            }}
            placeholder="开始你的创作，或者 @ 引用工作流/节点/资源"
            className="h-16 w-full resize-none bg-transparent px-1 text-xs leading-5 outline-none placeholder:text-[#666]"
          />
          {status && <p data-agent-status className="px-1 pb-1 text-[10px] text-[#75d7e8]">{status}</p>}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-0.5 text-[#888]">
              <button
                type="button"
                title="添加附件"
                aria-label="添加附件"
                onClick={() => setStatus("本地预览：附件上传未接入")}
                className="flex size-7 items-center justify-center rounded-md hover:bg-white/[0.08] hover:text-white"
              >
                <Plus size={15} />
              </button>
              <button
                type="button"
                title="选择模型"
                aria-label="选择模型"
                aria-expanded={openMenu === "model"}
                onClick={() => setOpenMenu((menu) => (menu === "model" ? null : "model"))}
                className={cn(
                  "flex size-7 items-center justify-center rounded-md hover:bg-white/[0.08] hover:text-white",
                  openMenu === "model" && "bg-white/[0.1] text-white",
                )}
              >
                <Box size={14} />
              </button>
              <button
                type="button"
                title="Skill"
                aria-label="Skill"
                onClick={() => setStatus("本地预览：Skill 面板未接入")}
                className="flex size-7 items-center justify-center rounded-md hover:bg-white/[0.08] hover:text-white"
              >
                <Bookmark size={14} />
              </button>
              <button
                type="button"
                title="生成模式"
                aria-label="生成模式"
                aria-expanded={openMenu === "mode"}
                onClick={() => setOpenMenu((menu) => (menu === "mode" ? null : "mode"))}
                className={cn(
                  "flex size-7 items-center justify-center rounded-md hover:bg-white/[0.08] hover:text-white",
                  openMenu === "mode" && "bg-white/[0.1] text-white",
                )}
              >
                <RefreshCw size={14} />
              </button>
            </div>
            <button
              type="button"
              data-agent-send
              onClick={handleSubmit}
              disabled={!prompt.trim()}
              aria-label="Send"
              className="flex size-8 items-center justify-center rounded-xl bg-[#ededed] text-[#171717] transition-colors hover:bg-white disabled:bg-[#8c8c8c] disabled:text-[#3b3b3b]"
            >
              <Send size={14} />
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
}
