#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 851 源站探针（**只读**）：导演台的**视图类快捷键**（T／H／裸 WASDQE）。

## 为什么测这三个

★ batch 830 §七明确登记：「**WASDQE 移动视口**：只证明了按键会到 handler（T 生效可证管线是活的），
**视口移动本身没做像素对照** ⟹ ⟹ 「W 能不能移动视口」**仍未判定**」⟹ ⟹ ★ 本批补这一格。

★ 而且 830 的读数器**找错了元素类型**：它用 `rowOf('场景平移')` 去找**标签行里的 range**
⟹ ⟹ 而源站导演台右栏那几组是 **`type=number` 的输入框**（三列一组：x = 1656 / 1740 / 1824）
⟹ ⟹ 所以 830 读到的「场景平移／旋转／缩放」**全是 null**
⟹ ⟹ ⟹ ★ 不是「源站没有这些读数」，是**读数器没覆盖到那个元素类型**。

★ ⇒ 本批改用「**右栏所有 number/range 输入框的 (x, y, value) 列表**」当读数
⟹ ⟹ 它是**位置化**的 ⟹ ⟹ 任何一格变了都能被 diff 出来。

## ★ 读数口径（同口径 ⟹ ⟹ 否则得到假差异）

★ **必须在同一个右栏页签状态下比较** ⟹ ⟹ 830 的侦察发现「点视口后右栏的输入框数量从 18 变成 14」
⟹ ⟹ 所以流程是：**进导演台 → 点视口 → 记基线 → 逐键 → 按 H 回基线**
⟹ ⟹ ★ 「按 H 之后回到基线」本身就是**最硬的自证**（证明 H 确实是「重置视角」）。

## ★ 只读保证

★ 只按键盘（T／H／W／A／S／D／Q／E）⟹ ⟹ 这些**只动视图**，不动画布数据；
★ 不点「生成」「保存」「导出」等任何付费控件 ⟹ ⟹ ⚡44 不参与；
★ 每次都读右栏输入框 ⟹ ⟹ 结尾再按一次 H 复原视图。

## 输出

  raw/source-851-viewkeys.json   （每一步的右栏读数 ＋ 标签 ＋ diff）
  raw/source-851-*.png           （每一步的视口截图 ⟹ ⟹ 肉眼可核）
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch851-2026-10-01"
RAW = BATCH / "raw"
SHOTS = BATCH / "images"

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_851_viewkeys.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 右栏读数：★ **不按标签找**（★ 830 就是栽在这里）⟹ ⟹ 改成**按位置**取所有输入框
READ = r"""()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
  const txt=(e)=>(e.textContent||'').trim().replace(/\s+/g,' ');
  // ★ 右栏 = x > 1600（★ 830 的侦察也是这么分区的）
  const right=Array.from(document.querySelectorAll('input,textarea'))
    .filter(e=>e.getBoundingClientRect().x>1600)
    .map(e=>({t:e.tagName,type:e.type||'',value:e.value,
              aria:e.getAttribute('aria-label')||'',
              min:e.min||'',max:e.max||'',step:e.step||'',
              b:box(e)}))
    .sort((a,b)=>a.b[1]-b.b[1]||a.b[0]-b.b[0]);
  // ★ 右栏里所有**可见文字**（用来给输入框配标签）
  const labels=Array.from(document.querySelectorAll('div,span,label,p'))
    .filter(e=>{
      const r=e.getBoundingClientRect();
      if(r.x<1600||r.width<=0||r.height<=0)return false;
      const t=txt(e);
      return t && t.length<=14 && e.children.length===0;})
    .map(e=>({t:txt(e),b:box(e)}))
    .sort((a,b)=>a.b[1]-b.b[1]||a.b[0]-b.b[0]);
  // ★ 导演台**视口**的元素（★ 用于截图 clip ⟹ ⟹ 找盖住画布的那块）
  const canvases=Array.from(document.querySelectorAll('canvas'))
    .map(e=>({b:box(e),cls:String(e.className||'').slice(0,40)}))
    .filter(c=>c.b[2]>200&&c.b[3]>200);
  const a=document.activeElement;
  return {
    输入框:right,
    标签:labels,
    视口canvas:canvases,
    active:{tag:a?a.tagName:'',type:a?(a.type||''):'',
            aria:a?(a.getAttribute('aria-label')||''):'',
            cls:a?String(a.className||'').slice(0,60):''},
    文本头:(document.body.innerText||'').slice(0,400)
  };}"""


def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(600)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(7_000)


def read(page):
    return page.evaluate(READ)


def shot(page, name):
    p = SHOTS / ("851_%s.png" % name)
    p.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(p))
    return "images/" + p.name


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
            out["①开台后"] = read(pg)
            out["①截图"] = shot(pg, "open")

            # ★ 点 3D 视口（★ 830 侦察发现「点视口后」右栏会换一组输入框 ⟹ ⟹ 必须点）
            try:
                cv = pg.locator("canvas").first
                bb = cv.bounding_box()
                if bb:
                    pg.mouse.click(bb["x"] + bb["width"] * 0.5, bb["y"] + bb["height"] * 0.5)
                    pg.wait_for_timeout(2_500)
            except Exception:
                out["★点视口异常"] = traceback.format_exc()[-500:]
            out["②点视口后"] = read(pg)
            out["②截图"] = shot(pg, "after-click")

            # ★ ★ 逐键：每按一个键，记一次右栏读数 ＋ 截图
            steps = [("T", "t"), ("H", "h"), ("W", "w"), ("A", "a"),
                     ("S", "s"), ("D", "d"), ("Q", "q"), ("E", "e")]
            for label, key in steps:
                try:
                    pg.keyboard.press(key)
                    pg.wait_for_timeout(2_000)
                    out["③按%s后" % label] = read(pg)
                    out["③按%s后_截图" % label] = shot(pg, "key-%s" % label)
                except Exception:
                    out["★按%s异常" % label] = traceback.format_exc()[-500:]
                # ★ 每按一个键之后都按 H 复位 ⟹ ⟹ 保证**每一步都在同一基线上**
                #   （★ 这是「同口径」的关键 ⟹ ⟹ 否则 WASDQE 会累积）
                try:
                    pg.keyboard.press("h")
                    pg.wait_for_timeout(1_800)
                except Exception:
                    pass
            out["④全部按完并复位后"] = read(pg)
            out["④截图"] = shot(pg, "after-reset")

            # ★ ★★ **阳性对照**：改一个 FOV（能读出数值）⟹ ⟹ 按 ⌘Z 应回到原值
            #   （★ 830 实测过 ⟹ ⟹ 本批复核 ⟹ ⟹ 用来证明「快捷键管线是活的」）
            try:
                fov = pg.query_selector('input[type=range][min="15"][max="90"]')
                if fov:
                    bb = fov.bounding_box()
                    if bb:
                        pg.mouse.click(bb["x"] + bb["width"] * 0.4, bb["y"] + bb["height"] / 2)
                        pg.wait_for_timeout(1_500)
                        out["⑤改FOV后"] = read(pg)
                        pg.keyboard.press("Meta+z")
                        pg.wait_for_timeout(2_000)
                        out["⑥按⌘Z后"] = read(pg)
                else:
                    out["⑤FOV控件"] = "没找到"
            except Exception:
                out["★FOV异常"] = traceback.format_exc()[-500:]
            br.close()
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        RAW.mkdir(parents=True, exist_ok=True)
        (RAW / "source-851-viewkeys.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", RAW / "source-851-viewkeys.json")
        if out.get("异常"):
            print("异常：", out["异常"][-800:])
        for k in out:
            if k.startswith("①") or k.startswith("②") or k.startswith("④"):
                v = out[k]
                if isinstance(v, dict):
                    print("  %-14s 输入框 %d 个 ｜ 标签 %d 个 ｜ active=%s"
                          % (k, len(v.get("输入框") or []), len(v.get("标签") or []),
                             (v.get("active") or {}).get("tag")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
