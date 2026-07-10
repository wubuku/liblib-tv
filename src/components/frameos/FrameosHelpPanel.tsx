"use client";

import { useFrameosStore } from "@/store/frameosStore";
import { CloseIcon } from "./icons";

/**
 * FrameOS 快捷键参考面板 (frameos.cn "?" 触发)
 * - 4 个 section: 创作 / 缩放 / 移动画布 / 其他
 * - 每行 label + key chips (kbd 风格)
 */

interface Shortcut {
  label: string;
  keys: string[];
}

interface Section {
  title: string;
  rows: Shortcut[];
}

const SECTIONS: Section[] = [
  {
    title: "创作",
    rows: [
      { label: "复制", keys: ["⌘", "C"] },
      { label: "剪切", keys: ["⌘", "X"] },
      { label: "粘贴", keys: ["⌘", "V"] },
      { label: "原地复制", keys: ["⌘", "D"] },
      { label: "拖拽复制", keys: ["⌥"] },
      { label: "全选", keys: ["⌘", "A"] },
      { label: "保存", keys: ["⌘", "S"] },
    ],
  },
  {
    title: "缩放",
    rows: [
      { label: "放大", keys: ["⌘", "+"] },
      { label: "缩小", keys: ["⌘", "−"] },
      { label: "重置视图", keys: ["⌘", "0"] },
      { label: "触控板", keys: [] },
      { label: "鼠标滚轮", keys: ["⌘"] },
    ],
  },
  {
    title: "移动画布",
    rows: [
      { label: "空格拖动", keys: ["Space"] },
      { label: "触控板", keys: [] },
      { label: "鼠标", keys: [] },
      { label: "滚轮", keys: [] },
    ],
  },
  {
    title: "其他",
    rows: [
      { label: "撤销", keys: ["⌘", "Z"] },
      { label: "重做", keys: ["⌘", "⇧", "Z"] },
      { label: "删除", keys: ["⌫"] },
      { label: "小地图", keys: ["M"] },
      { label: "帮助", keys: ["?"] },
      { label: "取消选中", keys: ["Esc"] },
    ],
  },
];

export function FrameosHelpPanel() {
  const isHelpOpen = useFrameosStore((s) => s.isHelpOpen);
  const closeHelp = useFrameosStore((s) => s.closeHelp);

  if (!isHelpOpen) return null;

  return (
    <>
      <div
        style={{ position: "fixed", inset: 0, zIndex: 4000, background: "rgba(0,0,0,0.5)" }}
        onClick={closeHelp}
        aria-hidden
      />
      <aside
        role="dialog"
        aria-label="快捷键参考"
        className="frameos-shortcuts-panel"
        style={{
          position: "fixed",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          width: 640,
          maxWidth: "calc(100vw - 32px)",
          maxHeight: "calc(100vh - 64px)",
          background: "#1C1C1C",
          border: "1px solid rgba(255,255,255,0.12)",
          borderRadius: 16,
          boxShadow: "0 24px 64px rgba(0,0,0,0.6)",
          zIndex: 4001,
          display: "flex",
          flexDirection: "column",
          animation: "frameos-pop-in 0.2s ease-out",
          overflow: "hidden",
        }}
      >
        {/* Header */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "16px 20px",
            borderBottom: "1px solid rgba(255,255,255,0.08)",
          }}
        >
          <h2
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              color: "#FFFFFF",
              fontSize: 16,
              fontWeight: 600,
              margin: 0,
            }}
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#60A5FA"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <rect x="2" y="6" width="20" height="14" rx="2" />
              <path d="M6 10h.01M10 10h.01M14 10h.01M18 10h.01M6 14h12" />
            </svg>
            快捷键
          </h2>
          <button
            type="button"
            aria-label="关闭"
            onClick={closeHelp}
            style={{
              width: 28,
              height: 28,
              borderRadius: 6,
              border: "none",
              background: "transparent",
              color: "#A3A3A3",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "rgba(255,255,255,0.05)";
              e.currentTarget.style.color = "#FFFFFF";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "transparent";
              e.currentTarget.style.color = "#A3A3A3";
            }}
          >
            <CloseIcon size={14} />
          </button>
        </div>

        {/* Body: 2-column grid 4 sections */}
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "20px",
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 20,
          }}
        >
          {SECTIONS.map((section) => (
            <section
              key={section.title}
              style={{
                background: "rgba(255,255,255,0.02)",
                border: "1px solid rgba(255,255,255,0.04)",
                borderRadius: 10,
                padding: 12,
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  marginBottom: 10,
                }}
              >
                <span
                  aria-hidden
                  style={{
                    width: 22,
                    height: 22,
                    borderRadius: 6,
                    background: "rgba(59,130,246,0.18)",
                    color: "#60A5FA",
                    display: "inline-flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 12,
                  }}
                >
                  ✎
                </span>
                <span
                  style={{
                    color: "#FFFFFF",
                    fontSize: 13,
                    fontWeight: 600,
                  }}
                >
                  {section.title}
                </span>
              </div>
              <ul
                style={{
                  listStyle: "none",
                  padding: 0,
                  margin: 0,
                  display: "flex",
                  flexDirection: "column",
                  gap: 4,
                }}
              >
                {section.rows.map((row) => (
                  <li
                    key={row.label}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      gap: 12,
                      padding: "5px 8px",
                      borderRadius: 4,
                    }}
                  >
                    <span style={{ color: "#C2C2C2", fontSize: 13 }}>{row.label}</span>
                    <span
                      aria-label={row.keys.join(" ")}
                      style={{ display: "inline-flex", gap: 4 }}
                    >
                      {row.keys.length === 0 ? (
                        <span style={{ color: "#5A5A5A", fontSize: 11 }}>—</span>
                      ) : (
                        row.keys.map((k, i) => (
                          <kbd
                            key={i}
                            style={{
                              minWidth: 22,
                              height: 22,
                              padding: "0 6px",
                              display: "inline-flex",
                              alignItems: "center",
                              justifyContent: "center",
                              background: "rgba(255,255,255,0.08)",
                              border: "1px solid rgba(255,255,255,0.12)",
                              borderBottom: "2px solid rgba(255,255,255,0.2)",
                              borderRadius: 4,
                              color: "#FFFFFF",
                              fontSize: 11,
                              fontFamily:
                                "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
                              fontWeight: 600,
                            }}
                          >
                            {k}
                          </kbd>
                        ))
                      )}
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      </aside>
    </>
  );
}
