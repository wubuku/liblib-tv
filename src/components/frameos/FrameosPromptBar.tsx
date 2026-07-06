"use client";

import { useRef, useState, useMemo } from "react";
import { ScissorsIcon, FullscreenIcon, FullscreenExitIcon, ArrowDownIcon, AddLineIcon } from "./icons";
import { useFrameosStore } from "@/store/frameosStore";

const MODELS = [
  { id: "O2", name: "帧界 O2", icon: "🔷" },
  { id: "O2-trial", name: "帧界 O2 体验版", icon: "🔷" },
  { id: "G2", name: "帧界 G2", icon: "🟢" },
  { id: "G-Pro", name: "帧界 G Pro", icon: "🟢" },
  { id: "1.0", name: "帧界 1.0", icon: "🟡" },
];

const SIZES = ["1K", "2K", "4K"];
const RATIOS = ["16:9", "1:1", "9:16", "4:3", "3:4"];

/**
 * FrameOS 底部 prompt 输入栏 + 模型选择栏
 * 浮动条，仅在节点被选中时显示，定位在选中节点下方
 * 支持全屏编辑模式
 */
export function FrameosPromptBar() {
  const promptValue = useFrameosStore((s) => s.promptValue);
  const setPromptValue = useFrameosStore((s) => s.setPromptValue);
  const selectedNodeId = useFrameosStore((s) => s.selectedNodeId);
  const nodes = useFrameosStore((s) => s.nodes);
  const selectedModel = useFrameosStore((s) => s.selectedModel);
  const setSelectedModel = useFrameosStore((s) => s.setSelectedModel);
  const isFullscreen = useFrameosStore((s) => s.isPromptFullscreen);
  const toggleFullscreen = useFrameosStore((s) => s.togglePromptFullscreen);
  const inputRef = useRef<HTMLDivElement>(null);

  const [modelOpen, setModelOpen] = useState(false);
  const [sizeOpen, setSizeOpen] = useState(false);
  const [ratioOpen, setRatioOpen] = useState(false);
  const [showMore, setShowMore] = useState(false);

  const selectedNode = useMemo(
    () => nodes.find((n) => n.id === selectedNodeId),
    [nodes, selectedNodeId]
  );

  if (!selectedNode) return null;

  const pos = selectedNode.position;
  const nodeW = (selectedNode.style?.width as number) ?? 300;
  const nodeH = (selectedNode.style?.height as number) ?? 169;
  const left = pos.x + nodeW / 2;
  const top = pos.y + nodeH + 12;

  return (
    <div
      className={`canvas-footer-prompt ${isFullscreen ? "is-fullscreen" : ""}`}
      style={{
        position: "absolute",
        left: isFullscreen ? "50%" : left,
        top: isFullscreen ? 80 : top,
        transform: isFullscreen ? "translate(-50%, 0)" : "translateX(-50%)",
        zIndex: isFullscreen ? 3000 : 2700,
        width: isFullscreen ? "min(900px, calc(100vw - 48px))" : 760,
        maxWidth: "calc(100vw - 48px)",
        transition: "all 0.2s ease",
      }}
    >
      <div
        className="prompt-shell"
        style={{
          background: "#1C1C1C",
          border: "1px solid rgba(255,255,255,0.12)",
          borderRadius: 14,
          padding: isFullscreen ? "20px 22px" : "12px 14px",
          boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
          maxHeight: isFullscreen ? "calc(100vh - 160px)" : undefined,
          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* 顶部：节点缩略图 + 输入框 + 全屏/退出 */}
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            gap: 10,
            marginBottom: 10,
          }}
        >
          {selectedNode.data.imageUrl && (
            <div
              style={{
                width: isFullscreen ? 80 : 48,
                height: isFullscreen ? 80 : 48,
                borderRadius: 8,
                overflow: "hidden",
                flexShrink: 0,
                background: "#0D0D0D",
                border: "1px solid rgba(255,255,255,0.08)",
                transition: "all 0.2s",
              }}
            >
              <img
                src={selectedNode.data.imageUrl}
                alt={selectedNode.data.title}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                  display: "block",
                }}
              />
            </div>
          )}

          <div
            ref={inputRef}
            contentEditable
            suppressContentEditableWarning
            data-placeholder="描述你想要的图像，@引用素材"
            className={`tb-mention-input ${promptValue ? "" : "has-placeholder"}`}
            onInput={(e) => setPromptValue((e.target as HTMLDivElement).textContent ?? "")}
            style={{
              flex: 1,
              minHeight: isFullscreen ? 200 : 48,
              color: "#FFFFFF",
              fontSize: isFullscreen ? 16 : 14,
              outline: "none",
              background: "transparent",
              border: "none",
              padding: "4px 0",
              cursor: "text",
              lineHeight: isFullscreen ? "28px" : "22px",
              transition: "all 0.2s",
            }}
          />

          <button
            type="button"
            aria-label={isFullscreen ? "退出全屏" : "全屏编辑"}
            onClick={toggleFullscreen}
            style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              border: "1px solid rgba(255,255,255,0.08)",
              background: isFullscreen ? "rgba(59,130,246,0.16)" : "transparent",
              color: isFullscreen ? "#60A5FA" : "#A3A3A3",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
              flexShrink: 0,
              transition: "background 0.15s, color 0.15s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = isFullscreen
                ? "rgba(59,130,246,0.24)"
                : "rgba(255,255,255,0.05)";
              e.currentTarget.style.color = "#FFFFFF";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = isFullscreen
                ? "rgba(59,130,246,0.16)"
                : "transparent";
              e.currentTarget.style.color = isFullscreen ? "#60A5FA" : "#A3A3A3";
            }}
          >
            {isFullscreen ? <FullscreenExitIcon size={14} /> : <FullscreenIcon size={14} />}
          </button>
        </div>

        {/* 底部：模型选择 + 更多参数 + 积分 + 提交 */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 8,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 4, position: "relative" }}>
            <Dropdown
              label={selectedModel}
              open={modelOpen}
              onToggle={() => {
                setModelOpen((v) => !v);
                setSizeOpen(false);
                setRatioOpen(false);
              }}
              onClose={() => setModelOpen(false)}
              icon={<span style={{ width: 18, height: 18, borderRadius: 4, background: "linear-gradient(135deg, #3B82F6, #1D4ED8)", display: "inline-block" }} />}
            >
              {MODELS.map((m) => (
                <DropdownItem
                  key={m.id}
                  icon={m.icon}
                  label={m.name}
                  selected={selectedModel === m.name}
                  onClick={() => {
                    setSelectedModel(m.name);
                    setModelOpen(false);
                  }}
                />
              ))}
            </Dropdown>

            <Dropdown
              label="1K"
              open={sizeOpen}
              onToggle={() => {
                setSizeOpen((v) => !v);
                setModelOpen(false);
                setRatioOpen(false);
              }}
              onClose={() => setSizeOpen(false)}
            >
              {SIZES.map((s) => (
                <DropdownItem key={s} label={s} onClick={() => setSizeOpen(false)} />
              ))}
            </Dropdown>

            <Dropdown
              label="16:9"
              open={ratioOpen}
              onToggle={() => {
                setRatioOpen((v) => !v);
                setModelOpen(false);
                setSizeOpen(false);
              }}
              onClose={() => setRatioOpen(false)}
            >
              {RATIOS.map((r) => (
                <DropdownItem key={r} label={r} onClick={() => setRatioOpen(false)} />
              ))}
            </Dropdown>

            <Pill onClick={() => setShowMore((v) => !v)} active={showMore}>
              <AddLineIcon size={12} />
              <span>更多参数</span>
              <ArrowDownIcon size={12} />
            </Pill>

            {showMore && (
              <div
                style={{
                  position: "absolute",
                  top: "calc(100% + 8px)",
                  left: 0,
                  background: "#1C1C1C",
                  border: "1px solid rgba(255,255,255,0.12)",
                  borderRadius: 10,
                  padding: 12,
                  boxShadow: "0 8px 24px rgba(0,0,0,0.5)",
                  width: 280,
                  zIndex: 2701,
                }}
              >
                <div style={{ color: "#A3A3A3", fontSize: 12, marginBottom: 8 }}>采样率</div>
                <div style={{ display: "flex", gap: 4, marginBottom: 12 }}>
                  {["1", "2", "3", "4", "5"].map((s, i) => (
                    <Pill key={s} active={i === 2} onClick={() => {}}>{s}</Pill>
                  ))}
                </div>
                <div style={{ color: "#A3A3A3", fontSize: 12, marginBottom: 8 }}>镜头运镜</div>
                <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                  {["静止", "推近", "拉远", "平移", "环绕"].map((m) => (
                    <Pill key={m} onClick={() => {}}>{m}</Pill>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 4,
                padding: "0 4px",
                color: "#E0E0E0",
                fontSize: 13,
              }}
            >
              <span
                style={{
                  width: 14,
                  height: 14,
                  borderRadius: 3,
                  background: "#FFC35E",
                  display: "inline-block",
                }}
              />
              <span>60</span>
            </span>
            <button
              type="button"
              disabled={!promptValue}
              aria-label="提交"
              style={{
                width: 32,
                height: 32,
                borderRadius: 8,
                border: "none",
                background: promptValue ? "#3B82F6" : "rgba(59,130,246,0.3)",
                color: "#FFFFFF",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: promptValue ? "pointer" : "not-allowed",
                transition: "all 0.15s",
                boxShadow: promptValue ? "0 0 0 4px rgba(59,130,246,0.18)" : "none",
              }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <path
                  d="M12 19V5M5 12l7-7 7 7"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Pill({
  children,
  active,
  onClick,
}: {
  children: React.ReactNode;
  active?: boolean;
  onClick?: () => void;
}) {
  return (
    <span
      onClick={onClick}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        padding: "5px 8px",
        background: active ? "rgba(59,130,246,0.16)" : "rgba(255,255,255,0.04)",
        border: `1px solid ${active ? "rgba(96,165,250,0.5)" : "rgba(255,255,255,0.06)"}`,
        borderRadius: 8,
        color: active ? "#60A5FA" : "#E0E0E0",
        fontSize: 13,
        cursor: "pointer",
        userSelect: "none",
        transition: "background 0.15s, border-color 0.15s",
      }}
      onMouseEnter={(e) => {
        if (!active) {
          e.currentTarget.style.background = "rgba(255,255,255,0.08)";
          e.currentTarget.style.borderColor = "rgba(255,255,255,0.12)";
        }
      }}
      onMouseLeave={(e) => {
        if (!active) {
          e.currentTarget.style.background = "rgba(255,255,255,0.04)";
          e.currentTarget.style.borderColor = "rgba(255,255,255,0.06)";
        }
      }}
    >
      {children}
    </span>
  );
}

interface DropdownProps {
  label: string;
  open: boolean;
  onToggle: () => void;
  onClose: () => void;
  children: React.ReactNode;
  icon?: React.ReactNode;
}

function Dropdown({ label, open, onToggle, onClose, children, icon }: DropdownProps) {
  const ref = useRef<HTMLDivElement>(null);
  return (
    <div ref={ref} style={{ position: "relative" }}>
      <Pill onClick={onToggle} active={open}>
        {icon}
        <span>{label}</span>
        <ArrowDownIcon size={12} />
      </Pill>
      {open && (
        <>
          <div
            style={{ position: "fixed", inset: 0, zIndex: 2700 }}
            onClick={onClose}
          />
          <div
            style={{
              position: "absolute",
              top: "calc(100% + 6px)",
              left: 0,
              background: "#1C1C1C",
              border: "1px solid rgba(255,255,255,0.12)",
              borderRadius: 10,
              padding: 6,
              boxShadow: "0 8px 24px rgba(0,0,0,0.5)",
              minWidth: 160,
              zIndex: 2701,
            }}
          >
            {children}
          </div>
        </>
      )}
    </div>
  );
}

function DropdownItem({
  label,
  icon,
  selected,
  onClick,
}: {
  label: string;
  icon?: React.ReactNode;
  selected?: boolean;
  onClick?: () => void;
}) {
  return (
    <div
      onClick={onClick}
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        padding: "8px 10px",
        borderRadius: 6,
        background: selected ? "rgba(59,130,246,0.16)" : "transparent",
        color: selected ? "#60A5FA" : "#FFFFFF",
        fontSize: 13,
        cursor: "pointer",
        transition: "background 0.15s",
      }}
      onMouseEnter={(e) => {
        if (!selected) e.currentTarget.style.background = "rgba(255,255,255,0.05)";
      }}
      onMouseLeave={(e) => {
        if (!selected) e.currentTarget.style.background = "transparent";
      }}
    >
      {icon && <span>{icon}</span>}
      <span style={{ flex: 1 }}>{label}</span>
      {selected && (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
          <path
            d="M5 12l5 5L20 7"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      )}
    </div>
  );
}
