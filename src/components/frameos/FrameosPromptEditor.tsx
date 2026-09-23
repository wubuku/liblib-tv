"use client";

import { useEffect, useState } from "react";
import { useFrameosStore } from "@/store/frameosStore";
import {
  CloseIcon,
  FullscreenExitIcon,
  ArrowDownIcon,
} from "./icons";

/**
 * FrameOS 画布底部 prompt 编辑面板 - 与 frameos.cn 视觉对齐
 * - 仅在选中节点时显示; 文本节点选中时不显示 (源站 2026-09-23 实测)
 * - 上方小型工具条: 聚焦 / 故事版 / 删除连线 (与 frameos.cn 一致)
 * - prompt 输入框 + 全屏按钮
 * - 模型 / 分辨率 / 比例 / 参数 / 步数 + 蓝色生成按钮
 *
 * 真实 frameos.cn 会用 ipc 推送到桌面后端; 此处为 mock，绑定到 store.startGeneration
 */
export function FrameosPromptEditor() {
  const selectedNodeId = useFrameosStore((s) => s.selectedNodeId);
  const nodes = useFrameosStore((s) => s.nodes);
  const promptValue = useFrameosStore((s) => s.promptValue);
  const setPromptValue = useFrameosStore((s) => s.setPromptValue);
  const selectedModel = useFrameosStore((s) => s.selectedModel);
  const setSelectedModel = useFrameosStore((s) => s.setSelectedModel);
  const currentGeneration = useFrameosStore((s) => s.currentGeneration);
  const startGeneration = useFrameosStore((s) => s.startGeneration);
  const edges = useFrameosStore((s) => s.edges);
  const removeEdge = useFrameosStore((s) => s.removeEdge);
  const setFocusModeNodeId = useFrameosStore((s) => s.setFocusModeNodeId);
  const setRefSelectTargetId = useFrameosStore((s) => s.setRefSelectTargetId);
  const storyboardMode = useFrameosStore((s) => s.storyboardMode);
  const toggleStoryboardMode = useFrameosStore((s) => s.toggleStoryboardMode);
  // Batch 180: 面板跟随选中节点 (源站: 面板在节点下方 12px, 随节点/缩放移动)
  const [pos, setPos] = useState<{ left: number; top: number } | null>(null);
  // Batch 190: 全屏编辑态 (编辑器居中放大)
  const [isFullscreenEdit, setIsFullscreenEdit] = useState(false);

  const sel = selectedNodeId ? nodes.find((n) => n.id === selectedNodeId) : undefined;

  useEffect(() => {
    if (!selectedNodeId || !sel || sel.type === "text") {
      // 无选中/文本节点时组件返回 null, 陈旧 pos 无需清理 (避免 effect 内同步 setState)
      return undefined;
    }
    let raf = 0;
    const tick = () => {
      const el = document.querySelector(
        `.react-flow__node[data-id="${CSS.escape(selectedNodeId)}"]`
      );
      if (!el) {
        raf = requestAnimationFrame(tick);
        return;
      }
      const r = el.getBoundingClientRect();
      const width = 480;
      const left = Math.max(
        12,
        Math.min(r.left + r.width / 2 - width / 2, window.innerWidth - width - 12),
      );
      const top = Math.min(r.bottom + 12, window.innerHeight - 200);
      setPos((prev) => {
        if (prev && Math.abs(prev.left - left) < 0.5 && Math.abs(prev.top - top) < 0.5) {
          return prev;
        }
        return { left, top };
      });
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [selectedNodeId, sel]);

  if (!selectedNodeId || !sel || sel.type === "text") return null;

  const isRunning = currentGeneration?.status === "running";
  // 源站语义: 引用 = 连线; 面板头部展示每个上游节点的引用芯片
  const incomingEdges = edges.filter((e) => e.target === sel.id);
  const removeIncomingEdges = () => {
    for (const e of incomingEdges) removeEdge(e.id);
  };

  // 2026-09-23 源站面板默认模型 Seedream 5.0 Pro; 其余条目为历史 mock 选项
  const modelOptions = ["Seedream 5.0 Pro", "帧界 O2.5", "帧界 O2", "帧界 v1.5", "Stable Diffusion XL", "Midjourney v6"];

  if (isFullscreenEdit) {
    return (
      <div
        data-frameos-fullscreen-editor
        style={{
          position: "fixed",
          left: "50%",
          transform: "translateX(-50%)",
          top: 80,
          width: 720,
          maxWidth: "calc(100vw - 32px)",
          background: "rgba(20,20,20,0.97)",
          border: "1px solid rgba(255,255,255,0.12)",
          borderRadius: 14,
          boxShadow: "0 24px 64px rgba(0,0,0,0.6)",
          zIndex: 3000,
          padding: 14,
          display: "flex",
          flexDirection: "column",
          gap: 10,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <span style={{ color: "#FFFFFF", fontSize: 14, fontWeight: 600 }}>全屏编辑</span>
          <button
            type="button"
            aria-label="退出全屏编辑"
            onClick={() => setIsFullscreenEdit(false)}
            style={{
              width: 26,
              height: 26,
              borderRadius: 6,
              border: "none",
              background: "transparent",
              color: "#A3A3A3",
              fontSize: 15,
              cursor: "pointer",
            }}
          >
            ×
          </button>
        </div>
        <textarea
          value={promptValue}
          onChange={(e) => setPromptValue(e.target.value)}
          placeholder={
            storyboardMode
              ? "描述一个 10-15 秒内能演完的小剧情片段，系统会整理为 4-8 个连续分镜，内容过长时会自动提炼关键剧情。提供角色三视图、美术设定图及准确的需求描述，生成效果会更好。"
              : "描述你想要的图像，@引用素材"
          }
          style={{
            width: "100%",
            height: 320,
            background: "#0D0D0D",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: 10,
            color: "#FFFFFF",
            fontSize: 14,
            padding: 12,
            outline: "none",
            resize: "none",
          }}
        />
        <div style={{ display: "flex", justifyContent: "flex-end" }}>
          <button
            type="button"
            aria-label="完成全屏编辑"
            onClick={() => setIsFullscreenEdit(false)}
            style={{
              height: 32,
              padding: "0 16px",
              borderRadius: 8,
              border: "none",
              background: "#3B82F6",
              color: "#FFFFFF",
              fontSize: 13,
              cursor: "pointer",
            }}
          >
            完成
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      className="frameos-prompt-editor"
      style={{
        position: "fixed",
        left: pos ? pos.left : 12,
        top: pos ? pos.top : 12,
        width: 480,
        maxWidth: "calc(100vw - 24px)",
        background: "rgba(20,20,20,0.85)",
        backdropFilter: "blur(12px)",
        border: "1px solid rgba(255,255,255,0.06)",
        borderRadius: 14,
        boxShadow: "0 12px 36px rgba(0,0,0,0.5)",
        zIndex: 2500,
        display: "flex",
        flexDirection: "column",
        padding: 10,
        gap: 8,
        animation: "frameos-pop-in 0.2s ease-out",
      }}
    >
      {/* 顶部工具行: 聚焦 / 故事版 / 参考 + 上游引用芯片 + 删除连线 / 替换参考
          (2026-09-23 源站实测: 芯片 = 上游节点图标 + 移除 ×; 删除连线移除全部入边) */}
      <div
        className="prompt-top-actions"
        data-frameos-prompt-top-actions
        style={{
          display: "flex",
          alignItems: "center",
          gap: 4,
        }}
      >
        <TileBtn icon="⌖" label="聚焦" onClick={() => setFocusModeNodeId(sel.id)} />
        <TileBtn
          icon="❒"
          label="故事版"
          active={storyboardMode}
          onClick={toggleStoryboardMode}
        />
        <TileBtn icon="＋" label="参考" onClick={() => setRefSelectTargetId(sel.id)} />
        {incomingEdges.map((e) => {
          const src = nodes.find((n) => n.id === e.source);
          return (
            <div
              key={e.id}
              className="frameos-ref-chip"
              data-frameos-ref-chip
              title={`引用 ${src?.data.title ?? "上游节点"}`}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 4,
                height: 36,
                padding: "0 6px",
                borderRadius: 8,
                border: "1px solid rgba(96,165,250,0.6)",
                background: "rgba(59,130,246,0.10)",
                marginLeft: 4,
              }}
            >
              <span
                aria-hidden
                style={{
                  width: 16,
                  height: 16,
                  borderRadius: 4,
                  background: "rgba(59,130,246,0.35)",
                  color: "#FFFFFF",
                  fontSize: 11,
                  fontWeight: 700,
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                T
              </span>
              <button
                type="button"
                data-frameos-ref-remove
                aria-label="移除引用"
                title="移除引用"
                onClick={() => removeEdge(e.id)}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: 16,
                  height: 16,
                  border: "none",
                  background: "transparent",
                  color: "#A3A3A3",
                  cursor: "pointer",
                  padding: 0,
                }}
              >
                <CloseIcon size={12} />
              </button>
            </div>
          );
        })}
        <div style={{ flex: 1 }} />
        <MiniBtn
          icon="⊘"
          label="删除连线"
          onClick={removeIncomingEdges}
        />
        <MiniBtn icon="⧉" label="替换参考" onClick={() => window.alert("替换参考 (mock)")} />
      </div>

      {/* prompt textarea */}
      <div
        style={{
          position: "relative",
          background: "#0D0D0D",
          border: "1px solid rgba(255,255,255,0.06)",
          borderRadius: 10,
          padding: "10px 12px",
        }}
      >
        <textarea
          value={promptValue}
          onChange={(e) => setPromptValue(e.target.value)}
          placeholder={
            storyboardMode
              ? "描述一个 10-15 秒内能演完的小剧情片段，系统会整理为 4-8 个连续分镜，内容过长时会自动提炼关键剧情。提供角色三视图、美术设定图及准确的需求描述，生成效果会更好。"
              : "描述你想要的图像，@引用素材"
          }
          rows={3}
          style={{
            width: "100%",
            minHeight: 60,
            background: "transparent",
            border: "none",
            outline: "none",
            color: "#FFFFFF",
            fontSize: 13,
            fontFamily: "inherit",
            resize: "vertical",
            lineHeight: 1.5,
          }}
        />
        <button
          type="button"
          aria-label="全屏编辑"
          title="全屏编辑"
          onClick={() => setIsFullscreenEdit(true)}
          style={{
            position: "absolute",
            right: 8,
            top: 8,
            width: 24,
            height: 24,
            borderRadius: 6,
            background: "transparent",
            border: "none",
            color: "#7A7A7A",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.color = "#FFFFFF")}
          onMouseLeave={(e) => (e.currentTarget.style.color = "#7A7A7A")}
        >
          <FullscreenExitIcon size={14} />
        </button>
      </div>

      {/* 下行 (2026-09-23 源站实测): 模型 / 档位合并 chip / 高级设置 + 积分 60·30·5折 + 生成按钮 */}
      <div
        className="prompt-bottom-controls"
        style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
        }}
      >
        <Dropdown
          value={storyboardMode ? "帧界 O2.5" : selectedModel}
          onChange={setSelectedModel}
          options={modelOptions}
        />
        <Dropdown
          value="2K · 16:9"
          onChange={() => {}}
          options={["1K · 16:9", "2K · 16:9", "2K · 9:16", "4K · 16:9"]}
        />
        <MiniBtn icon="⚙" label="高级设置" onClick={() => window.alert("高级设置 (mock)")} />
        <div style={{ flex: 1 }} />
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            padding: "0 10px",
            height: 32,
            borderRadius: 8,
            background: "transparent",
            color: "#E0E0E0",
            fontSize: 13,
            cursor: "pointer",
          }}
        >
          <span
            aria-hidden
            style={{
              width: 14,
              height: 14,
              borderRadius: 9999,
              background: "#F5A623",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 9,
              color: "#5A3A00",
              fontWeight: 700,
            }}
          >
            ¥
          </span>
          <span>{storyboardMode ? "100" : "60"}</span>
          {!storyboardMode && (
            <>
              <span style={{ color: "#A3A3A3" }}>30</span>
              <span style={{ color: "#F5A623" }}>5折</span>
            </>
          )}
        </div>
        <button
          type="button"
          aria-label="生成"
          title="生成"
          disabled={isRunning}
          onClick={() => {
            if (!sel) return;
            startGeneration({
              prompt: promptValue,
              edgeIds: [],
              nodeIds: [sel.id],
            });
            setPromptValue("");
          }}
          style={{
            width: 32,
            height: 32,
            borderRadius: 16,
            background: isRunning ? "rgba(59,130,246,0.4)" : "#3B82F6",
            border: "none",
            color: "#FFFFFF",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: isRunning ? "wait" : "pointer",
            fontWeight: 600,
            fontSize: 14,
            boxShadow: isRunning
              ? "none"
              : "0 4px 12px rgba(59,130,246,0.5)",
            transition: "all 0.15s",
          }}
        >
          ↑
        </button>
      </div>
    </div>
  );
}

function TileBtn({
  icon,
  label,
  active,
  onClick,
}: {
  icon: string;
  label: string;
  active?: boolean;
  onClick?: () => void;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      onClick={onClick}
      style={{
        display: "inline-flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 2,
        width: 46,
        height: 42,
        borderRadius: 8,
        border: active
          ? "1px solid rgba(96,165,250,0.6)"
          : "1px solid transparent",
        background: active ? "rgba(59,130,246,0.16)" : "transparent",
        color: active ? "#60A5FA" : "#C2C2C2",
        fontSize: 11,
        cursor: "pointer",
        transition: "background 0.15s, color 0.15s",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = "rgba(255,255,255,0.05)";
        e.currentTarget.style.color = "#FFFFFF";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = "transparent";
        e.currentTarget.style.color = "#C2C2C2";
      }}
    >
      <span style={{ fontSize: 14, lineHeight: "16px" }}>{icon}</span>
      <span>{label}</span>
    </button>
  );
}

function MiniBtn({
  icon,
  label,
  onClick,
}: {
  icon: string;
  label: string;
  onClick?: () => void;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      onClick={onClick}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        height: 32,
        padding: "0 8px",
        borderRadius: 8,
        border: "none",
        background: "transparent",
        color: "#C2C2C2",
        fontSize: 12,
        cursor: "pointer",
        transition: "background 0.15s, color 0.15s",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = "rgba(255,255,255,0.05)";
        e.currentTarget.style.color = "#FFFFFF";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = "transparent";
        e.currentTarget.style.color = "#C2C2C2";
      }}
    >
      <span style={{ width: 14, display: "inline-flex", justifyContent: "center" }}>{icon}</span>
      <span>{label}</span>
    </button>
  );
}

function Dropdown({
  value,
  onChange,
  options,
}: {
  value: string;
  onChange: (v: string) => void;
  options: string[];
}) {
  return (
    <div
      style={{
        position: "relative",
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        height: 32,
        padding: "0 8px",
        borderRadius: 8,
        background: "transparent",
        color: "#E0E0E0",
        fontSize: 12,
        cursor: "pointer",
        userSelect: "none",
      }}
    >
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-label={value}
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          opacity: 0,
          cursor: "pointer",
        }}
      >
        {options.map((o) => (
          <option key={o} value={o}>{o}</option>
        ))}
      </select>
      <span>{value}</span>
      <ArrowDownIcon size={10} color="#A3A3A3" />
    </div>
  );
}

/**
 * FrameOS 参考选择模式顶栏 (2026-09-24 源站实测, Batch 197):
 * 面板头部点「参考」进入——蓝色顶栏「从画布选择参考 / 返回节点 / ×」,
 * 点击画布上其他节点即加为参考 (建立连线); Esc / 返回节点 / × 退出。
 */
export function FrameosRefSelectBar() {
  const refSelectTargetId = useFrameosStore((s) => s.refSelectTargetId);
  const setRefSelectTargetId = useFrameosStore((s) => s.setRefSelectTargetId);
  if (!refSelectTargetId) return null;
  return (
    <div
      data-frameos-ref-select-bar
      style={{
        position: "fixed",
        top: 8,
        left: "50%",
        transform: "translateX(-50%)",
        zIndex: 2950,
        display: "inline-flex",
        alignItems: "center",
        gap: 10,
        padding: "8px 12px",
        background: "#3B82F6",
        borderRadius: 10,
        color: "#FFFFFF",
        fontSize: 13,
        boxShadow: "0 8px 24px rgba(59,130,246,0.4)",
      }}
    >
      <span
        aria-hidden
        style={{
          width: 18,
          height: 18,
          borderRadius: 4,
          background: "rgba(255,255,255,0.25)",
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 11,
        }}
      >
        ◧
      </span>
      <span>从画布选择参考</span>
      <button
        type="button"
        data-frameos-ref-select-back
        onClick={() => setRefSelectTargetId(null)}
        style={{
          height: 28,
          padding: "0 10px",
          borderRadius: 6,
          border: "1px solid rgba(255,255,255,0.4)",
          background: "transparent",
          color: "#FFFFFF",
          fontSize: 12,
          cursor: "pointer",
        }}
      >
        返回节点
      </button>
      <button
        type="button"
        aria-label="关闭参考选择"
        onClick={() => setRefSelectTargetId(null)}
        style={{
          width: 22,
          height: 22,
          borderRadius: 6,
          border: "none",
          background: "transparent",
          color: "#FFFFFF",
          fontSize: 14,
          cursor: "pointer",
        }}
      >
        ×
      </button>
    </div>
  );
}
