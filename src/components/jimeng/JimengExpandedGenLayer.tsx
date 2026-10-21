"use client";

/**
 * ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
 * 1032-②b-4：「**已展开的生成器**」浮层。
 *
 * ⭐⭐⭐⭐⭐ **SOURCE_FACT（批次 1032-②b-1 实测，产物
 * `docs/research/jimeng-canvas/inputs/source-expanded-gen-1032b1.json`）**：
 *  · 触发钮：面板级，40×40，`aria-label="展开视频生成器"`
 *  · 浮层：`role="dialog"` / `aria-label="已展开的视频生成器"` /
 *    `position: fixed` / **920×480** / radius **20px** / z-index **50**
 *    ⇒ ⇒ **不是全屏遮罩，是一个居中的浮动面板**
 *  · 5 枚「全部 / 图片 / 视频 / 音频 / 文本」：**42×36 的普通按钮**
 *    ⇒ ⇒ **没有** `role=tab`（源站浮层内**没有** role=tab/option/radio）
 *  · 右上角是「**折叠视频生成器**」36×36 ⇒ 与触发它的那枚是**同一个 affordance**
 *  · 「添加参考」48×48；「引用参考」24×24 与 32×32 各一
 *  · 模型 184×32 / 尺寸 129×32 / 生成模式 80×32 / 时长 46×32 / 生成 32×32
 *  · ⭐ 浮层内**没有 input/textarea** ⇒ 提示词区是 **contenteditable**
 *
 * ⚠️⭐⭐⭐ **诚实标注边界**：
 *  · 上面这些**只对「视频」这一种是实测的**（源站那次取证点的是
 *    「展开视频生成器」）⇒ ⇒ **图片 / 音频两种浮层的具体规格是 CLONE_DECISION**
 *    （沿用同构的形状，但**没有**逐项实测）⇒ ⇒ 代码里逐处标明。
 *  · 5 枚类型按钮在源站上的**确切作用未逐项验证**（源站没有把它们接成可测的切换）
 *    ⇒ ⇒ 复刻把它们实现为「**参考类型筛选**」（点了之后「引用参考」的
 *    `aria-label` 真的会带上类型）⇒ ⇒ 这是 **CLONE_DECISION**。
 *  · 「56 / Current price 56.」是源站**当前会话**的读数 ⇒ 不是常量规格
 *    ⇒ ⇒ 复刻用的是自己那档的取证值（`56.56`）。
 */

import { createPortal } from "react-dom";
import { useEffect, useRef, useState } from "react";
import { ChevronDown, Minimize2, Plus, Scan } from "lucide-react";

import { useJimengStore } from "@/store/jimengStore";
import { FEEDBACK } from "@/components/jimeng/jimengFeedback";

export type ExpandedGenKind = "video" | "image" | "audio";

/** 5 枚参考类型按钮（SOURCE_FACT：42×36，普通按钮，**没有** role=tab） */
const REF_TYPES = ["全部", "图片", "视频", "音频", "文本"] as const;
type RefType = (typeof REF_TYPES)[number];

interface KindSpec {
  /** 浮层的 aria-label（源站逐字） */
  layerAria: string;
  /** 折叠钮的 aria-label（源站逐字） */
  collapseAria: string;
  /** 模型按钮文案 / aria */
  model: string;
  modelAria: string;
  /** 尺寸按钮文案 / aria */
  size: string;
  sizeAria: string;
  /** 生成模式按钮文案 / aria */
  mode: string;
  modeAria: string;
  /** 时长按钮文案 / aria */
  duration: string;
  durationAria: string;
  /** 提示词区 placeholder（源站逐字） */
  placeholder: string;
  /** 价格（复刻自己的取证值；源站那次是「56」，是会话读数不是常量规格） */
  price: string;
  modelOptions: string[];
  sizeOptions: string[];
  modeOptions: string[];
  durationOptions: string[];
}

/** 视频：SOURCE_FACT（批次 1032-②b-1 实测） */
const VIDEO_SPEC: KindSpec = {
  layerAria: "已展开的视频生成器",
  collapseAria: "折叠视频生成器",
  model: "即梦 Seedance 2.0 VIP",
  modelAria: "选择模型: 即梦 Seedance 2.0 VIP, Standard-only model",
  size: "9:16 · 720P · 1",
  sizeAria: "视频尺寸选项: 9:16 · 720P · 1, Standard-only model",
  mode: "全能参考",
  modeAria: "生成模式: 全能参考",
  duration: "4s",
  durationAria: "选择视频生成时长: 4s",
  placeholder: "上传参考图、输入文字或 @ 主体，描述你想生成的视频",
  price: "56.56",
  modelOptions: [
    "即梦 Seedance 2.0 VIP",
    "即梦 Seedance 2.0 Fast VIP",
    "即梦 Seedance 2.0 mini",
  ],
  sizeOptions: ["9:16 · 720P · 1", "16:9 · 720P · 1", "1:1 · 720P · 1"],
  modeOptions: ["全能参考", "首尾帧"],
  durationOptions: ["4s", "8s", "12s"],
};

/** 图片：⚠️ CLONE_DECISION（源站**没有**实测过图片侧的展开浮层） */
const IMAGE_SPEC: KindSpec = {
  layerAria: "已展开的图片生成器",
  collapseAria: "折叠图片生成器",
  model: "即梦 Seedream 4.0",
  modelAria: "选择模型: 即梦 Seedream 4.0, Standard-only model",
  size: "1:1 · 2K",
  sizeAria: "图片尺寸选项: 1:1 · 2K, Standard-only model",
  mode: "全能参考",
  modeAria: "生成模式: 全能参考",
  duration: "1",
  durationAria: "选择图片生成张数: 1",
  placeholder: "上传参考图、输入文字或 @ 主体，描述你想生成的图片",
  price: "6.6",
  modelOptions: ["即梦 Seedream 4.0", "即梦 Seedream 3.0"],
  sizeOptions: ["1:1 · 2K", "4:3 · 2K", "3:4 · 2K"],
  modeOptions: ["全能参考", "精准参考"],
  durationOptions: ["1", "2", "3", "4"],
};

/** 音频：⚠️ CLONE_DECISION（源站**没有**实测过音频侧的展开浮层） */
const AUDIO_SPEC: KindSpec = {
  layerAria: "已展开的音频生成器",
  collapseAria: "折叠音频生成器",
  model: "即梦 SeedAudio 1.0",
  modelAria: "选择模型: 即梦 SeedAudio 1.0, Standard-only model",
  size: "音频生成",
  sizeAria: "音频尺寸选项: 音频生成, Standard-only model",
  mode: "全能参考",
  modeAria: "生成模式: 全能参考",
  duration: "12s",
  durationAria: "选择音频生成时长: 12s",
  placeholder: "上传参考音频、输入文字或 @ 主体，描述你想生成的音频",
  price: "12",
  modelOptions: ["即梦 SeedAudio 1.0", "即梦 SeedAudio 1.0 Pro"],
  sizeOptions: ["音频生成", "音乐生成"],
  modeOptions: ["全能参考", "精准参考"],
  durationOptions: ["12s", "24s", "36s"],
};

const SPECS: Record<ExpandedGenKind, KindSpec> = {
  video: VIDEO_SPEC,
  image: IMAGE_SPEC,
  audio: AUDIO_SPEC,
};

interface ParamMenuProps {
  /** 触发器的 aria-label（源站逐字） */
  aria: string;
  /** 可选值 */
  options: string[];
  /** 当前值 */
  value: string;
  /** 换值（真的换 ⇒ 浮层内可见文本会变） */
  onChange: (v: string) => void;
  /** 触发器宽度（源站逐项实测；走 inline style，不依赖 Tailwind CSS 构建产物） */
  width: number;
  /** aria-haspopup 的值（源站：模型/模式 = listbox、时长 = dialog） */
  hasPopup: "listbox" | "dialog";
  menuAria: string;
}

/** 参数下拉：**真的能换值**（不是装饰）。 */
function ParamMenu({
  aria,
  options,
  value,
  onChange,
  width,
  hasPopup,
  menuAria,
}: ParamMenuProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    window.addEventListener("mousedown", onDown);
    return () => window.removeEventListener("mousedown", onDown);
  }, [open]);

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        aria-label={aria}
        aria-haspopup={hasPopup}
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1 whitespace-nowrap rounded-lg px-2 text-[12px] text-white/90 hover:bg-white/[0.08]"
        style={{ width, height: 32 }}
      >
        {value}
        <ChevronDown size={12} className="text-white/60" />
      </button>
      {open ? (
        <div
          role={hasPopup === "dialog" ? "dialog" : "listbox"}
          aria-label={menuAria}
          data-testid="expanded-gen-param-menu"
          className="absolute bottom-[calc(100%+8px)] left-0 z-[140] min-w-[120px] rounded-[10px] border border-white/[0.06] p-1.5"
          style={{ background: "rgb(38,38,38)" }}
        >
          {options.map((o) => (
            <button
              key={o}
              type="button"
              role={hasPopup === "dialog" ? "button" : "option"}
              aria-selected={hasPopup === "dialog" ? undefined : o === value}
              onClick={() => {
                onChange(o);
                setOpen(false);
              }}
              className="block w-full rounded-md px-2 py-1 text-left text-[12px] text-white/85 hover:bg-white/[0.08]"
            >
              {o}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}

export function JimengExpandedGenLayer() {
  const layer = useJimengStore((s) => s.expandedGenLayer);
  const closeExpandedGenLayer = useJimengStore((s) => s.closeExpandedGenLayer);
  const selectedNodeId = useJimengStore((s) => s.selectedNodeId);
  const startRefPicking = useJimengStore((s) => s.startRefPicking);
  const generateInto = useJimengStore((s) => s.generateInto);
  const generateImageInto = useJimengStore((s) => s.generateImageInto);
  const generateAudioInto = useJimengStore((s) => s.generateAudioInto);
  const pushToast = useJimengStore((s) => s.pushToast);

  const [refType, setRefType] = useState<RefType>("全部");
  const [prompt, setPrompt] = useState("");

  const kind = layer?.kind ?? "video";
  const spec = SPECS[kind];
  /* ⭐⭐⭐ 参数初值**惰性初始化**（不是用 effect 铺）：
   *   本组件由 workspace **在浮层打开时**才挂载 ⇒ ⇒ 挂载那一刻的 spec 就是对的
   *   ⇒ ⇒ 于是不需要「先空一轮再补上」的那个 effect
   *   ⇒ ⇒ 而那个 effect 会被 react-hooks/set-state-in-effect 判为错
   *   ⇒ ⇒⇒ **「用 effect 同步派生状态」是 React 自己不推荐的形状** ——
   *   ⇒ ⇒⇒ 正确的做法是让**挂载时机**承载这件事。 */
  const [params, setParams] = useState(() => ({
    model: spec.model,
    size: spec.size,
    mode: spec.mode,
    duration: spec.duration,
  }));

  // ⭐ 节点不再被选中 ⇒ 浮层跟着关（浮层在 workspace 层，不随面板卸载而消失）
  useEffect(() => {
    if (!layer) return;
    if (selectedNodeId && selectedNodeId !== layer.nodeId) {
      closeExpandedGenLayer();
    }
  }, [layer, selectedNodeId, closeExpandedGenLayer]);

  if (!layer || !spec) return null;

  const onGenerate = () => {
    const text = prompt.trim();
    // ⭐⭐⭐ 负控：提示词为空 ⇒ **什么也不该发生**（不许调 action）
    if (!text) return;
    if (kind === "image") generateImageInto(layer.nodeId, text);
    else if (kind === "audio") generateAudioInto(layer.nodeId, text);
    else generateInto(layer.nodeId, text);
    pushToast(FEEDBACK.taskSubmitted("生成"));
  };

  return createPortal(
    <>
      {/* ⭐⭐⭐ CLONE_DECISION：透明点击层。
       *   源站只实测到「浮层是 fixed 的**居中浮动面板**、不是全屏遮罩」
       *   （批次 1032-②b-1 产物 `expanded_layer`），
       *   **没有**实测「点浮层外面会怎样」⇒ ⇒ 这里加一层**透明**点击层
       *   来承接「点外面关闭」⇒ 它**视觉上不是遮罩**（无背景色、无模糊）。 */}
      <div
        data-testid="expanded-gen-layer-backdrop"
        aria-hidden="true"
        className="fixed inset-0 z-[49]"
        onClick={closeExpandedGenLayer}
      />
      {/* ⭐⭐⭐⭐⭐ SOURCE_FACT：源站那条 `expanded_layer` 记录里，
       *   **`role="dialog"` 那个元素本身**就是
       *   `position: fixed` / 920×480 / radius 20px / z-index 50
       *   （批次 1032-②b-1 产物逐字读数：rect.x=296 rect.y=235 ⇒ 相对视口居中）
       *   ⇒ ⇒ 所以 `fixed` / 居中 / z 50 必须落在这个元素上，
       *   **不是**落在外面那层容器上。
       *
       *   ⚠️⭐⭐⭐ **尺寸写 inline style，不写进 className**：
       *   ① 源站逐项实测的数值就是这里的字面量 ⇒ 一眼能对着源站产物核对；
       *   ② **不依赖 Tailwind 的 CSS 构建产物** ——
       *      本仓 dev server（Next.js + Tailwind v4 + **PostCSS**）
       *      **不会监听新出现的内容文件**：新建组件的类名要等
       *      「CSS 文件自身发生内容变化」才会被重新扫描并生成。
       *      ⇒ ⇒ 一旦某个类名缺失，量几何的门读到的是**陈旧 CSS** ⇒ 报出**假阴性**。
       *      ⚠️ 这条陷阱在 1032-②b-4 真的踩到了：
       *      `w-[42px]` 没进 CSS ⇒ 5 枚类型钮量到 24px（内容宽）而不是 42px，
       *      一度被当成「复刻做错了」。 */}
      <div
        role="dialog"
        aria-label={spec.layerAria}
        data-testid="expanded-gen-layer"
        data-expanded-gen-kind={kind}
        className="fixed flex flex-col bg-[#202020] p-4"
        style={{
          width: 920,
          height: 480,
          zIndex: 50,
          borderRadius: 20,
          /* SOURCE_FACT：源站 rect.x=296 rect.y=235（视口 1512×950）⇒ 相对视口居中 */
          left: "50%",
          top: "50%",
          transform: "translate(-50%, -50%)",
        }}
      >
        {/* 顶部：5 枚类型按钮 + 右上角折叠钮 */}
        <div className="flex h-9 w-full items-start justify-between">
          <div className="flex items-center gap-1">
            {REF_TYPES.map((t) => (
              <button
                key={t}
                type="button"
                /* ⚠️ CLONE_DECISION：源站这 5 枚**没有** aria（源站浮层内
                   **没有** role=tab/option/radio）⇒ ⇒ 这里加 `aria-pressed`
                   是复刻自带的可访问性增强，**不声称**源站有同名属性。 */
                aria-pressed={refType === t}
                onClick={() => setRefType(t)}
                className={`flex items-center justify-center rounded-lg text-[12px] ${
                  refType === t
                    ? "bg-white/[0.12] text-white"
                    : "text-white/60 hover:bg-white/[0.08]"
                }`}
                /* SOURCE_FACT：42×36（源站产物 `buttons[0..4]` 逐字读数） */
                style={{ width: 42, height: 36 }}
              >
                {t}
              </button>
            ))}
          </div>
          <button
            type="button"
            aria-label={spec.collapseAria}
            onClick={closeExpandedGenLayer}
            className="flex items-center justify-center rounded-lg text-white/60 hover:bg-white/[0.08]"
            /* SOURCE_FACT：折叠视频生成器 36×36 */
            style={{ width: 36, height: 36 }}
          >
            <Minimize2 size={16} />
          </button>
        </div>

        {/* 主体：左侧素材栏 + 右侧提示词区 */}
        <div className="flex min-h-0 flex-1 gap-3 pt-3">
          <div className="flex w-[56px] flex-col items-center gap-2">
            {/* 添加参考 48×48（SOURCE_FACT） */}
            <button
              type="button"
              aria-label="添加参考"
              onClick={() => startRefPicking()}
              className="flex items-center justify-center rounded-xl bg-white/[0.06] text-white/80 hover:bg-white/10"
              /* SOURCE_FACT：添加参考 48×48 */
              style={{ width: 48, height: 48 }}
            >
              <Plus size={20} />
            </button>
            {/* 引用参考 24×24（SOURCE_FACT） */}
            <button
              type="button"
              aria-label={`引用参考${refType === "全部" ? "" : `: ${refType}`}`}
              onClick={() => startRefPicking()}
              className="flex items-center justify-center rounded-md bg-white/[0.06] text-white/70 hover:bg-white/10"
              /* SOURCE_FACT：引用参考 24×24 */
              style={{ width: 24, height: 24 }}
            >
              <Scan size={12} />
            </button>
            {/* 引用参考 32×32（SOURCE_FACT：浮层里有两枚「引用参考」，尺寸不同） */}
            <button
              type="button"
              aria-label={`引用参考${refType === "全部" ? "" : `: ${refType}`}`}
              onClick={() => startRefPicking()}
              className="mt-auto flex items-center justify-center rounded-lg bg-white/[0.06] text-white/70 hover:bg-white/10"
              /* SOURCE_FACT：引用参考 32×32（浮层里有两枚「引用参考」，尺寸不同） */
              style={{ width: 32, height: 32 }}
            >
              <Scan size={14} />
            </button>
          </div>

          <div className="flex min-w-0 flex-1 flex-col">
            {/* 提示词区：⭐ SOURCE_FACT —— 浮层内**没有 input/textarea**，
                提示词是 **contenteditable**。 */}
            <div className="relative min-h-0 flex-1 rounded-[12px] bg-white/[0.04] p-3">
              <div
                contentEditable
                suppressContentEditableWarning
                role="textbox"
                aria-label="提示词"
                aria-multiline="true"
                data-testid="expanded-gen-prompt"
                onInput={(e) =>
                  setPrompt((e.currentTarget as HTMLElement).innerText || "")
                }
                className="min-h-[120px] w-full overflow-y-auto text-[13px] leading-[22px] text-white outline-none"
              />
              {prompt.trim() ? null : (
                <span
                  className="pointer-events-none absolute left-3 top-3 text-[13px] leading-[22px] text-white/35"
                  data-testid="expanded-gen-prompt-placeholder"
                >
                  {spec.placeholder}
                </span>
              )}
            </div>

            {/* 底部控制行 */}
            <div className="flex h-8 w-full items-center justify-between gap-1 pt-3">
              <div className="flex min-w-0 items-center gap-1">
                <ParamMenu
                  aria={`选择模型: ${params.model}, Standard-only model`}
                  options={spec.modelOptions}
                  value={params.model}
                  onChange={(v) => setParams((p) => ({ ...p, model: v }))}
                  width={184}
                  hasPopup="listbox"
                  menuAria="模型选项"
                />
                <ParamMenu
                  aria={`${kind === "video" ? "视频尺寸选项" : kind === "image" ? "图片尺寸选项" : "音频尺寸选项"}: ${params.size}, Standard-only model`}
                  options={spec.sizeOptions}
                  value={params.size}
                  onChange={(v) => setParams((p) => ({ ...p, size: v }))}
                  width={129}
                  hasPopup="dialog"
                  menuAria="尺寸选项"
                />
                <ParamMenu
                  aria={`生成模式: ${params.mode}`}
                  options={spec.modeOptions}
                  value={params.mode}
                  onChange={(v) => setParams((p) => ({ ...p, mode: v }))}
                  width={80}
                  hasPopup="listbox"
                  menuAria="生成模式选项"
                />
                <ParamMenu
                  aria={
                    kind === "image"
                      ? `选择图片生成张数: ${params.duration}`
                      : `选择${kind === "audio" ? "音频" : "视频"}生成时长: ${params.duration}`
                  }
                  options={spec.durationOptions}
                  value={params.duration}
                  onChange={(v) => setParams((p) => ({ ...p, duration: v }))}
                  width={46}
                  hasPopup="dialog"
                  menuAria="Duration options"
                />
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <span className="text-[12px] text-white/60" title={`Current price ${spec.price}`}>
                  Current price {spec.price}
                </span>
                <button
                  type="button"
                  aria-label="生成"
                  onClick={onGenerate}
                  className="flex items-center justify-center rounded-lg bg-white/[0.12] text-[12px] text-white hover:bg-white/[0.2]"
                  style={{ width: 32, height: 32 }}
                >
                  生成
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>,
    document.body,
  );
}
