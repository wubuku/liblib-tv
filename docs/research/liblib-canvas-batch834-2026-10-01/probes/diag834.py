#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 834 诊断：源站的引导气泡**到底在哪、什么条件下出现**。

★ 为什么要有这一条：`probes/coach834.py` 按「n/5 ＋ 跳过/下一步」去找气泡，
  开了台、点了「帮助 → 使用教程」都**没找到** ⟹
  - 可能：① 气泡**需要时间轴打开**才渲染；
  - 可能：② 引导的触发条件不是那个菜单项；
  - 可能：③ 步数文本**不是「n/5」**（例如「1 / 5」被拆成两个元素）；
  - 可能：④ 它在 **iframe / shadow DOM** 里。
  ⟹ ★ 所以先**如实把整页的相关文本与固定定位元素 dump 出来**，再决定怎么找。
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_diag834.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 全页搜「教程 / 跳过 / 下一步 / n/5 / 引导」，不限叶子节点
DUMP_TEXT = """()=>{
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
  const hits=[];
  for(const e of document.querySelectorAll('body *')){
    if(!vis(e)) continue;
    const t=(e.textContent||'').trim();
    if(!t || t.length>60) continue;
    if(/教程|跳过|下一步|完成|引导|^\\d+\\s*\\/\\s*\\d+$/.test(t)){
      const r=e.getBoundingClientRect();
      hits.push({tag:e.tagName, t, childs:e.childElementCount,
                 cls:String(e.className||'').slice(0,100),
                 box:{x:Math.round(r.x),y:Math.round(r.y),
                      w:Math.round(r.width),h:Math.round(r.height)}});
    }
  }
  return hits;
}"""

# ★ 视口左下角（源站气泡的位置）附近的固定/绝对定位元素
DUMP_CORNER = """()=>{
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
  const out=[];
  for(const e of document.querySelectorAll('body *')){
    if(!vis(e)) continue;
    const r=e.getBoundingClientRect();
    if(r.x>700||r.y<600||r.width>600||r.height>400) continue;
    const cs=getComputedStyle(e);
    if(cs.position!=='fixed'&&cs.position!=='absolute') continue;
    out.push({tag:e.tagName, pos:cs.position, z:cs.zIndex,
              t:(e.textContent||'').trim().slice(0,60),
              cls:String(e.className||'').slice(0,110),
              box:{x:Math.round(r.x),y:Math.round(r.y),
                   w:Math.round(r.width),h:Math.round(r.height)}});
  }
  return out.slice(0,40);
}"""

# ★ 导演台里有没有「时间轴」的开关按钮（用于测试「打开时间轴才出现引导」）
DUMP_TIMELINE = """()=>{
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
  const out=[];
  for(const b of document.querySelectorAll('button')){
    if(!vis(b)) continue;
    const t=(b.textContent||'').trim();
    const aria=b.getAttribute('aria-label')||'';
    const title=b.getAttribute('title')||'';
    if(/时间轴|timeline|展开|收起/i.test(t+' '+aria+' '+title)){
      const r=b.getBoundingClientRect();
      out.push({t, aria, title,
                box:{x:Math.round(r.x),y:Math.round(r.y),
                     w:Math.round(r.width),h:Math.round(r.height)}});
    }
  }
  return out;
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
        out["①开台后·文本"] = page.evaluate(DUMP_TEXT)
        out["①开台后·左下角"] = page.evaluate(DUMP_CORNER)
        out["①开台后·时间轴开关"] = page.evaluate(DUMP_TIMELINE)
        page.screenshot(path="/tmp/liblib_source_diag834_open.png")

        # ★ 试试把时间轴打开
        try:
            tl = page.get_by_text("时间轴", exact=True).first
            tl.click()
            page.wait_for_timeout(2_500)
            out["②开时间轴后·文本"] = page.evaluate(DUMP_TEXT)
            page.screenshot(path="/tmp/liblib_source_diag834_timeline.png")
        except Exception as exc:  # noqa: BLE001
            out["②开时间轴异常"] = repr(exc)[:200]

        # ★ 再走「帮助 → 使用教程」
        try:
            page.locator("button[aria-label='帮助']").first.click()
            page.wait_for_timeout(1_200)
            page.locator("[role='menuitem']").filter(
                has_text="使用教程").first.click()
            page.wait_for_timeout(2_500)
            out["③点使用教程后·文本"] = page.evaluate(DUMP_TEXT)
            out["③点使用教程后·左下角"] = page.evaluate(DUMP_CORNER)
            page.screenshot(path="/tmp/liblib_source_diag834_tutorial.png")
        except Exception as exc:  # noqa: BLE001
            out["③异常"] = repr(exc)[:200]
        ctx.close()
        br.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已落盘：", OUT)
    for k in out:
        if k.endswith("文本"):
            print(k, "命中", len(out[k] or []), "条")
            for h in (out[k] or [])[:12]:
                print("   ", h["tag"], repr(h["t"][:40]), h["box"])
        elif k.endswith("左下角"):
            print(k, "命中", len(out[k] or []), "条")
            for h in (out[k] or [])[:8]:
                print("   ", h["tag"], h["pos"], repr(h["t"][:40]), h["box"])


if __name__ == "__main__":
    main()
