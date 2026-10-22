#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 839 源站探针③：进「官方角色库」页签 ⟹ 点开「查看角色资产」。

★ 前两趟各自暴露一条真问题（都不是「环境坏了」）：
  - v1（assets839）：读数器只扫 `span/div/p/label` ⟹ 面板里的**按钮文字**
    （性别／年龄段／文化区域／创建新角色）全都不在叶子表里 ⟹ 看上去像「面板没开」；
    ★ 而截图里面板明明开着 ⟹ ⟹ **读数器的元素类型覆盖不全**。
  - v2（iframe839）：先怀疑面板在 iframe 里 ⟹ ★ 主文档里**有**那个按钮
    （「我的角色库」BUTTON @(385,183)）⟹ ⟹ 假设被否 ⟹ 面板就在主文档。
  - ★★ 真正的关键在 826/827 的 raw 里：**「查看角色资产」记在「官方角色库」页签**
    ⟹ v1 一直在「我的角色库」页签里找 ⟹ **前提就不成立** ⟹ 找不到不是「没有」，
    是「不在这一页签」。

★ 本趟：切到「官方角色库」⟹ 找那枚元素 ⟹ **悬停它的卡片**（源站是
  `opacity-0` + `group-hover:opacity-100` ⟹ 不悬停就没法点）⟹ 点开 ⟹ **点前/点后 DOM 差分**。

★ 输出：`/tmp/liblib_source_assets839b.json`
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_assets839b.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

SNAP = """()=>{
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
  for(const e of document.querySelectorAll('span,div,p,h1,h2,h3,label,button,a')){
    if(e.children.length>0)continue;
    if(!realVis(e))continue;
    const t=txt(e);
    if(!t||t.length>40)continue;
    leaves.push({tag:e.tagName,text:t,box:box(e),
      cls:(e.getAttribute('class')||'').slice(0,90)});
  }
  leaves.sort((a,b)=>(a.box.y-b.box.y)||(a.box.x-b.box.x));
  const imgs=[];
  for(const e of document.querySelectorAll('img')){
    if(!realVis(e))continue;
    imgs.push({alt:e.getAttribute('alt')||'',box:box(e),
      src:(e.getAttribute('src')||'').slice(-70),
      cls:(e.getAttribute('class')||'').slice(0,60)});
  }
  return {url:location.href,leaves:leaves,imgs:imgs};
}"""

FIND_ASSETS = """()=>{
  const out=[];
  for(const e of document.querySelectorAll('span,div,button,a,p')){
    if((e.textContent||'').trim()!=='查看角色资产')continue;
    const r=e.getBoundingClientRect();
    const cs=getComputedStyle(e);
    out.push({tag:e.tagName,cls:(e.getAttribute('class')||'').slice(0,160),
      x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),
      h:Math.round(r.height),opacity:cs.opacity,pointerEvents:cs.pointerEvents,
      display:cs.display,visibility:cs.visibility,
      父cls:(e.parentElement&&e.parentElement.getAttribute('class')||'').slice(0,160),
      祖父cls:(e.parentElement&&e.parentElement.parentElement&&
               e.parentElement.parentElement.getAttribute('class')||'').slice(0,160)});
  }
  return out;}"""


def click_real(page, locator):
    bb = locator.bounding_box()
    if not bb:
        return False
    page.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
    return True


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
                click_real(pg, el)
            pg.wait_for_timeout(5000)

            # ── 切到「官方角色库」页签 ───────────────────────────────
            tab = pg.query_selector("button:text-is('官方角色库')")
            log["★是否找到官方角色库页签"] = tab is not None
            if tab is not None:
                click_real(pg, tab)
                pg.wait_for_timeout(4000)

            before = pg.evaluate(SNAP)
            log["A_点前_leaves"] = before["leaves"]
            log["A_点前_imgs"] = before["imgs"]
            log["A_★资产元素"] = pg.evaluate(FIND_ASSETS)
            pg.screenshot(path="/tmp/liblib_source_assets839b_before.png")

            assets = pg.evaluate(FIND_ASSETS)
            if not assets:
                log["★结论"] = "「官方角色库」页签里也没有「查看角色资产」元素 ⟹ 中止"
                br.close()
                return

            a = assets[0]
            log["★资产元素盒"] = a
            # ★ 悬停到那枚浮层所在的位置 ⟹ group-hover 生效 ⟹ 显形
            pg.mouse.move(a["x"] + a["w"] / 2, a["y"] + a["h"] / 2)
            pg.wait_for_timeout(1200)
            log["B_★悬停后_资产元素"] = pg.evaluate(FIND_ASSETS)
            pg.screenshot(path="/tmp/liblib_source_assets839b_hover.png")

            # ★ 点它（用真实鼠标点在它的盒中心）
            a2 = pg.evaluate(FIND_ASSETS)
            tgt = a2[0] if a2 else a
            pg.mouse.click(tgt["x"] + tgt["w"] / 2, tgt["y"] + tgt["h"] / 2)
            pg.wait_for_timeout(4000)
            after = pg.evaluate(SNAP)
            log["C_点后_leaves"] = after["leaves"]
            log["C_点后_imgs"] = after["imgs"]
            log["C_★URL前"] = before["url"]
            log["C_★URL后"] = after["url"]
            pg.screenshot(path="/tmp/liblib_source_assets839b_after.png")

            b_leaves = {(x["text"], x["box"]["x"], x["box"]["y"]) for x in before["leaves"]}
            a_leaves = {(x["text"], x["box"]["x"], x["box"]["y"]) for x in after["leaves"]}
            log["D_★新增的可见文本"] = sorted(a_leaves - b_leaves)[:120]
            log["D_★消失的可见文本"] = sorted(b_leaves - a_leaves)[:60]
            log["D_★新增的图片"] = [
                i for i in after["imgs"]
                if (i["alt"], i["box"]["x"], i["box"]["y"]) not in
                {(x["alt"], x["box"]["x"], x["box"]["y"]) for x in before["imgs"]}][:20]
            br.close()
    except Exception:
        log["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        for k in ("★是否找到官方角色库页签", "★资产元素盒", "★结论"):
            if k in log:
                print("%-22s %r" % (k, log[k]))
        for k in ("A_★资产元素", "B_★悬停后_资产元素"):
            v = log.get(k) or []
            print("%-22s %d 个" % (k, len(v)))
            for x in v[:4]:
                print("      ", json.dumps(x, ensure_ascii=False)[:230])
        for k in ("D_★新增的可见文本", "D_★新增的图片"):
            v = log.get(k) or []
            print("%-22s %d 条" % (k, len(v)))
            for x in v[:40]:
                print("      ", x)
        if log.get("异常"):
            print("异常：", log["异常"])


if __name__ == "__main__":
    main()
