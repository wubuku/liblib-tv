#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 832：逐枚点开 rail 入口，量**各自打开的东西**（源站 vs clone 同款）。

★ 为什么要逐枚点：batch 832 已确认 **rail 本身 7 枚入口与源站逐字对齐**
  （aria 名、盒 32×32、y 步长 40 全等）⟹ 差异不在「有哪些按钮」，
  而在**点开之后出现的东西**。

★ 关键坑（本探针踩过）：
  - 源站的 rail 是 **`<nav>`**（`w-12`），**不是** `<aside>`；
    `<aside>` 是 281 宽的**左侧对象树面板**⟹ 用 aside 找 rail 会得到
    「found: false」⟹ ★ 那是**选择器错了**，不是「台没开」⟹
    排查时必须先分清这两件事（`diag832.py` 就是干这个的）。
  - clone 的 rail 根是 **`<div class="w-12">`**，也没有 `<nav>` ⟹
    两边**结构不同** ⟹ 读数器必须用**各自的选择器**找 rail。

★ 读数口径（两边一致）：
  - 点开后的浮层：`role=dialog` / `role=menu` / 定位浮层（absolute|fixed 且有尺寸）
  - 浮层的盒、类名、可见文本前若干字
  - 点开后的**可见文本全量**（用来对比 clone 有没有少东西）

★ 纪律：只点 rail 入口、只读；不点生成/付费控件；不改源站数据。
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_desk832_entries.json")
SHOTS = pathlib.Path("/tmp/liblib_source_desk832")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 浮层读数（两边**逐字相同**的一段 JS）
DUMP_PANEL = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const cs=(e)=>{const c=getComputedStyle(e);
    return {bg:c.backgroundColor,color:c.color,fontSize:c.fontSize,
            borderRadius:c.borderRadius,border:c.border,padding:c.padding,
            boxShadow:c.boxShadow,backdropFilter:c.backdropFilter,
            position:c.position,zIndex:c.zIndex};};
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).visibility!=='hidden'
      &&getComputedStyle(e).display!=='none'
      &&getComputedStyle(e).opacity!=='0';};
  const dialogs=Array.from(document.querySelectorAll('[role="dialog"]')).filter(vis);
  const menus=Array.from(document.querySelectorAll('[role="menu"]')).filter(vis);
  const panels=Array.from(document.querySelectorAll('div')).filter(e=>{
    const c=getComputedStyle(e); const r=e.getBoundingClientRect();
    if(!vis(e)) return false;
    if(c.position!=='absolute'&&c.position!=='fixed') return false;
    return r.width>=100&&r.height>=60&&r.width<=1400&&r.height<=1000;});
  // ★ 只留「最外层」的那些（不被另一个候选包含）
  const outer=panels.filter(p=>!panels.some(q=>q!==p&&q.contains(p)));
  const bodyText=(document.body.innerText||'');
  return {
    dialogs:dialogs.map(e=>({box:box(e),aria:e.getAttribute('aria-label'),
      cls:String(e.className||'').slice(0,240),style:cs(e),
      text:(e.textContent||'').trim().slice(0,400)})),
    menus:menus.map(e=>({box:box(e),aria:e.getAttribute('aria-label'),
      cls:String(e.className||'').slice(0,240),
      items:Array.from(e.querySelectorAll('[role="menuitem"]')).map(i=>({
        t:(i.textContent||'').trim(),box:box(i)}))})),
    panels:outer.slice(-8).map(e=>({box:box(e),
      cls:String(e.className||'').slice(0,240),
      text:(e.textContent||'').trim().slice(0,300)})),
    bodyTextLen:bodyText.length,
    bodyTextHead:bodyText.replace(/\\s+/g,' ').slice(0,600),
  };
}"""


def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(800)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(8_000)


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
        SHOTS.mkdir(exist_ok=True)
        try:
            out["⓪开台后"] = page.evaluate(DUMP_PANEL)
            for aria in ["场景", "添加角色", "添加机位", "全景图",
                         "选择画幅比例", "AI 识图导入"]:
                key = "①" + aria
                try:
                    page.locator("[aria-label='%s']" % aria).first.click()
                    page.wait_for_timeout(1_800)
                    out[key] = page.evaluate(DUMP_PANEL)
                    page.screenshot(path=str(SHOTS / ("832_%s.png" % aria.replace(" ", ""))))
                    # 收掉：Esc ＋ 点空白
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(700)
                    page.mouse.click(1400, 950)
                    page.wait_for_timeout(900)
                except Exception as exc:  # noqa: BLE001
                    out[key] = {"异常": str(exc)[:400]}
                    try:
                        page.keyboard.press("Escape")
                        page.wait_for_timeout(500)
                        page.mouse.click(1400, 950)
                        page.wait_for_timeout(700)
                    except Exception:
                        pass
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
