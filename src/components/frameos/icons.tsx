/**
 * FrameOS 风格的 icon 组件 - 内联 SVG，模仿 Remix Icon `ri-*` 的形态
 * 所有 icon 接受 size prop (默认 16)，color prop (默认 currentColor)
 */

interface IconProps {
  size?: number;
  className?: string;
  color?: string;
}

const baseProps = (size: number, color: string | undefined, className: string | undefined) => ({
  width: size,
  height: size,
  viewBox: "0 0 24 24",
  fill: "none",
  xmlns: "http://www.w3.org/2000/svg",
  stroke: color ?? "currentColor",
  strokeWidth: 1.6,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  className,
});

export function ArrowLeftIcon({ size = 16, className, color }: IconProps) {
  return (
    <svg {...baseProps(size, color, className)}>
      <path d="M19 12H5M12 19l-7-7 7-7" />
    </svg>
  );
}

export function ArrowDownIcon({ size = 14, className, color }: IconProps) {
  return (
    <svg {...baseProps(size, color, className)}>
      <path d="M6 9l6 6 6-6" />
    </svg>
  );
}

export function ArrowGoBackIcon({ size = 16, className, color }: IconProps) {
  return (
    <svg {...baseProps(size, color, className)}>
      <path d="M9 14L4 9l5-5" />
      <path d="M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5v0a5.5 5.5 0 0 1-5.5 5.5H11" />
    </svg>
  );
}

export function ArrowGoForwardIcon({ size = 16, className, color }: IconProps) {
  return (
    <svg {...baseProps(size, color, className)}>
      <path d="M15 14l5-5-5-5" />
      <path d="M20 9H9.5a5.5 5.5 0 0 0-5.5 5.5v0a5.5 5.5 0 0 0 5.5 5.5H13" />
    </svg>
  );
}

export function AddLineIcon({ size = 16, className, color }: IconProps) {
  return (
    <svg {...baseProps(size, color, className)}>
      <path d="M12 5v14M5 12h14" />
    </svg>
  );
}

export function FolderImageIcon({ size = 16, className, color }: IconProps) {
  return (
    <svg {...baseProps(size, color, className)}>
      <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
      <circle cx="13" cy="13" r="1.5" />
      <path d="M9 17l3-3 3 3" />
    </svg>
  );
}

export function UploadCloudIcon({ size = 16, className, color }: IconProps) {
  return (
    <svg {...baseProps(size, color, className)}>
      <path d="M16 16l-5-5-5 5" />
      <path d="M11 11v8" />
      <path d="M20 16.7A5 5 0 0 0 17 7h-1.3A8 8 0 1 0 4 15.3" />
    </svg>
  );
}

export function QuestionIcon({ size = 16, className, color }: IconProps) {
  return (
    <svg {...baseProps(size, color, className)}>
      <circle cx="12" cy="12" r="9" />
      <path d="M9.5 9.5a2.5 2.5 0 0 1 5 0c0 1.5-2.5 2-2.5 4" />
      <circle cx="12" cy="17" r="0.5" fill="currentColor" />
    </svg>
  );
}

export function MapPinIcon({ size = 16, className, color }: IconProps) {
  return (
    <svg {...baseProps(size, color, className)}>
      <path d="M12 21s-7-6-7-12a7 7 0 1 1 14 0c0 6-7 12-7 12z" />
      <circle cx="12" cy="9" r="2.5" />
    </svg>
  );
}

export function SubtractIcon({ size = 16, className, color }: IconProps) {
  return (
    <svg {...baseProps(size, color, className)}>
      <path d="M5 12h14" />
    </svg>
  );
}

export function FullscreenExitIcon({ size = 16, className, color }: IconProps) {
  return (
    <svg {...baseProps(size, color, className)}>
      <path d="M9 4v5H4M15 4v5h5M9 20v-5H4M15 20v-5h5" />
    </svg>
  );
}

export function LayoutGridIcon({ size = 16, className, color }: IconProps) {
  return (
    <svg {...baseProps(size, color, className)}>
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </svg>
  );
}

export function PlayFillIcon({ size = 14, className, color }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      xmlns="http://www.w3.org/2000/svg"
      fill={color ?? "currentColor"}
      className={className}
    >
      <path d="M8 5v14l11-7z" />
    </svg>
  );
}

export function PauseFillIcon({ size = 14, className, color }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      xmlns="http://www.w3.org/2000/svg"
      fill={color ?? "currentColor"}
      className={className}
    >
      <rect x="6" y="5" width="4" height="14" rx="1" />
      <rect x="14" y="5" width="4" height="14" rx="1" />
    </svg>
  );
}

export function Upload2Icon({ size = 12, className, color }: IconProps) {
  return (
    <svg {...baseProps(size, color, className)}>
      <path d="M12 15V3M7 8l5-5 5 5" />
      <path d="M3 17v2a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-2" />
    </svg>
  );
}

export function ErrorWarningIcon({ size = 12, className, color }: IconProps) {
  return (
    <svg {...baseProps(size, color ?? "#F59E0B", className)}>
      <path d="M12 3l10 18H2z" />
      <path d="M12 10v5" />
      <circle cx="12" cy="18" r="0.6" fill="currentColor" />
    </svg>
  );
}

export function TextNodeIcon({ size = 12, className, color }: IconProps) {
  // 模仿 ri-text
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill={color ?? "currentColor"}
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <path d="M5 4h14v3h-5v13h-4V7H5z" />
    </svg>
  );
}

export function ImageNodeIcon({ size = 12, className, color }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={color ?? "currentColor"}
      strokeWidth="1.6"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <rect x="3" y="4" width="18" height="16" rx="2" />
      <circle cx="9" cy="10" r="2" />
      <path d="M21 17l-5-5-7 7" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function FilmNodeIcon({ size = 12, className, color }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={color ?? "currentColor"}
      strokeWidth="1.6"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="M7 5v14M17 5v14" />
      <path d="M10 9l4 3-4 3z" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function DownloadIcon({ size = 14, className, color }: IconProps) {
  return (
    <svg {...baseProps(size, color, className)}>
      <path d="M12 4v12M7 11l5 5 5-5" />
      <path d="M4 20h16" />
    </svg>
  );
}

export function FullscreenIcon({ size = 16, className, color }: IconProps) {
  return (
    <svg {...baseProps(size, color, className)}>
      <path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5" />
    </svg>
  );
}

export function ScissorsIcon({ size = 14, className, color }: IconProps) {
  // 模仿 prompt bar 左侧的"删除连线"剪刀按钮
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={color ?? "currentColor"}
      strokeWidth="1.6"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <circle cx="6" cy="6" r="3" />
      <circle cx="6" cy="18" r="3" />
      <path d="M8.5 7.5L20 18M8.5 16.5L20 6" strokeLinecap="round" />
    </svg>
  );
}

export function CloseIcon({ size = 14, className, color }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={color ?? "currentColor"}
      strokeWidth="1.8"
      strokeLinecap="round"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <path d="M18 6L6 18M6 6l12 12" />
    </svg>
  );
}
