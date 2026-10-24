"use client";

// ★★★ Batch 859（源站逐字）：导演台左侧的「**全景图**」**侧栏面板模式**。
//
// ★ ★★ Batch 861（源站实测）：这三行**在源站都不是死按钮**。
//   源站逐字（`aU` 的 panorama 段）：
//     ① 本地上传：`onClick:()=>{I?.(), et.current?.click()}`
//        ⟹ `I` ＝ `oY` ＝ **纯埋点**（`libtv.canvas.director.panorama.local_upload.click`）
//        ⟹ ⟹ 真正的动作是 **`et.current?.click()`**（触发一个隐藏的 file input）
//     ② 历史记录：`onClick:T` ⟹ `oB` ⟹ `eu?.((e,t)=>{… r6({panoramaUrl:e})})`
//     ③ AI生成  ：`onClick:P` ＋ `disabled:E` ⟹ `oX` ⟹ `td(!0)`（打开对话框）
//
// ★ 源站实测（`probes/source861_panorama_diff.py` ⟹ `raw/source-861-panorama-diff.json`）：
//   · 点「本地上传」⟹ ⟹ **弹出了文件选择器**（`filechooser` 事件触发 ＝ True）
//   · 点「历史记录」⟹ ⟹ 打开**资产库选择器**（按钮 86 → 95）
//   · 点「AI生成」  ⟹ ⟹ 打开**同一个**选择器 ＋ 多「上传图片」「生成」「关闭」
//                       （按钮 86 → 98）
//
// ★ ★★ clone 此前这三行**完全没有 onClick** ⟹ ⟹ 点了什么也不会发生
//   ⟹ ⟹ 本批把它们接上（详见 `DirectorPanoramaPicker.tsx` 的差异说明）。
import { useRef, useState } from "react";
import { History, Sparkles, Upload } from "lucide-react";

import {
  DirectorPanoramaPicker,
  type DirectorPanoramaPickerMode,
} from "@/components/director/DirectorPanoramaPicker";
import type {
  DirectorCanvasMediaInputV1,
  DirectorLocalPanoramaAsset,
} from "@/lib/directorCanvasMediaIngress";

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

export function DirectorPanoramaPanel({
  active,
  panoramaInputs,
  currentPanoramaSourceId,
  onSelectPanorama,
  onLocalAsset,
}: {
  active: boolean;
  /** ★ 可作全景图的输入（画布图片输入 ＋ 本地上传的那张）。 */
  panoramaInputs: DirectorCanvasMediaInputV1[];
  /** ★ 当前正在用的全景图来源（`sourceNodeId`）。 */
  currentPanoramaSourceId: string | null;
  /** ★ 选中某个输入当全景图。 */
  onSelectPanorama: (sourceNodeId: string) => void;
  /** ★ 「本地上传」选中文件后回调（**不上传**，只给一份本地 blob URL）。 */
  onLocalAsset: (asset: Omit<DirectorLocalPanoramaAsset, "id">) => void;
}) {
  // ★ 源站逐字：`et.current?.click()` ⟹ ⟹ 一个**隐藏的 file input**
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [pickerMode, setPickerMode] = useState<DirectorPanoramaPickerMode | null>(
    null,
  );

  // ★ 源站逐字：AI 那行带 `disabled:E`（`E` ＝ `panoramaAiGenerating`）。
  //   ★ ★ clone **不接真实全景图生成**（真实生图会产生费用）⟹ ⟹
  //   「生成中」这个状态在 clone 里**永远不会出现** ⟹ ⟹
  //   这里**不写**一个恒假的 `disabled` 表达式（恒假分支是假牙的温床），
  //   改成**如实注释**：将来真接生成时，在这里接 `panoramaAiGenerating`。

  // ★ 源站逐字：`"panorama"===z?(…):null` ⟹ ⟹ **条件渲染**（不是 `hidden`）
  //   ⟹ ⟹ 与 batch 858 的「添加角色」面板同一写法：组件常驻（监听器不死）、
  //   DOM 子树按模式在/不在。
  if (!active) return null;

  const openFileChooser = () => {
    // ★ 源站逐字：`et.current?.click()`
    fileInputRef.current?.click();
  };

  const handleLocalFile = (file: File | undefined) => {
    if (!file) return;
    const imageUrl = URL.createObjectURL(file);
    const probe = new Image();
    probe.onload = () => {
      onLocalAsset({
        filename: file.name,
        imageUrl,
        width: probe.naturalWidth || 1,
        height: probe.naturalHeight || 1,
      });
    };
    probe.onerror = () => {
      // ★ 读不出尺寸也要让用户看到点反应（用 1×1 兜底，形态照旧）
      onLocalAsset({ filename: file.name, imageUrl, width: 1, height: 1 });
    };
    probe.src = imageUrl;
    // ★ 允许重复选同一个文件（否则第二次 change 不触发）
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

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
              onClick={() => {
                if (item.id === "local-upload") {
                  // ★ 源站逐字：`I?.(), et.current?.click()`
                  openFileChooser();
                } else if (item.id === "history") {
                  setPickerMode("history");
                } else if (item.id === "ai-generate") {
                  setPickerMode("ai");
                }
              }}
              className={ROW_CLASS}
            >
              <Icon size={14} className="shrink-0" aria-hidden="true" />
              <span className="truncate">{item.label}</span>
            </button>
          );
        })}
        {/* ★ 源站逐字：`et` ＝ 那个隐藏的 file input（`accept="image/*"`）*/}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          data-director-panorama-file-input
          aria-label="选择本地全景图"
          className="hidden"
          onChange={(event) => handleLocalFile(event.target.files?.[0])}
        />
      </div>

      {/* ★ ★★ **clone 自己的扩展**（源站的面板里没有这一行）：
         源站选了全景图之后，**3D 场景**里会变（用户看得见）；
         而 clone 的检查器**默认不展开** ⟹ ⟹ 选完什么反馈都没有
         ⟹ ⟹ 这里补一行「当前全景图」读数 ⟹ ⟹
         ★ 既是**用户可见的反馈**，也是门禁的**可观测读数点**。 */}
      <div
        data-director-panorama-current
        data-director-panorama-current-source={currentPanoramaSourceId ?? ""}
        className="mt-2 px-2 text-[11px] leading-5 text-white/55"
      >
        <span className="block truncate">
          {currentPanoramaSourceId
            ? `当前全景图：${
                panoramaInputs.find(
                  (input) => input.sourceNodeId === currentPanoramaSourceId,
                )?.filename ?? "输入已失效"
              }`
            : "当前全景图：未选择"}
        </span>
      </div>

      {pickerMode ? (
        <DirectorPanoramaPicker
          mode={pickerMode}
          inputs={panoramaInputs}
          onClose={() => setPickerMode(null)}
          onConfirm={(sourceNodeId) => {
            onSelectPanorama(sourceNodeId);
            setPickerMode(null);
          }}
          onUploadImage={() => {
            // ★ 源站实测：AI 那行的对话框里多一枚「上传图片」
            setPickerMode(null);
            openFileChooser();
          }}
        />
      ) : null}
    </div>
  );
}
