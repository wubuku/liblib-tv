#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 830 源站撤销探针（v4 · 决定性）：撤销到底**能撤什么**。

★ v3 暴露的两个坑（都已避开）：
  ① 点「导演视角」会**取消选中机位** ⟹ 右栏从「摄像机属性」切成「3D场景」⟹
     之前把 FOV 输入框消失**归因给 Z** 是错的（锅在「导演视角」）⟹ ★ 先怀疑自己的动作。
  ② 同会话那次测试**前提不满足**（FOV 本来就是 40，没改成）⟹ 「Z 没撤」是无效读数。
★ 本版：
  A 视口移动（WASDQE 里的 W）能不能被 Z 撤掉（场景平移 x/y/z 是可读的）
  B 同会话内 FOV 改动（67→45）能不能被 Z 撤掉
    ★ 焦点用**树里的「机位1」行**（role=button tabindex=0）⟹ 焦点离开输入框、
      机位仍选中 ⟹ FOV 输入框还在
  C 跨关台重开后再按 Z（已测：FOV 45 不变）⟹ 复核
  D 复原（FOV 67）→ 干净关台 → 刷新 → 回读 → **全新 context 回读**（服务端干净）
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_desk830_undo3.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

READ_STATE = """()=>{
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
  const fov=document.querySelector('input[type=range][min="15"][max="90"]');
  const zoom=document.querySelector('[aria-label="时间轴缩放"]');
  // 场景平移/旋转的 x/y/z 数字（3D场景面板）
  const nums={};
  for(const label of ['场景平移','场景旋转','场景缩放']){
    const rows=Array.from(document.querySelectorAll('div,span,label'))
      .filter(e=>realVis(e)&&e.children.length===0&&(e.textContent||'').trim()===label);
    if(!rows.length) continue;
    const y=rows[0].getBoundingClientRect().y;
    const vals=Array.from(document.querySelectorAll('input'))
      .filter(e=>realVis(e)&&Math.abs(e.getBoundingClientRect().y-y)<60)
      .map(e=>({v:e.value,type:e.type,
                aria:e.getAttribute('aria-label')||'',
                title:e.getAttribute('title')||''}));
    if(vals.length) nums[label]=vals;
  }
  return {
    fov: fov ? {value:fov.value, box:box(fov), visible:realVis(fov)} : null,
    zoom: zoom ? {value:zoom.value, box:box(zoom)} : null,
    scene: nums,
    active: (()=>{const a=document.activeElement;
      return a?{tag:a.tagName,text:(a.textContent||'').trim().slice(0,14),
                type:a.type||''}:null;})(),
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


def select_camera(page):
    page.locator("text=机位1").first.click()
    page.wait_for_timeout(2_000)


def click_range(page, rng, frac):
    b = rng["box"]
    x = b["x"] + int(b["w"] * frac)
    y = b["y"] + b["h"] // 2
    page.mouse.move(x, y)
    page.mouse.down()
    page.wait_for_timeout(120)
    page.mouse.up()
    page.wait_for_timeout(900)
    return {"frac": frac, "at": [x, y]}


def set_fov(page, want):
    st = page.evaluate(READ_STATE)
    rng = st.get("fov")
    if not rng:
        return {"error": "no fov input"}
    frac = (float(want) - 15) / 75.0
    tries = []
    for f in (frac, frac - 0.02, frac + 0.02, frac - 0.04, frac + 0.04):
        act = click_range(page, rng, max(0.0, min(1.0, f)))
        now = page.evaluate(READ_STATE)
        v = (now.get("fov") or {}).get("value")
        tries.append({**act, "value_after": v})
        if v == str(want):
            return {"before": rng["value"], "after": v, "tries": tries}
    return {"before": rng["value"], "after": None, "tries": tries, "★没调到": True}


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

        # ── A 视口移动 + Z（先在 3D场景 面板下）
        out["①A_移动前"] = page.evaluate(READ_STATE)
        for _ in range(3):
            page.keyboard.press("w")
            page.wait_for_timeout(500)
        out["②A_按W三次后"] = page.evaluate(READ_STATE)
        page.keyboard.press("z")
        page.wait_for_timeout(1_500)
        out["③A_按Z后"] = page.evaluate(READ_STATE)

        # ── B 同会话内 FOV 改动 + Z
        select_camera(page)
        out["④B_FOV_改前"] = page.evaluate(READ_STATE)
        out["⑤B_改FOV"] = set_fov(page, 45)
        out["⑥B_改后"] = page.evaluate(READ_STATE)
        # ★ 焦点回到**树里的机位行**（不是「导演视角」按钮！后者会取消选中机位）
        page.locator("[data-director-tree] [role=treeitem], [role=treeitem]")
        page.locator("text=机位1").first.click()
        page.wait_for_timeout(600)
        out["⑦B_按Z前active"] = page.evaluate(READ_STATE)
        page.keyboard.press("z")
        page.wait_for_timeout(2_000)
        out["⑧B_按Z后"] = page.evaluate(READ_STATE)

        # ── C 跨关台重开 + Z
        out["⑨C_再改FOV"] = set_fov(page, 50)
        close_desk(page)
        open_desk(page)
        select_camera(page)
        out["⑩C_重开后"] = page.evaluate(READ_STATE)
        page.locator("text=机位1").first.click()
        page.wait_for_timeout(600)
        page.keyboard.press("z")
        page.wait_for_timeout(2_000)
        out["⑪C_重开后按Z"] = page.evaluate(READ_STATE)

        # ── D 复原 + 干净关台 + 刷新 + 回读 + 全新 context 回读
        out["复原动作_FOV"] = set_fov(page, 67)
        close_desk(page)
        page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(12_000)
        open_desk(page)
        select_camera(page)
        out["复原回读"] = page.evaluate(READ_STATE)
        out["★已复原(同context)"] = (out["复原回读"].get("fov") or {}).get("value") == "67"
        ctx.close()
        # 全新 context（服务端值）
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
        out["★全新context回读"] = p2.evaluate(READ_STATE)
        out["★已复原(新context)"] = \
            (out["★全新context回读"].get("fov") or {}).get("value") == "67"
        ctx2.close()
        br.close()


if __name__ == "__main__":
    main()
