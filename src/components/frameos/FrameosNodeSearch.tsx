"use client";

import { useMemo, useState } from "react";
import { useReactFlow } from "@xyflow/react";
import { useFrameosStore } from "@/store/frameosStore";
import { CloseIcon, TextNodeIcon, ImageNodeIcon, FilmNodeIcon } from "./icons";

/**
 * FrameOS 节点搜索面板 (2026-09-23 源站实测, SOURCE_OBSERVATIONS §13.7):
 * - 底部工具条「搜索节点」按钮或 ⌘F 打开, 输入框占位 "搜索节点名称"
 * - 按节点名称/内容实时过滤, 无匹配时显示 "无匹配节点"
 * - 点击结果: 选中该节点并把视野缩放聚焦到它 (源站实测 100%→273%)
 * - × / Esc 关闭
 */
const TYPE_ICONS: Record<string, React.ReactNode> = {
  text: <TextNodeIcon size={12} />,
  image: <ImageNodeIcon size={12} />,
  video: <FilmNodeIcon size={12} />,
};

export function FrameosNodeSearch() {
  const isNodeSearchOpen = useFrameosStore((s) => s.isNodeSearchOpen);
  const closeNodeSearch = useFrameosStore((s) => s.closeNodeSearch);
  const nodes = useFrameosStore((s) => s.nodes);
  const selectNode = useFrameosStore((s) => s.selectNode);
  const { setCenter } = useReactFlow();
  const [query, setQuery] = useState("");

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    return nodes.filter((n) => {
      const title = String(n.data.title ?? "");
      const content = String(n.data.content ?? "");
      return (
        title.toLowerCase().includes(q) || content.toLowerCase().includes(q)
      );
    });
  }, [nodes, query]);

  if (!isNodeSearchOpen) return null;

  const focusNode = (id: string) => {
    selectNode(id);
    const el = document.querySelector(
      `.react-flow__node[data-id="${CSS.escape(id)}"]`,
    );
    if (el) {
      const r = el.getBoundingClientRect();
      setCenter(
        r.left + r.width / 2,
        r.top + r.height / 2,
        { zoom: 2.73, duration: 600 },
      );
    }
  };

  return (
    <div
      data-frameos-node-search
      style={{
        position: "fixed",
        left: 64,
        bottom: 84,
        width: 260,
        background: "#161616",
        border: "1px solid rgba(255,255,255,0.08)",
        borderRadius: 10,
        boxShadow: "0 8px 24px rgba(0,0,0,0.5)",
        zIndex: 2700,
        padding: 8,
      }}
    >
      <div style={{ position: "relative" }}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="搜索节点名称"
          data-frameos-node-search-input
          style={{
            width: "100%",
            height: 32,
            background: "#0D0D0D",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: 8,
            color: "#FFFFFF",
            fontSize: 13,
            padding: "0 28px 0 10px",
            outline: "none",
          }}
        />
        <button
          type="button"
          aria-label="关闭搜索"
          title="关闭搜索"
          onClick={closeNodeSearch}
          style={{
            position: "absolute",
            right: 6,
            top: 8,
            width: 18,
            height: 18,
            border: "none",
            background: "transparent",
            color: "#7A7A7A",
            cursor: "pointer",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            padding: 0,
          }}
        >
          <CloseIcon size={12} />
        </button>
      </div>

      <div style={{ marginTop: 6, maxHeight: 220, overflow: "auto" }}>
        {query.trim() === "" ? null : results.length === 0 ? (
          <div
            data-frameos-node-search-empty
            style={{
              color: "#7A7A7A",
              fontSize: 13,
              textAlign: "center",
              padding: "12px 0",
            }}
          >
            无匹配节点
          </div>
        ) : (
          results.map((n) => (
            <button
              key={n.id}
              type="button"
              data-frameos-node-search-result={n.id}
              onClick={() => focusNode(n.id)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                width: "100%",
                padding: "8px 10px",
                borderRadius: 8,
                border: "none",
                background: "transparent",
                color: "#E0E0E0",
                fontSize: 13,
                cursor: "pointer",
                textAlign: "left",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "rgba(255,255,255,0.05)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "transparent";
              }}
            >
              <span style={{ color: "#A3A3A3", display: "inline-flex" }}>
                {TYPE_ICONS[n.type] ?? <TextNodeIcon size={12} />}
              </span>
              <span
                style={{
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {String(n.data.title ?? n.id)}
              </span>
            </button>
          ))
        )}
      </div>
    </div>
  );
}
