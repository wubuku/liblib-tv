"use client";

import { Bot, ChevronRight, ImageIcon, Send, Sparkles, Video, X } from "lucide-react";
import { useUIStore } from "@/store/uiStore";

const skills = [
  { icon: ImageIcon, title: "根据剧本生成分镜", subtitle: "解析场景并组织关键镜头" },
  { icon: Sparkles, title: "保持角色一致性", subtitle: "从参考图提取人物特征" },
  { icon: Video, title: "将分镜合成为视频", subtitle: "连接镜头并补充运镜提示" },
];

export function AgentDrawer() {
  const toggleAgent = useUIStore((state) => state.toggleAgent);

  return (
    <aside className="relative z-50 hidden h-screen w-[340px] shrink-0 flex-col border-l border-white/[0.08] bg-[#1b1b1b] text-[#ededed] sm:flex">
      <header className="flex h-14 items-center border-b border-white/[0.08] px-4">
        <Bot size={17} />
        <span className="ml-2 text-sm font-medium">Agent</span>
        <button onClick={toggleAgent} className="ml-auto flex h-7 w-7 items-center justify-center rounded-md text-[#777] hover:bg-white/[0.08] hover:text-white" aria-label="关闭 Agent">
          <X size={15} />
        </button>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-5">
        <p className="text-xs leading-5 text-[#8c8c8c]">从当前画布开始，可以直接让 Agent 组织分镜、检查素材或生成下一步方案。</p>
        <h3 className="mb-2 mt-6 text-xs text-[#777]">推荐技能</h3>
        <div className="space-y-2">
          {skills.map((skill) => {
            const Icon = skill.icon;
            return (
              <button key={skill.title} className="flex w-full items-center gap-3 rounded-lg border border-white/[0.08] bg-[#222] p-3 text-left hover:bg-[#282828]">
                <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#303030] text-[#cfcfcf]">
                  <Icon size={16} />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block text-xs text-[#efefef]">{skill.title}</span>
                  <span className="mt-1 block truncate text-[11px] text-[#777]">{skill.subtitle}</span>
                </span>
                <ChevronRight size={14} className="text-[#666]" />
              </button>
            );
          })}
        </div>
      </div>

      <div className="border-t border-white/[0.08] p-3">
        <div className="rounded-xl border border-white/[0.1] bg-[#242424] p-2 focus-within:border-white/20">
          <textarea className="h-16 w-full resize-none bg-transparent px-1 text-xs leading-5 outline-none placeholder:text-[#666]" placeholder="告诉 Agent 你想如何处理当前画布" />
          <div className="flex justify-end">
            <button className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#ededed] text-[#171717]" aria-label="发送">
              <Send size={14} />
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
}
