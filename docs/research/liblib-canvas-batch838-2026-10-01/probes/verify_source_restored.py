#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 838：★ **跨刷新复验**源站场景树（独立进程）。

★ 为什么独立进程：Playwright 的**同步 API 不能嵌套** `sync_playwright()`
  （v13/v15 都撞了 `You are using Playwright Sync API inside the asyncio loop`）⟹
  ⟹ 跨刷新那趟用**独立脚本 ＋ 独立进程**跑。

★ 口径与主探针一致：**class 同时含 `pl-1` 与 `z-10`** 的才是场景树对象行
  （★ 不用几何 ⟹ 浮层面板行不会混进来）。
"""
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

DUMP_TREE_OBJ = """() => {
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0 && getComputedStyle(e).visibility!=='hidden';};
  const out=[]; const seen=new Set();
  for (const el of Array.from(document.querySelectorAll('span,div,button,a,p,li'))) {
    if (!vis(el) || el.childElementCount>0) continue;
    const cls=(el.className||'').toString();
    if (cls.indexOf('pl-1')<0 || cls.indexOf('z-10')<0) continue;
    const r=el.getBoundingClientRect();
    const t=(el.textContent||'').trim();
    if (!t || t.length>30) continue;
    const key=Math.round(r.y)+'|'+t;
    if (seen.has(key)) continue; seen.add(key);
    out.push({text:t, x:Math.round(r.x), y:Math.round(r.y),
              w:Math.round(r.width), h:Math.round(r.height)});
  }
  return out.sort((a,b)=> (a.y-b.y) || (a.x-b.x));
}"""


def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        ctx = br.new_context(viewport={"width": 1920, "height": 1080}, locale="zh-CN")
        ctx.add_cookies([{"name": c["name"], "value": c["value"],
                          "domain": c["domain"], "path": c.get("path", "/"),
                          "expires": c.get("expires", -1),
                          "httpOnly": c.get("httpOnly", False),
                          "secure": c.get("secure", False),
                          "sameSite": c.get("sameSite", "Lax")} for c in cookies])
        page = ctx.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
        page.wait_for_timeout(12_000)
        card = page.locator(".react-flow__node-director-console-3d").first
        card.hover()
        page.wait_for_timeout(800)
        page.locator(
            ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
        page.wait_for_timeout(9_000)
        page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
        rows = page.evaluate(DUMP_TREE_OBJ)
        names = []
        for r in rows:
            if r["text"] not in names:
                names.append(r["text"])
        out = {
            "行名": names,
            "行数": len(rows),
            "行详情": rows,
            "还剩新建的": [t for t in names if t not in ("机位1", "机位2", "角色A")],
            "★口径": "class 同时含 pl-1 与 z-10 ⟹ 场景树对象行（不用几何）",
        }
        out["是否已复原"] = (not out["还剩新建的"]
                             and "角色A" in names
                             and "机位1" in names)
        try:
            page.screenshot(path="/tmp/liblib_source_restored.png")
        except Exception:
            pass
        br.close()
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
