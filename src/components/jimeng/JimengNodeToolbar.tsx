"use client";

import { useState } from "react";
import {
  Camera,
  ChevronDown,
  Clapperboard,
  Diamond,
  Download,
  FileSearch,
  Maximize2,
  Scan,
  Scissors,
  Sparkles,
} from "lucide-react";
import { NodeToolbar, Position } from "@xyflow/react";

import { VipDiamond } from "@/components/jimeng/icons";
import { useJimengStore } from "@/store/jimengStore";

/**
 * 选中视频节点后上方弹出的操作工具条 (复刻重心, Batch 2)。
 *
 * 证据 (SOURCE_FACT, docs/research/jimeng-canvas/README.md §6):
 * - 载体 xyflow <NodeToolbar>，位于节点上方；rgb(32,32,32) r12 h40
 * - 条目: 局部重拍✦ / 智能超清✦ / 视频编辑✦ / 截取帧∨ / 补帧✦ / 视频修剪 /
 *   提示词反推 ｜分隔线｜ 全屏 / 下载；✦=VIP rgb(0,158,250) 14×14
 * - 条目 13px/400 白色 + 16×16 前置图标；尾部图标钮 32×32 r8
 * - 截取帧下拉: rgb(38,38,38) r12，项 首帧/尾帧/自定义，锚在按钮下方居中
 * Batch 66 (SOURCE_FACT): 下载受保存状态门控 — 保存中… 禁用 (rgba
 * white/20 + title 导出前请保存画布)，已保存 可用 (62-first-frame-result
 * 下载亮色 vs 62-multiselect 下载灰暗)。
 */

type ToolbarItem =
  | { kind: "action"; label: string; icon: typeof Scan; vip?: boolean }
  | { kind: "dropdown"; label: string; icon: typeof Scan; menu: string[] };

const ITEMS: ToolbarItem[] = [
  { kind: "action", label: "局部重拍", icon: Scan, vip: true },
  { kind: "action", label: "智能超清", icon: Sparkles, vip: true },
  { kind: "action", label: "视频编辑", icon: Clapperboard, vip: true },
  { kind: "dropdown", label: "截取帧", icon: Camera, menu: ["首帧", "尾帧", "自定义"] },
  { kind: "action", label: "视频修剪", icon: Scissors },
];

export function JimengNodeToolbar({
  visible,
  onAction,
}: {
  visible: boolean;
  onAction?: (label: string) => void;
}) {
  const [openMenu, setOpenMenu] = useState<string | null>(null);
  // 批 484 SOURCE_FACT: 工具下拉 (预设 hover→补帧子菜单 + 提示词反推)
  const [toolOpen, setToolOpen] = useState(false);
  const [presetOpen, setPresetOpen] = useState(false);
  const saved = useJimengStore((s) => s.project.saved);

  const toggleMenu = (label: string) =>
    setOpenMenu((cur) => (cur === label ? null : label));

  const runAction = (label: string) => {
    setOpenMenu(null);
    onAction?.(label);
  };

  return (
    <NodeToolbar isVisible={visible} position={Position.Top} offset={36}>
      <div className="jimeng-node-toolbar flex h-10 select-none items-center gap-0.5 px-1.5">
        {ITEMS.map((item) => {
          const Icon = item.icon;
          const active = openMenu === item.label;
          return (
            <div key={item.label} className="relative">
              <button
                type="button"
                onClick={
                  item.kind === "dropdown"
                    ? () => toggleMenu(item.label)
                    : () => runAction(item.label)
                }
                className={`jimeng-node-toolbar-item flex h-8 items-center gap-1 whitespace-nowrap px-2 text-[13px] leading-none text-white ${
                  active ? "bg-white/10" : ""
                }`}
              >
                <Icon size={16} className="shrink-0" />
                {item.label}
                {"vip" in item && item.vip ? <VipDiamond size={14} /> : null}
                {item.kind === "dropdown" ? (
                  <ChevronDown size={12} className="ml-0.5 shrink-0 text-white/70" />
                ) : null}
              </button>

              {item.kind === "dropdown" && active ? (
                <div
                  className="absolute left-1/2 top-full z-[120] mt-2 -translate-x-1/2 rounded-xl p-1"
                  style={{ background: "rgb(38,38,38)" }}
                >
                  {item.menu.map((entry) => (
                    <button
                      key={entry}
                      type="button"
                      onClick={() => runAction(`${item.label}:${entry}`)}
                      className="flex h-10 w-full items-center gap-2 whitespace-nowrap rounded-lg px-2.5 text-[13px] text-white hover:bg-white/10"
                    >
                      <Camera size={16} className="shrink-0 text-white/85" />
                      {entry}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          );
        })}

        {/* 批 484 SOURCE_FACT: 工具下拉——预设 (hover 展开补帧子菜单)
            + 提示词反推；主条目已收缩为六项 (670×40) */}
        <div className="relative">
          <button
            type="button"
            onClick={() => {
              setToolOpen((v) => !v);
              setPresetOpen(false);
            }}
            className={`jimeng-node-toolbar-item flex h-8 items-center gap-1 whitespace-nowrap px-2 text-[13px] leading-none text-white ${
              toolOpen ? "bg-white/10" : ""
            }`}
          >
            工具
            <ChevronDown size={12} className="ml-0.5 shrink-0 text-white/70" />
          </button>
          {toolOpen ? (
            <div
              className="absolute left-1/2 top-full z-[120] mt-2 -translate-x-1/2 rounded-xl p-1"
              style={{ background: "rgb(38,38,38)" }}
            >
              <div
                className="relative"
                onMouseEnter={() => setPresetOpen(true)}
                onMouseLeave={() => setPresetOpen(false)}
              >
                <button
                  type="button"
                  className="flex h-7 w-full items-center whitespace-nowrap rounded-lg px-2.5 text-[13px] text-white hover:bg-white/10"
                >
                  预设
                </button>
                {presetOpen ? (
                  <div
                    className="absolute bottom-full left-0 z-[130] mb-1 rounded-xl p-1"
                    style={{ background: "rgb(38,38,38)" }}
                  >
                    <button
                      type="button"
                      onClick={() => runAction("补帧")}
                      className="flex h-9 w-full items-center whitespace-nowrap rounded-lg px-2.5 text-[13px] text-white hover:bg-white/10"
                    >
                      <Diamond size={16} className="mr-1 shrink-0 text-white/85" />
                      补帧
                      <VipDiamond size={14} />
                    </button>
                  </div>
                ) : null}
              </div>
              <button
                type="button"
                onClick={() => runAction("提示词反推")}
                className="flex h-9 w-full items-center whitespace-nowrap rounded-lg px-2.5 text-[13px] text-white hover:bg-white/10"
              >
                <FileSearch size={16} className="mr-1 shrink-0 text-white/85" />
                提示词反推
              </button>
            </div>
          ) : null}
        </div>

        <span className="jimeng-node-toolbar-divider mx-0.5" aria-hidden />

        <button
          type="button"
          aria-label="全屏"
          onClick={() => onAction?.("全屏预览")}
          className="jimeng-node-toolbar-item flex size-8 items-center justify-center text-white"
        >
          <Maximize2 size={16} />
        </button>
        <button
          type="button"
          aria-label="下载"
          title={saved ? undefined : "导出前请保存画布"}
          disabled={!saved}
          onClick={() => {
            if (saved) onAction?.("下载");
          }}
          className={`jimeng-node-toolbar-item flex size-8 items-center justify-center ${
            saved ? "text-white" : "cursor-not-allowed text-white/20"
          }`}
        >
          <Download size={16} />
        </button>
      </div>
    </NodeToolbar>
  );
}
