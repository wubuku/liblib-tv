#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 830 探针 v8：源站导演台**快捷键管线**的阳性对照 + 「Z 能撤什么」的第一格。

★ 为什么必须先做阳性对照（上一批栽在这里）：
  上一批说「源站按 Z 撤不掉 FOV/改名」——但那两版用来「把焦点挪开」的选择器
  `[data-director-workspace] h1, [role=dialog] h1` **在源站 DOM 里根本不存在**
  ⟹ 那个动作实际没执行（v7 复现了它的 TimeoutError）。
  ⟹ 本版先证明**快捷键管线是活的**，再问 Z 撤不撤得掉。

★ 阳性对照选 **T（俯视视角）**：它一定会改「场景旋转」数字 ⟹ 可读、可证伪。
  （对照 W：v7 里 W 那格根本没跑到；v6 里「W 没生效」是因为右栏一直在「摄像机属性」
    页签、场景数字压根读不到 ⟹ 那一格作废，本版重测。）

★ 读数器的两个修正（源站实测）：
  ① 源站的原生 range **全部 opacity:0 + 自绘轨道** ⟹ 任何「祖先/自身 opacity≤0
     就当不可见」的可见性判定，对它们**必然返回 false** ⟹ 读数器**不按可见性过滤
     input**，改按**结构位置**（标签行）取，并记录 opacity 备查。
  ② 源站「时间轴缩放」的 `value` **属性**是浮点 `43.77510040160642`，
     而 `.value` 读出 "44"（step 默认 1 ⟹ 四舍五入）⟹ "44" 是**显示值**不是真值。

★ 纪律：不点生成/付费控件；测完复原并用**全新 context 回读**验证。
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_desk830_undo5.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

READ = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const describe=(e)=>({type:e.type,value:e.value,
                        min:e.min||'',max:e.max||'',step:e.step||'',
                        opacity:getComputedStyle(e).opacity,
                        pointerEvents:getComputedStyle(e).pointerEvents,
                        box:box(e)});
  // ★ 按**标签行**取输入框（不按可见性过滤 ⟹ opacity:0 的原生 range 也在内）
  const rowOf=(labelText)=>{
    const cands=Array.from(document.querySelectorAll('div,span,label,p'))
      .filter(e=>(e.textContent||'').trim()===labelText);
    if(!cands.length) return null;
    cands.sort((a,b)=>{
      const ra=a.getBoundingClientRect(), rb=b.getBoundingClientRect();
      return (ra.width*ra.height)-(rb.width*rb.height);});
    for(const L of cands){
      let a=L;
      for(let i=0;i<7&&a;i++,a=a.parentElement){
        const ins=Array.from(a.querySelectorAll('input'));
        if(ins.length) return ins.map(describe);
      }
    }
    return null;
  };
  const fov=document.querySelector('input[type=range][min="15"][max="90"]');
  const zoom=document.querySelector('[aria-label="时间轴缩放"]');
  return {
    平移: rowOf('场景平移'),
    旋转: rowOf('场景旋转'),
    缩放: rowOf('场景缩放'),
    水平旋转: rowOf('水平旋转'),
    球形半径: rowOf('球形半径'),
    fov: fov?{value:fov.value,min:fov.min,max:fov.max,box:box(fov),
              opacity:getComputedStyle(fov).opacity}:null,
    zoom: zoom?{value:zoom.value,attr:zoom.getAttribute('value'),
                min:zoom.min,max:zoom.max,box:box(zoom),
                opacity:getComputedStyle(zoom).opacity}:null,
    active: (()=>{const a=document.activeElement;
      return a?{tag:a.tagName,cls:String(a.className||'').slice(0,50),
                aria:a.getAttribute('aria-label')||'',
                type:a.type||'',
                txt:(a.textContent||'').trim().slice(0,18)}:null;})(),
  };
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


def dump(out, page, key):
    out[key] = page.evaluate(READ)
    return out[key]


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

        # ── ① 基线
        dump(out, page, "①基线")

        # ── ② 阳性对照：T（俯视视角）⟹ 场景旋转该变
        try:
            page.keyboard.press("t")
            page.wait_for_timeout(2_500)
            dump(out, page, "②按T后")
        except Exception:
            out["②_异常"] = traceback.format_exc()[-800:]

        # ── ③ Z 能撤掉视角变化吗
        try:
            page.keyboard.press("z")
            page.wait_for_timeout(2_500)
            dump(out, page, "③按Z后")
        except Exception:
            out["③_异常"] = traceback.format_exc()[-800:]

        # ── ④ H（重置视角）⟹ 回到基线（顺带复原）
        try:
            page.keyboard.press("h")
            page.wait_for_timeout(2_500)
            dump(out, page, "④按H后")
        except Exception:
            out["④_异常"] = traceback.format_exc()[-800:]

        # ── ⑤ W（移动当前视角）×3 ⟹ 上一批作废的那一格
        try:
            for _ in range(3):
                page.keyboard.press("w")
                page.wait_for_timeout(600)
            dump(out, page, "⑤按W三次后")
            page.keyboard.press("z")
            page.wait_for_timeout(2_500)
            dump(out, page, "⑥W后按Z")
            page.keyboard.press("h")
            page.wait_for_timeout(2_500)
            dump(out, page, "⑦再按H")
        except Exception:
            out["⑤_异常"] = traceback.format_exc()[-800:]

        # ── ⑧ 复原核对 + 干净关台 + 刷新 + 全新 context 回读
        try:
            close_desk(page)
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(12_000)
            open_desk(page)
            dump(out, page, "⑧同context回读")
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
            dump(out, p2, "⑨全新context回读")
            ctx2.close()
        except Exception:
            out["⑧_异常"] = traceback.format_exc()[-800:]
        br.close()


if __name__ == "__main__":
    main()
