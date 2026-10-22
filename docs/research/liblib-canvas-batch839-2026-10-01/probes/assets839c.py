#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 839 源站探针④：资产视图之后的**两个**入口。

★ 探针③（assets839b）已经测清：「查看角色资产」点开 = **角色资产视图**
  （4 张图 ＋「选择角色音色」＋ 角色名），底部 CTA 换成
  〔创建新角色〕＋〔添加到画布〕＋〔编辑角色〕。

★ 本趟继续往下追两件事：
  ① 点「**选择角色音色**」→ 出现什么？
  ② 点「**编辑角色**」→ 出现什么？（★ 这才是那个「**大编辑器**」吗？）
    ⟹ 顺便记 URL 有没有变（可能跳路由）。

★ 方法仍是**点前/点后 DOM 差分** ＋ 绝对几何 ＋ 截图。
★ 只点这两枚，不点任何付费/生成/删除。

★ 输出：`/tmp/liblib_source_assets839c.json`
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_assets839c.json")
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
      cls:(e.getAttribute('class')||'').slice(0,80)});
  }
  leaves.sort((a,b)=>(a.box.y-b.box.y)||(a.box.x-b.box.x));
  const btns=[];
  for(const e of document.querySelectorAll('button,[role=button]')){
    if(!realVis(e))continue;
    btns.push({text:txt(e).slice(0,26),aria:e.getAttribute('aria-label')||'',
      box:box(e),cls:(e.getAttribute('class')||'').slice(0,70)});
  }
  btns.sort((a,b)=>(a.box.y-b.box.y)||(a.box.x-b.box.x));
  const imgs=[];
  for(const e of document.querySelectorAll('img')){
    if(!realVis(e))continue;
    imgs.push({alt:e.getAttribute('alt')||'',box:box(e),
      cls:(e.getAttribute('class')||'').slice(0,50)});
  }
  return {url:location.href,leaves:leaves,btns:btns,imgs:imgs};
}"""


def click_text(page, label, exact=True):
    """按可见文本点一枚元素（真实鼠标）。返回是否点到。"""
    for e in page.query_selector_all("span,div,button,a,p"):
        t = (e.text_content() or "").strip()
        if exact:
            if t != label:
                continue
        else:
            if label not in t:
                continue
        bb = e.bounding_box()
        if not bb:
            continue
        page.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
        return True
    return False


# ★ 「查看角色资产」浮层的**类名**里写死了 `pointer-events-none` ⟹
#   ★★ 直接点它 ⇒ 事件**穿透**到下面的卡片 ⟹ 什么也不会发生；
#   ★ 正解是：★ **先悬停**（让 `group-hover` 把 `pointer-events` 放开 ＋ 让它显形）
#   ⟹ **等样式生效**（≥1s）⟹ **再点**。上一趟探针③ 正是这么成功的。
FIND_ASSETS_BTN = """()=>{
  const out=[];
  for(const e of document.querySelectorAll('button')){
    if((e.textContent||'').trim()!=='查看角色资产')continue;
    const r=e.getBoundingClientRect();
    const cs=getComputedStyle(e);
    out.push({x:Math.round(r.x),y:Math.round(r.y),
      w:Math.round(r.width),h:Math.round(r.height),
      opacity:cs.opacity,pointerEvents:cs.pointerEvents,
      cls:(e.getAttribute('class')||'').slice(0,200)});
  }
  return out;}"""


def open_asset_view(page):
    """按探针③ 已验证的顺序：悬停 ⟹ 等 ⟹ 点。返回是否成功进入资产视图。"""
    btns = page.evaluate(FIND_ASSETS_BTN)
    if not btns:
        return False, "找不到「查看角色资产」按钮"
    b = btns[0]
    page.mouse.move(b["x"] + b["w"] / 2, b["y"] + b["h"] / 2)
    page.wait_for_timeout(1400)
    btns2 = page.evaluate(FIND_ASSETS_BTN)
    b2 = btns2[0] if btns2 else b
    page.mouse.click(b2["x"] + b2["w"] / 2, b2["y"] + b2["h"] / 2)
    page.wait_for_timeout(3000)
    return True, {"悬停前": b, "悬停后": b2}


def diff(a, b):
    ka = {(x["text"], x["box"]["x"], x["box"]["y"]) for x in a}
    kb = {(x["text"], x["box"]["x"], x["box"]["y"]) for x in b}
    return sorted(kb - ka), sorted(ka - kb)


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
                if bb:
                    pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
            pg.wait_for_timeout(5000)

            tab = pg.query_selector("button:text-is('官方角色库')")
            if tab:
                bb = tab.bounding_box()
                if bb:
                    pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
                pg.wait_for_timeout(4000)

            # ★ 进资产视图：★ **悬停 → 等 → 点**（浮层是 pointer-events-none）
            ok, info = open_asset_view(pg)
            log["★是否进入资产视图"] = ok
            log["★浮层读数"] = info
            s0 = pg.evaluate(SNAP)
            log["A_资产视图_leaves"] = s0["leaves"]
            log["A_资产视图_imgs"] = s0["imgs"]
            log["A_资产视图_btns"] = s0["btns"]
            log["A_★资产视图是否含选择角色音色"] = any(
                x["text"] == "选择角色音色" for x in s0["leaves"])
            pg.screenshot(path="/tmp/liblib_source_assets839c_assets.png")

            # ── ① 「选择角色音色」 ──────────────────────────────────
            log["★是否点到选择角色音色"] = click_text(pg, "选择角色音色")
            pg.wait_for_timeout(2500)
            s1 = pg.evaluate(SNAP)
            add1, del1 = diff(s0["leaves"], s1["leaves"])
            log["B_音色_新增文本"] = add1[:80]
            log["B_音色_消失文本"] = del1[:40]
            log["B_音色_新增按钮"] = [
                b for b in s1["btns"]
                if (b["text"], b["box"]["x"], b["box"]["y"]) not in
                {(x["text"], x["box"]["x"], x["box"]["y"]) for x in s0["btns"]}][:40]
            log["B_音色_URL前"] = s0["url"]
            log["B_音色_URL后"] = s1["url"]
            pg.screenshot(path="/tmp/liblib_source_assets839c_voice.png")

            # ★ 退回资产视图（按 Escape，若无效就重新走一遍悬停→点）
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(1500)
            s1b = pg.evaluate(SNAP)
            if "选择角色音色" not in [x["text"] for x in s1b["leaves"]]:
                log["★Escape没能退回资产视图"] = True
                ok2, _ = open_asset_view(pg)
                log["★重新进资产视图"] = ok2
                s1b = pg.evaluate(SNAP)

            # ── ② 「编辑角色」 ─────────────────────────────────────
            log["★是否点到编辑角色"] = click_text(pg, "编辑角色")
            pg.wait_for_timeout(4000)
            s2 = pg.evaluate(SNAP)
            add2, del2 = diff(s1b["leaves"], s2["leaves"])
            log["C_编辑_新增文本"] = add2[:120]
            log["C_编辑_消失文本"] = del2[:40]
            log["C_编辑_URL前"] = s1b["url"]
            log["C_编辑_URL后"] = s2["url"]
            log["C_编辑_leaves"] = s2["leaves"]
            log["C_编辑_btns"] = s2["btns"]
            log["C_编辑_imgs"] = s2["imgs"]
            pg.screenshot(path="/tmp/liblib_source_assets839c_edit.png")
            br.close()
    except Exception:
        log["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        for k in ("★是否进入资产视图", "★是否点到选择角色音色",
                  "A_★资产视图是否含选择角色音色",
                  "★Escape没能退回资产视图", "★是否点到编辑角色",
                  "B_音色_URL前", "B_音色_URL后", "C_编辑_URL前", "C_编辑_URL后"):
            if k in log:
                print("%-26s %r" % (k, log[k]))
        print("%-26s %r" % ("★浮层读数", log.get("★浮层读数")))
        for k in ("B_音色_新增文本", "C_编辑_新增文本"):
            v = log.get(k) or []
            print("%-26s %d 条" % (k, len(v)))
            for x in v[:40]:
                print("      ", x)
        if log.get("异常"):
            print("异常：", log["异常"])


if __name__ == "__main__":
    main()
