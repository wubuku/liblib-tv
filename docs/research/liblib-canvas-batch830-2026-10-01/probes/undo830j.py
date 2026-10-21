#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 830 探针 v10：补最后两格。

格 A：**时间轴缩放的改动，失焦（blur）提交之后**能不能被 ⌘Z 撤？
  - 上一版（v9）改完缩放时**焦点还停在滑杆上** ⟹ 那次改动大概率还是 transient
    （没进历史栈）⟹ ⌘Z 撤的是**上一条**（改名），不是缩放。
  - 本版：改缩放 → **点树里的机位行**（真实 pointerdown ⟹ 触发 blur ⟹ 提交）
    → 再按 ⌘Z ⟹ 读回。
  - 源码依据：`UPDATE_TIMELINE` **在**可撤销集合 `lX` 里 ⟹ 若提交了就该撤得掉。

格 B：**T（俯视视角）造成的视图变化**能不能被 ⌘Z 撤？
  - 源码依据：`"t"⟹ n0.setEditorCameraPose(iK("top"))` ⟹ 这是**直接调 3D 引擎**，
    不走 reducer ⟹ 预测：**不在历史栈里** ⟹ ⌘Z 撤不掉。
  - 阳性对照：先做一次**能撤的**改动（改 FOV）把栈弄成非空 ⟹ 再按 T ⟹ 再按 ⌘Z
    ⟹ 若 ⌘Z 撤掉的是 FOV（而不是视图）⟹ 视图不在栈里。

★ 纪律：测完复原（FOV 67 / 名称 机位1 / 缩放回默认）⟹ 干净关台 → 刷新 → 全新 context 回读。
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_desk830_undo10.json")
SHOTS = pathlib.Path("/tmp/liblib_source_desk830")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

READ = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const describe=(e)=>({type:e.type,value:e.value,
                        attr:e.getAttribute('value')||'',
                        min:e.min||'',max:e.max||'',box:box(e)});
  const rowOf=(labelText)=>{
    const cands=Array.from(document.querySelectorAll('div,span,label,p'))
      .filter(e=>(e.textContent||'').trim()===labelText);
    if(!cands.length) return null;
    cands.sort((a,b)=>{const ra=a.getBoundingClientRect(),rb=b.getBoundingClientRect();
      return (ra.width*ra.height)-(rb.width*rb.height);});
    for(const L of cands){let a=L;
      for(let i=0;i<7&&a;i++,a=a.parentElement){
        const ins=Array.from(a.querySelectorAll('input'));
        if(ins.length) return ins.map(describe);}}
    return null;
  };
  const fov=document.querySelector('input[type=range][min="15"][max="90"]');
  const zoom=document.querySelector('[aria-label="时间轴缩放"]');
  const nameInput=Array.from(document.querySelectorAll('input'))
    .filter(e=>e.type==='text'&&e.getBoundingClientRect().x>1600
      &&e.getBoundingClientRect().y<400)
    .map(e=>({value:e.value,box:box(e)}));
  return {
    场景平移: rowOf('场景平移'), 场景旋转: rowOf('场景旋转'),
    场景缩放: rowOf('场景缩放'),
    fov: fov?describe(fov):null,
    zoom: zoom?describe(zoom):null,
    names: nameInput,
    active: (()=>{const a=document.activeElement;
      return a?{tag:a.tagName,type:a.type||'',
                aria:a.getAttribute('aria-label')||'',
                txt:(a.textContent||'').trim().slice(0,16)}:null;})(),
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


def open_timeline(page):
    if page.evaluate(READ).get("zoom"):
        return "already"
    page.locator("[aria-label='动画时间轴']:visible").first.click()
    page.wait_for_timeout(3_500)
    return "opened"


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


def change_range(page, key, want):
    st = page.evaluate(READ)
    rng = st.get(key)
    if not rng:
        return {"error": "no %s" % key}
    span = float(rng["max"]) - float(rng["min"])
    frac = (float(want) - float(rng["min"])) / span
    tries = []
    for f in (frac, frac - 0.03, frac + 0.03, frac - 0.05, frac + 0.05):
        act = click_range(page, rng, max(0.0, min(1.0, f)))
        now = page.evaluate(READ)
        v = (now.get(key) or {}).get("value")
        tries.append({**act, "value_after": v})
        if v != str(rng["value"]):
            return {"before": rng["value"], "after": v, "tries": tries}
    return {"before": rng["value"], "after": None, "tries": tries, "★没改成": True}


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

        # ══ 格 A：缩放改动 → blur 提交 → ⌘Z ══
        try:
            open_timeline(page)
            out["①zoom_改前"] = page.evaluate(READ)
            out["②改zoom"] = change_range(page, "zoom", 75)
            out["③改zoom后"] = page.evaluate(READ)
            page.locator("text=机位1").first.click()      # ← 真实 pointerdown ⟹ blur ⟹ 提交
            page.wait_for_timeout(1_500)
            out["④失焦后"] = page.evaluate(READ)
            page.keyboard.press("Meta+z")
            page.wait_for_timeout(2_000)
            out["⑤失焦后按⌘Z"] = page.evaluate(READ)
        except Exception:
            out["格A_异常"] = traceback.format_exc()[-800:]

        # ══ 格 B：T 的视图变化 + ⌘Z（栈里先放一条能撤的改动）══
        try:
            SHOTS.mkdir(exist_ok=True)
            out["⑥B_改前"] = page.evaluate(READ)
            out["⑦改FOV"] = change_range(page, "fov", 50)
            page.screenshot(path=str(SHOTS / "830_v10_T_before.png"))
            page.keyboard.press("t")
            page.wait_for_timeout(3_000)
            page.screenshot(path=str(SHOTS / "830_v10_T_after.png"))
            out["⑧按T后"] = page.evaluate(READ)
            page.keyboard.press("Meta+z")
            page.wait_for_timeout(2_500)
            page.screenshot(path=str(SHOTS / "830_v10_T_undo.png"))
            out["⑨按⌘Z后"] = page.evaluate(READ)
        except Exception:
            out["格B_异常"] = traceback.format_exc()[-800:]

        # ══ 复原 ══
        try:
            out["复原_FOV"] = change_range(page, "fov", 67)
            out["复原后"] = page.evaluate(READ)
        except Exception:
            out["复原_异常"] = traceback.format_exc()[-800:]

        # ══ 干净关台 → 刷新 → 全新 context 回读（含时间轴面板，读缩放）══
        try:
            close_desk(page)
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(12_000)
            open_desk(page)
            select_camera(page)
            open_timeline(page)
            out["⑩同context回读"] = page.evaluate(READ)
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
            open_timeline(p2)
            out["⑪全新context回读"] = p2.evaluate(READ)
            ctx2.close()
        except Exception:
            out["回读_异常"] = traceback.format_exc()[-800:]
        br.close()


if __name__ == "__main__":
    main()
