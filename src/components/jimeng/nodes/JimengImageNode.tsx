"use client";

import type { NodeProps } from "@xyflow/react";

import { nodeRingShadow } from "@/components/jimeng/nodeChrome";
import type { JimengImageNodeData } from "@/types/jimeng";
import { FileBadgeIcon } from "@/components/jimeng/icons";
import { JimengImageNodeToolbar } from "@/components/jimeng/JimengImageNodeToolbar";
import { JimengImageGenPanel } from "@/components/jimeng/JimengImageGenPanel";
import { JimengNodeTitle } from "@/components/jimeng/nodes/JimengNodeTitle";
import { JimengConnectHandles } from "@/components/jimeng/JimengConnectHandles";
import { useJimengStore } from "@/store/jimengStore";
import { mockMsg } from "@/components/jimeng/jimengFeedback";
/**
 * 图片节点 (Batch 17)。结构与视频节点同族 (SOURCE_FACT §5 的视频节点骨架)；
 * 批 195 补源站图片节点提取: 569×320 同视频卡、选中工具条见
 * JimengImageNodeToolbar。
 */
export function JimengImageNode({ id, data, selected }: NodeProps) {
  const d = data as JimengImageNodeData;
  const pushToast = useJimengStore((s) => s.pushToast);
  const startTask = useJimengStore((s) => s.startTask);
  const openPreview = useJimengStore((s) => s.openPreview);
  const enterInfer = useJimengStore((s) => s.enterInfer);
  const openAiDrawer = useJimengStore((s) => s.openAiDrawer);
  const soloSelected =
    useJimengStore((s) => s.nodes.filter((n) => n.selected).length) === 1;

  /**
   * ⭐⭐⭐⭐⭐ Batch 1032-④-B（C01）：工具条的动作**逐条接真动作**。
   *
   * 此前这里是 `onAction={(label) => pushToast(mockMsg(`${label}已执行`))}` ——
   * 18 项全部只弹一句「X已执行」，画面零变化，而文案恰恰在说「已经做完了」。
   *
   * 处置：**能做的接真动作；做不了的由工具条渲染成真禁用态 + 可见理由**
   * （见 `JimengImageNodeToolbar` 的 `UNAVAILABLE_REASON`）。
   * ⇒ ⇒ 这里**只列真动作**；做不了的项**根本不会走到这里**（按钮是 disabled）。
   *
   * 逐条对应（与视频侧 `JimengVideoNode` 的 onAction 同型）：
   *  · 智能超清 ⇒ `startTask(upscale)` ⇒ 节点上出现「智能超清处理中…」遮罩
   *  · 全屏预览 ⇒ `openPreview(id)` ⇒ 真的开预览层
   *  · 下载     ⇒ 真的把**这张图**打成 Blob 下下来（不是「已下载」四个字）
   *  · 提示词反推 ⇒ `enterInfer` + `openAiDrawer` ⇒ 打开 AI 抽屉并预填提示词
   */
  const onToolbarAction = (label: string) => {
    if (label === "智能超清") {
      startTask(id, "upscale");
      return;
    }
    if (label === "全屏预览") {
      openPreview(id);
      return;
    }
    if (label === "下载") {
      /* 真下载：把节点自己的 poster（data URI）转成 Blob 走 `<a download>`。
       * ⚠️ 与 `JimengTextNode` 的下载同款手法（Blob + `<a download>`），
       *   而不是 data URI 直链 —— data URI 交给浏览器做下载名不稳。 */
      const href = d.poster ?? "";
      const a = document.createElement("a");
      if (href.startsWith("data:")) {
        const bin = atob(href.split(",")[1] ?? "");
        const bytes = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i += 1) bytes[i] = bin.charCodeAt(i);
        const url = URL.createObjectURL(new Blob([bytes], { type: "image/png" }));
        a.href = url;
        a.download = `${(d.title || "图片").replace(/[\\/:*?"<>|]/g, "_")}.png`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        setTimeout(() => URL.revokeObjectURL(url), 0);
      } else {
        a.href = href;
        a.download = `${(d.title || "图片").replace(/[\\/:*?"<>|]/g, "_")}.png`;
        document.body.appendChild(a);
        a.click();
        a.remove();
      }
      pushToast(mockMsg(`已下载「${d.title}」`));
      return;
    }
    if (label === "提示词反推") {
      /* 与视频侧同型：节点进入放大暂停态 + 打开 AI 抽屉并预填提示词。 */
      enterInfer(id);
      openAiDrawer(
        `用 图片反解 反推出 ${d.title} 的提示词，并创建文本节点，方便我拉片复刻`,
        d.poster ? { poster: d.poster, label: d.title } : undefined,
      );
    }
  };

  return (
    <>
      {/* 批 530 SOURCE_FACT: 空图片节点 (无 poster) 选中弹图片生成面板；
          带画面节点维持批 208 加工工具条 */}
      {d.poster ? (
        <JimengImageNodeToolbar
          visible={selected === true && soloSelected}
          onAction={onToolbarAction}
        />
      ) : (
        <JimengImageGenPanel
          visible={selected === true && soloSelected}
          nodeId={id}
        />
      )}
    <div
      className="group relative"
      style={{ width: d.width, height: d.height }}
      data-jimeng-node-selected={selected || undefined}
    >
      <div className="absolute inset-x-0 top-[-31px] z-10 flex h-8 items-start text-left">
        <FileBadgeIcon size={16} className="mt-1 shrink-0" />
        <JimengNodeTitle id={id} title={d.title} />
      </div>

      <div
        className="relative h-full w-full overflow-hidden rounded-lg"
        style={{
          background:
            "linear-gradient(to right bottom, rgb(34,34,34), rgb(20,20,20))",
          boxShadow: nodeRingShadow(selected === true),
        }}
      >
        {d.poster ? (
          // eslint-disable-next-line @next/next/no-img-element -- 本地 data URI mock 海报
          <img
            src={d.poster}
            alt={d.title}
            className="absolute inset-0 h-full w-full object-cover"
          />
        ) : (
          <span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-white/40">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden>
              <rect x="2" y="2" width="16" height="16" rx="3" stroke="currentColor" strokeWidth="1.3" />
              <circle cx="7" cy="7.5" r="1.6" fill="currentColor" />
              <path d="m4 15 4.5-5 3 3.4L14 10.5l2.5 3" stroke="currentColor" strokeWidth="1.3" fill="none" />
            </svg>
          </span>
        )}
        {/* 截取帧产出瞬态 (Batch 197 SOURCE_FACT「正在上传图片 0%」)；
            布局为 CLONE_DECISION (源站仅文本级证据) */}
        {typeof d.uploadProgress === "number" && d.uploadProgress < 100 ? (
          <div
            className="absolute inset-0 flex items-center justify-center bg-black/45"
            data-jimeng-image-uploading=""
          >
            <span className="text-[13px] text-white/90">
              正在上传图片 {d.uploadProgress}%
            </span>
          </div>
        ) : null}
        {/* ⭐⭐⭐ Batch 1032-②b-2：图片「生成中」处理态 (CLONE_DECISION)。
            与视频侧 `d.generating` 的覆盖层同款 (同文案「生成中…」)，
            ⇒ ⇒ 判据可以写成「**页面上出现了『生成中…』**」——
            这是**可观察的**，不是一个假 toast。
            ⚠️ 源站这个态需要付费才能看到 ⇒ ⇒ CLONE_DECISION。 */}
        {d.generating ? (
          <div
            className="absolute inset-0 z-[3] flex flex-col items-center justify-center gap-2 rounded-lg bg-black/55"
            data-jimeng-image-generating=""
          >
            <span className="size-6 animate-spin rounded-full border-2 border-white/25 border-t-white" />
            <span className="text-[12px] text-white/85">生成中…</span>
          </div>
        ) : null}
      </div>

      <JimengConnectHandles
        nodeId={id}
        title={d.title}
        size={{ width: d.width, height: d.height }}
        selected={selected === true}
      />
      </div>
    </>
  );
}
