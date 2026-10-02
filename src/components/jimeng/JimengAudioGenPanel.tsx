"use client";

import { useRef, useState } from "react";
import {
  ArrowUp,
  ChevronDown,
  Maximize2,
  Plus,
  Quote,
  Sparkle,
} from "lucide-react";
import { NodeToolbar, Position } from "@xyflow/react";
import { useArrowKeys, useTakeFocusAtOpen } from "@/components/jimeng/jimengMenuChrome";

/**
 * 音频节点选中态下方弹出的音频生成面板 (Batch 239；批 245/250/286/287/293/294 演进)。
 *
 * 证据 (SOURCE_FACT, 236-source-audio-node.png 及后续采样):
 * - 面板 680 宽，高度/占位随模式适配 (批 301 SOURCE_FACT):
 *   音频生成 196 /「请输入你想生成的说话内容」；
 *   音乐生成 144 /「请输入你想生成的音乐」
 *   + 右上展开钮
 * - 底行三选择器 (批 277 aria: 创作类型:/选择模型:/音色:):
 *   音频生成∨ (批 245: 音频生成/音乐生成 两项) ·
 *   Seed TTS∨ (批 248: 两行式菜单项 Seed TTS + 上百个预设音色描述) ·
 *   直爽女大∨ (批 250/278/282: 全音色网格 + 四筛选，性别真实过滤)
 * - 批 294: 切换 音乐生成 后选择器整组变化——模型位 SeedMusic 1.0
 *   Preview、第三位变时长触发钮
 * - 批 367 SOURCE_FACT (367e/367f/367-duration-slider.png): 时长控件实为
 *   连续自由滑杆弹出层——标题「选择音乐生成时长」+ 0-360s 连续滑轨
 *   (thumb 4×16 白色竖条, 刻度 0/60/120/180/240/300/360 10px white/35
 *   在轨下方, 首标签左对齐轨起点末标签右对齐轨终点) + 右侧数值输入框
 *   (数字 + 灰 s 后缀)。点轨取任意秒数 (53/108/165/224/286/341 实测)，
 *   弹出层在多次点选间保持打开；触发钮呈胶囊 bg，打开时 chevron 翻上。
 *   批 367f: 时长跨节点持久——新插入节点继承上次设定 (341s 实测)，
 *   非固定 120s 默认。
 * - 右侧价格签 (批 293 70px 裁切 → 批 368 演进为紧凑态「✦ + 整数」：
 *   音乐 6 / 音频 1，精确值 6.6/1.1 保留在 1px 裁切 span 与 title) +
 *   灰色圆形发送钮 (空提示 aria「请输入提示词」)。批 297: 值随模式
 *   变动；批 367e: 与时长无关 (53s-341s 恒 6.6)。批 370 SOURCE_FACT:
 *   发送钮空态 bg rgba(255,255,255,0.16) → 非空输入态 rgb(250,250,250)
 *   白色激活，「生成」裁切叶两态均保持折叠。
 * mock: 生成流程未接入 (BLOCKED_BY_FIXTURE)。
 */

/** 批 367f SOURCE_FACT: 音乐时长跨节点持久 (模块级，非 per-node 状态) */
let persistedMusicDuration = 120;

/** 批 367 SOURCE_FACT: 滑杆刻度 (轨上刻度点 + 轨下标签行共用) */
const DURATION_TICKS = [0, 60, 120, 180, 240, 300, 360];

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
  /* 批 835 SOURCE_FACT：音频面板里这 6 个下拉在源站上**互斥**（开下一个 ⇒
     上一个自动关闭）。复刻此前是 6 个独立 boolean，于是能同时开着：
     实测「音乐模型」（392 宽）会盖住「生成模式」（192 宽）里的选项，
     用户点「音频生成」点不动 —— 批 832 的 verifier 就是在这一步 30s 超时的。
     收成一个 state，顺带把 6 条声明缩成 1 条。 */
  const [open, setOpen] = useState<"gen" | "music" | "dur" | "tts" | "dub" | "voice" | null>(
    null,
  );
  /* 批 851 SOURCE_FACT（探针 851b，源站登录态实测，视口 1512×1200）：
     `audio-voice-model-listbox`（音色模型）与 `audio-gen-mode-listbox`
     （音频生成模式）**开层即把焦点移进层里**（落在层内 option 的 BUTTON 上），
     **不困 Tab**（第 1 次就逃出、层还在）、**Esc 后焦点不回触发器**
     （落到节点 / 顶栏控件 —— 源站自己的 a11y 失手，**照抄不修**）。

     ⚠️ 853 更正：这句话原先写「另外三个源站**至今没取到样**」，853b 取到样了 ——
     `audio-music-model-listbox` 与 `audio-all-voices-listbox` 两层都已进源站基线表
     （见审计 `SOURCE_BASELINE`），`audio-music-duration-listbox` 则是**源站事实**：
     音乐分支**压根没有**时长下拉（切过去后 `选择时长` 触发器计数 0，而同一时刻
     `选择模型` 计数 1）。**源站没做的，不许在复刻里假称可用**。
     剩下两层**刻意不接** `useTakeFocusAtOpen`：音乐时长（源站无此入口）、
     全音色（源站实测**开层不接管焦点** —— 焦点自始至终停在触发器上，
     复刻同样不接管，行为一致）。*/
  const voiceBoxRef = useRef<HTMLDivElement>(null);
  const dubBoxRef = useRef<HTMLDivElement>(null);
  const musicBoxRef = useRef<HTMLDivElement>(null);
  useTakeFocusAtOpen(voiceBoxRef, open === "tts");
  useTakeFocusAtOpen(dubBoxRef, open === "dub");
  /* 批 853 SOURCE_FACT（探针 853b 实测，登录态视口 1512×1200）：音乐模型层
     **开层即接管焦点**（焦点落在层内 `SeedMusic 1.0 Preview` 那个 BUTTON 上）、
     **不困 Tab**（第 1 次就逃出、层还在）、**Esc 后焦点不回触发器**（落到
     `BUTTON/生成`）—— 与音色模型/生成模式两层**完全同款**。
     ⚠️ 但方向键 `moved=False`，原因是**这一层只有 1 个选项**（实测 4 次
     ArrowDown 全停在同一项）⇒ 无处可去，**不是**「源站方向键坏了」。
     所以**只接接管焦点，刻意不接 `useArrowKeys`**：接了也只会让 1 个元素
     环绕到自己 —— 接一个源站没有的行为，比不接更坏。 */
  useTakeFocusAtOpen(musicBoxRef, open === "music");
  /* 批 852 SOURCE_FACT（探针 852 实测）：音色模型**方向键在层内移动**（2 项，
     moved=True）；音频生成模式**只有 1 个选项**，方向键无处可去（moved=False）。
     两层都接上 —— 后者接了也不会动（只有一个元素，环绕到自己），行为与源站
     一致；接上是为了「以后加了选项自动就有方向键」，而不是留个想起来才补的坑。 */
  useArrowKeys(voiceBoxRef, open === "tts");
  useArrowKeys(dubBoxRef, open === "dub");
  const [text, setText] = useState("");
  const canSend = text.trim().length > 0;
  const [genKind, setGenKind] = useState("音频生成");
  // 批 487 SOURCE_FACT: 全能配音下拉 192×36 单选项
  // 批 367 SOURCE_FACT: 时长连续滑杆弹出层 (0-360s 自由值)
  const [duration, setDurationState] = useState(persistedMusicDuration);
  const [durDraft, setDurDraft] = useState<string | null>(null);
  const trackRef = useRef<HTMLDivElement>(null);
  const draggingRef = useRef(false);
  const setDuration = (s: number) => {
    const clamped = Math.min(360, Math.max(0, Math.round(s)));
    persistedMusicDuration = clamped;
    setDurationState(clamped);
  };
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
          className="relative flex w-full flex-col justify-between rounded-[20px] bg-[#202020] p-4"
          style={{
            // 批 485 SOURCE_FACT: 音频生成 204 (SeedAudio 1.0 改版)
            height: genKind === "音乐生成" ? 144 : 204,
          }}
          onSubmit={(e) => e.preventDefault()}
        >
          {/* 批 304 SOURCE_FACT: 源站输入为 contenteditable (占位以真实
              元素渲染)——clone 以叠加层占位近似，textarea 保持可用 */}
          {/* 批 485 SOURCE_FACT: 添加参考 48×48 (音频生成态左上) */}
          {genKind === "音频生成" ? (
            <button
              type="button"
              aria-label="添加参考"
              className="mb-2 flex size-12 items-center justify-center rounded-xl bg-white/[0.06] text-white/80 hover:bg-white/10"
            >
              <Plus size={20} />
            </button>
          ) : null}
          {!canSend ? (
            <div
              className={`pointer-events-none absolute inset-x-4 flex items-start text-[13px] leading-[22px] text-white/35 ${
                genKind === "音频生成" ? "top-[72px]" : "top-4"
              }`}
            >
              {genKind === "音乐生成"
                ? "请输入你想生成的音乐"
                : "输入台词并描述声音，可上传参考音频，通过 @ 引用多个音色，使用时间戳编排人声、音效与配乐。"}
            </div>
          ) : null}
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            aria-label="音频生成提示词"
            rows={2}
            className="w-full resize-none bg-transparent text-[13px] leading-[22px] text-white outline-none"
          />

          <div className="flex h-8 w-full items-center justify-between">
            <div className="flex min-w-0 items-center gap-1">
              {/* 批 245 SOURCE_FACT: 音频生成下拉两项 */}
              <div className="relative">
                <button
                  type="button"
                  aria-label={`创作类型: ${genKind}`}
                  onClick={() => setOpen((v) => (v === "gen" ? null : "gen"))}
                  className="flex h-8 items-center gap-1 whitespace-nowrap rounded-lg px-2 text-[12px] text-white/90 hover:bg-white/[0.08]"
                >
                  {genKind}
                  <ChevronDown size={12} className="text-white/60" />
                </button>
                {open === "gen" ? (
                  <div
                    className="absolute bottom-[calc(100%+8px)] left-0 z-[140] w-[192px] rounded-xl p-1.5"
                    style={{ background: "rgb(38,38,38)" }}
                    role="listbox"
                    aria-label="生成类型"
                    // 批 832：只补锚点，不动名字 —— 名字是源站的，加了就成了「复刻自有」
                    data-testid="audio-gen-type-listbox"
                  >
                    {["音频生成", "音乐生成"].map((opt) => (
                      <button
                        key={opt}
                        type="button"
                        role="option"
                        aria-selected={genKind === opt}
                        onClick={() => {
                          setGenKind(opt);
                          setOpen(null);
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
                  {/* 批 294/295 SOURCE_FACT: 模型位 SeedMusic 两行式下拉 */}
                  <div className="relative">
                    <button
                      type="button"
                      aria-label="选择模型: SeedMusic 1.0 Preview"
                      onClick={() => setOpen((v) => (v === "music" ? null : "music"))}
                      className="flex h-8 items-center gap-1 whitespace-nowrap rounded-lg px-2 text-[12px] text-white/90 hover:bg-white/[0.08]"
                    >
                      SeedMusic 1.0 Preview
                      <ChevronDown size={12} className="text-white/60" />
                    </button>
                    {open === "music" ? (
                      <div
                        ref={musicBoxRef}
                        className="absolute bottom-[calc(100%+8px)] left-0 z-[140] w-[392px] rounded-xl p-1.5"
                        style={{ background: "rgb(38,38,38)" }}
                        role="listbox"
                        aria-label="音乐模型"
                        // 批 832：只补锚点，不动名字 —— 名字是源站的，加了就成了「复刻自有」
                        data-testid="audio-music-model-listbox"
                      >
                        <button
                          type="button"
                          role="option"
                          aria-selected
                          onClick={() => setOpen(null)}
                          className="flex w-full flex-col items-start gap-0.5 rounded-lg px-2.5 py-2 text-left hover:bg-white/10"
                        >
                          <span className="text-[13px] font-medium text-white">
                            SeedMusic 1.0 Preview
                          </span>
                          <span className="text-[12px] leading-4 text-white/45">
                            细腻风格控制与多语种演唱，人声表现更自然
                          </span>
                        </button>
                      </div>
                    ) : null}
                  </div>
                  {/* 批 367 SOURCE_FACT: 时长触发钮 (胶囊 bg，打开时 chevron 翻上) */}
                  <div className="relative">
                    <button
                      type="button"
                      aria-label={`选择时长: ${duration}s`}
                      onClick={() => setOpen((v) => (v === "dur" ? null : "dur"))}
                      className={`flex h-8 items-center gap-1 whitespace-nowrap rounded-lg px-2 text-[12px] text-white/90 hover:bg-white/[0.08] ${
                        open === "dur" ? "bg-white/[0.08]" : ""
                      }`}
                    >
                      {duration}s
                      <ChevronDown
                        size={12}
                        className={`text-white/60 transition-transform ${
                          open === "dur" ? "rotate-180" : ""
                        }`}
                      />
                    </button>
                    {open === "dur" ? (
                      <div
                        className="absolute bottom-[calc(100%+8px)] left-0 z-[140] w-[368px] rounded-xl p-3"
                        style={{ background: "rgb(38,38,38)" }}
                        role="listbox"
                        aria-label="音乐时长"
                        // 批 832：只补锚点，不动名字 —— 名字是源站的，加了就成了「复刻自有」
                        data-testid="audio-music-duration-listbox"
                      >
                        <p className="pb-2 text-[12px] text-white/45">
                          选择音乐生成时长
                        </p>
                        <div className="flex items-center gap-3">
                          <div className="min-w-0 flex-1">
                            <div
                              ref={trackRef}
                              className="relative h-4 cursor-pointer"
                              style={{ touchAction: "none" }}
                              onPointerDown={(e) => {
                                draggingRef.current = true;
                                e.currentTarget.setPointerCapture(e.pointerId);
                                const r =
                                  e.currentTarget.getBoundingClientRect();
                                setDuration(
                                  ((e.clientX - r.left) / r.width) * 360,
                                );
                              }}
                              onPointerMove={(e) => {
                                if (!draggingRef.current) return;
                                const r =
                                  e.currentTarget.getBoundingClientRect();
                                setDuration(
                                  ((e.clientX - r.left) / r.width) * 360,
                                );
                              }}
                              onPointerUp={(e) => {
                                draggingRef.current = false;
                                e.currentTarget.releasePointerCapture(
                                  e.pointerId,
                                );
                              }}
                            >
                              <span className="absolute inset-x-0 top-1/2 h-1 -translate-y-1/2 rounded-full bg-white/[0.14]" />
                              {DURATION_TICKS.map((s) => (
                                <span
                                  key={s}
                                  className="absolute top-1/2 h-1 w-px -translate-y-1/2 bg-white/25"
                                  style={{ left: `${(s / 360) * 100}%` }}
                                />
                              ))}
                              <span
                                className="absolute left-0 top-1/2 h-1 -translate-y-1/2 rounded-full bg-white/40"
                                style={{ width: `${(duration / 360) * 100}%` }}
                              />
                              <span
                                role="slider"
                                aria-valuenow={duration}
                                className="absolute top-1/2 h-4 w-1 -translate-x-1/2 -translate-y-1/2 rounded-[11px] border border-white/40 bg-white"
                                style={{ left: `${(duration / 360) * 100}%` }}
                              />
                            </div>
                            <div className="flex justify-between pt-1 text-[10px] leading-[18px] text-white/35">
                              {DURATION_TICKS.map((s) => (
                                <span key={s}>{s}</span>
                              ))}
                            </div>
                          </div>
                          {/* 批 367 SOURCE_FACT: 数值输入框 (数字 + 灰 s 后缀) */}
                          <div className="flex h-9 w-[90px] shrink-0 items-center gap-1 rounded-lg bg-white/[0.06] px-2.5">
                            <input
                              value={durDraft ?? String(duration)}
                              inputMode="numeric"
                              aria-label="音乐时长秒数"
                              onChange={(e) =>
                                setDurDraft(
                                  e.target.value.replace(/[^\d]/g, ""),
                                )
                              }
                              onBlur={() => {
                                if (durDraft !== null) {
                                  const n = parseInt(durDraft, 10);
                                  if (!Number.isNaN(n)) setDuration(n);
                                  setDurDraft(null);
                                }
                              }}
                              onKeyDown={(e) => {
                                if (e.key === "Enter") e.currentTarget.blur();
                              }}
                              className="min-w-0 flex-1 bg-transparent text-[15px] text-white outline-none"
                            />
                            <span className="shrink-0 text-[12px] text-white/45">
                              s
                            </span>
                          </div>
                        </div>
                      </div>
                    ) : null}
                  </div>
                </>
              ) : (
                <>
                  {/* 批 485 SOURCE_FACT: 模型位 SeedAudio 1.0 (New 标记) */}
                  <div className="relative">
                    <button
                      type="button"
                      aria-label="选择模型: SeedAudio 1.0, New"
                      onClick={() => setOpen((v) => (v === "tts" ? null : "tts"))}
                      className="flex h-8 items-center gap-1 whitespace-nowrap rounded-lg px-2 text-[12px] text-white/90 hover:bg-white/[0.08]"
                    >
                      SeedAudio 1.0
                      <span className="text-[10px] font-medium text-[#5AB0FF]">
                        New
                      </span>
                      <ChevronDown size={12} className="text-white/60" />
                    </button>
                    {open === "tts" ? (
                      <div
                        className="absolute bottom-[calc(100%+8px)] left-0 z-[140] w-[392px] rounded-xl p-1.5"
                        style={{ background: "rgb(38,38,38)" }}
                        role="listbox"
                        aria-label="音色模型"
                        // 批 832：只补锚点，不动名字 —— 名字是源站的，加了就成了「复刻自有」
                        ref={voiceBoxRef}
                        data-testid="audio-voice-model-listbox"
                      >
                        <button
                          type="button"
                          role="option"
                          aria-selected
                          onClick={() => setOpen(null)}
                          className="flex w-full flex-col items-start gap-0.5 rounded-lg px-2.5 py-2 text-left hover:bg-white/10"
                        >
                          <span className="text-[13px] font-medium text-white">
                            SeedAudio 1.0
                          </span>
                          <span className="text-[12px] leading-4 text-white/45">
                            通过引用多个音色，使用时间戳编排人声、音效与配乐
                          </span>
                        </button>
                        {/* 批 852 SOURCE_FACT（探针 852 实测）：源站这一层
                            **有 2 项** —— 第二项 `Seed TTS`，描述
                            「上百个预设音色，让你玩转人声配音」，整项
                            aria-label 是 `Seed TTS, 上百个预设音色，让你玩转人声配音`。
                            逐字照抄，不加「（mock）」标注（源站有的文案不加）。

                            ⚠️ 补这一项的**直接原因**是判据：复刻此前只有 1 项，
                            而方向键在「只有 1 项」时无处可去 —— 于是审计报出
                            「方向键焦点不动」。症状在键盘，**根因是内容缺项**。
                            补上之后源站那两项之间方向键是**来回**的
                            （实测轨迹 Seed TTS ↔ SeedAudio 1.0），
                            复刻接了 `useArrowKeys` 后行为一致。 */}
                        <button
                          type="button"
                          role="option"
                          aria-selected={false}
                          aria-label="Seed TTS, 上百个预设音色，让你玩转人声配音"
                          onClick={() => setOpen(null)}
                          className="flex w-full flex-col items-start gap-0.5 rounded-lg px-2.5 py-2 text-left hover:bg-white/10"
                        >
                          <span className="text-[13px] font-medium text-white">
                            Seed TTS
                          </span>
                          <span className="text-[12px] leading-4 text-white/45">
                            上百个预设音色，让你玩转人声配音
                          </span>
                        </button>
                      </div>
                    ) : null}
                  </div>
                  {/* 批 485 SOURCE_FACT: 音频生成: 全能配音 触发钮 + 引用参考 24×24 */}
                  <div className="relative">
                    <button
                      type="button"
                      aria-label="音频生成: 全能配音"
                      onClick={() => setOpen((v) => (v === "dub" ? null : "dub"))}
                      className={`flex h-8 items-center gap-1 whitespace-nowrap rounded-lg px-2 text-[12px] text-white/90 hover:bg-white/[0.08] ${
                        open === "dub" ? "bg-white/[0.08]" : ""
                      }`}
                    >
                      全能配音
                      <ChevronDown size={12} className="text-white/60" />
                    </button>
                    {open === "dub" ? (
                      <div
                        className="absolute bottom-[calc(100%+8px)] left-0 z-[140] w-[192px] rounded-xl p-1.5"
                        style={{ background: "rgb(38,38,38)" }}
                        role="listbox"
                        aria-label="音频生成模式"
                        // 批 832：只补锚点，不动名字 —— 名字是源站的，加了就成了「复刻自有」
                        ref={dubBoxRef}
                        data-testid="audio-gen-mode-listbox"
                      >
                        <button
                          type="button"
                          role="option"
                          aria-selected
                          onClick={() => setOpen(null)}
                          className="flex h-9 w-full items-center rounded-lg px-2.5 text-[13px] text-white bg-white/[0.10]"
                        >
                          全能配音
                        </button>
                      </div>
                    ) : null}
                  </div>
                  <button
                    type="button"
                    aria-label="引用参考"
                    className="flex size-6 items-center justify-center text-white/80 hover:bg-white/[0.08]"
                  >
                    <Quote size={13} />
                  </button>
                  {/* 批 250/278/282 SOURCE_FACT: 音色下拉 (全音色网格 + 四筛选) */}
                  <div className="relative">
                    <button
                      type="button"
                      aria-label="音色: 音色库"
                      onClick={() => setOpen((v) => (v === "voice" ? null : "voice"))}
                      className="flex h-8 items-center gap-1 whitespace-nowrap rounded-lg px-2 text-[12px] text-white/90 hover:bg-white/[0.08]"
                    >
                      音色库
                      <ChevronDown size={12} className="text-white/60" />
                    </button>
                    {open === "voice" ? (
                      <div
                        className="absolute bottom-[calc(100%+8px)] left-0 z-[140] w-[700px] rounded-xl p-3"
                        style={{ background: "rgb(38,38,38)" }}
                        role="listbox"
                        aria-label="全音色"
                        // 批 832：只补锚点，不动名字 —— 名字是源站的，加了就成了「复刻自有」
                        data-testid="audio-all-voices-listbox"
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
                                    /* ⚠️⚠️ 批 870：这一行原来是
                                       `[label]: m[label] === undefined
                                        ? null : m[label]` —— 后半支把值
                                        **原样写回去**，于是这个钮**只能开、
                                        关不掉**。改成 `undefined` 才成
                                       「开 ↔ 关」的切换。
                                       探针 870 实测：连点两回，筛选面板
                                       一直是 4 个（见 §87）。 */
                                    [label]: m[label] === undefined
                                      ? null : undefined,
                                  }))
                                }
                                aria-expanded={filterSel[label] !== undefined}
                                className="flex h-7 items-center gap-1 rounded-md bg-white/[0.06] px-2 text-[12px] text-white/70"
                              >
                                {filterSel[label] ?? label}
                                <ChevronDown size={10} className="text-white/50" />
                              </button>
                              {/* ⚠️⚠️ 批 870：渲染条件原来只有 `options ?`
                                  —— 而 `options` 是 FILTERS 里写死的**非空
                                  数组**，等于**没有开合状态**：「全音色」一
                                  打开，**四个筛选面板同时渲染**。
                                  探针 870 量完才动手（先探再判）；这里补上
                                  真正的开合判据。 */}
                              {options && filterSel[label] !== undefined ? (
                                /* ⚠️ 批 870：**版式按源站实测逐项对齐**（探针
                                   `jimeng_probe870_voicefilter_src.py`，
                                   登录态、视口 1512×1200）：
                                     · 音色库面板   680×96 @[522,600]
                                     · 筛选钮       153×28 @[538,656]（×4）
                                     · 展开层       161×124 @[534,692]
                                       role=listbox，aria-label=`性别 options`
                                     ⇒ 展开层落在筛选钮**正下方 +8**、
                                       **左移 4**、左右各留 4 padding。
                                   此前这里是 `bottom-[calc(100%+6px)]`
                                   （向上）⇒ 叠在已经抬起来的音色库之上，
                                   实测 y 跑到 **-56**，整个面板在视口外、
                                   点也点不到。源站是**向下**展开的。 */
                                <div
                                  className="absolute left-[-4px] top-[calc(100%+8px)] z-[150] w-[161px] rounded-xl p-1"
                                  style={{ background: "rgb(38,38,38)" }}
                                  role="listbox"
                                  /* 源站逐字：`性别 options`（探针 870 实测）。
                                     此前复刻写的是「筛选 性别」—— 那是**复刻
                                     自造**的名字，源站没有。 */
                                  aria-label={`${label} options`}
                                  // 批 832：只补锚点，不动名字 —— 名字是源站的，加了就成了「复刻自有」
                                  data-testid="audio-voice-filter-listbox"
                                >
                                {/* ⚠️ 批 870：`gap-1`（4px）是按源站实测补的 ——
                                    源站三个选项行 y=696/736/776、行高 36 ⇒
                                    行距 4（内层 116 = 3×36 + 2×4）。此前复刻
                                    没有间距，面板矮 8px。
                                    ⚠️ 顺带记一个自己踩的坑：这个注释**第一版
                                    写成裸的块注释**，而它在 JSX 的
                                    **children** 区域里 —— 那里块注释的
                                    起止符是**文本**不是注释，于是 eslint 报
                                    `Unexpected token`；改成形如
                                    「花括号包住块注释」之后，又因为**正文里
                                    写了块注释的结束符**而提前闭合。
                                    children 区的注释要写花括号包住的形式，
                                    而且**正文里不许再出现结束符**——
                                    跟 docstring 里不许写三引号是同一条。 */}
                                <div className="flex flex-col gap-1">
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
                                {/* ↑ 关掉「选项列表」那层（批 870 为了加
                                    gap-1 引入的），下面这个才是筛选面板本身 */}
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
                                setOpen(null);
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
                  {/* 批 485 SOURCE_FACT: 引用参考 32×32 (音色库之后) */}
                  <button
                    type="button"
                    aria-label="引用参考"
                    className="flex size-8 shrink-0 items-center justify-center text-white/80 hover:bg-white/[0.08]"
                  >
                    <Quote size={15} />
                  </button>
                </>
              )}
            </div>

            <div className="flex h-8 shrink-0 items-center gap-2">
              {/* 批 485 SOURCE_FACT (483c-audio-panel.png): 音频生成态为
                  折扣价格签——可见 ✦12 (white/70) + 24 原价划线 (white/35)
                  + 「显示折扣详情」钮 (aria)，隐藏叶 Current price 12.
                  Original …；音乐生成态维持批 368 契约 (✦ 6，待重采样) */}
              {genKind === "音频生成" ? (
                <button
                  type="button"
                  aria-label="显示折扣详情"
                  className="flex h-5 shrink-0 items-center gap-1 text-white/70"
                >
                  <Sparkle size={12} className="fill-current" />
                  <span className="text-[13px]">12</span>
                  <span className="text-[10px] text-white/35 line-through">
                    24
                  </span>
                  <span className="w-px overflow-hidden whitespace-nowrap text-[12px]">
                    Current price 12. Original 24
                  </span>
                </button>
              ) : (
                <span
                  className="flex h-8 items-center gap-1.5 text-[13px] text-white/85"
                  title="Current price 6.6"
                >
                  <Sparkle size={12} className="fill-current text-white/70" />
                  6
                  <span className="w-px overflow-hidden whitespace-nowrap text-[12px] text-white/[0.69]">
                    Current price 6.6
                  </span>
                </span>
              )}
              <button
                type="button"
                aria-label={canSend ? "生成" : "请输入提示词"}
                title={canSend ? undefined : "请输入提示词"}
                onClick={() => {
                  if (canSend) {
                    // mock: 音频生成流程未接入 (BLOCKED_BY_FIXTURE)
                  }
                }}
                className={`flex size-8 items-center justify-center rounded-full ${
                  canSend
                    ? "bg-[#fafafa] text-black hover:bg-white/90"
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
