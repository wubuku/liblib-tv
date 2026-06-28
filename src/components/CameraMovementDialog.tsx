"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

interface CameraMovementDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onApply?: (config: CameraMovementConfig) => void;
}

interface CameraMovementConfig {
  movementType: string;
  speed: string;
  duration: number;
  amplitude: number;
}

const movementTypes = [
  { id: "static", label: "静止", desc: "固定机位" },
  { id: "pan", label: "横摇", desc: "水平方向旋转" },
  { id: "tilt", label: "俯仰", desc: "垂直方向旋转" },
  { id: "dolly", label: "推拉", desc: "前后移动" },
  { id: "truck", label: "横移", desc: "左右平行移动" },
  { id: "pedestal", label: "升降", desc: "垂直方向移动" },
  { id: "roll", label: "旋转", desc: "围绕光轴旋转" },
  { id: "zoom", label: "变焦", desc: "改变焦距" },
  { id: "orbit", label: "环绕", desc: "围绕目标旋转" },
  { id: "crane", label: "摇臂", desc: "弧线运动" },
];

const speeds = ["极慢", "慢速", "标准", "快速", "极快"];

export function CameraMovementDialog({
  isOpen,
  onClose,
  onApply,
}: CameraMovementDialogProps) {
  const [config, setConfig] = useState<CameraMovementConfig>({
    movementType: "dolly",
    speed: "标准",
    duration: 3,
    amplitude: 50,
  });

  if (!isOpen) return null;

  const handleApply = () => {
    onApply?.(config);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Dialog */}
      <div className="relative z-10 w-[560px] rounded-xl bg-[#1f1f1f] shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
          <h2 className="text-lg font-medium text-white">运镜</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-white/60 transition-colors hover:bg-white/10 hover:text-white"
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="space-y-6 p-6">
          {/* Movement Type Selection */}
          <div className="space-y-3">
            <div className="text-sm text-white/60">运镜类型</div>
            <div className="grid grid-cols-5 gap-2">
              {movementTypes.map((movement) => (
                <button
                  key={movement.id}
                  onClick={() =>
                    setConfig({ ...config, movementType: movement.id })
                  }
                  className={cn(
                    "flex flex-col items-center gap-1 rounded-lg p-3 text-sm transition-all",
                    config.movementType === movement.id
                      ? "bg-[#09caf5] text-[#171717]"
                      : "bg-white/10 text-white/80 hover:bg-white/20"
                  )}
                >
                  <CameraIcon type={movement.id} />
                  <span className="font-medium">{movement.label}</span>
                </button>
              ))}
            </div>
            <p className="text-xs text-white/50">
              {
                movementTypes.find((m) => m.id === config.movementType)?.desc
              }
            </p>
          </div>

          {/* Speed Selection */}
          <div className="space-y-3">
            <div className="text-sm text-white/60">速度</div>
            <div className="flex flex-wrap gap-2">
              {speeds.map((speed) => (
                <button
                  key={speed}
                  onClick={() => setConfig({ ...config, speed })}
                  className={cn(
                    "rounded-lg px-4 py-2 text-sm transition-all",
                    config.speed === speed
                      ? "bg-[#09caf5] text-[#171717]"
                      : "bg-white/10 text-white/80 hover:bg-white/20"
                  )}
                >
                  {speed}
                </button>
              ))}
            </div>
          </div>

          {/* Duration */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="text-sm text-white/60">时长</div>
              <div className="text-white text-sm">{config.duration} 秒</div>
            </div>
            <input
              type="range"
              min="1"
              max="10"
              step="0.5"
              value={config.duration}
              onChange={(e) =>
                setConfig({
                  ...config,
                  duration: parseFloat(e.target.value),
                })
              }
              className="w-full h-1 bg-white/10 rounded-full appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:bg-[#09caf5] [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:cursor-pointer"
            />
            <div className="flex justify-between text-xs text-white/40">
              <span>1s</span>
              <span>10s</span>
            </div>
          </div>

          {/* Amplitude */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="text-sm text-white/60">幅度</div>
              <div className="text-white text-sm">{config.amplitude}%</div>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              step="5"
              value={config.amplitude}
              onChange={(e) =>
                setConfig({
                  ...config,
                  amplitude: parseInt(e.target.value),
                })
              }
              className="w-full h-1 bg-white/10 rounded-full appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:bg-[#09caf5] [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:cursor-pointer"
            />
            <div className="flex justify-between text-xs text-white/40">
              <span>0%</span>
              <span>100%</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex gap-3 border-t border-white/10 px-6 py-4">
          <button
            onClick={onClose}
            className="flex-1 rounded-lg bg-white/10 py-3 text-center font-medium text-white transition-colors hover:bg-white/20"
          >
            取消
          </button>
          <button
            onClick={handleApply}
            className="flex-1 rounded-lg bg-[#09caf5] py-3 text-center font-medium text-[#171717] transition-colors hover:bg-[#5ddcff]"
          >
            使用
          </button>
        </div>
      </div>
    </div>
  );
}

// Simple SVG icons representing each camera movement type
function CameraIcon({ type }: { type: string }) {
  const stroke = "currentColor";
  const sw = 1.5;
  switch (type) {
    case "static":
      return (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <rect x="4" y="6" width="12" height="8" rx="1" stroke={stroke} strokeWidth={sw} />
          <circle cx="10" cy="10" r="2" stroke={stroke} strokeWidth={sw} />
        </svg>
      );
    case "pan":
      return (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <rect x="4" y="6" width="12" height="8" rx="1" stroke={stroke} strokeWidth={sw} />
          <path d="M14 10H18" stroke={stroke} strokeWidth={sw} strokeLinecap="round" />
          <path d="M16 8L18 10L16 12" stroke={stroke} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "tilt":
      return (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <rect x="4" y="6" width="12" height="8" rx="1" stroke={stroke} strokeWidth={sw} />
          <path d="M10 14V18" stroke={stroke} strokeWidth={sw} strokeLinecap="round" />
          <path d="M8 16L10 18L12 16" stroke={stroke} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "dolly":
      return (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <rect x="4" y="6" width="12" height="8" rx="1" stroke={stroke} strokeWidth={sw} />
          <path d="M2 10H4M16 10H18" stroke={stroke} strokeWidth={sw} strokeLinecap="round" />
          <path d="M2 8L4 10L2 12" stroke={stroke} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "truck":
      return (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <rect x="4" y="6" width="12" height="8" rx="1" stroke={stroke} strokeWidth={sw} />
          <path d="M10 14V18M10 2V6" stroke={stroke} strokeWidth={sw} strokeLinecap="round" />
        </svg>
      );
    case "pedestal":
      return (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <rect x="4" y="6" width="12" height="8" rx="1" stroke={stroke} strokeWidth={sw} />
          <path d="M10 16V18M8 18H12" stroke={stroke} strokeWidth={sw} strokeLinecap="round" />
        </svg>
      );
    case "roll":
      return (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <rect x="4" y="6" width="12" height="8" rx="1" stroke={stroke} strokeWidth={sw} />
          <path d="M18 10C16 14 12 14 10 10" stroke={stroke} strokeWidth={sw} strokeLinecap="round" />
        </svg>
      );
    case "zoom":
      return (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <circle cx="10" cy="10" r="6" stroke={stroke} strokeWidth={sw} />
          <circle cx="10" cy="10" r="2" stroke={stroke} strokeWidth={sw} />
          <path d="M14 14L17 17M10 8V12M8 10H12" stroke={stroke} strokeWidth={sw} strokeLinecap="round" />
        </svg>
      );
    case "orbit":
      return (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <circle cx="10" cy="10" r="7" stroke={stroke} strokeWidth={sw} strokeDasharray="3 2" />
          <circle cx="10" cy="10" r="2" fill={stroke} />
          <circle cx="17" cy="10" r="1.5" fill={stroke} />
        </svg>
      );
    case "crane":
      return (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path d="M2 18L10 6L18 18" stroke={stroke} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" />
          <circle cx="10" cy="6" r="1.5" fill={stroke} />
        </svg>
      );
    default:
      return null;
  }
}