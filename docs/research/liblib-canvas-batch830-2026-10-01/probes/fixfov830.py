#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 830 修复探针：把源站测试项目的机位 FOV **修回 67**。

★ 出了什么事（v10 的复原函数）：
  它的判据是「点一下，**值变了**就返回」⟹ 复原 67 时第一击**正好命中 67**
  （tries[0].value_after = "67"）⟹ 判据不满足「变了」⟹ **继续点** ⟹
  第二击把 FOV 改成了 **64** ⟹ 而 FOV 会**落盘到服务端** ⟹ 用户的项目被改脏了。
  ⟹ ★★ 本批第三次「探针自己的判据写错」：
     前两次是「手打目标值 70 打不中」「focus_desk 的选择器在源站不存在」。

★ 修法（这次判据是「**等于目标值**就停」）：
  ① 首选：点轨道，按当前值重算 frac，逐次逼近，**命中即停**；
  ② 兜底：直接改 FOV 旁边的数字输入框（源站 FOV 有 number input）⟹ 精确、无歧义。
  ★ 修完必须：**干净关台 → 刷新 → 全新 context 回读** ⟹ 读到 67 才算修好。
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_desk830_fixfov.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

READ = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const fov=document.querySelector('input[type=range][min="15"][max="90"]');
  const num=Array.from(document.querySelectorAll('input'))
    .filter(e=>e.type==='number'&&e.getBoundingClientRect().x>1800
      &&e.getBoundingClientRect().y>800&&e.getBoundingClientRect().y<900)
    .map(e=>({value:e.value,box:box(e)}));
  const nameInput=Array.from(document.querySelectorAll('input'))
    .filter(e=>e.type==='text'&&e.getBoundingClientRect().x>1600
      &&e.getBoundingClientRect().y<400)
    .map(e=>({value:e.value,box:box(e)}));
  return {fov: fov?{value:fov.value,min:fov.min,max:fov.max,box:box(fov)}:null,
          fovNumInputs: num, names: nameInput};
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


def set_fov_by_click(page, want, rounds=8):
    """★ 判据是「**等于目标值**就停」⟹ 命中即停，不多点。"""
    log = []
    for _ in range(rounds):
        st = page.evaluate(READ)
        rng = st.get("fov")
        if not rng:
            return {"error": "no fov"}
        cur = rng["value"]
        if cur == str(want):
            return {"ok": True, "tries": log}
        span = float(rng["max"]) - float(rng["min"])
        frac = (float(want) - float(rng["min"])) / span
        x = rng["box"]["x"] + int(rng["box"]["w"] * max(0.0, min(1.0, frac)))
        y = rng["box"]["y"] + rng["box"]["h"] // 2
        page.mouse.move(x, y)
        page.mouse.down()
        page.wait_for_timeout(120)
        page.mouse.up()
        page.wait_for_timeout(900)
        v = (page.evaluate(READ).get("fov") or {}).get("value")
        log.append({"frac": frac, "at": [x, y], "value_after": v})
    return {"ok": False, "tries": log}


def set_fov_by_number(page, want):
    """兜底：直接改 FOV 旁边的数字输入框。"""
    st = page.evaluate(READ)
    ns = st.get("fovNumInputs") or []
    if not ns:
        return {"error": "no fov number input"}
    tgt = ns[0]
    page.mouse.click(tgt["box"]["x"] + 10, tgt["box"]["y"] + tgt["box"]["h"] // 2)
    page.wait_for_timeout(400)
    page.keyboard.press("Meta+a")
    page.wait_for_timeout(150)
    page.keyboard.type(str(want), delay=90)
    page.keyboard.press("Enter")
    page.wait_for_timeout(2_000)
    return {"typed": str(want),
            "fov_now": (page.evaluate(READ).get("fov") or {}).get("value"),
            "num_now": (page.evaluate(READ).get("fovNumInputs") or [{}])[0].get("value")}


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
        out["①改前"] = page.evaluate(READ)
        try:
            out["②点轨道"] = set_fov_by_click(page, 67)
            if not out["②点轨道"].get("ok"):
                out["③改数字框"] = set_fov_by_number(page, 67)
            out["④改后"] = page.evaluate(READ)
        except Exception:
            out["修FOV_异常"] = traceback.format_exc()[-800:]
        try:
            close_desk(page)
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(12_000)
            open_desk(page)
            select_camera(page)
            out["⑤同context回读"] = page.evaluate(READ)
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
            out["⑥全新context回读"] = p2.evaluate(READ)
            out["★已复原(新context)"] = \
                (out["⑥全新context回读"].get("fov") or {}).get("value") == "67"
            ctx2.close()
        except Exception:
            out["回读_异常"] = traceback.format_exc()[-800:]
        br.close()


if __name__ == "__main__":
    main()
