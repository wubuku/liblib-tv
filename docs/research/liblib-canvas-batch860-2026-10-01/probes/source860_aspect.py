#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 860 源站探针（**只读**）：量两件具体的事。

## ★ 靶子（batch 859 登记的 D11）

batch 859 读到源站逐字（chunk `/tmp/liblib_srcjs2/0fmehki05gkzw.js.js`）：

```js
o$ = useCallback(e => {
  tn(e);                                            // 写本地 ref tr
  let t = e1 || rL.cameras[0]?.id;                  // 当前机位 id
  t && n4(t, "aspect_ratio", (0,nZ.R)(e), "right_panel");  // ★ 发事件
}, [e1, rL.cameras, n4])
```

⟹ ⟹ 源站点「21:9」会**以 `"aspect_ratio"` 事件**把**数值比例**写给当前机位。
⟹ ⟹ 那么：**画布（3D 视口）的宽高比到底变没变？** ⟹ ⟹ 必须实测，不能推。

★ 而 clone 侧的 `aspectRatio` 是**截图/导出**用的三值
（`"16:9" | "9:16" | "1:1"`，被 15 个文件消费）⟹ ⟹ **与画布宽高比不是一回事**。

## ★ 本探针要读到的（不能猜）

① **画布视口**（3D 视口那个元素）的矩形 ⟹ ⟹ 算宽高比；
② 点「21:9」**前**的画布矩形 ＋ 视口里机位/地面框的矩形；
③ 点「21:9」**后**的同样读数 ⟹ ⟹ ★ **逐项比**；
④ ★ 选中态是否真的落在「21:9」那格（描边 alpha）；
⑤ ★ 「本地上传」那枚行点下去会触发什么 ⟹ ⟹ **只读**地看
   `input[type=file]` 是不是被 `click()`（源站逐字 `I?.(), et.current?.click()`）；
⑥ ★ 「AI生成」那枚的 `disabled` 状态（**不点它**）。

## ★ 副作用声明

- 点「21:9」⟹ ⟹ 只改机位的 `aspect_ratio` 参数 ⟹ ⟹ **不付费、不生成、不上传**；
  ⚠ 但它会**改源站工程里的机位参数** ⟹ ⟹ 探针结束时**复原**（点回「自适应」）。
- ★ **绝不点**「AI生成」（会触发付费生图）。
- ★ 「本地上传」**不点**（会弹系统文件选择框）⟹ ⟹ 只用**静态读数 + 源站逐字**判定。

## 输出
  raw/source-860-aspect.json
  images/860src_aspect_before.png ／ 860src_aspect_after.png
"""
from __future__ import annotations

import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch860-2026-10-01"
RAW = BATCH / "raw"
SHOTS = BATCH / "images"

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 画布视口：3D 视口那个大容器。⟹ ⟹ 读它的矩形 ⟹ ⟹ 算宽高比。
# ★ 判据：**排除**左侧 232 面板（x<300）与顶部/底部工具条（h<200）。
READ_VIEWPORT = r"""()=>{
  const rect=(e)=>{ if(!e) return null; const r=e.getBoundingClientRect();
    return {x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width),
            h:Math.round(r.height), right:Math.round(r.right),
            bottom:Math.round(r.bottom),
            ratio: r.height>0 ? +(r.width/r.height).toFixed(4) : null}; };
  const cands=[...document.querySelectorAll('div,canvas')].map(e=>{
    const r=e.getBoundingClientRect();
    return {e, r};
  }).filter(({r})=> r.width>400 && r.height>200 && r.x>280);
  // ★ 取**面积最大**的那个当视口
  cands.sort((a,b)=> (b.r.width*b.r.height)-(a.r.width*a.r.height));
  const top=cands[0];
  const vp=top?top.e:null;
  const canvas=top?top.e.querySelector('canvas'):null;
  const cr=canvas?canvas.getBoundingClientRect():null;
  return {
    视口: vp?rect(vp):null,
    视口类名: vp?(vp.className||'').toString().slice(0,200):null,
    canvas: cr?rect(canvas):null,
    canvas类名: canvas?(canvas.className||'').toString().slice(0,120):null,
    // ★ 机位相关的 DOM（源站逐字：aspect_ratio 事件发给机位）
    机位相关: [...document.querySelectorAll('[class*="aspect"],[class*="ratio"]')]
      .slice(0,8).map(e=>({tag:e.tagName,
        cls:(e.className||'').toString().slice(0,100),
        text:(e.textContent||'').replace(/\s+/g,' ').trim().slice(0,30)})),
  };
}"""

# ★ 画幅比例面板：七格的矩形 ＋ 文本 ＋ 描边 alpha ＋ aria-pressed
READ_ASPECT = r"""()=>{
  const rect=(e)=>{ if(!e) return null; const r=e.getBoundingClientRect();
    return {x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width),
            h:Math.round(r.height)}; };
  // ★ 找到含「自适应」且是 104 宽的那排按钮
  const all=[...document.querySelectorAll('button')];
  const grid=all.filter(b=>{
    const t=(b.textContent||'').replace(/\s+/g,' ').trim();
    return ['自适应','21:9','16:9','4:3','1:1','3:4','9:16'].includes(t);
  });
  const cells=grid.map(b=>{
    const cs=getComputedStyle(b);
    return {text:(b.textContent||'').replace(/\s+/g,' ').trim(),
            rect:rect(b),
            borderColor:cs.borderColor, borderWidth:cs.borderWidth,
            disabled:b.disabled,
            ariaPressed:b.getAttribute('aria-pressed'),
            glyph:(()=>{const g=b.querySelector('svg,span[class*="border"]');
              return g?rect(g):null;})()};
  });
  // ★ 「本地上传」等三枚行：读它们的 disabled 与附近有没有 file input
  const rows=all.filter(b=>{
    const t=(b.textContent||'').replace(/\s+/g,' ').trim();
    return ['本地上传','历史记录','AI生成'].includes(t);
  }).map(b=>({text:(b.textContent||'').replace(/\s+/g,' ').trim(),
             rect:rect(b), disabled:b.disabled,
             hasSvg:!!b.querySelector('svg')}));
  const fileInputs=[...document.querySelectorAll('input[type=file]')].map(e=>{
    const r=e.getBoundingClientRect();
    return {cls:(e.className||'').toString().slice(0,80),
            accept:e.getAttribute('accept'),
            w:Math.round(r.width), h:Math.round(r.height),
            x:Math.round(r.x), y:Math.round(r.y),
            visible:r.width>0&&r.height>0};
  });
  return {cells:cells, rows:rows, fileInputs:fileInputs,
          fileInputCount:fileInputs.length};
}"""


def open_desk(page) -> None:
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(600)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')"
    ).first.click()
    page.wait_for_timeout(8_000)


def main() -> int:
    out: dict = {}
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
            pg.set_default_timeout(20_000)
            pg.goto(URL, wait_until="domcontentloaded", timeout=90_000)
            pg.wait_for_timeout(12_000)
            el = pg.query_selector("text=下次再说")
            if el:
                el.click()
                pg.wait_for_timeout(900)
            open_desk(pg)
            out["①导演台已打开"] = True

            if pg.query_selector("[data-director-practice-escape]"):
                out["②有练习浮层"] = True
                pg.keyboard.press("Escape")
                pg.wait_for_timeout(900)

            # ── 切到「选择画幅比例」──
            # ★ 按**文案**找那枚 rail 按钮（不按位置硬猜）
            rail = pg.evaluate(r"""()=>{
              const out=[];
              document.querySelectorAll('button').forEach(b=>{
                const r=b.getBoundingClientRect();
                if(r.width<=0||r.height<=0) return;
                if(r.x>70) return;
                if(r.y<40||r.y>1000) return;
                out.push({x:Math.round(r.x),y:Math.round(r.y),
                  w:Math.round(r.width),h:Math.round(r.height),
                  aria:b.getAttribute('aria-label')||'',
                  title:b.getAttribute('title')||'',
                  text:(b.textContent||'').replace(/\s+/g,' ').trim().slice(0,24)});
              });
              out.sort((a,b)=>a.y-b.y); return out;}""")
            out["③rail按钮"] = rail

            asp_btn = None
            for r in rail:
                blob = f"{r.get('aria','')} {r.get('title','')} {r.get('text','')}"
                if "画幅" in blob or "比例" in blob:
                    asp_btn = r
                    break
            out["③画幅比例按钮"] = asp_btn
            if not asp_btn:
                raise SystemExit("没找到画幅比例那枚 rail 按钮")

            pg.mouse.click(asp_btn["x"] + asp_btn["w"] / 2,
                           asp_btn["y"] + asp_btn["h"] / 2)
            pg.wait_for_timeout(1_500)

            # ── ③ 点「21:9」之前 ──
            out["④点21比9之前"] = {
                "视口": pg.evaluate(READ_VIEWPORT),
                "面板": pg.evaluate(READ_ASPECT),
            }
            pg.screenshot(path=str(SHOTS / "860src_aspect_before.png"))

            # ── 点「21:9」──
            # ★ 找「21:9」那枚按钮并点它
            cell = pg.locator("button", has_text="21:9").first
            cell.scroll_into_view_if_needed(timeout=8_000)
            pg.wait_for_timeout(300)
            cell.click(timeout=15_000)
            pg.wait_for_timeout(2_500)

            out["⑤点21比9之后"] = {
                "视口": pg.evaluate(READ_VIEWPORT),
                "面板": pg.evaluate(READ_ASPECT),
            }
            pg.screenshot(path=str(SHOTS / "860src_aspect_after.png"))

            # ── ★ 复原：点回「自适应」──
            auto = pg.locator("button", has_text="自适应").first
            try:
                auto.click(timeout=15_000)
                pg.wait_for_timeout(2_000)
                out["⑥复原后"] = {
                    "视口": pg.evaluate(READ_VIEWPORT),
                    "面板": pg.evaluate(READ_ASPECT),
                }
            except Exception as ex:  # noqa: BLE001
                out["⑥复原后"] = {"★失败": str(ex)[:300]}

            pg.close()
            br.close()
    except Exception:  # noqa: BLE001
        out["★异常"] = traceback.format_exc()[-2500:]
    RAW.mkdir(parents=True, exist_ok=True)
    SHOTS.mkdir(parents=True, exist_ok=True)
    (RAW / "source-860-aspect.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2)[:12000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
