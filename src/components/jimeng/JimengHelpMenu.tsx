"use client";

import { useEffect, useRef } from "react";
import {
  BookOpen,
  CircleHelp,
  Command,
  Sparkles,
  Stamp,
  Terminal,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

/**
 * 顶栏账号菜单 (原「帮助下拉」, Batch 7)。
 *
 * ── Batch 826 全面对齐源站实测 ─────────────────────────────────────
 * 此前这里只有一句「一列五项」的近似实现，与源站不是一回事：
 *   容器 240×268 p-2、无 testid、无可访问名、项高 44、头是一行 12px 灰字。
 * 源站实测（@1680×826，登录态，`[data-testid="canvas-user-menu"]`）：
 *   240×312 @[1428,56]  bg rgb(34,34,34)  r12  p-1  gap-1  flex-col
 *   ├ 头行 232×56 @[4,4]  p 8/12  gap-12
 *   │   头像 36×36 r50% bg white/4  +  昵称 14/22/w500 @[64,21]
 *   ├ 分隔条容器 232×4 @[4,64]，内含 208×1 mx-12 bg white/4
 *   └ 6 枚 role=menuitem 232×36，y = 72/112/152/192/232/272（步进 40）
 *       每枚 p 9/12  gap-8  r8  13/20/400  color rgb(255,255,255)
 *       图标 16×16 包在 16×16 span 里，文案 184×20
 * 4 + 56 + 4 + 4 + 4 + 6×36 + 5×4 + 4 = 312，与源站严丝合缝。
 *
 * 本批补上的两处**真缺口**：
 *   1. 少了第 6 枚「新功能许愿」。实测它开外链
 *      https://bytedance.larkoffice.com/share/base/form/shrcnqQGbwjK0rSJpJiNMVWCecc
 *      （_blank，用打桩 window.open 取的，没真开页）。
 *      240→312 的 44px 差就是它：36 + 4。
 *   2. 容器既无 `data-testid` 也无可访问名 —— 全画布 8 个浮层里唯一的例外。
 *      源站两样都有（testid + aria-labelledby 指向触发器）。没有锚点意味着
 *      自动化只能靠 `[role=menu]` 猜；而批 821 刚给分享面板的权限下拉也加了
 *      `role=menu`，于是这个选择器**真的歧义了**。
 *
 * 昵称是**账号专属**的（源站样本为「西卡文案馆」），复刻用占位并按 812 门禁
 * 走 MOCK_MARK 标注。图标沿用 lucide（CLONE_DECISION，近似）。
 *
 * ── Batch 820：另外 4 项此前是**真死按钮** ──────────────────────────
 * 复刻的 onClick 写的是
 *     onClick={() => { if (label === "快捷键") onOpenShortcuts?.(); onClose(); }}
 * 每个按钮都**有 onClick**，所以"有没有 handler"这种存在性检查数不出问题 ——
 * 这正是 scripts/jimeng_dead_button_audit.py 漏掉它们的原因（它确实是按
 * 点击前后状态比对判定的，但**账号菜单这个浮层压根没被列入普查状态**，
 * 见该文件 STATES）。
 *
 * 源站逐项实测（README §27），批 820 接上：
 *   帮助中心        → 右侧浮层 360×648 @[1304,60]
 *   使用手册        → 新标签页 https://bytedance.larkoffice.com/wiki/X1elw8hpMiqWdLki3Mlc9WWznhd
 *   AI生成水印设置 → 全屏遮罩 + 居中 616×492 弹窗，含 24×24 水印开关与 84×36 保存钮
 *   即梦CLI         → 新标签页 https://jimeng.jianying.com/ai-tool/install?from_page=new_canvas
 * 说明：帮助中心浮层在源站**加载失败**（正文是「帮助中心加载失败，请重试」），
 * 故只对齐几何，内容标注 (mock)；另三项文案与控件均取自源站实测，不加标注。
 */
import { MOCK_MARK } from "@/components/jimeng/jimengFeedback";

const MANUAL_URL = "https://bytedance.larkoffice.com/wiki/X1elw8hpMiqWdLki3Mlc9WWznhd";
const CLI_URL = "https://jimeng.jianying.com/ai-tool/install?from_page=new_canvas";
/** 批 826 实测：「新功能许愿」开的外链表（打桩 window.open 取得） */
const WISH_URL =
  "https://bytedance.larkoffice.com/share/base/form/shrcnqQGbwjK0rSJpJiNMVWCecc";
/** 源站用 aria-labelledby 指向触发器（Radix 生成的 id）。复刻给触发器一个稳定 id。 */
export const USER_MENU_TRIGGER_ID = "jimeng-user-menu-trigger";

const HELP_ITEMS: { icon: LucideIcon; label: string }[] = [
  { icon: CircleHelp, label: "帮助中心" },
  { icon: BookOpen, label: "使用手册" },
  { icon: Command, label: "快捷键" },
  { icon: Stamp, label: "AI生成水印设置" },
  { icon: Terminal, label: "即梦CLI" },
  { icon: Sparkles, label: "新功能许愿" },
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
      aria-labelledby={USER_MENU_TRIGGER_ID}
      data-testid="canvas-user-menu"
      className="absolute right-0 top-[46px] flex w-[240px] flex-col gap-1 rounded-xl p-1"
      style={{ background: "rgb(34,34,34)" }}
    >
      {/* 头行 232×56：36×36 头像 + 14/22/500 昵称。昵称是账号专属的，标注 mock */}
      <div className="flex h-14 shrink-0 items-center gap-3 rounded-xl px-3 py-2">
        <span
          aria-hidden="true"
          className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-white/[0.04] text-[11px] text-white/80"
        >
          梦
        </span>
        <span className="truncate text-[14px] font-medium leading-[22px] text-white">
          个人空间{MOCK_MARK}
        </span>
      </div>
      {/* 分隔条：232×4 容器内放 208×1，左右各 12，线在盒内垂直居中（源站 y=65.5）*/}
      <div className="flex h-1 shrink-0 items-center px-3">
        <div className="h-px w-full bg-white/[0.04]" />
      </div>
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
            // 批 826 实测：与上面两项同型，外链 _blank
            if (label === "新功能许愿") window.open(WISH_URL, "_blank", "noopener");
            if (label === "AI生成水印设置") onOpenWatermark?.();
            onClose();
          }}
          className="flex h-9 w-full shrink-0 items-center gap-2 rounded-lg px-3 py-[9px] text-[13px] leading-5 text-white hover:bg-white/10"
        >
          <span className="flex size-4 shrink-0 items-center justify-center text-white/70">
            <Icon size={16} />
          </span>
          <span className="truncate">{label}</span>
        </button>
      ))}
    </div>
  );
}
