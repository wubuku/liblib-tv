#!/usr/bin/env python3
"""唤起一个**独立的有头 Google Chrome**，等用户登录即梦，检测到登录成功后自动捕获登录态。

为什么要"独立"：本机已有多处 Chrome 常驻（9222、9444 上都有别人的/自己的会话）。
复用会撞 profile 锁，甚至互相踢掉登录态。这里用完全隔离的三件套：

    profile : ~/.jimeng-automation/profile   （全新，专属本流程）
    端口    : 9555                            （与 9222/9444 隔离）
    引擎    : 真实 Google Chrome (channel=chrome)

流程：启动 → 打开即梦 → 轮询登录态（默认最长 60 分钟）→ 捕获 storageState
（含 IndexedDB）→ 立即用无头 Chrome 验证这份登录态真的可用 → 保持窗口打开，
用户可继续手动操作，随时 Ctrl-C 或关窗结束。

Run:
    ~/.venvs/liblib-harness/bin/python scripts/jimeng_login_capture.py
    ~/.venvs/liblib-harness/bin/python scripts/jimeng_login_capture.py --url <画布地址>
    ~/.venvs/liblib-harness/bin/python scripts/jimeng_login_capture.py --exit-after 20
"""

from __future__ import annotations

import argparse
import sys
import time

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))

import jimeng_auth as auth  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="有头 Chrome 登录即梦并捕获登录态")
    ap.add_argument("--url", default=auth.DEFAULT_URL, help="登录后要停留的即梦页面")
    ap.add_argument("--wait-minutes", type=float, default=60.0, help="等待登录的最长分钟数")
    ap.add_argument(
        "--exit-after", type=float, default=0.0,
        help="捕获成功后多少秒自动关闭窗口；0 = 一直开着等用户自己关",
    )
    ap.add_argument(
        "--force", action="store_true",
        help="即使未检测到强 session cookie，也按当前状态尝试捕获（应对判据失效）",
    )
    ap.add_argument(
        "--attach-cdp", default=None, metavar="URL",
        help="不新开浏览器，改为 attach 到已在运行的调试端口（如 http://127.0.0.1:9555）",
    )
    args = ap.parse_args()

    auth.ensure_home()

    with sync_playwright() as p:
        if args.attach_cdp:
            browser = p.chromium.connect_over_cdp(args.attach_cdp)
            ctx = browser.contexts[0] if browser.contexts else browser.new_context()
            print(f"attached: {args.attach_cdp}  pages={len(ctx.pages)}", flush=True)
        else:
            print(
                f"launching headed Chrome  profile={auth.PROFILE}  cdp={auth.CDP_PORT}",
                flush=True,
            )
            ctx = p.chromium.launch_persistent_context(
                str(auth.PROFILE),
                channel="chrome",
                headless=False,
                viewport=auth.CONTEXT_OPTIONS["viewport"],
                locale=auth.CONTEXT_OPTIONS["locale"],
                timezone_id=auth.CONTEXT_OPTIONS["timezone_id"],
                args=auth.LAUNCH_ARGS,
            )
        page = auth.pick_jimeng_page(ctx)
        if page is None:
            page = ctx.new_page()
        if not args.attach_cdp:
            try:
                page.goto(args.url, wait_until="domcontentloaded", timeout=90_000)
            except Exception as e:  # noqa: BLE001 - 首屏可能慢/被重定向，不致命
                print(f"  goto warning: {str(e)[:140]}", flush=True)

        print("", flush=True)
        if args.attach_cdp:
            print(f"┌─ 已 attach 到 {args.attach_cdp}，直接监控该窗口当前登录态", flush=True)
        else:
            print("┌─ 请在弹出的 Chrome 窗口里完成即梦登录（扫码/短信均可）", flush=True)
            print("│  检测到登录成功后本脚本会自动捕获并验证，无需你再操作", flush=True)
        print(f"└─ 等待中，最长 {args.wait_minutes:.0f} 分钟。窗口请勿关闭。", flush=True)
        print("", flush=True)

        deadline = time.time() + args.wait_minutes * 60
        state = None
        detected_at = None
        last_report = 0.0

        while time.time() < deadline and not ctx.pages[0].is_closed():
            try:
                probe = auth.login_probe(ctx)
            except Exception:  # noqa: BLE001 - 导航竞态
                time.sleep(2)
                continue

            if not detected_at and (probe["logged_in"] or args.force):
                detected_at = time.time()
                acct = probe.get("account") or {}
                print("", flush=True)
                print("=" * 68, flush=True)
                print(f"LOGIN DETECTED  url={probe['url']}  title={probe['title']}", flush=True)
                print(
                    f"  passport account : user_id={acct.get('user_id')} "
                    f"error_code={acct.get('error_code')} nickname={acct.get('nickname') or '-'}",
                    flush=True,
                )
                print(f"  strong cookies   : {', '.join(probe['strong_cookies']) or '(none)'}", flush=True)
                print(f"  login wall       : {', '.join(probe['login_wall']) or '(none)'}", flush=True)
                if not probe["logged_in"]:
                    print("  (!) 由 --force 触发，判据未确证，请自行核对下面的无头验证结果", flush=True)
                print("=" * 68, flush=True)

                try:
                    state = auth.capture_state(ctx)
                except Exception as e:  # noqa: BLE001
                    print(f"CAPTURE FAILED: {str(e)[:200]}", flush=True)
                    continue
                print(f"\nSTATE SAVED -> {auth.STATE}  (chmod 600)\n", flush=True)
                print(auth.summarize_state(state), flush=True)

                # 关键一步：立刻用无头 Chrome 验证这份登录态真的可用，
                # 免得用户回来后才发现会话根本带不过去。
                print("\nverifying with a fresh headless Chrome ...", flush=True)
                try:
                    b2, c2, pg2 = auth.open_headless(p, auth.STATE, headless=True)
                    v = auth.verify_login(c2, pg2)
                    va = v.get("account") or {}
                    print(f"  headless logged_in : {v['logged_in']}", flush=True)
                    print(f"  headless url       : {v['url']}", flush=True)
                    print(
                        f"  passport user_id   : {va.get('user_id')} "
                        f"error_code={va.get('error_code')} nickname={va.get('nickname') or '-'}",
                        flush=True,
                    )
                    if v["logged_in"]:
                        print("\n  ✅ 登录态已可用于后台无头任务。", flush=True)
                    else:
                        print(
                            f"\n  ❌ 无头侧未通过验证：{v.get('reason') or '未知原因'}\n"
                            "     这份 state.json 不可用于后台任务，登录完整后重跑本脚本。",
                            flush=True,
                        )
                    b2.close()
                except Exception as e:  # noqa: BLE001
                    print(f"  verification error: {str(e)[:200]}", flush=True)

                print(
                    f"\n无头任务入口：~/.venvs/liblib-harness/bin/python "
                    f"scripts/jimeng_headless.py probe",
                    flush=True,
                )
                if args.exit_after > 0:
                    print(f"将在 {args.exit_after:.0f}s 后自动关闭本窗口。", flush=True)
                else:
                    print("登录窗口保持打开，可继续手动操作；关闭窗口或 Ctrl-C 结束本脚本。", flush=True)

            # 尚未登录时每 15s 打一行心跳，避免用户以为脚本卡死
            if not detected_at and time.time() - last_report > 15:
                last_report = time.time()
                print(
                    f"  waiting… url={probe['url']} wall={probe['login_wall'] or 'none'}",
                    flush=True,
                )

            if detected_at and args.exit_after > 0 and time.time() - detected_at > args.exit_after:
                print("closing browser (--exit-after reached)", flush=True)
                if not args.attach_cdp:   # attach 模式绝不关用户的窗口
                    ctx.close()
                return 0 if state else 1

            time.sleep(2)

        if not detected_at:
            print(f"\nTIMEOUT: {args.wait_minutes:.0f} 分钟内未检测到登录成功。", flush=True)
        if args.attach_cdp:
            return 0 if state else 1
        # 不主动关窗：用户可能正在操作。关窗或 Ctrl-C 结束。
        while ctx.pages and not ctx.pages[0].is_closed():
            time.sleep(3)
    return 0 if state else 1


if __name__ == "__main__":
    sys.exit(main())
