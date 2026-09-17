"use client";

import { useState } from "react";
import { ArrowUp, ChevronDown, Maximize2 } from "lucide-react";
import { NodeToolbar, Position } from "@xyflow/react";

/**
 * 音频节点选中态下方弹出的音频生成面板 (Batch 239；批 245/250/286/287/293/294 演进)。
 *
 * 证据 (SOURCE_FACT, 236-source-audio-node.png 及后续采样):
 * - 面板 680×196 (批 293 演进，原 176)，占位「请输入你想生成的说话内容」
 *   + 右上展开钮
 * - 底行三选择器 (批 277 aria: 创作类型:/选择模型:/音色:):
 *   音频生成∨ (批 245: 音频生成/音乐生成 两项) ·
 *   Seed TTS∨ (批 248: 两行式菜单项 Seed TTS + 上百个预设音色描述) ·
 *   直爽女大∨ (批 250/278/282: 全音色网格 + 四筛选，性别真实过滤)
 * - 批 294: 切换 音乐生成 后选择器整组变化——模型位 SeedMusic 1.0
 *   Preview、第三位变 120s 时长
 * - 右侧「Current price 1.1」价格签 (批 293 演进，原 ✦1，70px 裁切) +
 *   灰色圆形发送钮 (空提示 aria「请输入提示词」)
 * mock: 生成流程未接入 (BLOCKED_BY_FIXTURE)。
 */

/** 批 278/282/285 SOURCE_FACT: 音色清单 男 18 / 女 18；批 285: 英文 8；
 *  批 286: 适合口播 维度 8 音色；批 287: 中文方言 7 新音色 (磁性男主播双属)。
 *  完整目录可能更长 (CLONE_DECISION 截止于此采样)。 */
const VOICES: {
  name: string;
  gender: "男" | "女";
  lang?: "英文" | "中文方言";
}[] = [
  { name: "Bill", gender: "男", lang: "英文" },
  { name: "Sarah", gender: "女", lang: "英文" },
  { name: "Liam", gender: "男", lang: "英文" },
  { name: "George", gender: "男", lang: "英文" },
  { name: "Lily", gender: "女", lang: "英文" },
  { name: "Callum", gender: "男", lang: "英文" },
  { name: "Chris", gender: "男", lang: "英文" },
  { name: "Daniel", gender: "男", lang: "英文" },
  { name: "直爽女大", gender: "女" },
  { name: "英气飒姐", gender: "女" },
  { name: "纯净女声", gender: "女" },
  { name: "温柔软妹", gender: "女" },
  { name: "黛玉", gender: "女" },
  { name: "明媚女声", gender: "女" },
  { name: "含蓄女声", gender: "女" },
  { name: "紫薇", gender: "女" },
  { name: "糯音女孩", gender: "女" },
  { name: "TVB女声Pro", gender: "女" },
  { name: "优雅女声", gender: "女" },
  { name: "狐媚姐姐", gender: "女" },
  { name: "将门女将", gender: "女" },
  { name: "成熟御姐", gender: "女" },
  { name: "灵动甜妹", gender: "女" },
  { name: "慈祥奶奶", gender: "女" },
  { name: "妩媚熟女", gender: "女" },
  { name: "正气女声", gender: "女" },
  { name: "灵动女声", gender: "女" },
  { name: "温柔女声", gender: "女" },
  { name: "知性熟女", gender: "女" },
  { name: "Vlog配音", gender: "女" },
  { name: "活泼女声", gender: "女" },
  { name: "清醒语录", gender: "女" },
  { name: "清晰语录", gender: "女" },
  { name: "低音炮", gender: "男" },
  { name: "阳光小男孩", gender: "男" },
  { name: "猴哥", gender: "男" },
  { name: "蜡笔小新", gender: "男" },
  { name: "八戒Pro", gender: "男" },
  { name: "动漫海绵", gender: "男" },
  { name: "聪慧胖仔", gender: "男" },
  { name: "憨萌福娃", gender: "男" },
  { name: "爽快小哥", gender: "男" },
  { name: "低沉大叔", gender: "男" },
  { name: "飒爽少侠", gender: "男" },
  { name: "权威精英男", gender: "男" },
  { name: "呆萌小男孩", gender: "男" },
  { name: "威严老爷子", gender: "男" },
  { name: "深夜博客", gender: "男" },
  { name: "成熟总裁", gender: "男" },
  { name: "皇上", gender: "男" },
  { name: "老实小哥", gender: "男" },
  { name: "磁性男主播", gender: "男" },
  { name: "真人播客男", gender: "男", lang: "中文方言" },
  { name: "台湾腔甜妹", gender: "女", lang: "中文方言" },
  { name: "天津小哥", gender: "男", lang: "中文方言" },
  { name: "台湾男生", gender: "男", lang: "中文方言" },
  { name: "春日部姐姐", gender: "女", lang: "中文方言" },
  { name: "蜡笔小妮", gender: "女", lang: "中文方言" },
  { name: "桃花庵主", gender: "男", lang: "中文方言" },
];

/** 批 254/255/257 SOURCE_FACT: 筛选下拉选项 (均已在源站采样) */
const FILTERS: { label: string; options: string[] }[] = [
  { label: "性别", options: ["全部 性别", "男", "女"] },
  { label: "年龄", options: ["全部 年龄", "幼儿", "少年", "青年", "中年", "老年"] },
  { label: "语言", options: ["全部 语言", "普通话", "中文方言", "英文"] },
  {
    label: "声音特点",
    options: ["全部 声音特点", "适合旁白", "情景演绎", "多情感", "适合口播", "知名 IP"],
  },
];

export function JimengAudioGenPanel({ visible }: { visible: boolean }) {
  const [text, setText] = useState("");
  const canSend = text.trim().length > 0;
  const [genKind, setGenKind] = useState("音频生成");
  const [genOpen, setGenOpen] = useState(false);
  const [ttsOpen, setTtsOpen] = useState(false);
  const [voiceOpen, setVoiceOpen] = useState(false);
  const [voice, setVoice] = useState("直爽女大");
  // 批 254/255/257: 筛选下拉选项与选中态；批 282: 性别筛选真实过滤网格
  const [filterSel, setFilterSel] = useState<Record<string, string | null>>({});

  const visibleVoices = VOICES.filter(
    (v) =>
      (!filterSel["性别"] ||
        filterSel["性别"] === "性别" ||
        v.gender === filterSel["性别"]) &&
      (!filterSel["语言"] ||
        filterSel["语言"] === "语言" ||
        (filterSel["语言"] === "英文"
          ? v.lang === "英文"
          : filterSel["语言"] === "中文方言"
            ? v.lang === "中文方言"
            : v.lang !== "英文" && v.lang !== "中文方言")),
  );

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
          className="flex h-[196px] w-full flex-col justify-between rounded-[20px] bg-[#202020] p-4"
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

              {genKind === "音乐生成" ? (
                <>
                  {/* 批 294 SOURCE_FACT: 音乐生成态 模型位 SeedMusic 1.0 Preview */}
                  <button
                    type="button"
                    aria-label="选择模型: SeedMusic 1.0 Preview"
                    className="flex h-8 items-center gap-1 whitespace-nowrap rounded-lg px-2 text-[12px] text-white/90 hover:bg-white/[0.08]"
                  >
                    SeedMusic 1.0 Preview
                    <ChevronDown size={12} className="text-white/60" />
                  </button>
                  {/* 批 294 SOURCE_FACT: 音乐生成态 第三位变 120s 时长 */}
                  <button
                    type="button"
                    aria-label="选择时长: 120s"
                    className="flex h-8 items-center gap-1 whitespace-nowrap rounded-lg px-2 text-[12px] text-white/90 hover:bg-white/[0.08]"
                  >
                    120s
                    <ChevronDown size={12} className="text-white/60" />
                  </button>
                </>
              ) : (
                <>
                  {/* 批 248 SOURCE_FACT: Seed TTS 两行式下拉 */}
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
                  {/* 批 250/278/282 SOURCE_FACT: 音色下拉 (全音色网格 + 四筛选) */}
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
                          {visibleVoices.map(({ name: v }) => (
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
                </>
              )}
            </div>

            <div className="flex h-8 shrink-0 items-center gap-2">
              {/* 批 293 SOURCE_FACT: 价格区演进为「Current price 1.1」
                  (70px 裁切容器，同批 206 生成面板形态) */}
              <span className="flex h-8 w-[70px] items-center overflow-hidden whitespace-nowrap text-[12px] text-white/[0.69]">
                <span className="shrink-0 text-white/[0.6]">Current price</span>
                <span className="shrink-0">1.1</span>
              </span>
              <button
                type="button"
                aria-label={canSend ? "生成语音" : "请输入提示词"}
                title={canSend ? undefined : "请输入提示词"}
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
