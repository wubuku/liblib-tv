/* Batch 180: 源站尝试芯片 iconify (libtv 集) 图标原字形——SVG path 逐字
   直采（2026-09-08 CDP，viewBox 与 d 与源站一致），替代 lucide 形似替代。 */

interface AttemptChipIconProps {
  className?: string;
}

export function LongVideoIcon({ className }: AttemptChipIconProps) {
  return (
    <svg aria-hidden="true" role="img" className={className} width="14" height="14" viewBox="0 0 16 16" fill="none">
      <g transform="translate(1 1)">
        <path
          d="M1.1 4.3a2.94 2.94 0 0 1 4.42.13l1.5 1.7 1.48-1.7.12-.12a2.94 2.94 0 0 1 4.41.12 4 4 0 0 1 0 5.14l-.12.13a2.94 2.94 0 0 1-4.41-.13L7 7.88l-1.48 1.7-.12.13a2.93 2.93 0 0 1-4.3 0l-.12-.13a4 4 0 0 1 0-5.14zm11.21.96a2 2 0 0 0-3.09 0L7.67 7.01l1.55 1.76a2 2 0 0 0 3.09 0c.85-.97.85-2.54 0-3.5M4.8 5.25a2 2 0 0 0-3.1 0 2.7 2.7 0 0 0 0 3.5 2 2 0 0 0 3.1 0l1.5-1.7a.1.1 0 0 0 0-.1z"
          fill="currentColor"
        />
      </g>
    </svg>
  );
}

export function FirstLastFrameIcon({ className }: AttemptChipIconProps) {
  return (
    <svg aria-hidden="true" role="img" className={className} width="14" height="14" viewBox="0 0 20.05 22" fill="none">
      <path
        d="M19.49 15c.75.43.75 1.51 0 1.94l-8.36 4.77c-.68.39-1.52.39-2.21 0L.56 16.94a1.12 1.12 0 0 1 0-1.94l.82-.47 7.54 4.3c.69.4 1.53.4 2.21 0l7.54-4.3zm0-5.12c.75.43.75 1.5 0 1.94l-8.36 4.76c-.68.4-1.52.4-2.21 0L.56 11.82a1.12 1.12 0 0 1 0-1.94l.82-.47 7.54 4.3c.69.4 1.53.4 2.21 0l7.54-4.3zM8.92.29a2.2 2.2 0 0 1 2.21 0l8.36 4.77c.75.43.75 1.51 0 1.94l-8.36 4.77c-.68.39-1.52.39-2.21 0L.56 7a1.12 1.12 0 0 1 0-1.94z"
        fill="currentColor"
      />
    </svg>
  );
}

export function FirstFrameIcon({ className }: AttemptChipIconProps) {
  return (
    <svg aria-hidden="true" role="img" className={className} width="14" height="14" viewBox="0 0 22 22" fill="none">
      <path
        d="M11.58 0c0 5.76 4.66 10.42 10.42 10.42v1.16A10.4 10.4 0 0 0 11.58 22h-1.16l-.01-.54A10.4 10.4 0 0 0 0 11.58v-1.16c5.76 0 10.42-4.66 10.42-10.42z"
        fill="currentColor"
      />
    </svg>
  );
}
