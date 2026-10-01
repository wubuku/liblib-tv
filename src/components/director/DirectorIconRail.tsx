"use client";

import { useRef, useState, type ChangeEvent } from "react";
import {
  ArrowDownToLine,
  Clapperboard,
  HelpCircle,
  History,
  Image as ImageIcon,
  Sparkles,
  Proportions,
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
    if (itemId === "crowd-3x3") {
      addCrowdArray({ rows: 3, columns: 3, spacing: 1.2 });
      setCharacterAck("已加入群众 (3x3)（本地等效）");
      setOpenFlyout(null);
      window.setTimeout(() => setCharacterAck(null), 2000);
      return;
    }
    if (itemId === "local-upload") {
      setOpenFlyout(null);
      characterUploadInputRef.current?.click();
      return;
    }
    if (itemId === "geometry") {
      setOpenFlyout(null);
      return;
    }
    setCharacterAck(`预设角色「${label}」为本地等效占位`);
    setOpenFlyout(null);
    window.setTimeout(() => setCharacterAck(null), 2000);
  };

  return (
    <div
      data-director-icon-rail
      aria-label="导演台资源栏"
      className="absolute inset-y-0 left-0 z-30 hidden w-[46px] flex-col items-center gap-1 border-r border-white/[0.07] bg-[#1a1a1a] py-3 min-[900px]:flex"
    >
      <div className="flex flex-col items-center gap-1">
        {railEntries.map((entry) => {
          const Icon = entry.icon;
          const isActive = active === entry.id;
          return (
            <div key={entry.id} className="relative">
              <button
                type="button"
                data-director-rail-entry={entry.id}
                aria-label={entry.label}
                title={entry.label}
                aria-pressed={isActive}
                onClick={() => select(entry.id)}
                className={cn(
                  "flex size-8 items-center justify-center rounded-lg text-[#a5a5a5] transition-colors",
                  isActive ? "bg-white/[0.12] text-white" : "hover:bg-white/[0.06] hover:text-[#d8d8d8]",
                )}
              >
                <Icon size={16} />
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
                      "grid grid-cols-2 gap-1.5 p-2",
                    )}
                  >
                  {aspectRatios.map((ratio) => (
                    <button
                      key={ratio}
                      type="button"
                      data-director-aspect-option={ratio}
                      aria-pressed={aspectRatio === ratio}
                      onClick={() => setAspectRatio(ratio)}
                      // Batch 589: 源站七卡实测行距 ≈81px（y=134/215/298/379），
                      // 面板 324px 高 ÷ 4 行；clone 原为 64px 卡 + 6px 间距。
                      className={cn(
                        "flex h-[72px] flex-col items-center justify-center gap-1 rounded-lg border text-[11px]",
                        aspectRatio === ratio
                          ? "border-[#09caf5]/60 text-[#09caf5]"
                          : "border-white/10 text-[#b5b5b5] hover:border-white/25",
                      )}
                    >
                      <span
                        aria-hidden="true"
                        className={cn(
                          "block rounded-sm border",
                          ratio === "自适应" ? "h-3 w-5" : ratio === "21:9" ? "h-2 w-6" : ratio === "16:9" ? "h-2.5 w-5" : ratio === "4:3" ? "h-3.5 w-4.5" : ratio === "1:1" ? "h-4 w-4" : ratio === "3:4" ? "h-4.5 w-3.5" : "h-5 w-2.5",
                        )}
                      />
                      {ratio}
                    </button>
                  ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
      <button
        type="button"
        data-director-rail-entry="help"
        aria-label="帮助"
        title="帮助"
        className="mt-auto flex size-8 items-center justify-center rounded-full text-[#a5a5a5] hover:bg-white/[0.06] hover:text-[#d8d8d8]"
      >
        <HelpCircle size={16} />
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
    </div>
  );
}
