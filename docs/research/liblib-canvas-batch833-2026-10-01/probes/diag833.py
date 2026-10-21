#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 833 诊断探针：源站**右栏机位属性面板**到底长什么样（读数器要先能定位它）。

★ 上一批（832）的语义探针为什么全空：
  `DUMP_CAMPROPS` 找的是 `aside` 里 `r.x > 1500 && r.width > 200` 的元素
  ⟹ ★ 实测源站的右栏**不是 `<aside>`** ⟹ 那个选择器**零命中**
  ⟹ 于是 `props.found` 恒为 false ⟹ ★★ 读数器**扫的元素类型**与界面真实类型
  **不相交** ⟹ 差集恒空 ⟹ 造出一个「什么都没有」的假否定
  ⟹ （与已存记忆里的「读数器扫的元素类型必须与界面真实元素类型相交」同族）

★ 所以本探针先**只做一件事**：把源站右栏是什么元素、里面有什么，**如实**读出来。

★ 纪律：只读；**不点任何预设**（会新建机位）。
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_diag833.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 枚举视口右侧 300px 带上的**所有**元素（按 tag + 类名），不猜类型
DUMP_RIGHT = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
  const rows=[];
  for(const e of document.querySelectorAll('body *')){
    const r=e.getBoundingClientRect();
    if(r.width<=0||r.height<=0) continue;
    if(r.x<1500) continue;
    if(getComputedStyle(e).display==='none') continue;
    rows.push({tag:e.tagName,
               cls:String(e.className||'').slice(0,110),
               role:e.getAttribute('role')||'',
               aria:e.getAttribute('aria-label')||'',
               type:e.getAttribute('type')||'',
               value:(e.value!==undefined&&e.value!=='')?String(e.value).slice(0,24):'',
               text:(e.childElementCount===0)?(e.textContent||'').trim().slice(0,28):'',
               box:box(e)});
  }
  return {count:rows.length, rows:rows.slice(0,120)};
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
        try:
            out["①开台后右栏"] = page.evaluate(DUMP_RIGHT)
            # ★ 选一个机位（点场景树里的「机位1」）⟹ 右栏变成机位属性
            page.get_by_text("机位1", exact=True).first.click()
            page.wait_for_timeout(2_500)
            out["②选中机位1后右栏"] = page.evaluate(DUMP_RIGHT)
            page.screenshot(path="/tmp/liblib_source_diag833.png")
        except Exception:
            out["异常"] = traceback.format_exc()[-1500:]
        try:
            page.locator("[aria-label='关闭']:visible").first.click()
            page.wait_for_timeout(2_500)
        except Exception:
            pass
        ctx.close()
        br.close()


if __name__ == "__main__":
    main()
