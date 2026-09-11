/**
 * 即梦画布复刻 — 品牌专属图标 (内联 SVG)。
 * 通用图标用 lucide-react；此处只放 lucide 没有的源站品牌图形。
 * 形状为视觉近似 (CLONE_DECISION)，非源站资产拷贝。
 */

/** 顶栏纸飞机 Logo (蓝紫渐变) */
export function JimengLogo({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 28 28" fill="none" aria-hidden>
      <defs>
        <linearGradient id="jimeng-logo-g" x1="2" y1="4" x2="24" y2="24">
          <stop offset="0" stopColor="#69B6FF" />
          <stop offset="0.5" stopColor="#3D7BFF" />
          <stop offset="1" stopColor="#7B5BFF" />
        </linearGradient>
      </defs>
      <path
        d="M25.2 3.4 3.6 11.1c-1 .4-1 1.8 0 2.2l7.5 2.9c.4.2.7.5.9.9l2.9 7.5c.4 1 1.8 1 2.2 0L24.6 3.4c.3-.8-.5-1.6-1.3-1.3Z"
        fill="url(#jimeng-logo-g)"
      />
      <path
        d="m12 16.2 4.6-4.6c.4-.4.1-1-.4-.9l-6.5 1.9c-.6.2-.7 1-.1 1.3l1.6.7c.3.1.6.4.8.6Z"
        fill="#0D0D0D"
        fillOpacity="0.35"
      />
    </svg>
  );
}

/** VIP 钻石 ✦ (text-dreamina-brand-bright-default → rgb(0,158,250) SOURCE_FACT) */
export function VipDiamond({ size = 14 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 14 14"
      fill="none"
      aria-hidden
      className="shrink-0"
    >
      <path
        d="M7 0.8 8.6 5.4 13.2 7 8.6 8.6 7 13.2 5.4 8.6 0.8 7 5.4 5.4Z"
        fill="#009EFA"
      />
    </svg>
  );
}

/** 节点标题左侧的文件占位小图标 */
export function FileBadgeIcon({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none" aria-hidden>
      <rect
        x="1.5"
        y="2.5"
        width="13"
        height="11"
        rx="2"
        stroke="currentColor"
        strokeWidth="1.2"
      />
      <path d="M7 6v4l3.2-2L7 6Z" fill="currentColor" />
    </svg>
  );
}
