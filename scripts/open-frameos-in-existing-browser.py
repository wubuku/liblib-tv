#!/usr/bin/env python3
"""在已存在的 :9222 浏览器里打开 FrameOS 画布标签页，交给用户手动登录。

背景：frameos.cn 对**自动化启动**的浏览器（新建 profile）弹出「确定你不是机器人」
人机验证，即使用户手动点击也判失败 —— 校验与浏览器指纹绑定，不尝试绕过。

因此改为复用项目**既有的** :9222 会话（profile=libtv-cdp-profile，已持有
liblib.tv 登录态，属已授权的源站取证通道）。本脚本只做三件事：
连接 → 开新标签 → 置前，然后**原地等待**，不导航、不点击、不读取 cookie。

登录完成后由采样脚本通过 CDP 复用该标签页。

Run: ~/.venvs/liblib-harness/bin/python scripts/open-frameos-in-existing-browser.py
"""

import sys
import time

from playwright.sync_api import sync_playwright

CANVAS_URL = (
    "https://www.frameos.cn/#/canvas/01KT17B610DG417X8Q76QZSN8Z/"
    "01KWS3TK5BTEH7680N4W9JW4KW"
)


def main() -> int:
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222", timeout=15000)
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR: cannot attach to :9222 ({exc})")
            print("请确认已有浏览器在运行（带 --remote-debugging-port=9222）。")
            return 1

        ctx = browser.contexts[0]
        page = ctx.new_page()
        page.goto(CANVAS_URL, wait_until="domcontentloaded", timeout=90000)
        page.bring_to_front()
        print(f"opened tab: {page.url}", flush=True)
        print("已将该标签页置前。请在浏览器窗口中手动完成登录/人机验证。", flush=True)
        print("本脚本不点击、不读取 cookie；登录完成后请回复我。", flush=True)

        # 原地等待登录完成（最多 30 分钟），检测到画布挂载即报告
        deadline = time.time() + 1800
        while time.time() < deadline:
            if page.is_closed():
                print("tab closed by user")
                return 0
            try:
                if "/login" not in page.url:
                    mounted = page.evaluate(
                        """() => !!document.querySelector('.react-flow__node')
                            || !!document.querySelector('[class*=react-flow]')"""
                    )
                    if mounted:
                        print(f"READY: canvas mounted at {page.url}", flush=True)
                        print("可关闭本脚本（Ctrl-C）；登录态已存入 :9222 profile。", flush=True)
                        while not page.is_closed():
                            page.wait_for_timeout(5000)
                        return 0
            except Exception:  # noqa: BLE001
                pass
            page.wait_for_timeout(3000)

        print("TIMEOUT: 30 分钟内未检测到画布挂载。", flush=True)
        return 0


if __name__ == "__main__":
    sys.exit(main())
