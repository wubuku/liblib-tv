"use client";

import { useState } from "react";
import { ArrowUp, ChevronDown, Maximize2 } from "lucide-react";
import { NodeToolbar, Position } from "@xyflow/react";

/**
 * 音频节点选中态下方弹出的音频生成面板 (Batch 239)。
 *
 * 证据 (SOURCE_FACT, 236-source-audio-node.png): 面板 680×~176，
 * 占位「请输入你想生成的说话内容」+ 右上展开钮；底行三选择器:
 * 音频生成∨ / Seed TTS∨ / 直爽女大∨ (12-13px 白字) + 右侧 ✦1 +
 * 灰色圆形发送钮 (禁用样式)。
 * 批 245 SOURCE_FACT: 「音频生成」下拉两项 音频生成/音乐生成 (192×76，
 * 36px 行)。批 248 SOURCE_FACT: 「Seed TTS」下拉为两行式菜单项——
 * 标题 Seed TTS + 描述「上百个预设音色，让你玩转人声配音」(392×72)。
 * 批 250 SOURCE_FACT: 「直爽女大」(音色) 下拉——「全音色」头 + 性别/
 * 年龄/语言/声音特点 4 筛选 + 3 列音色网格 (直爽女大✓/低音炮/英气飒姐/
 * 阳光小男孩/纯净女声/温柔软妹/黛玉/明媚女声/含蓄女声/紫薇/猴哥/
 * 蜡笔小新/八戒Pro/动漫海绵/聪慧群仔，每项 ▶+名称，选中带勾)。
 */
/** 批 250 SOURCE_FACT: 音色网格 3 列 × 5+ 行 (可滚动，已采样可见 15 项) */
const VOICES = [
  "直爽女大",
  "低音炮",
  "英气飒姐",
  "阳光小男孩",
  "纯净女声",
  "温柔软妹",
  "黛玉",
  "明媚女声",
  "含蓄女声",
  "紫薇",
  "猴哥",
  "蜡笔小新",
  "八戒Pro",
  "动漫海绵",
  "聪慧群仔",
];

export function JimengAudioGenPanel({ visible }: { visible: boolean }) {
  const [text, setText] = useState("");
  const canSend = text.trim().length > 0;
  const [genKind, setGenKind] = useState("音频生成");
  const [genOpen, setGenOpen] = useState(false);
  const [ttsOpen, setTtsOpen] = useState(false);
  const [voiceOpen, setVoiceOpen] = useState(false);
  const [voice, setVoice] = useState("直爽女大");
  // 批 254/255/257 SOURCE_FACT: 筛选下拉选项 (均已在源站采样)
  const FILTERS: { label: string; options: string[] }[] = [
    { label: "性别", options: ["全部 性别", "男", "女"] },
    { label: "年龄", options: ["全部 年龄", "幼儿", "少年", "青年", "中年", "老年"] },
    { label: "语言", options: ["全部 语言", "普通话", "中文方言", "英文"] },
    {
      label: "声音特点",
      options: ["全部 声音特点", "适合旁白", "情景演绎", "多情感", "适合口播", "知名 IP"],
    },
  ];
  const [filterSel, setFilterSel] = useState<Record<string, string | null>>({});

  return (
    <NodeToolbar isVisible={visible} position={Position.Bottom} offset={16}>
      <div className="relative w-[680px]">
        <button
          type="button"
          aria-label="展开面板"
          className="absolute -top-1.5 right-0 z-[2] flex size-10 items-center justify-center"
        >
          <span className="flex size-6 items-center justify-center rounded-full text-white/60">
            <Maximize2 size={13} />
          </span>
        </button>

        <form
          className="flex h-[176px] w-full flex-col justify-between rounded-[20px] bg-[#202020] p-4"
          onSubmit={(e) => e.preventDefault()}
        >
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="请输入你想生成的说话内容"
            rows={2}
            className="w-full resize-none bg-transparent text-[13px] leading-[22px] text-white outline-none placeholder:text-white/35"
          />

          <div className="flex h-8 w-full items-center justify-between">
            <div className="flex min-w-0 items-center gap-1">
              {/* 批 245 SOURCE_FACT: 音频生成下拉两项 */}
              <div className="relative">
                <button
                  type="button"
                  aria-label={`创作类型: ${genKind}`}
                  onClick={() => setGenOpen((v) => !v)}
                  className="flex h-8 items-center gap-1 whitespace-nowrap rounded-lg px-2 text-[12px] text-white/90 hover:bg-white/[0.08]"
                >
                  {genKind}
                  <ChevronDown size={12} className="text-white/60" />
                </button>
                {genOpen ? (
                  <div
                    className="absolute bottom-[calc(100%+8px)] left-0 z-[140] w-[192px] rounded-xl p-1.5"
                    style={{ background: "rgb(38,38,38)" }}
                    role="listbox"
                    aria-label="生成类型"
                  >
                    {["音频生成", "音乐生成"].map((opt) => (
                      <button
                        key={opt}
                        type="button"
                        role="option"
                        aria-selected={genKind === opt}
                        onClick={() => {
                          setGenKind(opt);
                          setGenOpen(false);
                        }}
                        className={`flex h-9 w-full items-center rounded-lg px-2.5 text-[13px] ${
                          genKind === opt ? "bg-white/[0.10] text-white" : "text-white/85 hover:bg-white/10"
                        }`}
                      >
                        {opt}
                      </button>
                    ))}
                  </div>
                ) : null}
              </div>
              <div className="relative">
                <button
                  type="button"
                  aria-label="选择模型: Seed TTS"
                  onClick={() => setTtsOpen((v) => !v)}
                  className="flex h-8 items-center gap-1 whitespace-nowrap rounded-lg px-2 text-[12px] text-white/90 hover:bg-white/[0.08]"
                >
                  Seed TTS
                  <ChevronDown size={12} className="text-white/60" />
                </button>
                {ttsOpen ? (
                  <div
                    className="absolute bottom-[calc(100%+8px)] left-0 z-[140] w-[392px] rounded-xl p-1.5"
                    style={{ background: "rgb(38,38,38)" }}
                    role="listbox"
                    aria-label="音色模型"
                  >
                    {/* 批 248 SOURCE_FACT: 两行式菜单项 标题+描述 */}
                    <button
                      type="button"
                      role="option"
                      aria-selected
                      onClick={() => setTtsOpen(false)}
                      className="flex w-full flex-col items-start gap-0.5 rounded-lg px-2.5 py-2 text-left hover:bg-white/10"
                    >
                      <span className="text-[13px] font-medium text-white">Seed TTS</span>
                      <span className="text-[12px] leading-4 text-white/45">
                        上百个预设音色，让你玩转人声配音
                      </span>
                    </button>
                  </div>
                ) : null}
              </div>
              <div className="relative">
                <button
                  type="button"
                  aria-label={`音色: ${voice}`}
                  onClick={() => setVoiceOpen((v) => !v)}
                  className="flex h-8 items-center gap-1 whitespace-nowrap rounded-lg px-2 text-[12px] text-white/90 hover:bg-white/[0.08]"
                >
                  {voice}
                  <ChevronDown size={12} className="text-white/60" />
                </button>
                {voiceOpen ? (
                  <div
                    className="absolute bottom-[calc(100%+8px)] left-0 z-[140] w-[700px] rounded-xl p-3"
                    style={{ background: "rgb(38,38,38)" }}
                    role="listbox"
                    aria-label="全音色"
                  >
                    <p className="pb-2 text-[13px] text-white/80">全音色</p>
                    <div className="flex gap-1.5 pb-2">
                      {FILTERS.map(({ label, options }) => (
                        <div key={label} className="relative">
                          <button
                            type="button"
                            onClick={() =>
                              setFilterSel((m) => ({
                                ...m,
                                [label]: m[label] === undefined ? null : m[label],
                              }))
                            }
                            className="flex h-7 items-center gap-1 rounded-md bg-white/[0.06] px-2 text-[12px] text-white/70"
                          >
                            {filterSel[label] ?? label}
                            <ChevronDown size={10} className="text-white/50" />
                          </button>
                          {options ? (
                            <div
                              className="absolute bottom-[calc(100%+6px)] left-0 z-[150] w-[150px] rounded-xl p-1.5"
                              style={{ background: "rgb(38,38,38)" }}
                              role="listbox"
                              aria-label={`筛选 ${label}`}
                            >
                              {options.map((opt) => (
                                <button
                                  key={opt}
                                  type="button"
                                  role="option"
                                  aria-selected={(filterSel[label] ?? label) === opt}
                                  onClick={() =>
                                    setFilterSel((m) => ({
                                      ...m,
                                      [label]: opt.startsWith("全部") ? label : opt,
                                    }))
                                  }
                                  className={`flex h-9 w-full items-center rounded-lg px-2.5 text-[13px] ${
                                    (filterSel[label] ?? label) === opt
                                      ? "bg-white/[0.10] text-white"
                                      : "text-white/85 hover:bg-white/10"
                                  }`}
                                >
                                  {opt}
                                </button>
                              ))}
                            </div>
                          ) : null}
                        </div>
                      ))}
                    </div>
                    <div className="grid grid-cols-3 gap-1">
                      {VOICES.map((v) => (
                        <button
                          key={v}
                          type="button"
                          role="option"
                          aria-selected={voice === v}
                          onClick={() => {
                            setVoice(v);
                            setVoiceOpen(false);
                          }}
                          className={`flex h-9 items-center gap-2 rounded-lg px-2 text-[13px] ${
                            voice === v
                              ? "bg-white/[0.12] text-white"
                              : "text-white/85 hover:bg-white/[0.06]"
                          }`}
                        >
                          <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden className="shrink-0 text-white/60">
                            <path d="M4 2v10l7-5Z" fill="currentColor" />
                          </svg>
                          {v}
                          {voice === v ? (
                            <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden className="ml-auto shrink-0 text-white/80">
                              <path d="M2 6.5 4.8 9 10 3.5" stroke="currentColor" strokeWidth="1.5" fill="none" />
                            </svg>
                          ) : null}
                        </button>
                      ))}
                    </div>
                  </div>
                ) : null}
              </div>
            </div>

            <div className="flex h-8 shrink-0 items-center gap-2">
              <span className="inline-flex items-center gap-1 text-dreamina-number text-[12px] font-medium text-white/60">
                ✦ 1
              </span>
              <button
                type="button"
                aria-label="生成语音"
                onClick={() => {
                  if (canSend) {
                    // mock: 音频生成流程未接入 (BLOCKED_BY_FIXTURE)
                  }
                }}
                className={`flex size-8 items-center justify-center rounded-full ${
                  canSend
                    ? "bg-white text-black hover:bg-white/90"
                    : "bg-white/[0.16] text-white/20"
                }`}
              >
                <ArrowUp size={15} />
              </button>
            </div>
          </div>
        </form>
      </div>
    </NodeToolbar>
  );
}
