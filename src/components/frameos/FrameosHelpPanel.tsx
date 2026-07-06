"use client";

import { useFrameosStore } from "@/store/frameosStore";
import { CloseIcon } from "./icons";

const SHORTCUTS = [
  { keys: ["⌘", "Z"], desc: "撤销上一步" },
  { keys: ["⌘", "⇧", "Z"], desc: "重做" },
  { keys: ["⌘", "D"], desc: "复制选中节点" },
  { keys: ["Delete"], desc: "删除选中节点" },
  { keys: ["Esc"], desc: "取消选中 / 退出全屏编辑" },
  { keys: ["?"], desc: "打开/关闭此帮助面板" },
  { keys: ["+"], desc: "放大画布" },
  { keys: ["-"], desc: "缩小画布" },
  { keys: ["0"], desc: "适应画布" },
  { keys: ["Space", "拖动"], desc: "平移画布" },
];

const ACTIONS = [
  { title: "添加节点", desc: "点击左侧蓝色 + 按钮，选择文本/图片/视频类型" },
  { title: "选中节点", desc: "点击节点卡片即可选中，节点显示连接端口和编辑面板" },
  { title: "连接节点", desc: "从节点的右侧蓝色圆点拖动到另一节点的左侧端口" },
  { title: "删除连线", desc: "hover 边线时出现剪刀按钮，点击删除" },
  { title: "整理节点", desc: "点击左下角一键整理按钮，支持横向/纵向/网格三种模式" },
  { title: "全屏编辑", desc: "选中节点后，点击 PromptBar 右上角全屏图标" },
  { title: "替换素材", desc: "hover 图片/视频节点时显示上传图标，点击可替换内容" },
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
      />
      <div
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
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
          animation: "frameos-pop-in 0.2s ease-out",
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
          <div>
            <h2 style={{ color: "#FFFFFF", fontSize: 18, fontWeight: 600, margin: 0 }}>
              快捷键 & 操作指南
            </h2>
            <p style={{ color: "#A3A3A3", fontSize: 12, margin: "4px 0 0" }}>
              帮助你更快地上手帧界 FrameOS 画布
            </p>
          </div>
          <button
            type="button"
            aria-label="关闭帮助"
            onClick={closeHelp}
            style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              border: "none",
              background: "transparent",
              color: "#A3A3A3",
              display: "flex",
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
            <CloseIcon size={16} />
          </button>
        </div>

        {/* 内容 */}
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "20px",
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 24,
          }}
        >
          {/* 键盘快捷键 */}
          <section>
            <h3
              style={{
                color: "#60A5FA",
                fontSize: 12,
                fontWeight: 600,
                margin: "0 0 12px",
                textTransform: "uppercase",
                letterSpacing: 0.5,
              }}
            >
              键盘快捷键
            </h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {SHORTCUTS.map((s, i) => (
                <div
                  key={i}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "8px 10px",
                    background: "#0D0D0D",
                    borderRadius: 6,
                    border: "1px solid rgba(255,255,255,0.04)",
                  }}
                >
                  <span style={{ color: "#E0E0E0", fontSize: 13 }}>{s.desc}</span>
                  <div style={{ display: "flex", gap: 4 }}>
                    {s.keys.map((k, j) => (
                      <kbd
                        key={j}
                        style={{
                          minWidth: 22,
                          height: 22,
                          padding: "0 6px",
                          display: "inline-flex",
                          alignItems: "center",
                          justifyContent: "center",
                          background: "rgba(255,255,255,0.08)",
                          border: "1px solid rgba(255,255,255,0.12)",
                          borderBottom: "2px solid rgba(255,255,255,0.18)",
                          borderRadius: 4,
                          color: "#FFFFFF",
                          fontSize: 11,
                          fontFamily: "monospace",
                          fontWeight: 600,
                        }}
                      >
                        {k}
                      </kbd>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* 操作指南 */}
          <section>
            <h3
              style={{
                color: "#60A5FA",
                fontSize: 12,
                fontWeight: 600,
                margin: "0 0 12px",
                textTransform: "uppercase",
                letterSpacing: 0.5,
              }}
            >
              操作指南
            </h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {ACTIONS.map((a, i) => (
                <div
                  key={i}
                  style={{
                    padding: "10px 12px",
                    background: "#0D0D0D",
                    borderRadius: 8,
                    border: "1px solid rgba(255,255,255,0.04)",
                  }}
                >
                  <div style={{ color: "#FFFFFF", fontSize: 13, fontWeight: 500 }}>{a.title}</div>
                  <div style={{ color: "#A3A3A3", fontSize: 12, marginTop: 4 }}>{a.desc}</div>
                </div>
              ))}
            </div>
          </section>
        </div>

        {/* Footer */}
        <div
          style={{
            padding: "12px 20px",
            borderTop: "1px solid rgba(255,255,255,0.08)",
            color: "#7A7A7A",
            fontSize: 12,
            textAlign: "center",
          }}
        >
          按 <kbd style={{ padding: "1px 6px", background: "rgba(255,255,255,0.08)", borderRadius: 3, fontFamily: "monospace" }}>Esc</kbd> 或点击空白处关闭
        </div>
      </div>
    </>
  );
}
