"use client";

import { useState } from "react";
import {
  ArrowDownToLine,
  Clapperboard,
  HelpCircle,
  Image as ImageIcon,
  Proportions,
  UserRoundPlus,
  Layers,
} from "lucide-react";
import { cn } from "@/lib/utils";

// Batch 536: 2026-09-27 源站采样（liblib-source-exploration-2026-09-25
// NOTES §8 + 截图 18）——3D 导演台最左窄图标栏（约 46px）。
// Batch 537: 同日 CDP DOM 补采修正——rail 实际七入口（aria-label 实证）：
// 场景 / 添加角色 / 添加机位 / 全景图 / 选择画幅比例 / AI 识图导入 +
// 底部帮助（? 圆钮）。仅场景（场景树）与添加角色 flyout 在 clone 有实现；
// 添加机位为直接动作（无面板采样），其余面板未采样（SOURCE_UNCERTAIN）
// 做视觉切换不导航（CLONE_DECISION）。
const railEntries = [
  { id: "scene", label: "场景", icon: Layers, kind: "panel" },
  { id: "add-character", label: "添加角色", icon: UserRoundPlus, kind: "flyout" },
  { id: "add-camera", label: "添加机位", icon: Clapperboard, kind: "action" },
  { id: "panorama", label: "全景图", icon: ImageIcon, kind: "panel" },
  { id: "aspect-ratio", label: "选择画幅比例", icon: Proportions, kind: "panel" },
  { id: "ai-import", label: "AI 识图导入", icon: ArrowDownToLine, kind: "panel" },
] as const;

// 添加角色 flyout 菜单（截图 44-director-rail-23 DOM/视觉转录）。
const characterFlyout = [
  { id: "local-upload", label: "本地上传", kind: "upload" as const },
  { id: "standard-male", label: "标准男性", kind: "preset" as const },
  { id: "standard-female", label: "标准女性", kind: "preset" as const },
  { id: "muscular", label: "健硕", kind: "preset" as const },
  { id: "slim", label: "纤细", kind: "preset" as const },
  { id: "teen", label: "少年", kind: "preset" as const },
  { id: "child", label: "儿童", kind: "preset" as const },
  { id: "broad", label: "宽厚", kind: "preset" as const },
  { id: "chibi", label: "二头身", kind: "preset" as const },
  { id: "crowd-3x3", label: "群众 (3x3)", kind: "submenu" as const },
  { id: "geometry", label: "几何模型", kind: "submenu" as const },
];

export function DirectorIconRail() {
  const [active, setActive] = useState<string>("scene");
  const [characterFlyoutOpen, setCharacterFlyoutOpen] = useState(false);

  const select = (id: string) => {
    setActive(id);
    setCharacterFlyoutOpen(id === "add-character");
  };

  return (
    <div
      data-director-icon-rail
      aria-label="导演台资源栏"
      className="absolute inset-y-0 left-0 z-30 flex w-[46px] flex-col items-center gap-1 border-r border-white/[0.07] bg-[#1a1a1a] py-3"
    >
      <div className="flex flex-col items-center gap-1">
        {railEntries.map((entry) => {
          const Icon = entry.icon;
          const isActive = active === entry.id;
          return (
            <div key={entry.id} className="relative">
              <button
                type="button"
                data-director-rail-entry={entry.id}
                aria-label={entry.label}
                title={entry.label}
                aria-pressed={isActive}
                onClick={() => select(entry.id)}
                className={cn(
                  "flex size-8 items-center justify-center rounded-lg text-[#a5a5a5] transition-colors",
                  isActive ? "bg-white/[0.12] text-white" : "hover:bg-white/[0.06] hover:text-[#d8d8d8]",
                )}
              >
                <Icon size={16} />
              </button>
              {entry.id === "add-character" && characterFlyoutOpen && (
                <div
                  data-director-character-flyout
                  aria-label="添加角色"
                  className="absolute left-[calc(100%+8px)] top-0 z-40 w-[150px] rounded-xl border border-white/10 bg-[#242424] p-1.5 shadow-[0_16px_40px_rgba(0,0,0,0.5)]"
                >
                  {characterFlyout.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      data-director-character-option={item.id}
                      className="flex h-8 w-full items-center gap-2 rounded-lg px-2 text-left text-xs text-[#d8d8d8] hover:bg-white/[0.07]"
                    >
                      <span className="min-w-0 flex-1 truncate">{item.label}</span>
                      {item.kind === "submenu" && (
                        <span aria-hidden="true" className="text-[10px] text-[#777]">›</span>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
      <button
        type="button"
        data-director-rail-entry="help"
        aria-label="帮助"
        title="帮助"
        className="mt-auto flex size-8 items-center justify-center rounded-full text-[#a5a5a5] hover:bg-white/[0.06] hover:text-[#d8d8d8]"
      >
        <HelpCircle size={16} />
      </button>
    </div>
  );
}
