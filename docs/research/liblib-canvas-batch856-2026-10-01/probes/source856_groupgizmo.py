#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 856 源站探针之二：选中组之后，**画布上有没有 gizmo**。

## ★ 为什么单独一个探针

★ 探针一（`source856_groupinspector.py`）已经证明：
  源站的**组检查器只有「名称」一个字段**（没有位置／旋转／缩放）。
★ ⟹ ⟹ 那组**还能不能动**？⟹ ⟹ 只有两条可能：
  ① 画布上的 **gizmo**（像角色那样有轴）；
  ② **组轨道**（时间轴上的关键帧）。

★ clone 两条都有：Inspector 的三个字段 ＋ Viewport 的组 gizmo 拖拽。
⟹ ⟹ 本探针要回答：**源站有没有 ①**。

## ★ 读数策略

★ 源站的 gizmo 是 three.js 的 TransformControls ⟹ ⟹ 在 DOM 上**读不到**。
⟹ ⟹ 只能靠**像素**：把画布区域截图 ⟹ ⟹ 比较「选中角色前后」与「选中组前后」
  的**像素差** ⟹ ⟹ 有 gizmo ⟹ ⟹ 会出现三轴箭头／彩色线段。

★ ★ 为了让像素差可比，**两次截图必须同尺寸同位置**。
★ ★ 还要**逐像素数**出变化的像素数 ⟹ ⟹ 判据是**数字**，不是「看着像」。

## ★ 副作用与复原

★ 建组会存进用户工程 ⟹ ⟹ 最后解组复原；兜底 ⌘Z。

## 输出
  raw/source-856-groupgizmo.json
  images/856gizmo_*.png
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch856-2026-10-01"
RAW = BATCH / "raw"
SHOTS = BATCH / "images"

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 只截**画布区**（不含右侧面板）⟹ ⟹ 两张图严格同尺寸
CANVAS_CLIP = {"x": 0, "y": 100, "width": 900, "height": 700}

CAMERA_ICON = 'x="1.75"'
CHARACTER_ICON = "8.3125"

READ_ROWS = r"""()=>{
  const out = [];
  document.querySelectorAll('span').forEach(e=>{
    const cls = e.className || '';
    if(typeof cls !== 'string' || cls.indexOf('truncate pl-1') < 0) return;
    const r = e.getBoundingClientRect();
    if(r.width<=0||r.height<=0) return;
    if(r.x > 300) return;
    const t = (e.textContent||'').trim();
    if(!t) return;
    const row = e.parentElement;
    let icon = '';
    if(row){
      const svg = row.querySelector('span svg') || row.querySelector('svg');
      icon = svg ? svg.innerHTML.slice(0, 160) : '';
    }
    out.push({label:t, x:Math.round(r.x), y:Math.round(r.y),
              w:Math.round(r.width), h:Math.round(r.height), icon});
  });
  out.sort((a,b)=>a.y-b.y);
  return out;
}"""


def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(600)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(8_000)


def rows(page):
    return page.evaluate(READ_ROWS)


def kind_of(row):
    icon = row.get("icon") or ""
    if CAMERA_ICON in icon:
        return "camera"
    if CHARACTER_ICON in icon:
        return "character"
    return "other"


def click_row(page, row, modifier=None):
    x = row["x"] + row["w"] / 2
    y = row["y"] + row["h"] / 2
    if modifier:
        page.keyboard.down(modifier)
    page.mouse.click(x, y)
    if modifier:
        page.keyboard.up(modifier)
    page.wait_for_timeout(500)


def diff_pixels(path_a, path_b):
    """★ 逐像素数两张图有多少点不同 ⟹ ⟹ 判据是**数字**。"""
    from PIL import Image
    a = Image.open(path_a).convert("RGB")
    b = Image.open(path_b).convert("RGB")
    if a.size != b.size:
        return {"尺寸不同": [a.size, b.size]}
    pa = a.load()
    pb = b.load()
    w, h = a.size
    changed = 0
    bbox = [w, h, 0, 0]
    for y in range(h):
        for x in range(w):
            if pa[x, y] != pb[x, y]:
                changed += 1
                if x < bbox[0]:
                    bbox[0] = x
                if y < bbox[1]:
                    bbox[1] = y
                if x > bbox[2]:
                    bbox[2] = x
                if y > bbox[3]:
                    bbox[3] = y
    return {"尺寸": [w, h], "不同像素数": changed,
            "变化包围盒": bbox,
            "占比": round(changed / float(w * h), 6)}


def main() -> int:
    out = {}
    try:
        cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                                 locale="zh-CN")
            ctx.add_cookies([{"name": c["name"], "value": c["value"],
                              "domain": c["domain"], "path": c.get("path", "/")}
                             for c in cookies])
            pg = ctx.new_page()
            pg.set_default_timeout(30_000)
            pg.goto(URL, wait_until="domcontentloaded", timeout=90_000)
            pg.wait_for_timeout(12_000)
            el = pg.query_selector("text=下次再说")
            if el:
                el.click()
                pg.wait_for_timeout(900)
            open_desk(pg)
            SHOTS.mkdir(parents=True, exist_ok=True)

            base = rows(pg)
            out["①基线类别"] = [kind_of(r) for r in base]
            cam = next((r for r in base if kind_of(r) == "camera"), None)
            chr_ = next((r for r in base if kind_of(r) == "character"), None)

            # ── 参照组：选中**角色** ⟹ 源站会显示 gizmo ⟹ ⟹ 这是**阳性对照**
            p_none = SHOTS / "856gizmo_00-none.png"
            pg.screenshot(path=str(p_none), clip=CANVAS_CLIP)

            if chr_:
                click_row(pg, chr_)
                pg.wait_for_timeout(1200)
                p_char = SHOTS / "856gizmo_01-character.png"
                pg.screenshot(path=str(p_char), clip=CANVAS_CLIP)
                out["②选中角色后 vs 未选中"] = diff_pixels(p_none, p_char)

            # ── 主角：建组 ⟹ 选中**组** ⟹ 看画布上有没有 gizmo
            if cam and chr_:
                click_row(pg, cam)
                click_row(pg, chr_, modifier="Meta")
                pg.keyboard.press("Meta+g")
                pg.wait_for_timeout(1400)
                after = rows(pg)
                out["③⌘G后类别"] = [kind_of(r) for r in after]
                grp = next((r for r in after if kind_of(r) == "other"), None)
                if grp:
                    click_row(pg, grp)
                    pg.wait_for_timeout(1400)
                    p_group = SHOTS / "856gizmo_02-group.png"
                    pg.screenshot(path=str(p_group), clip=CANVAS_CLIP)
                    out["④选中组后 vs 建组后未选组"] = diff_pixels(
                        p_char if chr_ else p_none, p_group)
                    out["④选中组后 vs 未选中任何"] = diff_pixels(p_none, p_group)

            # ── 复原
            try:
                pg.keyboard.press("Meta+Shift+d")
                pg.wait_for_timeout(1400)
            except Exception:
                pass
            final = rows(pg)
            out["⑤复原后类别"] = [kind_of(r) for r in final]
            out["⑤是否回到基线"] = (
                [r["label"] for r in final] == [r["label"] for r in base]
            )

    except Exception:
        out["★异常"] = traceback.format_exc()[-2500:]
    finally:
        RAW.mkdir(parents=True, exist_ok=True)
        (RAW / "source-856-groupgizmo.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", RAW / "source-856-groupgizmo.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
