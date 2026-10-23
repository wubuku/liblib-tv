#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 851 源站探针（**只读**·第三版）：**WASDQE 到底能不能移动视口**？

## ★ 前两版的教训（★ 阴性读数必须先证明注入生效）

* **v1（source851_viewkeys.py）**：按右栏输入框读数 ⟹ 逐键差异 0。
  ★ 但那一轮右栏停在「3D场景」面板 ⟹ ⟹ 830 的 FOV 属于「导演视角」⟹ ⟹ **两轮不是同一块面板**，
  ⟹ ⟹ 「零差异」不可判定。
* **v2（source851_camkeys.py）**：改用**视口像素**⟹ ⟹ 抖动基线 = 0（读数是硬的）
  ⟹ ⟹ **T 有效**（俯视图，1.4M 像素差）、**H ≡「重置视角」按钮**（差 1492 且 bbox 全在按钮上）
  ⟹ ⟹ 但 **WASDQE 六键两两差异 = 0**。
* ★ **v2 的致命嫌疑**：点视口时用的是 `canvas.first` ⟹ ⟹ 那是**左上角 72×72 的小预览**，
  ⟹ ⟹ **从没点过真正的 3D 视口 canvas（index 1，全屏 1920x1080）**
  ⟹ ⟹ ⟹ WASDQE 的 handler 很可能挂在**那个 canvas** 上 ⟹ ⟹ 事件根本没送到它。

## ★ v3 的做法：把「条件」全部铺开

对每个**前置条件**组合，单独取基线，逐键 WASDQE，记录**视口像素差**：

| 条件 | 前置动作 |
| --- | --- |
| A 默认 | 开台后什么都不做（但**焦点明确点在 3D 视口 canvas 上**）|
| B 机位视角 | 切到「机位视角」|
| C 导演视角 | 切到「导演视角」|
| D 选中角色 | 点左列「角色A」|
| E 选中机位 | 点左列「机位1」|

★ 每个条件里都先按 **T** 一次（阳性对照：证明这条路径上键盘事件确实到达了应用层）
⟹ ⟹ 再按 **H** 复位 ⟹ ⟹ 然后才测 WASDQE。

## ★ 读数口径

* **视口像素**：clip = (281, 100, 1359, 980) ⟹ ⟹ 避开左列（x<280）、右栏（x>1640）
  ⟹ ⟹ 也避开**左上角 72×72 小预览**（它在 y<88）⟹ ⟹ 所以**只有 3D 内容**会贡献差异。
* **抖动基线**：同条件下不动、等 2 秒、两图之差（本轮实测 0 ⟹ ⟹ 任何非零都算真变化）。
* **activeElement**：每步都记 ⟹ ⟹ 证明按键送到了哪个元素。

## ★ 只读保证

★ 只按键盘 ＋ 点「重置视角」/「导演视角」/「机位视角」/场景树项 ⟹ ⟹ 全是**视图/选中**操作
⟹ ⟹ 不改画布结构、不触发付费控件 ⟹ ⟹ ⚡44 不参与；
★ 结尾改 FOV 后按 ⌘Z 复原。

## 输出

  raw/source-851-camkeys3.json
  images/851cam3_*.png
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

# ★ 视口 clip ⟹ ⟹ 只取 3D 内容区（避开左右面板与左上小预览）
CLIP = {"x": 281, "y": 100, "width": 1359, "height": 980}

READ = r"""()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
  const txt=(e)=>(e.textContent||'').trim().replace(/\s+/g,' ');
  const right=Array.from(document.querySelectorAll('input,textarea'))
    .filter(e=>e.getBoundingClientRect().x>1600)
    .map(e=>({t:e.tagName,type:e.type||'',value:e.value,
              aria:e.getAttribute('aria-label')||'',
              min:e.min||'',max:e.max||'',step:e.step||'',
              b:box(e)}))
    .sort((a,b)=>a.b[1]-b.b[1]||a.b[0]-a.b[0]);
  const canvases=Array.from(document.querySelectorAll('canvas')).map((e,i)=>({i,b:box(e)}));
  const a=document.activeElement;
  // ★ 场景树里被选中的项（★ 用来确认「选中态」真的变了）
  const sel=Array.from(document.querySelectorAll('div,span'))
    .filter(e=>{
      const c=String(e.className||'');
      return /text-white|bg-white\/|text-neutral-50/.test(c)&&txt(e).length<=8&&txt(e);})
    .map(e=>({t:txt(e),b:box(e),cls:String(e.className||'').slice(0,60)}))
    .filter(e=>e.b[0]<280&&e.b[1]>=52)
    .slice(0,10);
  return {
    输入框:right, canvas:canvases, 选中态:sel,
    active:{tag:a?a.tagName:'',type:a?(a.type||''):'',
            aria:a?(a.getAttribute('aria-label')||''):'',
            cls:a?String(a.className||'').slice(0,70):'',
            isCanvas:a?(a.tagName==='CANVAS'):false},
    顶部按钮:Array.from(document.querySelectorAll('button'))
      .filter(e=>{const r=e.getBoundingClientRect();
        return r.y>=8&&r.y<=48&&r.x>820&&r.x<1100;})
      .map(e=>({t:txt(e),b:box(e),
                cls:String(e.className||'').slice(0,60),
                on:String(e.className||'').includes('bg-white')?'白底':''}))
  };}"""


def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(600)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(8_000)


def read(page):
    return page.evaluate(READ)


def shot(page, name):
    p = SHOTS / ("851cam3_%s.png" % name)
    p.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(p), clip=CLIP)
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

            # ★ ★★ 把焦点**明确放到真正的 3D 视口 canvas（index 1）**上
            #   ⟹ ⟹ v2 从没做到这一点 ⟹ ⟹ 这是 v2「WASDQE 全零」的头号嫌疑
            try:
                info = pg.evaluate(
                    "()=>{const c=document.querySelectorAll('canvas')[1];"
                    "if(!c)return null;const r=c.getBoundingClientRect();"
                    "return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];}")
                out["★3D视口canvas盒"] = info
                if info:
                    pg.mouse.click(info[0] + info[2] * 0.5, info[1] + info[3] * 0.5)
                    pg.wait_for_timeout(1_500)
            except Exception:
                out["★点3D视口异常"] = traceback.format_exc()[-500:]
            out["①点3D视口后"] = read(pg)

            # ★ 抖动基线
            v0 = shot(pg, "A-v0")
            pg.wait_for_timeout(2_000)
            v0b = shot(pg, "A-v0b")
            out["②抖动基线"] = diff_px(v0, v0b)

            def condition(tag, setup=None):
                """一个前置条件：⟹ 复位 ⟹ 取基线 ⟹ 先按 T（阳性）⟹ 复位 ⟹ 逐键 WASDQE"""
                if setup:
                    try:
                        setup()
                        pg.wait_for_timeout(2_000)
                    except Exception:
                        out["★%s_setup异常" % tag] = traceback.format_exc()[-400:]
                # ★ 复位到标准视角 ⟹ ⟹ 保证每个条件都从同一个起点出发
                pg.keyboard.press("h")
                pg.wait_for_timeout(1_800)
                base = shot(pg, "%s-base" % tag)
                # ★ 阳性对照：按 T ⟹ 必须有变化（证明这条路径上键盘事件到达了应用层）
                pg.keyboard.press("t")
                pg.wait_for_timeout(1_800)
                vt = shot(pg, "%s-T" % tag)
                out["%s_按T_与基线差" % tag] = diff_px(base, vt)
                # ★ 复位
                pg.keyboard.press("h")
                pg.wait_for_timeout(1_800)
                base2 = shot(pg, "%s-base2" % tag)
                out["%s_按T后按H_与基线差" % tag] = diff_px(base, base2)
                # ★ ★ 逐键 WASDQE
                for k in ["w", "a", "s", "d", "q", "e"]:
                    pg.keyboard.press(k)
                    pg.wait_for_timeout(1_600)
                    vk = shot(pg, "%s-%s" % (tag, k))
                    out["%s_按%s_与基线差" % (tag, k.upper())] = diff_px(base, vk)
                    # ★ 每键后按 H 复位 ⟹ ⟹ 同口径
                    pg.keyboard.press("h")
                    pg.wait_for_timeout(1_600)
                    vr = shot(pg, "%s-%s-reset" % (tag, k))
                    out["%s_按%s后按H_与基线差" % (tag, k.upper())] = diff_px(base, vr)
                out["%s_末态active" % tag] = read(pg)["active"]
                out["%s_末态输入框数" % tag] = len(read(pg)["输入框"])

            condition("A默认")

            def click_top(page, text):
                page.locator("button:has-text('%s')" % text).first.click()

            condition("B机位视角", lambda: click_top(pg, "机位视角"))
            condition("C导演视角", lambda: click_top(pg, "导演视角"))

            def pick_tree(text):
                pg.locator("div.group:has-text('%s')" % text).first.click()

            condition("D选中角色", lambda: pick_tree("角色A"))
            condition("E选中机位", lambda: pick_tree("机位1"))

            out["⑤顶部按钮"] = read(pg)["顶部按钮"]

            # ★ ★★ 阳性对照（面板层）：导演视角下改 FOV（range min0.1 max10）⟹ ⟹ ⌘Z 复原
            try:
                click_top(pg, "导演视角")
                pg.wait_for_timeout(2_000)
                out["⑥导演视角_输入框"] = [
                    {"b": i["b"], "type": i["type"], "value": i["value"],
                     "min": i["min"], "max": i["max"]}
                    for i in read(pg)["输入框"]]
                fov = pg.query_selector('input[type=range][min="0.1"][max="10"]')
                if fov:
                    before = fov.input_value()
                    bb = fov.bounding_box()
                    if bb:
                        pg.mouse.click(bb["x"] + bb["width"] * 0.3,
                                       bb["y"] + bb["height"] / 2)
                        pg.wait_for_timeout(1_500)
                    after = fov.input_value()
                    pg.keyboard.press("Meta+z")
                    pg.wait_for_timeout(2_000)
                    out["⑦FOV"] = {"改前": before, "改后": after,
                                   "按⌘Z后": fov.input_value()}
                else:
                    out["⑦FOV"] = "没找到 range(min0.1,max10)"
            except Exception:
                out["★FOV异常"] = traceback.format_exc()[-600:]

            br.close()
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        RAW.mkdir(parents=True, exist_ok=True)
        (RAW / "source-851-camkeys3.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", RAW / "source-851-camkeys3.json")
        if out.get("异常"):
            print("异常：", out["异常"][-800:])
        print("--- 汇总 ---")
        for k in sorted(out):
            if isinstance(out[k], int):
                print("   %-34s %d" % (k, out[k]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
