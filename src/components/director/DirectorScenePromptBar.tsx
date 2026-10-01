"use client";

import { useRef, useState } from "react";
import { ImagePlus, MoveUp } from "lucide-react";
import { cn } from "@/lib/utils";

// Batch 604（源站 2026-10-01 实测，1920x1150）——视口底部浮动条是**两段并列
// 胶囊**，不是一条扁条：
//
//   div.z-(--z-sticky) pointer-events-none absolute inset-x-0 bottom-0
//        flex flex-col items-center gap-1            1920x182 @(0,968) z=200
//     └ div.pointer-events-auto flex items-center gap-2   360x48 @(780,968)
//        └ div.nodrag nopan nowheel relative flex items-end gap-2
//           ├ nav.w-32 h-12 rounded-full …             128x48  ← DirectorViewport 那枚
//           └ div.shrink-0.transition-[width]           224x48  ← 本组件（prompt 胶囊）
//              └ div.grid grid-cols-[32px_142px_32px] p-2 min-h-12
//                 bg rgba(33,33,33,0.94) / border-white/10 / 三段 shadow
//
// 本组件逐字对齐外层网格胶囊：
//   `relative z-10 grid min-h-12 w-full border border-white/10
//    bg-[rgba(33,33,33,0.94)] p-2 text-white
//    shadow-[0_16px_24px_rgba(0,0,0,0.18),0_4px_8px_rgba(0,0,0,0.16),0_1px_1px_rgba(0,0,0,0.12)]`
//   列宽 `grid-cols-[32px_1fr_32px]`（源站中间列实测 142px，是 1fr 的解析值，
//   不是写死的定值——所以这里用 1fr 而非 142px）。
//
// 三格：col-1「上传图片」/ col-2 输入 / col-3「发送」，两个按钮都是
// **rounded-full**（与 DirectorViewport 那枚胶囊的 rounded-lg 按钮不同，
// 源站确实两段视觉语言不一致，照抄不修正）、图标 16px（size-4）。
//
// 源站 col-2 的可见输入本体实测是 1x1 的隐藏 input（未展开态），真实输入区
// 是 contenteditable(role=textbox, 14px)；clone 沿用自有的 <input> 实现。
//
// 不声称：源站「发送」的 Enter 提交语义、以及上传后是否真的发起云端生成，
// 都未取证（点它可能触发付费生成）。本组件的提交只在本地回显草稿。
export function DirectorScenePromptBar() {
  const [value, setValue] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [attachment, setAttachment] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const submit = () => {
    if (!value.trim()) return;
    setSubmitted(true);
    window.setTimeout(() => setSubmitted(false), 2000);
  };

  return (
    <div
      data-director-scene-prompt-bar
      // `h-12` 而非源站写的 `min-h-12`：源站这枚胶囊实测 224x48，可它自己的
      // 算术是 8(p-2) + 32(按钮) + 8 + 1 + 1(border) = 50——`min-h-12` 只设
      // 下限，内容照样把盒子撑到 50，而源站实测是 48（且 col-1 按钮实测落在
      // +9 处、底部留 7px，即确实被压过）。按「以实测为准」这里用 `h-12`
      // 把 48 钉死，让 32px 按钮上下各溢出 1px，与源站几何一致。
      className="pointer-events-auto relative z-10 grid h-12 w-full grid-cols-[32px_1fr_32px] items-center rounded-full border border-white/10 bg-[rgba(33,33,33,0.94)] p-2 text-white shadow-[0_16px_24px_rgba(0,0,0,0.18),0_4px_8px_rgba(0,0,0,0.16),0_1px_1px_rgba(0,0,0,0.12)]"
    >
      {/* 源站 col-1 可及名逐字是「上传图片」（aria-label），圆形、16px 图标、
          `text-white/60 hover:text-white`，无文字。点开本地文件选择器，选中后
          只把文件名回填进输入区（本地 mock，不发起任何云端请求）。 */}
      <button
        type="button"
        data-director-scene-prompt-upload
        aria-label="上传图片"
        title="上传图片"
        onClick={() => fileInputRef.current?.click()}
        className="hover:bg-white/8 col-start-1 row-start-1 flex size-8 shrink-0 items-center justify-center rounded-full text-white/60 transition-colors hover:text-white"
      >
        <ImagePlus size={16} aria-hidden="true" />
      </button>
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        tabIndex={-1}
        aria-hidden="true"
        data-director-scene-prompt-file
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (!file) return;
          setAttachment(file.name);
          setSubmitted(false);
        }}
        className="absolute h-px w-px min-w-0 overflow-hidden border-0 p-0 opacity-0"
      />

      <input
        data-director-scene-prompt-input
        value={value}
        onChange={(event) => { setValue(event.target.value); setSubmitted(false); }}
        onKeyDown={(event) => {
          if (event.key === "Enter") submit();
        }}
        // Batch 592（源站 2026-10-01 实测）：可及名逐字是「描述想搭建的
        // 场景」——clone 原写作「描述想要搭建的场景」，多了一个「要」。
        // 源站输入区本体是 contenteditable(role=textbox, 14px)，可见
        // 占位文案另作「描述您想搭建的场景」；此处沿用 clone 的 input
        // 实现（见 batch 592 记录的未取证项）。
        placeholder="描述想搭建的场景"
        aria-label="描述想搭建的场景"
        className={cn(
          "col-start-2 row-start-1 min-w-0 bg-transparent text-center text-xs text-[#e0e0e0] outline-none placeholder:text-[#777] transition-opacity",
          // 状态回显与输入同格叠放（grid 同 cell），胶囊高度因此恒为 48px。
          submitted && "opacity-0",
        )}
      />

      {/* Batch 592：提交钮的可及名/提示逐字为「发送」（源站实测 32×32、
          border-radius 9999px、空态底色 rgba(255,255,255,0.08)）；batch 604
          补齐源站的有值态 `bg-white text-[#171717] hover:bg-white/90`、
          16px 图标与 `ml-1`。 */}
      <button
        type="button"
        data-director-scene-prompt-submit
        aria-label="发送"
        title="发送"
        onClick={submit}
        disabled={!value.trim()}
        className="col-start-3 row-start-1 ml-1 flex size-8 shrink-0 items-center justify-center rounded-full bg-white text-[#171717] transition-colors hover:bg-white/90 disabled:bg-white/8 disabled:text-white/28"
      >
        <MoveUp size={16} aria-hidden="true" />
      </button>

      <span
        data-director-scene-prompt-status
        aria-live="polite"
        className={cn(
          // batch 604：状态文案改为与输入同格（col-2 / row-1）叠放，不再是
          // 一个浮在视口工具条之上的独立气泡——旧形态的 pointer-events-auto
          // 气泡在基线实测里正好盖住工具条按钮整条，吞掉点击。
          "pointer-events-none col-start-2 row-start-1 self-center truncate text-center text-[11px] text-[#9ddbb9] transition-opacity",
          submitted ? "opacity-100" : "opacity-0",
        )}
      >
        {attachment ? `已附上本地图片：${attachment}` : "场景描述已记录（本地草稿）"}
      </span>
    </div>
  );
}
