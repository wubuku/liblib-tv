#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 831 源站几何探针：导演台「帮助」→ 菜单 → 快捷键对话框 / 使用教程。

★ 要抓的：
  ① 「帮助」按钮的盒与计算样式（size-8 / rounded-lg / 文字色）
  ② 点开后那枚 **role=menu** 菜单：盒、两枚 menuitem 的盒与计算样式
  ③ 点「快捷键」⟹ 那个 **role=dialog aria-modal** 的 480×314 对话框：
     盒、标题、两列各 192px、每行 12 行的行盒、每行右侧键帽徽标的盒、
     **⌘ 那个 SVG 的盒**（★ 纯文本读数器看不见它，必须单独量）
  ④ 「使用教程」打开的东西（盒 + 结构 + 截图）—— 菜单里两枚都要有下文，
     不能做出一枚点了没反应的「死按钮」

★ 纪律：不点生成/付费控件；本批**只读**，不改任何源站数据。
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_desk831_help.json")
SHOTS = pathlib.Path("/tmp/liblib_source_desk831")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

DUMP_MENU = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const cs=(e)=>{const c=getComputedStyle(e);
    return {bg:c.backgroundColor,color:c.color,fontSize:c.fontSize,
            fontWeight:c.fontWeight,borderRadius:c.borderRadius,
            padding:c.padding,gap:c.gap,width:c.width,height:c.height,
            border:c.border,boxShadow:c.boxShadow,lineHeight:c.lineHeight,
            backdropFilter:c.backdropFilter,opacity:c.opacity,
            display:c.display,position:c.position,zIndex:c.zIndex};};
  const menu=document.querySelector('[role="menu"]');
  const btn=document.querySelector('[aria-label="帮助"]');
  const items=menu?Array.from(menu.querySelectorAll('[role="menuitem"]')):[];
  const svgs=menu?Array.from(menu.querySelectorAll('svg')).map(e=>({box:box(e)})):[];
  return {
    helpButton: btn?{box:box(btn),style:cs(btn),
                     ariaExpanded:btn.getAttribute('aria-expanded'),
                     ariaHasPopup:btn.getAttribute('aria-haspopup'),
                     cls:String(btn.className||'')}:null,
    menu: menu?{box:box(menu),style:cs(menu),
                cls:String(menu.className||''),
                items:items.map(e=>({t:(e.textContent||'').trim(),box:box(e),
                                     style:cs(e),cls:String(e.className||'')})),
                svgs:svgs}:null,
  };
}"""

DUMP_DIALOG = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const cs=(e)=>{const c=getComputedStyle(e);
    return {bg:c.backgroundColor,color:c.color,fontSize:c.fontSize,
            fontWeight:c.fontWeight,borderRadius:c.borderRadius,
            padding:c.padding,gap:c.gap,width:c.width,height:c.height,
            border:c.border,lineHeight:c.lineHeight,
            backdropFilter:c.backdropFilter};};
  const dlg=Array.from(document.querySelectorAll('[role="dialog"]'))
    .filter(e=>{const r=e.getBoundingClientRect();
      return r.width>0&&r.height>0;});
  const d=dlg[dlg.length-1];
  if(!d) return {found:false, dialogs:dlg.length};
  // 标题
  const h2=d.querySelector('h2');
  // 两列：直接子 div 里带 flex 的
  const cols=Array.from(d.querySelectorAll('div')).filter(e=>{
    const c=getComputedStyle(e);
    return c.display==='flex'&&e.children.length>=5
      &&e.getBoundingClientRect().width>150&&e.getBoundingClientRect().width<260;});
  const rows=[];
  for(const col of cols){
    for(const row of Array.from(col.children)){
      const kids=Array.from(row.children).map(k=>({
        tag:k.tagName,t:(k.textContent||'').trim().slice(0,20),
        box:box(k),cls:String(k.className||'').slice(0,70),
        style:cs(k),
        svgs:Array.from(k.querySelectorAll('svg')).map(s=>{
          const r=s.getBoundingClientRect();
          return {x:Math.round(r.x),y:Math.round(r.y),
                  w:Math.round(r.width),h:Math.round(r.height)};}),
        badges:Array.from(k.querySelectorAll('span')).map(s=>({
          t:(s.textContent||'').trim().slice(0,8),
          box:box(s),cls:String(s.className||'').slice(0,80)}))}));
      rows.push({colX:Math.round(col.getBoundingClientRect().x),
                 colBox:box(col),kids:kids});
    }
  }
  return {found:true,
          box:box(d),style:cs(d),
          aria:d.getAttribute('aria-label'),
          ariaModal:d.getAttribute('aria-modal'),
          cls:String(d.className||''),
          title:h2?{t:(h2.textContent||'').trim(),box:box(h2),
                    style:cs(h2)}:null,
          cols:cols.map(c=>({box:box(c),style:cs(c),
                              cls:String(c.className||'')})),
          rows:rows,
          allSvgs:Array.from(d.querySelectorAll('svg')).map(s=>{
            const r=s.getBoundingClientRect();
            return {x:Math.round(r.x),y:Math.round(r.y),
                    w:Math.round(r.width),h:Math.round(r.height),
                    html:s.outerHTML.slice(0,120)};})};
}"""


def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(600)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(6_000)


def close_desk(page):
    page.locator("[aria-label='关闭']:visible").first.click()
    page.wait_for_timeout(3_000)


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
        SHOTS.mkdir(exist_ok=True)

        try:
            out["①帮助按钮"] = page.evaluate(DUMP_MENU)
            page.locator("[aria-label='帮助']").first.click()
            page.wait_for_timeout(1_200)
            out["②菜单打开"] = page.evaluate(DUMP_MENU)
            page.screenshot(path=str(SHOTS / "831_menu.png"))

            # ── 快捷键对话框
            page.get_by_text("快捷键", exact=True).first.click()
            page.wait_for_timeout(1_800)
            out["③快捷键对话框"] = page.evaluate(DUMP_DIALOG)
            page.screenshot(path=str(SHOTS / "831_shortcuts.png"))
            page.keyboard.press("Escape")
            page.wait_for_timeout(1_000)

            # ── 使用教程
            page.locator("[aria-label='帮助']").first.click()
            page.wait_for_timeout(1_000)
            page.get_by_text("使用教程", exact=True).first.click()
            page.wait_for_timeout(2_500)
            out["④使用教程"] = page.evaluate(DUMP_DIALOG)
            page.screenshot(path=str(SHOTS / "831_tutorial.png"))
        except Exception:
            out["异常"] = traceback.format_exc()[-1500:]
        try:
            close_desk(page)
        except Exception:
            pass
        ctx.close()
        br.close()


if __name__ == "__main__":
    main()
