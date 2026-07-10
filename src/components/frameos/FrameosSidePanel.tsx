"use client";

import { useEffect, useState } from "react";
import { ArrowLeftIcon } from "./icons";

/**
 * FrameOS 产品级左侧导航 (点击 AppHeader 的"展开菜单"按钮 toggle)
 * 与原站 frameos.cn 一致: 全屏左侧栏, 列出"我的作品/任务/报表/..."
 * 等模块导航项. 复刻真实行为而非臆造内容.
 */

interface NavItem {
  label: string;
  badge?: string; // 例如 "HOT" 角标
}

const NAV_ITEMS: NavItem[] = [
  { label: "我的作品" },
  { label: "我的任务" },
  { label: "我的报表" },
  { label: "编剧工作台" },
  { label: "工具箱" },
  { label: "Seedance 2.0", badge: "HOT" },
  { label: "无限画布" },
  { label: "资产库" },
  { label: "素材库" },
  { label: "团队管理" },
  { label: "服务记录" },
  { label: "问题反馈" },
];

export function FrameosSidePanel() {
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState("我的作品");

  useEffect(() => {
    const toggle = () => setOpen((o) => !o);
    window.addEventListener("frameos:toggle-side", toggle);
    return () => window.removeEventListener("frameos:toggle-side", toggle);
  }, []);

  if (!open) return null;

  return (
    <>
      {/* 仅关闭面板用的遮罩 (不拦截动画外的视觉) */}
      <div
        style={{
          position: "fixed",
          inset: 0,
          zIndex: 2680,
          pointerEvents: "none",
        }}
      />
      <aside
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          bottom: 0,
          width: 220,
          background: "rgba(16,16,16,0.92)",
          backdropFilter: "blur(16px)",
          borderRight: "1px solid rgba(255,255,255,0.06)",
          zIndex: 2690,
          display: "flex",
          flexDirection: "column",
          animation: "frameos-slide-in-left 0.2s ease-out",
          paddingTop: 12,
        }}
        aria-label="产品导航"
      >
        {/* 顶部收起按钮 */}
        <div
          style={{
            padding: "4px 12px 12px",
            display: "flex",
            justifyContent: "flex-end",
          }}
        >
          <button
            type="button"
            onClick={() => setOpen(false)}
            aria-label="收起菜单"
            title="收起菜单"
            style={{
              width: 28,
              height: 28,
              borderRadius: 6,
              background: "transparent",
              border: "none",
              color: "#C2C2C2",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
              transition: "background 0.15s",
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
            <ArrowLeftIcon size={14} />
          </button>
        </div>

        {/* 主体导航 */}
        <nav
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "4px 8px",
            display: "flex",
            flexDirection: "column",
            gap: 2,
          }}
          aria-label="主导航"
        >
          {NAV_ITEMS.map((item) => {
            const isActive = item.label === active;
            return (
              <button
                key={item.label}
                type="button"
                onClick={() => setActive(item.label)}
                aria-current={isActive ? "page" : undefined}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: 8,
                  padding: "8px 12px",
                  borderRadius: 8,
                  background: isActive ? "rgba(59,130,246,0.16)" : "transparent",
                  color: isActive ? "#60A5FA" : "#C2C2C2",
                  border: "none",
                  fontSize: 13,
                  cursor: "pointer",
                  textAlign: "left",
                  width: "100%",
                  transition: "background 0.15s, color 0.15s",
                }}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.background = "rgba(255,255,255,0.04)";
                    e.currentTarget.style.color = "#FFFFFF";
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.background = "transparent";
                    e.currentTarget.style.color = "#C2C2C2";
                  }
                }}
              >
                <span>{item.label}</span>
                {item.badge && (
                  <span
                    style={{
                      padding: "2px 6px",
                      borderRadius: 4,
                      background: "rgba(245,158,11,0.18)",
                      color: "#F59E0B",
                      fontSize: 10,
                      fontWeight: 600,
                      letterSpacing: "0.05em",
                    }}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </aside>
    </>
  );
}
