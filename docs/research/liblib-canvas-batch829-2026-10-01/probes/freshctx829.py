#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 829 收尾（v4）：**全新 context** 读源站 ⟹ 判定「场景缩放」到底存在哪。

★ 为什么要全新 context：每个探针都是新浏览器 context（localStorage 独立）。
  若「场景缩放」只存在**客户端**（localStorage），那么：
    - 同一 context 内：改值 → 刷新页面 → 读回**新值**（本地还在）
    - 全新 context：读回**服务端**的值（本地没了）
  ⟹ 我前两轮「复原」可能**只改了客户端**，服务端仍是脏的 3.1。
★ 本探针：全新 context → 开台 → 读「场景缩放」与「FOV」⟹
  - 读到 3  ⟹ 服务端干净（本地那份也正好是 3）
  - 读到 3.1 ⟹ 服务端**仍脏** ⟹ 需要在**能触发落盘**的时机再复原一次
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_desk829_freshctx.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

READ_RANGES = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const rows=Array.from(document.querySelectorAll('div,span,label,p'))
    .filter(e=>{const t=(e.textContent||'').trim();
      if(e.children.length!==0||!t||t.length>=20)return false;
      for(let n=e;n&&n.nodeType===1;n=n.parentElement){
        const cs=getComputedStyle(n);
        if(cs.display==='none'||cs.visibility==='hidden')return false;
        if(Number(cs.opacity||'1')<=0.001)return false;
      }
      return true;})
    .map(e=>({t:(e.textContent||'').trim(),box:box(e)}));
  const out=[];
  for(const e of document.querySelectorAll('input[type=range]')){
    const b=box(e);
    let label=null;
    for(const r of rows){
      if(r.box.y+r.box.h<=b.y+2 && r.box.x<b.x+b.w && b.x<r.box.x+r.box.w){
        if(!label||r.box.y>label.box.y)label=r;
      }
    }
    out.push({label:label?label.t:null,box:b,value:e.value,
              min:e.min,max:e.max,step:e.step});
  }
  return out;
}"""


def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(600)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(6_000)


def pick(ranges, key):
    for r in ranges:
        if r["label"] and key in r["label"]:
            return r
    return None


def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    out = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        # ★ 全新 context ①
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
        rs = page.evaluate(READ_RANGES)
        z = pick(rs, "场景缩放")
        out["context1_场景缩放"] = z["value"] if z else None
        out["context1_所有range"] = [{"label": r["label"], "value": r["value"],
                                      "min": r["min"], "max": r["max"]}
                                     for r in rs]
        page.locator("text=机位1").first.click()
        page.wait_for_timeout(2_500)
        rs2 = page.evaluate(READ_RANGES)
        f = pick(rs2, "FOV")
        out["context1_FOV"] = f["value"] if f else None
        out["★localStorage键"] = page.evaluate(
            "() => Object.keys(localStorage).filter(k=>/director|scene|zoom|canvas/i.test(k))")
        ctx.close()

        # ★ 全新 context ②（再读一次，确认不是偶然）
        ctx2 = br.new_context(viewport={"width": 1920, "height": 1080},
                               locale="zh-CN")
        ctx2.add_cookies([{"name": c["name"], "value": c["value"],
                           "domain": c["domain"], "path": c.get("path", "/"),
                           "expires": c.get("expires", -1),
                           "httpOnly": c.get("httpOnly", False),
                           "secure": c.get("secure", False),
                           "sameSite": c.get("sameSite", "Lax")} for c in cookies])
        page2 = ctx2.new_page()
        page2.goto(URL, wait_until="domcontentloaded", timeout=90_000)
        page2.wait_for_timeout(12_000)
        open_desk(page2)
        rs3 = page2.evaluate(READ_RANGES)
        z2 = pick(rs3, "场景缩放")
        out["context2_场景缩放"] = z2["value"] if z2 else None
        page2.locator("text=机位1").first.click()
        page2.wait_for_timeout(2_500)
        rs4 = page2.evaluate(READ_RANGES)
        f2 = pick(rs4, "FOV")
        out["context2_FOV"] = f2["value"] if f2 else None
        ctx2.close()
        br.close()
    out["★服务端判定"] = {
        "场景缩放": out["context1_场景缩放"],
        "FOV": out["context1_FOV"],
        "两次一致": out["context1_场景缩放"] == out["context2_场景缩放"],
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1)[:3000])


if __name__ == "__main__":
    main()
