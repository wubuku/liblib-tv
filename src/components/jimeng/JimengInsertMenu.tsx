"use client";

import {
  AudioLines,
  Folder,
  GalleryVertical,
  Image,
  MonitorPlay,
  SquareUser,
  Type,
  Upload,
  Video,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

/**
 * 「添加节点」菜单 (Batch 4/24)。
 *
 * 证据 (SOURCE_FACT): 点击节点边缘 + 圆钮弹出 192×276 菜单
 * (`rgb(38,38,38)` r12)：标题「添加节点」+ 7 项
 * 文本/图片/视频/音频/时间线/主体/导演台；行高约 44px，16px 图标 + 13px 文本。
 * Batch 24 (SOURCE_FACT): 双击节点标题弹出同款菜单，末尾多一段
 * 「从资产库添加」「本地上传」(extended)。
 * mock: 视频/图片/文本/音频真实创建；时间线/主体/导演台/资产库/本地上传关闭菜单。
 */
const MENU_ITEMS: { icon: LucideIcon; label: string }[] = [
  { icon: Type, label: "文本" },
  { icon: Image, label: "图片" },
  { icon: Video, label: "视频" },
  { icon: AudioLines, label: "音频" },
  { icon: GalleryVertical, label: "时间线" },
  { icon: SquareUser, label: "主体" },
  { icon: MonitorPlay, label: "导演台" },
];

const EXTENDED_ITEMS: { icon: LucideIcon; label: string }[] = [
  { icon: Folder, label: "从资产库添加" },
  { icon: Upload, label: "本地上传" },
];

export function JimengInsertMenu({
  onPick,
  onClose,
  extended,
}: {
  onPick: (label: string) => void;
  onClose: () => void;
  extended?: boolean;
}) {
  return (
    <div
      className="absolute top-full left-1/2 z-[120] mt-3 w-48 -translate-x-1/2 rounded-xl p-2"
      style={{ background: "rgb(38,38,38)" }}
      role="menu"
    >
      <p className="px-2 pb-1 text-[13px] leading-8 text-white/45">添加节点</p>
      {MENU_ITEMS.map(({ icon: Icon, label }) => (
        <button
          key={label}
          type="button"
          role="menuitem"
          onClick={() => {
            onPick(label);
            onClose();
          }}
          className="flex h-11 w-full items-center gap-2.5 rounded-lg px-2.5 text-[13px] text-white/85 hover:bg-white/10"
        >
          <Icon size={16} className="shrink-0 text-white/70" />
          {label}
        </button>
      ))}
      {extended ? (
        <>
          <div className="mx-2 my-1 h-px bg-white/[0.08]" />
          {EXTENDED_ITEMS.map(({ icon: Icon, label }) => (
            <button
              key={label}
              type="button"
              role="menuitem"
              onClick={() => {
                onPick(label);
                onClose();
              }}
              className="flex h-11 w-full items-center gap-2.5 rounded-lg px-2.5 text-[13px] text-white/85 hover:bg-white/10"
            >
              <Icon size={16} className="shrink-0 text-white/70" />
              {label}
            </button>
          ))}
        </>
      ) : null}
    </div>
  );
}
