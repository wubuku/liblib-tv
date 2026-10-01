"use client";

import { useEffect, useRef, useState } from "react";
import { ChevronRight } from "lucide-react";
import {
  AudioLines,
  Bot,
  Folder,
  Image,
  LayoutTemplate,
  SquarePlay,
  Type,
  Upload,
  User,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

/**
 * 画布空白右键菜单 (Batch 25)。
 *
 * 证据 (SOURCE_FACT): 空白画布右键弹出菜单: 新建节点 > (子菜单)、
 * 粘贴 ⌘V、重做 ⌘⇧Z (无历史禁用)、撤销 ⌘Z；样式与节点右键菜单同族
 * (rgb(38,38,38) r12)。批 221 采样: 面板 232×164、行 36px、重做禁用行
 * 附「无需重做操作」；「新建节点」子菜单 10 项 (222-pane-menu.json):
 * 「添加节点」表头 (white/35) + 文本/图片/视频/音频/时间线/主体/导演台/
 * 从资产库添加/本地上传 (后 5 项为仅展示 mock，CLONE_DECISION)。
 */
const INSERT_ITEMS: {
  icon: LucideIcon;
  label: string;
  kind?: "video" | "image" | "text" | "audio";
}[] = [
  { icon: Type, label: "文本", kind: "text" },
  { icon: Image, label: "图片", kind: "image" },
  { icon: SquarePlay, label: "视频", kind: "video" },
  { icon: AudioLines, label: "音频", kind: "audio" },
  // 批 221 SOURCE_FACT: 子菜单共 10 项；以下为仅展示 mock
  { icon: LayoutTemplate, label: "时间线" },
  { icon: User, label: "主体" },
  { icon: Bot, label: "导演台" },
  { icon: Folder, label: "从资产库添加" },
  { icon: Upload, label: "本地上传" },
];

export interface JimengPaneMenuState {
  x: number;
  y: number;
}

export function JimengPaneContextMenu({
  state,
  canUndo,
  canRedo,
  clipboard,
  onClose,
  onInsert,
  onPaste,
  onUndo,
  onRedo,
}: {
  state: JimengPaneMenuState;
  canUndo: boolean;
  canRedo: boolean;
  clipboard: boolean;
  onClose: () => void;
  onInsert: (kind: "video" | "image" | "text" | "audio") => void;
  onPaste: () => void;
  onUndo: () => void;
  onRedo: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [submenuOpen, setSubmenuOpen] = useState(false);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    };
        // 捕获阶段（batch 794 实测踩坑）：JimengFlow 的全局 Escape 监听注册更早，
    // 会先触发同步重渲染；重渲染使本 effect 清理并重新注册监听，
    // removeEventListener 会把该 listener 标记为 removed，浏览器在**同一次
    // 事件派发中**跳过它 → 冒泡监听收不到 Escape，浮层关不掉。
    window.addEventListener("keydown", onKey, true);
    window.addEventListener("mousedown", onDown, true);
    return () => {
      window.removeEventListener("keydown", onKey, true);
      window.removeEventListener("mousedown", onDown, true);
    };
  }, [onClose]);

  return (
    <div
      ref={ref}
      role="menu"
      className="fixed z-[200] w-48 rounded-xl p-2"
      style={{
        left: state.x,
        top: state.y,
        background: "rgb(38,38,38)",
      }}
    >
      {/* 新建节点 (hover 展开子菜单) */}
      <div
        className="relative"
        onMouseEnter={() => setSubmenuOpen(true)}
        onMouseLeave={() => setSubmenuOpen(false)}
      >
        {/* Batch 808: 此前 onClick 是 toggle，配合 onMouseEnter 就出了个怪现象 ——
            指针移上来子菜单已开，再点一下反而把它关掉。用户点「新建节点」
            看起来毫无反应。改成「只开不关」：关子菜单交给 onMouseLeave，
            与源站 hover 展开的行为一致。 */}
        <button
          type="button"
          role="menuitem"
          data-testid="pane-menu-insert"
          onClick={() => setSubmenuOpen(true)}
          className="flex h-9 w-full items-center justify-between rounded-lg px-2.5 text-[13px] text-white/85 hover:bg-white/10"
        >
          新建节点
          <ChevronRight size={13} className="text-white/45" />
        </button>
        {submenuOpen ? (
          <div
            className="absolute left-full top-0 ml-1 w-48 rounded-xl p-2"
            style={{ background: "rgb(38,38,38)" }}
            role="menu"
          >
            {/* 批 221 SOURCE_FACT: 子菜单以「添加节点」表头开始 */}
            <p className="flex h-8 items-center px-2.5 text-[13px] text-white/35">
              添加节点
            </p>
            {INSERT_ITEMS.map(({ icon: Icon, label, kind }) => (
              <button
                key={label}
                type="button"
                role="menuitem"
                onClick={() => {
                  if (!kind) {
                    onClose();
                    return;
                  }
                  onInsert(kind);
                  onClose();
                }}
                className="flex h-9 w-full items-center gap-2.5 rounded-lg px-2.5 text-[13px] text-white/85 hover:bg-white/10"
              >
                <Icon size={16} className="shrink-0 text-white/70" />
                {label}
              </button>
            ))}
          </div>
        ) : null}
      </div>

      <button
        type="button"
        role="menuitem"
        disabled={!clipboard}
        onClick={() => {
          onPaste();
          onClose();
        }}
        className={`flex h-11 w-full items-center justify-between rounded-lg px-2.5 text-[13px] ${
          clipboard ? "text-white/85 hover:bg-white/10" : "cursor-default text-white/30"
        }`}
      >
        粘贴
        <span className="text-[12px] text-white/45">⌘ V</span>
      </button>
      <div className="mx-2 my-1 h-px bg-white/[0.08]" />
      <button
        type="button"
        role="menuitem"
        disabled={!canRedo}
        onClick={() => {
          onRedo();
          onClose();
        }}
        className={`flex h-11 w-full items-center justify-between rounded-lg px-2.5 text-[13px] ${
          canRedo ? "text-white/85 hover:bg-white/10" : "cursor-default text-white/30"
        }`}
      >
        重做
        <span className="text-[12px] text-white/45">
          ⌘ ⇧ Z
          {!canRedo ? <span className="ml-1 text-white/30">无需重做操作</span> : null}
        </span>
      </button>
      <button
        type="button"
        role="menuitem"
        disabled={!canUndo}
        onClick={() => {
          onUndo();
          onClose();
        }}
        className={`flex h-11 w-full items-center justify-between rounded-lg px-2.5 text-[13px] ${
          canUndo ? "text-white/85 hover:bg-white/10" : "cursor-default text-white/30"
        }`}
      >
        撤销
        <span className="text-[12px] text-white/45">⌘ Z</span>
      </button>
    </div>
  );
}
