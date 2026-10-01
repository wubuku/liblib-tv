#!/usr/bin/env python3
"""即梦后台无头任务运行器：复用 scripts/jimeng_login_capture.py 捕获的登录态。

每次调用都是**全新**的无头 Chrome + 独立 context，跑完即退，不留进程、不动有头
profile。这样可以放心地反复执行、和用户的有头窗口并行。

计费边界：与 scripts/jimeng-explore.mjs 一致，`click` 默认硬拦截会**消耗积分**的
关键词（生成/发送/局部重拍/…）。确实要花积分时显式加 --allow-billed。

常用：
    python scripts/jimeng_headless.py probe                 # 登录态 + 账户概况
    python scripts/jimeng_headless.py open <url> --shot a.png
    python scripts/jimeng_headless.py text                  # 当前页可见文本
    python scripts/jimeng_headless.py click "AI画布"          # （护栏内）点击
    python scripts/jimeng_headless.py fill "#kw" "一只猫" --press Enter
    python scripts/jimeng_headless.py run scripts/my_task.py # 复杂任务写脚本
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import jimeng_auth as auth  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

# 页面可读性工具：把 innerText 里的连续空白压掉，方便人读与后续 grep
_SQUEEZE = re.compile(r"[ \t]+")


def dump_page(page, max_chars: int = 4000) -> str:
    try:
        text = page.evaluate("() => document.body ? document.body.innerText : ''")
    except Exception as e:  # noqa: BLE001
        return f"<read failed: {str(e)[:120]}>"
    text = _SQUEEZE.sub(" ", text.replace("\r", ""))
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text[:max_chars]


def cmd_probe(page, ctx, args) -> int:
    v = auth.verify_login(ctx, page, args.url)
    print("== 登录态 ==")
    print(f"  logged_in    : {v['logged_in']}")
    print(f"  url          : {v['url']}")
    print(f"  title        : {v['title']}")
    print(f"  strong cookie: {', '.join(v['strong_cookies']) or '(none)'}")
    print(f"  login wall   : {', '.join(v['login_wall']) or '(none)'}")

    if not v["logged_in"]:
        print("\n登录态无效：请重跑 scripts/jimeng_login_capture.py。", file=sys.stderr)
        return 2

    info = page.evaluate(
        """() => {
      const txt = (el) => (el?.textContent || '').trim();
      const all = Array.from(document.querySelectorAll('button,a,[role="button"]'));
      const labels = all.map(txt).filter((t) => t && t.length < 30);
      const links = Array.from(document.querySelectorAll('a[href]'))
        .map((a) => ({ href: a.getAttribute('href'), text: txt(a).slice(0, 24) }))
        .filter((x) => x.href && x.text)
        .slice(0, 40);
      const m = document.body.innerText.match(/(\\d[\\d,.]*)\\s*(积分|条|张|次)/);
      return {
        buttons: Array.from(new Set(labels)).slice(0, 60),
        links: Array.from(new Map(links.map((l) => [l.href, l])).values()).slice(0, 40),
        creditHint: m ? m[0].replace(/\\s+/g, ' ') : null,
        dialogs: Array.from(document.querySelectorAll('[role="dialog"],.semi-modal-content'))
          .map((d) => txt(d).slice(0, 60)).filter(Boolean).slice(0, 10),
      };
    }"""
    )
    print("\n== 账户线索 ==")
    print(f"  积分文案线索 : {info['creditHint'] or '(未在首屏找到)'}")
    if info["dialogs"]:
        print(f"  弹窗         : {' | '.join(info['dialogs'])}")
    print("\n== 可见按钮（去重，前 60） ==")
    print("  " + " | ".join(info["buttons"]))
    print("\n== 链接（前 40） ==")
    for l in info["links"]:
        print(f"  {l['text']}  ->  {l['href']}")
    return 0


def cmd_open(page, ctx, args) -> int:
    page.goto(args.url, wait_until=args.wait_until, timeout=args.timeout)
    page.wait_for_timeout(args.settle)
    print(f"opened: {page.url}")
    print(f"title : {page.title()}")
    if args.shot:
        Path(args.shot).parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=args.shot, full_page=args.full)
        print(f"shot  : {args.shot}")
    if args.text:
        print("\n---- text ----")
        print(dump_page(page, args.max_chars))
    return 0


def cmd_text(page, ctx, args) -> int:
    if args.selector:
        el = page.query_selector(args.selector)
        if el is None:
            print(f"selector 未命中: {args.selector}", file=sys.stderr)
            return 1
        print(el.inner_text()[: args.max_chars])
    else:
        print(dump_page(page, args.max_chars))
    return 0


def cmd_dom(page, ctx, args) -> int:
    html = page.evaluate(
        "(sel) => (document.querySelector(sel)?.outerHTML || '<no match>').slice(0, 20000)",
        args.selector,
    )
    print(html)
    return 0


def cmd_shot(page, ctx, args) -> int:
    Path(args.path).parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=args.path, full_page=args.full)
    print(f"shot: {args.path}  url={page.url}")
    return 0


def cmd_click(page, ctx, args) -> int:
    """按可见文本点击。护栏只拦"计费"文本，不拦普通导航。"""
    target = page.get_by_text(args.text, exact=False).first
    label = target.inner_text()[:60]
    auth.assert_not_billed_action(label, allow_billed=args.allow_billed)
    target.click(timeout=args.timeout)
    page.wait_for_timeout(args.settle)
    print(f"clicked: {label.strip()!r} -> {page.url}")
    return 0


def cmd_fill(page, ctx, args) -> int:
    auth.assert_not_billed_action(args.text, allow_billed=args.allow_billed)
    page.fill(args.selector, args.text, timeout=args.timeout)
    print(f"filled {args.selector}")
    if args.press:
        page.keyboard.press(args.press)
        print(f"pressed {args.press}")
    page.wait_for_timeout(args.settle)
    return 0


def cmd_press(page, ctx, args) -> int:
    page.keyboard.press(args.key)
    page.wait_for_timeout(args.settle)
    print(f"pressed: {args.key} -> {page.url}")
    return 0


def cmd_wait(page, ctx, args) -> int:
    page.wait_for_timeout(args.ms)
    print(f"waited {args.ms}ms -> {page.url}")
    return 0


def cmd_run(page, ctx, args) -> int:
    """执行任意 python 任务脚本。可用全局变量：page / context / browser / args / auth。

    复杂任务（多步交互、轮询、抽取数据）写脚本比堆 CLI 子命令更好维护。
    """
    path = Path(args.path).resolve()
    if not path.exists():
        print(f"任务脚本不存在: {path}", file=sys.stderr)
        return 1
    ns = {
        "page": page, "context": ctx, "browser": page.context.browser,
        "args": args, "auth": auth, "__name__": "__main__", "__file__": str(path),
    }
    # 让任务脚本既能直接用注入的全局变量（page/context），也能 import 同目录模块
    # （`import jimeng_auth as auth`），不必关心自己被放在哪。
    scripts_dir = str(Path(__file__).resolve().parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    # 把透传参数还原成任务脚本视角的 argv，否则脚本里 sys.argv[1] 读到的是
    # "run" 而不是它自己的第一个参数。
    saved_argv = sys.argv
    sys.argv = [str(path)] + list(getattr(args, "extra", []) or [])
    try:
        exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), ns)  # noqa: S102
    finally:
        sys.argv = saved_argv
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="即梦后台无头任务运行器")
    ap.add_argument("--state", default=str(auth.STATE), help="登录态文件路径")
    ap.add_argument("--headed", action="store_true", help="调试用：无头改成有头")
    ap.add_argument("--allow-billed", action="store_true", help="放行计费类点击（会花积分）")
    ap.add_argument("--url", default=auth.DEFAULT_URL, help="启动后访问的页面")
    ap.add_argument("--settle", type=int, default=2000, help="交互后等待毫秒")
    ap.add_argument("--timeout", type=int, default=45_000)
    ap.add_argument("--keep-open", action="store_true", help="执行完不关浏览器")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("probe", help="登录态 + 账户概况")
    p.add_argument("--url", default=auth.DEFAULT_URL)
    p.add_argument("--max-chars", type=int, default=4000)
    p.set_defaults(fn=cmd_probe)

    p = sub.add_parser("open", help="打开 URL")
    p.add_argument("url")
    p.add_argument("--wait-until", default="domcontentloaded")
    p.add_argument("--text", action="store_true", help="顺便打印页面文本")
    p.add_argument("--shot", help="顺便截图到该路径")
    p.add_argument("--full", action="store_true", help="整页截图")
    p.add_argument("--max-chars", type=int, default=4000)
    p.set_defaults(fn=cmd_open)

    p = sub.add_parser("text", help="打印页面文本")
    p.add_argument("selector", nargs="?")
    p.add_argument("--max-chars", type=int, default=4000)
    p.set_defaults(fn=cmd_text)

    p = sub.add_parser("dom", help="打印某选择器的 outerHTML")
    p.add_argument("selector")
    p.set_defaults(fn=cmd_dom)

    p = sub.add_parser("shot", help="截图")
    p.add_argument("path")
    p.add_argument("--full", action="store_true")
    p.set_defaults(fn=cmd_shot)

    p = sub.add_parser("click", help="按文本点击（默认拦截计费动作）")
    p.add_argument("text")
    p.set_defaults(fn=cmd_click)

    p = sub.add_parser("fill", help="填输入框")
    p.add_argument("selector")
    p.add_argument("text")
    p.add_argument("--press", help="填完按某个键，如 Enter")
    p.set_defaults(fn=cmd_fill)

    p = sub.add_parser("press", help="按键")
    p.add_argument("key")
    p.set_defaults(fn=cmd_press)

    p = sub.add_parser("wait", help="等待毫秒")
    p.add_argument("ms", type=int)
    p.set_defaults(fn=cmd_wait)

    p = sub.add_parser("run", help="执行 python 任务脚本")
    p.add_argument("path")
    p.add_argument(
        "extra", nargs=argparse.REMAINDER,
        help="透传给任务脚本的位置参数（任务脚本从自己的 sys.argv[1:] 读）",
    )
    p.set_defaults(fn=cmd_run)

    args = ap.parse_args()

    rc = 1
    # 在启动 Playwright **之前**就检查登录态：既省掉一次浏览器冷启动，
    # 也避免在异常路径上拆连接时打出一堆无意义的 TargetClosedError 噪音。
    state_path = Path(args.state)
    if not state_path.exists():
        print(
            f"未找到登录态文件 {state_path}；"
            "请先运行 scripts/jimeng_login_capture.py 完成登录。",
            file=sys.stderr,
        )
        return 2

    with sync_playwright() as p:
        browser, ctx, page = auth.open_headless(p, state_path, headless=not args.headed)
        try:
            # probe 自己会做 verify_login + 必要的导航；其余命令先落到默认页，
            # 这样 click/fill/press 一上来就有内容可操作。
            start_url = getattr(args, "url", None)
            if args.cmd != "probe" and start_url:
                try:
                    page.goto(start_url, wait_until="domcontentloaded", timeout=args.timeout)
                except Exception as e:  # noqa: BLE001
                    print(f"startup goto warning: {str(e)[:120]}", file=sys.stderr)
            rc = args.fn(page, ctx, args)
        finally:
            if args.keep_open:
                print("\n--keep-open：浏览器保持打开，Ctrl-C 结束。", flush=True)
                try:
                    while not page.is_closed():
                        page.wait_for_timeout(1000)
                except KeyboardInterrupt:
                    pass
            browser.close()
    return rc


if __name__ == "__main__":
    sys.exit(main())
