#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 832：**批量删掉**源站测试项目里被误建的机位（机位2..机位31）。

★ 为什么要这个脚本：batch 832 的语义探针（`presets832.py`）逐枚点了 15 个预设，
  源站**每点一枚就新建一台机位** ⟹ 累计建了 30 台（机位2..机位31）
  ⟹ 而那个探针里的 `delete_camera()` **一次都没生效**（右键菜单的选择器不对）
  ⟹ ★ 所以源站项目被弄脏了 ⟹ 必须复原。

★ ★ 删法（要可靠，不靠猜）：
  1. 打开导演台；
  2. 在**场景树**里逐个找到「机位N」（N ≥ 2）；
  3. 右键 → 找「删除」；
  4. ★ 如果右键菜单里**没有**「删除」，就**先打开机位的属性面板**
     （右栏有「删除」按钮）⟹ 逐条验证哪条路真的能删。

★ ★ 复原判据（必须证明）：删完后场景树里**只剩机位1**，
  且**用全新浏览器 context 复验**一遍。
"""
import json
import pathlib
import re
import sys
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_restore832b.json")
SHOTS = pathlib.Path("/tmp/liblib_source_restore832b")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

CAM_RE = re.compile(r"^机位\s*(\d+)$")


def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(800)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(9_000)


def tree_cameras(page):
    return page.evaluate(
        """()=>{
      const vis=(e)=>{const r=e.getBoundingClientRect();
        return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
      return [...new Set(Array.from(document.querySelectorAll('span')).filter(vis)
        .map(s=>(s.textContent||'').trim())
        .filter(t=>/^机位\\s*\\d+$/.test(t)))].sort();
    }""")


def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    out = {}
    try:
        run(out, cookies)
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        for k, v in out.items():
            if k.startswith(("①", "②", "③", "④", "异常")):
                print(" ", k, "→", v)


def run(out, cookies):
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                             locale="zh-CN")
        ctx.add_cookies([{"name": c["name"], "value": c["value"],
                          "domain": c["domain"], "path": c.get("path", "/"),
                          "expires": c.get("expires", -1),
                          "httpOnly": c.get("httpOnly", False),
                          "secure": c.get("secure", False),
                          "sameSite": c.get("sameSite", "Lax")} for c in cookies])
        page = ctx.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
        page.wait_for_timeout(12_000)
        open_desk(page)
        SHOTS.mkdir(exist_ok=True)
        try:
            out["①删前"] = tree_cameras(page)
            out["②删前数量"] = len(out["①删前"])
            page.screenshot(path=str(SHOTS / "before.png"))

            # ── 先探一次右键菜单到底有什么（不猜）
            cams = out["①删前"]
            target = None
            for c in cams:
                m = CAM_RE.match(c)
                if m and int(m.group(1)) >= 2:
                    target = c
                    break
            if target is None:
                out["③无需删"] = "只有机位1"
            else:
                item = page.get_by_text(target, exact=True).first
                item.click()
                page.wait_for_timeout(900)
                item.click(button="right")
                page.wait_for_timeout(1_500)
                out["③右键菜单项"] = page.evaluate(
                    "()=>Array.from(document.querySelectorAll('[role=menuitem]'))"
                    ".map(e=>(e.textContent||'').trim())")
                out["③b所有可见短文本"] = page.evaluate(
                    "()=>Array.from(document.querySelectorAll('button,li,[role=menuitem]'))"
                    ".filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0;})"
                    ".map(e=>(e.textContent||'').trim()).filter(t=>t&&t.length<10)")
                page.screenshot(path=str(SHOTS / "menu.png"))
        except Exception:
            out["异常"] = traceback.format_exc()[-1800:]
        try:
            page.locator("[aria-label='关闭']:visible").first.click()
            page.wait_for_timeout(2_500)
        except Exception:
            pass
        ctx.close()
        br.close()


if __name__ == "__main__":
    main()
