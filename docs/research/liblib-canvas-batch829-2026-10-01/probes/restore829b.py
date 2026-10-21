#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 829 收尾（v2）：把源站测试项目**真正**复原，并测出「滑杆改动什么时候落盘」。

★ ★★ 上一轮的「复原」只改了客户端、**没落盘**：复原后立刻关掉浏览器 ⟹ 再开时
  读到的还是脏值（FOV 34、场景缩放 3.1）⟹ ⟹ **源站的滑杆改动不是即时落盘的**。
★ 本轮：改值 → **干净地关台** → **刷新页面** → 重开 → **回读** ⟹ 读到 67/3 才算复原成功。
★ 同时记录「从改值到落盘」需要什么动作（干净关台 / 等待 / 重新开台）。
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_desk829_restore2.json")
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


def close_desk(page):
    page.locator("[aria-label='关闭']:visible").first.click()
    page.wait_for_timeout(3_000)


def pick(ranges, key, minv=None, maxv=None):
    for r in ranges:
        if r["label"] and key in r["label"]:
            if minv is not None and r["min"] != minv:
                continue
            if maxv is not None and r["max"] != maxv:
                continue
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


def set_to(page, ranges, key, want, minv=None, maxv=None):
    """把 range 调到目标值（真实点击 + 回读）。"""
    rng = pick(ranges, key, minv, maxv)
    if not rng:
        return {"error": "no range %s" % key}
    span = float(rng["max"]) - float(rng["min"])
    frac = (float(want) - float(rng["min"])) / span
    tries = []
    for f in (frac, frac - 0.01, frac + 0.01, frac - 0.02):
        act = click_range(page, rng, max(0.0, min(1.0, f)))
        now = pick(page.evaluate(READ_RANGES), key, minv, maxv)
        v = now["value"] if now else None
        tries.append({**act, "value_after": v})
        if v == str(want) or (want == 3 and v == "3.0"):
            return {"label": key, "want": want, "got": v, "tries": tries}
    return {"label": key, "want": want, "got": None, "tries": tries,
            "★没调到": True}


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
        out["开台后"] = {"zoom": pick(rs, "场景缩放"),
                         "fov": pick(rs, "FOV", "15", "90")}
        # ① 场景缩放 → 3（3D场景面板下，FOV 此刻还没显示）
        out["复原缩放"] = set_to(page, rs, "场景缩放", 3)
        # ② FOV → 67（选中机位1 后属性面板才有 FOV）
        page.locator("text=机位1").first.click()
        page.wait_for_timeout(2_500)
        out["复原FOV"] = set_to(page, page.evaluate(READ_RANGES), "FOV", 67,
                                minv="15", maxv="90")
        # ③ **干净关台**（这才是落盘的触发点？）
        close_desk(page)
        page.wait_for_timeout(3_000)
        # ④ 刷新页面 → 重开 → 回读
        page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(12_000)
        open_desk(page)
        rs2 = page.evaluate(READ_RANGES)
        zoom_after_reload = pick(rs2, "场景缩放")
        # ★ FOV 只在**选中机位1**后的属性面板里 ⟹ 先选机位再读
        page.locator("text=机位1").first.click()
        page.wait_for_timeout(2_500)
        rs3 = page.evaluate(READ_RANGES)
        out["刷新后"] = {"zoom": zoom_after_reload,
                         "fov": pick(rs3, "FOV", "15", "90")}
        out["回读"] = {
            "场景缩放": (out["刷新后"]["zoom"] or {}).get("value"),
            "FOV": (out["刷新后"]["fov"] or {}).get("value"),
        }
        out["★已复原"] = (out["回读"]["场景缩放"] == "3"
                          and out["回读"]["FOV"] == "67")
        page.screenshot(path="/tmp/liblib_source_desk829_restored.png")
        ctx.close()
        br.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
