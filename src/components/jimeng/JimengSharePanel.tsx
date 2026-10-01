"use client";

import { useEffect, useRef, useState } from "react";

/**
 * 顶栏「分享」→ 分享画布面板。
 *
 * SOURCE_FACT 2026-10-04 @1680×826（登录态，canvas-share-panel-surface）：
 * 400×251 @[1268,56]，bg rgb(38,38,38) / radius 16 / flex-col。
 * 纵向是**三段**，不是一列 —— 批 821 实测树：
 *   header  400×52  p 12/16/4/16  items-center   h2 14/22/w500
 *   body    400×199 flex-1 flex-col gap-4
 *     section 400×122 p 12/16/12/16 gap-4… 实测 gap-12
 *       链接药丸  368×40 r8 bg white/8  p 0/2/0/12 gap-4 items-center
 *         url span 14/22 white/35 ellipsis-nowrap
 *         分隔条  1×10 bg white/4
 *         复制链接  100×36 r6 bg white/8 13/22/w500 #FAFAFA
 *       权限行  368×46 flex gap-12 → 内层 gap-8 items-center
 *         圆标    36×36 r50% bg white/8，内含 20×20 锁 svg
 *         文字列  324×46
 *           权限 chip 106×26 r8 p 0/4/0/4 gap-4 13/22/w500 + 16×16 倒角 svg
 *           说明      12/20 white/35 ml-4 ellipsis-nowrap
 *     footer (canvas-share-scope-action) 400×73 p 0/0/4/0 gap-4
 *       分隔线  376×1 mx-12 bg white/4
 *       行      400×64 p 14/16/14/16 r12 items-center justify-between
 *         文案 span 13/22 white/60 + 16×16 星芒 svg（品牌蓝 rgb(0,158,250)）
 *         创建团队  80×36 r6 p 0/4/0/4 gap-4 13/22/w500 #FAFAFA + 16×16 svg
 *                  ——源站这枚是**透明底无边框** ghost，不是描边按钮
 *
 * 批 821 之前这面板是「一列裸文案」：没有药丸、没有分隔线、权限行是纯文本，
 * 内容自然高度 246 > 可用 219，flex 把两枚按钮从 32/36 压到 19.5/21.5。
 * 按源站三段结构重排后纵向严丝合缝 52+199=251。
 *
 * 权限 chip 点开是 role=menu 200×84 @[1316,202]（=chip 左移 12、下沿 +4）：
 * bg rgb(51,51,51) r12 p-1 gap-1；两枚 role=menuitemradio 192×36 r8 p 0/12/0/12
 * 13/22/w500 #FAFAFA，选中项 aria-checked=true 且右侧带 16×16 对勾。
 */

const PERM_LABEL = {
  self: "仅自己可访问",
  anyone: "获得此链接的任何人",
} as const;
type Perm = keyof typeof PERM_LABEL;

// 两态文案都是源站实测（第二态需在源站改权限后读，已立即改回）。
// 写之前先猜的「获得此链接的任何人都可以访问画布」是错的 —— 源站是
// 「任何人都能使用此链接访问画布」。chip 宽度也随文案走：106 → 145。
const PERM_DESC: Record<Perm, string> = {
  self: "只有你可以通过此链接访问画布",
  anyone: "任何人都能使用此链接访问画布",
};

function LockIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path
        clipRule="evenodd"
        d="M10 1.66667C7.23858 1.66667 5 3.90524 5 6.66667V7.7423C3.7784 8.23679 2.91667 9.43442 2.91667 10.8333V15C2.91667 16.8409 4.40905 18.3333 6.25 18.3333H13.75C15.5909 18.3333 17.0833 16.8409 17.0833 15V10.8333C17.0833 9.43442 16.2216 8.23679 15 7.7423V6.66667C15 3.90524 12.7614 1.66667 10 1.66667ZM13.3333 6.66667V7.5H6.66667V6.66667C6.66667 4.82572 8.15905 3.33333 10 3.33333C11.8409 3.33333 13.3333 4.82572 13.3333 6.66667ZM6.25 9.16667C5.32953 9.16667 4.58333 9.91286 4.58333 10.8333V15C4.58333 15.9205 5.32953 16.6667 6.25 16.6667H13.75C14.6705 16.6667 15.4167 15.9205 15.4167 15V10.8333C15.4167 9.91286 14.6705 9.16667 13.75 9.16667H6.25ZM9.9998 14.1665C10.6902 14.1665 11.2498 13.6068 11.2498 12.9165C11.2498 12.2261 10.6902 11.6665 9.9998 11.6665C9.30944 11.6665 8.7498 12.2261 8.7498 12.9165C8.7498 13.6068 9.30944 14.1665 9.9998 14.1665Z"
        fill="currentColor"
      />
    </svg>
  );
}

function ChevronIcon({ className }: { className?: string }) {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      aria-hidden="true"
      className={className}
    >
      <path
        d="M7.62309 5.62305C7.83137 5.41479 8.16872 5.41478 8.37699 5.62305L12.0437 9.28972C12.2519 9.498 12.2519 9.83536 12.0437 10.0436C11.8354 10.2519 11.498 10.2518 11.2898 10.0436L8.00004 6.75391L4.71033 10.0436C4.50207 10.2519 4.16471 10.2518 3.95642 10.0436C3.74814 9.83534 3.74814 9.498 3.95642 9.28972L7.62309 5.62305Z"
        fill="currentColor"
        transform="rotate(180 8 8)"
      />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <g transform="translate(1.2 3.2)">
        <path
          clipRule="evenodd"
          d="M13.3657 0.234315C13.6781 0.546734 13.6781 1.05327 13.3657 1.36569L5.36569 9.36569C5.05327 9.67811 4.54673 9.67811 4.23431 9.36569L0.234315 5.36569C-0.0781049 5.05327 -0.0781049 4.54673 0.234315 4.23431C0.546734 3.9219 1.05327 3.9219 1.36569 4.23431L4.8 7.66863L12.2343 0.234315C12.5467 -0.0781049 13.0533 -0.0781049 13.3657 0.234315Z"
          fill="currentColor"
        />
      </g>
    </svg>
  );
}

function SparkleIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M11.324 3.488c.216-.65 1.136-.65 1.352 0l1.275 3.85a4.27 4.27 0 0 0 2.711 2.71l3.85 1.276c.65.216.65 1.136 0 1.352l-3.85 1.275a4.27 4.27 0 0 0-2.71 2.711l-1.276 3.85c-.216.65-1.136.65-1.352 0l-1.275-3.85a4.27 4.27 0 0 0-2.711-2.71l-3.85-1.276c-.65-.216-.65-1.136 0-1.352l3.85-1.275a4.271 4.271 0 0 0 2.71-2.711l1.276-3.85Z"
        fill="rgb(0, 158, 250)"
      />
    </svg>
  );
}

function TeamPlusIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path
        d="M12.0938 10.4268C12.4618 10.4269 12.7598 10.7257 12.7598 11.0938V12.2598H13.9268C14.2949 12.2598 14.5937 12.5586 14.5938 12.9268C14.5937 13.2949 14.2949 13.5938 13.9268 13.5938H12.7598V14.7598C12.7598 15.1278 12.4618 15.4266 12.0938 15.4268C11.7256 15.4268 11.4268 15.128 11.4268 14.7598V13.5938H10.2598C9.89175 13.5936 9.59379 13.2948 9.59375 12.9268C9.59375 12.5587 9.89173 12.2599 10.2598 12.2598H11.4268V11.0938C11.4268 10.7256 11.7256 10.4268 12.0938 10.4268ZM5.88184 8.8584C7.11658 8.8585 8.22014 9.41983 8.95215 10.3008C8.63561 10.6791 8.38672 11.1157 8.22266 11.5918C7.77446 10.7583 6.89436 10.1915 5.88184 10.1914H5.09473C3.62782 10.1915 2.43852 11.3807 2.43848 12.8477C2.43848 13.2157 2.14043 13.5144 1.77246 13.5146C1.40427 13.5146 1.10547 13.2158 1.10547 12.8477C1.10551 10.6444 2.89144 8.85849 5.09473 8.8584H5.88184ZM11.5029 4.2666C12.7719 4.26678 13.8006 5.28908 13.8008 6.5498C13.8007 7.81066 12.772 8.83283 11.5029 8.83301C10.2338 8.83296 9.20512 7.81074 9.20508 6.5498C9.20528 5.289 10.2339 4.26665 11.5029 4.2666ZM5.48828 2.24609C7.05293 2.24627 8.32224 3.52726 8.32227 5.10742C8.32222 6.68757 7.05291 7.96857 5.48828 7.96875C3.92365 7.96857 2.65532 6.68757 2.65527 5.10742C2.6553 3.52726 3.92364 2.24627 5.48828 2.24609ZM11.5029 5.60059C10.9621 5.60063 10.5383 6.03351 10.5381 6.5498C10.5381 7.06623 10.962 7.49996 11.5029 7.5C12.0437 7.49983 12.4677 7.06615 12.4678 6.5498C12.4676 6.03359 12.0436 5.60076 11.5029 5.60059ZM5.48828 3.5791C4.67236 3.57928 3.9883 4.25124 3.98828 5.10742C3.98832 5.96359 4.67237 6.63556 5.48828 6.63574C6.30419 6.63556 6.98824 5.96359 6.98828 5.10742C6.98826 4.25124 6.3042 3.57928 5.48828 3.5791Z"
        fill="currentColor"
      />
    </svg>
  );
}

export function JimengSharePanel({
  canvasUrl,
  onClose,
  onCopy,
  onCreateTeam,
}: {
  canvasUrl: string;
  onClose: () => void;
  onCopy?: () => void;
  onCreateTeam?: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [perm, setPerm] = useState<Perm>("self");
  const [permOpen, setPermOpen] = useState(false);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      // 先收权限下拉，再收面板（源站是两层浮层）
      if (permOpen) {
        setPermOpen(false);
        return;
      }
      onClose();
    };
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    };
    // 捕获阶段：工作区有全局 Escape 处理器会在冒泡阶段 stopPropagation，
    // 冒泡监听收不到事件，浮层就关不掉。
    window.addEventListener("keydown", onKey, true);
    window.addEventListener("mousedown", onDown, true);
    return () => {
      window.removeEventListener("keydown", onKey, true);
      window.removeEventListener("mousedown", onDown, true);
    };
  }, [onClose, permOpen]);

  return (
    <div
      ref={ref}
      role="dialog"
      aria-label="分享画布"
      data-testid="topbar-share-panel"
      className="absolute right-0 top-[46px] z-[120] flex h-[251px] w-[400px] flex-col overflow-hidden rounded-2xl"
      style={{ background: "rgb(38,38,38)" }}
    >
      {/* header 52 = 12 + 22(h2) + … +4，h2 在内容盒里居中 */}
      <div className="flex h-[52px] shrink-0 items-center px-4 pb-1 pt-3">
        <h2 className="m-0 text-[14px] font-medium leading-[22px] text-white">
          分享画布
        </h2>
      </div>

      <div className="flex flex-1 flex-col gap-1">
        <div className="flex flex-col gap-3 px-4 py-3">
          {/* 链接药丸：url 省略 + 1×10 分隔条 + 复制链接 100×36 */}
          <div
            data-testid="share-link-pill"
            className="flex h-10 shrink-0 items-center gap-1 rounded-lg bg-white/[0.08] py-0 pl-3 pr-0.5"
          >
            <span className="min-w-0 flex-1 truncate text-[14px] leading-[22px] text-white/35">
              {canvasUrl}
            </span>
            <span aria-hidden="true" className="h-2.5 w-px shrink-0 bg-white/[0.04]" />
            <button
              type="button"
              aria-label="复制链接"
              data-testid="share-copy-link"
              onClick={onCopy}
              className="flex h-9 w-[100px] shrink-0 items-center justify-center rounded-md bg-white/[0.08] text-[13px] font-medium leading-[22px] text-[#FAFAFA] hover:bg-white/[0.16]"
            >
              复制链接
            </button>
          </div>

          {/* 权限行：36×36 圆标 + 权限 chip(106×26) + 说明 */}
          <div className="flex shrink-0 gap-3">
            <div className="flex flex-1 items-center gap-2">
              <span
                aria-hidden="true"
                className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-white/[0.08] text-[#FAFAFA]"
              >
                <LockIcon />
              </span>
              <div className="min-w-0 flex-1">
                <div className="relative">
                  <button
                    type="button"
                    aria-haspopup="menu"
                    aria-expanded={permOpen}
                    data-testid="share-perm-trigger"
                    onClick={() => setPermOpen((v) => !v)}
                    className="flex h-[26px] items-center gap-1 rounded-lg px-1 text-[13px] font-medium leading-[22px] text-[#FAFAFA] hover:bg-white/[0.08] aria-expanded:bg-white/[0.08]"
                  >
                    {PERM_LABEL[perm]}
                    {/* 源站实测：展开时 chip 底色 rgba(255,255,255,0.08)，
                        倒角由 matrix(none) 变 matrix(-1,0,0,-1,0,0) 即 180° 反向 */}
                    <ChevronIcon className={permOpen ? "rotate-180" : undefined} />
                  </button>
                  {permOpen ? (
                    <div
                      role="menu"
                      aria-label="访问权限"
                      data-testid="share-perm-menu"
                      className="absolute left-[-12px] top-[30px] z-[130] flex w-[200px] flex-col gap-1 rounded-xl p-1"
                      style={{ background: "rgb(51,51,51)" }}
                    >
                      {(Object.keys(PERM_LABEL) as Perm[]).map((k) => (
                        <button
                          key={k}
                          type="button"
                          role="menuitemradio"
                          aria-checked={perm === k}
                          data-testid="share-perm-option"
                          onClick={() => {
                            setPerm(k);
                            setPermOpen(false);
                          }}
                          className="flex h-9 w-full items-center gap-1 rounded-lg px-3 text-[13px] font-medium leading-[22px] text-[#FAFAFA] hover:bg-white/[0.08]"
                        >
                          <span className="min-w-0 flex-1 truncate text-left">
                            {PERM_LABEL[k]}
                          </span>
                          {perm === k ? <CheckIcon /> : null}
                        </button>
                      ))}
                    </div>
                  ) : null}
                </div>
                <p className="ml-1 truncate text-[12px] leading-5 text-white/35">
                  {PERM_DESC[perm]}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* footer 73 = 分隔线 1 + gap 4 + 行 64 + pb 4 */}
        <div
          data-testid="canvas-share-scope-action"
          className="flex flex-col gap-1 pb-1"
        >
          <div aria-hidden="true" className="mx-3 h-px shrink-0 bg-white/[0.04]" />
          <div className="flex h-16 shrink-0 items-center justify-between rounded-xl px-4 py-3.5">
            <span className="flex min-w-0 items-center gap-1 text-[13px] leading-[22px] text-white/60">
              <SparkleIcon />
              <span className="truncate">创建团队，与成员在画布实时协作</span>
            </span>
            {/* 批 821 SOURCE_FACT: 源站这枚是 80×36 @[1572,253]，透明底 ghost，
                点开是**全屏**商业化抽屉「高级团队会员-12个月」（实测 1680×1050，
                含席位价与倒计时）。那是付费购买流程 —— 本轮计费边界内不去点购买，
                也不在复刻里造一个带死 CTA 的假购买页。改为接到**已存在且能用**的
                会员弹窗 (CLONE_DECISION)：语义同源（团队会员），且不新增死按钮。
                此按钮此前无 onClick，是普查在 share 态查出的唯一真死按钮。 */}
            <button
              type="button"
              aria-label="创建团队"
              data-testid="share-create-team"
              onClick={onCreateTeam}
              className="flex h-9 w-20 shrink-0 items-center justify-center gap-1 rounded-md text-[13px] font-medium leading-[22px] text-[#FAFAFA] hover:bg-white/[0.08]"
            >
              <TeamPlusIcon />
              创建团队
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
