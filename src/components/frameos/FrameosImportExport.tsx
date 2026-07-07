"use client";

import { useFrameosStore } from "@/store/frameosStore";
import { useRef } from "react";

/**
 * FrameOS 画布导入/导出
 * - "导出" → 下载当前 nodes/edges 为 frameos-canvas-YYYYMMDD-HHMMSS.json
 * - "导入" → 上传 JSON 替换当前画布
 */
export function FrameosImportExport() {
  const setNodes = useFrameosStore((s) => s.setNodes);
  const setEdges = useFrameosStore((s) => s.setEdges);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleExport = () => {
    const state = useFrameosStore.getState();
    const payload = {
      version: 1,
      exportedAt: new Date().toISOString(),
      nodes: state.nodes,
      edges: state.edges,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    const ts = new Date()
      .toISOString()
      .replace(/[-:]/g, "")
      .replace(/\..+/, "")
      .replace("T", "-");
    a.href = url;
    a.download = `frameos-canvas-${ts}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const text = await file.text();
      const data = JSON.parse(text);
      if (!Array.isArray(data.nodes) || !Array.isArray(data.edges)) {
        throw new Error("Invalid format");
      }
      setNodes(data.nodes);
      setEdges(data.edges);
    } catch (err) {
      alert("导入失败：文件格式无效");
      console.error(err);
    } finally {
      // 重置 input 允许同一文件再选
      e.target.value = "";
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        top: 70,
        right: 240,
        zIndex: 2700,
        display: "flex",
        gap: 6,
      }}
    >
      <button
        type="button"
        onClick={handleExport}
        title="导出当前画布为 JSON"
        style={{
          height: 32,
          padding: "0 10px",
          borderRadius: 8,
          background: "rgba(20,20,20,0.85)",
          backdropFilter: "blur(8px)",
          border: "1px solid rgba(255,255,255,0.08)",
          color: "#E0E0E0",
          fontSize: 12,
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          gap: 6,
          transition: "background 0.15s, border-color 0.15s",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = "rgba(40,40,40,0.95)";
          e.currentTarget.style.borderColor = "rgba(96,165,250,0.4)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = "rgba(20,20,20,0.85)";
          e.currentTarget.style.borderColor = "rgba(255,255,255,0.08)";
        }}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5-5 5 5M12 5v12" />
        </svg>
        <span>导出</span>
      </button>
      <button
        type="button"
        onClick={() => fileInputRef.current?.click()}
        title="从 JSON 文件加载画布"
        style={{
          height: 32,
          padding: "0 10px",
          borderRadius: 8,
          background: "rgba(20,20,20,0.85)",
          backdropFilter: "blur(8px)",
          border: "1px solid rgba(255,255,255,0.08)",
          color: "#E0E0E0",
          fontSize: 12,
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          gap: 6,
          transition: "background 0.15s, border-color 0.15s",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = "rgba(40,40,40,0.95)";
          e.currentTarget.style.borderColor = "rgba(96,165,250,0.4)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = "rgba(20,20,20,0.85)";
          e.currentTarget.style.borderColor = "rgba(255,255,255,0.08)";
        }}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12" />
        </svg>
        <span>导入</span>
      </button>
      <input
        ref={fileInputRef}
        type="file"
        accept="application/json,.json"
        onChange={handleImport}
        style={{ display: "none" }}
      />
    </div>
  );
}
