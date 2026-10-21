#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""源站探针 —— 点底部那个「TV Director」胶囊，**到底发生什么**？

★ 为什么必须实测：clone 的「打开导演台」按钮挂在**导演台节点卡片**上
  （`ScriptExecutionNode.tsx:54`）⟹ ⟹ ★ 用户想用导演台**必须先在画布上
  造一个「导演台」节点**。而源站画布底部有一条 **TV Director 胶囊**
  （48×48、青色、svg=3）⟹ ⟹ ★★ 源站是不是**不需要节点**就能进导演台？
  ⟹ ⟹ **不能凭猜实施**：可能是① 直接进导演台 ② 新建一个导演台节点再进
  ③ 弹一个介绍浮层。

★ 判据：URL 变没变、画布节点数变没变、出现什么浮层、有没有新 DOM。
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_tvdirector.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

STATE = """()=>{
  const visible=(e)=>{const r=e.getBoundingClientRect();
    if(r.width===0&&r.height===0)return false;
    const cs=getComputedStyle(e);
    return cs.visibility!=='hidden'&&cs.display!=='none'
      && Number(cs.opacity||'1')>0;};
  const texts=[];
  for(const e of Array.from(document.querySelectorAll('button,a,[role=button],'
      +'[role=dialog],h1,h2,h3,p,span'))){
    if(!visible(e))continue;
    const t=(e.textContent||'').trim().replace(/\\s+/g,' ');
    if(!t||t.length>40)continue;
    const r=e.getBoundingClientRect();
    if(r.width<8||r.height<8)continue;
    texts.push({tag:e.tagName,t:t.slice(0,36),
      x:Math.round(r.x),y:Math.round(r.y)});}
  return {url:location.href,
    title:document.title,
    rf:document.querySelectorAll('.react-flow').length,
    nodes:document.querySelectorAll('.react-flow__node').length,
    nodeIds:Array.from(document.querySelectorAll('.react-flow__node'))
      .map(e=>e.getAttribute('data-id')).slice(0,30),
    可见文本:texts.slice(0,60)};}"""

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
    pg.wait_for_timeout(9000)
    # ★ 关掉可能挡住底部的弹窗
    for label in ("下次再说",):
        el = pg.query_selector("text=%s" % label)
        if el:
            el.click()
            pg.wait_for_timeout(900)
            break
    out["点之前"] = pg.evaluate(STATE)

    # ★ 找那个胶囊：aria-label = "TV Director"（48×48，svg=3）
    cap = pg.query_selector('button[aria-label="TV Director"]')
    out["胶囊"] = {
        "存在": bool(cap),
        "矩形": (cap.bounding_box() if cap else None),
    }
    if cap:
        cap.click()
        pg.wait_for_timeout(6000)
        out["点之后_6s"] = pg.evaluate(STATE)
        pg.wait_for_timeout(8000)
        out["点之后_14s"] = pg.evaluate(STATE)
        pg.screenshot(path="/tmp/liblib_source_after_tv.png")
    br.close()

OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
b, a = out.get("点之前", {}), out.get("点之后_6s", {})
print("胶囊:", json.dumps(out.get("胶囊"), ensure_ascii=False))
print("\n点之前: url=%s rf=%s nodes=%s" % (b.get("url"), b.get("rf"),
                                           b.get("nodes")))
print("点之后: url=%s rf=%s nodes=%s" % (a.get("url"), a.get("rf"),
                                           a.get("nodes")))
print("URL 变了:", b.get("url") != a.get("url"))
print("节点数变了:", b.get("nodes"), "→", a.get("nodes"))
new_nodes = set(a.get("nodeIds") or []) - set(b.get("nodeIds") or [])
print("★ 新增节点:", sorted(new_nodes))
bt = {t["t"] for t in b.get("可见文本", [])}
at = {t["t"] for t in a.get("可见文本", [])}
print("★ 新出现的文本:", sorted(at - bt)[:25])
