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

  /* ── Batch 846：ARIA menu 键盘模式 ────────────────────────────────
   * SOURCE_FACT（探针 `jimeng_probe846_focustrap2.py`，登录态 1512×950，
   * 每项各自重开层测，口径与复刻侧审计一致）：
   *   · 开层**即接管焦点**，落在第一项上（实测 activeElement 就是第 1 项）
   *   · **漫游 tabindex**：8 项里只有 2 项 `tabindex="0"`（当前项 + 首项），
   *     其余 6 项全 `-1` —— 探针打到的原文：
   *       新建节点 "0" / 文本 "0" / 图片·视频·音频·时间线·主体·导演台 "-1"
   *   · **方向键在层内移动且环绕**（实测轨迹）：
   *       ArrowDown 粘贴 → 重做 → 撤销 → 新建节点（绕回来了）
   *       ArrowUp   撤销 → 重做 → 粘贴 → 新建节点
   *   · Tab **不困**（第 1 次就跑到画布左栏的「文本」上）—— 源站就是这行为，
   *     所以这里**故意不加**焦点陷阱：菜单的主路径是方向键，Tab 是旁路。
   *     （模态才该困，源站 `timeline-fullscreen-editor` 12 次 Tab 全在层内。）
   * 复刻此前三条全无：开层焦点停在 body、各项都是原生 button（tab 序里
   * N 站而不是 2 站）、方向键完全不动。判据见
   * `scripts/jimeng_unclickable_audit.py` 的 `keyboard_no_initial_focus` /
   * `keyboard_arrow_dead` 两个桶（都对照源站基线表，不是凭感觉）。
   *
   * ⚠️⚠️ **本组件和 `JimengContextMenu`（节点右键菜单）共用同一个
   *   `data-testid="canvas-context-menu"`** —— 这是**有意的**（源站两处同名，
   *   批 828 照抄，见下面 role 处的注释）。但它意味着：改右键菜单的键盘行为
   *   时**很容易改错文件**。批 846 第一版就改到了 `JimengContextMenu` 上，
   *   实测 `tabindex` 全是 null、焦点压根没动 —— 改错文件时**什么都不会报错**，
   *   只有对着真页面量才发现。所以：**画布空白处右键走的是本组件**。
   *   （`JimengContextMenu` 那个节点菜单的键盘模式源站**没单独取样**，
   *   按「源站测不到的行为不实现」的规矩暂不动它，记为待办。） */
  const [activeIdx, setActiveIdx] = useState(0);
  /* 当前项的**镜像**。方向键要靠它算 next：把计算塞进 setState 的 updater 里，
   * 等于在渲染期做副作用（还可能被 StrictMode 双调用），实测会「一顿一顿」——
   * 连按 5 下 ArrowDown 只走 1 格。放在 ref 里算，next 一次定死。 */
  const activeRef = useRef(0);
  /* 顶层项的**可用性从 props 声明式推导**，不读 DOM。
   * ⚠️ 第一版在 `roving()` 里 `ref.current.querySelectorAll(...)` 来数哪些项
   * 可用，eslint 直接判 **`Cannot access refs during render`** —— 而且它是对的：
   * 渲染期读 ref 在并发渲染下没有保证（渲染可能被打断重跑）。8 条 error 全是
   * 这个。所以「哪些项禁用」必须是**纯数据**（`hasSelection` / `clipboard` /
   * `hasReadyResource` / `canRedo` / `canUndo` 都是 props），DOM 只在
   * **事件回调**里用来落焦点。 */
  const TOP_DISABLED = [
    false,                    // 0 新建节点
    !hasSelection,           // 1 复制
    !hasSelection,           // 2 复制副本
    !clipboard,              // 3 粘贴
    !hasReadyResource,       // 4 下载
    !canRedo,                // 5 重做
    !canUndo,                // 6 撤销
    !hasSelection,           // 7 删除
  ];
  const enabledIdxs = (): number[] =>
    TOP_DISABLED.reduce<number[]>((acc, off, i) => {
      if (!off) acc.push(i);
      return acc;
    }, []);

  /** 落焦点：DOM 只在**事件回调**里读（不在渲染期，见上面那条注释） */
  const focusIdx = (i: number) => {
    if (!ref.current) return;
    const items = Array.from(
      ref.current.querySelectorAll('[role=menuitem]'),
    ).filter((el) => !el.closest('[data-testid=canvas-insert-submenu]'));
    (items[i] as HTMLElement | undefined)?.focus();
  };

  /** 漫游 tabindex：只有**当前项**和**首个可用项**在 tab 序里（源站实测 8 项里 2 项） */
  const roving = (i: number) => {
    const enabled = enabledIdxs();
    const firstEnabled = enabled.length ? enabled[0] : 0;
    // 当前项读 **state**（activeIdx）而不是 ref —— 渲染期读 ref 同理不安全。
    // activeIdx 落在禁用项上时退回首个可用项。
    const cur = activeIdx === i && enabled.includes(i) ? i : firstEnabled;
    return {
      tabIndex: i === cur || i === firstEnabled ? 0 : -1,
      onFocus: () => {
        activeRef.current = i;
        setActiveIdx(i);
      },
    };
  };

  /* 顶层项数**不写死**：源站是 8 项（探针实测 8 项里 2 项 tabindex=0），
   * 但复刻的可用项会随画布状态变（无选中时复制/粘贴/删除全禁用），而方向键
   * 本来就该在**可用项**之间走。子菜单里的项由 `focusIdx` 的 filter 排除 ——
   * 源站子菜单是独立元素（212×404 @x=666），实测方向键也不进它。 */

  /** 上下键在层内移动并**环绕**，且**跳过禁用项**（源站实测环绕，不是到头就停） */
  const step = (dir: 1 | -1) => {
    const en = enabledIdxs();
    if (en.length === 0) return;
    const pos = en.indexOf(activeRef.current);
    const next = en[(pos === -1 ? (dir > 0 ? 0 : en.length - 1)
                              : (pos + dir + en.length) % en.length)];
    activeRef.current = next;
    setActiveIdx(next);
    /* 同步落焦点。**不要**用 requestAnimationFrame 等 tabindex 更新 ——
     * `tabindex="-1"` 本来就可编程聚焦，等它没必要。 */
    focusIdx(next);
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
        return;
      }
      /* ↑↓ 在层内移动。**必须** preventDefault：不拦的话画布会跟着平移
       * （画布自己监听方向键），用户按 ↑ 菜单动了、画布也动了。 */
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        e.stopPropagation();
        step(e.key === "ArrowDown" ? 1 : -1);
        return;
      }
      if (e.key === "Home" || e.key === "End") {
        e.preventDefault();
        e.stopPropagation();
        const en = enabledIdxs();
        if (en.length === 0) return;
        const next = e.key === "Home" ? en[0] : en[en.length - 1];
        activeRef.current = next;
        setActiveIdx(next);
        focusIdx(next);
      }
    };
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    };
    // 开层即接管焦点（源站实测：焦点落在第一项上）。同步落，别用 rAF（同上）。
    // 落**首个可用项**而不是硬编码索引 0：首项被禁用时 focus() 会静默失败，
    // 焦点就压根没接管 —— 而那正是本条判据要抓的现象。
    const en = enabledIdxs();
    if (en.length) focusIdx(en[0]);
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
    // 刻意只跟 onClose：菜单是一次性浮层，重渲染期间重挂监听会把
    // 「开层即接管焦点」再执行一次，焦点被抢回第一项（方向键走到第 3 项就弹回）。
  }, [onClose]);

  const run = (fn: () => void) => () => {
    fn();
    onClose();
  };

  return (
    <div
      ref={ref}
      role="menu"
      // 批 828：批 824 给**同级**的 JimengContextMenu（节点右键菜单）补上了
      // testid + 可访问名，却漏了这一个 —— 而画布空白处右键走的正是本组件。
      // 两处是同一段代码的两个拷贝，只修一处等于没修。
      // 名字逐字取自源站实测（@1680×826，稳定后测得）：
      //   [data-testid="canvas-context-menu"] aria-label="Canvas context menu"
      //   240×172 @[900,620] position:fixed
      aria-label="Canvas context menu"
      data-testid="canvas-context-menu"
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
            {...roving(0)}
          testId="pane-menu-insert"
          onSelect={() => setSubmenuOpen(true)}
          submenuAffordance={<ChevronRight size={13} className="text-white/45" />}
        />
        {submenuOpen ? (
          <div
            className="absolute left-full top-0 ml-1 flex w-[200px] flex-col gap-1 rounded-xl p-1"
            style={{ background: MENU_PANEL_BG }}
            role="menu"
            // 批 828：只补锚点，**不补 aria-label** —— 源站这个子菜单实测同样
            // 既无 data-testid 也无 aria-label（200×404 @[1148,414] static）。
            // 源站没有的名字不编：编一个就成了"复刻自有"，得标 (mock)，而这里
            // 一个用户可见的名字都不需要。给自动化一个 testid 就够。
            data-testid="canvas-insert-submenu"
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
          {...roving(1)}
        shortcut="⌘ C"
        disabled={!hasSelection}
        onSelect={run(onCopy)}
      />
      <MenuItem
        label="复制副本"
          {...roving(2)}
        shortcut="⌘ D"
        disabled={!hasSelection}
        onSelect={run(onDuplicate)}
      />
      <MenuItem
        label="粘贴"
          {...roving(3)}
        shortcut="⌘ V"
        disabled={!clipboard}
        onSelect={run(onPaste)}
      />

      <MenuSeparator />

      <MenuItem
        label="下载"
          {...roving(4)}
        disabled={!hasReadyResource}
        disabledReason="没有可用的就绪资源"
        onSelect={onClose}
      />
      <MenuItem
        label="重做"
          {...roving(5)}
        shortcut="⌘ ⇧ Z"
        disabled={!canRedo}
        disabledReason="无需重做操作"
        onSelect={run(onRedo)}
      />
      <MenuItem
        label="撤销"
          {...roving(6)}
        shortcut="⌘ Z"
        disabled={!canUndo}
        disabledReason="无需撤销操作"
        onSelect={run(onUndo)}
      />
      <MenuItem
        label="删除"
          {...roving(7)}
        shortcut="⌫"
        disabled={!hasSelection}
        onSelect={run(onDelete)}
      />
    </div>
  );
}
