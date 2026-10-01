"use client";

import { useEffect, useRef, useState } from "react";
import {
  ArrowUp,
  AtSign,
  AudioLines,
  ChevronDown,
  ChevronRight,
  Image as ImageIcon,
  LayoutGrid,
  Maximize2,
  Play,
  Plus,
  Scan,
  SquarePen,
  User,
  X,
} from "lucide-react";
import { NodeToolbar, Position, useReactFlow } from "@xyflow/react";

import { useJimengStore } from "@/store/jimengStore";
import { VipDiamond } from "@/components/jimeng/icons";
import { FEEDBACK } from "@/components/jimeng/jimengFeedback";

/**
 * 引用 chip (Batch 792 SOURCE_FACT 2026-09-27: 选中画布节点后插入
 * 提示框的 node-composerChip——48×48 缩略图 + 名称 + Remove 角标)。
 */
interface RefChip {
  id: string;
  name: string;
  kind: "image" | "video" | "audio";
  poster?: string;
  /** 视频秒数 → 左下 mm:ss 徽章 (源站 00:06) */
  duration?: number;
}

const REF_CATEGORIES = ["主体", "图片", "视频", "音频"] as const;
type RefCategory = (typeof REF_CATEGORIES)[number];

const CATEGORY_ICONS: Record<RefCategory, typeof User> = {
  主体: User,
  图片: ImageIcon,
  视频: Play,
  音频: AudioLines,
};

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

/**
 * 模型列表 (Batch 41, SOURCE_FACT: 源站模型下拉提取的 8 项，名称+描述)。
 */
const MODELS = [
  // 批 531 SOURCE_FACT (用户手册 20-reference): 模型清单首项为
  // Seedance 2.5 (样片模式)——desc 未采样 CLONE_DECISION
  {
    name: "即梦 Seedance 2.5 样片模式",
    desc: "样片模式，快速预览镜头效果",
  },
  { name: "即梦 Seedance 2.5", desc: "最强模型，支持 50个参考，新增视频编辑、超长生成" },
  { name: "即梦 Seedance 2.0 mini", desc: "极致性价比，相近的体验，比Fast更快的推理速度" },
  { name: "即梦 Seedance 2.0 Fast VIP", desc: "极速推理，会员专属通道，音视文图均可参考（暂不支持真人人脸）" },
  { name: "即梦 Seedance 2.0 VIP", desc: "全模态能力，会员专属通道，音视文图均可参考（暂不支持真人人脸）" },
  { name: "即梦 Seedance 1.0 Fast", desc: "Pro级表现，加量不加价" },
  { name: "MiniMax H3", desc: "开源视频生成模型" },
  { name: "HappyHorse 1.1", desc: "国产视频生成模型" },
  { name: "Wan 3.0", desc: "Wan系列最新视频模型" },
];

/**
 * 空视频节点选中后下方弹出的视频生成面板 (Batch 3；Batch 206 细节对齐)。
 *
 * 证据 (SOURCE_FACT, README §7 + 206-genpanel-detail.json):
 * - 载体 xyflow <NodeToolbar> position=bottom；面板 680×208，节点下方 20px，居中
 * - 本体 form: rgb(32,32,32) r20 内边距 16 (batch 206 复测，原 17)
 * - 三行: 素材栏 h-12 (+ 按钮) / 提示词占位区 (占位 14px，@主体为行内
 *   白/[0.08] chip，批 206；placeholder 属性保留供 a11y/验证器，视觉置透明)
 * - 底部行 h-8: 即梦 Seedance 2.0 VIP ✦∨ · 16:9·720P ✦·1∨ · 全能参考∨ · 4s∨
 *   · @ (控件 12px，批 206 复测)
 * - 底部行右组: 「Current price」标签 + ✦56.56 (白/[0.69]，70px 裁切容器，
 *   源站自身即截断显示——批 206) + 32px 圆形发送钮 bg 白/16 禁用态
 *   (sr-only "请输入提示词")
 * - 右上角 40×40 展开钮 (icon 24, white/60)
 * mock: 提示词可输入、下拉不开合 (Batch 5 接 store)。
 */
export function JimengGenPanel({
  visible,
  nodeId,
}: {
  visible: boolean;
  nodeId: string;
}) {
  // Batch 40/50: 提示词可输入；发送 → generateInto (mock 全流程)
  const [prompt, setPrompt] = useState("");
  const generateInto = useJimengStore((s) => s.generateInto);
  // Batch 41/61: 模型下拉，选择持久化到 store
  const [modelOpen, setModelOpen] = useState(false);
  const model = useJimengStore((s) => s.genModel);
  const setGenModel = useJimengStore((s) => s.setGenModel);
  // Batch 42: 比例/分辨率/数量 + 参考模式 + 时长 (SOURCE_FACT batch 42 提取)
  const [openMenu, setOpenMenu] = useState<string | null>(null);
  const [ratio, setRatio] = useState("16:9");
  const [resolution, setResolution] = useState("720P");
  const [count, setCount] = useState("1");
  const [reference, setReference] = useState("全能参考");
  const [duration, setDuration] = useState("4s");
  // Batch 792 SOURCE_FACT (2026-09-27 深采, 替代批 688 行内条方案):
  // 引用参考钮 → 提示框插入 "@" + 弹「可能@的内容」自动补全弹层
  // (候选区 + 添加参考分区: 主体/图片/视频/音频 四行下钻)；点子菜单
  // 行 → 插入引用 chip (48×48 缩略图 + 名称 + Remove 角标)；chip 行
  // 横向堆叠于素材栏。
  const [refMenuOpen, setRefMenuOpen] = useState(false);
  const [refSubmenu, setRefSubmenu] = useState<RefCategory | null>(null);
  const [refChips, setRefChips] = useState<RefChip[]>([]);
  // Batch 793 SOURCE_FACT: chip 行 添加参考钮 → 三选项菜单 (上传参考
  // 内容 / 从资产库添加 / 从画布选择)；从画布选择进入点选模式
  const [addRefMenuOpen, setAddRefMenuOpen] = useState(false);
  const uploadInputRef = useRef<HTMLInputElement>(null);
  const jimengNodes = useJimengStore((s) => s.nodes);
  const pushToast = useJimengStore((s) => s.pushToast);
  const setAssetsOpen = useJimengStore((s) => s.setAssetsOpen);
  const startRefPicking = useJimengStore((s) => s.startRefPicking);
  const pickedRefNodeId = useJimengStore((s) => s.pickedRefNodeId);
  const clearPickedRefNode = useJimengStore((s) => s.clearPickedRefNode);
  const { screenToFlowPosition } = useReactFlow();
  const addLocalUpload = useJimengStore((s) => s.addLocalUpload);
  const mediaNodes = jimengNodes
    .filter(
      (n): n is typeof n & { type: "image" | "video" | "audio" } =>
        n.type === "image" || n.type === "video" || n.type === "audio",
    )
    .map((n) => {
      const data = n.data as { title?: string; poster?: string; duration?: number };
      return {
        id: n.id,
        kind: n.type,
        name: data.title ?? n.id,
        poster: data.poster,
        duration: data.duration,
      };
    });
  const insertChip = (node: (typeof mediaNodes)[number]) => {
    setRefChips((chips) =>
      chips.some((c) => c.id === node.id)
        ? chips
        : [...chips, { id: node.id, name: node.name, kind: node.kind, poster: node.poster, duration: node.duration }],
    );
    setPrompt((p) => p.replace(/@$/, ""));
    setRefMenuOpen(false);
    setRefSubmenu(null);
  };
  // Batch 793: 点选模式选中节点 → 插 chip + 「添加完成」提示
  useEffect(() => {
    if (pickedRefNodeId === null) return;
    const node = mediaNodes.find((n) => n.id === pickedRefNodeId);
    if (node) {
      insertChip(node);
      pushToast("添加完成");
    }
    clearPickedRefNode();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- mediaNodes 随渲染重建，仅在 pickedRefNodeId 变化时消费
  }, [pickedRefNodeId]);
  const submenuNodes =
    refSubmenu === null
      ? []
      : mediaNodes.filter((n) =>
          refSubmenu === "主体"
            ? false
            : refSubmenu === "图片"
              ? n.kind === "image"
              : refSubmenu === "视频"
                ? n.kind === "video"
                : n.kind === "audio",
        );
  const canSend = prompt.trim().length > 0;

  return (
    <NodeToolbar isVisible={visible} position={Position.Bottom} offset={20}>
      <div className="relative h-[208px] w-[680px]">
        {/* 右上角展开钮 (骑在面板顶边) */}
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
          className="flex h-full w-full flex-col justify-between rounded-[20px] bg-[#202020] p-4"
          onSubmit={(e) => {
            e.preventDefault();
            if (!canSend) return;
            generateInto(nodeId, prompt);
            pushToast(FEEDBACK.taskSubmitted("生成"));
            setPrompt("");
          }}
        >
          {/* 素材栏 */}
          <div className="flex h-12 w-full items-center">
            {refChips.length > 0 ? (
              /* Batch 792 SOURCE_FACT: 引用 chip 行 (48×48 缩略图 +
                  Remove 角标) + 添加参考钮, 横向堆叠 */
              <div className="flex h-12 w-full items-center gap-1.5" data-testid="ref-chip-row">
                {refChips.map((chip) => (
                  <div
                    key={chip.id}
                    className="relative size-11 shrink-0 rounded-xl border border-white/10 bg-white/[0.06]"
                    aria-label={`Reference material: ${chip.name}`}
                  >
                    {chip.poster ? (
                      <img src={chip.poster} alt="" className="size-full rounded-xl object-cover" />
                    ) : (
                      <span className="flex size-full items-center justify-center text-white/50">
                        {chip.kind === "image" ? <ImageIcon size={18} /> : chip.kind === "video" ? <Play size={18} /> : <AudioLines size={18} />}
                      </span>
                    )}
                    {chip.kind === "video" && chip.duration ? (
                      <span className="absolute bottom-0.5 left-0.5 rounded bg-black/70 px-1 text-[9px] leading-[14px] text-white/90">
                        {formatDuration(chip.duration)}
                      </span>
                    ) : null}
                    <button
                      type="button"
                      aria-label={`Remove ${chip.name}`}
                      onClick={() => setRefChips((chips) => chips.filter((c) => c.id !== chip.id))}
                      className="absolute -right-1 -top-1 flex size-4 items-center justify-center rounded-full bg-[#2a2a2a] text-white/70 ring-1 ring-white/15 hover:text-white"
                    >
                      <X size={10} />
                    </button>
                  </div>
                ))}
                <div className="relative shrink-0">
                  <button
                    type="button"
                    aria-label="添加参考"
                    aria-pressed={addRefMenuOpen}
                    onClick={() => setAddRefMenuOpen((v) => !v)}
                    className="flex size-11 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/[0.06] text-white/80 hover:bg-white/10"
                  >
                    <Plus size={20} />
                  </button>
                  {addRefMenuOpen ? (
                    /* Batch 793 SOURCE_FACT: 三选项菜单 */
                    <div
                      className="absolute bottom-[calc(100%+8px)] left-0 z-[140] w-[232px] rounded-[10px] border border-white/[0.06] p-1"
                      style={{ background: "rgb(38,38,38)" }}
                      data-testid="addref-menu"
                    >
                      {[
                        { label: "上传参考内容", icon: SquarePen },
                        { label: "从资产库添加", icon: LayoutGrid },
                        { label: "从画布选择", icon: Scan },
                      ].map(({ label, icon: Icon }) => (
                        <button
                          key={label}
                          type="button"
                          onClick={() => {
                            setAddRefMenuOpen(false);
                            if (label === "上传参考内容") {
                              uploadInputRef.current?.click();
                            } else if (label === "从资产库添加") {
                              setAssetsOpen(true);
                            } else {
                              startRefPicking();
                            }
                          }}
                          className="flex h-[38px] w-full items-center gap-2 rounded-lg px-2.5 text-left text-[13px] text-white/90 hover:bg-white/10"
                        >
                          <Icon size={15} className="shrink-0 text-white/70" />
                          {label}
                        </button>
                      ))}
                    </div>
                  ) : null}
                </div>
              </div>
            ) : (
              <button
                type="button"
                aria-label="上传参考图"
                className="flex size-11 items-center justify-center rounded-xl border border-white/10 bg-white/[0.06] text-white/80 hover:bg-white/10"
              >
                <Plus size={20} />
              </button>
            )}
            {refMenuOpen ? (
              /* Batch 792 SOURCE_FACT: 「可能@的内容」@ 自动补全弹层
                  (批 688 行内条方案已被源站真态替代) */
              <div
                className="absolute bottom-[calc(100%-8px)] left-0 z-[140] flex w-[336px] rounded-[10px] border border-white/[0.06] p-1.5"
                style={{ background: "rgb(38,38,38)" }}
                data-testid="ref-menu"
              >
                <div className="min-w-0 flex-1">
                  <p className="px-2.5 pb-1 pt-1.5 text-[12px] text-white/40">可能@的内容</p>
                  {mediaNodes.map((node) => (
                    <button
                      key={node.id}
                      type="button"
                      onClick={() => insertChip(node)}
                      className="flex h-10 w-full items-center gap-2 rounded-lg px-2.5 text-left hover:bg-white/10"
                    >
                      {node.poster ? (
                        <img src={node.poster} alt="" className="size-8 shrink-0 rounded-md object-cover" />
                      ) : (
                        <span className="flex size-8 shrink-0 items-center justify-center rounded-md bg-white/[0.08] text-white/55">
                          {node.kind === "image" ? <ImageIcon size={14} /> : node.kind === "video" ? <Play size={14} /> : <AudioLines size={14} />}
                        </span>
                      )}
                      <span className="min-w-0 flex-1 truncate text-[13px] text-white/90">{node.name}</span>
                    </button>
                  ))}
                  <p className="px-2.5 pb-1 pt-2 text-[12px] text-white/40">添加参考</p>
                  {REF_CATEGORIES.map((cat) => {
                    const Icon = CATEGORY_ICONS[cat];
                    return (
                      <button
                        key={cat}
                        type="button"
                        aria-pressed={refSubmenu === cat}
                        onClick={() => setRefSubmenu((cur) => (cur === cat ? null : cat))}
                        className={`flex h-10 w-full items-center gap-2 rounded-lg px-2.5 text-left hover:bg-white/10 ${
                          refSubmenu === cat ? "bg-white/[0.10]" : ""
                        }`}
                      >
                        <Icon size={15} className="shrink-0 text-white/70" />
                        <span className="min-w-0 flex-1 truncate text-[13px] text-white/90">{cat}</span>
                        <ChevronRight size={14} className="shrink-0 text-white/40" />
                      </button>
                    );
                  })}
                </div>
                {refSubmenu !== null ? (
                  /* Batch 792 SOURCE_FACT: 类别下钻子菜单 (48px 行 +
                      32px 缩略图 + 视频时长徽章; 空类别「暂无相关节点」) */
                  <div
                    className="ml-1 flex w-[248px] flex-col rounded-[10px] border border-white/[0.06] p-1.5"
                    style={{ background: "rgb(38,38,38)" }}
                    data-testid="ref-submenu"
                  >
                    {submenuNodes.length > 0 ? (
                      submenuNodes.map((node) => (
                        <button
                          key={node.id}
                          type="button"
                          onClick={() => insertChip(node)}
                          className="relative flex h-12 w-full items-center gap-2 rounded-lg px-1.5 text-left hover:bg-white/10"
                        >
                          {node.poster ? (
                            <img src={node.poster} alt="" className="size-8 shrink-0 rounded-md object-cover" />
                          ) : (
                            <span className="flex size-8 shrink-0 items-center justify-center rounded-md bg-white/[0.08] text-white/55">
                              {node.kind === "image" ? <ImageIcon size={14} /> : node.kind === "video" ? <Play size={14} /> : <AudioLines size={14} />}
                            </span>
                          )}
                          <span className="min-w-0 flex-1 truncate text-[13px] text-white/90">{node.name}</span>
                          {node.kind === "video" && node.duration ? (
                            <span className="shrink-0 rounded bg-black/70 px-1 text-[9px] leading-[14px] text-white/90">
                              {formatDuration(node.duration)}
                            </span>
                          ) : null}
                        </button>
                      ))
                    ) : (
                      <div className="flex h-16 items-center justify-center text-[13px] text-white/45">
                        暂无相关节点
                      </div>
                    )}
                    {refSubmenu === "视频" ? (
                      /* Batch 791 SOURCE_FACT: 视频子菜单的 展开视频生成器 入口 */
                      <button
                        type="button"
                        aria-label="展开视频生成器"
                        className="mt-auto flex size-10 items-center justify-center self-end rounded-lg text-white/60 hover:bg-white/10"
                      >
                        <Maximize2 size={16} />
                      </button>
                    ) : null}
                  </div>
                ) : null}
              </div>
            ) : null}
          </div>

          {/* 提示词输入区 (Batch 40: 可编辑)。批 206: 占位 14px + @主体
              行内 chip——视觉由叠加层渲染，textarea placeholder 属性保留
              (a11y/验证器)，占位色置透明避免双重显示 */}
          <div className="relative flex w-full items-start">
            {!canSend ? (
              <div className="pointer-events-none absolute inset-0 flex items-start text-[14px] leading-[24px] text-white/35">
                <span className="whitespace-nowrap">上传参考图、输入文字或</span>
                <span className="mx-1 inline-flex shrink-0 items-center gap-0.5 self-start rounded bg-white/[0.08] px-1 text-white/55">
                  <AtSign size={10} />
                  主体
                </span>
                <span className="whitespace-nowrap">，描述你想生成的视频</span>
              </div>
            ) : null}
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="上传参考图、输入文字或 @ 主体，描述你想生成的视频"
              rows={2}
              className="w-full resize-none bg-transparent text-[13px] leading-[22px] text-white outline-none placeholder:text-transparent"
            />
          </div>

          {/* 底部控制行 */}
          <div className="flex h-8 w-full items-center justify-between gap-1">
            <div className="flex min-w-0 items-center gap-1">
              <div className="relative">
                <button
                  type="button"
                  aria-label="选择模型: 即梦 Seedance 2.0 VIP, Standard-only model"
                  onClick={() => setModelOpen((v) => !v)}
                  className="flex h-8 items-center gap-1 whitespace-nowrap rounded-lg px-2 text-[12px] text-white/90 hover:bg-white/[0.08]"
                >
                  {model}
                  <VipDiamond size={12} />
                  <ChevronDown size={12} className="text-white/60" />
                </button>
                {modelOpen ? (
                  <div
                    className="absolute bottom-[calc(100%+8px)] left-0 z-[140] w-[392px] rounded-[10px] border border-white/[0.06] p-1.5"
                    style={{ background: "rgb(38,38,38)" }}
                    role="listbox"
                    aria-label="模型列表"
                  >
                    {MODELS.map((m) => (
                      <button
                        key={m.name}
                        type="button"
                        role="option"
                        aria-selected={model === m.name}
                        onClick={() => {
                          setGenModel(m.name);
                          setModelOpen(false);
                        }}
                        className={`flex w-full flex-col items-start gap-0.5 rounded-lg px-2.5 py-2 text-left hover:bg-white/10 ${
                          model === m.name ? "bg-white/[0.08]" : ""
                        }`}
                      >
                        <span className="text-[13px] font-medium text-white">
                          {m.name}
                        </span>
                        <span className="text-[12px] leading-4 text-white/45">
                          {m.desc}
                        </span>
                      </button>
                    ))}
                  </div>
                ) : null}
              </div>
              {/* 比例/分辨率/数量 组合菜单 (SOURCE_FACT batch 42: 三组选项) */}
              <div className="relative">
                <button
                  type="button"
                  aria-label="视频尺寸选项: 16:9 · 720P · 1, Standard-only model"
                  onClick={() => setOpenMenu(openMenu === "ratio" ? null : "ratio")}
                  className="flex h-8 items-center gap-1 whitespace-nowrap rounded-lg px-2 text-[12px] text-white/90 hover:bg-white/[0.08]"
                >
                  {ratio} · {resolution}
                  <VipDiamond size={12} />
                  · {count}
                  <ChevronDown size={12} className="text-white/60" />
                </button>
                {openMenu === "ratio" ? (
                  <div
                    className="absolute bottom-[calc(100%+8px)] left-0 z-[140] flex w-[334px] gap-4 rounded-[10px] border border-white/[0.06] p-3"
                    style={{ background: "rgb(38,38,38)" }}
                    role="listbox"
                    aria-label="视频尺寸选项: 16:9 · 720P · 1, Standard-only model"
                  >
                    {[
                      { title: "选择比例", key: "ratio", options: ["21:9", "16:9", "4:3", "1:1", "3:4", "9:16"] },
                      { title: "选择分辨率", key: "resolution", options: ["720P", "1080P", "4K"] },
                      { title: "选择生成数量", key: "count", options: ["1", "2", "3", "4"] },
                    ].map((group) => (
                      <div key={group.key} className="flex flex-col gap-0.5">
                        <p className="text-[12px] text-white/40">{group.title}</p>
                        {group.options.map((opt) => (
                          <button
                            key={opt}
                            type="button"
                            role="option"
                            aria-selected={
                              (group.key === "ratio" ? ratio : group.key === "resolution" ? resolution : count) === opt
                            }
                            onClick={() => {
                              if (group.key === "ratio") setRatio(opt);
                              if (group.key === "resolution") setResolution(opt);
                              if (group.key === "count") setCount(opt);
                              setOpenMenu(null);
                            }}
                            className={`flex h-7 items-center rounded-md px-2 text-[12px] ${
                              (group.key === "ratio" ? ratio : group.key === "resolution" ? resolution : count) === opt
                                ? "bg-white/[0.12] text-white"
                                : "text-white/75 hover:bg-white/10"
                            }`}
                          >
                            {opt}
                          </button>
                        ))}
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
              {/* 全能参考切换 (SOURCE_FACT batch 42: 首尾帧/全能参考 两项) */}
              <div className="relative">
                <button
                  type="button"
                  aria-label="生成模式: 全能参考"
                  onClick={() => setOpenMenu(openMenu === "ref" ? null : "ref")}
                  className="flex h-8 items-center gap-1 whitespace-nowrap rounded-lg px-2 text-[12px] text-white/90 hover:bg-white/[0.08]"
                >
                  {reference}
                  <ChevronDown size={12} className="text-white/60" />
                </button>
                {openMenu === "ref" ? (
                  <div
                    className="absolute bottom-[calc(100%+8px)] left-0 z-[140] w-[192px] rounded-[10px] border border-white/[0.06] p-1.5"
                    style={{ background: "rgb(38,38,38)" }}
                    role="listbox"
                    aria-label="生成模式: 全能参考"
                  >
                    {["首尾帧", "全能参考"].map((opt) => (
                      <button
                        key={opt}
                        type="button"
                        role="option"
                        aria-selected={reference === opt}
                        onClick={() => {
                          setReference(opt);
                          setOpenMenu(null);
                        }}
                        className={`flex h-10 w-full items-center rounded-lg px-2.5 text-[13px] ${
                          reference === opt ? "bg-white/[0.10] text-white" : "text-white/75 hover:bg-white/10"
                        }`}
                      >
                        {opt}
                      </button>
                    ))}
                  </div>
                ) : null}
              </div>
              {/* 时长 (Batch 42: 4s/8s/12s, CLONE_DECISION 8s/12s 推断) */}
              <div className="relative">
                <button
                  type="button"
                  aria-label="选择视频生成时长: 4s"
                  onClick={() => setOpenMenu(openMenu === "dur" ? null : "dur")}
                  className="flex h-8 items-center gap-1 whitespace-nowrap rounded-lg px-2 text-[12px] text-white/90 hover:bg-white/[0.08]"
                >
                  {duration}
                  <ChevronDown size={12} className="text-white/60" />
                </button>
                {openMenu === "dur" ? (
                  <div
                    className="absolute bottom-[calc(100%+8px)] left-0 z-[140] w-[120px] rounded-[10px] border border-white/[0.06] p-1.5"
                    style={{ background: "rgb(38,38,38)" }}
                    role="listbox"
                    aria-label="选择视频生成时长: 4s"
                  >
                    {["4s", "8s", "12s"].map((opt) => (
                      <button
                        key={opt}
                        type="button"
                        role="option"
                        aria-selected={duration === opt}
                        onClick={() => {
                          setDuration(opt);
                          setOpenMenu(null);
                        }}
                        className={`flex h-10 w-full items-center rounded-lg px-2.5 text-[13px] ${
                          duration === opt ? "bg-white/[0.10] text-white" : "text-white/75 hover:bg-white/10"
                        }`}
                      >
                        {opt}
                      </button>
                    ))}
                  </div>
                ) : null}
              </div>
              {/* 批 403 SOURCE_FACT: 行内图标钮 aria 实测 引用参考;
                  批 792 SOURCE_FACT (2026-09-27 深采): 点击 = 提示框
                  插入 "@" + 弹「可能@的内容」自动补全弹层 */}
              <button
                type="button"
                aria-label="引用参考"
                aria-pressed={refMenuOpen}
                onClick={() => {
                  setPrompt((p) => (p.endsWith("@") ? p : `${p}@`));
                  setRefSubmenu(null);
                  setRefMenuOpen((v) => !v);
                }}
                className={`flex size-8 items-center justify-center rounded-lg hover:bg-white/[0.08] ${
                  refMenuOpen ? "bg-white/[0.14] text-white" : "text-white/80"
                }`}
              >
                <AtSign size={15} />
              </button>
            </div>

            <div className="flex h-8 shrink-0 items-center gap-2">
              {/* 批 384 SOURCE_FACT (384-empty-gen-panel.json): 价格签已演进
                  为紧凑态「✦ + 整数」(56)——精确值「Current price 56.56」
                  为 1px 裁切隐藏叶 (与批 368 音频面板同族)；激活态 #fafafa
                  同批 370 */}
              <span
                className="flex h-8 items-center gap-1.5 text-[13px] text-white/85"
                title="Current price 56.56"
              >
                <VipDiamond size={12} />
                56
                <span className="w-px overflow-hidden whitespace-nowrap text-[12px] text-white/[0.6]">
                  Current price 56.56
                </span>
              </span>
              <button
                type="submit"
                aria-label="生成"
                disabled={!canSend}
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
          {/* Batch 793: 上传参考内容 的隐藏文件入口 (同左栏上传链路) */}
          <input
            ref={uploadInputRef}
            type="file"
            multiple
            accept="video/*,image/*,audio/*"
            className="hidden"
            data-testid="panel-upload-input"
            onChange={(e) => {
              const files = Array.from(e.target.files ?? []);
              const el = document.querySelector(".jimeng-canvas");
              const center = screenToFlowPosition({
                x: el ? el.clientWidth / 2 : window.innerWidth / 2,
                y: el ? el.clientHeight / 2 : window.innerHeight / 2,
              });
              files.forEach((file, i) => {
                addLocalUpload(file.name, {
                  x: center.x - 284.5 + i * 40,
                  y: center.y - 160 + i * 40,
                });
              });
              e.target.value = "";
            }}
          />
        </form>
      </div>
    </NodeToolbar>
  );
}
