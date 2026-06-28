"use client"

import { cn } from "@/lib/utils"

interface KeyboardShortcutsDialogProps {
  isOpen: boolean
  onClose: () => void
}

interface ShortcutItem {
  label: string
  keys: string
}

interface ShortcutSection {
  title: string
  items: ShortcutItem[]
}

const shortcutSections: ShortcutSection[] = [
  {
    title: "创作",
    items: [
      { label: "成组", keys: "G" },
      { label: "合并分镜组", keys: "⌥G" },
      { label: "解组", keys: "⇧G" },
      { label: "连线", keys: "L" },
      { label: "复制节点和连线", keys: "D" },
      { label: "生成", keys: "Enter" },
      { label: "新建节点", keys: "Tab" },
      { label: "节点复制", keys: "Option+拖动节点" },
      { label: "创建副本", keys: "Option+拖动" },
    ],
  },
  {
    title: "缩放",
    items: [
      { label: "放大", keys: "⌘+=" },
      { label: "缩小", keys: "⌘+-" },
      { label: "适应画布", keys: "0" },
      { label: "触控板", keys: "pinch" },
      { label: "鼠标", keys: "⌘+scroll" },
    ],
  },
  {
    title: "移动画布",
    items: [
      { label: "键盘", keys: "Space+拖动" },
      { label: "触控板", keys: "two-finger" },
      { label: "鼠标", keys: "middle-click" },
      { label: "整理画布", keys: "⌥⇧F" },
    ],
  },
  {
    title: "其他",
    items: [
      { label: "撤销", keys: "⌘Z" },
      { label: "重做", keys: "⇧⌘Z" },
      { label: "删除", keys: "Backspace/Delete" },
    ],
  },
]

function KeyBadge({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center justify-center rounded-md bg-[#09caf5]/20 px-1.5 py-0.5 text-xs font-medium text-[#09caf5]">
      {children}
    </span>
  )
}

function PinchIcon({ className }: { className?: string }) {
  return (
    <svg
      className={cn("size-4", className)}
      viewBox="0 0 16 16"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M8 2v12M4 6l4-4 4 4M4 10l4 4 4-4"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function ScrollIcon({ className }: { className?: string }) {
  return (
    <svg
      className={cn("size-4", className)}
      viewBox="0 0 16 16"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect x="4" y="2" width="8" height="12" rx="4" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="8" cy="6" r="1" fill="currentColor" />
    </svg>
  )
}

function TwoFingerIcon({ className }: { className?: string }) {
  return (
    <svg
      className={cn("size-4", className)}
      viewBox="0 0 16 16"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M5 8V4a1 1 0 012 0v4M9 8V3a1 1 0 012 0v5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
      <path
        d="M5 8a2 2 0 004 0"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  )
}

function MiddleClickIcon({ className }: { className?: string }) {
  return (
    <svg
      className={cn("size-4", className)}
      viewBox="0 0 16 16"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect x="2" y="4" width="12" height="9" rx="3" stroke="currentColor" strokeWidth="1.5" />
      <line x1="8" y1="4" x2="8" y2="8" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  )
}

function getKeysDisplay(keys: string) {
  switch (keys) {
    case "pinch":
      return (
        <KeyBadge>
          <PinchIcon className="text-[#09caf5]" />
        </KeyBadge>
      )
    case "⌘+scroll":
      return (
        <span className="inline-flex items-center gap-1">
          <KeyBadge>⌘</KeyBadge>
          <span className="text-xs text-[#999]">+</span>
          <KeyBadge>
            <ScrollIcon className="text-[#09caf5]" />
          </KeyBadge>
        </span>
      )
    case "two-finger":
      return (
        <KeyBadge>
          <TwoFingerIcon className="text-[#09caf5]" />
        </KeyBadge>
      )
    case "middle-click":
      return (
        <KeyBadge>
          <MiddleClickIcon className="text-[#09caf5]" />
        </KeyBadge>
      )
    default:
      return keys.split("+").map((part, i) => (
        <span key={i} className="inline-flex items-center gap-1">
          {i > 0 && <span className="text-xs text-[#999]">+</span>}
          <KeyBadge>{part.trim()}</KeyBadge>
        </span>
      ))
  }
}

export function KeyboardShortcutsDialog({ isOpen, onClose }: KeyboardShortcutsDialogProps) {
  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative w-[480px] max-h-[80vh] overflow-y-auto rounded-xl bg-[#1f1f1f] p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">键盘快捷键</h2>
          <button
            onClick={onClose}
            className="flex size-8 items-center justify-center rounded-lg text-[#999] transition-colors hover:bg-white/10 hover:text-white"
            aria-label="关闭"
          >
            <svg
              className="size-5"
              viewBox="0 0 20 20"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M15 5L5 15M5 5l10 10"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            </svg>
          </button>
        </div>

        {/* Sections */}
        <div className="space-y-6">
          {shortcutSections.map((section) => (
            <div key={section.title}>
              <h3 className="mb-3 text-sm font-medium text-[#666]">{section.title}</h3>
              <div className="space-y-2">
                {section.items.map((item) => (
                  <div
                    key={item.label}
                    className="flex items-center justify-between rounded-lg px-3 py-2 transition-colors hover:bg-white/5"
                  >
                    <span className="text-sm text-[#ccc]">{item.label}</span>
                    <div className="inline-flex items-center gap-1">{getKeysDisplay(item.keys)}</div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
