#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 829 收尾（v3）：把**场景缩放**真正复原成 3，并回读验证。

★ 为什么上一轮没成功：复原时右栏停在**机位1 的属性面板**上 ⟹ 「场景缩放」那枚 range
  **根本不在 DOM** ⟹ 按旧坐标去点，点了个寂寞。
★ 做法：先让右栏回到**「3D场景」**页签（点顶部「导演视角」⟹ 取消选中机位），
  再点那枚 range，调完**干净关台 → 刷新页面 → 重开 → 回读**。
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_desk829_restore3.json")
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


def click_range(page, rng, frac):
    b = rng["box"]
    x = b["x"] + int(b["w"] * frac)
    y = b["y"] + b["h"] // 2
    page.mouse.move(x, y)
    page.mouse.down()
    page.wait_for_timeout(120)
    page.mouse.up()
    page.wait_for_timeout(800)
    return {"frac": frac, "at": [x, y]}


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
        open_desk(page)
        rs = page.evaluate(READ_RANGES)
        out["开台后_3D场景面板"] = pick(rs, "场景缩放")
        out["★场景缩放此刻在不在DOM"] = out["开台后_3D场景面板"] is not None

        rng = out["开台后_3D场景面板"]
        if rng:
            span = float(rng["max"]) - float(rng["min"])
            frac = (3.0 - float(rng["min"])) / span
            tries = []
            for f in (frac, frac - 0.01, frac + 0.01):
                act = click_range(page, rng, max(0.0, min(1.0, f)))
                now = pick(page.evaluate(READ_RANGES), "场景缩放")
                v = now["value"] if now else None
                tries.append({**act, "value_after": v})
                if v == "3":
                    break
            out["复原动作"] = tries
            out["改后"] = pick(page.evaluate(READ_RANGES), "场景缩放")

        # 干净关台 → 刷新 → 重开 → 回读
        page.locator("[aria-label='关闭']:visible").first.click()
        page.wait_for_timeout(3_000)
        page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(12_000)
        open_desk(page)
        rs2 = page.evaluate(READ_RANGES)
        z = pick(rs2, "场景缩放")
        out["回读_场景缩放"] = z["value"] if z else None
        # FOV 也复核一下
        page.locator("text=机位1").first.click()
        page.wait_for_timeout(2_500)
        rs3 = page.evaluate(READ_RANGES)
        f = pick(rs3, "FOV")
        out["回读_FOV"] = f["value"] if f else None
        out["★已复原"] = (out["回读_场景缩放"] == "3" and out["回读_FOV"] == "67")
        page.screenshot(path="/tmp/liblib_source_desk829_restored3.png")
        ctx.close()
        br.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
