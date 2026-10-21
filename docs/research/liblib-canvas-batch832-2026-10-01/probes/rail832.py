#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 832 源站盘点探针：导演台 **rail 的全部入口**与它们各自打开的东西。

★ 为什么要盘点（不是逐个做）：
  batch 831 补上了 rail 最底下那枚「帮助」⟹ 但 rail 上**还有 7 枚**入口
  ⟹ 得先知道**源站每一枚打开的是什么**、**clone 的对应物是什么**、**差在哪**
  ⟹ 才能挑出下一批该做哪一块，而不是凭印象猜。

★ 本探针**只读**：只点 rail 入口、量东西、关掉，**不碰生成/付费控件**，
  不改源站任何数据。

★ 读数要点：
  - rail 入口是 `aside` 里的 `button`，靠**图标**区分 ⟹ 文本读数器读不到图标名
    ⟹ 改读**每个 button 的 DOM 位置序**（自上而下）＋ 盒 ＋ 类名
  - rail 上那枚「帮助」在最底下（`mt-auto`）⟹ 单独记它
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_desk832_rail.json")
SHOTS = pathlib.Path("/tmp/liblib_source_desk832")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ rail 枚举：找最左侧那根 48px 宽的 aside，取它里面的 button
DUMP_RAIL = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const cs=(e)=>{const c=getComputedStyle(e);
    return {bg:c.backgroundColor,color:c.color,fontSize:c.fontSize,
            fontWeight:c.fontWeight,borderRadius:c.borderRadius,
            padding:c.padding,gap:c.gap,opacity:c.opacity,
            display:c.display,position:c.position,zIndex:c.zIndex};};
  // ★ 最左侧那根竖条：宽度 48（w-12）
  const asides=Array.from(document.querySelectorAll('aside')).filter(e=>{
    const r=e.getBoundingClientRect();
    return r.x<=2&&r.width>=40&&r.width<=60&&r.height>400;});
  const rail=asides[asides.length-1];
  if(!rail) return {found:false, asides:asides.length};
  const btns=Array.from(rail.querySelectorAll('button')).filter(b=>{
    const r=b.getBoundingClientRect();
    return r.width>0&&r.height>0;});
  return {
    found:true,
    railBox:box(rail), railCls:String(rail.className||'').slice(0,160),
    count:btns.length,
    buttons:btns.map((b,i)=>({
      idx:i,
      aria:b.getAttribute('aria-label'),
      title:b.getAttribute('title'),
      text:(b.textContent||'').trim().slice(0,20),
      box:box(b), style:cs(b),
      cls:String(b.className||'').slice(0,150),
      hasPopup:b.getAttribute('aria-haspopup'),
      expanded:b.getAttribute('aria-expanded'),
      svgCount:b.querySelectorAll('svg').length,
      svgBox:b.querySelector('svg')?box(b.querySelector('svg')):null,
      svgHtml:b.querySelector('svg')?b.querySelector('svg').outerHTML.slice(0,200):null,
    })),
  };
}"""

# ★ 点开某个东西之后，量「新出现的浮层」（用「开前后的元素快照差」定位）
DUMP_OVERLAY = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const cs=(e)=>{const c=getComputedStyle(e);
    return {bg:c.backgroundColor,color:c.color,fontSize:c.fontSize,
            borderRadius:c.borderRadius,border:c.border,padding:c.padding,
            boxShadow:c.boxShadow,backdropFilter:c.backdropFilter};};
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).visibility!=='hidden'
      &&getComputedStyle(e).display!=='none';};
  const dialogs=Array.from(document.querySelectorAll('[role="dialog"]')).filter(vis);
  const menus=Array.from(document.querySelectorAll('[role="menu"]')).filter(vis);
  // 浮层：position 绝对/固定且盖住视口中部的那些
  const overlays=Array.from(document.querySelectorAll('div')).filter(e=>{
    const c=getComputedStyle(e); const r=e.getBoundingClientRect();
    if(!vis(e)) return false;
    if(c.position!=='absolute'&&c.position!=='fixed') return false;
    return r.width>=160&&r.height>=80&&r.width<=900&&r.height<=900;});
  return {
    dialogs:dialogs.map(e=>({box:box(e),aria:e.getAttribute('aria-label'),
      cls:String(e.className||'').slice(0,200),style:cs(e),
      text:(e.textContent||'').trim().slice(0,200)})),
    menus:menus.map(e=>({box:box(e),aria:e.getAttribute('aria-label'),
      cls:String(e.className||'').slice(0,200),
      items:Array.from(e.querySelectorAll('[role="menuitem"]')).map(i=>({
        t:(i.textContent||'').trim(),box:box(i)}))})),
    overlays:overlays.slice(-6).map(e=>({box:box(e),
      cls:String(e.className||'').slice(0,200),
      text:(e.textContent||'').trim().slice(0,120)})),
  };
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
            out["⓪开台后"] = page.evaluate(DUMP_OVERLAY)
            out["①rail"] = page.evaluate(DUMP_RAIL)
            page.screenshot(path=str(SHOTS / "832_rail.png"))

            # ★ 逐枚 rail 入口点一遍，看各自打开什么（点完按 Esc / 点外面关掉）
            rail = out["①rail"]
            btns = rail.get("buttons") or []
            per = {}
            for b in btns:
                aria = b.get("aria") or ""
                title = b.get("title") or ""
                label = aria or title or ("按钮#%d" % b["idx"])
                try:
                    page.locator("[aria-label='%s']" % aria).first.click() if aria \
                        else page.locator("aside button").nth(b["idx"]).click()
                    page.wait_for_timeout(1_400)
                    per[label] = page.evaluate(DUMP_OVERLAY)
                    page.screenshot(path=str(SHOTS / ("832_click_%d.png" % b["idx"])))
                    # 关掉：先按 Esc，再点视口中间偏下（空白处）
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(600)
                    page.mouse.click(960, 900)
                    page.wait_for_timeout(800)
                except Exception as exc:  # noqa: BLE001
                    per[label] = {"异常": str(exc)[:300]}
                    try:
                        page.keyboard.press("Escape")
                        page.wait_for_timeout(500)
                    except Exception:
                        pass
            out["②逐枚入口"] = per
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
