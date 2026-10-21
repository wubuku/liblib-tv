#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 830 侦察 v8：源站导演台的**焦点落点**与**快捷键管线**到底怎么接的。

★ 为什么必须侦察：
  上一批说「源站按 Z 撤不掉 FOV/改名」——但那两版的「把焦点挪开」动作
  （`focus_desk` 的选择器 `[data-director-workspace] h1, [role=dialog] h1`）
  **在源站 DOM 里压根不存在** ⟹ 焦点可能一直停在 range/输入框上 ⟹
  ★★ 若源站对可编辑目标会吞掉快捷键，那「Z 撤不掉」就是**前提不满足**的无效读数
  （与 batch 828 在 709 上纠正过的是同一类错）。
  ⟹ 先侦察：① 点 3D 视口后焦点落在哪 ② 桌面上有哪些可聚焦元素
  ③ 右栏「3D场景」页签的输入框结构（写一个不串台的读数器）。
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_desk830_recon8.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

DUMP = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const short=(e)=>({tag:e.tagName,ti:e.getAttribute('tabindex'),
                     role:e.getAttribute('role')||'',
                     aria:e.getAttribute('aria-label')||'',
                     cls:(e.className&&e.className.baseVal!==undefined
                          ?e.className.baseVal:String(e.className||'')).slice(0,60),
                     box:box(e),
                     txt:(e.textContent||'').trim().slice(0,18)});
  const all=Array.from(document.querySelectorAll('*'));
  const tabbables=all.filter(e=>e.getAttribute('tabindex')!==null).map(short);
  const canvases=Array.from(document.querySelectorAll('canvas')).map(short);
  // 右栏（x>1600）里的所有输入框：结构侦察用
  const rightInputs=Array.from(document.querySelectorAll('input'))
    .map(e=>({...short(e),type:e.type,value:e.value,
              min:e.min||'',max:e.max||'',step:e.step||'',
              opacity:getComputedStyle(e).opacity,
              pointerEvents:getComputedStyle(e).pointerEvents}))
    .filter(o=>o.box.x>1600);
  const act=(()=>{const a=document.activeElement;
    return a?{tag:a.tagName,type:a.type||'',
              aria:a.getAttribute('aria-label')||'',
              cls:String(a.className||'').slice(0,60),
              txt:(a.textContent||'').trim().slice(0,20)}:null;})();
  return {tabbables:tabbables.slice(0,80),
          tabbables_total:tabbables.length,
          canvases:canvases,
          rightInputs:rightInputs,
          active:act,
          bodyActiveChain:(()=>{const c=[];let a=document.activeElement;
            for(let i=0;a&&i<4;i++,a=a.parentElement)
              c.push(a.tagName+'.'+String(a.className||'').slice(0,40));
            return c;})()};
}"""


def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(600)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(6_000)


def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    out = {}
    try:
        run(out, cookies)
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)


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

        out["①开台后"] = page.evaluate(DUMP)

        # ── 点最大的 canvas（3D 视口）中心 ⟹ 看焦点落到哪
        canv = out["①开台后"]["canvases"]
        big = max(canv, key=lambda c: c["box"]["w"] * c["box"]["h"]) if canv else None
        out["②最大canvas"] = big
        if big:
            b = big["box"]
            page.mouse.click(b["x"] + b["w"] // 2, b["y"] + b["h"] // 2)
            page.wait_for_timeout(1_200)
            out["③点视口后"] = page.evaluate(DUMP)

        # ── 点空白面板（右下角空白处，避开所有控件）⟹ 焦点落到 body？
        page.mouse.click(300, 1000)
        page.wait_for_timeout(800)
        out["④点空白后"] = page.evaluate(DUMP)

        # ── 切「3D场景」页签 ⟹ 再 dump 右栏输入框结构
        try:
            page.get_by_text("3D场景", exact=True).first.click()
            page.wait_for_timeout(2_500)
            out["⑤3D场景页签"] = page.evaluate(DUMP)
        except Exception as e:
            out["⑤_异常"] = str(e)[:400]

        # ── 「动画时间轴」面板 ⟹ dump 时间轴缩放控件的邻居结构
        try:
            if not page.evaluate(
                "()=>!!document.querySelector('[aria-label=\"时间轴缩放\"]')"):
                page.locator("[aria-label='动画时间轴']:visible").first.click()
                page.wait_for_timeout(3_000)
            out["⑥时间轴面板"] = page.evaluate(
                """()=>{
                  const e=document.querySelector('[aria-label="时间轴缩放"]');
                  if(!e) return {found:false};
                  const p=e.parentElement;
                  const sibs=Array.from(p.children).map(c=>({
                    tag:c.tagName,cls:String(c.className||'').slice(0,50),
                    txt:(c.textContent||'').trim().slice(0,20),
                    html:c.outerHTML.slice(0,220)}));
                  return {found:true, outer:e.outerHTML,
                          readOnly:e.readOnly, disabled:e.disabled,
                          step:e.step, value:e.value,
                          opacity:getComputedStyle(e).opacity,
                          parentHTML:p.outerHTML.slice(0,1200),
                          sibs:sibs};
                }""")
        except Exception as e:
            out["⑥_异常"] = str(e)[:400]

        ctx.close()
        br.close()


if __name__ == "__main__":
    main()
