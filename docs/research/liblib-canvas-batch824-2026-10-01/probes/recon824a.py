#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""源站画布侦察 —— **用户到底怎么新建节点**？（源站侧第一手事实）

★ 为什么要问这个：clone 侧 811/812/814/815 四批都用
  `addNodeAtPosition` **后门**造节点 ⟹ 至今**没有纯 UI 替身**。
  batch 823 在 clone 上找到的入口是**左栏「添加节点」**（`LeftSidebar.tsx:153`，
  渲染成 `button[aria-label="添加节点"]`），
  ★ 但那只是**clone 自己**的入口 ⟹ **源站是怎么做的？** 本批去问源站。

★ 用无头 + 已导出的登录态（`/tmp/liblib-cookie.json`）⟹ 不需要有头浏览器。
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_addnode.json")
SHOT = pathlib.Path("/tmp/liblib_source_canvas.png")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

DUMP = """()=>{
  const visible=(e)=>{const r=e.getBoundingClientRect();
    if(r.width===0&&r.height===0)return false;
    const cs=getComputedStyle(e);
    return cs.visibility!=='hidden'&&cs.display!=='none'
      && Number(cs.opacity||'1')>0;};
  const out=[];
  for(const e of Array.from(document.querySelectorAll(
      'button,[role=button],[role=menuitem],a,input'))) {
    if(!visible(e))continue;
    const r=e.getBoundingClientRect();
    out.push({tag:e.tagName,
      text:(e.textContent||'').trim().replace(/\\s+/g,' ').slice(0,30),
      aria:e.getAttribute('aria-label')||'',
      title:e.getAttribute('title')||'',
      role:e.getAttribute('role')||'',
      cls:(e.getAttribute('class')||'').slice(0,50),
      rect:{x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)}});}
  return out;}"""

cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
out = {}
with sync_playwright() as pw:
    br = pw.chromium.launch(headless=True)
    ctx = br.new_context(viewport={"width": 1600, "height": 950},
                          user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X "
                                      "10_15_7) AppleWebKit/537.36 (KHTML, "
                                      "like Gecko) Chrome/134.0.0.0 "
                                      "Safari/537.36"))
    ctx.add_cookies(cookies)
    pg = ctx.new_page()
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    for i in range(30):
        pg.wait_for_timeout(2000)
        if pg.evaluate("()=>document.querySelectorAll('.react-flow').length") > 0:
            break
    pg.wait_for_timeout(8000)
    out["页面"] = pg.evaluate(
        "()=>({url:location.href,title:document.title,"
        "rf:document.querySelectorAll('.react-flow').length,"
        "nodes:document.querySelectorAll('.react-flow__node').length})")
    out["可见可点元素"] = pg.evaluate(DUMP)
    pg.screenshot(path=str(SHOT))

    # ★ 右键画布空白处 —— 源站的「添加节点」常在这个菜单里
    pg.mouse.click(1300, 700)
    pg.wait_for_timeout(800)
    pg.mouse.click(1300, 700, button="right")
    pg.wait_for_timeout(1400)
    out["右键后可见可点元素"] = pg.evaluate(DUMP)
    out["右键菜单文本"] = pg.evaluate(
        "()=>Array.from(document.querySelectorAll("
        "'[role=menu],[role=menuitem],li,ul,div')).map(e=>(e.textContent||'')"
        ".trim().replace(/\\s+/g,' ')).filter(t=>t&&t.length<30)"
        ".filter((v,i,a)=>a.indexOf(v)===i).slice(0,60)")
    pg.screenshot(path="/tmp/liblib_source_rightclick.png")
    br.close()

OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("页面:", json.dumps(out["页面"], ensure_ascii=False))
print("\n=== 可见可点元素（前 60）===")
for d in out["可见可点元素"][:60]:
    print("  %-7s %-24s aria=%-14s title=%-12s %s" % (
        d["tag"], d["text"][:24], d["aria"][:14], d["title"][:12], d["rect"]))
print("\n=== 右键后新增的可点元素 ===")
before = {(d["rect"]["x"], d["rect"]["y"], d["text"]) for d in out["可见可点元素"]}
for d in out["右键后可见可点元素"]:
    if (d["rect"]["x"], d["rect"]["y"], d["text"]) not in before:
        print("  %-7s %-24s aria=%-14s %s" % (
            d["tag"], d["text"][:24], d["aria"][:14], d["rect"]))
print("\n=== 可能的菜单文本 ===")
for t in out["右键菜单文本"][:40]:
    print("  ", t)
