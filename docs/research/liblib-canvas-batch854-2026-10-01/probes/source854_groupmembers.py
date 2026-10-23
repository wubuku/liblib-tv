#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 854 源站探针（**有副作用**·会真的建组／解组，最后复原）：导演台的**组成员语义**。

## ★ 本批要证明的三件事（逐字依据见 raw/source-854-contract.json，17 片段全命中）

1. ★★ **组可以包含不同类别的成员**（不只角色）
   - 源站逐字 `function sg(e){return"character"===e||"prop"===e||"emptyObject"===e||"camera"===e}`
   - 源站逐字 `case"CREATE_CHARACTER_GROUP":{let r=lB(t.members&&t.members.length>0?t.members:lB(e.selectedSceneMembers,e.characters,e.props,e.emptyObjects,e.cameras),...)`
2. ★★ **组成员在树里是缩进子行、且组默认展开**
   - 源站逐字 `expanded:!!F||!j.has(e.id)`（`j` 是**被折叠**的组集合 ⟹ 默认展开）
   - 源站逐字 `(F||!j.has(e.id))&&r.map((e,t)=>(0,i.jsx)(sM,{row:e,indent:!0,...}))`
3. ★★ **树多选是 ⇧／⌘／Ctrl ＋ 点击，且只对可分组类别生效**
   - 源站逐字 `let r=t.shiftKey||t.metaKey||t.ctrlKey;a(e.id,e.category,sg(e.category)?{additive:r,individual:!0}:void 0)`

## ★★ 一个测量同时证明第 1 条与第 3 条

★ 源站这个工程里**只有一个角色**（角色A）＋ **两个机位** ⟹ ⟹
★ 若要建一个**跨类别**的组，只能用「一个机位 ＋ 一个角色」。
★ 而「⌘+点击一个机位」能不能把它加进选择，正是第 3 条。
★ ⟹ ⟹ **若按 ⌘G 之后组里同时出现机位与角色**，
★ ⟹ ⟹ 就**同时**证明了「⌘+点击可加选机位」与「组可含不同类别的成员」。

## ★ 读数

★ 行 ＝ label span 的 class 含 `truncate pl-1` 且 x<300（★ 结构定位）。
★ ★ **不手打中文条目名**：机位行与角色行靠**图标指纹**区分
（机位图标含 `x="1.75"`，角色图标含 `8.3125`）⟹ ⟹ 探针自己认得出哪行是哪类。

## ★ 副作用与复原

★ 建组会**存进用户工程** ⟹ ⟹ 最后必须解组复原；兜底 ⌘Z。

## 输出
  raw/source-854-groupmembers.json
  images/854src_*.png
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch854-2026-10-01"
RAW = BATCH / "raw"
SHOTS = BATCH / "images"

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

TREE_CLIP = {"x": 40, "y": 100, "width": 250, "height": 420}

# ★ 行的类别指纹：★ **不手打中文** ⟹ ⟹ 靠图标 innerHTML 的特征串
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
    // ★ 行的完整 class（用于看选中态）
    const rowCls = row ? (row.className || '') : '';
    // ★★ Batch 854 补充：**同口径**的第二层几何 —— 行的**元素** x（不是标签 span 的 x）
    // ★ ⟹ ⟹ 源站与 clone 可以按**同一种粒度**相减（文本 x vs 元素 x 各比各的）。
    const rr = row ? row.getBoundingClientRect() : null;
    // ★ 行内**第一个子元素**的宽度（用来分辨「组行多一个折叠按钮」这类结构差）
    let firstW = null;
    if(row && row.firstElementChild){
      const fr = row.firstElementChild.getBoundingClientRect();
      firstW = Math.round(fr.width*100)/100;
    }
    out.push({label:t, x:Math.round(r.x), y:Math.round(r.y),
              w:Math.round(r.width), h:Math.round(r.height),
              rowX: rr? Math.round(rr.x*100)/100 : null,
              rowW: rr? Math.round(rr.width*100)/100 : null,
              firstW,
              icon, rowCls: String(rowCls).slice(0, 200)});
  });
  out.sort((a,b)=>a.y-b.y);
  return out;
}"""

# ★ 树里的「节标题」探测：源站是**平铺列表** ⟹ ⟹ 应当**找不到**分节标题
READ_SECTIONS = r"""()=>{
  const heads = [];
  document.querySelectorAll('h1,h2,h3,h4,h5,h6,[role="heading"]').forEach(e=>{
    const r = e.getBoundingClientRect();
    if(r.width<=0||r.height<=0) return;
    if(r.x > 300) return;
    heads.push({tag:e.tagName, text:(e.textContent||'').trim().slice(0,40),
                x:Math.round(r.x), y:Math.round(r.y)});
  });
  return heads;
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


def shot(page, name):
    p = SHOTS / ("854src_%s.png" % name)
    p.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(p), clip=TREE_CLIP)
    return p


def kind_of(row):
    """★ 靠**图标指纹**判类别 ⟹ ⟹ 不手打中文条目名。"""
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
            out["①基线类别"] = [kind_of(r) for r in base]
            out["①基线x"] = [r["x"] for r in base]
            out["①基线节标题"] = pg.evaluate(READ_SECTIONS)
            shot(pg, "baseline")

            cam = next((r for r in base if kind_of(r) == "camera"), None)
            chr_ = next((r for r in base if kind_of(r) == "character"), None)
            out["②挑中的机位行标签"] = cam["label"] if cam else None
            out["②挑中的角色行标签"] = chr_["label"] if chr_ else None

            if cam is None or chr_ is None:
                out["★异常"] = "基线里没有机位或角色行"

            # ── ① 点一个机位 ＋ ⌘+点一个角色 ⟹ ⌘G ⟹ 应当建出一个**跨类别**的组
            try:
                click_row(pg, cam)
                out["③点机位后标签"] = [r["label"] for r in rows(pg)]
                click_row(pg, chr_, modifier="Meta")
                out["④⌘加选角色后标签"] = [r["label"] for r in rows(pg)]
                shot(pg, "two-selected")
                pg.keyboard.press("Meta+g")
                pg.wait_for_timeout(1000)
                after = rows(pg)
                out["⑤⌘G后行"] = after
                out["⑤⌘G后标签"] = [r["label"] for r in after]
                out["⑤⌘G后类别"] = [kind_of(r) for r in after]
                out["⑤⌘G后x"] = [r["x"] for r in after]
                out["⑤行数变化"] = len(after) - len(base)
                shot(pg, "after-group")
            except Exception:
                out["★建组段异常"] = traceback.format_exc()[-600:]

            # ── ② ⌘⇧D 解组 ⟹ 回到基线
            try:
                pg.keyboard.press("Meta+Shift+d")
                pg.wait_for_timeout(1000)
                out["⑥⌘⇧D后标签"] = [r["label"] for r in rows(pg)]
                out["⑥行数变化"] = len(rows(pg)) - len(base)
                out["⑥回到基线"] = [r["label"] for r in rows(pg)] == \
                    [r["label"] for r in base]
                shot(pg, "after-ungroup")
            except Exception:
                out["★解组段异常"] = traceback.format_exc()[-600:]

            # ── ③ 兜底复原
            try:
                fin = [r["label"] for r in rows(pg)]
                out["⑦结束时标签"] = fin
                if len(fin) > len(base):
                    pg.keyboard.press("Meta+z")
                    pg.wait_for_timeout(1000)
                    out["⑦兜底⌘Z后标签"] = [r["label"] for r in rows(pg)]
                else:
                    out["⑦无需兜底"] = True
                shot(pg, "final")
            except Exception:
                out["★兜底段异常"] = traceback.format_exc()[-600:]

            br.close()
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        RAW.mkdir(parents=True, exist_ok=True)
        (RAW / "source-854-groupmembers.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", RAW / "source-854-groupmembers.json")
        if out.get("异常"):
            print("异常：", out["异常"][-800:])
        print("基线标签 :", out.get("①基线标签"))
        print("基线类别 :", out.get("①基线类别"))
        print("基线 x   :", out.get("①基线x"))
        print("基线节标题:", out.get("①基线节标题"))
        print("⌘G 后   :", out.get("⑤⌘G后标签"))
        print("⌘G 后类别:", out.get("⑤⌘G后类别"))
        print("⌘G 后 x :", out.get("⑤⌘G后x"))
        print("行数变化 :", out.get("⑤行数变化"))
        print("⌘⇧D 后 :", out.get("⑥⌘⇧D后标签"), "回到基线", out.get("⑥回到基线"))
        print("结束时   :", out.get("⑦结束时标签"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
