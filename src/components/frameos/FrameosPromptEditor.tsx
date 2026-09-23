"use client";

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

  if (!selectedNodeId) return null;
  const sel = nodes.find((n) => n.id === selectedNodeId);
  // 2026-09-23 源站实测: 选中文本节点不出现 prompt 面板 (只有 全屏查看/下载 工具条)
  if (!sel || sel.type === "text") return null;

  const isRunning = currentGeneration?.status === "running";
  // 源站语义: 引用 = 连线; 面板头部展示每个上游节点的引用芯片
  const incomingEdges = edges.filter((e) => e.target === sel.id);
  const removeIncomingEdges = () => {
    for (const e of incomingEdges) removeEdge(e.id);
  };

  // 2026-09-23 源站面板默认模型 Seedream 5.0 Pro; 其余条目为历史 mock 选项
  const modelOptions = ["Seedream 5.0 Pro", "帧界 O2", "帧界 v1.5", "Stable Diffusion XL", "Midjourney v6"];

  return (
    <div
      className="frameos-prompt-editor"
      style={{
        position: "fixed",
        right: 12,
        bottom: 80,
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
        <MiniBtn
          icon="⌖"
          label="聚焦"
          onClick={() => {
            const el = document.querySelector(`.react-flow__node[data-id="${CSS.escape(sel.id)}"]`);
            el?.scrollIntoView({ behavior: "smooth", block: "center" });
          }}
        />
        <MiniBtn icon="❒" label="故事版" onClick={() => window.alert("故事版 (mock)")} />
        <MiniBtn icon="＋" label="参考" onClick={() => window.alert("参考 (mock)")} />
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
          placeholder="描述你想要的图像，@引用素材"
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
          onClick={() => window.alert("全屏编辑 (mock)")}
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
          value={selectedModel}
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
          <span>60</span>
          <span style={{ color: "#A3A3A3" }}>30</span>
          <span style={{ color: "#F5A623" }}>5折</span>
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
