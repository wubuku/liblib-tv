"use client";

import Image from "next/image";
import Link from "next/link";
import { DownloadIcon } from "./icons";

/**
 * FrameOS 顶部 AppHeader (60px 高, 浮动, z=2000)
 * - 左: Logo
 * - 右: 下载桌面端 + 金币 + 积分
 */
export function FrameosAppHeader() {
  return (
    <header
      className="app-header is-floating"
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        height: 60,
        zIndex: 2000,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 24px",
        pointerEvents: "none", // 让背景不阻挡画布；子元素单独打开
      }}
    >
      {/* 左侧 logo */}
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
          />
        </div>
      </div>

      {/* 右侧操作 */}
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
        {/* 下载桌面端 */}
        <button
          type="button"
          className="hd-download-client"
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
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 4,
            padding: "4px 10px",
            borderRadius: 8,
            background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.08)",
          }}
        >
          {/* 金币 */}
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
          {/* 积分 */}
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
    </header>
  );
}
