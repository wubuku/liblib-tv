#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 838 源站探针 v7：查源站**角色**的默认命名规则（★ 区分实验）。

★ 背景：源站场景树实测显示「机位1 / 机位2 / **角色A**」。
★ 要回答：「角色A」是**系统生成的默认名**（像「机位1」那样按序号），
  还是**用户自己起的名**？
⟹ ★ **区分实验**：在源站**新建一个角色** ⟹ 看它叫什么。
  - 叫「角色B」/「角色2」⟹ 源站按**字母序号**给默认名 ⟹ clone 的「角色01 · 陈默」应该改成序号式；
  - 叫别的（例如「角色 1」「新角色」）⟹ 仍是序号式，只是形式不同；
  - ★ 若**根本不能新建角色** ⟹ 判「实验无效」，不���结论。

★ 纪律：
  - **新建的角色必须复原**（删掉）⟹ 且**用无正则口径复验**删后数量；
  - 「角色A」这条读数要分清楚：它是**场景树里的一行**，不是**某个面板的标题**；
  - 先记**进站基线**（源站有并发活动 ⟹ 不删不属于本批的对象）。

★ ⚠️ 本批只做**可逆**的创建/删除；不做付费/生图。
"""
import json
import pathlib
import re
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_charname838.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 场景树（左栏 x<300）里的所有可见叶子文本
DUMP_TREE = """() => {
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0 && getComputedStyle(e).visibility!=='hidden';};
  const out=[];
  for (const el of Array.from(document.querySelectorAll('span,div,button,a,p,li'))) {
    if (!vis(el) || el.childElementCount>0) continue;
    const r=el.getBoundingClientRect();
    if (r.x > 300) continue;
    const t=(el.textContent||'').trim();
    if (!t || t.length>30) continue;
    out.push({text:t, x:Math.round(r.x), y:Math.round(r.y),
              cls:(el.className||'').toString().slice(0,80), tag:el.tagName});
  }
  return out.sort((a,b)=> (a.y-b.y) || (a.x-b.x));
}"""

# ★ 右栏（属性面板）里的可见叶子文本 ⟹ 找「添加角色」之类的入口
DUMP_RIGHT = """() => {
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0 && getComputedStyle(e).visibility!=='hidden';};
  const out=[];
  for (const el of Array.from(document.querySelectorAll('span,div,button,a,p,li'))) {
    if (!vis(el) || el.childElementCount>0) continue;
    const r=el.getBoundingClientRect();
    if (r.x < 1300) continue;
    const t=(el.textContent||'').trim();
    if (!t || t.length>30) continue;
    out.push({text:t, x:Math.round(r.x), y:Math.round(r.y), tag:el.tagName,
              cls:(el.className||'').toString().slice(0,70)});
  }
  return out.sort((a,b)=> (a.y-b.y) || (a.x-b.x));
}"""

# ★ 左栏底部按钮（资源栏）里的可见文本 ⟹ 「人物」入口
DUMP_RAIL = """() => {
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0 && getComputedStyle(e).visibility!=='hidden';};
  const out=[];
  const els=Array.from(document.querySelectorAll('button,a,[role="button"],span,div'))
    .filter(e=>e.childElementCount===0 || e.getAttribute('aria-label'));
  for (const el of els) {
    if (!vis(el)) continue;
    const r=el.getBoundingClientRect();
    if (r.x > 60) continue;
    const t=(el.textContent||'').trim();
    const aria=el.getAttribute('aria-label')||'';
    const title=el.getAttribute('title')||'';
    if (!t && !aria && !title) continue;
    out.push({text:t, aria, title, x:Math.round(r.x), y:Math.round(r.y),
              w:Math.round(r.width), h:Math.round(r.height), tag:el.tagName});
  }
  return out.sort((a,b)=> (a.y-b.y));
}"""


def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(800)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(9_000)


def clean(page):
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")


def tree_names(page):
    """★ 场景树里的**对象行**名（用**无正则**口径：取左栏里位于 x∈[50,300] 的叶子文本）"""
    items = page.evaluate(DUMP_TREE)
    names = []
    for it in items:
        if 50 <= it["x"] <= 300 and it["text"] and it["text"] not in ("场景", "对象"):
            names.append(it["text"])
    # 去重保序
    seen = set()
    out = []
    for x in names:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out, items


def run(out, cookies):
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
        open_desk(page)
        clean(page)

        base, items = tree_names(page)
        out["①进站基线_场景树名字"] = base
        out["①进站基线_场景树文本"] = items
        out["②资源栏"] = page.evaluate(DUMP_RAIL)
        out["③右栏文本"] = page.evaluate(DUMP_RIGHT)
        try:
            page.screenshot(path="/tmp/liblib_source_charname838.png")
            out["截图"] = "/tmp/liblib_source_charname838.png"
        except Exception:
            pass
        br.close()


def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    out = {}
    try:
        run(out, cookies)
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        print("\n=== 进站基线：场景树名字（无正则口径）===")
        print("  ", out.get("①进站基线_场景树名字"))
        print("\n=== 资源栏 ===")
        for d in (out.get("②资源栏") or [])[:40]:
            print("  @(%s,%s) text=%r aria=%r title=%r" % (d["x"], d["y"], d["text"], d["aria"], d["title"]))
        print("\n=== 右栏文本（前 40）===")
        for d in (out.get("③右栏文本") or [])[:40]:
            print("  @(%s,%s) %r" % (d["x"], d["y"], d["text"]))
        if out.get("异常"):
            print("异常：", out["异常"])


if __name__ == "__main__":
    main()
