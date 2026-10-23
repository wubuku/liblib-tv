#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 851 源站探针（**只读**·第五版）：**Y（正面视角）** ＋ **T/H 在机位视角下的行为**。

## ★ 为什么还要这一版

★ 读码已经给出确切语义（`iK("top")` / `iK("front")` / `iK("default")`），
★ 但★ **读码 ≠ 画面** ⟹ ⟹ 视角类的**朝向**必须用画面取证（★ 记忆里的老规矩：
「class 名是作者意图，计算值是浏览器裁决」）。
★ 而且 T/Y 在**机位视角**下按会怎样，读码里**看不出来**（`setEditorCameraPose` 只改「编辑器相机」）。

## ★ 读数

* 视口像素（clip 只取 3D 内容区）
* ★ **顶部「导演视角／机位视角」两个按钮的白底高亮态** ⟹ ⟹ 用来判定「当前处于哪个视图模式」
  （读码：`eJ("director")` 是切模式 ⟹ ⟹ 按 H 后应当切回导演视角 ⟹ ⟹ 高亮态会变）

## ★ 只读保证

★ 只按键盘（T／H／Y）＋ 点顶部两个模式按钮 ⟹ ⟹ 全是视图操作。

## 输出

  raw/source-851-viewmodes.json
  images/851vm_*.png
"""
import json
import pathlib
import sys
import traceback

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch851-2026-10-01"
RAW = BATCH / "raw"
SHOTS = BATCH / "images"

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")
CLIP = {"x": 281, "y": 100, "width": 1359, "height": 980}

READ = r"""()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
  const txt=(e)=>(e.textContent||'').trim().replace(/\s+/g,' ');
  // ★ 顶部两个模式按钮 ⟹ ⟹ 白色高亮 = 当前选中
  const modes=Array.from(document.querySelectorAll('button'))
    .filter(e=>{const r=e.getBoundingClientRect();
      return r.y>=8&&r.y<=48&&r.x>820&&r.x<1100&&(txt(e)==='导演视角'||txt(e)==='机位视角');})
    .map(e=>({t:txt(e),b:box(e),
              白底:String(e.className||'').includes('bg-white'),
              文字:String(e.className||'').match(/text-[a-z0-9-]+/g)||[]}));
  const inputs=Array.from(document.querySelectorAll('input'))
    .filter(e=>e.getBoundingClientRect().x>1600)
    .map(e=>({b:[Math.round(e.getBoundingClientRect().x),Math.round(e.getBoundingClientRect().y)],
              type:e.type,value:e.value}));
  return {模式:modes, 右栏输入框:inputs};}"""


def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(600)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(8_000)


def shot(page, name):
    p = SHOTS / ("851vm_%s.png" % name)
    p.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(p), clip=CLIP)
    return p


def diff_px(a, b):
    ia = Image.open(a).convert("RGB")
    ib = Image.open(b).convert("RGB")
    d = ImageChops.difference(ia, ib)
    return sum(1 for px in d.getdata() if px[0] or px[1] or px[2])


def main() -> int:
    out = {}
    try:
        cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                                 locale="zh-CN")
            ctx.add_cookies([{"name": c["name"], "value": c["value"],
                              "domain": c["domain"], "path": c.get("path", "/")} for c in cookies])
            pg = ctx.new_page()
            pg.set_default_timeout(30_000)
            pg.goto(URL, wait_until="domcontentloaded", timeout=90_000)
            pg.wait_for_timeout(12_000)
            el = pg.query_selector("text=下次再说")
            if el:
                el.click()
                pg.wait_for_timeout(900)

            open_desk(pg)
            pg.wait_for_timeout(1_500)
            out["①开台_模式"] = pg.evaluate(READ)["模式"]

            def mode_state():
                return {m["t"]: m["白底"] for m in pg.evaluate(READ)["模式"]}

            # ══ 导演视角下：Y（正面视角）
            base = shot(pg, "director-base")
            pg.keyboard.press("y")
            pg.wait_for_timeout(1_800)
            vy = shot(pg, "director-Y")
            out["②导演视角按Y_差异"] = diff_px(base, vy)
            out["②导演视角按Y_模式"] = mode_state()
            # ★ 按 H 复位
            pg.keyboard.press("h")
            pg.wait_for_timeout(1_800)
            out["③Y后按H_差异"] = diff_px(base, shot(pg, "director-Y-then-H"))
            out["③Y后按H_模式"] = mode_state()

            # ══ 切到机位视角
            pg.locator("button:has-text('机位视角')").first.click()
            pg.wait_for_timeout(2_500)
            out["④切机位视角_模式"] = mode_state()
            cbase = shot(pg, "camera-base")

            # ★ 机位视角下按 T
            pg.keyboard.press("t")
            pg.wait_for_timeout(1_800)
            ct = shot(pg, "camera-T")
            out["⑤机位视角按T_差异"] = diff_px(cbase, ct)
            out["⑤机位视角按T_模式"] = mode_state()

            # ★ 机位视角下按 H ⟹ ⟹ 读码说 H 会 eJ("director") ⟹ ⟹ 应当切回导演视角
            pg.keyboard.press("h")
            pg.wait_for_timeout(2_000)
            ch = shot(pg, "camera-H")
            out["⑥机位视角按H_差异"] = diff_px(cbase, ch)
            out["⑥机位视角按H_模式"] = mode_state()
            out["⑥机位视角按H_右栏输入框数"] = len(pg.evaluate(READ)["右栏输入框"])

            br.close()
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        RAW.mkdir(parents=True, exist_ok=True)
        (RAW / "source-851-viewmodes.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", RAW / "source-851-viewmodes.json")
        if out.get("异常"):
            print("异常：", out["异常"][-800:])
        for k in sorted(out):
            if isinstance(out[k], (int, dict, list)):
                print("   %-26s %s" % (k, json.dumps(out[k], ensure_ascii=False)[:220]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
