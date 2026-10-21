#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 830 源站实测：①「时间轴缩放」关台重开/刷新后留不留（599/604 的原题）
                          ② 源站导演台的撤销（快捷键 = Z）能不能撤、跨关台还在不在。

★ 侦察定位（本批先做的）：
  - 源站「时间轴缩放」＝ `input[type=range][aria-label="时间轴缩放"]`，
    **min 0 / max 100 / 当前值 44**，@1592,957 71×24（透明原生控件）
  - clone 同名控件 `DirectorTimeline.tsx:1339` min=0 max=100 ⟹ 量程一致
  - 源站「快捷键」面板：**撤销 = Z**（无修饰键）⟹ clone 绑 Cmd/Ctrl+Z ⟹ 不一致
★ 纪律：不点生成/付费控件；测完把 FOV 与时间轴缩放**复原**并回读验证。
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_desk830_measure.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

READ_ZOOM = """()=>{
  const e=document.querySelector('[aria-label="时间轴缩放"]');
  if(!e) return null;
  const r=e.getBoundingClientRect();
  return {value:e.value,min:e.min,max:e.max,
          box:{x:Math.round(r.x),y:Math.round(r.y),
               w:Math.round(r.width),h:Math.round(r.height)}};
}"""

READ_FOV = """()=>{
  const e=document.querySelector('input[type=range][min="15"][max="90"]');
  if(!e) return null;
  const r=e.getBoundingClientRect();
  return {value:e.value,min:e.min,max:e.max,
          box:{x:Math.round(r.x),y:Math.round(r.y),
               w:Math.round(r.width),h:Math.round(r.height)}};
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
    if page.evaluate(READ_ZOOM):
        return "already"
    page.locator("[aria-label='动画时间轴']:visible").first.click()
    page.wait_for_timeout(3_500)
    return "opened"


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


def set_range(page, read_js, want, label):
    rng = page.evaluate(read_js)
    if not rng:
        return {"error": "no %s input" % label}
    span = float(rng["max"]) - float(rng["min"])
    frac = (float(want) - float(rng["min"])) / span
    tries = []
    for f in (frac, frac - 0.02, frac + 0.02, frac - 0.04):
        act = click_range(page, rng, max(0.0, min(1.0, f)))
        now = page.evaluate(read_js)
        v = now["value"] if now else None
        tries.append({**act, "value_after": v})
        if v == str(want):
            return {"before": rng["value"], "after": v, "tries": tries}
    return {"before": rng["value"], "after": None, "tries": tries,
            "★没调到": True}


def focus_desk(page):
    """把焦点从输入框挪走（点标题文字，非可编辑元素）⟹ 键快捷键才会生效。"""
    page.locator("[data-director-workspace] h1, [role=dialog] h1").first.click()
    page.wait_for_timeout(400)


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

        # ── ① 时间轴缩放：改 → 关台重开 → 刷新后
        out["①开台_缩放"] = {"timeline": open_timeline(page),
                             "zoom": page.evaluate(READ_ZOOM)}
        out["②改缩放"] = set_range(page, READ_ZOOM, 70, "zoom")
        out["③改缩放后"] = page.evaluate(READ_ZOOM)
        close_desk(page)
        open_desk(page)
        out["④关台重开后_缩放"] = {"timeline": open_timeline(page),
                                  "zoom": page.evaluate(READ_ZOOM)}
        page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(12_000)
        open_desk(page)
        out["⑤刷新后_缩放"] = {"timeline": open_timeline(page),
                              "zoom": page.evaluate(READ_ZOOM)}

        # ── ② 撤销：同会话内
        page.locator("text=机位1").first.click()
        page.wait_for_timeout(2_500)
        out["⑥FOV_初始"] = page.evaluate(READ_FOV)
        out["⑦改FOV"] = set_range(page, READ_FOV, 40, "fov")
        out["⑧改FOV后"] = page.evaluate(READ_FOV)
        focus_desk(page)
        page.keyboard.press("z")
        page.wait_for_timeout(1_500)
        out["⑨按Z后"] = page.evaluate(READ_FOV)
        page.keyboard.press("z")
        page.wait_for_timeout(1_500)
        out["⑩再按Z后"] = page.evaluate(READ_FOV)
        # Cmd+Z 呢？
        focus_desk(page)
        page.keyboard.press("Meta+z")
        page.wait_for_timeout(1_500)
        out["⑪按CmdZ后"] = page.evaluate(READ_FOV)

        # ── ③ 撤销跨关台重开
        out["⑫再改FOV"] = set_range(page, READ_FOV, 45, "fov")
        out["⑬改FOV后2"] = page.evaluate(READ_FOV)
        close_desk(page)
        open_desk(page)
        page.locator("text=机位1").first.click()
        page.wait_for_timeout(2_500)
        out["⑭重开后_FOV"] = page.evaluate(READ_FOV)
        focus_desk(page)
        page.keyboard.press("z")
        page.wait_for_timeout(1_500)
        out["⑮重开后按Z"] = page.evaluate(READ_FOV)

        # ── ④ 复原：FOV 回 67、缩放回 44（干净关台 → 刷新 → 回读）
        out["复原动作_FOV"] = set_range(page, READ_FOV, 67, "fov")
        out["复原动作_缩放"] = set_range(page, READ_ZOOM, 44, "zoom")
        close_desk(page)
        page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(12_000)
        open_desk(page)
        open_timeline(page)
        out["复原回读_缩放"] = page.evaluate(READ_ZOOM)
        page.locator("text=机位1").first.click()
        page.wait_for_timeout(2_500)
        out["复原回读_FOV"] = page.evaluate(READ_FOV)
        out["★已复原"] = (out["复原回读_FOV"] or {}).get("value") == "67" \
            and (out["复原回读_缩放"] or {}).get("value") == "44"
        ctx.close()
        br.close()


if __name__ == "__main__":
    main()
