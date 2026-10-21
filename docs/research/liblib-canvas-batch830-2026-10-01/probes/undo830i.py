#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 830 探针 v9：**⌘Z** 重测源站撤销（上一批用裸 Z 测 ⟹ 前提不满足，读数作废）。

★ 上一批错在哪（读源码才知道）：
  源站键盘处理（window 捕获阶段）：
    hY = new Set(["escape","enter","v","r","f","h","x","t","y","c","d","g","delete","backspace","z"])
    hX = new Set(["w","a","s","d","q","e"])
    if(hY.has(n) && ("z"!==n||e.ctrlKey||e.metaKey) && …)
  ⟹ ★★ **裸 `z` 被明确排除**，撤销是 **⌘Z**（面板里那个 ⌘ 是 SVG 图标，纯文本读数器看不见它）
  ⟹ 上一批「源站 Z 撤不掉 FOV/改名」是**前提不满足**的无效读数。
  ⟹ 而 reducer 的可撤销集合 `lX` **含 UPDATE_CAMERA** ⟹ 理论上 ⌘Z 该撤得掉。

★ 本探针用 **Meta+z** 重测三格：机位 FOV、机位改名、时间轴缩放；
  另用**截图对**测「俯视视角 T」是否真的改了视图（上一批读的是场景变换数字，
  而 T 改的是 editor camera pose ⟹ 读数口径不对 ⟹ 假阴性）。

★ 纪律：不点生成/付费控件；测完复原并用**全新 context 回读**验证。
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_desk830_undo9.json")
SHOTS = pathlib.Path("/tmp/liblib_source_desk830")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

READ = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const describe=(e)=>({type:e.type,value:e.value,
                        attr:e.getAttribute('value')||'',
                        min:e.min||'',max:e.max||'',
                        box:box(e)});
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
    """按「点轨道」改值（源站的原生 range 是 opacity:0 的，靠坐标点击才生效）。"""
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
    st2 = page.evaluate(READ)
    ns2 = st2.get("names") or []
    return {"before": before, "typed": value,
            "after": ns2[0]["value"] if ns2 else None}


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

        # ══ 格 1：机位 FOV + ⌘Z ══
        try:
            out["①FOV_改前"] = page.evaluate(READ)
            out["②改FOV"] = change_range(page, "fov", 45)
            out["③改FOV后"] = page.evaluate(READ)
            page.keyboard.press("Meta+z")
            page.wait_for_timeout(2_000)
            out["④按⌘Z后"] = page.evaluate(READ)
            page.keyboard.press("Meta+Shift+z")
            page.wait_for_timeout(2_000)
            out["⑤按⌘⇧Z后"] = page.evaluate(READ)
        except Exception:
            out["格1_异常"] = traceback.format_exc()[-800:]

        # ══ 格 2：机位改名 + ⌘Z ══
        try:
            out["⑥改名"] = set_name(page, "机位1-830")
            out["⑦改名后"] = page.evaluate(READ)
            page.locator("text=机位1").first.click()   # 焦点离开输入框（h5 早退）
            page.wait_for_timeout(800)
            out["⑧按Z前active"] = page.evaluate(READ)
            page.keyboard.press("Meta+z")
            page.wait_for_timeout(2_000)
            out["⑨按⌘Z后"] = page.evaluate(READ)
            page.keyboard.press("Meta+Shift+z")
            page.wait_for_timeout(2_000)
            out["⑩按⌘⇧Z后"] = page.evaluate(READ)
        except Exception:
            out["格2_异常"] = traceback.format_exc()[-800:]

        # ══ 格 3：时间轴缩放 + ⌘Z ══
        try:
            open_timeline(page)
            out["⑪zoom_改前"] = page.evaluate(READ)
            out["⑫改zoom"] = change_range(page, "zoom", 75)
            out["⑬改zoom后"] = page.evaluate(READ)
            page.keyboard.press("Meta+z")
            page.wait_for_timeout(2_000)
            out["⑭按⌘Z后"] = page.evaluate(READ)
        except Exception:
            out["格3_异常"] = traceback.format_exc()[-800:]

        # ══ 格 4：T（俯视视角）⟹ 截图对（视图变了没有，DOM 读数看不出来）══
        try:
            SHOTS.mkdir(exist_ok=True)
            page.screenshot(path=str(SHOTS / "830_T_before.png"))
            page.keyboard.press("t")
            page.wait_for_timeout(3_000)
            page.screenshot(path=str(SHOTS / "830_T_after.png"))
            out["⑮T后"] = page.evaluate(READ)
        except Exception:
            out["格4_异常"] = traceback.format_exc()[-800:]

        # ══ 复原 ══
        try:
            out["复原_FOV"] = change_range(page, "fov", 67)
            out["复原_改名"] = set_name(page, "机位1")
            out["复原后"] = page.evaluate(READ)
        except Exception:
            out["复原_异常"] = traceback.format_exc()[-800:]

        # ══ 干净关台 → 刷新 → 全新 context 回读 ══
        try:
            close_desk(page)
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(12_000)
            open_desk(page)
            select_camera(page)
            out["⑯同context回读"] = page.evaluate(READ)
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
            out["⑰全新context回读"] = p2.evaluate(READ)
            ctx2.close()
        except Exception:
            out["回读_异常"] = traceback.format_exc()[-800:]
        br.close()


if __name__ == "__main__":
    main()
