#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 845 源站**视觉**探针（**只读**）：截「身材塑形」段右栏的滑杆区域。

## 为什么需要这一趟

`source845_body.py` 量到的是**结构**：每条滑杆是
「LABEL(240×55) → 标签行(240×22) ＋ 轨道容器(240×25) → range input(240×12) ＋ 一枚 2×2 的 `studioRangeThumbDot`」。

但**外观**（拇指到底长什么样、轨道是实心还是分段、名字是纯白还是灰白）
**结构量不出来** ⟹ ⟹ 必须**截屏看像素**。

★ 源站的 input 计算样式是 `appearance: none` ⟹ ⟹ 原生滑块**不画**
  ⟹ ⟹ 那枚 2×2 的 span **就是**拇指 ⟹ ⟹ clone 现在画的 12px 圆头是**偏差**。
  （本趟用像素**证实**这件事，不靠推理。）

★ **只读**：只点左列的**分段** ⟹ ⟹ 不消耗积分 ⟹ ⟹ 点击前后核对那颗积分。

★ 输出：`/tmp/liblib_source_845_visual.png`（截图片段）
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

URL = ("https://www.liblib.tv/canvas"
       "?spaceId=7709759&projectId=a860e1da8e9e4504bececda022386429")
COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT_PNG = pathlib.Path("/tmp/liblib_source_845_visual.png")
OUT_JSON = pathlib.Path("/tmp/liblib_source_845_visual.json")

SEGMENT = "身材塑形"

# ★ 截图片段（**绝对**坐标 ⟹ 覆盖第 1、2 条滑杆的标签行 ＋ 轨道 ＋ 2×2 拇指点）
CLIP = {"x": 1285, "y": 235, "width": 260, "height": 175}


def read_credit(page):
    """★ 只读**那一颗**积分（x 540..575、y 855..885）。"""
    return page.evaluate("""()=>{
      const hits=[];
      for(const e of document.querySelectorAll('span,div,b')){
        const t=(e.textContent||'').trim();
        if(!/^\\d+$/.test(t)||e.children.length!==0)continue;
        const r=e.getBoundingClientRect();
        if(r.width<=0||r.height<=0)continue;
        const x=Math.round(r.x), y=Math.round(r.y);
        if(x>=540&&x<=575&&y>=855&&y<=885)hits.push({t,x,y});}
      return hits;}""")


def main():
    log = {}
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
            pg.set_default_timeout(25_000)
            pg.goto(URL, wait_until="domcontentloaded", timeout=90_000)
            pg.wait_for_timeout(12_000)
            el = pg.query_selector("text=下次再说")
            if el:
                el.click()
                pg.wait_for_timeout(900)
            el = pg.query_selector('[data-sidebar-btn="character-library"]')
            if el:
                bb = el.bounding_box()
                if bb:
                    pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
            pg.wait_for_timeout(5000)
            tab = pg.query_selector("button:text-is('官方角色库')")
            if tab:
                bb = tab.bounding_box()
                if bb:
                    pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
                pg.wait_for_timeout(4000)

            ok_edit = False
            for e in pg.query_selector_all("span,div,button,a,p"):
                if (e.text_content() or "").strip() != "编辑角色":
                    continue
                bb = e.bounding_box()
                if not bb:
                    continue
                pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
                ok_edit = True
                break
            log["★是否点到编辑角色"] = ok_edit
            pg.wait_for_timeout(5000)

            before = read_credit(pg)
            ok_seg = pg.evaluate("""(label)=>{
              const bs=[...document.querySelectorAll('button')].filter(e=>{
                const r=e.getBoundingClientRect();
                return r.x<700&&r.width>100;});
              const b=bs.find(e=>(e.textContent||'').trim().startsWith(label));
              if(!b)return false; b.click(); return true;}""", SEGMENT)
            pg.wait_for_timeout(3000)
            after = read_credit(pg)
            log["★分段_是否点到"] = ok_seg
            log["★分段_积分是否变化"] = (before != after)
            if before != after:
                log["★★ 积分变了 ⟹ 立刻停"] = True
                raise SystemExit("积分变了")

            # ★ 自证：读到的必须是**目标段**（第一条滑杆是「丰胸」）
            first = pg.evaluate("""()=>{
              const a=[...document.querySelectorAll('aside')].find(x=>{
                const r=x.getBoundingClientRect();
                return r.x>=1273&&Math.round(r.width)===288;});
              if(!a)return null;
              const r=a.querySelector('input[type=range]');
              return r?r.getAttribute('aria-label'):null;}""")
            log["★读数_第一条滑杆"] = first
            log["★读数_是目标段"] = (first == "丰胸")
            if first != "丰胸":
                log["★★ 读到的**不是**目标段 ⟹ 这份读数不可信 ⟹ 立刻停"] = True
                raise SystemExit("读到的不是目标段")

            # ★ 截图（**不滚动的视口坐标** ⟹ 直接 clip）
            pg.screenshot(path=str(OUT_PNG), clip=CLIP)
            log["★截图片段"] = CLIP
            log["★截图文件"] = str(OUT_PNG)

            # ★ 再量一次「拇指点」与「轨道容器」的盒（给像素对照用）
            geo = pg.evaluate("""()=>{
              const a=[...document.querySelectorAll('aside')].find(x=>{
                const r=x.getBoundingClientRect();
                return r.x>=1273&&Math.round(r.width)===288;});
              const r=a.querySelector('input[type=range]');
              const wrap=r.parentElement, dot=wrap.querySelector('span');
              const bb=(e)=>{const q=e.getBoundingClientRect();
                return {x:Math.round(q.x),y:Math.round(q.y),
                        w:Math.round(q.width),h:Math.round(q.height)};};
              return {轨道容器:bb(wrap),输入:bb(r),拇指点:bb(dot),
                      轨道容器类名:wrap.getAttribute('class')||'',
                      拇指点类名:dot.getAttribute('class')||'',
                      名字:(()=>{const l=wrap.parentElement.firstElementChild
                        .firstElementChild.querySelector('span');
                        return {文字:(l.textContent||'').trim(),盒:bb(l)};})()};}""")
            log["★几何"] = geo
            log["★读完_积分是否变化"] = (read_credit(pg) != after)
    except SystemExit:
        pass
    except Exception:
        log["异常"] = traceback.format_exc()
    finally:
        OUT_JSON.write_text(json.dumps(log, ensure_ascii=False, indent=1),
                            encoding="utf-8")
        print("已落盘：", OUT_JSON)
        for k, v in log.items():
            if k.startswith("★"):
                print("  %-22s %s" % (k, json.dumps(v, ensure_ascii=False)[:200]))
        if log.get("异常"):
            print("异常：", log["异常"])


if __name__ == "__main__":
    sys.exit(main())
