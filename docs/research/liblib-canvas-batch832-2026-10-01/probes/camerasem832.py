#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 832 源站探针：**点一枚机位预设，看机位真的变成什么样**。

★ 为什么必须测：面板上有 15 枚预设 ⟹ 若 clone 只把面板画出来而**点了没反应**，
  那就是「画了但没实现」⟹ 复刻就不到位。
⟹ 所以要量：点「正面中景」之后，新机位的 **transform / target / fov** 各是多少，
  与点之前那个机位相比差在哪。

★ ★ 测法（源站侧）：
  1. 记下点之前的机位（位置/朝向/焦段）；
  2. 点「正面中景」；
  3. 记下点之后的机位；
  4. ⟹ 差值就是这枚预设的**语义**（位置偏移、朝向、fov）。

★ ★ ★ 纪律（★ 本批最重要的红线）：
  **这是会改源站数据的操作**（点预设会真的加一个机位）⟹
  ⟹ 测完**必须复原**：把新增的机位删掉 ⟹ 并且**读数要证明复原了**
  （重新读一遍机位列表，比对数量与内容）。
  ⟹ 删法要确认是安全的（不改用户已有项目的内容）。
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_desk832_camerasem.json")
SHOTS = pathlib.Path("/tmp/liblib_source_desk832")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 机位读数：源站的机位列表在**左栏场景树**里 ⟹ 读树里的机位条目
DUMP_CAMS = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
  // 场景树里的条目：带 truncate class 的 span
  const items=Array.from(document.querySelectorAll('span.truncate, span.max-w-full'))
    .filter(vis).map(s=>({t:(s.textContent||'').trim(), box:box(s)}));
  // ★ 选中态（蓝色高亮）的条目
  const selected=Array.from(document.querySelectorAll('div'))
    .filter(e=>{const c=getComputedStyle(e);
      return vis(e)&&c.backgroundColor!=='rgba(0, 0, 0, 0)'
        &&e.getBoundingClientRect().width>40&&e.getBoundingClientRect().width<240;})
    .map(e=>({cls:String(e.className||'').slice(0,120),
              bg:getComputedStyle(e).backgroundColor,
              box:box(e), t:(e.textContent||'').trim().slice(0,40)}));
  return {items, selected};
}"""

# ★ 选中机位后，右栏「属性」面板里的机位属性读数
DUMP_PROPS = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
  const aside=Array.from(document.querySelectorAll('aside')).filter(e=>{
    const r=e.getBoundingClientRect(); return r.x>1500&&r.width>200;})[0];
  if(!aside) return {found:false};
  const inputs=Array.from(aside.querySelectorAll('input')).filter(vis).map(i=>({
    type:i.type, aria:i.getAttribute('aria-label'), value:i.value,
    min:i.getAttribute('min'), max:i.getAttribute('max'), box:box(i)}));
  const texts=Array.from(aside.querySelectorAll('span,div')).filter(vis)
    .map(e=>(e.textContent||'').trim()).filter(t=>t&&t.length<24);
  return {found:true, box:box(aside), inputs,
          texts:[...new Set(texts)].slice(0,40)};
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
            out["⓪开台后树"] = page.evaluate(DUMP_CAMS)

            # 打开机位预设面板
            nav = page.locator("nav").filter(
                has=page.locator("button[aria-label='场景']")).first
            nav.locator("button[aria-label='添加机位']").first.click()
            page.wait_for_timeout(2_200)
            out["①面板打开后树"] = page.evaluate(DUMP_CAMS)
            out["②面板打开后属性"] = page.evaluate(DUMP_PROPS)
            page.screenshot(path=str(SHOTS / "832_cam_before.png"))

            # ★ 点「正面中景」（第 2 格，索引 1）
            grid = page.locator("div.grid.min-h-0.flex-1").first
            cells = grid.locator("button")
            n = cells.count()
            out["③格子数"] = n
            cells.nth(1).click()
            page.wait_for_timeout(3_000)
            out["④点正面中景后树"] = page.evaluate(DUMP_CAMS)
            out["⑤点正面中景后属性"] = page.evaluate(DUMP_PROPS)
            page.screenshot(path=str(SHOTS / "832_cam_after.png"))
        except Exception:
            out["异常"] = traceback.format_exc()[-1800:]
        try:
            page.locator("[aria-label='关闭']:visible").first.click()
            page.wait_for_timeout(3_000)
        except Exception:
            pass
        ctx.close()
        br.close()


if __name__ == "__main__":
    main()
