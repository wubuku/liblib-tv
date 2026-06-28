"use client"

import { useState, useCallback } from "react"
import { cn } from "@/lib/utils"

interface SidebarButtonProps {
  label: string
  icon: React.ReactNode
}

function SidebarButton({ label, icon }: SidebarButtonProps) {
  const [showTooltip, setShowTooltip] = useState(false)
  const [timeoutId, setTimeoutId] = useState<ReturnType<typeof setTimeout> | null>(null)

  const handleMouseEnter = useCallback(() => {
    const id = setTimeout(() => setShowTooltip(true), 500)
    setTimeoutId(id)
  }, [])

  const handleMouseLeave = useCallback(() => {
    if (timeoutId) {
      clearTimeout(timeoutId)
      setTimeoutId(null)
    }
    setShowTooltip(false)
  }, [timeoutId])

  return (
    <div className="relative">
      <button
        className={cn(
          "flex size-8 items-center justify-center rounded-lg border-none bg-transparent",
          "cursor-pointer transition-colors duration-150 ease-in-out",
          "hover:bg-[#353639]"
        )}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        aria-label={label}
      >
        {icon}
      </button>
      {showTooltip && (
        <div
          className={cn(
            "absolute left-full top-1/2 z-50 ml-2 -translate-y-1/2",
            "whitespace-nowrap rounded-md bg-[#1c1d29] px-3 py-1.5",
            "text-xs text-[#f7f7f7] shadow-[0_2px_8px_rgba(0,0,0,0.2)]"
          )}
        >
          {label}
        </div>
      )}
    </div>
  )
}

// Placeholder SVG icons (16x16)
const AddNodeIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
    <rect x="3" y="3" width="10" height="10" rx="2" stroke="#f7f7f7" strokeWidth="1.5" />
    <path d="M8 5.5V10.5M5.5 8H10.5" stroke="#f7f7f7" strokeWidth="1.5" strokeLinecap="round" />
  </svg>
)

const ToolboxIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
    <rect x="2" y="5" width="12" height="8" rx="1.5" stroke="#f7f7f7" strokeWidth="1.5" />
    <path d="M5 5V3.5C5 2.67 5.67 2 6.5 2H9.5C10.33 2 11 2.67 11 3.5V5" stroke="#f7f7f7" strokeWidth="1.5" />
    <path d="M2 8.5H14" stroke="#f7f7f7" strokeWidth="1.5" />
  </svg>
)

const MaterialIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
    <rect x="2" y="2" width="5" height="5" rx="1" stroke="#f7f7f7" strokeWidth="1.5" />
    <rect x="9" y="2" width="5" height="5" rx="1" stroke="#f7f7f7" strokeWidth="1.5" />
    <rect x="2" y="9" width="5" height="5" rx="1" stroke="#f7f7f7" strokeWidth="1.5" />
    <rect x="9" y="9" width="5" height="5" rx="1" stroke="#f7f7f7" strokeWidth="1.5" />
  </svg>
)

const CharacterIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
    <circle cx="8" cy="5" r="3" stroke="#f7f7f7" strokeWidth="1.5" />
    <path d="M2.5 14C2.5 11 4.5 9 8 9C11.5 9 13.5 11 13.5 14" stroke="#f7f7f7" strokeWidth="1.5" strokeLinecap="round" />
  </svg>
)

const HistoryIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
    <circle cx="8" cy="8" r="6" stroke="#f7f7f7" strokeWidth="1.5" />
    <path d="M8 4.5V8L10.5 10.5" stroke="#f7f7f7" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
)

const ShortcutsIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
    <rect x="1.5" y="4" width="13" height="8" rx="1.5" stroke="#f7f7f7" strokeWidth="1.5" />
    <path d="M4.5 7H6.5M8 7H11.5M5 9.5H11" stroke="#f7f7f7" strokeWidth="1.5" strokeLinecap="round" />
  </svg>
)

const TutorialIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
    <circle cx="8" cy="8" r="6" stroke="#f7f7f7" strokeWidth="1.5" />
    <path d="M6.5 6.5C6.5 5.67 7.17 5 8 5C8.83 5 9.5 5.67 9.5 6.5C9.5 7.33 8.83 8 8 8V9.5" stroke="#f7f7f7" strokeWidth="1.5" strokeLinecap="round" />
    <circle cx="8" cy="11" r="0.75" fill="#f7f7f7" />
  </svg>
)

const sidebarItems: SidebarButtonProps[] = [
  { label: "添加节点", icon: <AddNodeIcon /> },
  { label: "打开工具箱", icon: <ToolboxIcon /> },
  { label: "素材库", icon: <MaterialIcon /> },
  { label: "角色库", icon: <CharacterIcon /> },
  { label: "历史记录", icon: <HistoryIcon /> },
  { label: "快捷键", icon: <ShortcutsIcon /> },
  { label: "教程", icon: <TutorialIcon /> },
]

export function LeftSidebar() {
  return (
    <aside className="flex w-12 flex-col gap-1 bg-transparent p-2">
      {sidebarItems.map((item) => (
        <SidebarButton key={item.label} {...item} />
      ))}
    </aside>
  )
}
