#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 830 源站撤销探针（v6 · 收官）：撤销能不能撤**改名**（与 clone 828 S4 同口径）。

★ 沿用 recon830c 里那套**已验证可用**的可见性判定（祖先 opacity/visibility + 矩形）。
★ 流程：改名 → 焦点挪到树里的机位行 → 按 Z → 读名字 → 再按 Z → 读名字
  → **复原**（改回「机位1」）→ 干净关台 → 刷新 → 全新 context 回读。
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_desk830_rename_undo2.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

READ = """()=>{
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
  // ★ CSS 的 `input[type=text]` 匹配的是**属性**⟹ 源站那个名称输入**没有 type 属性**
  //   （它的 type *property* 默认是 text）⟹ 必须用 property 判定
  const nameInput=Array.from(document.querySelectorAll('input'))
    .filter(e=>e.type==='text'&&realVis(e)
      &&e.getBoundingClientRect().x>1600
      &&e.getBoundingClientRect().y<400)
    .map(e=>({value:e.value,box:box(e)}));
  const fov=document.querySelector('input[type=range][min="15"][max="90"]');
  return {names:nameInput,
          fov:fov?{value:fov.value}:null,
          active:(()=>{const a=document.activeElement;
            return a?{tag:a.tagName,text:(a.textContent||'').trim().slice(0,14),
                      type:a.type||''}:null;})()};
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


def select_camera(page):
    page.locator("text=机位1").first.click()
    page.wait_for_timeout(2_000)


def name_value(page):
    st = page.evaluate(READ)
    ns = st.get("names") or []
    return ns[0]["value"] if ns else None


def set_name(page, value):
    st = page.evaluate(READ)
    ns = st.get("names") or []
    if not ns:
        return {"error": "no name input"}
    before = ns[0]["value"]
    b = ns[0]["box"]
    page.mouse.click(b["x"] + 12, b["y"] + b["h"] // 2)
    page.wait_for_timeout(500)
    page.keyboard.press("Meta+a")
    page.wait_for_timeout(200)
    page.keyboard.type(value, delay=80)
    page.wait_for_timeout(600)
    page.keyboard.press("Enter")
    page.wait_for_timeout(1_800)
    return {"before": before, "typed": value, "after": name_value(page)}


def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    out = {}
    try:
        run(out, cookies)
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)


def run(out, cookies):
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
        select_camera(page)
        out["①初始"] = page.evaluate(READ)
        out["②改名"] = set_name(page, "机位1-830")
        out["③改名后"] = page.evaluate(READ)
        # 焦点挪到**树里的机位行**（不动选中状态）⟹ 焦点离开输入框
        page.locator("text=机位1").first.click()
        page.wait_for_timeout(700)
        out["④按Z前"] = page.evaluate(READ)
        page.keyboard.press("z")
        page.wait_for_timeout(2_000)
        out["⑤按Z后"] = page.evaluate(READ)
        page.keyboard.press("z")
        page.wait_for_timeout(2_000)
        out["⑥再按Z后"] = page.evaluate(READ)
        # 复原
        out["⑦复原改名"] = set_name(page, "机位1")
        out["⑧复原后"] = page.evaluate(READ)
        close_desk(page)
        page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(12_000)
        open_desk(page)
        select_camera(page)
        out["复原回读"] = page.evaluate(READ)
        out["★已复原(同context)"] = name_value(page) == "机位1"
        ctx.close()
        ctx2 = br.new_context(viewport={"width": 1920, "height": 1080},
                              locale="zh-CN")
        ctx2.add_cookies([{"name": c["name"], "value": c["value"],
                           "domain": c["domain"], "path": c.get("path", "/"),
                           "expires": c.get("expires", -1),
                           "httpOnly": c.get("httpOnly", False),
                           "secure": c.get("secure", False),
                           "sameSite": c.get("sameSite", "Lax")} for c in cookies])
        p2 = ctx2.new_page()
        p2.goto(URL, wait_until="domcontentloaded", timeout=90_000)
        p2.wait_for_timeout(12_000)
        open_desk(p2)
        select_camera(p2)
        out["★全新context回读"] = p2.evaluate(READ)
        out["★已复原(新context)"] = name_value(p2) == "机位1"
        ctx2.close()
        br.close()


if __name__ == "__main__":
    main()
