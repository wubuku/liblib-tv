#!/usr/bin/env python3
"""Jimeng clone batch 820 verifier — 账号菜单另外 4 项此前是真死按钮。

起因：复刻 `JimengHelpMenu` 的 onClick 写的是
    onClick={() => { if (label === "快捷键") onOpenShortcuts?.(); onClose(); }}
**每个按钮都带 onClick**，所以"有没有 handler"这种存在性检查数不出问题。
（`jimeng_dead_button_audit.py` 确实是按点击前后状态比对判定的，漏掉它们的真正
原因是**账号菜单这个浮层压根没被列入普查状态**。）

源站逐项实测（README §27），本批接上：
    帮助中心        → 右侧浮层 360×648 @[1304,60]
    使用手册        → 新标签页 …/wiki/X1elw8hpMiqWdLki3Mlc9WWznhd
    AI生成水印设置 → 全屏遮罩 + 居中 616×492 弹窗，24×24 水印开关 + 84×36 保存钮
    即梦CLI         → 新标签页 …/ai-tool/install?from_page=new_canvas

判据纪律：断言**点击后的状态变化**（新浮层出现 / 新标签页 URL 正确），
不是"元素有 onClick"。
"""

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = os.environ.get("JIMENG_CLONE_URL", "http://localhost:4317")
URL = f"{BASE}/jimeng/canvas/demo"
STATE = Path.home() / ".jimeng-automation" / "state.json"

MANUAL_URL = "https://bytedance.larkoffice.com/wiki/X1elw8hpMiqWdLki3Mlc9WWznhd"
CLI_URL = "https://jimeng.jianying.com/ai-tool/install?from_page=new_canvas"

failures: list[str] = []
checks = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global checks
    checks += 1
    if ok:
        print(f"  PASS  {name}" + (f"  ({detail})" if detail else ""))
    else:
        print(f"  FAIL  {name}  {detail}")
        failures.append(name)


def open_menu(page) -> None:
    page.locator('button[aria-label="用户菜单"]').click()
    page.wait_for_timeout(600)


def close_all(page) -> None:
    for _ in range(3):
        if page.locator('[data-dialog-overlay="true"]').count():
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
        else:
            break
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)


def click_item(page, label: str) -> None:
    open_menu(page)
    page.locator(f'[data-testid="account-menu-item-{label}"]').click()
    page.wait_for_timeout(900)


def main() -> int:
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(storage_state=str(STATE) if STATE.exists() else None,
                            viewport={"width": 1680, "height": 1050})
        page = ctx.new_page()
        errs: list[str] = []
        page.on("pageerror", lambda e: errs.append(str(e)[:160]))
        popups: list[str] = []
        ctx.on("page", lambda np: popups.append(np.url))
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)

        # 判据改为"产品调用了 window.open 且 URL 正确"，而不是"真的打开了新标签页"。
        # 踩坑：使用手册指向 bytedance.larkoffice.com，沙箱里这个域名不通，
        # 真实导航压根不发生 → 断言恒失败。而同机制的即梦CLI（同域）却能过，
        # 差点被误判成"使用手册这项没接上"。外链能不能打开是网络的事，
        # 不是产品行为。
        page.evaluate("""() => {
            window.__opened = [];
            const orig = window.open;
            window.open = function (url, ...rest) {
                window.__opened.push(String(url));
                return null;   // 不真开，避免依赖外网
            };
            window.__origOpen = orig;
        }""")

        # ── 0. 菜单结构 ──────────────────────────────────────────────
        open_menu(page)
        items = page.evaluate(
            """() => [...document.querySelectorAll('[role="menuitem"]')]
                .map(e => e.getAttribute('aria-label') ||
                          (e.getAttribute('data-testid')||'').replace('account-menu-item-',''))"""
        )
        check("0.1 账号菜单 5 项齐全",
              len(items) == 5, str(items))

        # ── 1. 帮助中心：右侧浮层 360×648 ────────────────────────────
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
        click_item(page, "帮助中心")
        hc = page.locator('[data-testid="account-help-center"]')
        check("1.1 帮助中心打开右侧浮层", hc.count() == 1)
        if hc.count():
            bb = hc.bounding_box()
            # 源站 360×648 @[1304,60]；浮层在 fixed 定位下不受画布缩放影响，
            # 这里可以写死绝对值（与 817 的画布内元素不同）
            check("1.2 浮层几何 360×648（源站实测）",
                  bb and abs(bb["width"] - 360) <= 1 and abs(bb["height"] - 648) <= 1,
                  f"{bb['width']:.0f}×{bb['height']:.0f}" if bb else "无")
            check("1.3 浮层右缘贴 12px、上缘 60px（源站 @[1304,60]，视口 1680）",
                  bb and abs(bb["x"] - (1680 - 12 - 360)) <= 2 and abs(bb["y"] - 60) <= 2,
                  f"x={bb['x']:.0f} y={bb['y']:.0f}" if bb else "无")
            check("1.4 可访问名是源站的 \"Help center\"",
                  hc.get_attribute("aria-label") == "Help center",
                  str(hc.get_attribute("aria-label")))
            check("1.5 正文标注 (mock)（源站该浮层实测加载失败，成功态无证据）",
                  "mock" in (hc.inner_text() or ""))
        close_all(page)

        # ── 2. 使用手册：外链 ────────────────────────────────────────
        page.evaluate("() => { window.__opened = []; }")
        click_item(page, "使用手册")
        page.wait_for_timeout(600)
        opened = page.evaluate("() => window.__opened")
        check("2.1 使用手册调用 window.open 且 URL 与源站逐字一致",
              any(MANUAL_URL in u for u in opened), str(opened))
        close_all(page)

        # ── 3. AI 生成水印设置：全屏遮罩 + 居中弹窗 ──────────────────
        click_item(page, "AI生成水印设置")
        dlg = page.locator('[data-testid="account-watermark-dialog"]')
        check("3.1 打开水印设置弹窗", dlg.count() == 1)
        check("3.2 带全屏遮罩（源站 data-dialog-overlay 0→1）",
              page.locator('[data-dialog-overlay="true"]').count() == 1)
        if dlg.count():
            bb = dlg.bounding_box()
            check("3.3 弹窗 616×492 居中（源站实测 @[532,279]）",
                  bb and abs(bb["width"] - 616) <= 2 and abs(bb["height"] - 492) <= 2
                  and abs(bb["x"] - 532) <= 3 and abs(bb["y"] - 279) <= 3,
                  f"{bb['x']:.0f},{bb['y']:.0f} {bb['width']:.0f}×{bb['height']:.0f}" if bb else "无")
            txt = dlg.inner_text() or ""
            check("3.4 法条文案逐字取自源站（抽查开头与结尾）",
                  txt.startswith("AI生成水印设置")
                  and "根据法律法规要求，即梦AI平台" in txt
                  and "因此所发生的后果和责任均由您自行承担。" in txt,
                  txt[:50])
            tg = page.locator('[data-testid="watermark-toggle"]')
            check("3.5 水印开关 24×24（源站实测）",
                  tg.count() == 1 and abs(tg.bounding_box()["width"] - 24) <= 1,
                  str(tg.bounding_box()) if tg.count() else "无")
            # 开关真的改变状态
            before = tg.get_attribute("aria-checked")
            tg.click()
            page.wait_for_timeout(300)
            after = tg.get_attribute("aria-checked")
            check("3.6 开关真改变 aria-checked（不是摆设）", before != after,
                  f"{before} -> {after}")
            save = page.locator('[data-testid="watermark-save"]')
            sb = save.bounding_box()
            check("3.7 保存钮 84×36（源站实测）",
                  sb and abs(sb["width"] - 84) <= 1 and abs(sb["height"] - 36) <= 1,
                  f"{sb['width']:.0f}×{sb['height']:.0f}" if sb else "无")
            save.click()
            page.wait_for_timeout(400)
            check("3.8 点保存后有反馈（文案变化）",
                  (save.inner_text() or "") != "保存设置", save.inner_text())
        close_all(page)
        check("3.9 Escape 能关掉弹窗（不留遮罩）",
              page.locator('[data-testid="account-watermark-dialog"]').count() == 0
              and page.locator('[data-dialog-overlay="true"]').count() == 0)

        # ── 4. 即梦CLI：外链 ────────────────────────────────────────
        page.evaluate("() => { window.__opened = []; }")
        click_item(page, "即梦CLI")
        page.wait_for_timeout(600)
        opened = page.evaluate("() => window.__opened")
        check("4.1 即梦CLI 调用 window.open 且 URL 与源站逐字一致",
              any(CLI_URL in u for u in opened), str(opened))
        close_all(page)

        # ── 5. 回归：快捷键仍正常 ────────────────────────────────────
        click_item(page, "快捷键")
        check("5.1 快捷键面板仍能打开（未被本批改坏）",
              page.locator('div[aria-label="快捷键"]').count() == 1)
        close_all(page)

        check("6.0 无页面 JS 报错", not errs, "; ".join(errs[:2]))
        ctx.close()
        b.close()

    print(f"\n{checks - len(failures)}/{checks}")
    if failures:
        print("FAILED: " + ", ".join(failures))
        return 1
    print("batch 820 OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
