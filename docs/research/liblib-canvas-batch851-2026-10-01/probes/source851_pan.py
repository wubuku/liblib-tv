#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 851 源站探针（**只读**·第四版）：**按住** WASDQE 移动视口。

## ★ 为什么前三版都测成「无效」——★ 口径错，不是源站没实现

★ 读源站 chunk（`0fmehki05gkzw.js.js`）读出的**逐字实现**：

```js
// keydown（捕获阶段，window）
if(hX.has(r)&&!(e.ctrlKey||e.metaKey)){e.preventDefault(),oo(r,e);return}
// oo：只「登记」，不直接移动
oo=(0,o.useCallback)((e,t)=>{nK.current.add(e),nW.current=t.shiftKey,
  null===nQ.current&&(nq.current=performance.now()-16,nQ.current=window.requestAnimationFrame(oi))},[oi]);
// oi：每帧按「当前仍按住的键」移动相机
oi=(0,o.useCallback)(e=>{nQ.current=null;let t=nK.current;if(0===t.size)return; …
  if(t.has("w"))d.add(o), t.has("s")d.sub(o), t.has("d")d.add(c), t.has("a")d.sub(c),
  t.has("e")d.add(s), t.has("q")d.sub(s);
  if(d.lengthSq()>0){let e=1.2*Math.max(r.position.distanceTo(n.target),.5)*(nW.current?3:1);
    d.normalize().multiplyScalar(e*i), r.position.add(d), n.target.add(d), n.update();} …},[oa,n0]);
// keyup
hX.has(t)&&(nK.current.delete(t), …, 0===nK.current.size&&oa());
```

★ ⇒ ★★ **WASDQE 是「按住连续平移」**：keydown 只把键**加进 Set**，
真正的位移在 **requestAnimationFrame 回调**里按「Set 里仍存在的键」算；
**keyup 会把键从 Set 删掉**。
★ ⇒ ⟹ ⟹ ★ **`keyboard.press`（按下即松开）在下一帧之前就把键删了 ⟹ ⟹ 相机一帧都没动**
⟹ ⟹ 前三版测出的「全零差异」是**探针口径错误**，**不是**源站没实现。

## ★ 本版做法

★ `keyboard.down(k)` ⟹ ⟹ **保持 350ms**（≈21 帧）⟹ ⟹ `keyboard.up(k)`
⟹ ⟹ 每键之前先按 **H** 复位（保证同口径）⟹ ⟹ 记像素差。

## ★ 方向判据（★ 用**角色蓝色像素的包围盒**，六个键各自可判定）

源站角色是蓝色人偶 ⟹ ⟹ 在视口截图里提取「蓝像素」的包围盒与面积：

| 键 | 源站语义（读码） | 画面应表现为 |
| --- | --- | --- |
| W | 沿相机前向**前进** | 角色**变大**（面积↑）|
| S | 沿相机前向**后退** | 角色**变小**（面积↓）|
| D | 沿 right=forward×up **右移** | 角色在画面里**左移**（bbox.x↓）|
| A | 沿 right **左移** | 角色在画面里**右移**（bbox.x↑）|
| E | 沿 up **上升** | 角色在画面里**下移**（bbox.y↑）|
| Q | 沿 up **下降** | 角色在画面里**上移**（bbox.y↓）|

★ 另测 **Shift 加速对照**：源站步长 ×3。

## ★ 只读保证

★ 只按键盘（T／H／WASDQE／Shift）⟹ ⟹ 全是视图操作 ⟹ ⟹ 不改画布结构、不触发付费控件。

## 输出

  raw/source-851-pan.json
  images/851pan_*.png
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
HOLD_MS = 350
KEYS = ["w", "a", "s", "d", "q", "e"]

READ = r"""()=>{
  const a=document.activeElement;
  const inputs=Array.from(document.querySelectorAll('input,textarea'))
    .filter(e=>e.getBoundingClientRect().x>1600)
    .map(e=>({b:[Math.round(e.getBoundingClientRect().x),Math.round(e.getBoundingClientRect().y)],v:e.value}));
  return {active:{tag:a?a.tagName:'',type:a?(a.type||''):'',
                  isEditable:a?(a.tagName==='INPUT'||a.tagName==='TEXTAREA'||a.isContentEditable):false},
          右栏输入框:inputs};}"""


def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(600)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(8_000)


def shot(page, name):
    p = SHOTS / ("851pan_%s.png" % name)
    p.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(p), clip=CLIP)
    return p


def diff_px(a, b):
    ia = Image.open(a).convert("RGB")
    ib = Image.open(b).convert("RGB")
    d = ImageChops.difference(ia, ib)
    return sum(1 for px in d.getdata() if px[0] or px[1] or px[2])


def blue_box(path):
    """提取**蓝色角色像素**的包围盒与面积（★ 方向判据的载体）"""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    minx, miny, maxx, maxy, n = w, h, -1, -1, 0
    for y in range(0, h, 1):
        for x in range(0, w, 1):
            r, g, b = px[x, y]
            if b > 90 and b - r > 40 and b - g > 25:
                n += 1
                if x < minx:
                    minx = x
                if x > maxx:
                    maxx = x
                if y < miny:
                    miny = y
                if y > maxy:
                    maxy = y
    if n == 0:
        return {"面积": 0, "x0": -1, "y0": -1, "x1": -1, "y1": -1, "宽": 0, "高": 0}
    return {"面积": n, "x0": minx, "y0": miny, "x1": maxx, "y1": maxy,
            "宽": maxx - minx, "高": maxy - miny}


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
            # ★ 点真正的 3D 视口 canvas（index 1）⟹ ⟹ 焦点不会落在输入框
            try:
                pg.evaluate("()=>{const c=document.querySelectorAll('canvas')[1];"
                            "if(c){const r=c.getBoundingClientRect();"
                            "window.__cxy=[r.x+r.width/2,r.y+r.height/2];}}")
                xy = pg.evaluate("()=>window.__cxy")
                if xy:
                    pg.mouse.click(xy[0], xy[1])
                    pg.wait_for_timeout(1_200)
            except Exception:
                out["★点视口异常"] = traceback.format_exc()[-400:]
            out["①起点"] = pg.evaluate(READ)

            def reset():
                pg.keyboard.press("h")
                pg.wait_for_timeout(1_200)

            # ★ 基线（按 H 后的标准位姿）
            reset()
            base = shot(pg, "base")
            out["②基线蓝盒"] = blue_box(base)

            for k in KEYS:
                try:
                    reset()
                    b0 = shot(pg, "%s-base" % k)
                    box0 = blue_box(b0)
                    # ★ ★★ 按住不放
                    pg.keyboard.down(k)
                    pg.wait_for_timeout(HOLD_MS)
                    pg.keyboard.up(k)
                    pg.wait_for_timeout(700)
                    a1 = shot(pg, "%s-after" % k)
                    box1 = blue_box(a1)
                    out["③按%s" % k.upper()] = {
                        "差异像素": diff_px(b0, a1),
                        "蓝盒前": box0, "蓝盒后": box1,
                        "面积变化": box1["面积"] - box0["面积"],
                        "x0变化": box1["x0"] - box0["x0"],
                        "y0变化": box1["y0"] - box0["y0"],
                    }
                except Exception:
                    out["★按%s异常" % k.upper()] = traceback.format_exc()[-400:]

            # ★ Shift 加速对照：按住 Shift + w
            try:
                reset()
                b0 = shot(pg, "shift-base")
                box0 = blue_box(b0)
                pg.keyboard.down("Shift")
                pg.keyboard.down("w")
                pg.wait_for_timeout(HOLD_MS)
                pg.keyboard.up("w")
                pg.keyboard.up("Shift")
                pg.wait_for_timeout(700)
                a1 = shot(pg, "shift-after")
                box1 = blue_box(a1)
                out["④Shift加W"] = {
                    "差异像素": diff_px(b0, a1),
                    "蓝盒前": box0, "蓝盒后": box1,
                    "面积变化": box1["面积"] - box0["面积"],
                }
            except Exception:
                out["★Shift异常"] = traceback.format_exc()[-400:]

            out["⑤末态"] = pg.evaluate(READ)
            br.close()
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        RAW.mkdir(parents=True, exist_ok=True)
        (RAW / "source-851-pan.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", RAW / "source-851-pan.json")
        if out.get("异常"):
            print("异常：", out["异常"][-800:])
        print("--- 按住实测 ---")
        for k in KEYS + ["Shift加W"]:
            key = "④Shift加W" if k == "Shift加W" else "③按%s" % k.upper()
            v = out.get(key)
            if not v:
                continue
            print("   %-10s 差异像素=%-9d 面积Δ=%-8d x0Δ=%-6d y0Δ=%-6d"
                  % (k, v["差异像素"], v["面积变化"], v["x0变化"], v["y0变化"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
