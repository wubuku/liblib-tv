#!/usr/bin/env python3
"""打开 FrameOS 登录用有头浏览器（独立 profile + 独立 CDP 端口）。

为什么独立 profile/端口：:9222 上已有别人（或用户自己）开的浏览器持有
liblib.tv 登录态，且 Chrome 会**锁定** profile 目录 —— 复用会导致启动失败
或互相踢掉会话。因此这里用：

  profile : ~/frameos-login-profile   （新建，与 libtv-cdp-profile 隔离）
  CDP 端口: 9333                      （与 9222 隔离）

登录完成后，本脚本会自动检测是否已进入画布路由并打印 READY。
用户随后可以关掉窗口；探针会通过 CDP 复用已保存的登录态（cookie 落盘在
上面那个 profile 目录内）。

Run: ~/.venvs/liblib-harness/bin/python scripts/open-frameos-login-browser.py
"""

import sys
import time

from playwright.sync_api import sync_playwright

PROFILE = "/Users/yangjiefeng/frameos-login-profile"
CDP_PORT = 9333
CANVAS_URL = (
    "https://www.frameos.cn/#/canvas/01KT17B610DG417X8Q76QZSN8Z/"
    "01KWS3TK5BTEH7680N4W9JW4KW"
)
# 登录后应落到的路由特征（画布而非 /login）
LOGGED_IN_MARKERS = ("react-flow__node", "canvas-node", "react-flow")


def main() -> int:
    with sync_playwright() as p:
        print(f"launching headed chromium profile={PROFILE} cdp={CDP_PORT}", flush=True)
        ctx = p.chromium.launch_persistent_context(
            PROFILE,
            headless=False,
            viewport={"width": 1920, "height": 1150},
            args=[
                f"--remote-debugging-port={CDP_PORT}",
                "--no-first-run",
                "--no-default-browser-check",
                "--start-maximized",
            ],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(CANVAS_URL, wait_until="domcontentloaded", timeout=90000)
        print(f"opened: {page.url}", flush=True)
        print("请在弹出的浏览器窗口中完成 frameos.cn 登录。", flush=True)

        # 最多等待 60 分钟；一旦检测到画布就绪即报 READY
        deadline = time.time() + 3600
        ready = False
        while time.time() < deadline:
            if page.is_closed():
                break
            try:
                url = page.url
                if "/login" not in url:
                    found = page.evaluate(
                        """(markers) => markers.some((m) => document.querySelector('.' + m)
                            || document.querySelector('.' + m + '-container'))""",
                        list(LOGGED_IN_MARKERS),
                    )
                    if found:
                        ready = True
                        print(f"READY: logged in, canvas mounted at {url}", flush=True)
                        print(
                            f"CDP available on http://localhost:{CDP_PORT} — "
                            "探针用 FRAMEOS_CDP_URL=http://localhost:9333 复用此登录态。",
                            flush=True,
                        )
                        break
            except Exception:  # noqa: BLE001 - 导航中/重定向中属正常
                pass
            page.wait_for_timeout(2000)

        if not ready and not page.is_closed():
            print("TIMEOUT: 60 分钟内未检测到画布挂载，窗口保持打开供手动操作。", flush=True)
        # 不主动关闭：用户可能还在操作。Ctrl-C 结束本脚本即可。
        while not page.is_closed():
            page.wait_for_timeout(5000)
    return 0


if __name__ == "__main__":
    sys.exit(main())
