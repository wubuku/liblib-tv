"use client";

import Image from "next/image";
import {
  Box,
  ChevronRight,
  History,
  MessageSquarePlus,
  PanelRightClose,
  Plus,
  RefreshCw,
  Send,
  Share2,
  SlidersHorizontal,
  Sparkles,
  SquareDashed,
  X,
} from "lucide-react";
import { useState } from "react";
import { useUIStore } from "@/store/uiStore";
import { cn } from "@/lib/utils";

interface Skill {
  id: string;
  title: string;
  path: string;
  image: string;
}

const skillBatches: Skill[][] = [
  [
    { id: "pixar", title: "皮克斯动画风格", path: "/pixar-animation", image: "/images/scene-coffee-1.png" },
    { id: "viral", title: "爆款拉片分析", path: "/viral-video", image: "/images/scene-coffee-2.png" },
    { id: "neo-china", title: "新中式美学", path: "/neo-chinese", image: "/images/scene-coffee-3.png" },
    { id: "wuxia", title: "古典武侠镜头", path: "/hujiquan", image: "/images/scene-coffee-4.png" },
  ],
  [
    { id: "character", title: "角色一致性检查", path: "/character-consistency", image: "/images/liblib-panels/character-thumb-03.webp" },
    { id: "storyboard", title: "分镜节奏优化", path: "/storyboard-rhythm", image: "/images/storyboard-2.png" },
    { id: "lighting", title: "电影感打光", path: "/cinematic-lighting", image: "/images/liblib-panels/toolbox-08.webp" },
    { id: "continuity", title: "镜头连续性检查", path: "/shot-continuity", image: "/images/liblib-panels/toolbox-14.webp" },
  ],
];

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

export function AgentDrawer() {
  const toggleAgent = useUIStore((state) => state.toggleAgent);
  const [skillBatch, setSkillBatch] = useState(0);
  const [selectedSkillId, setSelectedSkillId] = useState<string | null>(null);
  const [prompt, setPrompt] = useState("");
  const [showNotification, setShowNotification] = useState(true);
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);
  const [status, setStatus] = useState("");
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

  return (
    <aside
      data-liblib-overlay="agent"
      data-agent-drawer
      className="relative z-50 hidden h-screen w-[340px] shrink-0 flex-col border-l border-white/[0.08] bg-[#1b1b1b] text-[#ededed] sm:flex"
    >
      <header className="flex h-14 shrink-0 items-center border-b border-white/[0.08] px-3">
        <span className="text-sm font-medium text-[#f2f2f2]">新对话</span>
        <div className="ml-auto flex items-center gap-0.5 text-[#8b8b8b]">
          <button type="button" title="新建对话" aria-label="新建对话" className="flex size-7 items-center justify-center rounded-md hover:bg-white/[0.08] hover:text-white">
            <MessageSquarePlus size={15} />
          </button>
          <button type="button" title="历史对话" aria-label="历史对话" className="flex size-7 items-center justify-center rounded-md hover:bg-white/[0.08] hover:text-white">
            <History size={15} />
          </button>
          <button type="button" title="分享对话" aria-label="分享对话" className="flex size-7 items-center justify-center rounded-md hover:bg-white/[0.08] hover:text-white">
            <Share2 size={15} />
          </button>
          <button type="button" title="CLI 与 Skill" aria-label="CLI 与 Skill" className="flex size-7 items-center justify-center rounded-md hover:bg-white/[0.08] hover:text-white">
            <SlidersHorizontal size={15} />
          </button>
          <button type="button" onClick={toggleAgent} title="关闭 Agent" aria-label="关闭 Agent" className="flex size-7 items-center justify-center rounded-md hover:bg-white/[0.08] hover:text-white">
            <PanelRightClose size={15} />
          </button>
        </div>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto px-2.5 py-3">
        <div className="flex min-h-full flex-col justify-end">
          <div className="mb-2 flex items-center gap-2 px-1 text-xs text-[#d6d6d6]">
            <Sparkles size={15} className="text-[#ededed]" />
            <span className="min-w-0 flex-1 truncate">Skill 就位, ready when you...</span>
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
        <div data-agent-composer className="rounded-xl border border-white/[0.1] bg-[#242424] p-2 focus-within:border-white/20">
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
              <button type="button" title="添加内容" aria-label="添加内容" className="flex size-7 items-center justify-center rounded-md hover:bg-white/[0.08] hover:text-white"><Plus size={15} /></button>
              <button type="button" title="引用工作流" aria-label="引用工作流" className="flex size-7 items-center justify-center rounded-md hover:bg-white/[0.08] hover:text-white"><Box size={14} /></button>
              <button type="button" title="引用节点" aria-label="引用节点" className="flex size-7 items-center justify-center rounded-md hover:bg-white/[0.08] hover:text-white"><SquareDashed size={14} /></button>
              <button type="button" title="刷新上下文" aria-label="刷新上下文" className="flex size-7 items-center justify-center rounded-md hover:bg-white/[0.08] hover:text-white"><RefreshCw size={14} /></button>
            </div>
            <button
              type="button"
              data-agent-send
              onClick={handleSubmit}
              disabled={!prompt.trim()}
              aria-label="发送"
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
