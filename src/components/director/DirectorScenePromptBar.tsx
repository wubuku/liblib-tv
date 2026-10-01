"use client";

import { useState } from "react";
import { Camera, Hand, MousePointer2, MoveUp } from "lucide-react";
import { cn } from "@/lib/utils";

// Batch 535: 2026-09-27 源站采样（liblib-source-exploration-2026-09-25
// NOTES §8 + 截图 18-director-console-opened.png）——3D 导演台视口底部
// 居中胶囊条：左段三个模式图标（光标/相机/手，可切换）+「+ 描述想要
// 搭建的场景」输入 + ↑ 圆形提交。真实场景搭建为云端 AI 动作，clone
// 仅维护本地输入草稿与模式选择态，提交不触发任何生成（回显已采样
// 的本地确认即可）。视口左下 ? 帮助圆钮未采样交互，仅展示。
const sceneModes = [
  { id: "cursor", label: "光标", icon: MousePointer2 },
  { id: "camera", label: "相机", icon: Camera },
  { id: "hand", label: "手", icon: Hand },
] as const;

type SceneMode = (typeof sceneModes)[number]["id"];

export function DirectorScenePromptBar() {
  const [mode, setMode] = useState<SceneMode>("cursor");
  const [value, setValue] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const submit = () => {
    if (!value.trim()) return;
    setSubmitted(true);
    window.setTimeout(() => setSubmitted(false), 2000);
  };

  return (
    <div
      data-director-scene-prompt-bar
      className="pointer-events-none absolute inset-x-0 bottom-4 z-20 flex items-center justify-center gap-2"
    >
      <div className="pointer-events-auto flex h-11 items-center gap-0.5 rounded-full border border-white/10 bg-[#1f1f1f] px-2 shadow-[0_10px_30px_rgba(0,0,0,0.5)]">
        {sceneModes.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              type="button"
              data-director-scene-mode={item.id}
              aria-label={item.label}
              aria-pressed={mode === item.id}
              onClick={() => setMode(item.id)}
              className={cn(
                "flex size-8 items-center justify-center rounded-full text-[#b5b5b5] transition-colors",
                mode === item.id ? "bg-white/[0.12] text-white" : "hover:bg-white/[0.06]",
              )}
            >
              <Icon size={15} />
            </button>
          );
        })}
      </div>
      <div className="pointer-events-auto flex h-11 min-w-[300px] items-center gap-2 rounded-full border border-white/10 bg-[#1f1f1f] px-3 shadow-[0_10px_30px_rgba(0,0,0,0.5)]">
        <span aria-hidden="true" className="text-lg leading-none text-[#8c8c8c]">+</span>
        <input
          data-director-scene-prompt-input
          value={value}
          onChange={(event) => { setValue(event.target.value); setSubmitted(false); }}
          onKeyDown={(event) => {
            if (event.key === "Enter") submit();
          }}
          // Batch 592（源站 2026-10-01 实测）：可及名逐字是「描述想搭建的
          // 场景」——clone 原写作「描述想要搭建的场景」，多了一个「要」。
          // 源站输入区本体是 contenteditable(role=textbox, 14px)，可见
          // 占位文案另作「描述您想搭建的场景」；此处沿用 clone 的 input
          // 实现（见 batch 592 记录的未取证项）。
          placeholder="描述想搭建的场景"
          aria-label="描述想搭建的场景"
          className="min-w-0 flex-1 bg-transparent text-xs text-[#e0e0e0] outline-none placeholder:text-[#777]"
        />
        {/* Batch 592：提交钮的可及名/提示逐字为「发送」（源站实测 32×32、
            border-radius 9999px、空态底色 rgba(255,255,255,0.08)——与 clone
            原有的 disabled 态一致），无文字只有图标。 */}
        <button
          type="button"
          data-director-scene-prompt-submit
          aria-label="发送"
          title="发送"
          onClick={submit}
          disabled={!value.trim()}
          className="flex size-8 shrink-0 items-center justify-center rounded-full bg-[#e8e8e8] text-[#1a1a1a] hover:bg-white disabled:bg-white/[0.08] disabled:text-[#555]"
        >
          <MoveUp size={14} />
        </button>
      </div>
      <span
        data-director-scene-prompt-status
        aria-live="polite"
        className={cn(
          "pointer-events-auto rounded-full bg-black/60 px-2.5 py-1 text-[11px] text-[#9ddbb9] transition-opacity",
          submitted ? "opacity-100" : "opacity-0",
        )}
      >
        场景描述已记录（本地草稿）
      </span>
    </div>
  );
}
