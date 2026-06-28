"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

interface CameraConfigDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onApply?: (config: CameraConfig) => void;
}

interface CameraConfig {
  camera: string;
  lens: string;
  focalLength: number;
  aperture: string;
}

const cameras = [
  "Sony Venice",
  "Arri Alexa 35",
  "Arri Alexa 65",
  "Red V-Raptor",
  "Panavision DXL2",
  "Arricam LT",
  "ArriFlex 435",
  "IMAX Keighley",
  "IMAX Film Camera",
];

const lenses = [
  "Zeiss Ultra Prime",
  "Cooke SF 1.8x",
  "Canon K-35",
  "Cooke S4",
  "Cooke Panchro",
  "Arri Signature Prime",
  "Helios",
  "Panavision C-series",
  "Panavision Primo",
  "Hawk Class X",
];

const focalLengths = [8, 14, 24, 35, 50, 75, 125];

const apertures = ["ƒ/1.4", "ƒ/4", "ƒ/11"];

export function CameraConfigDialog({
  isOpen,
  onClose,
  onApply,
}: CameraConfigDialogProps) {
  const [config, setConfig] = useState<CameraConfig>({
    camera: "Panavision DXL2",
    lens: "Arri Signature Prime",
    focalLength: 35,
    aperture: "ƒ/4",
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
      <div className="relative z-10 w-[480px] rounded-xl bg-[#1f1f1f] shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
          <h2 className="text-lg font-medium text-white">摄像机</h2>
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
          {/* Camera Selection */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <button className="rounded-lg p-2 text-white/60 transition-colors hover:bg-white/10 hover:text-white">
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M15 18l-6-6 6-6" />
                </svg>
              </button>
              <div className="flex-1">
                <div className="text-sm text-white/60">相机</div>
                <div className="text-white">{config.camera}</div>
              </div>
            </div>
            <div className="flex flex-wrap gap-2 pl-8">
              {cameras.map((camera) => (
                <button
                  key={camera}
                  onClick={() => setConfig({ ...config, camera })}
                  className={cn(
                    "rounded-lg px-4 py-2 text-sm transition-all",
                    config.camera === camera
                      ? "bg-blue-500 text-white"
                      : "bg-white/10 text-white/80 hover:bg-white/20"
                  )}
                >
                  {camera}
                </button>
              ))}
            </div>
          </div>

          {/* Lens Selection */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <button className="rounded-lg p-2 text-white/60 transition-colors hover:bg-white/10 hover:text-white">
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M15 18l-6-6 6-6" />
                </svg>
              </button>
              <div className="flex-1">
                <div className="text-sm text-white/60">镜头</div>
                <div className="text-white">{config.lens}</div>
              </div>
            </div>
            <div className="flex flex-wrap gap-2 pl-8">
              {lenses.map((lens) => (
                <button
                  key={lens}
                  onClick={() => setConfig({ ...config, lens })}
                  className={cn(
                    "rounded-lg px-4 py-2 text-sm transition-all",
                    config.lens === lens
                      ? "bg-blue-500 text-white"
                      : "bg-white/10 text-white/80 hover:bg-white/20"
                  )}
                >
                  {lens}
                </button>
              ))}
            </div>
          </div>

          {/* Focal Length Selection */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <button className="rounded-lg p-2 text-white/60 transition-colors hover:bg-white/10 hover:text-white">
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M15 18l-6-6 6-6" />
                </svg>
              </button>
              <div className="flex-1">
                <div className="text-sm text-white/60">焦距</div>
                <div className="text-white">{config.focalLength} mm</div>
              </div>
            </div>
            <div className="flex flex-wrap gap-2 pl-8">
              {focalLengths.map((focalLength) => (
                <button
                  key={focalLength}
                  onClick={() => setConfig({ ...config, focalLength })}
                  className={cn(
                    "rounded-lg px-4 py-2 text-sm transition-all",
                    config.focalLength === focalLength
                      ? "bg-blue-500 text-white"
                      : "bg-white/10 text-white/80 hover:bg-white/20"
                  )}
                >
                  {focalLength}
                </button>
              ))}
            </div>
          </div>

          {/* Aperture Selection */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <button className="rounded-lg p-2 text-white/60 transition-colors hover:bg-white/10 hover:text-white">
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M15 18l-6-6 6-6" />
                </svg>
              </button>
              <div className="flex-1">
                <div className="text-sm text-white/60">光圈</div>
                <div className="text-white">{config.aperture}</div>
              </div>
            </div>
            <div className="flex flex-wrap gap-2 pl-8">
              {apertures.map((aperture) => (
                <button
                  key={aperture}
                  onClick={() => setConfig({ ...config, aperture })}
                  className={cn(
                    "rounded-lg px-4 py-2 text-sm transition-all",
                    config.aperture === aperture
                      ? "bg-blue-500 text-white"
                      : "bg-white/10 text-white/80 hover:bg-white/20"
                  )}
                >
                  {aperture}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-white/10 px-6 py-4">
          <button
            onClick={handleApply}
            className="w-full rounded-lg bg-blue-500 py-3 text-center font-medium text-white transition-colors hover:bg-blue-600"
          >
            使用
          </button>
        </div>
      </div>
    </div>
  );
}
