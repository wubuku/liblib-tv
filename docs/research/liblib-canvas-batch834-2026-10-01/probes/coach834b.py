#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 834：源站探针二 —— 把引导气泡的 **5 步正文 ＋ 每步几何 ＋ 被高亮的目标**读全。

★ 第一版（`probes/coach834.py`）的不足（都记在 README）：
  ① 我的 host 定位器只要「同时含跳过 ＋ 下一步」的祖先 ⟹ 抓到的是**按钮行**
     （class `mt-3 flex items-center justify-between gap-1`）⟹ **没抓到引导正文**；
  ② 第 5 步的按钮行**没有**「跳过／下一步」⟹ 定位器直接报「没找到」⟹ 第 5 步**没采到**。

★ 这一版的定位规则（**不靠 class 名**）：
  从「n/5」那个元素往上走 ⟹ 找**第一个**同时满足两个条件的祖先：
    (a) 它的后代里有一个**长度 > 6 的文本块**（= 引导正文）；
    (b) 它还包含那个「n/5」元素。
  ⟹ 那个祖先就是气泡容器 ⟹ 正文、按钮、盒都能读到。

★ 顺带记录**每步被高亮的目标**：找带非默认 `box-shadow`／`outline` 的可见元素
  ⟹ 引导通常会给一个目标加一圈光晕。

★ 走完 5 步后引导会消失（这就是「完成」）；本探针**不点「跳过」**。
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_coach834b.json")
SHOTS = pathlib.Path("/tmp/liblib_source_coach834b")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

DUMP_GUIDE = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
  const all=Array.from(document.querySelectorAll('body *'));
  const stepEls=all.filter(e=>{
    if(e.childElementCount!==0) return false;
    return /^\\d\\s*\\/\\s*\\d+$/.test((e.textContent||'').trim());
  }).filter(vis);
  if(!stepEls.length) return {found:false, reason:'没有「n/5」步数元素'};
  const stepEl=stepEls[stepEls.length-1];
  // ★ 向上找第一个「含长度>6 的文本块」的祖先
  let node=stepEl, host=null;
  for(let i=0;i<10 && node;i++){
    const longTexts=Array.from(node.querySelectorAll('div,span,p')).filter(vis)
      .map(e=>(e.textContent||'').trim())
      .filter(t=>t.length>6 && t.length<120);
    if(longTexts.length) {host=node; break;}
    node=node.parentElement;
  }
  if(!host) return {found:false, reason:'没找到含正文的祖先', step:stepEl.textContent};
  const texts=Array.from(host.querySelectorAll('div,span,p')).filter(vis)
    .filter(e=>e.childElementCount===0)
    .map(e=>({t:(e.textContent||'').trim(), box:box(e)}))
    .filter(x=>x.t);
  const buttons=Array.from(host.querySelectorAll('button')).filter(vis)
    .map(b=>({t:(b.textContent||'').trim(), box:box(b),
              cls:String(b.className||'').slice(0,130)}));
  const cs=getComputedStyle(host);
  return {found:true, step:(stepEl.textContent||'').trim(),
          hostBox:box(host), texts, buttons,
          hostClass:String(host.className||'').slice(0,260),
          position:cs.position, zIndex:cs.zIndex, top:cs.top, left:cs.left};
}"""

# ★ 被高亮的目标（引导一般给一个元素加光晕）
DUMP_RING = """()=>{
  const out=[];
  for(const e of document.querySelectorAll('body *')){
    const r=e.getBoundingClientRect();
    if(r.width<=0||r.height<=0) continue;
    const cs=getComputedStyle(e);
    const sh=cs.boxShadow||'';
    if(sh && sh!=='none' && sh.indexOf('rgba(0, 0, 0, 0)')===-1){
      out.push({tag:e.tagName, cls:String(e.className||'').slice(0,80),
                box:{x:Math.round(r.x),y:Math.round(r.y),
                     w:Math.round(r.width),h:Math.round(r.height)},
                shadow:sh.slice(0,110), outline:cs.outline});
    }
  }
  return out.slice(0,20);
}"""


def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(800)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(9_000)


def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    out = {}
    SHOTS.mkdir(exist_ok=True)
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                             locale="zh-CN")
        ctx.add_cookies([{
            "name": c["name"], "value": c["value"], "domain": c["domain"],
            "path": c.get("path", "/"), "expires": c.get("expires", -1),
            "httpOnly": c.get("httpOnly", False),
            "secure": c.get("secure", False),
            "sameSite": c.get("sameSite", "Lax"),
        } for c in cookies])
        page = ctx.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
        page.wait_for_timeout(9_000)
        open_desk(page)
        try:
            page.locator("button[aria-label='动画时间轴']").first.click()
            page.wait_for_timeout(3_000)
        except Exception as exc:  # noqa: BLE001
            out["★开时间轴异常"] = repr(exc)[:200]

        steps = []
        for i in range(8):
            g = page.evaluate(DUMP_GUIDE)
            ring = page.evaluate(DUMP_RING)
            steps.append({"轮次": i, "guide": g, "高亮": ring})
            page.screenshot(path=str(SHOTS / ("834b_step_%d.png" % i)))
            if not g.get("found"):
                break
            # ★ 推进按钮：文案含「下一步」或「完成」（第 5 步可能没有「跳过」）
            labels = [b.get("t") or "" for b in g.get("buttons") or []]
            advance = None
            for want in ("下一步", "完成", "知道了", "开始"):
                hit = [b for b in g["buttons"] if want in (b.get("t") or "")]
                if hit:
                    advance = hit[0]
                    break
            out.setdefault("每步按钮文案", []).append(labels)
            if advance is None:
                break
            page.get_by_role("button", name=advance["t"], exact=True).first.click()
            page.wait_for_timeout(1_600)
        out["①逐步"] = steps
        out["②走完后"] = page.evaluate(DUMP_GUIDE)
        ctx.close()
        br.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已落盘：", OUT)
    for s in out.get("①逐步") or []:
        g = s["guide"]
        if not g.get("found"):
            print("  轮%s：%s" % (s["轮次"], g.get("reason")))
            continue
        body = [x["t"] for x in g["texts"] if x["t"] not in ("跳过", "下一步", "完成")]
        print("  轮%s 步数=%s 容器盒=%s" % (s["轮次"], g["step"], g["hostBox"]))
        print("      正文=%s" % body[:2])
        print("      按钮=%s" % [b["t"] for b in g["buttons"]])


if __name__ == "__main__":
    main()
