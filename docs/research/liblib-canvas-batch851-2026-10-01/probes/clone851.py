#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 851 clone 探针：导演台的**视图类快捷键**（T／Y／H／裸 WASDQE）。

## ★ 判据：不是「画面变了」，而是「相机到了哪个坐标」

★ clone 把当前相机位姿暴露成 DOM 属性（`data-director-view-position` /
`data-director-view-target` / `data-director-view-fov`）⟹ ⟹ 本探针读**数值**，
⟹ ⟹ 期望值由**源站 chunk 的逐字公式**在 Python 里复刻出来（见下面的 `expect_*`）。

## ★ 五个必须钉死的语义

1. **T（俯视视角）**：`position = target + normalize(0,1,0.001) × |position−target|`
   ⟹ ⟹ **只改方向、不改视距**，且 `target` **完全不变**。
2. **Y（正面视角）**：`position = target + (0,0,1) × |position−target|`。
3. **H（重置视角）**：回到默认位姿 `{fov:45, position:[6.2,4.25,7.4], target:[0,1,0]}`。
4. ★★ **WASDQE 必须「按住」** ⟹ ⟹ **单击（按下即松开）不许产生任何位移**
   （源站 keydown 只登记键、keyup 把键删掉，位移在 rAF 回调里算）。
5. **WASDQE 是纯平移** ⟹ ⟹ `|position − target|` **不变**；
   方向：W 沿相机前向、A 沿 `−(forward×up)`、E 沿 `+up`；Shift 时步长 ×3。

## ★ 只读保证

★ 只按键盘 ＋ 读 DOM 属性 ⟹ ⟹ 不改画布数据、不触发付费控件。

## 输出

  raw/clone-851-viewkeys.json
  images/851clone_*.png
"""
import json
import math
import pathlib
import sys
import traceback

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch851-2026-10-01"
RAW = BATCH / "raw"
SHOTS = BATCH / "images"
BASE = "http://localhost:4317"

HOLD_MS = 350
DEFAULT_POSITION = (6.2, 4.25, 7.4)
DEFAULT_TARGET = (0.0, 1.0, 0.0)
DEFAULT_FOV = 45.0

# ★ 源站 `iK` 的方向向量（逐字）
PRESET_DIRECTIONS = {
    "top": (0.0, 1.0, 0.001),
    "front": (0.0, 0.0, 1.0),
}


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def scale(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def length(a):
    return math.sqrt(dot(a, a))


def norm(a, fallback=(0.0, 0.0, -1.0)):
    n = length(a)
    if n == 0:
        return fallback
    return (a[0] / n, a[1] / n, a[2] / n)


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def expect_preset(direction, position, target):
    """源站 `iK(preset)`：**只改方向、不改视距**"""
    d = PRESET_DIRECTIONS[direction]
    dist = length(sub(position, target))
    s = length(d) or 1.0
    return add(target, scale((d[0] / s, d[1] / s, d[2] / s), dist))


READ_VIEW = r"""()=>{
  const s=document.querySelector('[data-director-viewport]');
  if(!s)return null;
  return {
    position:(s.getAttribute('data-director-view-position')||'').split(',').map(Number),
    target:(s.getAttribute('data-director-view-target')||'').split(',').map(Number),
    fov:Number(s.getAttribute('data-director-view-fov')),
    view:s.getAttribute('data-director-view')||'',
    active:(()=>{const a=document.activeElement;
      return {tag:a?a.tagName:'',editable:a?!!a.closest('input,textarea,select,[contenteditable="true"]'):false};})()
  };}"""


def open_desk(pg):
    pg.goto(BASE + "/?batch851=1", wait_until="domcontentloaded")
    pg.wait_for_timeout(3000)
    pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
    pg.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
    pg.wait_for_timeout(1200)
    # ★ clone 的导演台入口是画布上的 `script-execution` 节点（按钮带 `data-open-director`）
    #   ⟹ ⟹ **不是**源站那个 `react-flow__node-director-console-3d`。
    node = pg.locator(".react-flow__node-script-execution").first
    try:
        node.scroll_into_view_if_needed(timeout=8000)
    except Exception:
        pass
    pg.wait_for_timeout(400)
    try:
        node.hover(timeout=8000)
        pg.wait_for_timeout(600)
    except Exception:
        pass
    pg.locator("[data-open-director]").first.click(timeout=15000)
    pg.wait_for_timeout(6000)
    pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")


def read_view(pg):
    v = pg.evaluate(READ_VIEW)
    if not v:
        return None
    return {
        "position": tuple(v["position"]),
        "target": tuple(v["target"]),
        "fov": v["fov"],
        "view": v["view"],
        "active": v["active"],
    }


def wait_stable_view(pg, tries=80):
    """等相机位姿**连续多次不变** ⟹ ⟹ 说明渲染与回读都稳了"""
    last = None
    stable = 0
    for _ in range(tries):
        v = read_view(pg)
        if v and v["position"] == last:
            stable += 1
            if stable >= 3:
                return v
        else:
            stable = 0
        if v:
            last = v["position"]
        pg.wait_for_timeout(250)
    return read_view(pg)


def shot(pg, name):
    p = SHOTS / ("851clone_%s.png" % name)
    p.parent.mkdir(parents=True, exist_ok=True)
    box = pg.evaluate(
        """()=>{const c=document.querySelector('[data-director-webgl-canvas] canvas')
          ||document.querySelector('[data-director-webgl-canvas]');
          if(!c)return null;const r=c.getBoundingClientRect();
          return {x:Math.round(r.x),y:Math.round(r.y),
                  w:Math.round(r.width),h:Math.round(r.height)};}"""
    )
    if not box or box["w"] <= 0:
        pg.screenshot(path=str(p))
    else:
        pg.screenshot(path=str(p), clip=box)
    return p


def diff_px(a, b):
    ia = Image.open(a).convert("RGB")
    ib = Image.open(b).convert("RGB")
    if ia.size != ib.size:
        return -1
    d = ImageChops.difference(ia, ib)
    return sum(1 for px in d.getdata() if px[0] or px[1] or px[2])


def main() -> int:
    out = {}
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            ctx = br.new_context(viewport={"width": 1600, "height": 900},
                                 locale="zh-CN")
            pg = ctx.new_page()
            pg.set_default_timeout(30_000)
            open_desk(pg)
            base = wait_stable_view(pg)
            out["①开台"] = base
            if not base or len(base["position"]) != 3:
                out["★异常"] = "没读到相机位姿属性"
                br.close()
                return 1
            # ★ 点一下视口空白处 ⟹ ⟹ 焦点不要落在输入框里
            pg.mouse.click(700, 500)
            pg.wait_for_timeout(600)
            out["①开台_active"] = read_view(pg)["active"]

            def reset():
                pg.keyboard.press("h")
                pg.wait_for_timeout(900)
                return wait_stable_view(pg)

            # ══ T（俯视视角）
            reset()
            v0 = read_view(pg)
            pg.keyboard.press("t")
            pg.wait_for_timeout(900)
            v1 = wait_stable_view(pg)
            out["②按T"] = {
                "前": v0, "后": v1,
                "期望position": expect_preset("top", v0["position"], v0["target"]),
            }

            # ══ Y（正面视角）
            reset()
            v0 = read_view(pg)
            pg.keyboard.press("y")
            pg.wait_for_timeout(900)
            v1 = wait_stable_view(pg)
            out["③按Y"] = {
                "前": v0, "后": v1,
                "期望position": expect_preset("front", v0["position"], v0["target"]),
            }

            # ══ H（重置视角）
            reset()
            pg.keyboard.press("h")
            pg.wait_for_timeout(900)
            v1 = wait_stable_view(pg)
            out["④按H"] = {"后": v1}

            # ══ ★ 单击 W（按下即松开）⟹ ⟹ **不许有位移**
            reset()
            v0 = read_view(pg)
            pg.keyboard.press("w")
            pg.wait_for_timeout(900)
            v1 = wait_stable_view(pg)
            out["⑤单击W"] = {"前": v0, "后": v1}

            # ══ ★ 按住 W
            for key in ["w", "a", "e", "q"]:
                reset()
                v0 = read_view(pg)
                pg.keyboard.down(key)
                pg.wait_for_timeout(HOLD_MS)
                pg.keyboard.up(key)
                pg.wait_for_timeout(700)
                v1 = wait_stable_view(pg)
                # ★ 相机的**前向**是 `getWorldDirection()` ⟹ ⟹ 对 lookAt(target) 的相机
                #   就是 normalize(target − position) ⟹ ⟹ **不是** position − target。
                forward = norm(sub(v0["target"], v0["position"]))
                right = norm(cross(forward, (0.0, 1.0, 0.0)), (1.0, 0.0, 0.0))
                up = (0.0, 1.0, 0.0)
                expected = {
                    "w": forward,
                    "a": scale(right, -1.0),
                    "e": up,
                    "q": scale(up, -1.0),
                }[key]
                out["⑥按住%s" % key.upper()] = {
                    "前": v0, "后": v1,
                    "位移": sub(v1["position"], v0["position"]),
                    "期望方向": expected,
                    "与期望点积": dot(sub(v1["position"], v0["position"]), expected),
                    "位移长度": length(sub(v1["position"], v0["position"])),
                    "视距前": length(sub(v0["position"], v0["target"])),
                    "视距后": length(sub(v1["position"], v1["target"])),
                    "target位移": sub(v1["target"], v0["target"]),
                }

            # ══ ★ Shift 加速
            reset()
            v0 = read_view(pg)
            pg.keyboard.down("Shift")
            pg.keyboard.down("w")
            pg.wait_for_timeout(HOLD_MS)
            pg.keyboard.up("w")
            pg.keyboard.up("Shift")
            pg.wait_for_timeout(700)
            v1 = wait_stable_view(pg)
            out["⑦按住Shift+W"] = {
                "前": v0, "后": v1,
                "位移长度": length(sub(v1["position"], v0["position"])),
            }

            out["⑧末态_active"] = read_view(pg)["active"]
            out["⑧末态_view"] = read_view(pg)["view"]
            br.close()
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        RAW.mkdir(parents=True, exist_ok=True)
        (RAW / "clone-851-viewkeys.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", RAW / "clone-851-viewkeys.json")
        if out.get("异常"):
            print("异常：", out["异常"][-1200:])
        for k in sorted(out):
            v = out[k]
            if isinstance(v, dict) and "后" in v:
                after = v["后"]
                before = v.get("前")
                line = "   %-14s position=%s target=%s" % (
                    k, after["position"], after["target"])
                if "期望position" in v:
                    line += "\n%22s期望position=%s" % ("", v["期望position"])
                if "位移长度" in v:
                    line += "\n%22s位移长度=%.4f 视距前=%.4f 视距后=%.4f 点积=%.4f" % (
                        "", v["位移长度"], v.get("视距前", 0), v.get("视距后", 0),
                        v.get("与期望点积", 0))
                if before:
                    line += "\n%22sΔposition=%s" % (
                        "", tuple(round(before["position"][i] - after["position"][i], 5)
                                 for i in range(3)))
                print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
