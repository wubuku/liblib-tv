#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 829 收尾：把源站测试项目的「场景缩放」恢复成原值 3。

★ 上一轮把它从 3 改成了 3.1（测「关台重开/刷新后留不留」用的）⟹ 必须改回去，
  别把用户的测试项目留在改脏的状态里。
★ FOV 已经恢复成 67（上一轮最后一步），本轮**顺带复核**。
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_desk829_restore.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

READ_ZOOM = """()=>{
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
    if(e.min!=='0.1'||e.max!=='10')continue;
    const b=box(e);
    let label=null;
    for(const r of rows){
      if(r.box.y+r.box.h<=b.y+2 && r.box.x<b.x+b.w && b.x<r.box.x+r.box.w){
        if(!label||r.box.y>label.box.y)label=r;
      }
    }
    out.push({label:label?label.t:null,box:b,value:e.value,min:e.min,max:e.max,step:e.step});
  }
  return out;
}"""


def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    out = {}
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
        card = page.locator(".react-flow__node-director-console-3d").first
        card.hover()
        page.wait_for_timeout(600)
        page.locator(
            ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
        page.wait_for_timeout(6_000)
        rs = page.evaluate(READ_ZOOM)
        out["开台后"] = rs
        rng = rs[0] if rs else None
        tries = []
        if rng:
            before = rng["value"]
            for f in (0.293, 0.29, 0.28):
                b = rng["box"]
                x = b["x"] + int(b["w"] * f)
                y = b["y"] + b["h"] // 2
                page.mouse.move(x, y)
                page.mouse.down()
                page.wait_for_timeout(120)
                page.mouse.up()
                page.wait_for_timeout(800)
                now = page.evaluate(READ_ZOOM)
                v = now[0]["value"] if now else None
                tries.append({"frac": f, "value_after": v})
                if v == "3":
                    break
            out["恢复动作"] = tries
            out["恢复后"] = page.evaluate(READ_ZOOM)
            out["before"] = before
        ctx.close()
        br.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
