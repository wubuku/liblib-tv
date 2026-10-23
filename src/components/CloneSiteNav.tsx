import Link from "next/link";

/**
 * 1032-③：**站点级导航**（挂在站点根目录 `/` 的顶栏左簇里）。
 *
 * ⭐⭐⭐⭐⭐ **为什么需要它**：站点根路由 `/` 是 **LibTV 画布本身**，
 * 而**即梦画布、全部项目、克隆总览**同样是「已完成的克隆成果」，
 * ⇒ 它们曾经只能靠手敲 URL 才走得到 ⇒ **「做完了」不等于「走得到」**。
 *
 * ⭐⭐⭐⭐⭐ **为什么这一组链接必须住在这个文件里**：
 * `scripts/jimeng_probe1033_clone_reachability.py` 的 P5 断言
 * 「**站点导航必须以字面量 href 指向每一个克隆成果页**」⇒ ⇒ ⇒⇒
 * ⇒ ⇒ ⇒⇒ 而它要**精确**（不许过近似）⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒⇒
 * ⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒⇒ **⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 就得有一个「点名到文件」的落点** ⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒
 * ⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 所以链接集中在这里、而不是散在各页** ⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒
 *
 * ⚠️⭐⭐ **为什么用 `<a>` 而不是 `<button>`**：
 * 站内跳转就该是链接（可右键新标签页打开、可被浏览器历史、可被抓取），
 * 而 `<button onClick={router.push}>` 三样都不是。
 *
 * ⚠️ **只挂在根目录**：`/frameos` 与 `/jimeng` 是**别的产品的复刻**，
 * 而它们的顶栏必须**忠于源站** ⇒ 不许把本站的导航塞进去。
 */

function LibTvMark() {
  return (
    <svg width="25" height="18" viewBox="0 0 25 18" fill="none" aria-hidden="true">
      <path d="M2.4 2h20.2L18 16H1L5.4 4.6h10.7l-1.3 3.2H7.7l-1.9 5h9.9l3-7.7H1.5L2.4 2Z" fill="currentColor" />
    </svg>
  );
}

const CHIP =
  "flex h-8 items-center rounded-lg bg-[#262626] px-2 text-[11px] leading-none text-[#c9c9c9] shadow-[0_4px_16px_rgba(0,0,0,0.25)] transition-colors hover:bg-[#303030] hover:text-white";

export function CloneSiteNav() {
  return (
    <div
      data-clone-site-nav
      className="flex h-8 items-center gap-1"
    >
      {/* LibTV 标记芯片（沿用源站 logo 位的形态）⇒ 它同时是「另一个克隆成果」的入口 */}
      <Link
        href="/frameos/canvas/demo"
        data-clone-site-nav-link="frameos-canvas"
        title="进入 FrameOS 画布（本站另一个克隆成果）"
        className="flex h-8 w-10 items-center justify-center rounded-lg bg-[#262626] text-white shadow-[0_4px_16px_rgba(0,0,0,0.25)] hover:bg-[#303030]"
      >
        <LibTvMark />
      </Link>
      <div className="flex h-8 items-center gap-1 border-l border-white/10 pl-1">
        <Link
          href="/project"
          data-clone-site-nav-link="liblib-projects"
          title="全部项目（LibTV 项目列表）"
          className={CHIP}
        >
          全部项目
        </Link>
        <Link
          href="/jimeng/canvas/demo"
          data-clone-site-nav-link="jimeng-canvas"
          title="进入即梦 AI 画布（本站另一个克隆成果）"
          className={CHIP}
        >
          即梦画布
        </Link>
        <Link
          href="/clones"
          data-clone-site-nav-link="clone-index"
          title="克隆总览：所有已完成克隆页 ＋ 怎么走 ＋ 怎么交互测试"
          className={CHIP}
        >
          克隆总览
        </Link>
      </div>
    </div>
  );
}
