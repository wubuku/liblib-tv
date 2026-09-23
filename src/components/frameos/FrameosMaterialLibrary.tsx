"use client";

import { useEffect, useMemo, useState } from "react";
import { CloseIcon, SearchIcon } from "./icons";

/**
 * FrameOS 素材库对话框 (2026-09-24 源站实测对齐, Batch 212):
 * - 标题 选择素材, 副标题 从素材库选择图片或视频作为生成参考
 * - 左侧目录树: 测试作品 > 测试项目 > 工具箱素材/画布素材/上传素材 + 其他目录
 * - 筛选: 全部/图片/视频/音频/3D + 收藏 + 创建者 + 创建时间
 * - 操作: 批量操作 / + 本地上传; 空目录显示 暂无数据
 * - 底部: 已选 N 个 / 取消 / 添加参考素材
 * - 目录/素材为泛化 mock (不复制用户真实数据); 真实上传流程未验证
 */

interface MockAsset {
  id: string;
  name: string;
  kind: "image" | "video" | "audio";
}

const FOLDERS = [
  { id: "toolbox", name: "工具箱素材", depth: 0 },
  { id: "project", name: "测试项目", depth: 0 },
  { id: "canvas", name: "画布素材", depth: 1 },
  { id: "upload", name: "上传素材", depth: 1 },
];

const FILTERS = ["全部", "图片", "视频", "音频", "3D"] as const;

const MOCK_ASSETS: MockAsset[] = [
  { id: "a1", name: "咖啡馆外景参考图", kind: "image" },
  { id: "a2", name: "主角定妆照", kind: "image" },
  { id: "a3", name: "对峙分镜片段", kind: "video" },
  { id: "a4", name: "环境音效", kind: "audio" },
];

export function FrameosMaterialLibrary() {
  const [open, setOpen] = useState(false);
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>("全部");
  const [selected, setSelected] = useState<string[]>([]);
  const [query, setQuery] = useState("");

  useEffect(() => {
    const openPanel = () => setOpen(true);
    window.addEventListener("frameos:open-material-library", openPanel);
    return () =>
      window.removeEventListener("frameos:open-material-library", openPanel);
  }, []);

  const list = useMemo(() => {
    const byFilter =
      filter === "全部"
        ? MOCK_ASSETS
        : MOCK_ASSETS.filter((a) =>
            filter === "图片"
              ? a.kind === "image"
              : filter === "视频"
              ? a.kind === "video"
              : filter === "音频"
              ? a.kind === "audio"
              : false,
          );
    const q = query.trim();
    if (!q) return byFilter;
    return byFilter.filter((a) => a.name.includes(q));
  }, [filter, query]);

  useEffect(() => {
    const openPanel = () => setOpen(true);
    window.addEventListener("frameos:open-material-library", openPanel);
    return () =>
      window.removeEventListener("frameos:open-material-library", openPanel);
  }, []);

  const toggleSelect = (id: string) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  };

  return (
    <>
      {open && (
        <>
          <div
            style={{ position: "fixed", inset: 0, zIndex: 4100 }}
            onClick={() => setOpen(false)}
          />
          <div
            role="dialog"
            aria-label="素材库"
            style={{
              position: "fixed",
              top: 60,
              left: "50%",
              transform: "translateX(-50%)",
              width: 1000,
              maxWidth: "calc(100vw - 40px)",
              height: 600,
              background: "#141414",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: 12,
              boxShadow: "0 24px 64px rgba(0,0,0,0.6)",
              zIndex: 4101,
              display: "flex",
              flexDirection: "column",
              overflow: "hidden",
            }}
          >
            {/* 头部 */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "14px 20px 10px",
              }}
            >
              <div>
                <div style={{ color: "#FFFFFF", fontSize: 16, fontWeight: 600 }}>
                  选择素材
                </div>
                <div style={{ color: "#7A7A7A", fontSize: 12, marginTop: 2 }}>
                  从素材库选择图片或视频作为生成参考
                </div>
              </div>
              <button
                type="button"
                aria-label="关闭素材库"
                onClick={() => setOpen(false)}
                style={{
                  width: 26,
                  height: 26,
                  borderRadius: 6,
                  border: "none",
                  background: "transparent",
                  color: "#A3A3A3",
                  fontSize: 15,
                  cursor: "pointer",
                }}
              >
                <CloseIcon size={14} />
              </button>
            </div>

            <div style={{ display: "flex", flex: 1, minHeight: 0 }}>
              {/* 左侧目录树 */}
              <div
                style={{
                  width: 240,
                  borderRight: "1px solid rgba(255,255,255,0.08)",
                  padding: "8px 10px",
                  overflowY: "auto",
                }}
              >
                <div
                  style={{
                    color: "#A3A3A3",
                    fontSize: 12,
                    padding: "4px 8px",
                  }}
                >
                  分类
                </div>
                {FOLDERS.map((f) => (
                  <div
                    key={f.id}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 6,
                      padding: "6px 8px",
                      borderRadius: 6,
                      color: "#C2C2C2",
                      fontSize: 13,
                      marginLeft: f.depth * 14,
                      cursor: "pointer",
                    }}
                  >
                    <span aria-hidden>▸</span>
                    <span>{f.name}</span>
                  </div>
                ))}
              </div>

              {/* 右侧主区 */}
              <div
                style={{
                  flex: 1,
                  display: "flex",
                  flexDirection: "column",
                  padding: "10px 14px",
                  minHeight: 0,
                }}
              >
                <div
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 8,
                    height: 32,
                    padding: "0 10px",
                    background: "#0D0D0D",
                    border: "1px solid rgba(255,255,255,0.08)",
                    borderRadius: 8,
                    maxWidth: 280,
                  }}
                >
                  <SearchIcon size={14} color="#7A7A7A" />
                  <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="搜索当前文件夹"
                    style={{
                      flex: 1,
                      background: "transparent",
                      border: "none",
                      outline: "none",
                      color: "#FFFFFF",
                      fontSize: 12,
                    }}
                  />
                </div>

                <div style={{ display: "flex", gap: 6, margin: "10px 0" }}>
                  {FILTERS.map((f) => (
                    <button
                      key={f}
                      type="button"
                      onClick={() => setFilter(f)}
                      style={{
                        height: 28,
                        padding: "0 12px",
                        borderRadius: 6,
                        border: "none",
                        background:
                          filter === f
                            ? "rgba(59,130,246,0.25)"
                            : "rgba(255,255,255,0.06)",
                        color: filter === f ? "#FFFFFF" : "#A3A3A3",
                        fontSize: 12,
                        cursor: "pointer",
                      }}
                    >
                      {f}
                    </button>
                  ))}
                </div>

                <div
                  style={{
                    display: "flex",
                    gap: 8,
                    marginBottom: 8,
                  }}
                >
                  <button
                    type="button"
                    style={{
                      height: 30,
                      padding: "0 12px",
                      borderRadius: 6,
                      border: "1px solid rgba(255,255,255,0.14)",
                      background: "transparent",
                      color: "#E0E0E0",
                      fontSize: 12,
                      cursor: "pointer",
                    }}
                  >
                    批量操作
                  </button>
                  <button
                    type="button"
                    style={{
                      height: 30,
                      padding: "0 12px",
                      borderRadius: 6,
                      border: "none",
                      background: "rgba(59,130,246,0.25)",
                      color: "#60A5FA",
                      fontSize: 12,
                      cursor: "pointer",
                    }}
                  >
                    + 本地上传
                  </button>
                </div>

                <div
                  style={{
                    flex: 1,
                    display: "flex",
                    flexWrap: "wrap",
                    alignContent: list.length === 0 ? "center" : "flex-start",
                    justifyContent: list.length === 0 ? "center" : "flex-start",
                    gap: 10,
                    overflowY: "auto",
                  }}
                >
                  {list.length === 0 ? (
                    <div
                      style={{
                        width: "100%",
                        textAlign: "center",
                        color: "#7A7A7A",
                        fontSize: 13,
                      }}
                    >
                      暂无数据
                    </div>
                  ) : (
                    list.map((a) => {
                      const isSel = selected.includes(a.id);
                      return (
                        <button
                          key={a.id}
                          type="button"
                          data-frameos-material-card={a.name}
                          onClick={() => toggleSelect(a.id)}
                          style={{
                            width: 120,
                            padding: 8,
                            borderRadius: 8,
                            border: isSel
                              ? "1px solid rgba(96,165,250,0.8)"
                              : "1px solid rgba(255,255,255,0.1)",
                            background: isSel
                              ? "rgba(59,130,246,0.12)"
                              : "rgba(255,255,255,0.04)",
                            color: "#E0E0E0",
                            fontSize: 12,
                            cursor: "pointer",
                            textAlign: "center",
                          }}
                        >
                          <div style={{ fontSize: 24, marginBottom: 4 }}>
                            {a.kind === "image" ? "🖼" : a.kind === "video" ? "🎬" : "🎵"}
                          </div>
                          <div>{a.name}</div>
                          <div style={{ color: "#7A7A7A", fontSize: 10, marginTop: 2 }}>
                            {a.kind === "image" ? "图片" : a.kind === "video" ? "视频" : "音频"}
                          </div>
                        </button>
                      );
                    })
                  )}
                </div>
              </div>
            </div>

            {/* 底部操作条 */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "10px 20px",
                borderTop: "1px solid rgba(255,255,255,0.08)",
              }}
            >
              <span style={{ color: "#A3A3A3", fontSize: 12 }}>
                已选 {selected.length} 个
              </span>
              <div style={{ display: "flex", gap: 10 }}>
                <button
                  type="button"
                  aria-label="取消选择素材"
                  onClick={() => setOpen(false)}
                  style={{
                    height: 32,
                    padding: "0 16px",
                    borderRadius: 8,
                    border: "1px solid rgba(255,255,255,0.14)",
                    background: "transparent",
                    color: "#E0E0E0",
                    fontSize: 13,
                    cursor: "pointer",
                  }}
                >
                  取消
                </button>
                <button
                  type="button"
                  aria-label="添加参考素材"
                  style={{
                    height: 32,
                    padding: "0 16px",
                    borderRadius: 8,
                    border: "none",
                    background: "#3B82F6",
                    color: "#FFFFFF",
                    fontSize: 13,
                    cursor: "pointer",
                  }}
                >
                  添加参考素材
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
}
