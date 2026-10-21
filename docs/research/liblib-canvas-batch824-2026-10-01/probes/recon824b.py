#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""源站画布**底部工具条**精确测量 —— clone 缺这一条（有源站依据）。

★ 源站截图里画布底部中间有一条工具条：白底 **加号**、鼠标指针、剪贴、
  表情（带蓝点）、时钟、键盘、**?**、分隔线、青色「TV Director」胶囊。
★ clone 侧实测**没有**这条（`BottomToolbar` 在**左下角**，内容也不同：
  资产管理／整理画布／小地图／隐藏连线／网格吸附／缩放）。
⟹ 本脚本量出源站那条工具条的**每个按钮**的矩形、图标线索与可及名。
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_bottombar.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 只看**底部中间**那条（y>860、x 在中间 500~1100）
BOTTOM = """()=>{
  const visible=(e)=>{const r=e.getBoundingClientRect();
    if(r.width===0&&r.height===0)return false;
    const cs=getComputedStyle(e);
    return cs.visibility!=='hidden'&&cs.display!=='none'
      && Number(cs.opacity||'1')>0;};
  const out=[];
  for(const e of Array.from(document.querySelectorAll(
      'button,[role=button],a,div[class*=tooltip]'))){
    if(!visible(e))continue;
    const r=e.getBoundingClientRect();
    if(r.y<850)continue;
    if(r.x<450||r.x>1250)continue;
    if(r.width>300||r.height>90)continue;
    out.push({tag:e.tagName,
      text:(e.textContent||'').trim().replace(/\\s+/g,' ').slice(0,24),
      aria:e.getAttribute('aria-label')||'',
      title:e.getAttribute('title')||'',
      data:Array.from(e.attributes).filter(a=>a.name.startsWith('data-'))
            .map(a=>a.name+'='+a.value).join(' ').slice(0,60),
      cls:(e.getAttribute('class')||'').slice(0,70),
      svg:e.querySelectorAll('svg').length,
      矩形:{x:Math.round(r.x),y:Math.round(r.y),
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
    pg.wait_for_timeout(9000)
    # ★ 关掉可能挡住底部的弹窗（「下次再说」）
    for label in ("下次再说",):
        el = pg.query_selector("text=%s" % label)
        if el:
            el.click()
            pg.wait_for_timeout(800)
            break
    out["底部中间"] = pg.evaluate(BOTTOM)
    # ★ 再量一次**整条**底部（不限 x），把左下角那簇也记下来做对照
    out["底部全部"] = pg.evaluate("""()=>{
      const visible=(e)=>{const r=e.getBoundingClientRect();
        if(r.width===0&&r.height===0)return false;
        const cs=getComputedStyle(e);
        return cs.visibility!=='hidden'&&cs.display!=='none';};
      const out=[];
      for(const e of Array.from(document.querySelectorAll('button,[role=button]'))){
        if(!visible(e))continue;
        const r=e.getBoundingClientRect();
        if(r.y<840)continue;
        out.push({text:(e.textContent||'').trim().replace(/\\s+/g,' ').slice(0,20),
                  aria:e.getAttribute('aria-label')||'',
                  cls:(e.getAttribute('class')||'').slice(0,56),
                  矩形:{x:Math.round(r.x),y:Math.round(r.y),
                        w:Math.round(r.width),h:Math.round(r.height)}});}
      return out;}""")
    pg.screenshot(path="/tmp/liblib_source_bottom.png")
    br.close()

OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("=== 源站底部中间工具条 ===")
for d in out["底部中间"]:
    print("  %-7s %-20s aria=%-14s svg=%d %s" % (
        d["tag"], d["text"][:20], d["aria"][:14], d["svg"], d["矩形"]))
print("\n=== 源站底部全部按钮 ===")
for d in out["底部全部"]:
    print("  %-20s aria=%-16s %s" % (d["text"][:20], d["aria"][:16], d["矩形"]))
