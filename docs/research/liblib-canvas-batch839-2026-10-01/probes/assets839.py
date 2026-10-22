#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 839 源站探针①：「查看角色资产」点开之后**是什么**。

★ 为什么要探这个：仓库里已有的源站 raw（batch 826／827）**只记到了「查看角色资产」这行文字**
  （在「官方角色库」页签的可见叶子文本里）⟹ **从没测过点开它会发生什么** ⟹
  而 clone 侧那枚入口目前**只是卡片里的悬停浮层**（点它只会选中卡片）⟹
  ⇒ 本探针要回答：**源站点开它 → 出现的是什么面板？**

★ 三条纪律：
  1. ★ **悬停才显形**（源站是 `opacity-0` + `group-hover:opacity-100`）⟹
     必须**真实鼠标悬停**才能点到 ⟹ 且读数必须用**祖先 opacity 一起算**的可见性
     （★ 否则会读到「在 DOM 里但屏幕上没有」的元素 —— batch 827 已踩过这个坑）；
  2. ★ **点前/点后做 DOM 差分** ⟹ 「多出来的东西」就是它点开的面板 ⟹
     而不是靠「我记得源站长什么样」去猜；
  3. ★ **只点这一枚**，不点任何生成/付费/删除按钮。

★ 输出：`/tmp/liblib_source_assets839.json`
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_assets839.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 可见性：**祖先链**的 display/visibility/opacity 一起算 ⟹ 祖先 opacity:0 也不算可见
VIS = """
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
"""

# ★ 快照：可见叶子文本 ＋ 可见按钮 ＋ 可见 input ＋ 图片
SNAP = """()=>{
  %s
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const txt=(e)=>(e.textContent||'').trim().replace(/\\s+/g,' ');
  const leaves=[];
  for(const e of document.querySelectorAll('span,div,p,h1,h2,h3,label')){
    if(e.children.length>0)continue;
    if(!realVis(e))continue;
    const t=txt(e);
    if(!t||t.length>40)continue;
    leaves.push({tag:e.tagName,text:t,box:box(e),
      cls:(e.getAttribute('class')||'').slice(0,80)});
  }
  leaves.sort((a,b)=>(a.box.y-b.box.y)||(a.box.x-b.box.x));
  const btns=[];
  for(const e of document.querySelectorAll('button,[role=button],[role=tab]')){
    if(!realVis(e))continue;
    btns.push({text:txt(e).slice(0,30),aria:e.getAttribute('aria-label')||'',
      role:e.getAttribute('role')||'',box:box(e),
      cls:(e.getAttribute('class')||'').slice(0,80)});
  }
  btns.sort((a,b)=>(a.box.y-b.box.y)||(a.box.x-b.box.x));
  const inputs=[];
  for(const e of document.querySelectorAll('input,textarea,select')){
    if(!realVis(e))continue;
    inputs.push({tag:e.tagName,type:e.getAttribute('type')||'',
      value:(e.value||'').slice(0,40),aria:e.getAttribute('aria-label')||'',
      placeholder:e.getAttribute('placeholder')||'',box:box(e)});
  }
  return {url:location.href,leaves:leaves,btns:btns,inputs:inputs,
          title:document.title};
}""" % VIS


def click_real(page, locator):
    bb = locator.bounding_box()
    if not bb:
        return False
    page.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
    return True


def find_assets_el(page):
    """找出所有「查看角色资产」元素（含未显形的），返回它们的 class 与盒。"""
    return page.evaluate("""()=>{
      const out=[];
      for(const e of document.querySelectorAll('span,div,button,a,p')){
        const t=(e.textContent||'').trim();
        if(t!=='查看角色资产')continue;
        const r=e.getBoundingClientRect();
        let op='1';
        for(let n=e;n&&n.nodeType===1;n=n.parentElement){
          const cs=getComputedStyle(n);
          if(Number(cs.opacity||'1')<=0.001){op='0';break;}
        }
        out.push({tag:e.tagName,cls:(e.getAttribute('class')||'').slice(0,120),
          x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),
          h:Math.round(r.height),祖先opacity0:op==='0',
          pe:(e.parentElement&&e.parentElement.getAttribute('class')||'').slice(0,100)});
      }
      return out;}""")


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
            for label in ("下次再说",):
                el = pg.query_selector("text=%s" % label)
                if el:
                    el.click()
                    pg.wait_for_timeout(900)
                    break

            el = pg.query_selector('[data-sidebar-btn="character-library"]')
            log["★是否找到角色库入口"] = bool(el)
            if el:
                click_real(pg, el)
            pg.wait_for_timeout(5000)

            # ── 我的角色库页签 ──────────────────────────────────────
            before = pg.evaluate(SNAP)
            log["A_点前_我的角色库"] = before
            log["A_★查看角色资产元素"] = find_assets_el(pg)
            pg.screenshot(path="/tmp/liblib_source_assets839_mine_before.png")

            # ★ 悬停第一张卡片 ⟹ 浮层显形 ⟹ 再找一次
            card = pg.query_selector('[data-character-strip-card]')
            if card is None:
                card = pg.query_selector('img[alt]')
            log["★找到的卡片选择器"] = "data-character-strip-card" if card is not None else "img[alt]"
            if card is not None:
                bb = card.bounding_box()
                log["★卡片盒"] = bb
                if bb:
                    pg.mouse.move(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
                    pg.wait_for_timeout(1200)
            log["B_★悬停后_查看角色资产元素"] = find_assets_el(pg)
            pg.screenshot(path="/tmp/liblib_source_assets839_mine_hover.png")

            # ★ 点它
            target = None
            for e in pg.query_selector_all("span,div,button,a,p"):
                if (e.text_content() or "").strip() == "查看角色资产":
                    target = e
                    break
            log["★是否找到可点的目标"] = target is not None
            if target is not None:
                bb = target.bounding_box()
                log["★目标盒"] = bb
                if bb:
                    pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
                    pg.wait_for_timeout(3500)
            after = pg.evaluate(SNAP)
            log["C_点后"] = after
            pg.screenshot(path="/tmp/liblib_source_assets839_mine_after.png")

            # ── DOM 差分 ────────────────────────────────────────────
            b_leaves = {(x["text"], x["box"]["x"], x["box"]["y"]) for x in before["leaves"]}
            a_leaves = {(x["text"], x["box"]["x"], x["box"]["y"]) for x in after["leaves"]}
            log["D_★新增的可见叶子文本"] = sorted(a_leaves - b_leaves)[:80]
            log["D_★消失的可见叶子文本"] = sorted(b_leaves - a_leaves)[:40]
            b_btn = {(x["text"], x["box"]["x"], x["box"]["y"]) for x in before["btns"]}
            a_btn = {(x["text"], x["box"]["x"], x["box"]["y"]) for x in after["btns"]}
            log["D_★新增的按钮"] = sorted(a_btn - b_btn)[:60]
            log["D_★URL是否变了"] = (before["url"] != after["url"])
            log["D_★URL前"] = before["url"]
            log["D_★URL后"] = after["url"]
            log["D_★点后input"] = after["inputs"]
            br.close()
    except Exception:
        log["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        for k in ("★是否找到角色库入口", "★找到的卡片选择器", "★是否找到可点的目标",
                  "D_★URL是否变了", "D_★新增的可见叶子文本", "D_★新增的按钮"):
            v = log.get(k)
            if isinstance(v, list):
                print("%-24s %d 条" % (k, len(v)))
                for x in v[:25]:
                    print("      ", x)
            else:
                print("%-24s %r" % (k, v))
        if log.get("异常"):
            print("异常：", log["异常"])


if __name__ == "__main__":
    main()
