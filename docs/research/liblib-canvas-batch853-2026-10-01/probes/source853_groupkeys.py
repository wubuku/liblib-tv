#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 853 源站探针（**有副作用**·会真的建组／解组，最后复原）：导演台的**打组／解组快捷键**。

## ★ 靶子与逐字依据（机器提取见 `raw/source-853-contract.json`）

```js
hY=new Set(["escape","enter","v","r","f","h","x","t","y","c","d","g","delete","backspace","z"])
&&("g"!==n||e.ctrlKey||e.metaKey)&&("d"!==n||e.shiftKey&&(e.ctrlKey||e.metaKey))
else if("g"===n||"d"===n)if(e.shiftKey){
  let e=nf.current.selectedGroupId;e&&rY(e)}else"g"===n&&rW();
```

⟹ **⌘G 打组／⌘⇧G 与 ⌘⇧D 解组／⌘D 不做／裸 G 不做**。

★ 源站 reducer 的建组规则（同样逐字）：
`r.length<2 ⟹ return e`（**成员不足两个就什么都不做**）；
成员范围 ＝ `selectedSceneMembers` 里的 **character／prop／emptyObject／camera**
（`sg(e)` ＝ `"character"===e||"prop"===e||"emptyObject"===e||"camera"===e`）。

## ★ 读数：**场景树的条目数**

★ 源站的组是**树上的一个条目**（带 lucide `Group` 图标 ＋ 自己的 label），
⟹ ⟹ 「组出现了」＝ **树里多了一行**；「组消失了」＝ **树里少了一行**。
★ 行的定位用**结构**（label span 的 class 含 `truncate pl-1` ＋ x<300），
★ **不手打中文条目名**（机位1／机位2／角色A 都是读出来的）。

## ★ 为什么用「机位1 + 机位2」而不是两个角色

★ 源站这个工程里**只有一个角色**（角色A）⟹ ⟹ 想在源站上触发建组，
★ 就得用**两个机位** ⟹ ⟹ ★★ **顺带证明了一件事**：★ 源站的组**可以装机位**，
★ 而 clone 的 `groupSelectedCharacters` **只收角色** ⟹ ⟹ 这是**功能差异**（不是快捷键差异）。

## ★ 副作用与复原

★ ⌘G 会**真的建组**（会存到用户工程里）⟹ ⟹ 所以最后**必须解组复原**。
★ 兜底：若结束时树上仍有组 ⟹ ⟹ 按 **⌘Z** 撤销建组 ⟹ ⟹ 再验一次。

## 输出

  raw/source-853-groupkeys.json
  images/853src_*.png
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch852-2026-10-01"
BATCH = ROOT / "docs/research/liblib-canvas-batch853-2026-10-01"
RAW = BATCH / "raw"
SHOTS = BATCH / "images"

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

TREE_CLIP = {"x": 40, "y": 100, "width": 250, "height": 420}

# ★ 场景树的行 ⟹ label span 的 class 含 `truncate pl-1`（★ 源站 chunk 里
#   `(0,i.jsx)("span",{className:"z-10 min-w-0 flex-1 truncate pl-1",children:e.label})`
#   ⟹ ★ 组的条目也用同一个 class ⟹ ⟹ 行数变化正好反映「组出现／消失」）。
READ_ROWS = r"""()=>{
  const out = [];
  document.querySelectorAll('span').forEach(e=>{
    const cls = e.className || '';
    if(typeof cls !== 'string' || cls.indexOf('truncate pl-1') < 0) return;
    const r = e.getBoundingClientRect();
    if(r.width<=0||r.height<=0) return;
    if(r.x > 300) return;                    // ★ 只看左侧场景树那一栏
    const t = (e.textContent||'').trim();
    if(!t) return;
    // ★ 行的图标：在同一行里的第一个 span，其 svg 的 innerHTML 当作「类别指纹」
    const row = e.parentElement;
    let icon = '';
    if(row){
      const svg = row.querySelector('span svg') || row.querySelector('svg');
      icon = svg ? svg.innerHTML.slice(0, 120) : '';
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


def shot(page, name):
    p = SHOTS / ("853src_%s.png" % name)
    p.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(p), clip=TREE_CLIP)
    return p


def rows(page):
    return page.evaluate(READ_ROWS)


def labels(page):
    return [r["label"] for r in rows(page)]


def click_row(page, index, modifier=None):
    """★ 点第 index 行（★ 结构定位，不按中文名）"""
    rs = rows(page)
    if index >= len(rs):
        raise SystemExit("★ 没有第 %d 行（共 %d 行）" % (index, len(rs)))
    r = rs[index]
    box = {"x": r["x"], "y": r["y"], "width": r["w"], "height": r["h"]}
    if modifier:
        page.keyboard.down(modifier)
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    if modifier:
        page.keyboard.up(modifier)
    page.wait_for_timeout(500)


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
            base = rows(pg)
            out["①基线行"] = base
            out["①基线标签"] = [r["label"] for r in base]
            shot(pg, "baseline")

            # ── ① 只选 1 个 ⟹ ⌘G 应当**什么都不做**（成员不足 2）
            try:
                click_row(pg, 0)
                out["②选中1个后标签"] = labels(pg)
                pg.keyboard.press("Meta+g")
                pg.wait_for_timeout(700)
                out["②单选按⌘G后标签"] = labels(pg)
                out["②单选按⌘G行数变化"] = len(labels(pg)) - len(base)
                shot(pg, "single-group")
            except Exception:
                out["★单选段异常"] = traceback.format_exc()[-400:]

            # ── ② 加选第 2 个（⌘+点击 ⟹ 源站的 additive 多选）⟹ ⌘G 应当**建组**
            try:
                click_row(pg, 1, modifier="Meta")
                out["③选中2个后标签"] = labels(pg)
                # ★ 记下**点了哪两行**（★ 按下标记，不手打中文）⟹ ⟹ 门禁才能
                #   区分「组内成员被缩进」与「非成员没被缩进」这两种情况。
                out["③选中的两行标签"] = [base[0]["label"], base[1]["label"]]
                out["③选中的两行下标"] = [0, 1]
                shot(pg, "two-selected")
                pg.keyboard.press("Meta+g")
                pg.wait_for_timeout(900)
                after = rows(pg)
                out["③双选按⌘G后行"] = after
                out["③双选按⌘G后标签"] = [r["label"] for r in after]
                out["③行数变化"] = len(after) - len(base)
                shot(pg, "after-group")
            except Exception:
                out["★双选段异常"] = traceback.format_exc()[-400:]

            # ── ③ ⌘D 应当**什么都不做**（源站要求 ⇧ ＋ ⌘）
            try:
                before = labels(pg)
                pg.keyboard.press("Meta+d")
                pg.wait_for_timeout(600)
                out["④按⌘D后标签"] = labels(pg)
                out["④⌘D有变化"] = labels(pg) != before
            except Exception:
                out["★⌘D段异常"] = traceback.format_exc()[-400:]

            # ── ④ ⌘⇧D 应当**解组**（树里少一行）
            try:
                before = labels(pg)
                pg.keyboard.press("Meta+Shift+d")
                pg.wait_for_timeout(900)
                out["⑤按⌘⇧D后标签"] = labels(pg)
                out["⑤行数变化"] = len(labels(pg)) - len(base)
                out["⑤回到基线"] = labels(pg) == [r["label"] for r in base]
                shot(pg, "after-ungroup")
            except Exception:
                out["★⌘⇧D段异常"] = traceback.format_exc()[-400:]

            # ── ⑤ 兜底复原：若树上仍有组 ⟹ ⌘Z 撤销 ⟹ 再验一次
            try:
                fin = labels(pg)
                out["⑥结束时标签"] = fin
                if len(fin) > len(base):
                    pg.keyboard.press("Meta+z")
                    pg.wait_for_timeout(900)
                    out["⑥兜底⌘Z后标签"] = labels(pg)
                    out["⑥兜底后行数"] = len(labels(pg))
                else:
                    out["⑥无需兜底"] = True
                shot(pg, "final")
            except Exception:
                out["★兜底段异常"] = traceback.format_exc()[-400:]

            br.close()
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        RAW.mkdir(parents=True, exist_ok=True)
        (RAW / "source-853-groupkeys.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", RAW / "source-853-groupkeys.json")
        if out.get("异常"):
            print("异常：", out["异常"][-800:])
        print("基线标签 :", out.get("①基线标签"))
        print("单选⌘G后:", out.get("②单选按⌘G后标签"), "行数变化", out.get("②单选按⌘G行数变化"))
        print("双选⌘G后:", out.get("③双选按⌘G后标签"), "行数变化", out.get("③行数变化"))
        print("⌘D 后   :", out.get("④按⌘D后标签"), "有变化", out.get("④⌘D有变化"))
        print("⌘⇧D 后  :", out.get("⑤按⌘⇧D后标签"), "行数变化", out.get("⑤行数变化"),
              "回到基线", out.get("⑤回到基线"))
        print("结束时   :", out.get("⑥结束时标签"), "兜底", out.get("⑥兜底⌘Z后标签"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
