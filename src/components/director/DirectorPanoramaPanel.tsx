"use client";

// ★★★ Batch 859（源站逐字）：导演台左侧的「**全景图**」**侧栏面板模式**。
//
// ★ ★★ 本组件存在的理由（= batch 858 登记的 D8）：
//
//   源站逐字（源站 chunk，`aU` 组件）：
//     `e?null:(0,i.jsxs)("div",{className:"flex w-[232px] min-w-0 flex-col bg-[#171717]",
//        children:["scene"===z?n:null,"character"===z?(…),"camera"===z?(…),
//                  "panorama"===z?(…),"aspect"===z?(…)]})`
//     ⟹ ⟹ 左侧那个 232px 的面板是**五模式互斥容器**
//     ⟹ ⟹ **「全景图」是面板的一个模式**，**不是** rail 上的浮层。
//
//   clone 此前把「全景图」做成 **rail 上的 portal 浮层**（`data-director-panorama-flyout`）
//     ⟹ ⟹ 与源站逐字**不符** ⟹ ⟹ 本批改成面板模式。
//
// ★ 源站逐字（`"panorama"===z` 那段）：
//     标题条 `aO` ＝ `flex h-12 shrink-0 items-center px-3 text-[12px] leading-5
//                      text-white/90`，文本 `D("canvas:directorPanorama")`（「全景图」）
//     内容容器 `className:"px-2"`
//     三枚**行**（行类 `eu`，**不是**卡片）：
//       ① 本地上传：图标 `u.p.Upload`、文本 `D("canvas:directorLocalUpload")`
//       ② 历史记录：图标 `u.p.HistoryN`、文本 `D("canvas:directorHistory")`
//       ③ AI生成  ：图标 `aM.f`、`aria-hidden:!0`、`disabled:E`、
//                    文本 `E?D("canvas:directorGenerating"):D("canvas:directorAiGenerate")`
//
// ★ 源站实测（`docs/research/liblib-canvas-batch859-2026-10-01/raw/source-859-panels.json`）：
//     面板 @(48,52) 232 宽、标题条 @(48,52) 232×48 / 12px、
//     内容容器 @(48,100) 232×96（`px-2`）
//     三行 @(56,100) / (56,132) / (56,164)，各 **216×32**、字号 **13px**、行高 **20px**
//     图标 14×14 @(64,109)
//     ★ **场景树不在场**（模式互斥被实测确认）⟹ ⟹ 坐实「它是面板模式」
//
// ★ 本组件**常驻挂载**（哪怕 `active=false`）⟹ ⟹ 与 batch 858 的
//   `DirectorCharacterPanel` 同一约定：面板内部的监听器不能因为
//   「切到别的模式」而消失。
import { History, Sparkles, Upload } from "lucide-react";

// ★ 源站逐字（`aO`）：标题条。
const TITLE_CLASS =
  "flex h-12 shrink-0 items-center px-3 text-[12px] leading-5 text-white/90";

// ★ 源站逐字（`eu`）：行样式。`disabled:*` 两段源站也有，这里照抄。
const ROW_CLASS =
  "flex h-8 w-full items-center gap-2 rounded-lg px-2 text-left text-[13px] leading-5 text-white/88 transition-colors hover:bg-white/8 disabled:cursor-not-allowed disabled:opacity-45";

// ★ 全景图三条（源站逐字顺序 ＋ 逐字文本 ＋ 逐字图标）
const panoramaItems = [
  { id: "local-upload", label: "本地上传", icon: Upload },
  { id: "history", label: "历史记录", icon: History },
  { id: "ai-generate", label: "AI生成", icon: Sparkles },
] as const;

export function DirectorPanoramaPanel({ active }: { active: boolean }) {
  // ★ 源站逐字：`"panorama"===z?(…):null` ⟹ ⟹ **条件渲染**（不是 `hidden`）
  //   ⟹ ⟹ 与 batch 858 的「添加角色」面板同一写法：组件常驻（监听器不死）、
  //   DOM 子树按模式在/不在。
  if (!active) return null;
  return (
    <div
      data-director-panorama-panel
      aria-label="全景图"
      className="flex h-full min-h-0 w-full flex-col bg-[#171717]"
    >
      <div data-director-panel-title="panorama" className={TITLE_CLASS}>
        <span className="truncate">全景图</span>
      </div>
      {/* ★ 源站逐字：内容容器是 `px-2`（不是 grid、也不是可滚动列表）*/}
      <div data-director-panorama-list className="px-2">
        {panoramaItems.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              type="button"
              data-director-panorama-option={item.id}
              className={ROW_CLASS}
            >
              <Icon size={14} className="shrink-0" aria-hidden="true" />
              <span className="truncate">{item.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
