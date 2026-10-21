#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 834 诊断二：源站的引导气泡**到底能不能被触发**。

★ 上一条诊断的发现：源站导演台**开台后时间轴是收起的** ⟹ 而引导气泡锚在时间轴上
  ⟹ 所以「没找到气泡」可能只是**它没机会出现**。
  ⟹ 而 batch 572 记的是「气泡收起状态**跨重载持久**（浏览器重启后仍收起）」
  ⟹ ★ 那可能是**服务端**的用户偏好 ⟹ 若是如此，这个测试帐号可能**再也看不到**它。

★ 本探针依次试四种触发方式，每种都记录「导演台里多了什么 / 少了什么」：
  ① 点 rail 的「动画时间轴」按钮（开时间轴）
  ② 点「帮助」⟹ 菜单是否真的打开（dump 菜单项）
  ③ 点「使用教程」⟹ 时间轴是否被打开、页面是否变化
  ④ 试「重新载入页面后再开台」（有些引导只在首屏挂载时出现）

★ 判据用**可见元素签名表**（元素标签 ＋ 类名 ＋ 盒）的集合差 ⟹
  「多出来的元素」就是引导相关的东西 ⟹ 不靠猜选择器。
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_diag834b.json")
SHOTS = pathlib.Path("/tmp/liblib_source_diag834b")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

SIGNATURE = """()=>{
  const out=new Set();
  for(const e of document.querySelectorAll('body *')){
    const r=e.getBoundingClientRect();
    if(r.width<=0||r.height<=0) continue;
    const cs=getComputedStyle(e);
    if(cs.display==='none'||cs.visibility==='hidden') continue;
    const key=[e.tagName, String(e.className||'').slice(0,60),
               Math.round(r.x), Math.round(r.y),
               Math.round(r.width), Math.round(r.height)].join('|');
    out.add(key);
  }
  return [...out];
}"""

TEXT_SNAP = """()=>{
  const t=[];
  for(const e of document.querySelectorAll('button,span,div,p')){
    const r=e.getBoundingClientRect();
    if(r.width<=0||r.height<=0) continue;
    if(e.childElementCount!==0) continue;
    const s=(e.textContent||'').trim();
    if(!s||s.length>24) continue;
    t.push(s+'@'+Math.round(r.x)+','+Math.round(r.y));
  }
  return t;
}"""


def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(800)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(9_000)


def diff(a, b):
    sa, sb = set(a), set(b)
    return {"新增": sorted(sb - sa)[:40], "消失": sorted(sa - sb)[:20]}


def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    out = {}
    SHOTS.mkdir(exist_ok=True)
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                             locale="zh-CN")
        ctx.add_cookies([{
            "name": c["name"], "value": c["value"], "domain": c["domain"],
            "path": c.get("path", "/"), "expires": c.get("expires", -1),
            "httpOnly": c.get("httpOnly", False),
            "secure": c.get("secure", False),
            "sameSite": c.get("sameSite", "Lax"),
        } for c in cookies])
        page = ctx.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
        page.wait_for_timeout(9_000)
        open_desk(page)

        sig0 = page.evaluate(SIGNATURE)
        txt0 = page.evaluate(TEXT_SNAP)
        out["⓪开台后"] = {"签名数": len(sig0)}

        # ① 开时间轴
        try:
            page.locator("button[aria-label='动画时间轴']").first.click()
            page.wait_for_timeout(2_500)
            sig1 = page.evaluate(SIGNATURE)
            out["①开时间轴"] = diff(sig0, sig1)
            out["①开时间轴·文本差"] = diff(txt0, page.evaluate(TEXT_SNAP))
            page.screenshot(path=str(SHOTS / "834b_timeline.png"))
        except Exception as exc:  # noqa: BLE001
            out["①开时间轴异常"] = repr(exc)[:200]

        # ② 帮助菜单
        try:
            page.locator("button[aria-label='帮助']").first.click()
            page.wait_for_timeout(1_200)
            out["②帮助菜单项"] = page.evaluate("""()=>{
              return Array.from(document.querySelectorAll('[role="menuitem"]'))
                .map(e=>{const r=e.getBoundingClientRect();
                  return {t:(e.textContent||'').trim(),
                          box:{x:Math.round(r.x),y:Math.round(r.y),
                               w:Math.round(r.width),h:Math.round(r.height)}};});
            }""")
            page.screenshot(path=str(SHOTS / "834b_helpmenu.png"))
        except Exception as exc:  # noqa: BLE001
            out["②帮助异常"] = repr(exc)[:200]

        # ③ 点「使用教程」
        try:
            sig2 = page.evaluate(SIGNATURE)
            page.locator("[role='menuitem']").filter(
                has_text="使用教程").first.click()
            page.wait_for_timeout(3_000)
            out["③点使用教程"] = diff(sig2, page.evaluate(SIGNATURE))
            out["③点使用教程·文本差"] = diff(txt2 if (txt2 := out.get("②文本")) else [],
                                            page.evaluate(TEXT_SNAP))
            page.screenshot(path=str(SHOTS / "834b_tutorial.png"))
        except Exception as exc:  # noqa: BLE001
            out["③点使用教程异常"] = repr(exc)[:200]

        ctx.close()
        br.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已落盘：", OUT)
    print(json.dumps(out, ensure_ascii=False, indent=1)[:3000])


if __name__ == "__main__":
    main()
