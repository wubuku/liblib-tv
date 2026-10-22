#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 839 源站探针②：**读数器扫错文档**的诊断。

★ 上一趟（assets839）的现象：
  - 截图里**角色库面板明明开着**（1198×758 的大弹窗：我的角色库／官方角色库 页签、
    性别／年龄段／文化区域 筛选、横向角色条、右上三枚视图切换、底部「创建新角色」白胶囊）；
  - 但 `document.querySelectorAll(...)` **读不到它的一根叶子文本** ⟹
    `A_★查看角色资产元素 = []`、`点前可见叶子文本` 里全是画布节点。

★ 假设：那个面板**不在主文档里** ⟹ 在 **iframe** 里 ⟹ ⟹ 读数器扫错了**文档**。
★ 这正是已入库那条「**读数器扫的元素类型必须与界面真实元素类型相交**」的升级版：
  这次连「元素类型」都对，但**文档**不对。

★ 本探针只做诊断：
  1. 列出所有 iframe（src / 盒 / 可见性）；
  2. 若有 iframe ⟹ 进入它，列它的可见叶子文本 ＋ 按钮；
  3. 顺便在主文档里搜「我的角色库」这行字，确认它**到底在哪个文档**。
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_iframe839.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

MAIN_SCAN = """()=>{
  const out={};
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0 && getComputedStyle(e).visibility!=='hidden';};
  out['主文档_我的角色库命中']=[];
  for(const e of document.querySelectorAll('span,div,p,button,a')){
    const t=(e.textContent||'').trim();
    if(t!=='我的角色库')continue;
    const r=e.getBoundingClientRect();
    out['主文档_我的角色库命中'].push({tag:e.tagName,
      x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),
      h:Math.round(r.height),可见:vis(e),
      cls:(e.getAttribute('class')||'').slice(0,90)});
  }
  out['主文档_iframe数']=document.querySelectorAll('iframe').length;
  out['主文档_body直接子元素数']=document.body.children.length;
  return out;}"""

FRAME_SCAN = """()=>{
  const out={};
  const realVis=(e)=>{
    for(let n=e;n&&n.nodeType===1;n=n.parentElement){
      const cs=getComputedStyle(n);
      if(cs.display==='none')return false;
      if(cs.visibility==='hidden')return false;
      if(Number(cs.opacity||'1')<=0.001)return false;
    }
    const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0;
  };
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const txt=(e)=>(e.textContent||'').trim().replace(/\\s+/g,' ');
  const leaves=[];
  for(const e of document.querySelectorAll('span,div,p,h1,h2,h3,label,button')){
    if(e.children.length>0)continue;
    if(!realVis(e))continue;
    const t=txt(e);
    if(!t||t.length>40)continue;
    leaves.push({tag:e.tagName,text:t,box:box(e),
      cls:(e.getAttribute('class')||'').slice(0,90)});
  }
  leaves.sort((a,b)=>(a.box.y-b.box.y)||(a.box.x-b.box.x));
  out['可见叶子文本']=leaves.slice(0,120);
  const imgs=[];
  for(const e of document.querySelectorAll('img')){
    if(!realVis(e))continue;
    imgs.push({alt:e.getAttribute('alt')||'',box:box(e),
      src:(e.getAttribute('src')||'').slice(-70)});
  }
  out['可见图片']=imgs.slice(0,30);
  out['含查看角色资产的元素']=[];
  for(const e of document.querySelectorAll('span,div,button,a,p')){
    if((e.textContent||'').trim()!=='查看角色资产')continue;
    const r=e.getBoundingClientRect();
    out['含查看角色资产的元素'].push({tag:e.tagName,
      cls:(e.getAttribute('class')||'').slice(0,140),
      x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),
      h:Math.round(r.height),
      祖先opacity0:!realVis(e),
      父cls:(e.parentElement&&e.parentElement.getAttribute('class')||'').slice(0,120)});
  }
  return out;}"""


def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    log = {}
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                                 locale="zh-CN")
            ctx.add_cookies([{"name": c["name"], "value": c["value"],
                              "domain": c["domain"], "path": c.get("path", "/")}
                             for c in cookies])
            pg = ctx.new_page()
            pg.set_default_timeout(20_000)
            pg.goto(URL, wait_until="domcontentloaded", timeout=90_000)
            pg.wait_for_timeout(12_000)
            el = pg.query_selector("text=下次再说")
            if el:
                el.click()
                pg.wait_for_timeout(900)
            el = pg.query_selector('[data-sidebar-btn="character-library"]')
            if el:
                bb = el.bounding_box()
                log["★入口盒"] = bb
                if bb:
                    pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
            pg.wait_for_timeout(6000)

            log["主文档"] = pg.evaluate(MAIN_SCAN)

            frames = []
            for f in pg.frames:
                if f == pg.main_frame:
                    continue
                try:
                    el = f.frame_element()
                    bb = el.bounding_box()
                except Exception:
                    bb = None
                rec = {"url": f.url, "name": f.name, "盒": bb}
                try:
                    rec["内容"] = f.evaluate(FRAME_SCAN)
                except Exception as exc:
                    rec["读不到"] = str(exc)[:160]
                frames.append(rec)
            log["★子frame数"] = len(frames)
            log["子frame"] = frames
            pg.screenshot(path="/tmp/liblib_source_iframe839.png")
            br.close()
    except Exception:
        log["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        print("主文档：", json.dumps(log.get("主文档"), ensure_ascii=False)[:600])
        print("子frame数：", log.get("★子frame数"))
        for f in log.get("子frame") or []:
            print("─" * 60)
            print(" frame:", (f.get("url") or "")[:100], "盒:", f.get("盒"))
            c = f.get("内容")
            if not c:
                print("   读不到：", f.get("读不到"))
                continue
            print("   可见叶子 %d 条；含「查看角色资产」%d 个" % (
                len(c.get("可见叶子文本") or []), len(c.get("含查看角色资产的元素") or [])))
            for x in (c.get("可见叶子文本") or [])[:20]:
                print("      ", x["text"][:26], x["box"])
            for x in (c.get("含查看角色资产的元素") or []):
                print("   ★资产元素:", json.dumps(x, ensure_ascii=False)[:260])
        if log.get("异常"):
            print("异常：", log["异常"])


if __name__ == "__main__":
    main()
