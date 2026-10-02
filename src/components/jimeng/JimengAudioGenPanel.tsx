"use client";

import { useRef, useState } from "react";
import type { RefObject } from "react";
import {
  ArrowUp,
  ChevronDown,
  Maximize2,
  Plus,
  Quote,
  Sparkle,
  X,
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
  /* 批 873：把「**开着没有**」和「**选了什么**」拆成**两个**状态。

     原来只有一个 `filterSel`，它同时承担两件事：既是选中值，又是开合标志
     （面板渲染条件 `filterSel[label] !== undefined`）。于是**选完一个选项
     后面板收不起来** —— 选中值还在 ⇒ 「开着」⇒ 层一直挂着。

     源站实测（`jimeng_probe873_voiceselect.py`，登录态、视口 1512×1200）：
     选「男」**和**选「全部 性别」**都**自动收起层，焦点回到筛选钮
     （实测落点 `BUTTON/性别: 男` / `BUTTON/性别: 全部 性别`）。
     两个选项**都**收 ⇒ 拆状态是唯一能同时表达「值留着、层收了」的写法。 */
  const [filterOpen, setFilterOpen] = useState<Record<string, boolean>>({});

  /* 批 875：四个筛选**芯片**的 ref，点「清除」后要把焦点送回芯片
     （源站实测点完 Clear 焦点落回 `BUTTON/{label}: 全部 {label}`）。
     这里是 ref 而不是 hook，所以 `FILTERS.map` 里访问 `chipRefs.current[label]`
     不违反 Hooks 规则 —— 上面 871 那条约束针对的是 `useXxx()` 调用。 */
  const chipRefs = useRef<Record<string, HTMLButtonElement | null>>({});

  /* 批 871：四个筛选面板各接一次「开层接管焦点」。
     ⚠️ 为什么是**四组显式 ref + 四次 hook 调用**，而不是
        `FILTERS.map((f) => useTakeFocusAtOpen(...))` —— 在 map / 回调里调
        hook 违反 Hooks 规则（数量会随渲染变），eslint 会拦。四组写死虽然
        啰嗦，但**数量固定、顺序固定**，且和 FILTERS 的四项一一对应
        （批 871 核对过：性别/年龄/语言/声音特点）。

     依据是**源站实测**（`jimeng_probe871_voicefilter_kb.py`，登录态、
     视口 1512×1200）：打开筛选层时焦点落在**第一项** option
     （`全部 性别`，idx=0），复刻原先**开层完全不接管焦点**。
     `useTakeFocusAtOpen` 聚焦层内第一个可聚焦项，对这个 listbox
     正好就是第一项 ⇒ 与源站等价。

     ⚠️ 刻意**不接** `useModalFocusTrap`：源站实测从层内**第 1 次** Tab
     就逃到下一个筛选 chip（不困 Tab），困了反而与源站相反（§82 分流）。 */
  const filterGenderBox = useRef<HTMLDivElement>(null);
  const filterAgeBox = useRef<HTMLDivElement>(null);
  const filterLangBox = useRef<HTMLDivElement>(null);
  const filterToneBox = useRef<HTMLDivElement>(null);
  useTakeFocusAtOpen(filterGenderBox, filterOpen["性别"] === true);
  useTakeFocusAtOpen(filterAgeBox, filterOpen["年龄"] === true);
  useTakeFocusAtOpen(filterLangBox, filterOpen["语言"] === true);
  useTakeFocusAtOpen(filterToneBox, filterOpen["声音特点"] === true);
  const filterBoxRef: Record<string, RefObject<HTMLDivElement | null>> = {
    "性别": filterGenderBox, "年龄": filterAgeBox,
    "语言": filterLangBox, "声音特点": filterToneBox,
  };

  /* ⚠️⚠️ 批 875：「没设值」在源站**不是**「什么都不选中」，而是
     **`全部 {筛选名}` 那一项处于选中态**。探针 875 实测（4/4）：
       · 刚开层：`全部 性别` 的 `aria-selected="true"`
       · 选「男」再点 Clear：回到 `全部 性别` = true
     复刻原先把「没设值」写成 `filterSel[label] ?? label`（拿**筛选名**
     当哨兵），于是清掉之后层里 `seld=[]` —— 一个都不选中，与源站相反。

     所以哨兵统一成 **`null`**：可见文案仍然显示筛选名（源站 chip 上写的
     是「性别」不是「全部 性别」），但**可访问名和选中态**按「全部 {筛选名}」算。 */
  const curFilterVal = (label: string): string =>
    filterSel[label] ?? `全部 ${label}`;

  const visibleVoices = VOICES.filter(
    (v) =>
      (!filterSel["性别"] || v.gender === filterSel["性别"]) &&
      (!filterSel["语言"] ||
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
                            /* ⚠️⚠️ 批 875 SOURCE_FACT：外层格子**恒定 153×28**
                               —— 选中与否都不变。变的是**格子里装什么**：
                                 · 未选中：一个 153 宽的筛选钮
                                 · 已选中：芯片 111 + gap 8 + Clear 16 = 135
                                   （外层左右各 9 padding ⇒ 135+18 = 153 ✓）
                               探针 875 实测 `row_dom_after`：外层
                               `w-canvas-audio-voice-filter-control` 选中前后
                               都是 153×28，只有内层从 1 个元素变成 2 个。
                               所以 Clear 是**格子里并排的第二个元素**，
                               不是浮在上面 —— 也就不会盖住芯片。

                               ⚠️ 第一版这里没锁宽，于是复刻的格子选中后
                               **缩到 135**（探针：格子宽高不变 0/4，
                               源站 4/4）—— 整行跟着左移，后面三个筛选钮
                               全部错位。锁 `w-[153px]` 即可。 */
                            <div key={label} className="relative flex h-7 w-[153px] shrink-0 items-center gap-2 px-[9px]">
                              <button
                                type="button"
                                ref={(el) => {
                                  chipRefs.current[label] = el;
                                }}
                                onClick={() => {
                                  /* ⚠️⚠️ 批 873：箭头**必须改成块体**
                                     `{ … }` —— 原来它是**表达式体**
                                     `() => setFilterSel(…)`，一个表达式体里
                                     放不下第二条语句：加分号会把 JSX 属性
                                     表达式**切断**，parser 报 `'}' expected`
                                     而位置指着**下一句**（查错地方的经典坑）。
                                     要两条语句，就得是块体。 */
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
                                  }));
                                  /* 批 873：开合**另算**（见上面 filterOpen）。
                                     ⚠️ 原来 `onClick={() => setFilterSel(…)}`
                                        是**单表达式**箭头（结尾没分号）；
                                        现在多了一句，就必须补 `;` ——
                                        少一个分号，parser 报的是
                                        `'}' expected`，位置却指着**下一句**，
                                        很容易查错地方。
                                     870 修的「关不掉」靠的就是这条切换 ——
                                     拆状态之后它仍然成立，**没有回归**。 */
                                  setFilterOpen((o) => ({ ...o, [label]: !o[label] }));
                                }}
                                aria-expanded={filterOpen[label] === true}
                                /* 批 873：源站这个钮的 `aria-label` 是
                                   **`{筛选名}: {当前值}`**（探针 873 实测焦点落点
                                   读作 `BUTTON/性别: 男`）。
                                   ⚠️⚠️ 批 875 补：873 **只抄了一半** ——
                                   同一个注释里其实记着另一个读数
                                   `BUTTON/性别: 全部 性别`（未选中时），
                                   但代码写的是 `?? label`，读出来是
                                   `性别: 性别`。探针 875 在源站复测
                                   **4/4** 都读到 `全部 {筛选名}`，已改正。
                                   可见文案**仍然**是筛选名（源站 chip 上
                                   写「性别」），只有可访问名用「全部」。 */
                                aria-label={`${label}: ${curFilterVal(label)}`}
                                /* 批 875：外层格子 153 宽里扣掉左右各 9 的
                                   padding ⇒ 内部可用 **135**。选中时排成
                                   芯片 111 + gap 8 + Clear 16 = 135（满）；
                                   未选中时芯片独占 135。外层宽高选中前后
                                   不变，变的只有这里。 */
                                className={
                                  filterSel[label]
                                    ? "flex h-[26px] w-[111px] items-center gap-1 rounded-md bg-white/[0.06] px-2 text-[12px] text-white/70"
                                    : "flex h-7 w-[135px] items-center gap-1 rounded-md bg-white/[0.06] px-2 text-[12px] text-white/70"
                                }
                              >
                                {filterSel[label] ?? label}
                                <ChevronDown size={10} className="text-white/50" />
                              </button>
                              {/* ⚠️⚠️ 批 875 SOURCE_FACT：源站选中一个值之后，
                                 芯片**右边**会冒出���个 16×16 的清除钮，
                                 `aria-label="Clear {筛选名} filter"`（英文，
                                 逐字照抄；探针 875 四个筛选钮**逐个**量到，
                                 4/4 一致，不是拿性别外推的）。

                                 复刻原先**没有**这个控件 ⇒ 选中之后
                                 **没法退回「全部」**，只能逐个点开层再点
                                 「全部 X」—— 这是功能缺失，不是样式差异。

                                 实测行为（4/4 一致）：
                                   · 未选中时**不存在**
                                   · 选中后出现，垂直居中
                                   · 点它 ⇒ 值回落到「全部 {筛选名}」
                                     （复开层读 `aria-selected`：全部=true）
                                   · 它自己同时消失
                                   · 焦点回到芯片（aria 变成
                                     `{label}: 全部 {label}`）
                                 因此这里必须**先 focus 芯片再 setState**
                                 ——与 873 选完值那次的顺序同因。 */}
                              {filterSel[label] ? (
                                <button
                                  type="button"
                                  aria-label={`Clear ${label} filter`}
                                  onClick={() => {
                                    /* 先收焦点再改状态：层若正开着，
                                       收焦点会让它在同一帧被卸载。 */
                                    chipRefs.current[label]?.focus();
                                    setFilterSel((m) => ({ ...m, [label]: null }));
                                    setFilterOpen((o) => ({ ...o, [label]: false }));
                                  }}
                                  /* ⚠️ 批 876 SOURCE_FACT：焦点在这个钮上按
                                     **Esc 会清除**（探针 876c 源站**三次复现**
                                     一致：值 男 → 全部 性别、Clear 消失）。
                                     这是「撤销刚设的那个筛选」的语义，
                                     与「焦点在**芯片**上按 Esc」**不同** ——
                                     874 实测后者只收层、**值保留**。
                                     Esc 的行为**由焦点位置决定**。

                                     ⚠️ 刻意**不** `stopPropagation()`：
                                     源站 Esc 是「清除 **+** 关掉整个音色库面板」
                                     两个动作**同时**发生（实测 `voices_open`
                                     变 False、焦点落到音频节点本体）。清除
                                     归这一层，关面板**冒泡给上层 handler**，
                                     两边都做，才与源站等价。
                                     也因此这里**不** `focus()` 芯片 ——
                                     源站焦点落点不是芯片（面板要关，
                                     芯片一起卸载），强行聚焦只会多出
                                     一个源站没有的落点。 */
                                  onKeyDown={(e) => {
                                    if (e.key === "Escape") {
                                      /* ⚠️⚠️ 批 878–881：这块 focus 修了两轮
                                         才查到**机制**，而机制给出的结论是
                                         「同步落焦点**不够**」。

                                         探针链（每一步都排除了一个假设）：
                                           878 `closest('.react-flow__node')`
                                               → 没生效（NodeToolbar 是
                                                 portal，不在节点里面）
                                           879 改走 `data-id`
                                               → 仍没生效
                                           880 手工 replay：**全部可行**
                                               —— closest ✓、data-id ✓、
                                               focus() ✓、300ms 后焦点**稳在**
                                               节点上 ✓ ⇒ 排除「focus 不可行」
                                               「焦点留不住」「代码没编译」
                                           881 焦点**事件流**：
                                               +3ms  focusin 节点 ← **成功了**
                                               +52ms blur     ← **被抢走了**
                                               节点 DOM **没被替换**
                                               （标记还在、isConnected、
                                                 同一个元素）
                                         ⇒ 同步 focus 之后有个**延迟动作**
                                         （~52ms，不是同帧）把焦点拿走。

                                         所以这里**落三次**：同步、下一帧、
                                         120ms（盖过 52ms 那个）。前两次
                                         覆盖「同帧就抢」，第三次覆盖
                                         「延迟才抢」。

                                         ⚠️ 仍**可能**不够：若抢焦点的东西
                                         还会再抢，就会变成打地鼠。真到
                                         那一步就**记账收手**（§77：机制
                                         没验死之前不许改判据），不许
                                         靠加 setTimeout 试到「碰巧对了」。 */
                                      const tb = (
                                        e.currentTarget as HTMLElement
                                      ).closest(".react-flow__node-toolbar");
                                      const nid = tb?.getAttribute("data-id");
                                      let nodeEl: HTMLElement | null = null;
                                      if (nid) {
                                        /* 用**属性相等**（`getAttribute` 比较）
                                           而不是**选择器字符串拼接**：节点 id
                                           可能含 `:` 等选择器里有意义的字符，
                                           拼进 `[data-id="…"]` 会选错。 */
                                        nodeEl = [
                                          ...document.querySelectorAll(
                                            ".react-flow__node"),
                                        ].find(
                                          (n) =>
                                            n.getAttribute("data-id") === nid,
                                        ) ?? null;
                                      }
                                      const refocus = () => {
                                        /* 已被抢走（不在节点上）才补落 ——
                                           已经落在上面就别重复动，免得自己
                                           把「本来就对」的状态搅乱。 */
                                        if (
                                          nodeEl &&
                                          document.activeElement !== nodeEl
                                        ) {
                                          nodeEl.focus();
                                        }
                                      };
                                      refocus();
                                      requestAnimationFrame(refocus);
                                      setTimeout(refocus, 120);
                                      setFilterSel((m) => ({
                                        ...m, [label]: null,
                                      }));
                                      setFilterOpen((o) => ({
                                        ...o, [label]: false,
                                      }));
                                    }
                                  }}
                                  className="flex size-4 items-center justify-center rounded-full text-white/50 hover:text-white/80"
                                >
                                  <X size={10} />
                                </button>
                              ) : null}
                              {/* ⚠️⚠️ 批 870：渲染条件原来只有 `options ?`
                                  —— 而 `options` 是 FILTERS 里写死的**非空
                                  数组**，等于**没有开合状态**：「全音色」一
                                  打开，**四个筛选面板同时渲染**。
                                  探针 870 量完才动手（先探再判）；这里补上
                                  真正的开合判据。 */}
                              {options && filterOpen[label] === true ? (
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
                                  /* 批 871：三条键盘行为，全部按**源站实测**接上
                                     （`jimeng_probe871_voicefilter_kb.py`，
                                     登录态、视口 1512×1200，每项都单独验过
                                     前置态）：

                                       ① 开层**接管焦点到第一项**（实测焦点落在
                                          `全部 性别`，idx=0）⇒ 接
                                          `useTakeFocusAtOpen`（它聚焦层内第一个
                                          可聚焦元素，对这个 listbox 正好是第一项）。
                                       ② **不困 Tab**：实测从层内**第 1 次** Tab
                                          就逃到下一个筛选 chip ⇒ 刻意**不接**
                                          `useModalFocusTrap`（§82 的分流）。
                                       ③ **方向键在层内逐格移动**：实测
                                          idx 0 → 1 → 2（3 个选项）⇒ 下面这个
                                          `onKeyDown`。
                                       ④ **Esc 收层且焦点回筛选钮**（实测焦点
                                          落到 `BUTTON/性别`）⇒ 同一个 handler。

                                     ⚠️ 复刻原先这四条**一条都没有**：开层不接管
                                     焦点、方向键不动、Esc 关不掉。 */
                                  onKeyDown={(e) => {
                                    // 找到这一块筛选自己的容器（chip 的下一个兄弟）
                                    const box = (e.currentTarget as HTMLElement);
                                    const chip: HTMLElement | null =
                                      box.previousElementSibling;
                                    if (e.key === "Escape") {
                                      e.preventDefault();
                                      e.stopPropagation();
                                      // 批 873：**只关层，不清选中值**。
                                      // 源站「Esc 之后选中值还在不在」**没量到**
                                      // —— 这里按「收层 ≠ 取消选择」实现，
                                      // 并把它记进范围限制，别让下一个人
                                      // 以为这是源站行为。
                                      setFilterOpen((o) => ({ ...o, [label]: false }));
                                      // 焦点回筛选钮（源站实测就是回到它）
                                      chip?.focus();
                                      return;
                                    }
                                    if (e.key !== "ArrowDown"
                                        && e.key !== "ArrowUp"
                                        && e.key !== "Home" && e.key !== "End") {
                                      return;
                                    }
                                    const opts = [
                                      ...box.querySelectorAll<HTMLButtonElement>(
                                        '[role="option"]'),
                                    ];
                                    if (!opts.length) return;
                                    e.preventDefault();
                                    const cur = opts.indexOf(
                                      document.activeElement as HTMLButtonElement);
                                    const next = e.key === "Home" ? 0
                                      : e.key === "End" ? opts.length - 1
                                      : e.key === "ArrowDown"
                                        ? (cur < 0 ? 0
                                          : Math.min(cur + 1, opts.length - 1))
                                        : (cur < 0 ? opts.length - 1
                                          : Math.max(cur - 1, 0));
                                    opts[next]?.focus();
                                  }}
                                  ref={filterBoxRef[label]}
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
                                      aria-selected={curFilterVal(label) === opt}
                                      onClick={(e) => {
                                        /* 块体，理由同上（一条 JSX 属性里
                                           要三条语句 ⇒ 必须是块体）。 */
                                        /* 批 873：源站实测选完之后**焦点回到
                                           那个筛选钮**（落点 `BUTTON/性别: 男`）。
                                           复刻原先什么都不做 ⇒ 面板一卸，焦点
                                           **掉到 body**（复刻探针实测
                                           `focus='body'`）—— 那是最坏落点：
                                           键盘用户完全不知道自己在哪。
                                           ⚠️ 必须**先** focus 再 setState：
                                           收层后这块 DOM 就被卸载了。 */
                                        const chipBtn = (e.currentTarget as HTMLElement)
                                          .closest('[role="listbox"]')
                                          ?.previousElementSibling as HTMLElement | null;
                                        chipBtn?.focus();
                                        setFilterSel((m) => ({
                                          ...m,
                                          /* ⚠️ 批 875：选「全部 X」= **没设值**。
                                             原来这里写的是 `? label : opt`，
                                             拿筛选名当哨兵；现在哨兵统一
                                             成 `null`（见 curFilterVal）。 */
                                          [label]: opt.startsWith("全部")
                                            ? null : opt,
                                        }));
                                        /* 批 873：源站实测**选完自动收层**
                                           （选「男」和选「全部 性别」都收，
                                           探针 873 两条路径分别量过），
                                           焦点回到筛选钮。 */
                                        setFilterOpen((o) => ({
                                          ...o, [label]: false,
                                        }));
                                      }}
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
