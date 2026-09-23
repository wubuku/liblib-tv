"use client";

import { useState } from "react";
import { useFrameosStore } from "@/store/frameosStore";

/**
 * FrameOS 项目资产面板 (2026-09-23 源站实测, SOURCE_OBSERVATIONS §13.10):
 * - 左栏「查看项目资产」按钮开关
 * - 页签: 角色 / 物品 / 环境 (角色默认激活)
 * - 搜索占位: "搜索资产名称..."
 * - 空态: "暂无已生成的资产图"
 * - × 关闭
 */

const ASSET_TABS = ["角色", "物品", "环境"] as const;

export function FrameosProjectAssetsPanel() {
  const isProjectAssetsPanelOpen = useFrameosStore(
    (s) => s.isProjectAssetsPanelOpen,
  );
  const toggleProjectAssetsPanel = useFrameosStore(
    (s) => s.toggleProjectAssetsPanel,
  );
  const [activeTab, setActiveTab] = useState<(typeof ASSET_TABS)[number]>("角色");

  if (!isProjectAssetsPanelOpen) return null;

  return (
    <div
      data-frameos-project-assets-panel
      style={{
        position: "fixed",
        left: 72,
        top: 108,
        width: 320,
        height: 540,
        background: "#161616",
        border: "1px solid rgba(255,255,255,0.08)",
        borderRadius: 14,
        boxShadow: "0 12px 36px rgba(0,0,0,0.5)",
        zIndex: 2650,
        display: "flex",
        flexDirection: "column",
        padding: 12,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "2px 4px",
        }}
      >
        <span style={{ color: "#FFFFFF", fontSize: 15, fontWeight: 600 }}>
          项目资产
        </span>
        <button
          type="button"
          aria-label="关闭项目资产面板"
          title="关闭项目资产面板"
          onClick={toggleProjectAssetsPanel}
          style={{
            width: 24,
            height: 24,
            borderRadius: 6,
            border: "none",
            background: "transparent",
            color: "#7A7A7A",
            fontSize: 15,
            cursor: "pointer",
          }}
        >
          ×
        </button>
      </div>

      <div
        style={{
          display: "flex",
          gap: 6,
          marginTop: 8,
        }}
      >
        {ASSET_TABS.map((tab) => {
          const active = tab === activeTab;
          return (
            <button
              key={tab}
              type="button"
              data-frameos-assets-tab={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                flex: 1,
                height: 32,
                borderRadius: 8,
                border: active
                  ? "1px solid rgba(96,165,250,0.6)"
                  : "1px solid transparent",
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

      <div style={{ marginTop: 10 }}>
        <input
          placeholder="搜索资产名称..."
          data-frameos-assets-search
          style={{
            width: "100%",
            height: 32,
            background: "#0D0D0D",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: 8,
            color: "#FFFFFF",
            fontSize: 13,
            padding: "0 10px",
            outline: "none",
          }}
        />
      </div>

      <div
        style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#7A7A7A",
          fontSize: 13,
        }}
      >
        暂无已生成的资产图
      </div>
    </div>
  );
}

/** 左栏「查看项目资产」按钮 (供 FrameosToolRail 使用) */
export function ProjectAssetsRailEntry() {
  const toggleProjectAssetsPanel = useFrameosStore(
    (s) => s.toggleProjectAssetsPanel,
  );
  return (
    <button
      type="button"
      aria-label="查看项目资产"
      title="查看项目资产"
      data-frameos-assets-button
      onClick={toggleProjectAssetsPanel}
      style={{
        width: 32,
        height: 32,
        borderRadius: 8,
        border: "none",
        background: "transparent",
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
        e.currentTarget.style.background = "transparent";
        e.currentTarget.style.color = "#C2C2C2";
      }}
    >
      <svg width={18} height={18} viewBox="0 0 24 24" fill="none">
        <circle cx="9" cy="8" r="3.2" stroke="currentColor" strokeWidth="1.6" />
        <path
          d="M3.5 19c.8-3 3-4.5 5.5-4.5S13.7 16 14.5 19"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
        />
        <circle cx="17" cy="9.5" r="2.4" stroke="currentColor" strokeWidth="1.6" />
        <path
          d="M15.5 18.6c.7-2.2 2.2-3.3 4-3.3 1 0 1.9.3 2.6 1"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
        />
      </svg>
    </button>
  );
}
