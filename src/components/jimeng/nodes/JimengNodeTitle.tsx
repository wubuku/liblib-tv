"use client";

import { useEffect, useRef, useState } from "react";

import { useJimengStore } from "@/store/jimengStore";

/**
 * 节点标题文本 (Batch 88)。
 *
 * SOURCE_FACT (batch 87/88): 各类节点的标题行均支持点击行内重命名
 * (源站 aria "Rename <标题>"，视频/文本节点实证)，Enter 提交、可撤销。
 *
 * Batch 813 SOURCE_FACT (2026-10-03 @1512×950，100% 缩放，选中态实测)：
 * 源站的重命名入口是**一个真按钮**，不是裸文字 ——
 *   `<button aria-label="Rename 视频 1">` **36×32 @ (20,-31)**、圆角 8、
 *   padding 0；盒内文字 span 36×24 @ (20,-31)（= 22 行高 + 上下 1px）。
 *   **未选中时该按钮不渲染**（只留 DIV + SPAN）。
 * 复刻此前只有裸 span，虽有同样的重命名行为，却缺了这个按钮与它的实名。
 *
 * 选中态从 store 反查而不是走 props —— 这样 7 个调用点一行都不用改
 * （其中 JimengTimelineNode 正被并行会话编辑，不去碰它），
 * 且比 `selectedNodeId` 更准：多选时按 `nodes[].selected` 逐个判定。
 *
 * 另记一条源站现状：连点该按钮 3 次都**不弹**内联输入框，只取焦
 * （activeElement 停在按钮上）。复刻**保留**点开输入框的行为 ——
 * 照抄一个点不动的按钮等于主动删功能，差异记为 OPEN_QUESTION 813-a。
 */
export function JimengNodeTitle({ id, title }: { id: string; title: string }) {
  const renameNode = useJimengStore((s) => s.renameNode);
  const isSelected = useJimengStore(
    (s) => s.nodes.find((n) => n.id === id)?.selected === true,
  );
  const [renaming, setRenaming] = useState(false);
  const [draft, setDraft] = useState(title);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (renaming) inputRef.current?.select();
  }, [renaming]);

  const startRename = () => {
    setDraft(title);
    setRenaming(true);
  };

  const commit = () => {
    const next = draft.trim();
    if (renaming && next && next !== title) renameNode(id, next);
    setRenaming(false);
  };

  if (renaming) {
    return (
      <input
        ref={inputRef}
        value={draft}
        data-testid="node-rename-input"
        onChange={(e) => setDraft(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => {
          e.stopPropagation();
          if (e.key === "Enter") commit();
          if (e.key === "Escape") {
            setDraft(title);
            setRenaming(false);
          }
        }}
        onMouseDown={(e) => e.stopPropagation()}
        className="max-w-full truncate whitespace-nowrap rounded border border-white/30 bg-transparent px-1 py-px text-[13px] leading-[22px] text-white/70 outline-none"
      />
    );
  }

  // 源站：选中 = 一个 36×32 圆角 8 的按钮，实名 `Rename {标题}`，盒内文字顶对齐
  // （按钮 32 高、文字 24 高且顶着按钮顶，所以按钮要 h-8 而不是只包住文字）。
  //
  // 文字 span 的类只有一份、两个分支共用。
  //
  // Batch 813 踩到的坑：未选中态**不能**再套一层 `<span onClick>` 包着它。
  // 那层是行内盒，会让里面的 span 变成"行内盒里的行内盒"，
  // getBoundingClientRect 按**字体**算高度（13px → 18）而不是按 line-height，
  // 于是量到 20 高、下移 3px（实测 -28/20），而源站是 24 高、-31。
  // 行内元素只有作为 flex 直接子项（被 blockify）才量得到 24 高 @ -31。
  // 所以未选中态就让文字 span 自己做 flex 直接子项，点击处理挂在它自己身上。
  const textClass =
    "max-w-full cursor-text truncate whitespace-nowrap py-px text-[13px] leading-[22px]";

  if (isSelected) {
    return (
      <button
        type="button"
        aria-label={`Rename ${title}`}
        onClick={(e) => {
          e.stopPropagation();
          startRename();
        }}
        onMouseDown={(e) => e.stopPropagation()}
        // Batch 1031-④c：补 `data-testid="flow-node-title"`（节点级契约口径）。
        //
        // 更正一条自己写错的注释：④c 第一版只加了 class 名 `flow-node-title`，
        // 并在注释里声称「源站节点标题的容器 class 是 flow-node-title」——
        // **那是假陈述**。源站取证 `source-canvas-census.json` 里这一条的字段
        // 是 `tid`（= data-testid），不是 class；`source-addsource-probe.json`
        // 也是把它列在 testids 数组里。全仓没有任何一条源站证据记录过这个 class。
        //
        // 症状极具欺骗性：class 加上了、DOM 里也真能 querySelector 到，
        // 但判据查的是 testid ⇒ 仍判「缺」⇒ 差一点就当成「判据坏了」去改判据。
        // class 保留（同名的语义钩子，调试时好定位），但契约依据的是 testid。
        data-testid="flow-node-title"
        className="flow-node-title flex h-8 max-w-full items-start rounded-lg text-left"
      >
        <span className={textClass} title={title} data-testid="node-title-text">
          {title}
        </span>
      </button>
    );
  }

  return (
    <span
      className={textClass}
      title={title}
      data-testid="node-title-text"
      onClick={(e) => {
        e.stopPropagation();
        startRename();
      }}
    >
      {title}
    </span>
  );
}
