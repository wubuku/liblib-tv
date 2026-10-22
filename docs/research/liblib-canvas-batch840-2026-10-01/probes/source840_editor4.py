#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 840 源站探针④：补三处**视觉**细节（颜色／图标／复选框可见件）。

① 三列的**底色**（模态／左列 ASIDE／预览 MAIN／右列 ASIDE／底栏）—— 取**计算样式**，
   不看类名（类名里是**被截断的** CSS 变量任意值类，读不出来）。
   ★★ **警告**：本文件里**不要**写出「bg- 前缀 ＋ 方括号包一个 var(...)」那种**截断**的
   类名原文 —— Tailwind v4 会扫描**整个项目**（含 .py/.md/.json）⟹ 它会把那个字面量
   当成真类名生成一条**坏规则**（`var(--character-st...)` 不是合法 CSS 值）⟹
   ⟹ PostCSS 解析失败 ⟹ **整站 500**（本批实测踩过一次）。
② 「44」前面那枚 **⚡ 图标**是什么（svg？文字？盒多大）。
③ 底栏那个 **sr-only 复选框**的**可见件**长什么样（peer 兄弟节点）。

★★ 只读。
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_840_editor4.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

READ = r"""()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};};
  const txt=(e)=>(e.textContent||'').trim().replace(/\s+/g,' ');
  const leafByText=(t)=>{for(const e of document.querySelectorAll('span,div,button,a,p,label')){
    if(e.children.length===0&&txt(e)===t)return e;}return null;};
  const cs=(e)=>{const s=getComputedStyle(e);
    return {bg:s.backgroundColor,border:s.borderColor,borderW:s.borderTopWidth,
      radius:s.borderRadius,color:s.color};};
  const seg=leafByText('脸部精修'), gen=leafByText('确认生成'), save=leafByText('保存');
  const fortyFour=leafByText('44');
  const out={};
  if(seg&&gen){
    const chain=(e)=>{const s=new Set();for(let n=e;n;n=n.parentElement)s.add(n);return s;};
    const ca=chain(seg);let body=null;
    for(let n=gen;n;n=n.parentElement){if(ca.has(n)){body=n;break;}}
    if(body){
      out.body=body;
      out.bodyBox=box(body);
      out.bodyStyle=cs(body);
      const asides=[...body.querySelectorAll('aside')];
      out.asides=asides.map(a=>({box:box(a),style:cs(a),
        cls:(a.getAttribute('class')||'').slice(0,160)}));
      const main=body.querySelector('main');
      out.main=main?{box:box(main),style:cs(main),
        cls:(main.getAttribute('class')||'').slice(0,160)}:null;
    }
  }
  if(save&&seg){
    const chain=(e)=>{const s=new Set();for(let n=e;n;n=n.parentElement)s.add(n);return s;};
    const ca=chain(seg);let modal=null;
    for(let n=save;n;n=n.parentElement){if(ca.has(n)){modal=n;break;}}
    if(modal){
      out.modal={box:box(modal),style:cs(modal),
        cls:(modal.getAttribute('class')||'').slice(0,200)};
      // 底栏：模态最底部 120px 内、y>830 的元素
      out.footer=[...modal.querySelectorAll('*')].filter(e=>{
        const r=e.getBoundingClientRect();
        return r.height>0&&r.y>830&&r.x>=361&&r.x<=1559;})
        .map(e=>({tag:e.tagName,role:e.getAttribute('role')||'',text:txt(e).slice(0,20),
          box:box(e),cls:(e.getAttribute('class')||'').slice(0,120),
          style:cs(e)})).slice(0,40);
    }
  }
  if(fortyFour){
    out.fortyFour={box:box(fortyFour),style:cs(fortyFour),
      prevTag:fortyFour.previousElementSibling?fortyFour.previousElementSibling.tagName:'',
      prevBox:fortyFour.previousElementSibling?box(fortyFour.previousElementSibling):null,
      prevCls:fortyFour.previousElementSibling?(fortyFour.previousElementSibling.getAttribute('class')||'').slice(0,140):'',
      prevText:fortyFour.previousElementSibling?txt(fortyFour.previousElementSibling).slice(0,20):''};
  }
  // 复选框可见件：sr-only input 的**前一个兄弟**与**后一个兄弟**
  const cb=[...document.querySelectorAll('input.peer.sr-only')][0];
  if(cb){
    const sib=(el)=>el?{tag:el.tagName,box:box(el),style:cs(el),
      cls:(el.getAttribute('class')||'').slice(0,140),text:txt(el).slice(0,16)}:null;
    out.checkbox={input:{box:box(cb),checked:cb.checked},
      prev:sib(cb.previousElementSibling),next:sib(cb.nextElementSibling),
      parentCls:(cb.parentElement?(cb.parentElement.getAttribute('class')||'').slice(0,160):'')};
  }
  return out;
}"""

FIND_ASSETS_BTN = """()=>{
  const out=[];
  for(const e of document.querySelectorAll('button')){
    if((e.textContent||'').trim()!=='查看角色资产')continue;
    const r=e.getBoundingClientRect();
    out.push({x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),
      h:Math.round(r.height)});
  }
  return out;}"""


def click_text(page, label):
    for e in page.query_selector_all("span,div,button,a,p"):
        if (e.text_content() or "").strip() != label:
            continue
        bb = e.bounding_box()
        if not bb:
            continue
        page.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
        return True
    return False


def main():
    log = {}
    try:
        cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                                 locale="zh-CN")
            ctx.add_cookies([{"name": c["name"], "value": c["value"],
                              "domain": c["domain"], "path": c.get("path", "/")}
                             for c in cookies])
            pg = ctx.new_page()
            pg.set_default_timeout(25_000)
            pg.goto(URL, wait_until="domcontentloaded", timeout=90_000)
            pg.wait_for_timeout(12_000)
            el = pg.query_selector("text=下次再说")
            if el:
                el.click()
                pg.wait_for_timeout(900)
            el = pg.query_selector('[data-sidebar-btn="character-library"]')
            if el:
                bb = el.bounding_box()
                if bb:
                    pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
            pg.wait_for_timeout(5000)
            tab = pg.query_selector("button:text-is('官方角色库')")
            if tab:
                bb = tab.bounding_box()
                pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
                pg.wait_for_timeout(4000)
            bs = pg.evaluate(FIND_ASSETS_BTN)
            if bs:
                b = bs[0]
                pg.mouse.move(b["x"] + b["w"] / 2, b["y"] + b["h"] / 2)
                pg.wait_for_timeout(1500)
                bs2 = pg.evaluate(FIND_ASSETS_BTN)
                b2 = bs2[0] if bs2 else b
                pg.mouse.click(b2["x"] + b2["w"] / 2, b2["y"] + b2["h"] / 2)
                pg.wait_for_timeout(3500)
            log["★是否点到编辑角色"] = click_text(pg, "编辑角色")
            pg.wait_for_timeout(5000)
            log["★视觉读数"] = pg.evaluate(READ)
            br.close()
    except Exception:
        log["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        v = log.get("★视觉读数") or {}
        print("modal :", json.dumps(v.get("modal"), ensure_ascii=False))
        print("body  :", json.dumps({"box": v.get("bodyBox"), "style": v.get("bodyStyle")},
                                     ensure_ascii=False))
        for a in v.get("asides") or []:
            print("aside :", json.dumps(a, ensure_ascii=False))
        print("main  :", json.dumps(v.get("main"), ensure_ascii=False))
        print("44    :", json.dumps(v.get("fortyFour"), ensure_ascii=False))
        print("cb    :", json.dumps(v.get("checkbox"), ensure_ascii=False))
        for f in (v.get("footer") or [])[:16]:
            print("  foot:", json.dumps(f, ensure_ascii=False))
        if log.get("异常"):
            print("异常：", log["异常"])


if __name__ == "__main__":
    main()
