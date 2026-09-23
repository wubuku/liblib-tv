"use client";

import { useState } from "react";
import { useFrameosStore } from "@/store/frameosStore";
import { LayoutGridIcon } from "./icons";

/**
 * FrameOS 模板面板 (2026-09-23 源站实测, SOURCE_OBSERVATIONS §14):
 * - 左栏「模板」按钮开关 (源站行为: 按钮切换, Esc 不关闭)
 * - 页签: 公共模板 / 企业模板 / 我的模板 (公共模板默认激活)
 * - 模板卡片: 30s小说切片 / 九宫格大师分镜 / 大师电影分镜 / 时间凝固流光 /
 *   暂别×视角×特效镜头大全 / 360度旋转展示
 * - 模板卡片的应用结果源站未采样: 点击保持 mock, 不复刻创建流程
 */

const TEMPLATE_TABS = ["公共模板", "企业模板", "我的模板"] as const;

const TEMPLATE_CARDS: { name: string; tone: string }[] = [
  { name: "30s小说切片", tone: "linear-gradient(160deg, #2A2A2A, #1A1A1A)" },
  { name: "九宫格大师分镜", tone: "linear-gradient(160deg, #26282E, #16171B)" },
  { name: "大师电影分镜", tone: "linear-gradient(160deg, #22303C, #141B22)" },
  { name: "时间凝固流光", tone: "linear-gradient(160deg, #302A22, #1B1712)" },
  { name: "暂别×视角×特效镜头大全", tone: "linear-gradient(160deg, #2E2630, #1A151C)" },
  { name: "360度旋转展示", tone: "linear-gradient(160deg, #26302A, #161B17)" },
];

export function FrameosTemplatePanel() {
  const isTemplatePanelOpen = useFrameosStore((s) => s.isTemplatePanelOpen);
  const toggleTemplatePanel = useFrameosStore((s) => s.toggleTemplatePanel);
  const [activeTab, setActiveTab] = useState<(typeof TEMPLATE_TABS)[number]>("公共模板");

  if (!isTemplatePanelOpen) return null;

  return (
    <div
      data-frameos-template-panel
      style={{
        position: "fixed",
        left: 72,
        top: 108,
        width: 368,
        maxHeight: "calc(100vh - 220px)",
        overflow: "auto",
        background: "#161616",
        border: "1px solid rgba(255,255,255,0.08)",
        borderRadius: 14,
        boxShadow: "0 12px 36px rgba(0,0,0,0.5)",
        zIndex: 2650,
        padding: 12,
      }}
    >
      <div
        style={{
          display: "flex",
          gap: 6,
          marginBottom: 10,
        }}
      >
        {TEMPLATE_TABS.map((tab) => {
          const active = tab === activeTab;
          return (
            <button
              key={tab}
              type="button"
              data-frameos-template-tab={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                flex: 1,
                height: 32,
                borderRadius: 8,
                border: active ? "1px solid rgba(96,165,250,0.6)" : "1px solid transparent",
                background: active ? "rgba(59,130,246,0.16)" : "transparent",
                color: active ? "#60A5FA" : "#A3A3A3",
                fontSize: 13,
                cursor: "pointer",
              }}
            >
              {tab}
            </button>
          );
        })}
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: 8,
        }}
      >
        {TEMPLATE_CARDS.map((card) => (
          <button
            key={card.name}
            type="button"
            data-frameos-template-card={card.name}
            title={`${card.name} (应用流程未验证)`}
            onClick={() => window.alert(`模板「${card.name}」应用 (mock，未验证)`)}
            style={{
              border: "none",
              borderRadius: 10,
              background: card.tone,
              cursor: "pointer",
              overflow: "hidden",
              padding: 0,
              textAlign: "left",
            }}
          >
            <div style={{ height: 64 }} />
            <div
              style={{
                color: "#C2C2C2",
                fontSize: 11,
                padding: "4px 6px 6px",
                whiteSpace: "normal",
                lineHeight: 1.3,
              }}
            >
              {card.name}
            </div>
          </button>
        ))}
      </div>

      <button
        type="button"
        aria-label="关闭模板面板"
        title="关闭模板面板"
        onClick={toggleTemplatePanel}
        style={{
          position: "absolute",
          right: 10,
          top: 10,
          width: 24,
          height: 24,
          borderRadius: 6,
          border: "none",
          background: "transparent",
          color: "#7A7A7A",
          cursor: "pointer",
          fontSize: 14,
        }}
      >
        ×
      </button>
    </div>
  );
}

/** 左栏「模板」按钮 (供 FrameosToolRail 使用, 保持 rail 单一来源) */
export function TemplateRailEntry() {
  const isTemplatePanelOpen = useFrameosStore((s) => s.isTemplatePanelOpen);
  const toggleTemplatePanel = useFrameosStore((s) => s.toggleTemplatePanel);
  return (
    <button
      type="button"
      aria-label="模板"
      title="模板"
      data-frameos-template-button
      onClick={toggleTemplatePanel}
      style={{
        width: 32,
        height: 32,
        borderRadius: 8,
        border: "none",
        background: isTemplatePanelOpen ? "rgba(255,255,255,0.05)" : "transparent",
        color: "#C2C2C2",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
        transition: "background 0.15s, color 0.15s",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = "rgba(255,255,255,0.05)";
        e.currentTarget.style.color = "#FFFFFF";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = isTemplatePanelOpen
          ? "rgba(255,255,255,0.05)"
          : "transparent";
        e.currentTarget.style.color = "#C2C2C2";
      }}
    >
      <LayoutGridIcon size={18} />
    </button>
  );
}
