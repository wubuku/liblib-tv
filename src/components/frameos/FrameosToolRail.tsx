"use client";

import {
  AddLineIcon,
  FolderImageIcon,
  UploadCloudIcon,
  QuestionIcon,
} from "./icons";
import { useFrameosStore } from "@/store/frameosStore";
import { useViewport } from "@xyflow/react";

const NODE_TYPES = [
  { type: "text" as const, title: "文本节点", desc: "纯文本描述，可连接到任意节点", icon: "T" },
  { type: "image" as const, title: "图片节点", desc: "输入图片，可用作参考或输出", icon: "🖼" },
  { type: "video" as const, title: "视频节点", desc: "视频素材或生成的视频", icon: "🎬" },
  { type: "character" as const, title: "角色节点", desc: "人物角色，含形象 + 描述", icon: "👤" },
  { type: "scene" as const, title: "场景节点", desc: "剧本/分镜的场景描述", icon: "🎬" },
  { type: "audio" as const, title: "音频节点", desc: "背景音乐 / 配音 / 音效", icon: "🎵" },
  { type: "style" as const, title: "风格节点", desc: "画面风格参数 (色调/光影/笔触)", icon: "🎨" },
  { type: "batch" as const, title: "批量节点", desc: "批量生成多个相似内容", icon: "📦" },
];

interface RailButtonProps {
  label: string;
  icon: React.ReactNode;
  primary?: boolean;
  onClick?: () => void;
  active?: boolean;
}

function RailButton({ label, icon, primary, onClick, active }: RailButtonProps) {
  return (
    <button
      type="button"
      aria-label={label}
      className={`rail-btn${primary ? " rail-btn--primary" : ""}${active ? " is-active" : ""}`}
      onClick={onClick}
      style={{
        // frameos.cn: primary 添加节点 36px 圆 + 蓝色渐变; 其他 32px 方角 (8px) + 透明
        width: primary ? 36 : 32,
        height: primary ? 36 : 32,
        borderRadius: primary ? 9999 : 8,
        border: "none",
        background: active
          ? "rgba(59,130,246,0.16)"
          : primary
          ? "linear-gradient(135deg, rgb(37,99,235), rgb(29,78,216))"
          : "transparent",
        boxShadow: active
          ? "0 0 0 3px rgba(59,130,246,0.3)"
          : primary
          ? "rgba(59,130,246,0.35) 0 2px 8px 0"
          : "none",
        color: active ? "#60A5FA" : "#C2C2C2",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
        transition: "background 0.15s, transform 0.15s, box-shadow 0.15s, color 0.15s",
      }}
      onMouseEnter={(e) => {
        if (!active) {
          if (!primary) {
            e.currentTarget.style.background = "rgba(255,255,255,0.05)";
            e.currentTarget.style.color = "#FFFFFF";
          }
        }
      }}
      onMouseLeave={(e) => {
        if (!active && !primary) {
          e.currentTarget.style.background = "transparent";
          e.currentTarget.style.color = "#C2C2C2";
        }
      }}
    >
      {icon}
    </button>
  );
}

function Divider() {
  return (
    <span
      className="rail-divider"
      style={{
        display: "block",
        width: 24,
        height: 1,
        background: "rgba(255,255,255,0.08)",
      }}
    />
  );
}

/**
 * FrameOS 左侧浮动工具栏 (absolute, left:12, top 居中, z=2700)
 * 添加节点 / 素材库 / 本地上传 / 帮助
 */
export function FrameosToolRail() {
  const isAddNodeMenuOpen = useFrameosStore((s) => s.isAddNodeMenuOpen);
  const toggleAddNodeMenu = useFrameosStore((s) => s.toggleAddNodeMenu);
  const closeAddNodeMenu = useFrameosStore((s) => s.closeAddNodeMenu);
  const addNode = useFrameosStore((s) => s.addNode);
  const toggleHelp = useFrameosStore((s) => s.toggleHelp);
  const { x: panX, y: panY, zoom } = useViewport();

  const addNodeOpts = {
    panX,
    panY,
    zoom,
    viewportWidth: typeof window !== "undefined" ? window.innerWidth : 1440,
    viewportHeight: typeof window !== "undefined" ? window.innerHeight : 900,
  };

  return (
    <div
      className="canvas-tool-rail-root"
      style={{
        position: "absolute",
        left: 12,
        top: "50%",
        transform: "translateY(-50%)",
        zIndex: 2700,
        pointerEvents: "none",
      }}
    >
      <div
        className="tool-rail"
        style={{
          // frameos.cn 工具栏无独立容器背景, 按钮各自独立浮动
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 8,
          padding: 0,
          background: "transparent",
          backdropFilter: "none",
          borderRadius: 0,
          border: "none",
          pointerEvents: "auto",
        }}
      >
        <div style={{ position: "relative" }}>
          <RailButton
            label="添加节点"
            icon={<AddLineIcon size={18} />}
            primary
            active={isAddNodeMenuOpen}
            onClick={toggleAddNodeMenu}
          />

          {/* 添加节点菜单 */}
          {isAddNodeMenuOpen && (
            <>
              <div
                style={{ position: "fixed", inset: 0, zIndex: 2699 }}
                onClick={closeAddNodeMenu}
              />
              <div
                style={{
                  position: "absolute",
                  left: "calc(100% + 8px)",
                  top: 0,
                  background: "#1C1C1C",
                  border: "1px solid rgba(255,255,255,0.12)",
                  borderRadius: 12,
                  padding: 6,
                  boxShadow: "0 8px 24px rgba(0,0,0,0.5)",
                  minWidth: 220,
                  zIndex: 2700,
                }}
              >
                <div
                  style={{
                    color: "#A3A3A3",
                    fontSize: 12,
                    padding: "8px 10px",
                    borderBottom: "1px solid rgba(255,255,255,0.06)",
                    marginBottom: 4,
                  }}
                >
                  选择节点类型
                </div>
                {NODE_TYPES.map((nt) => (
                  <NodeTypeItem
                    key={nt.type}
                    icon={<span style={{ fontSize: 16 }}>{nt.icon}</span>}
                    title={nt.title}
                    desc={nt.desc}
                    onClick={() => addNode(nt.type, addNodeOpts)}
                  />
                ))}
              </div>
            </>
          )}
        </div>

        <Divider />
        <RailButton
          label="从素材库选择"
          icon={<FolderImageIcon size={18} />}
          onClick={() => {
            window.dispatchEvent(new CustomEvent("frameos:open-material-library"));
          }}
        />
        <RailButton
          label="本地上传"
          icon={<UploadCloudIcon size={18} />}
          onClick={() => {
            const input = document.createElement("input");
            input.type = "file";
            input.accept = "image/*,video/*";
            input.multiple = true;
            input.onchange = () => {
              for (let i = 0; i < input.files!.length; i++) {
                const file = input.files![i];
                const type = file.type.startsWith("image/")
                  ? "image"
                  : file.type.startsWith("video/")
                  ? "video"
                  : null;
                if (type) {
                  useFrameosStore.getState().addNode(type);
                }
              }
            };
            input.click();
          }}
        />
        <Divider />
        <RailButton
          label="帮助 (?)"
          icon={<QuestionIcon size={18} />}
          onClick={toggleHelp}
        />
      </div>
    </div>
  );
}

function NodeTypeItem({
  icon,
  title,
  desc,
  onClick,
}: {
  icon: React.ReactNode;
  title: string;
  desc: string;
  onClick?: () => void;
}) {
  return (
    <div
      onClick={onClick}
      style={{
        display: "flex",
        alignItems: "flex-start",
        gap: 10,
        padding: "8px 10px",
        borderRadius: 8,
        cursor: "pointer",
        transition: "background 0.15s",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = "rgba(255,255,255,0.05)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = "transparent";
      }}
    >
      <div
        style={{
          width: 32,
          height: 32,
          borderRadius: 8,
          background: "rgba(255,255,255,0.05)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#C2C2C2",
          flexShrink: 0,
        }}
      >
        {icon}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ color: "#FFFFFF", fontSize: 13, fontWeight: 500 }}>{title}</div>
        <div style={{ color: "#7A7A7A", fontSize: 12, marginTop: 2 }}>{desc}</div>
      </div>
    </div>
  );
}
