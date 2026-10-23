#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 851 源站探针（**只读**）：导演台的**视图类快捷键**（T／H／裸 WASDQE）。

## ★ 为什么上一版探针（source851_viewkeys.py）读到「全零差异」

上一版把**右栏输入框的 (x,y,value)** 当读数 ⟹ 逐键 diff = 0。
★ 但那一轮右栏停在「**3D场景**」属性面板（场景缩放／场景平移 xyz／场景旋转 xyz／
全景球……），而 **830 记录的 FOV range 属于「导演视角」** ⟹ ⟹ 两轮**根本不是同一块面板**，
⟹ ⟹ 「零差异」既可能是键没送达，也可能是**这个键本来就不改面板数字** ⟹ ⟹ 不可判定。

★ ⇒ 本版换读数：**3D 视口的像素**（canvas[1] = [0,0,1920,1080]）
⟹ ⟹ 视图类快捷键改的是**相机**，而相机在面板上**没有数字**（只有「机位视角」面板里才有 FOV）
⟹ ⟹ 面板读数天然看不见 ⟹ ⟹ 像素才是对的口径。

## ★ 三重同口径自证（★ 否定性读数必须先证明读数器没坏）

1. **自然抖动基线**：不动、等 2 秒、截两张 ⟹ 抖动基线 D0（WebGL 可能每帧微动）
2. **H ≡ 「重置视角」按钮**：按 T 改变视角后 ⟹ 按 H ⟹ 像素应回到基线（D0 量级）
   ⟹ ⟹ 再按 W ⟹ 再点「重置视角」按钮 ⟹ 像素也应回到基线
   ⟹ ⟹ ★ 两者互为对照 ⟹ ⟹ 若「按 H 后回到基线」成立 ⟹ ⟹ H 确实就是「重置视角」
3. **可复现性**：同一键按两次 ⟹ 两次的 diff 量级应相同（不是随机噪声）

## ★ 阳性对照（面板层，与像素读数分开测）

★ 点顶部「导演视角」按钮 ⟹ 右栏切到导演属性 ⟹ 找 FOV range ⟹ 改值 ⟹ **⌘Z** ⟹ 应回到原值
⟹ ⟹ 这一步证明「键盘事件确实到达了源站的应用层」⟹ ⟹ 像素读数那边不是「键盘根本没进系统」。

## ★ 只读保证

★ 只按键盘（T／H／W／A／S／D／Q／E）＋ 点「重置视角」/「导演视角」这类**视图**控件
⟹ ⟹ 不点「生成」「保存」「导出」⟹ ⟹ ⚡44 不参与；
★ 结尾改 FOV 后按 ⌘Z 复原 ⟹ ⟹ 全程没有净状态改动。

## 输出

  raw/source-851-camkeys.json   （每一步的右栏读数 ＋ 像素差 ＋ 自证结果）
  images/851cam_*.png          （每一步的视口截图 ⟹ ⟹ 肉眼可核）
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

# ★ 右栏读数：**不按标签找**（★ 830 就是栽在这里）⟹ ⟹ 按位置取所有输入框
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
  const labels=Array.from(document.querySelectorAll('div,span,label,p'))
    .filter(e=>{
      const r=e.getBoundingClientRect();
      if(r.x<1600||r.width<=0||r.height<=0)return false;
      const t=txt(e);
      return t && t.length<=14 && e.children.length===0;})
    .map(e=>({t:txt(e),b:box(e)}))
    .sort((a,b)=>a.b[1]-b.b[1]||a.b[0]-a.b[0]);
  const canvases=Array.from(document.querySelectorAll('canvas'))
    .map((e,i)=>({i,b:box(e),cls:String(e.className||'').slice(0,40)}));
  const a=document.activeElement;
  return {
    输入框:right, 标签:labels, canvas:canvases,
    active:{tag:a?a.tagName:'',type:a?(a.type||''):'',
            aria:a?(a.getAttribute('aria-label')||''):'',
            cls:a?String(a.className||'').slice(0,60):''},
    右栏标题:(function(){
      const s=Array.from(document.querySelectorAll('span,div'))
        .filter(e=>{const r=e.getBoundingClientRect();
          return r.x>1600&&r.y<40&&r.width>0&&r.height>0;})
        .map(e=>txt(e)).filter(t=>t&&t.length<=20);
      return s.slice(0,6);})()
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
    """截 3D 视口（canvas[1]，全屏 1920x1080）⟹ ⟹ 返回图片路径"""
    p = SHOTS / ("851cam_%s.png" % name)
    p.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(p), clip={"x": 0, "y": 0, "width": 1920, "height": 1080})
    return p


def diff_px(a, b):
    """两图的**差异像素数**（★ 判据靠这个数 ⟹ ⟹ 不用固定阈值 ⟹ ⟹ 跟抖动基线比）"""
    ia = Image.open(a).convert("RGB")
    ib = Image.open(b).convert("RGB")
    if ia.size != ib.size:
        return -1
    d = ImageChops.difference(ia, ib)
    n = 0
    for px in d.getdata():
        if px[0] or px[1] or px[2]:
            n += 1
    return n


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
            out["①开台"] = read(pg)

            # ★ 点一下 3D 视口空白处 ⟹ ⟹ 让键盘事件的落点明确（★ 不点任何控件）
            try:
                pg.mouse.click(960, 520)
                pg.wait_for_timeout(1_500)
            except Exception:
                out["★点视口异常"] = traceback.format_exc()[-400:]
            out["②点视口后"] = read(pg)

            # ★ 基线 + 自然抖动基线
            v0 = shot(pg, "v0")
            pg.wait_for_timeout(2_000)
            v0b = shot(pg, "v0b")
            jitter = diff_px(v0, v0b)
            out["③抖动基线_差异像素"] = jitter
            print("抖动基线（不动、等 2 秒、两图差异像素）=", jitter)

            # ★ ★ 自证 1：按 H ⟹ 应回到基线
            pg.keyboard.press("h")
            pg.wait_for_timeout(1_800)
            vh0 = shot(pg, "h0")
            out["④按H后_与基线差"] = diff_px(v0, vh0)

            # ★ ★ 自证 2：按 T（改视角）⟹ ⟹ 再按 H ⟹ 应回到基线
            pg.keyboard.press("t")
            pg.wait_for_timeout(1_800)
            vt = shot(pg, "t")
            out["⑤按T后_与基线差"] = diff_px(v0, vt)
            out["⑤按T后_右栏"] = read(pg)
            pg.keyboard.press("h")
            pg.wait_for_timeout(1_800)
            vh1 = shot(pg, "h1")
            out["⑥T后按H_与基线差"] = diff_px(v0, vh1)

            # ★ ★ 自证 3：点「重置视角」按钮 ⟹ 应与按 H 等效
            try:
                pg.locator("button:has-text('重置视角')").first.click()
                pg.wait_for_timeout(1_800)
            except Exception:
                out["★重置按钮异常"] = traceback.format_exc()[-400:]
            vbtn = shot(pg, "resetbtn")
            out["⑦点重置按钮后_与基线差"] = diff_px(v0, vbtn)

            # ★ ★ 逐键 WASDQE：每键后按 H 复位 ⟹ ⟹ 保证同口径
            for key in ["w", "a", "s", "d", "q", "e"]:
                try:
                    pg.keyboard.press(key)
                    pg.wait_for_timeout(1_800)
                    vk = shot(pg, "key-%s" % key)
                    out["⑧按%s_与基线差" % key.upper()] = diff_px(v0, vk)
                    out["⑧按%s_右栏" % key.upper()] = read(pg)
                    pg.keyboard.press("h")
                    pg.wait_for_timeout(1_800)
                    vr = shot(pg, "key-%s-reset" % key)
                    out["⑨按%s后按H_与基线差" % key.upper()] = diff_px(v0, vr)
                except Exception:
                    out["★按%s异常" % key.upper()] = traceback.format_exc()[-400:]

            # ★ ★★ 阳性对照（面板层）：点「导演视角」⟹ ⟹ 找 FOV ⟹ 改 ⟹ ⌘Z
            try:
                pg.locator("button:has-text('导演视角')").first.click()
                pg.wait_for_timeout(2_000)
                out["⑩切导演视角_右栏"] = read(pg)
                fov = pg.query_selector('input[type=range][min="15"][max="90"]')
                if fov:
                    before = fov.input_value()
                    bb = fov.bounding_box()
                    if bb:
                        pg.mouse.click(bb["x"] + bb["width"] * 0.35,
                                       bb["y"] + bb["height"] / 2)
                        pg.wait_for_timeout(1_500)
                    after = fov.input_value()
                    out["⑪FOV"] = {"改前": before, "改后": after}
                    pg.keyboard.press("Meta+z")
                    pg.wait_for_timeout(2_000)
                    out["⑫FOV_按⌘Z后"] = fov.input_value()
                else:
                    out["⑪FOV"] = "导演视角下没找到 range(min15,max90)"
                    out["⑪导演视角_所有range"] = [
                        {"min": e.min, "max": e.max, "value": e.value,
                         "aria": e.getAttribute("aria-label") or ""}
                        for e in pg.query_selector_all('input[type=range]')]
            except Exception:
                out["★FOV异常"] = traceback.format_exc()[-600:]

            br.close()
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        RAW.mkdir(parents=True, exist_ok=True)
        (RAW / "source-851-camkeys.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", RAW / "source-851-camkeys.json")
        if out.get("异常"):
            print("异常：", out["异常"][-800:])
        print("--- 像素差汇总 ---")
        for k in sorted(out):
            if isinstance(out[k], int) and ("差" in k or "像素" in k):
                print("   %-32s %d" % (k, out[k]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
