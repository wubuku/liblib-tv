"use client";

import Image from "next/image";
import Link from "next/link";
import { useFrameosStore } from "@/store/frameosStore";
import { DownloadIcon, UndoIcon, RedoIcon } from "./icons";
import { FrameosBreadcrumb } from "./FrameosBreadcrumb";

/**
 * FrameOS 顶部 AppHeader (共 100px 高, 浮动, z=2000)
 * - 60px 上条: 左 logo, 右 下载桌面端 + 金币 + 积分
 * - 40px 下条: 左面包屑 (项目 / 场景 / 画布), 右 undo/redo
 *
 * 与原站 frameos.cn 一致: logo 浮在画布最上沿, 面包屑紧贴 logo 下; undo/redo 在右上角
 */
export function FrameosAppHeader() {
  const undo = useFrameosStore((s) => s.undo);
  const redo = useFrameosStore((s) => s.redo);
  const past = useFrameosStore((s) => s.past);
  const future = useFrameosStore((s) => s.future);

  const canUndo = past.length > 0;
  const canRedo = future.length > 0;

  return (
    <header
      className="app-header is-floating"
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        height: 100,
        zIndex: 2000,
        display: "flex",
        flexDirection: "column",
        background:
          "linear-gradient(to bottom, rgba(13,13,13,0.92) 0%, rgba(13,13,13,0.6) 70%, rgba(13,13,13,0) 100%)",
        pointerEvents: "none",
      }}
    >
      {/* 上条 60px: logo + 右侧操作 */}
      <div
        style={{
          height: 60,
          padding: "0 24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          pointerEvents: "none",
        }}
      >
        <div
          className="hd-left"
          style={{
            display: "flex",
            alignItems: "center",
            pointerEvents: "auto",
          }}
        >
          <div
            className="hd-logo"
            style={{
              display: "flex",
              alignItems: "center",
              height: 32,
            }}
          >
            <Image
              src="/images/frameos/frameos-logo.svg"
              alt="帧界 FrameOS"
              width={200}
              height={32}
              style={{ height: 32, width: "auto" }}
              unoptimized
              priority
            />
          </div>
        </div>

        <div
          className="hd-right"
          style={{
            display: "flex",
            alignItems: "center",
            gap: 16,
            pointerEvents: "auto",
          }}
        >
          {/* 返回 LibTV 画布 */}
          <Link
            href="/"
            aria-label="返回 LibTV 画布"
            title="返回 LibTV 画布"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
              height: 36,
              padding: "0 12px",
              borderRadius: 8,
              background: "rgba(20,20,20,0.6)",
              border: "1px solid rgba(255,255,255,0.12)",
              color: "#E0E0E0",
              fontSize: 13,
              textDecoration: "none",
              transition: "background 0.15s, border-color 0.15s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "rgba(20,20,20,0.9)";
              e.currentTarget.style.borderColor = "rgba(96,165,250,0.4)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "rgba(20,20,20,0.6)";
              e.currentTarget.style.borderColor = "rgba(255,255,255,0.12)";
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
            <span>LibTV</span>
          </Link>

          {/* undo / redo 浮动按钮组 (原站右上) */}
          <div
            className="hd-undo-redo"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 4,
              padding: 4,
              borderRadius: 8,
              background: "rgba(20,20,20,0.6)",
              border: "1px solid rgba(255,255,255,0.12)",
            }}
          >
            <HeaderIconBtn
              label="撤销 (Ctrl+Z)"
              onClick={canUndo ? undo : undefined}
              disabled={!canUndo}
              icon={<UndoIcon size={14} />}
            />
            <HeaderIconBtn
              label="重做 (Ctrl+Y)"
              onClick={canRedo ? redo : undefined}
              disabled={!canRedo}
              icon={<RedoIcon size={14} />}
            />
          </div>

          {/* 下载桌面端 */}
          <button
            type="button"
            className="hd-download-client"
            onClick={() => window.alert("下载桌面端 (mock)")}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
              height: 36,
              padding: "0 12px",
              borderRadius: 8,
              background: "transparent",
              border: "1px solid rgba(255,255,255,0.12)",
              color: "#FFFFFF",
              fontSize: 13,
              cursor: "pointer",
              transition: "background 0.15s, border-color 0.15s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "rgba(255,255,255,0.05)";
              e.currentTarget.style.borderColor = "rgba(255,255,255,0.2)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "transparent";
              e.currentTarget.style.borderColor = "rgba(255,255,255,0.12)";
            }}
          >
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <DownloadIcon size={14} />
            </span>
            <span>下载桌面端</span>
          </button>

          {/* 金币 + 积分 */}
          <div
            className="credits-wrap"
            onClick={() => window.alert("余额详情 (mock)")}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 4,
              padding: "4px 10px",
              borderRadius: 8,
              background: "rgba(255,255,255,0.04)",
              border: "1px solid rgba(255,255,255,0.08)",
              cursor: "pointer",
            }}
          >
            <span
              className="cr-badge orange"
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                width: 22,
                height: 22,
                borderRadius: 4,
                marginRight: 2,
              }}
            >
              <Image
                src="/images/frameos/credit-logo.svg"
                alt="金币"
                width={18}
                height={18}
                unoptimized
              />
            </span>
            <span style={{ color: "#FFC35E", fontSize: 13, fontWeight: 500 }}>
              16942
            </span>
            <span
              className="cr-divider"
              style={{
                width: 1,
                height: 14,
                background: "rgba(255,255,255,0.1)",
                margin: "0 8px",
              }}
            />
            <span
              className="cr-badge blue"
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                width: 22,
                height: 22,
                borderRadius: 4,
                marginRight: 2,
              }}
            >
              <Image
                src="/images/frameos/point-logo.svg"
                alt="积分"
                width={18}
                height={18}
                unoptimized
              />
            </span>
            <span style={{ color: "#60A5FA", fontSize: 13, fontWeight: 500 }}>
              19712
            </span>
          </div>
        </div>
      </div>

      {/* 下条 40px: 面包屑 (左上) */}
      <div
        className="hd-breadcrumb-bar"
        style={{
          height: 40,
          padding: "0 24px",
          display: "flex",
          alignItems: "center",
          gap: 16,
          pointerEvents: "none",
        }}
      >
        <button
          type="button"
          aria-label="展开菜单"
          onClick={() =>
            window.dispatchEvent(new CustomEvent("frameos:toggle-side"))
          }
          style={{
            width: 28,
            height: 28,
            borderRadius: 6,
            background: "rgba(20,20,20,0.85)",
            border: "1px solid rgba(255,255,255,0.12)",
            color: "#C2C2C2",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
            transition: "background 0.15s",
            pointerEvents: "auto",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "rgba(40,40,40,0.95)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "rgba(20,20,20,0.85)";
          }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <FrameosBreadcrumb />
      </div>
    </header>
  );
}

function HeaderIconBtn({
  label,
  onClick,
  disabled,
  icon,
}: {
  label: string;
  onClick?: () => void;
  disabled?: boolean;
  icon: React.ReactNode;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      onClick={onClick}
      disabled={disabled}
      style={{
        width: 28,
        height: 28,
        borderRadius: 6,
        background: "transparent",
        border: "none",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        color: disabled ? "#5A5A5A" : "#FFFFFF",
        cursor: disabled ? "not-allowed" : "pointer",
        transition: "background 0.15s, color 0.15s",
      }}
      onMouseEnter={(e) => {
        if (!disabled) e.currentTarget.style.background = "rgba(255,255,255,0.08)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = "transparent";
      }}
    >
      {icon}
    </button>
  );
}

