"use client";

import { cn } from "@/lib/utils";

interface ToolbarButtonProps {
  icon: React.ReactNode;
  label: string;
  badge?: string;
  onClick?: () => void;
}

function ToolbarButton({ icon, label, badge, onClick }: ToolbarButtonProps) {
  return (
    <button
      onClick={onClick}
      className="flex flex-col items-center gap-1 p-2 rounded-lg hover:bg-[#353639] transition-colors group"
    >
      <div className="text-[#919191] group-hover:text-[#f7f7f7] transition-colors">
        {icon}
      </div>
      <span className="text-[10px] text-[#919191] group-hover:text-[#f7f7f7] transition-colors">
        {label}
      </span>
      {badge && (
        <span className="absolute -top-1 -right-1 text-[8px] px-1 py-0.5 bg-[#f53f3f] text-white rounded">
          {badge}
        </span>
      )}
    </button>
  );
}

export function ImageToolbar() {
  return (
    <div className="absolute right-[-60px] top-1/2 -translate-y-1/2 z-50 flex flex-col gap-1">
      {/* Portrait texture adjustment */}
      <ToolbarButton
        icon={
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="6" r="3" stroke="currentColor" strokeWidth="1.2" />
            <path d="M4 14C4 11 5.5 9 8 9C10.5 9 12 11 12 14" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
          </svg>
        }
        label="人像质感"
        badge="NEW"
      />

      {/* Panorama */}
      <ToolbarButton
        icon={
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M2 4C2 4 4 2 8 2C12 2 14 4 14 4V12C14 12 12 10 8 10C4 10 2 12 2 12V4Z" stroke="currentColor" strokeWidth="1.2" />
          </svg>
        }
        label="全景"
      />

      {/* Multi-angle */}
      <ToolbarButton
        icon={
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <rect x="2" y="2" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.2" />
            <rect x="9" y="2" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.2" />
            <rect x="2" y="9" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.2" />
            <rect x="9" y="9" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.2" />
          </svg>
        }
        label="多角度"
      />

      {/* Lighting */}
      <ToolbarButton
        icon={
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="6" r="3" stroke="currentColor" strokeWidth="1.2" />
            <path d="M8 9V14M6 12H10" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
          </svg>
        }
        label="打光"
      />

      {/* Grid */}
      <ToolbarButton
        icon={
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <rect x="2" y="2" width="12" height="12" rx="1" stroke="currentColor" strokeWidth="1.2" />
            <path d="M6 2V14M10 2V14M2 6H14M2 10H14" stroke="currentColor" strokeWidth="1" />
          </svg>
        }
        label="九宫格"
      />

      {/* HD */}
      <ToolbarButton
        icon={
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <rect x="2" y="4" width="12" height="8" rx="1" stroke="currentColor" strokeWidth="1.2" />
            <path d="M5 7V9M8 6V10M11 7V9M5 8H8M8 8H11" stroke="currentColor" strokeWidth="1" strokeLinecap="round" />
          </svg>
        }
        label="高清"
      />

      {/* Grid split */}
      <ToolbarButton
        icon={
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <rect x="2" y="2" width="12" height="12" rx="1" stroke="currentColor" strokeWidth="1.2" />
            <path d="M8 2V14M2 8H14" stroke="currentColor" strokeWidth="1.2" />
          </svg>
        }
        label="宫格切分"
      />
    </div>
  );
}
