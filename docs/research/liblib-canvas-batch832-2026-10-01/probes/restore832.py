#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 832：把源站测试项目**复原**（删掉本批测出来的「机位2」）。

★ 为什么必须复原：batch 832 的语义探针（`camerasem832.py`）点了「正面中景」，
  源站**真的新建了一个机位**（机位2 / 位置 (0,1.5,4) / FOV 50 / 注视 (0,1.2,0)）
  ⟹ 这是**改了用户的项目**⟹ 必须删掉。

★ 删法：走源站自己的 UI（场景树条目的右键菜单 → 删除）⟹
  **不直接改接口**（免得留下不一致的状态）。

★ ★ 复原的判据（必须证明，不能假设）：
  ① 场景树里**不再有**「机位2」；
  ② 场景树里**仍只有**原来那一台机位（机位1）；
  ③ FOV 等原有属性读数与复原前一致（机位1 不受影响）。
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_restore832.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 场景树里的机位条目读数（按文本找，不依赖类名）
DUMP_TREE = """()=>{
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
  const names=Array.from(document.querySelectorAll('span'))
    .filter(vis).map(s=>(s.textContent||'').trim())
    .filter(t=>/^机位\\s*\\d+$/.test(t)||/^角色/.test(t));
  return {names:[...new Set(names)]};
}"""


def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(800)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(8_000)


def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    out = {}
    try:
        run(out, cookies)
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        print(json.dumps({k: v for k, v in out.items()
                          if k.startswith(("①", "②", "③", "异常"))},
                         ensure_ascii=False, indent=1))


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
        try:
            out["①复原前树"] = page.evaluate(DUMP_TREE)

            # ── 在场景树里找到「机位2」并右键 → 删除
            item = page.get_by_text("机位2", exact=True).first
            item.click()
            page.wait_for_timeout(1_200)
            item.click(button="right")
            page.wait_for_timeout(1_500)
            page.screenshot(path="/tmp/liblib_source_restore832_menu.png")
            # 右键菜单里找「删除」
            try:
                page.get_by_text("删除", exact=True).first.click()
            except Exception:
                out["右键菜单"] = page.evaluate(
                    "()=>Array.from(document.querySelectorAll('[role=menuitem],button'))"
                    ".map(e=>(e.textContent||'').trim()).filter(t=>t&&t.length<8).slice(0,30)")
                raise
            page.wait_for_timeout(1_500)
            # 可能有一个确认弹层
            for label in ("确认删除", "确定", "删除"):
                try:
                    b = page.get_by_role("button", name=label, exact=True)
                    if b.count() and b.first.is_visible():
                        b.first.click()
                        page.wait_for_timeout(1_200)
                        break
                except Exception:
                    pass
            page.wait_for_timeout(1_500)
            out["②复原后树"] = page.evaluate(DUMP_TREE)
            page.screenshot(path="/tmp/liblib_source_restore832_after.png")
        except Exception:
            out["异常"] = traceback.format_exc()[-1800:]
        try:
            page.locator("[aria-label='关闭']:visible").first.click()
            page.wait_for_timeout(3_000)
        except Exception:
            pass
        ctx.close()
        br.close()


if __name__ == "__main__":
    main()
