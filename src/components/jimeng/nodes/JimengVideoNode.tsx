"use client";

import { useEffect, useRef, useState } from "react";
import { Plus } from "lucide-react";
import { Handle, Position, useReactFlow } from "@xyflow/react";
import type { NodeProps } from "@xyflow/react";

import type { JimengVideoNodeData } from "@/types/jimeng";
import { JimengNodeToolbar } from "@/components/jimeng/JimengNodeToolbar";
import { JimengGenPanel } from "@/components/jimeng/JimengGenPanel";
import { JimengInsertMenu } from "@/components/jimeng/JimengInsertMenu";
import { JimengFramePicker } from "@/components/jimeng/JimengFramePicker";
import { JimengRepaintPanel } from "@/components/jimeng/JimengRepaintPanel";
import { JimengTrimPanel } from "@/components/jimeng/JimengTrimPanel";
import { JimengVideoEditMode } from "@/components/jimeng/JimengVideoEditMode";
import { JimengVideoPreview } from "@/components/jimeng/JimengVideoPreview";
import { JimengVideoTitleRow } from "@/components/jimeng/nodes/JimengVideoTitleRow";
import { JimengVideoMediaCard } from "@/components/jimeng/nodes/JimengVideoMediaCard";
import { useJimengStore } from "@/store/jimengStore";

/**
 * 即梦视频节点 — 复刻重点 (本地上传视频)。
 *
 * 结构证据 (SOURCE_FACT, docs/research/jimeng-canvas/README.md):
 * - 标题行在卡片上方 32px：文件徽标 16×16 + 13px/22px rgba(255,255,255,0.7) 标题 + 右侧 Tag 图标
 * - 卡片 569×320 世界尺寸、8px 圆角；媒体 object-cover
 * - 有内容: 中央 32px 半透明播放圆钮 + 底部 播放/时间/静音/全屏 控制 + 底边 2px 进度条
 * - 空节点: 对角渐变占位 + 中央小图标
 * - 左右连接热区 60×120 (隐形)；"+ " 圆钮 24px：本地上传节点仅右侧，空节点两侧 (hover/选中显示)
 * Batch 74: 拆分为 JimengVideoTitleRow + JimengVideoMediaCard + 本编排器
 * (无行为变更)。
 */
const HANDLE_BASE = {
  width: 60,
  height: 120,
  background: "transparent",
  border: "none",
  borderRadius: 0,
} as const;

export function JimengVideoNode({ id, data, selected }: NodeProps) {
  const d = data as JimengVideoNodeData;
  // 播放态由 data.playing 显式驱动 (mock 初始为暂停，与源站提取时一致)
  const playing = d.hasMedia && d.playing === true;
  const addVideoNodeAfter = useJimengStore((s) => s.addVideoNodeAfter);
  const repaintNodeId = useJimengStore((s) => s.repaintNodeId);
  const enterRepaint = useJimengStore((s) => s.enterRepaint);
  const exitRepaint = useJimengStore((s) => s.exitRepaint);
  const editNodeId = useJimengStore((s) => s.editNodeId);
  const enterEdit = useJimengStore((s) => s.enterEdit);
  const exitEdit = useJimengStore((s) => s.exitEdit);
  const inferNodeId = useJimengStore((s) => s.inferNodeId);
  const enterInfer = useJimengStore((s) => s.enterInfer);
  const openAiDrawer = useJimengStore((s) => s.openAiDrawer);
  const framePickerNodeId = useJimengStore((s) => s.framePickerNodeId);
  const framePickerMode = useJimengStore((s) => s.framePickerMode);
  const enterFramePicker = useJimengStore((s) => s.enterFramePicker);
  const exitFramePicker = useJimengStore((s) => s.exitFramePicker);
  const captureFrame = useJimengStore((s) => s.captureFrame);
  const trimNodeId = useJimengStore((s) => s.trimNodeId);
  const enterTrim = useJimengStore((s) => s.enterTrim);
  const exitTrim = useJimengStore((s) => s.exitTrim);
  const tasks = useJimengStore((s) => s.tasks);
  const startTask = useJimengStore((s) => s.startTask);
  const addNodeAt = useJimengStore((s) => s.addNodeAt);
  const [insertMenu, setInsertMenu] = useState<
    "left" | "right" | "title" | null
  >(null);

  const [tagPickerOpen, setTagPickerOpen] = useState(false);
  const repaintMode = repaintNodeId === id;
  const editMode = editNodeId === id;
  const inferMode = inferNodeId === id;
  const pickerMode = framePickerNodeId === id;
  const trimMode = trimNodeId === id;
  const task = tasks.find((t) => t.nodeId === id);
  const groupId = useJimengStore((s) =>
    s.nodes.find((n) => n.id === id)?.groupId,
  );
  const tickPlay = useJimengStore((s) => s.tickPlay);
  const pushToast = useJimengStore((s) => s.pushToast);
  const applyTrim = useJimengStore((s) => s.applyTrim);
  const previewNodeId = useJimengStore((s) => s.previewNodeId);
  const soloSelected =
    useJimengStore((s) => s.nodes.filter((n) => n.selected).length) === 1;
  const openPreview = useJimengStore((s) => s.openPreview);
  const closePreview = useJimengStore((s) => s.closePreview);
  const previewOpen = previewNodeId === id;

  // 播放中 mock 时间走动 (Batch 15)；播完自停
  useEffect(() => {
    if (!playing) return;
    const timer = window.setInterval(() => tickPlay(id, 0.25), 250);
    return () => window.clearInterval(timer);
  }, [playing, id, tickPlay]);

  // 插入菜单 Escape 关闭 (Batch 24)
  useEffect(() => {
    if (!insertMenu) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setInsertMenu(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [insertMenu]);

  // 批 373 SOURCE_FACT: 编辑态 Escape 退出 (无历史入栈)；
  // 进入时画布自动 zoom 176% 聚焦节点，退出还原视口 (373b)
  const rf = useReactFlow();
  const prevViewportRef = useRef<{
    x: number;
    y: number;
    zoom: number;
  } | null>(null);
  useEffect(() => {
    if (editMode && prevViewportRef.current === null) {
      const bounds = document
        .querySelector(".react-flow")
        ?.getBoundingClientRect();
      const node = rf.getNodes().find((n) => n.id === id);
      if (bounds && node) {
        prevViewportRef.current = rf.getViewport();
        const z = 1.76;
        rf.setViewport({
          x: bounds.width / 2 - (node.position.x + d.width / 2) * z,
          y: bounds.height / 2 - (node.position.y + d.height / 2) * z,
          zoom: z,
        });
      }
    }
    if (!editMode && prevViewportRef.current) {
      rf.setViewport(prevViewportRef.current);
      prevViewportRef.current = null;
    }
  }, [editMode, id, d.width, d.height, rf]);
  useEffect(() => {
    if (!editMode) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") exitEdit();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [editMode, exitEdit]);

  return (
    <div
      className="group relative"
      style={{ width: d.width, height: d.height }}
      data-jimeng-node-selected={selected || undefined}
      data-group-id={groupId}
    >
      {/* 选中后弹出的操作工具条 / 编辑态 / 反推面板 / 空节点生成面板 */}
      {d.hasMedia && repaintMode ? (
        <JimengRepaintPanel
          visible
          data={d}
          onSubmit={() => exitRepaint()}
        />
      ) : d.hasMedia && editMode ? (
        <JimengVideoEditMode onSubmit={() => exitEdit()} />
      ) : d.hasMedia && pickerMode ? (
        <JimengFramePicker
          visible
          data={d}
          mode={framePickerMode}
          onConfirm={() => {
            // 批 203 SOURCE_FACT: 源站「确认」= 选择器关闭 + 直出该帧的
            // 图片节点 (非写回 currentTime——batch 34 旧语义已修正)
            captureFrame(id, "custom");
            exitFramePicker();
          }}
        />
      ) : d.hasMedia && trimMode ? (
        <JimengTrimPanel
          visible
          data={d}
          onConfirm={(trimmedDuration, startOffset) => {
            applyTrim(id, trimmedDuration, startOffset);
            exitTrim();
          }}
        />
      ) : d.hasMedia ? (
        <JimengNodeToolbar
          visible={selected === true && soloSelected}
          onAction={(label) => {
            if (label === "局部重拍") enterRepaint(id);
            if (label === "视频编辑") enterEdit(id);
            // 批 216 SOURCE_FACT: 提示词反推 → 节点放大暂停 + 打开 AI 抽屉
            // 并预填 视频反解 提示词 (原 mock 反推面板已被该流程取代)
            if (label === "提示词反推") {
              enterInfer(id);
              openAiDrawer(
                `用 视频反解 反推出 ${d.title} 的提示词，并创建文本节点，方便我拉片复刻`,
                d.poster ? { poster: d.poster, label: d.title } : undefined,
              );
            }
            if (label === "视频修剪") enterTrim(id);
            if (label === "智能超清") startTask(id, "upscale");
            if (label === "补帧") startTask(id, "interpolate");
            if (label === "下载") pushToast("视频下载已开始（mock）");
            if (label === "保存到主体库") pushToast("已保存到主体库（mock）");
            if (label === "全屏预览") openPreview(id);
            if (label === "截取帧:自定义") enterFramePicker(id, "custom");
            // Batch 62 (SOURCE_FACT): 源站 首帧/尾帧 直接产出图片节点
            if (label === "截取帧:首帧") captureFrame(id, "first");
            if (label === "截取帧:尾帧") captureFrame(id, "last");
          }}
        />
      ) : null}
      {!d.hasMedia ? (
        // 多选时不显示生成面板 (SOURCE_FACT batch 62: 62-multiselect 截图
        // 中多选无 gen panel)，与单选工具条同用 soloSelected 门控
        <JimengGenPanel visible={selected === true && soloSelected} nodeId={id} />
      ) : null}
      {/* 标题行 (卡片上方 32px)；编辑/反推/帧选择/修剪态隐藏仅 repaint；
          批 373 SOURCE_FACT: 编辑态与修剪态标题行均保持可见 */}
      {!repaintMode && !inferMode && !pickerMode ? (
        <JimengVideoTitleRow
          id={id}
          d={d}
          tagPickerOpen={tagPickerOpen}
          onToggleTagPicker={() => setTagPickerOpen((v) => !v)}
          onDblClick={() =>
            setInsertMenu((cur) => (cur === "title" ? null : "title"))
          }
        />
      ) : null}

      {/* 卡片主体；双击 = 从头重播 (SOURCE_FACT batch 24) */}
      <JimengVideoMediaCard
        id={id}
        d={d}
        selected={selected === true}
        playing={playing}
        task={task}
        minimal={editMode}
      />

      {/* 连接热区 (隐形) + "+" 圆钮 (hover/选中显示；点击弹「添加节点」菜单) */}
      <Handle
        type="target"
        position={Position.Left}
        className="!z-10"
        style={{ ...HANDLE_BASE, left: -30, top: "50%", transform: "translateY(-50%)" }}
      >
        {/* 证据: 本地上传节点左侧无 "+" (SOURCE_FACT §5)，仅空节点两侧都有 */}
        {d.source === "empty" ? (
          <span
            role="button"
            aria-label="左侧添加节点"
            className="absolute left-1/2 top-1/2 hidden size-9 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-white/50 bg-[#0D0D0D] text-white group-hover:flex group-data-[jimeng-node-selected]:flex"
            onClick={(e) => {
              e.stopPropagation();
              setInsertMenu((cur) => (cur === "left" ? null : "left"));
            }}
            onMouseDown={(e) => e.stopPropagation()}
          >
            <Plus size={16} />
          </span>
        ) : null}
      </Handle>
      <Handle
        type="source"
        position={Position.Right}
        className="!z-10"
        style={{ ...HANDLE_BASE, right: -30, top: "50%", transform: "translateY(-50%)" }}
      >
        <span
          role="button"
          aria-label="右侧添加节点"
          className="absolute left-1/2 top-1/2 hidden size-9 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-white/50 bg-[#0D0D0D] text-white group-hover:flex group-data-[jimeng-node-selected]:flex"
          onClick={(e) => {
            e.stopPropagation();
            setInsertMenu((cur) => (cur === "right" ? null : "right"));
          }}
          onMouseDown={(e) => e.stopPropagation()}
        >
          <Plus size={16} />
        </span>
      </Handle>
      {insertMenu ? (
        <div
          className="absolute z-[130]"
          style={
            insertMenu === "right"
              ? { left: "100%", top: "50%", marginLeft: 22 }
              : insertMenu === "left"
                ? { right: "100%", top: "50%", marginRight: 22 }
                : { left: "18%", top: 8 }
          }
        >
          <JimengInsertMenu
            extended={insertMenu === "title"}
            onPick={(label) => {
              if (label === "视频") addVideoNodeAfter(id);
              if (label === "图片")
                addNodeAt("image", { x: d.width + 200, y: 0 });
              if (label === "文本")
                addNodeAt("text", { x: d.width + 200, y: 120 });
              if (label === "音频")
                addNodeAt("audio", { x: d.width + 200, y: 240 });
            }}
            onClose={() => setInsertMenu(null)}
          />
        </div>
      ) : null}
      {/* 全屏播放器 (Batch 27) */}
      {previewOpen ? (
        <JimengVideoPreview
          nodeId={id}
          data={d}
          onClose={() => closePreview()}
        />
      ) : null}
    </div>
  );
}
