"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { NodeToolbar, Position as TBPosition } from "@xyflow/react";
import {
  Bold,
  ChevronDown,
  Download,
  Italic,
  List,
  ListOrdered,
  Maximize2,
  Square,
  Strikethrough,
  Type,
  Underline,
  X,
} from "lucide-react";
import type { NodeProps } from "@xyflow/react";

import { nodeRingShadow } from "@/components/jimeng/nodeChrome";
import type { JimengTextNodeData } from "@/types/jimeng";
import { JimengNodeTitle } from "@/components/jimeng/nodes/JimengNodeTitle";
import { JimengConnectHandles } from "@/components/jimeng/JimengConnectHandles";
import { useJimengStore } from "@/store/jimengStore";

/** 纯文本 → 富文本片段：转义后包一层 <p>（批 816 编辑面改成 innerHTML 后必须转义，
 *  否则节点正文里的尖括号会被当成标签解析）。 */
function escapeHtml(s: string) {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

/** 批 816: execCommand 在 Chromium 里产出的是<b>/<i>/<strike>，而源站落库的是
 *  <strong>/<em>/<s>（源站实测 innerHTML 逐条比对）。渲染效果等价，但既然是复刻，
 *  存进 store 的形态按源站来，免得日后对源站比对时对不上。 */
function normalizeRichHtml(html: string) {
  return html
    .replace(/<(b)(\s[^>]*)?>/gi, "<strong>")
    .replace(/<\/b>/gi, "</strong>")
    .replace(/<(i)(\s[^>]*)?>/gi, "<em>")
    .replace(/<\/i>/gi, "</em>")
    .replace(/<(strike|s)(\s[^>]*)?>/gi, "<s>")
    .replace(/<\/strike>/gi, "</s>")
    .replace(/<\/s>/gi, "</s>")
    // execCommand 的 formatBlock 在已是 <p> 的块上会再套一层，产出 <p><p>…</p></p>
    // （实测），顺手压平
    .replace(/<(p|h[1-6])>\s*<\1>/gi, "<$1>")
    .replace(/<\/(p|h[1-6])>\s*<\/\1>/gi, "</$1>");
}

/**
 * 文字节点 (Batch 17/38/68)。结构与视频节点同族 (SOURCE_FACT §5 骨架)。
 * Batch 68 (SOURCE_FACT): 标题图标 T 字形、选中无工具条、占位
 * 「双击编辑文本」、默认 328×340 (68-newnode-selected.png 实测)。
 * Batch 38: 双击卡片进入行内编辑，Enter/失焦提交。
 * Batch 241 (SOURCE_FACT, 241-source-text-edit.png): 编辑态卡上方出现
 * 富文本工具条——字体 T∨ / 无序列表 / 有序列表 / 加粗 B / 删除线 S /
 * 斜体 I / 下划线 U / 展开钮。
 * Batch 241b (SOURCE_FACT, 243-source-font-menu.png): 选中(非编辑)态
 * 另有工具条 背景色(调色板: 无+青绿/靛蓝/紫/橙/黄 六格) / 展开钮 /
 * 下载——「选中无工具条」的批 68 观察已被源站演进推翻。
 *
 * ── Batch 817：两个按钮名订正 + 「全屏编辑」接上 ──────────────────
 * 批 241 给这 8 个按钮起的名有两个是**猜的**，批 816 逐项向源站核对后订正
 * （aria-label 与几何均实测，见 README §26）：
 *   第 1 个：复刻「字体」   → 源站 aria-label 是英文 "Text style"，48×32（带 chevron）
 *   第 8 个：复刻「展开编辑」→ 源站 aria-label 是「**全屏**」32×32，点开的面板
 *             标题是「**全屏编辑**」（实测 126×42 的标签按钮 @[1340,406]）
 * 第 8 个此前是本文件留的 OPEN_QUESTION 816-a，本批拿到形态，接成真面板。
 *
 * ── Batch 816：工具条从"视觉 mock"接成真行为 ──────────────────────
 * 批 241 把这 8 个按钮明确标为「视觉 mock，未接真实格式化」。本批接上 7 个，
 * 依据是源站逐键实测（README §25，全部带 contenteditable 前置态门禁）：
 *   ⌘B 加粗    <p>文字</p> → <p><strong>文字</strong></p>          响应
 *   ⌘I 倾斜    → <strong><em>文字</em></strong>                  响应
 *   ⌘U 下划线  → …<u>文字</u>…                                    响应
 *   ⌘⇧X 删除线 → …<s><u>文字</u></s>…                             响应
 *   ⌘⌥1/2/3 一~三级标题  p → h1 → h2 → h3                        响应
 *   ⌘⌥0 普通文本  h1 → p                                          响应
 *   ⌘⇧8/7 无序/有序列表 → ul+li / ol+li                            响应
 * 由此可知源站编辑面是 **contenteditable DIV**（activeElement 实测 ce=true），
 * 故编辑面从 <textarea> 改为 contenteditable div，格式化走 execCommand。
 * 「展开编辑」是第 8 个按钮，源站形态待取证，暂不猜（见文件尾 OPEN_QUESTION）。
 */
export function JimengTextNode({ id, data, selected }: NodeProps) {
  const d = data as JimengTextNodeData;
  const [editing, setEditing] = useState(false);
  const [fontMenuOpen, setFontMenuOpen] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const editorRef = useRef<HTMLDivElement>(null);
  const fsRef = useRef<HTMLDivElement>(null);
  /** 批 817: 全屏面板的初始内容，在**点击那一刻**从行内编辑面取。
   *  踩过的坑：一开始让 effect 去读 d.html，灌出来是上一次保存的旧内容 ——
   *  commit() 写 store 与 setFullscreen 在同一批里，但 effect 跑的时候
   *  data prop 还没更新到。改成点击时先取值存 ref，effect 只负责灌。 */
  const fsSeedRef = useRef("");

  /** 进入编辑态的初始内容：优先富文本，回落纯文本 */
  const initialHtml = d.html ?? (d.text ? `<p>${escapeHtml(d.text)}</p>` : "");

  // 批 816: 编辑面**不用** dangerouslySetInnerHTML。
  // 实测那样写的话，点任意工具条按钮触发重渲染时 React 会把 innerHTML 重写回
  // initialHtml（这里是空串），**用户刚打的字当场消失**。改成进入编辑态时
  // 由 effect 用 ref 灌一次，之后这个节点归用户（浏览器）管，React 不再碰。
  const seededRef = useRef(false);
  useEffect(() => {
    if (!editing) {
      seededRef.current = false;
      return;
    }
    if (seededRef.current) return;
    seededRef.current = true;
    const el = editorRef.current;
    if (el) el.innerHTML = initialHtml;
    el?.focus();
  }, [editing, initialHtml]);

  // 批 817: 全屏编辑面同样由 effect 灌一次内容（理由同上面的 editing 分支：
  // 一旦用 dangerouslySetInnerHTML，重渲染就会把用户输入抹掉）
  useEffect(() => {
    if (!fullscreen) return;
    const el = fsRef.current;
    if (el) {
      el.innerHTML = fsSeedRef.current;
      el.focus();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fullscreen]);

  const updateNodeData = useJimengStore((s) => s.updateNodeData);
  // Batch 48: 提交写回 store (mock 文字节点真实联动)；批 816 起同时写富文本 HTML
  const commit = () => {
    setEditing(false);
    setFontMenuOpen(false);
    const el = editorRef.current;
    if (!el) return;
    const nextHtml = normalizeRichHtml(el.innerHTML);
    const nextText = (el.innerText || "").trim();
    updateNodeData(id, { html: nextHtml, text: nextText });
  };

  /** 批 817: 全屏编辑面的提交（写回同一个节点的 html/text） */
  const commitFs = () => {
    const el = fsRef.current;
    if (!el) return;
    updateNodeData(id, {
      html: normalizeRichHtml(el.innerHTML),
      text: (el.innerText || "").trim(),
    });
  };

  // ── Batch 816: 源站实测的 10 个文本快捷键 ──────────────────────────  // 走 execCommand：它作用在当前选区上，与源站「选区加粗」的行为一致，
  // 且不需要自己维护 Range。（批 241 的按钮是纯视觉 mock，现在共用这一套。）
  // 批 817: 全屏编辑面复用同一套格式化，故这两个函数要作用在**当前激活**的
  // 编辑面上，而不是写死 editorRef。
  const activeEditor = () => (fullscreen ? fsRef.current : editorRef.current);

  const exec = useCallback((cmd: string, value?: string) => {
    const el = activeEditor();
    if (!el) return;
    // 批 816: 点工具条按钮时焦点会短暂离开编辑面，再 focus() 回来时选区已经没了，
    // execCommand 就会作用在光标处而不是选中文字上。先存 Range、focus 后还原。
    const sel = window.getSelection();
    const saved = sel && sel.rangeCount ? sel.getRangeAt(0) : null;
    el.focus();
    if (saved && sel) {
      sel.removeAllRanges();
      sel.addRange(saved);
    }
    document.execCommand(cmd, false, value);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fullscreen]);

  /** 块级切换（普通文本 / 一~三级标题，对应面板 ⌘⌥0~3）。

   * 不用 execCommand('formatBlock')：实测它在**已经是 <p> 的块上会再套一层**，
   * 产出 `<p><p>…</p></p>`，反复按同一个键能堆出七八层。这里自己换块：
   * 找到选区所在的最内层块，用目标标签重建它并把子节点搬过去，天然幂等。
   */
  const applyBlock = useCallback((tag: string) => {
    const el = activeEditor();
    if (!el) return;
    el.focus();
    const sel = window.getSelection();
    if (!sel || !sel.rangeCount) return;

    const BLOCK = new Set(["P", "H1", "H2", "H3", "H4", "H5", "H6", "LI", "UL", "OL", "BLOCKQUOTE"]);
    let block: HTMLElement | null = sel.getRangeAt(0).startContainer as HTMLElement;
    while (block && block !== el && !(block.tagName && BLOCK.has(block.tagName))) {
      block = block.parentElement;
    }
    if (block === el) block = null;

    // 在列表里：把整个列表摊平成一个块（列表→标题/段落的常规语义）
    let target: HTMLElement | null = block;
    if (block?.tagName === "LI") {
      target = block.parentElement; // UL / OL
    }

    const next = document.createElement(tag);
    if (target) {
      if (target.tagName === "UL" || target.tagName === "OL") {
        // 摊平列表：搬 **<li> 的内容**，不是把 <li> 塞进 <p>（那是非法 HTML，
        // 实测会得到 `<p><li>…</li></p>`）
        const items = [...target.children].filter((c) => c.tagName === "LI");
        items.forEach((li, i) => {
          if (i > 0) next.appendChild(document.createElement("br"));
          while (li.firstChild) next.appendChild(li.firstChild);
        });
      } else {
        while (target.firstChild) next.appendChild(target.firstChild);
      }
      target.replaceWith(next);
    } else {
      next.textContent = sel.toString();
      el.appendChild(next);
    }
    const r = document.createRange();
    r.selectNodeContents(next);
    sel.removeAllRanges();
    sel.addRange(r);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fullscreen]);

  const onEditorKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    const mod = e.metaKey || e.ctrlKey;
    if (mod) {
      const k = e.key.toLowerCase();
      if (k === "b" && !e.shiftKey) {
        e.preventDefault(); exec("bold"); return;
      }
      if (k === "i" && !e.shiftKey) {
        e.preventDefault(); exec("italic"); return;
      }
      if (k === "u" && !e.shiftKey) {
        e.preventDefault(); exec("underline"); return;
      }
      if (k === "x" && e.shiftKey) {
        e.preventDefault(); exec("strikeThrough"); return;
      }
      if (k === "8" && e.shiftKey) {
        e.preventDefault(); exec("insertUnorderedList"); return;
      }
      if (k === "7" && e.shiftKey) {
        e.preventDefault(); exec("insertOrderedList"); return;
      }
      // ⌘⌥0~3 = 普通文本 / 一~三级标题（源站实测 p ⇄ h1/h2/h3）
      if (e.altKey && ["0", "1", "2", "3"].includes(e.key)) {
        e.preventDefault();
        applyBlock(e.key === "0" ? "p" : `h${e.key}`);
        return;
      }
    }
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      commit();
    }
    if (e.key === "Escape") {
      e.preventDefault();
      setEditing(false);
      setFontMenuOpen(false);
    }
  };

  /** 批 817: 全屏编辑面的键盘。格式化键与行内共用（exec/applyBlock 已指向
   *  当前激活面），Enter = 提交并留在全屏、Escape = 提交并关闭。
   *  行内是 Enter 提交退出、Escape 取消，两处语义不同，故分开写。 */
  const onFsKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    const mod = e.metaKey || e.ctrlKey;
    if (mod) {
      const k = e.key.toLowerCase();
      const map: Record<string, string> = { b: "bold", i: "italic", u: "underline" };
      if (!e.shiftKey && map[k]) { e.preventDefault(); exec(map[k]); return; }
      if (e.shiftKey && k === "x") { e.preventDefault(); exec("strikeThrough"); return; }
      if (e.shiftKey && k === "8") { e.preventDefault(); exec("insertUnorderedList"); return; }
      if (e.shiftKey && k === "7") { e.preventDefault(); exec("insertOrderedList"); return; }
      if (e.altKey && ["0", "1", "2", "3"].includes(e.key)) {
        e.preventDefault();
        applyBlock(e.key === "0" ? "p" : `h${e.key}`);
        return;
      }
    }
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); commitFs(); return; }
    if (e.key === "Escape") { e.preventDefault(); commitFs(); setFullscreen(false); }
  };

  // 批 241b SOURCE_FACT: 调色板 无 + 青绿/靛蓝/紫/橙/黄 (色值为 CLONE_DECISION)
  const BG_COLORS: { label: string; value: string | null }[] = [
    { label: "无", value: null },
    { label: "青绿", value: "#4ECDE6" },
    { label: "靛蓝", value: "#6B7CFF" },
    { label: "紫", value: "#A46BFF" },
    { label: "橙", value: "#FF9A4D" },
    { label: "黄", value: "#FFD44D" },
  ];

  return (
    <div
      className="group relative"
      style={{ width: d.width, height: d.height }}
      data-jimeng-node-selected={selected || undefined}
    >
      <div className="absolute inset-x-0 top-[-31px] z-10 flex h-8 items-start gap-1 text-left">
        <Type size={16} className="mt-1 shrink-0" />
        <JimengNodeTitle id={id} title={d.title} />
      </div>

      {/* 批 241b SOURCE_FACT: 选中(非编辑)态工具条 背景色/展开/下载 */}
      <NodeToolbar isVisible={selected === true && !editing} position={TBPosition.Top} offset={36}>
        <div className="jimeng-node-toolbar relative flex h-10 select-none items-center gap-1 px-1.5">
          <div className="relative">
            <button
              type="button"
              aria-label="背景色"
              onClick={() => setPaletteOpen((v) => !v)}
              className="jimeng-node-toolbar-item flex h-8 items-center gap-1.5 whitespace-nowrap px-2 text-[13px] text-white"
            >
              <Square size={13} />
              背景色
            </button>
            {paletteOpen ? (
              <div
                className="absolute right-0 top-full z-[140] mt-2 flex items-center gap-1.5 rounded-xl px-2.5 py-2"
                style={{ background: "rgb(38,38,38)" }}
                role="menu"
                aria-label="背景色调色板"
              >
                {BG_COLORS.map(({ label, value }) => (
                  <button
                    key={label}
                    type="button"
                    role="menuitem"
                    aria-label={`背景色 ${label}`}
                    onClick={() => {
                      updateNodeData(id, { bgColor: value });
                      setPaletteOpen(false);
                    }}
                    className="flex size-5 items-center justify-center rounded-full"
                    style={{
                      background: value ?? "transparent",
                      border: value ? "none" : "1.5px solid rgba(255,255,255,0.5)",
                    }}
                  >
                    {value === null ? <span className="text-[10px] leading-none text-white/60">∅</span> : null}
                  </button>
                ))}
              </div>
            ) : null}
          </div>
          <button
            type="button"
            aria-label="展开文本面板"
            onClick={() => setPaletteOpen(false)}
            className="jimeng-node-toolbar-item flex size-8 items-center justify-center text-white"
          >
            <Maximize2 size={15} />
          </button>
          <button
            type="button"
            aria-label="下载"
            className="jimeng-node-toolbar-item flex size-8 items-center justify-center text-white"
          >
            <Download size={15} />
          </button>
        </div>
      </NodeToolbar>

      <div
        className="h-full w-full overflow-hidden rounded-lg p-4"
        style={{
          background:
            d.bgColor ??
            "linear-gradient(to right bottom, rgb(30,30,32), rgb(22,22,24))",
          boxShadow: nodeRingShadow(selected === true),
        }}
        onDoubleClick={(e) => {
          e.stopPropagation();
          setEditing(true);
        }}
      >
        {/* 批 241 SOURCE_FACT: 编辑态富文本工具条。
            批 816: 7 个按钮接上真行为（与上方 10 个快捷键共用 exec 这一套），
            与快捷键的实测对应见文件头。 */}
        {editing ? (
          <div
            className="absolute bottom-full left-1/2 z-[130] mb-2 flex -translate-x-1/2 items-center gap-0.5 rounded-xl bg-[#262626] p-1"
            role="toolbar"
            aria-label="文本格式"
            data-testid="text-format-toolbar"
          >
            <div className="relative">
              <button
                type="button"
                aria-label="Text style"
                aria-expanded={fontMenuOpen}
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => setFontMenuOpen((v) => !v)}
                // 批 817 SOURCE_FACT: 源站 Text style 48×32（唯一带 chevron、比其他宽 16）
                className="flex h-8 w-12 items-center justify-center gap-0.5 rounded-lg text-white/85 hover:bg-white/10"
              >
                <Type size={14} />
                <ChevronDown size={10} className="text-white/60" />
              </button>
              {/* 批 816: 字体菜单 = 面板承诺的 ⌘⌥0~3 四个块级样式
                  （源站实测 p ⇄ h1/h2/h3 双向可转，见文件头） */}
              {fontMenuOpen ? (
                <div
                  role="menu"
                  aria-label="字体"
                  data-testid="text-font-menu"
                  className="absolute bottom-full left-0 z-[140] mb-1 flex w-28 flex-col rounded-lg py-1"
                  style={{ background: "rgb(38,38,38)" }}
                >
                  {[
                    { label: "普通文本", tag: "p", cls: "text-[13px] font-normal" },
                    { label: "一级标题", tag: "h1", cls: "text-[16px] font-semibold" },
                    { label: "二级标题", tag: "h2", cls: "text-[15px] font-semibold" },
                    { label: "三级标题", tag: "h3", cls: "text-[14px] font-semibold" },
                  ].map(({ label, tag, cls }) => (
                    <button
                      key={label}
                      type="button"
                      role="menuitem"
                      aria-label={`字体 ${label}`}
                      onMouseDown={(e) => e.preventDefault()}
                      onClick={() => {
                        applyBlock(tag);
                        setFontMenuOpen(false);
                      }}
                      className={`px-3 py-1.5 text-left text-white/85 hover:bg-white/10 ${cls}`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
            {[
              { label: "无序列表", node: <List size={14} />, cmd: "insertUnorderedList" },
              { label: "有序列表", node: <ListOrdered size={14} />, cmd: "insertOrderedList" },
              { label: "加粗", node: <Bold size={14} />, cmd: "bold" },
              { label: "删除线", node: <Strikethrough size={14} />, cmd: "strikeThrough" },
              { label: "斜体", node: <Italic size={14} />, cmd: "italic" },
              { label: "下划线", node: <Underline size={14} />, cmd: "underline" },
            ].map(({ label, node: icon, cmd }) => (
              <button
                key={label}
                type="button"
                aria-label={label}
                data-testid={`text-fmt-${label}`}
                // mousedown 阻止默认：否则点按钮会先把编辑面的选区收掉
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => exec(cmd)}
                // 批 817 SOURCE_FACT: 源站这六个都是 32×32
                className="flex size-8 items-center justify-center rounded-lg text-white/85 hover:bg-white/10"
              >
                {icon}
              </button>
            ))}
            {/* 批 817 SOURCE_FACT: 源站第 8 个按钮 aria-label 是「全屏」（32×32），
                点开的面板标题是「全屏编辑」。批 816 留的 OPEN_QUESTION 816-a 就此关闭。 */}
            <button
              type="button"
              aria-label="全屏"
              data-testid="text-expand"
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => {
                // 批 817: 取当前行内编辑面的实时内容作为全屏面板的种子，
                // 再提交 —— 否则用户刚打的字还没落库，effect 读到的仍是旧值。
                const live = editorRef.current?.innerHTML ?? "";
                fsSeedRef.current = live || initialHtml;
                if (editing) commit();
                setFontMenuOpen(false);
                setFullscreen(true);
              }}
              // 批 817 SOURCE_FACT: 源站第 8 个按钮 32×32
              className="flex size-8 items-center justify-center rounded-lg text-white/85 hover:bg-white/10"
            >
              <Maximize2 size={12} />
            </button>
          </div>
        ) : null}
        {editing ? (
          /* 批 816 SOURCE_FACT: 源站编辑面是 contenteditable DIV（activeElement.ce=true），
             富文本结构活在 innerHTML 里，故不用 textarea。 */
          <div
            ref={editorRef}
            data-testid="text-rich-editor"
            contentEditable
            suppressContentEditableWarning
            onKeyDown={onEditorKeyDown}
            onBlur={(e) => {
              // 批 816: 点工具条按钮会把焦点移出编辑面。若不挡这一下，
              // onBlur→commit()→setEditing(false) 会把工具条整个卸掉，
              // 表现为「点第一个按钮有效、之后全找不到按钮」。
              const next = e.relatedTarget as HTMLElement | null;
              if (next?.closest?.('[data-testid="text-format-toolbar"]')) return;
              commit();
            }}
            className="h-full w-full overflow-y-auto text-[13px] leading-[22px] text-white outline-none [&_h1]:text-[16px] [&_h1]:font-semibold [&_h2]:text-[15px] [&_h2]:font-semibold [&_h3]:text-[14px] [&_h3]:font-semibold [&_p]:m-0 [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5"
          />
        ) : d.html ? (
          <div
            data-testid="text-rich-view"
            className="text-[13px] leading-[22px] text-white/85 [&_h1]:text-[16px] [&_h1]:font-semibold [&_h2]:text-[15px] [&_h2]:font-semibold [&_h3]:text-[14px] [&_h3]:font-semibold [&_p]:m-0 [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5"
            dangerouslySetInnerHTML={{ __html: d.html }}
          />
        ) : (
          <p
            className={`text-[13px] leading-[22px] whitespace-pre-wrap ${
              d.text ? "text-white/85" : "text-white/40"
            }`}
          >
            {d.text || "双击编辑文本"}
          </p>
        )}
      </div>

      <JimengConnectHandles
        nodeId={id}
        title={d.title}
        size={{ width: d.width, height: d.height }}
        selected={selected === true}
      />

      {/* 批 817 SOURCE_FACT: 点工具条「全屏」打开的面板，源站标题是「全屏编辑」
          （实测 126×42 的标签按钮 @[1340,406]），面板是带 1px 描边、圆角 8px 的
          浮层，正文在左上角。源站该面板**不是** contenteditable（点开后页面上
          已无 [contenteditable]）—— 但照抄一个只能看不能改的面板等于又造一个
          死入口（同 §21 ⌘0 那条判据：多一个能用的，好过一个源站式的死面板），
          故此处沿用同一套富文本编辑面与 10 个快捷键 (CLONE_DECISION)。
          源站面板右缘还有一个 ⊕ 圆形钮，作用未取证，不猜、不复刻。 */}
      {fullscreen ? (
        <div
          className="absolute left-full top-1/2 z-[200] ml-6 flex h-[324px] w-[326px] -translate-y-1/2 flex-col rounded-lg border border-white/25 bg-[rgb(20,20,22)]"
          role="dialog"
          aria-label="全屏编辑"
          data-testid="text-fullscreen"
        >
          <div className="flex h-11 shrink-0 items-center justify-between px-3">
            <span className="text-[13px] text-white/80">全屏编辑</span>
            <button
              type="button"
              aria-label="关闭全屏编辑"
              data-testid="text-fullscreen-close"
              onClick={() => setFullscreen(false)}
              className="flex size-7 items-center justify-center rounded-md text-white/60 hover:bg-white/10 hover:text-white"
            >
              <X size={14} />
            </button>
          </div>
          <div
            ref={fsRef}
            data-testid="text-fullscreen-editor"
            contentEditable
            suppressContentEditableWarning
            onKeyDown={onFsKeyDown}
            onBlur={(e) => {
              const el = fsRef.current;
              if (!el) return;
              const next = e.relatedTarget as HTMLElement | null;
              if (next?.closest?.('[data-testid="text-fullscreen"]')) return;
              updateNodeData(id, {
                html: normalizeRichHtml(el.innerHTML),
                text: (el.innerText || "").trim(),
              });
            }}
            className="min-h-0 flex-1 overflow-y-auto px-3 pb-3 text-[13px] leading-[22px] text-white/85 outline-none [&_h1]:text-[16px] [&_h1]:font-semibold [&_h2]:text-[15px] [&_h2]:font-semibold [&_h3]:text-[14px] [&_h3]:font-semibold [&_p]:m-0 [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5"
          />
        </div>
      ) : null}
    </div>
  );
}
