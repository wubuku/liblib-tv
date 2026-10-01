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

import {
  MENU_PANEL_BG,
  MENU_PANEL_CLASS,
  MenuItem,
  MenuSeparator,
} from "@/components/jimeng/jimengMenuChrome";

/**
 * 画布空白右键菜单。
 *
 * ## SOURCE_FACT batch 814 (2026-10-03 @1512×950 登录态，逐元素实测)
 *
 * 源站是 **7 项 + 1 分隔线**，200×292、padding 4、圆角 12、bg rgb(38,38,38)、
 * 行 192×36 @x=4（`padding 9px 12px`、圆角 8）、行间隙 4：
 *
 * ```
 *   复制        ⌘ C        启用
 *   复制副本    ⌘ D        启用
 *   粘贴        ⌘ V        启用
 *   ─────────── separator
 *   下载                     禁用 · 原因「没有可用的就绪资源」
 *   重做        ⌘ ⇧ Z      禁用 · 原因「无需重做操作」
 *   撤销        ⌘ Z        禁用 · 原因「无需撤销操作」
 *   删除        ⌫          启用
 * ```
 *
 * `aria` = 文案本身；`title` = 启用时 `{文案} ({快捷键})`、禁用时**直接是禁用原因**；
 * 禁用原因另有一个 1×1 绝对定位的隐藏 span，由 `aria-describedby` 指过去。
 * 竖向账与缩放菜单同款：4 + 7×36 + 4 + 7×4 + 4 = 292 ✓
 *
 * 复刻此前只有 4 项（新建节点/粘贴/重做/撤销）、192 宽、padding 8、行高 44，
 * 且把「无需重做操作」当**正文**内联渲染 —— 那会把快捷键顶偏并溢出，是布局 bug。
 *
 * ## 两处刻意的不一致（如实记账）
 *
 * 1. **保留「新建节点」子菜单**。源站右键菜单里没有这一项，但它是复刻侧
 *    batch 25/221 建立的真插入通道（batch 808 把它接成了真交互），
 *    删掉等于主动删功能。与 §21 的 `⌘0`、§23 的 `Rename` 同一判据：
 *    多一个能用的入口，好过一个源站式死按钮。记为 OPEN_QUESTION 814-a。
 *
 * 2. **复制/复制副本/删除 按"选中范围"实现并据此禁用**。源站在**空画布**上
 *    这三项仍渲染为启用（纯白），但**无法安全实测**它们的作用域：源站画布
 *    只剩 1 个节点且 ⌘Z 无效、无撤销入口（§16.6 已记录），
 *    点「复制副本」或「删除」会**不可逆**地改动它。故按画布类工具的
 *    通行约定实现为选中范围，并据此置灰；不复制"亮着但什么都不做"。
 *    记为 OPEN_QUESTION 814-b。
 *
 * 「下载」的禁用条件取自源站原因文案**「没有可用的就绪资源」**的字面意思：
 * 画布上没有任何带媒体的节点时禁用。
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
  hasSelection,
  hasReadyResource,
  onClose,
  onInsert,
  onCopy,
  onDuplicate,
  onDelete,
  onPaste,
  onUndo,
  onRedo,
}: {
  state: JimengPaneMenuState;
  canUndo: boolean;
  canRedo: boolean;
  clipboard: boolean;
  hasSelection: boolean;
  hasReadyResource: boolean;
  onClose: () => void;
  onInsert: (kind: "video" | "image" | "text" | "audio") => void;
  onCopy: () => void;
  onDuplicate: () => void;
  onDelete: () => void;
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

  const run = (fn: () => void) => () => {
    fn();
    onClose();
  };

  return (
    <div
      ref={ref}
      role="menu"
      // 200 宽 / padding 4 / 行间隙 4 —— 与缩放菜单同一套（batch 814 收口到
      // jimengMenuChrome，此前这里是 w-48 p-2，行高 44）
      className={`fixed z-[200] ${MENU_PANEL_CLASS}`}
      style={{ left: state.x, top: state.y, background: MENU_PANEL_BG }}
    >
      {/* 新建节点 (hover 展开子菜单) —— 复刻侧独有，见文件头 OPEN_QUESTION 814-a */}
      <div
        className="relative"
        onMouseEnter={() => setSubmenuOpen(true)}
        onMouseLeave={() => setSubmenuOpen(false)}
      >
        {/* Batch 808: 此前 onClick 是 toggle，配合 onMouseEnter 就出了个怪现象 ——
            指针移上来子菜单已开，再点一下反而把它关掉。用户点「新建节点」
            看起来毫无反应。改成「只开不关」：关子菜单交给 onMouseLeave，
            与源站 hover 展开的行为一致。 */}
        <MenuItem
          label="新建节点"
          testId="pane-menu-insert"
          onSelect={() => setSubmenuOpen(true)}
          submenuAffordance={<ChevronRight size={13} className="text-white/45" />}
        />
        {submenuOpen ? (
          <div
            className="absolute left-full top-0 ml-1 flex w-[200px] flex-col gap-1 rounded-xl p-1"
            style={{ background: MENU_PANEL_BG }}
            role="menu"
          >
            {/* 批 221 SOURCE_FACT: 子菜单以「添加节点」表头开始 */}
            <p className="flex h-8 shrink-0 items-center px-3 text-[13px] text-white/35">
              添加节点
            </p>
            {INSERT_ITEMS.map(({ icon: Icon, label, kind }) => (
              <MenuItem
                key={label}
                label={label}
                testId={kind ? `pane-menu-insert-${kind}` : undefined}
                icon={<Icon size={16} className="shrink-0 text-white/70" />}
                onSelect={() => {
                  if (kind) onInsert(kind);
                  onClose();
                }}
              />
            ))}
          </div>
        ) : null}
      </div>

      {/* ↓ 源站 7 项，顺序与文案逐字对齐 */}
      <MenuItem
        label="复制"
        shortcut="⌘ C"
        disabled={!hasSelection}
        onSelect={run(onCopy)}
      />
      <MenuItem
        label="复制副本"
        shortcut="⌘ D"
        disabled={!hasSelection}
        onSelect={run(onDuplicate)}
      />
      <MenuItem
        label="粘贴"
        shortcut="⌘ V"
        disabled={!clipboard}
        onSelect={run(onPaste)}
      />

      <MenuSeparator />

      <MenuItem
        label="下载"
        disabled={!hasReadyResource}
        disabledReason="没有可用的就绪资源"
        onSelect={onClose}
      />
      <MenuItem
        label="重做"
        shortcut="⌘ ⇧ Z"
        disabled={!canRedo}
        disabledReason="无需重做操作"
        onSelect={run(onRedo)}
      />
      <MenuItem
        label="撤销"
        shortcut="⌘ Z"
        disabled={!canUndo}
        disabledReason="无需撤销操作"
        onSelect={run(onUndo)}
      />
      <MenuItem
        label="删除"
        shortcut="⌫"
        disabled={!hasSelection}
        onSelect={run(onDelete)}
      />
    </div>
  );
}
