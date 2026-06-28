import Image from "next/image";
import { cn } from "@/lib/utils";

/** Placeholder logo SVG — will be replaced with the real asset */
function LogoMark() {
  return (
    <svg
      width="28"
      height="28"
      viewBox="0 0 28 28"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <rect width="28" height="28" rx="6" fill="#05dff6" />
      <text
        x="14"
        y="19"
        textAnchor="middle"
        fill="#141414"
        fontSize="14"
        fontWeight="700"
      >
        L
      </text>
    </svg>
  );
}

/** Placeholder logo wordmark SVG */
function LogoWordmark() {
  return (
    <svg
      width="72"
      height="20"
      viewBox="0 0 72 20"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <text x="0" y="15" fill="#f7f7f7" fontSize="14" fontWeight="600">
        LibTV
      </text>
    </svg>
  );
}

/** Placeholder notification bell icon */
function NotificationIcon({ className }: { className?: string }) {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden
    >
      <path
        d="M8 1.5a4.5 4.5 0 0 0-4.5 4.5v2.17L2.47 9.84a.75.75 0 0 0 .53 1.29h10a.75.75 0 0 0 .53-1.29L12.5 8.17V6A4.5 4.5 0 0 0 8 1.5Z"
        fill="#919191"
      />
      <path
        d="M6.25 12a1.75 1.75 0 0 0 3.5 0h-3.5Z"
        fill="#919191"
      />
    </svg>
  );
}

export function TopNavBar() {
  return (
    <nav
      className={cn(
        "flex h-12 items-center justify-between px-4",
        "bg-transparent",
      )}
    >
      {/* ── Left Section ─────────────────────────────────────────── */}
      <div className="flex items-center gap-2">
        {/* Logo */}
        <div className="flex items-center gap-1.5">
          <LogoMark />
          <LogoWordmark />
        </div>

        {/* Separator */}
        <div
          className="mx-1 h-5 w-px bg-[#525252]"
          aria-hidden
        />

        {/* Project name input */}
        <input
          type="text"
          defaultValue="未命名项目"
          className={cn(
            "h-8 max-w-[180px] bg-transparent px-1 text-base text-[#f7f7f7]",
            "outline-none",
            "placeholder:text-[#919191]",
            "border-b border-transparent focus:border-[#525252]",
            "transition-colors duration-150",
          )}
        />

        {/* Canvas tab button */}
        <button
          type="button"
          className={cn(
            "flex h-8 items-center gap-1 rounded-lg px-2 text-base text-[#f7f7f7]",
            "bg-[rgba(38,38,38,0.8)] hover:bg-[#353639]",
            "transition-colors duration-150",
          )}
        >
          画布 2
        </button>
      </div>

      {/* ── Right Section ────────────────────────────────────────── */}
      <div className="flex items-center gap-2">
        {/* Notification icon */}
        <button
          type="button"
          className={cn(
            "flex h-8 w-8 items-center justify-center rounded-lg",
            "hover:bg-[#353639]",
            "transition-colors duration-150",
          )}
          aria-label="通知"
        >
          <NotificationIcon />
        </button>

        {/* VIP button */}
        <button
          type="button"
          className={cn(
            "relative flex h-10 items-center gap-1 rounded-xl px-3",
            "border-[0.5px] border-[#363636] bg-[rgba(38,38,38,0.8)]",
            "text-sm text-[#05dff6]",
            "hover:bg-[#353639]",
            "transition-colors duration-150",
          )}
        >
          <VipIcon />
          <span>会员超市</span>
          {/* Promo badge */}
          <span
            className={cn(
              "absolute -right-2 -top-2 rounded-md px-1 py-0.5",
              "bg-[#05dff6] text-[10px] font-semibold leading-none text-[#141414]",
            )}
          >
            限时 37 折
          </span>
        </button>

        {/* Credits button */}
        <button
          type="button"
          className={cn(
            "flex h-10 items-center gap-1.5 rounded-xl px-3",
            "border-[0.5px] border-[#363636] bg-[rgba(38,38,38,0.8)]",
            "text-sm text-[#f7f7f7]",
            "hover:bg-[#353639]",
            "transition-colors duration-150",
          )}
        >
          <CoinIcon />
          <span>64</span>
        </button>

        {/* User avatar */}
        <button
          type="button"
          className={cn(
            "relative h-8 w-8 overflow-hidden rounded-full",
            "ring-1 ring-[#525252]",
          )}
          aria-label="用户菜单"
        >
          <Image
            src="/images/avatar.png"
            alt="用户头像"
            fill
            className="object-cover"
            sizes="32px"
          />
        </button>
      </div>
    </nav>
  );
}

/* ── Inline placeholder icons (will be replaced with real SVGs) ── */

function VipIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <path
        d="M2 4h12l-2 8H4L2 4Z"
        fill="#05dff6"
        opacity="0.8"
      />
      <path d="M5 4l1.5 4L8 5l1.5 3L12 4" stroke="#141414" strokeWidth="1.2" />
    </svg>
  );
}

function CoinIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <circle cx="8" cy="8" r="6" fill="#f5a623" />
      <text
        x="8"
        y="11"
        textAnchor="middle"
        fill="#141414"
        fontSize="8"
        fontWeight="700"
      >
        $
      </text>
    </svg>
  );
}
