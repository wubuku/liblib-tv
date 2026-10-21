#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 836 源站探针 v5：★ **不用正则**地读场景树 ⟹ 查清到底有几台机位、叫什么。

★★★ 为什么必须重读：前面 v1／v3／v4 的读数都用了正则 `/^机位\\s*\\d+$/`
  ⟹ ★★ **它不匹配「机位01 · 对峙中景」** ⟹ 如果源站场景里**还有一台**那种名字的机位
  ⟹ 我的计数**一直漏了它** ⟹ ⟹ ★★ 那么「删 机位1：3 → 3 台 ✘ 未减少」就可能是
  **我的计数口径错了**（真删掉了，但因为我只数正则匹配的、所以看起来没少），
  而**不是**「产品保护」⟹ ★★ 前面的结论就都站不住了。

★ 本探针：**把场景树里所有含「机位」的文本原样读出来**（不设正则、不做过滤），
  并**同时**读右栏机位名 ⟹ 于是「到底有几台、叫什么」是**读出来的**，不是**推断出来的**。

★ 同时：读**每个**含「机位」文本的完整 class 链 ⟹ 便于区分「树节点」与「别处的标签」。
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_camnum836e.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 所有含「机位」的可见文本，**原样**、不加正则
DUMP_ALL_CAM_TEXT = """()=>{
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
  const out=[];
  for (const el of Array.from(document.querySelectorAll('span,div,button,a'))) {
    if (!vis(el)) continue;
    if (el.childElementCount > 0) continue;   // 只要叶子节点 ⟹ 避免父节点重复
    const t=(el.textContent||'').trim();
    if (!t || t.indexOf('机位')<0) continue;
    const r=el.getBoundingClientRect();
    out.push({text:t, x:Math.round(r.x), y:Math.round(r.y),
              w:Math.round(r.width), h:Math.round(r.height),
              cls:(el.className||'').toString().slice(0,100),
              tag:el.tagName});
  }
  return out;
}"""

# ★ 右栏（选中机位）的名字
DUMP_RIGHT = """()=>{
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
  const cols=Array.from(document.querySelectorAll('div')).filter(e=>{
    const r=e.getBoundingClientRect();
    return vis(e)&&r.x>=1600&&r.width>=240&&r.width<=300&&r.height>=900;});
  const col=cols[cols.length-1];
  if(!col) return null;
  const ins=Array.from(col.querySelectorAll('input')).filter(vis);
  return {first:ins.length?ins[0].value:null, n:ins.length};
}"""


def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(800)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(9_000)


def back_to_scene(page):
    try:
        nav = page.locator("nav").filter(
            has=page.locator("button[aria-label='场景']")).first
        nav.locator("button[aria-label='场景']").first.click()
        page.wait_for_timeout(1_600)
    except Exception:
        pass


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
            back_to_scene(page)
            alls = page.evaluate(DUMP_ALL_CAM_TEXT)
            out["①所有含「机位」的可见文本"] = alls
            out["①右栏"] = page.evaluate(DUMP_RIGHT)
            # ★ 按 y 排序（场景树是竖排的）⟹ 便于看层级
            alls2 = sorted(alls, key=lambda d: (d["y"], d["x"]))
            out["①按位置排序"] = [{"text": d["text"], "x": d["x"], "y": d["y"],
                                "cls": d["cls"][:60]} for d in alls2]
            # ★ 树区域（左侧 x < 400）的那些 ⟹ 最可能是场景树节点
            left = [d for d in alls2 if d["x"] < 400]
            out["②左侧（树区）的机位相关文本"] = [
                {"text": d["text"], "x": d["x"], "y": d["y"], "cls": d["cls"][:60]} for d in left]
            out["②左侧文本条数"] = len(left)
            out["②左侧去重后的文本"] = sorted({d["text"] for d in left})
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
        print("右栏：", json.dumps(out.get("①右栏"), ensure_ascii=False))
        print("左侧（树区）文本条数：", out.get("②左侧文本条数"))
        print("左侧去重文本：", json.dumps(out.get("②左侧去重后的文本"), ensure_ascii=False))
        print("\n左侧逐条：")
        for d in out.get("②左侧（树区）的机位相关文本") or []:
            print("   @(%s,%s) %r  %s" % (d["x"], d["y"], d["text"], d["cls"]))
        if out.get("异常"):
            print("异常：", out["异常"])


if __name__ == "__main__":
    main()
