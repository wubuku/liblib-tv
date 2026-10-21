#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 832 诊断探针：源站**此刻**是什么状态？导演台开了没？

★ 为什么需要它：上一版盘点探针用「最左侧 48px 宽的 aside」找 rail，
  结果 `found: false`，而 DOM_OVERLAY 取到的还是**画布节点**
  ⟹ ★ 说明那一刻**导演台根本没开**（或开台动作没生效）
  ⟹ 所以先分清「选择器不对」与「台没开」这两件事，再谈别的。

★ 读数：
  - 页面上有没有 `aria-label="关闭"` 的按钮（源站关台按钮）
  - 有几个 `aside`、各自是什么
  - 视口最左侧 0..80px 带上的元素是谁（按 hit-test + DOM 枚举两条都读）
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_diag832.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

DUMP_STATE = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const asides=Array.from(document.querySelectorAll('aside')).map(e=>({
    box:box(e), cls:String(e.className||'').slice(0,120),
    btns:Array.from(e.querySelectorAll('button')).map(b=>({
      aria:b.getAttribute('aria-label'), title:b.getAttribute('title'),
      box:box(b)}))}));
  // 最左侧 80px 带上的所有可见元素
  const left=[];
  for(const e of document.querySelectorAll('body *')){
    const r=e.getBoundingClientRect();
    if(r.width<=0||r.height<=0) continue;
    if(r.x>80) continue;
    if(getComputedStyle(e).display==='none') continue;
    left.push({tag:e.tagName, cls:String(e.className||'').slice(0,90),
               box:box(e), aria:e.getAttribute('aria-label'),
               text:(e.textContent||'').trim().slice(0,24)});
  }
  return {
    closeBtns:Array.from(document.querySelectorAll("[aria-label='关闭']")).map(e=>({
      box:box(e), visible:e.getBoundingClientRect().width>0})),
    asides:asides,
    leftStrip:left.slice(0,40),
    totalLeft: left.length,
    hit:(function(){
      const e=document.elementFromPoint(24,900);
      return e?{tag:e.tagName,cls:String(e.className||'').slice(0,90),
        aria:e.getAttribute('aria-label')}:null;})(),
  };
}"""


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
        out["①开台前"] = page.evaluate(DUMP_STATE)

        # ── 开台
        try:
            card = page.locator(".react-flow__node-director-console-3d").first
            card.hover()
            page.wait_for_timeout(800)
            page.locator(
                ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
            page.wait_for_timeout(8_000)
        except Exception:
            out["开台异常"] = traceback.format_exc()[-1200:]
        out["②开台后"] = page.evaluate(DUMP_STATE)
        page.screenshot(path="/tmp/liblib_source_diag832.png")

        # ── 再等一会儿（有些面板懒加载）
        page.wait_for_timeout(6_000)
        out["③再等6秒后"] = page.evaluate(DUMP_STATE)
        ctx.close()
        br.close()


if __name__ == "__main__":
    main()
