#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 832：**批量删掉**源站测试项目里被误建的机位（机位2..机位31）。

★ 为什么要这个脚本：batch 832 的语义探针（`presets832.py`）逐枚点了 15 个预设，
  源站**每点一枚就新建一台机位** ⟹ 累计建了 30 台（机位2..机位31），
  而那个探针里的 `delete_camera()` **一次都没生效**
  ⟹ ★ 所以源站项目被弄脏了 ⟹ 必须复原。

★ ★ 上一版（restore832b.py）只**探查**了右键菜单，确认它**确实有**「删除」：
     `['打组', '显示/隐藏', '锁定/解锁', '创建副本', '删除']`
  ⟹ 之前的失败原因是 `get_by_text("删除", exact=True)` 匹配到了**别的**元素
  ⟹ 本版改用 `[role="menuitem"]` **精确**点。

★ ★ 复原判据（必须证明，不能假设）：
  ① 删完后场景树里**只剩机位1**；
  ② **用全新浏览器 context 复验**一遍（不是同一个页面里看）。
"""
import json
import pathlib
import re
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_restore832c.json")
SHOTS = pathlib.Path("/tmp/liblib_source_restore832c")
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
        .filter(t=>/^机位\\s*\\d+$/.test(t)))];
    }""")


def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    out = {}
    try:
        run(out, cookies)
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        for k in ("①删前数量", "②删除次数", "③删后", "④全新context复验", "异常"):
            if k in out:
                print(" ", k, "→", out[k])


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
            out["①删前数量"] = len(out["①删前"])
            page.screenshot(path=str(SHOTS / "before.png"))

            deleted = 0
            # ★ 循环删：每次删掉**编号最大**的那台（最稳：编号唯一、位置稳定）
            for _ in range(60):
                cams = tree_cameras(page)
                victims = [c for c in cams
                           if (m := CAM_RE.match(c)) and int(m.group(1)) >= 2]
                if not victims:
                    break
                victim = max(victims, key=lambda c: int(CAM_RE.match(c).group(1)))
                item = page.get_by_text(victim, exact=True).first
                item.click()
                page.wait_for_timeout(600)
                item.click(button="right")
                page.wait_for_timeout(1_200)
                del_item = page.locator("[role='menuitem']").filter(
                    has_text="删除").first
                if not del_item.count():
                    out["异常"] = "右键菜单里没有 menuitem『删除』"
                    page.screenshot(path=str(SHOTS / "no_delete.png"))
                    break
                del_item.click()
                page.wait_for_timeout(1_400)
                # 可能有确认弹层
                for label in ("确认删除", "确定", "确认"):
                    try:
                        b = page.get_by_role("button", name=label, exact=True)
                        if b.count() and b.first.is_visible():
                            b.first.click()
                            page.wait_for_timeout(1_000)
                            break
                    except Exception:
                        pass
                page.wait_for_timeout(700)
                deleted += 1
            out["②删除次数"] = deleted
            out["③删后"] = tree_cameras(page)
            page.screenshot(path=str(SHOTS / "after.png"))
        except Exception:
            out["异常"] = traceback.format_exc()[-1800:]
        try:
            page.locator("[aria-label='关闭']:visible").first.click()
            page.wait_for_timeout(2_500)
        except Exception:
            pass
        ctx.close()
        br.close()

        # ★ 全新 context 复验
        try:
            ctx2 = br.new_context(viewport={"width": 1920, "height": 1080},
                                  locale="zh-CN")
            ctx2.add_cookies([{"name": c["name"], "value": c["value"],
                               "domain": c["domain"], "path": c.get("path", "/"),
                               "expires": c.get("expires", -1),
                               "httpOnly": c.get("httpOnly", False),
                               "secure": c.get("secure", False),
                               "sameSite": c.get("sameSite", "Lax")} for c in cookies])
            p2 = ctx2.new_page()
            p2.goto(URL, wait_until="domcontentloaded", timeout=90_000)
            p2.wait_for_timeout(12_000)
            open_desk(p2)
            out["④全新context复验"] = tree_cameras(p2)
            ctx2.close()
        except Exception:
            out["复验异常"] = traceback.format_exc()[-1200:]
        br.close()


if __name__ == "__main__":
    main()
