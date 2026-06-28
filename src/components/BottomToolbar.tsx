"use client"

import { Tooltip } from "@base-ui/react/tooltip"
import { cn } from "@/lib/utils"

// Placeholder SVG icons (16x16)
function AssetIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="2" y="2" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5" />
      <rect x="9" y="2" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5" />
      <rect x="2" y="9" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5" />
      <rect x="9" y="9" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  )
}

function ArrangeIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M2 4h12M2 8h12M2 12h12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  )
}

function MinimapIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="1.5" y="1.5" width="13" height="13" rx="2" stroke="currentColor" strokeWidth="1.5" />
      <rect x="4" y="4" width="5" height="4" rx="0.5" stroke="currentColor" strokeWidth="1" />
    </svg>
  )
}

function GridIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M2 2h12v12H2V2z" stroke="currentColor" strokeWidth="1.5" />
      <path d="M2 6.5h12M2 10.5h12M6.5 2v12M10.5 2v12" stroke="currentColor" strokeWidth="1" />
    </svg>
  )
}

interface ToolbarButtonProps {
  children: React.ReactNode
  tooltip?: string
  className?: string
  onClick?: () => void
}

function ToolbarButton({ children, tooltip, className, onClick }: ToolbarButtonProps) {
  const button = (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "inline-flex items-center justify-center size-7 rounded-lg text-[#f7f7f7] transition-colors duration-150 ease-in-out hover:bg-[#353639]",
        className
      )}
    >
      {children}
    </button>
  )

  if (!tooltip) {
    return button
  }

  return (
    <Tooltip.Provider delay={300}>
      <Tooltip.Root>
        <Tooltip.Trigger render={button} />
        <Tooltip.Portal>
          <Tooltip.Positioner side="top" sideOffset={8}>
            <Tooltip.Popup className="rounded-lg bg-[#1c1d29] px-3 py-1.5 text-xs text-[#f7f7f7] shadow-lg border border-[#525252]">
              {tooltip}
            </Tooltip.Popup>
          </Tooltip.Positioner>
        </Tooltip.Portal>
      </Tooltip.Root>
    </Tooltip.Provider>
  )
}

export function BottomToolbar() {
  return (
    <div className="fixed bottom-0 left-0 right-0 flex flex-row items-center gap-1 p-2 bg-transparent z-50">
      <ToolbarButton className="h-7 w-auto gap-1.5 px-3 text-base font-normal">
        <AssetIcon />
        <span>资产管理</span>
      </ToolbarButton>

      <ToolbarButton tooltip="整理画布，Option+Shift+F">
        <ArrangeIcon />
      </ToolbarButton>

      <ToolbarButton tooltip="切换小地图">
        <MinimapIcon />
      </ToolbarButton>

      <ToolbarButton tooltip="网格吸附">
        <GridIcon />
      </ToolbarButton>

      <ToolbarButton>
        <span className="text-xs">54%</span>
      </ToolbarButton>
    </div>
  )
}
