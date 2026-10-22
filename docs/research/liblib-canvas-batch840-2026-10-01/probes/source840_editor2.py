#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 840 源站探针②：补齐第一趟读数的三处缺口。

★ 第一趟（`source840_editor`）的 LCA 是编辑器的**内容行**（1198×602 @361,231）⟹
  ⟹ **底栏**（保存／保存并添加到画布／保存时生成角色资产 ⚡44）**不在**那棵子树里；
  ⟹ 且「祛斑祛痘」那行**没读到开关**（它不是 `role=switch`、也不是 `input[type=checkbox]`）；
  ⟹ 且**中间预览区**（角色立绘）的几何没读。

⟹ 本趟：
  ① 以「保存」为锚点找**模态容器**（它同时含底栏与内容行）⟹ 读**整棵**子树；
  ② 专门扫「祛斑祛痘」那一行（y 725..775 × x 1280..1545）里**所有**元素 ⟹ 找出开关是什么；
  ③ 扫**中间预览区**（x 620..1290 × y 270..790）的元素。

★★ 仍然**只读**：绝不点「确认生成／保存／保存并添加到画布」。
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_840_editor2.json")
SHOT = pathlib.Path("/tmp/liblib_source_840_editor2.png")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

MEASURE = r"""()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};};
  const txt=(e)=>(e.textContent||'').trim().replace(/\s+/g,' ');
  const vis=(e)=>{const r=e.getBoundingClientRect();
    if(r.width<=0||r.height<=0)return false;
    const cs=getComputedStyle(e);
    return cs.display!=='none'&&cs.visibility!=='hidden'&&Number(cs.opacity||'1')>0.001;};
  const leafByText=(t)=>{for(const e of document.querySelectorAll('span,div,button,a,p,label')){
    if(e.children.length===0&&txt(e)===t)return e;}return null;};
  const save=leafByText('保存'), seg=leafByText('脸部精修');
  if(!save||!seg)return {err:'锚点没找到',hasSave:!!save,hasSeg:!!seg};
  const chain=(e)=>{const s=new Set();for(let n=e;n;n=n.parentElement)s.add(n);return s;};
  const cs_=chain(seg);let modal=null;
  for(let n=save;n;n=n.parentElement){if(cs_.has(n)){modal=n;break;}}

  const all=[];
  const walk=(root)=>{
    for(const e of root.querySelectorAll('*')){
      if(!vis(e))continue;
      const r=e.getBoundingClientRect();
      const t=txt(e);
      all.push({tag:e.tagName,role:e.getAttribute('role')||'',
        text:(e.children.length===0?t:''),
        type:e.getAttribute('type')||'',
        value:(e.tagName==='INPUT'||e.tagName==='TEXTAREA')?(e.value||''):'',
        aria:e.getAttribute('aria-label')||'',
        box:box(e),cls:(e.getAttribute('class')||'').slice(0,110)});
    }
  };
  if(modal)walk(modal);

  const inRect=(b,x0,y0,x1,y1)=>b.x<x1&&b.x+b.w>x0&&b.y<y1&&b.y+b.h>y0;
  const rowAcne=all.filter(e=>inRect(e.box,1280,725,1545,775));
  const preview=all.filter(e=>inRect(e.box,620,270,1292,790));

  const leaves=[],inputs=[],ctrls=[];
  for(const e of all){
    if(e.text&&e.text.length<=40)leaves.push(e);
    if(e.tag==='INPUT'||e.tag==='TEXTAREA')inputs.push(e);
    if(e.tag==='BUTTON'||e.role==='button'||e.role==='slider'||e.role==='switch'
       ||e.type==='checkbox'||e.type==='range')ctrls.push(e);
  }
  const mc=modal?getComputedStyle(modal):null;
  return {
    modal:modal?{tag:modal.tagName,box:box(modal),
      cls:(modal.getAttribute('class')||'').slice(0,220),
      position:mc.position,zIndex:mc.zIndex,bg:mc.backgroundColor,
      radius:mc.borderRadius}:null,
    leaves,inputs,ctrls,
    rowAcne,preview,
    count:all.length,url:location.href};
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
            log["★读数"] = pg.evaluate(MEASURE)
            pg.screenshot(path=str(SHOT))
            br.close()
    except Exception:
        log["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        r = log.get("★读数") or {}
        if r.get("err"):
            print("★ 读数失败：", r)
        if r.get("modal"):
            print("模态容器：", json.dumps(r["modal"], ensure_ascii=False))
            print("元素总数：", r.get("count"))
        if log.get("异常"):
            print("异常：", log["异常"])


if __name__ == "__main__":
    main()
