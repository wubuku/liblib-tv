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
  keys?: string[];
  desc?: string;
}

interface Section {
  title: string;
  icon: string;
  rows: Shortcut[];
}

// 2026-09-23 源站逐字对齐 (SOURCE_OBSERVATIONS §13.9, Batch 166)
const SECTIONS: Section[] = [
  {
    title: "创作",
    icon: "✎",
    rows: [
      // ⚠️ Batch 346 教训: 这两行是**源站帮助面板的逐字转录**(见
      // verify-frameos-batch183.py 的 "help panel 26 verbatim shortcut rows",
      // 它锁的就是这些字符串, 源自 2026-09-24 源站新版本的重新采样)。
      //
      // 我一度把它们改写/删掉, 理由是「面板不该承诺 app 做不到的事」。**那是错的**:
      // 面板文本不是克隆自己的措辞, 而是**源站事实**。克隆的职责是复现源站,
      // 做不到就**如实记录差距**, 而不是把差距从证据里抹掉 ——
      // 抹掉等于改写证据让自己的论证好看, 这是最坏的一种「修复」。
      //
      // 因此: 文本保持逐字不动; 能兑现的部分去**实现**
      // (双击节点聚焦 → onNodeDoubleClick, 见 page.tsx); 兑现不了的部分
      // (双击空白添加哪种节点) 记录为**源站保真度差距**, 待源站可采样后按
      // 采样结果实现。详见 docs/research/liblib-frameos-batch346-2026-10-01/README.md。
      { label: "双击空白", desc: "双击空白处添加节点" },
      { label: "复制", keys: ["⌘", "C"] },
      { label: "剪切", keys: ["⌘", "X"] },
      { label: "粘贴", keys: ["⌘", "V"] },
      { label: "原地复制", keys: ["⌘", "D"] },
      { label: "拖拽复制", desc: "⌥ 拖动节点" },
      { label: "保存", keys: ["⌘", "S"] },
    ],
  },
  {
    title: "缩放",
    icon: "◎",
    rows: [
      // 同样是源站逐字转录, 保持不动(见上方「创作」区的 Batch 346 教训注释)。
      // 其中「双击节点聚焦填满视口」在克隆里**部分**成立: 文本节点双击进编辑、
      // 视频节点双击预览(两者都被节点自己的 handler 消费), 只有图片等会聚焦 ——
      // 批次 346 已实现后者。源站自身是否也如此需采样确认, 记为待核。
      { label: "双击节点", desc: "双击节点聚焦填满视口" },
      { label: "放大", keys: ["⌘", "+"] },
      { label: "缩小", keys: ["⌘", "−"] },
      { label: "重置视图", keys: ["⌘", "0"] },
      { label: "触控板", desc: "双指捏合" },
      { label: "鼠标滚轮", desc: "⌘ 滚轮" },
    ],
  },
  {
    title: "移动画布",
    icon: "✥",
    rows: [
      { label: "空格拖动", keys: ["Space"] },
      { label: "左键拖动" },
      { label: "触控板", desc: "双指平移" },
      { label: "鼠标中键 / 右键拖动" },
      { label: "滚轮", desc: "滚轮平移" },
    ],
  },
  {
    title: "其他",
    icon: "⚙",
    rows: [
      { label: "撤销", keys: ["⌘", "Z"] },
      { label: "重做", keys: ["⌘", "⇧", "Z"] },
      { label: "删除", keys: ["⌫"] },
      { label: "搜索节点", keys: ["⌘", "F"] },
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
          top: 108,
          left: 72,
          width: 320,
          height: 540,
          background: "#1C1C1C",
          border: "1px solid rgba(255,255,255,0.12)",
          borderRadius: 14,
          boxShadow: "0 12px 36px rgba(0,0,0,0.5)",
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
            padding: "12px",
            display: "flex",
            flexDirection: "column",
            gap: 12,
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
                  data-frameos-help-icon={section.title}
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
                  {section.icon}
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
                    // Batch 346: 与 FrameosToast 同类问题 —— 面板行只有内联样式,
                    // 没有任何标识属性。帮助面板是「承诺清单」, 验证器必须能逐条
                    // 读到它承诺了什么, 否则「面板是否在撒谎」根本测不了
                    // (Batch 345 的元缺陷重演)。
                    data-frameos-help-row=""
                    data-frameos-help-label={row.label}
                    data-frameos-help-desc={row.desc ?? ""}
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
                      aria-label={row.desc ?? row.keys?.join(" ") ?? ""}
                      style={{ display: "inline-flex", gap: 4, alignItems: "center" }}
                    >
                      {row.desc ? (
                        <span style={{ color: "#A3A3A3", fontSize: 12 }}>{row.desc}</span>
                      ) : row.keys && row.keys.length > 0 ? (
                        row.keys!.map((k, i) => (
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
                      ) : null}
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
