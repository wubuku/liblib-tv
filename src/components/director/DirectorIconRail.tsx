"use client";

import { Fragment, useRef, useState, type ChangeEvent } from "react";
import {
  ArrowDownToLine,
  Boxes,
  Circle,
  Clapperboard,
  Cylinder,
  HelpCircle,
  History,
  Image as ImageIcon,
  Plus,
  Sparkles,
  Proportions,
  Triangle,
  Upload,
  UserRoundPlus,
  Layers,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useDirectorStore } from "@/store/directorStore";
import { DirectorAiImportModal } from "@/components/director/DirectorAiImportModal";
import { readDirectorLocalModelFiles } from "@/components/director/directorLocalModelImport";

// Batch 536: 2026-09-27 源站采样（liblib-source-exploration-2026-09-25
// NOTES §8 + 截图 18）——3D 导演台最左窄图标栏（约 46px）。
// Batch 537: 同日 CDP DOM 补采修正——rail 实际七入口（aria-label 实证）：
// 场景 / 添加角色 / 添加机位 / 全景图 / 选择画幅比例 / AI 识图导入 +
// 底部帮助（? 圆钮）。仅场景（场景树）与添加角色 flyout 在 clone 有实现；
// 添加机位为直接动作（无面板采样），其余面板未采样（SOURCE_UNCERTAIN）
// 做视觉切换不导航（CLONE_DECISION）。
// Batch 538: 2026-09-27 已存截图转录——全景图 flyout = 本地上传/历史记录/
// AI生成（44-director-rail-25，batch 589 DOM 复核确认无空格）；选择画幅比例 =
// 自适应（默认激活）/
// 21:9/16:9/4:3/1:1/3:4/9:16 七卡单选（44-director-rail-26）。
// AI生成/AI 识图为付费 AI 动作，clone 仅可视不触发。
const railEntries = [
  { id: "scene", label: "场景", icon: Layers, kind: "panel" },
  { id: "add-character", label: "添加角色", icon: UserRoundPlus, kind: "flyout" },
  { id: "add-camera", label: "添加机位", icon: Clapperboard, kind: "action" },
  { id: "panorama", label: "全景图", icon: ImageIcon, kind: "flyout" },
  { id: "aspect-ratio", label: "选择画幅比例", icon: Proportions, kind: "flyout" },
  { id: "ai-import", label: "AI 识图导入", icon: ArrowDownToLine, kind: "modal" },
] as const;

// 添加角色 flyout 菜单（截图 44-director-rail-23 DOM/视觉转录）。
const characterFlyout = [
  { id: "local-upload", label: "本地上传", kind: "upload" as const },
  { id: "standard-male", label: "标准男性", kind: "preset" as const },
  { id: "standard-female", label: "标准女性", kind: "preset" as const },
  { id: "muscular", label: "健硕", kind: "preset" as const },
  { id: "slim", label: "纤细", kind: "preset" as const },
  { id: "teen", label: "少年", kind: "preset" as const },
  { id: "child", label: "儿童", kind: "preset" as const },
  { id: "broad", label: "宽厚", kind: "preset" as const },
  { id: "chibi", label: "二头身", kind: "preset" as const },
  { id: "crowd-3x3", label: "群众 (3x3)", kind: "submenu" as const },
  { id: "geometry", label: "几何模型", kind: "submenu" as const },
];

// 全景图 flyout（源站 2026-10-01 DOM 复核：232×96 @(48,100)，三项行距
// 32px）。Batch 589 修正文案：逐字是「AI生成」——**无空格**，batch 538
// 从截图转录时记成了「AI 生成」。
const panoramaFlyout = [
  { id: "local-upload", label: "本地上传", icon: Upload },
  { id: "history", label: "历史记录", icon: History },
  { id: "ai-generate", label: "AI生成", icon: Sparkles },
] as const;

// 选择画幅比例（截图 44-director-rail-26 转录）：七卡单选，自适应默认。
const aspectRatios = [
  "自适应",
  "21:9",
  "16:9",
  "4:3",
  "1:1",
  "3:4",
  "9:16",
] as const;

// Batch 590（源站 2026-10-01 实测）：七张卡的示意框尺寸逐项对齐。
// 注意源站 `3:4` 与 `9:16` 实测**同为 8×16**（看起来是源站自身的取整
// 结果），clone 按实测照抄，不按比例自行「修正」。
const ASPECT_GLYPH: Record<(typeof aspectRatios)[number], string> = {
  自适应: "h-[11px] w-4",
  "21:9": "h-[7px] w-4",
  "16:9": "h-[9px] w-4",
  "4:3": "h-3 w-4",
  "1:1": "h-[14px] w-[14px]",
  "3:4": "h-4 w-2",
  "9:16": "h-4 w-2",
};

// Batch 590（源站 2026-10-01 实测）：`几何模型` 子菜单在**父项下方**展开
// （204×256，八项各 199×32、行距 32px），不在右侧。
const geometrySubmenu = [
  { id: "geometry-upload", label: "上传文件", icon: Upload },
  { id: "cube", label: "立方体", icon: Boxes },
  { id: "sphere", label: "球体", icon: Circle },
  { id: "cylinder", label: "圆柱体", icon: Cylinder },
  { id: "torus", label: "环状体", icon: Circle },
  { id: "cone", label: "圆锥", icon: Triangle },
  { id: "pyramid", label: "棱锥", icon: Triangle },
  { id: "empty-object", label: "添加空对象", icon: Plus },
] as const;

// Batch 590（源站 2026-10-01 实测）：`群众 (3x3)` 打开的是弹窗而非直接
// 出结果——220×204 @(280,388)，标题 `添加群众阵列`、右上角 `共N人` 计数、
// 三个数字输入 行数/列数/间距（量程见 CROWD_LIMITS），页脚 取消 / 添加
// （`添加` 为白底主按钮）。
const CROWD_LIMITS = {
  rows: { min: 1, max: 10 },
  columns: { min: 1, max: 10 },
  spacing: { min: 0.1, max: 10 },
} as const;

// Batch 589（源站 2026-10-01 实测）：三个 flyout 面板实测宽度**一致为
// 232px**（@(48,100)），且每个面板顶部都有一行 12px `truncate` 的标题
// （`添加角色` @(60,66) 48×20）。另注：rail 按钮 hover 会弹一个 Mantine
// `Tooltip-tooltip`（@(45,118) 64×28），与面板标题是两件事。
const FLYOUT_WIDTH = "w-[232px]";
const FLYOUT_CARD_CLASS =
  "rounded-xl border border-white/10 bg-[#242424] shadow-[0_16px_40px_rgba(0,0,0,0.5)]";
// 标题行在卡片**之外**（源站 `添加角色` 标题 @(60,66)，卡片从 y=100 起），
// 故外层定位容器同时承载标题与卡片。
const FLYOUT_TITLE_CLASS = "block truncate px-3 pb-2 text-xs text-[#8a8a8a]";

export function DirectorIconRail({
  onPanoramaSourceChange,
}: {
  onPanoramaSourceChange?: (sourceNodeId: string | null) => void;
} = {}) {
  const [active, setActive] = useState<string>("scene");
  const [openFlyout, setOpenFlyout] = useState<string | null>(null);
  const [aspectRatio, setAspectRatio] = useState<string>("自适应");
  // Batch 539: AI 识图导入 打开居中模态。
  const [aiImportOpen, setAiImportOpen] = useState(false);
  // Batch 540: 源站 rail「添加机位」为直接动作（点击无面板）——
  // 与场景树「新增机位」同源，接通 directorStore.addDirectorCamera。
  const addDirectorCamera = useDirectorStore((state) => state.addDirectorCamera);
  // Batch 541: 添加角色 flyout——群众 (3x3) 接通本地等效 addCrowdArray
  // （与 DirectorViewport 群众面板同默认 3/3/1.2）；预设体型项为本地等效
  // 占位（store 无单角色变体加建），点击仅回显本地提示，不生成 3D 模型。
  const addCrowdArray = useDirectorStore((state) => state.addCrowdArray);
  // Batch 542: 本地上传 复用导演台本地模型库导入管线（batch 537 采样菜单项；
  // 与 DirectorViewport 模型库导入同 readDirectorLocalModelFiles 管线）。
  const addLocalModelLibraryItem = useDirectorStore(
    (state) => state.addLocalModelLibraryItem,
  );
  // Batch 587: rail「场景」兼作收起态的恢复入口（源站收起后浮层内唯一
  // 能把顶栏 + 左侧场景面板叫回来的控件）。
  const setViewportPanelsCollapsed = useDirectorStore(
    (state) => state.setViewportPanelsCollapsed,
  );
  const characterUploadInputRef = useRef<HTMLInputElement | null>(null);
  const [characterAck, setCharacterAck] = useState<string | null>(null);
  // Batch 590: 群众弹窗 + 几何模型子菜单（源站实测）
  const [crowdDialogOpen, setCrowdDialogOpen] = useState(false);
  const [crowdDraft, setCrowdDraft] = useState({ rows: 3, columns: 3, spacing: 1.2 });
  const [geometrySubmenuOpen, setGeometrySubmenuOpen] = useState(false);

  const flashCharacterAck = (message: string) => {
    setCharacterAck(message);
    window.setTimeout(() => setCharacterAck(null), 2000);
  };

  const handleCharacterUploadChange = async (
    event: ChangeEvent<HTMLInputElement>,
  ) => {
    const input = event.currentTarget;
    try {
      const items = await readDirectorLocalModelFiles(input.files ?? []);
      if (items.length === 0) {
        flashCharacterAck("未选择可用模型文件");
        return;
      }
      items.forEach(addLocalModelLibraryItem);
      flashCharacterAck(`已导入 ${items.length} 个本地模型至模型库`);
    } finally {
      input.value = "";
    }
  };

  const select = (id: string) => {
    if (id === "ai-import") {
      setAiImportOpen(true);
      return;
    }
    if (id === "add-camera") {
      addDirectorCamera();
      return;
    }
    setOpenFlyout(null);
    // Batch 587（源站 2026-10-01 实测）：收起之后顶栏与「收起」按钮一并
    // 消失，浮层内没有第二个恢复按钮——点图标栏的「场景」条目即恢复
    // 顶栏与左侧场景面板。图标栏本身在收起态保留。
    if (id === "scene") {
      setViewportPanelsCollapsed(false);
    }
    if (id === "add-character") {
      // 仅 add-character 自身打开 flyout；由 handleCharacterOption 控制关闭。
      setOpenFlyout("add-character");
      return;
    }
    setActive(id);
    if (id === "panorama" || id === "aspect-ratio") {
      setOpenFlyout(id);
    }
  };

  const handleCharacterOption = (itemId: string, label: string) => {
    // Batch 590（源站 2026-10-01 实测）：源站的两个子菜单项各自带面板，
    // 不是点一下就出结果——
    //   群众 (3x3) -> 弹窗「添加群众阵列」(220×204) 含 行数/列数/间距
    //   几何模型   -> 展开 8 项子菜单（上传文件 + 6 种几何体 + 添加空对象）
    if (itemId === "crowd-3x3") {
      // 源站的弹窗是**并排**出现在 flyout 右侧（@(280,388)，flyout 占
      // 48..280），flyout 保持打开；clone 此前是直接关掉 flyout。
      setOpenFlyout("add-character");
      setCrowdDialogOpen(true);
      return;
    }
    if (itemId === "local-upload") {
      setOpenFlyout(null);
      characterUploadInputRef.current?.click();
      return;
    }
    if (itemId === "geometry") {
      setGeometrySubmenuOpen((open) => !open);
      return;
    }
    setCharacterAck(`预设角色「${label}」为本地等效占位`);
    setOpenFlyout(null);
    window.setTimeout(() => setCharacterAck(null), 2000);
  };

  const handleGeometryOption = (optionId: string, label: string) => {
    setGeometrySubmenuOpen(false);
    if (optionId === "geometry-upload") {
      characterUploadInputRef.current?.click();
      return;
    }
    setCharacterAck(`几何体「${label}」为本地等效占位`);
    window.setTimeout(() => setCharacterAck(null), 2000);
  };

  const confirmCrowdArray = () => {
    addCrowdArray(crowdDraft);
    setCrowdDialogOpen(false);
    setCharacterAck(
      `已加入群众 ${crowdDraft.rows}×${crowdDraft.columns}（间距 ${crowdDraft.spacing}）`,
    );
    window.setTimeout(() => setCharacterAck(null), 2000);
  };

  return (
    <div
      data-director-icon-rail
      aria-label="导演台资源栏"
      // Batch 602（源站 2026-10-01 实测，/tmp/src593/probe50）：
      // 源站 rail 是 `<nav>`，`border-white/8 flex w-12 shrink-0 flex-col
      // items-center gap-2 border-r p-2` —— 48px 宽、**gap 2(8px)**、四周
      // `p-2`，底色 `#171717`，右边框 `white/8`。clone 原先是 46px /
      // gap-1 / py-3 / `#1a1a1a` / `white/[0.07]`，节奏密了 4px、底色偏浅。
      className="absolute inset-y-0 left-0 z-30 hidden w-12 shrink-0 flex-col items-center gap-2 border-r border-white/8 bg-[#171717] p-2 min-[900px]:flex"
    >
      {/* 源站节奏：gap-2（8px）。`场景` 与 `添加角色` 之间还夹一条
          `<div class="border-white/8 h-2 w-8 border-b">` 分隔线（32×8
          @(8,100)）——加上上下各 8px 的 gap，正好把 添加角色 顶到 y=116。 */}
      <div className="flex flex-col items-center gap-2">
        {railEntries.map((entry, index) => {
          const Icon = entry.icon;
          const isActive = active === entry.id;
          return (
            <Fragment key={entry.id}>
            <div className="relative">
              <button
                type="button"
                data-director-rail-entry={entry.id}
                aria-label={entry.label}
                title={entry.label}
                aria-pressed={isActive}
                onClick={() => select(entry.id)}
                // 源站逐字：`text-white/72 hover:bg-white/8 flex size-8
                // items-center justify-center rounded-lg transition-colors
                // hover:text-white`，选中态叠 `bg-white/10 text-white`。
                className={cn(
                  "flex size-8 items-center justify-center rounded-lg text-white/72 transition-colors",
                  "hover:bg-white/8 hover:text-white",
                  isActive && "bg-white/10 text-white",
                )}
              >
                <Icon size={20} />
              </button>
              {entry.id === "add-character" && openFlyout === "add-character" && (
                <div
                  data-director-character-flyout
                  aria-label="添加角色"
                  className={cn(
                    "absolute left-[calc(100%+8px)] top-0 z-40",
                    FLYOUT_WIDTH,
                  )}
                >
                  <span
                    data-director-flyout-title="add-character"
                    className={FLYOUT_TITLE_CLASS}
                  >
                    添加角色
                  </span>
                  <div className={cn(FLYOUT_CARD_CLASS, "p-1.5")}>
                  {characterFlyout.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      data-director-character-option={item.id}
                      onClick={() => handleCharacterOption(item.id, item.label)}
                      className="flex h-8 w-full items-center gap-2 rounded-lg px-2 text-left text-xs text-[#d8d8d8] hover:bg-white/[0.07]"
                    >
                      <span className="min-w-0 flex-1 truncate">{item.label}</span>
                      {item.kind === "submenu" && (
                        <span aria-hidden="true" className="text-[10px] text-[#777]">›</span>
                      )}
                    </button>
                  ))}
                  {/* Batch 590（源站实测）：`几何模型` 子菜单在父项下方展开
                      （204×256），八项各 199×32、行距 32px。 */}
                  {geometrySubmenuOpen && (
                    <div
                      data-director-geometry-submenu
                      aria-label="几何模型"
                      className={cn(
                        FLYOUT_CARD_CLASS,
                        "absolute left-1 top-[calc(100%+2px)] z-50 w-[204px] p-1.5",
                      )}
                    >
                      {geometrySubmenu.map((option) => {
                        const OptionIcon = option.icon;
                        return (
                          <button
                            key={option.id}
                            type="button"
                            data-director-geometry-option={option.id}
                            onClick={() => handleGeometryOption(option.id, option.label)}
                            className="flex h-8 w-full items-center gap-2 rounded-lg px-2 text-left text-xs text-[#d8d8d8] hover:bg-white/[0.07]"
                          >
                            <OptionIcon size={13} className="shrink-0 text-[#9a9a9a]" />
                            <span className="truncate">{option.label}</span>
                          </button>
                        );
                      })}
                    </div>
                  )}
                  </div>
                </div>
              )}
              {entry.id === "panorama" && openFlyout === "panorama" && (
                <div
                  data-director-panorama-flyout
                  aria-label="全景图"
                  className={cn(
                    "absolute left-[calc(100%+8px)] top-0 z-40",
                    FLYOUT_WIDTH,
                  )}
                >
                  <span
                    data-director-flyout-title="panorama"
                    className={FLYOUT_TITLE_CLASS}
                  >
                    全景图
                  </span>
                  <div className={cn(FLYOUT_CARD_CLASS, "p-1.5")}>
                  {panoramaFlyout.map((item) => {
                    const ItemIcon = item.icon;
                    return (
                      <button
                        key={item.id}
                        type="button"
                        data-director-panorama-option={item.id}
                        className="flex h-8 w-full items-center gap-2 rounded-lg px-2 text-left text-xs text-[#d8d8d8] hover:bg-white/[0.07]"
                      >
                        <ItemIcon size={13} className="shrink-0 text-[#9a9a9a]" />
                        <span className="truncate">{item.label}</span>
                      </button>
                    );
                  })}
                  </div>
                </div>
              )}
              {entry.id === "aspect-ratio" && openFlyout === "aspect-ratio" && (
                <div
                  data-director-aspect-flyout
                  aria-label="选择画幅比例"
                  className={cn(
                    "absolute left-[calc(100%+8px)] top-0 z-40",
                    FLYOUT_WIDTH,
                  )}
                >
                  <span
                    data-director-flyout-title="aspect-ratio"
                    className={FLYOUT_TITLE_CLASS}
                  >
                    选择画幅比例
                  </span>
                  <div
                    data-director-aspect-grid
                    className={cn(
                      FLYOUT_CARD_CLASS,
                      // Batch 590（源站实测）：gap 8px、padding 0 8 12 →
                      // 4×72 + 3×8 + 12 = 324，与源站卡片高逐像素一致。
                      "grid grid-cols-2 gap-2 px-2 pb-3 pt-0",
                    )}
                  >
                  {aspectRatios.map((ratio) => (
                    <button
                      key={ratio}
                      type="button"
                      data-director-aspect-option={ratio}
                      aria-pressed={aspectRatio === ratio}
                      onClick={() => setAspectRatio(ratio)}
                      // Batch 590（源站实测 104×72 / radius 12px）：
                      // 选中态与未选中态的**文字色相同**（都是
                      // rgba(255,255,255,0.9)），唯一差别是按钮描边——
                      // 选中 0.85、未选中 0.1，背景两态皆透明。源站按钮
                      // 无 aria-pressed，clone 保留作 a11y 超集。
                      className={cn(
                        "flex h-[72px] flex-col items-center justify-center gap-1 rounded-xl border text-xs",
                        aspectRatio === ratio
                          ? "border-white/[0.85] text-white/90"
                          : "border-white/10 text-white/90 hover:border-white/25",
                      )}
                    >
                      <span
                        aria-hidden="true"
                        data-director-aspect-glyph
                        className={cn("block rounded-sm border border-white/90", ASPECT_GLYPH[ratio])}
                      />
                      {ratio}
                    </button>
                  ))}
                  </div>
                </div>
              )}
            </div>
            {/* 源站在 `场景` 与 `添加角色` 之间有一条
                `<div class="border-white/8 h-2 w-8 border-b">`（32×8 @(8,100)）。
                它是 nav 的直接子节点，所以要跟按钮的包裹 div 平级。 */}
            {index === 0 ? (
              <span
                aria-hidden="true"
                data-director-rail-divider
                className="block h-2 w-8 border-b border-white/8"
              />
            ) : null}
            </Fragment>
          );
        })}
      </div>
      <button
        type="button"
        data-director-rail-entry="help"
        aria-label="帮助"
        title="帮助"
        // 源站的「帮助」与其它 rail 项同款：`rounded-lg`（不是 clone 的
        // rounded-full）+ `text-white/72 hover:bg-white/8 hover:text-white`，
        // 图标同为 20px。
        className="mt-auto flex size-8 items-center justify-center rounded-lg text-white/72 transition-colors hover:bg-white/8 hover:text-white"
      >
        <HelpCircle size={20} />
      </button>
      <input
        ref={characterUploadInputRef}
        type="file"
        accept=".glb,.gltf,.fbx,.obj"
        multiple
        aria-label="导入本地角色模型"
        className="hidden"
        onChange={handleCharacterUploadChange}
      />
      {characterAck && (
        <span
          data-director-character-ack
          aria-live="polite"
          className="absolute bottom-14 left-[calc(100%+8px)] whitespace-nowrap rounded-full bg-black/70 px-2.5 py-1 text-[11px] text-[#9ddbb9]"
        >
          {characterAck}
        </span>
      )}
      {aiImportOpen && (
        <DirectorAiImportModal
          onClose={() => setAiImportOpen(false)}
          onPanoramaSourceChange={onPanoramaSourceChange}
        />
      )}
      {/* Batch 590（源站实测 220×204 @(280,388)）：`群众 (3x3)` 打开的是
          弹窗——标题「添加群众阵列」、右上角「共N人」计数、三个数字输入
          行数/列数/间距，页脚 取消 / 添加（添加为白底主按钮）。弹窗并排
          出现在 flyout 右侧（源站 x=280，flyout 占 48..280），flyout 保持
          打开。clone 此前是点一下直接按 3×3/1.2 出结果。 */}
      {crowdDialogOpen && (
        <div
          data-director-crowd-dialog
          role="dialog"
          aria-label="添加群众阵列"
          className="absolute left-[294px] top-0 z-50 w-[220px] rounded-xl border border-white/10 bg-[#242424] p-3 shadow-[0_16px_40px_rgba(0,0,0,0.5)]"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs text-[#d8d8d8]">添加群众阵列</span>
            <span
              data-director-crowd-count
              className="text-[11px] text-[#8a8a8a]"
            >
              共{crowdDraft.rows * crowdDraft.columns}人
            </span>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2">
            {(
              [
                ["rows", "行数"],
                ["columns", "列数"],
              ] as const
            ).map(([key, label]) => (
              <label key={key} className="flex flex-col gap-1 text-[11px] text-[#8a8a8a]">
                <span>{label}</span>
                <input
                  type="number"
                  data-director-crowd-input={key}
                  aria-label={label}
                  min={CROWD_LIMITS[key].min}
                  max={CROWD_LIMITS[key].max}
                  step={1}
                  value={crowdDraft[key]}
                  onChange={(event) =>
                    setCrowdDraft((draft) => ({
                      ...draft,
                      [key]: Math.min(
                        CROWD_LIMITS[key].max,
                        Math.max(CROWD_LIMITS[key].min, Number(event.target.value)),
                      ),
                    }))
                  }
                  className="h-7 w-full rounded-lg border border-white/10 bg-[#1e1e1e] px-2 text-xs text-[#d8d8d8] outline-none focus:border-white/30"
                />
              </label>
            ))}
          </div>
          <label className="mt-3 flex flex-col gap-1 text-[11px] text-[#8a8a8a]">
            <span>间距</span>
            <input
              type="number"
              data-director-crowd-input="spacing"
              aria-label="间距"
              min={CROWD_LIMITS.spacing.min}
              max={CROWD_LIMITS.spacing.max}
              step={0.1}
              value={crowdDraft.spacing}
              onChange={(event) =>
                setCrowdDraft((draft) => ({
                  ...draft,
                  spacing: Math.min(
                    CROWD_LIMITS.spacing.max,
                    Math.max(CROWD_LIMITS.spacing.min, Number(event.target.value)),
                  ),
                }))
              }
              className="h-7 w-full rounded-lg border border-white/10 bg-[#1e1e1e] px-2 text-xs text-[#d8d8d8] outline-none focus:border-white/30"
            />
          </label>
          <div className="mt-4 flex justify-end gap-2">
            <button
              type="button"
              data-director-crowd-cancel
              onClick={() => setCrowdDialogOpen(false)}
              className="h-7 w-12 rounded-lg border border-white/10 text-xs text-[#b5b5b5] hover:bg-white/[0.06]"
            >
              取消
            </button>
            <button
              type="button"
              data-director-crowd-confirm
              onClick={confirmCrowdArray}
              className="h-7 w-12 rounded-lg bg-white text-xs text-[#1a1a1a] hover:bg-white/90"
            >
              添加
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
