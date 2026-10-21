#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 837 源站探针 v2：找「**镜头**」在源站的**显示位置**，并读出镜头名。

★★★ 为什么上一趟没读到：场景树里**没有镜头节点**（只读到一枚「确认镜头」按钮）
  ⟹ ★ 镜头不在场景树里 ⟹ 上一趟的读法（扫左侧树区含「镜头」的文本）**读错了地方**。

★ 源站的「镜头」最可能出现在三处：
  ① 视口**下方**的结果镜头条（一排 chip）；
  ② 底部**时间轴**里；
  ③ 右侧属性面板的某处。
⟹ 本探针**整页**扫（含「镜头」「对峙」「中景」「镜」）⟹ 把命中位置的**几何**一起记下 ⟹
  ⟹ 由**位置**反推那是哪块 UI（不靠猜）。

★ 同时读**视口下方的横向条带**（clone 的镜头条在视口底部）里所有可见文本。

★ 只读，不改源站项目。
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_shotname837b.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 整页所有可见叶子文本（带几何）—— 只保留含关键词的
DUMP_KW = """(kws) => {
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
  const out=[];
  for (const el of Array.from(document.querySelectorAll('span,div,button,a,p,li,h1,h2,h3'))) {
    if (!vis(el)) continue;
    if (el.childElementCount > 0) continue;
    const t=(el.textContent||'').trim();
    if (!t || t.length > 40) continue;
    for (const k of kws) {
      if (t.indexOf(k) >= 0) {
        const r=el.getBoundingClientRect();
        out.push({kw:k, text:t, x:Math.round(r.x), y:Math.round(r.y),
                  w:Math.round(r.width), h:Math.round(r.height),
                  cls:(el.className||'').toString().slice(0,90), tag:el.tagName});
        break;
      }
    }
  }
  return out.sort((a,b)=> (a.y-b.y) || (a.x-b.x));
}"""

# ★ 视口下方的横向带（clone 的镜头条在视口底部）
DUMP_BOTTOM = """() => {
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
  const out=[];
  for (const el of Array.from(document.querySelectorAll('span,div,button,a'))) {
    if (!vis(el) || el.childElementCount > 0) continue;
    const r=el.getBoundingClientRect();
    if (r.y < 700) continue;                       // ★ 只要下半屏
    if (r.x < 1200) continue;                      // ★ 只要右半（避开画布与左栏）
    const t=(el.textContent||'').trim();
    if (!t || t.length > 40) continue;
    out.push({text:t, x:Math.round(r.x), y:Math.round(r.y),
              w:Math.round(r.width), h:Math.round(r.height),
              cls:(el.className||'').toString().slice(0,80), tag:el.tagName});
  }
  return out.sort((a,b)=> (a.y-b.y) || (a.x-b.x));
}"""


def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(800)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(9_000)


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
        try:
            page.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
            out["①含「镜头/对峙/中景」的所有可见文本"] = page.evaluate(
                DUMP_KW, ["镜头", "对峙", "中景", "镜"])
            out["②右下区域所有可见文本"] = page.evaluate(DUMP_BOTTOM)
            try:
                page.screenshot(path="/tmp/liblib_source_shotname837b.png")
                out["截图"] = "/tmp/liblib_source_shotname837b.png"
            except Exception:
                pass
        finally:
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
        print("\n=== 含「镜头/对峙/中景/镜」的可见文本 ===")
        for d in out.get("①含「镜头/对峙/中景」的所有可见文本") or []:
            print("  @(%s,%s) %r  <%s> %s" % (d["x"], d["y"], d["text"], d["tag"], d["cls"][:60]))
        print("\n=== 右下区域文本（前 40 条）===")
        for d in (out.get("②右下区域所有可见文本") or [])[:40]:
            print("  @(%s,%s) %r" % (d["x"], d["y"], d["text"]))
        if out.get("异常"):
            print("异常：", out["异常"])


if __name__ == "__main__":
    main()
