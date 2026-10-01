"use client";

import { useEffect, useRef } from "react";
import {
  BookOpen,
  CircleHelp,
  Command,
  Stamp,
  Terminal,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

/**
 * 顶栏帮助下拉 (Batch 7)。
 *
 * 证据 (SOURCE_FACT): 点击顶栏 ? 图标弹出 240×272 rgb(34,34,34) r12 菜单:
 * 帮助中心 / 使用手册 / 快捷键 / AI生成水印设置 / 即梦CLI（每行 16px 图标）。
 * 顶部还展示租户名 — 复刻用静态「个人空间」占位 (mock)。
 * CLONE_DECISION: 行距与图标为近似 (截图读取)。
 *
 * ── Batch 820：另外 4 项此前是**真死按钮** ──────────────────────────
 * 复刻的 onClick 写的是
 *     onClick={() => { if (label === "快捷键") onOpenShortcuts?.(); onClose(); }}
 * 每个按钮都**有 onClick**，所以"有没有 handler"这种存在性检查数不出问题 ——
 * 这正是 scripts/jimeng_dead_button_audit.py 漏掉它们的原因（它确实是按
 * 点击前后状态比对判定的，但**账号菜单这个浮层压根没被列入普查状态**，
 * 见该文件 STATES）。
 *
 * 源站逐项实测（README §27），本批接上：
 *   帮助中心        → 右侧浮层 360×648 @[1304,60]
 *   使用手册        → 新标签页 https://bytedance.larkoffice.com/wiki/X1elw8hpMiqWdLki3Mlc9WWznhd
 *   AI生成水印设置 → 全屏遮罩 + 居中 616×492 弹窗，含 24×24 水印开关与 84×36 保存钮
 *   即梦CLI         → 新标签页 https://jimeng.jianying.com/ai-tool/install?from_page=new_canvas
 * 说明：帮助中心浮层在源站**加载失败**（正文是「帮助中心加载失败，请重试」），
 * 故只对齐几何，内容标注 (mock)；另三项文案与控件均取自源站实测，不加标注。
 */
const MANUAL_URL = "https://bytedance.larkoffice.com/wiki/X1elw8hpMiqWdLki3Mlc9WWznhd";
const CLI_URL = "https://jimeng.jianying.com/ai-tool/install?from_page=new_canvas";

const HELP_ITEMS: { icon: LucideIcon; label: string }[] = [
  { icon: CircleHelp, label: "帮助中心" },
  { icon: BookOpen, label: "使用手册" },
  { icon: Command, label: "快捷键" },
  { icon: Stamp, label: "AI生成水印设置" },
  { icon: Terminal, label: "即梦CLI" },
];

export function JimengHelpMenu({
  onClose,
  onOpenShortcuts,
  onOpenHelpCenter,
  onOpenWatermark,
}: {
  onClose: () => void;
  onOpenShortcuts?: () => void;
  onOpenHelpCenter?: () => void;
  onOpenWatermark?: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);

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
      className="absolute right-0 top-[calc(100%+8px)] w-[240px] rounded-xl p-2"
      style={{ background: "rgb(34,34,34)" }}
    >
      <p className="px-2 pb-1 pt-1 text-[12px] leading-6 text-white/45">个人空间</p>
      {HELP_ITEMS.map(({ icon: Icon, label }) => (
        <button
          key={label}
          type="button"
          role="menuitem"
          data-testid={`account-menu-item-${label}`}
          onClick={() => {
            // 批 820: 四项此前只关菜单（真死按钮），各自接上源站行为
            if (label === "快捷键") onOpenShortcuts?.();
            if (label === "帮助中心") onOpenHelpCenter?.();
            if (label === "使用手册") window.open(MANUAL_URL, "_blank", "noopener");
            if (label === "即梦CLI") window.open(CLI_URL, "_blank", "noopener");
            if (label === "AI生成水印设置") onOpenWatermark?.();
            onClose();
          }}
          className="flex h-11 w-full items-center gap-2.5 rounded-lg px-2.5 text-[13px] text-white/85 hover:bg-white/10"
        >
          <Icon size={16} className="shrink-0 text-white/70" />
          {label}
        </button>
      ))}
    </div>
  );
}
