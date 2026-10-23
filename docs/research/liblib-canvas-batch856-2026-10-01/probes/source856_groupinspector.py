#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 856 源站探针（**有副作用**·会真的建组／解组，最后复原）：
导演台**组检查器的变换字段**。

## ★ 本批要取证的事（855 登记的 D1）

★ clone 的组检查器有**三个**变换字段：「位置／旋转／缩放」
  （`DirectorInspector.tsx` 里 `[["position","位置"],["rotation","旋转"],["scale","缩放"]]`）
  ⟹ ⟹ 改旋转／缩放时走 `applyDirectorGroupTransform`
  ⟹ ⟹ 那个函数会按「**旋转增量 ＋ 缩放比**」把成员绕锚点转过去。

★ 源站逐字的两条线索：
  1. `groupTransform` 在源站 chunk 里命中 **0** 次 ⟹ ⟹ 源站的组**没有 transform 字段**；
  2. 源站组轨道的编辑属性：`speedCurveSegments:hi(t.speedCurveSegments,["position"])`
     ⟹ ⟹ 组轨道**只有 `position`** 一个可编辑属性。

★ ⟹ ⟹ 但**组检查器面板**到底显示哪些字段，**光看 chunk 不够**
  ⟹ ⟹ 必须**实测**：建一个组、选中它、把检查器面板的 DOM 结构读下来。

## ★ 读数策略（★ 不手打中文字段名）

★ 源站的检查器右侧面板里，每个可编辑数值字段有 label ＋ 若干输入框。
  ⟹ ⟹ 探针读「**面板里所有可见的输入框**」＋「它们各自的 label 文本」，
  ⟹ ⟹ 再按「**输入框的轴标签**（X/Y/Z）＋ 所属分组」归类。
★ ★ **关键**：靠**结构**（输入框的 type／aria／相邻文本）定位，
  而不是靠手打「位置」「旋转」「缩放」这三个词。

## ★ 副作用与复原

★ 建组会**存进用户工程** ⟹ ⟹ 最后必须解组复原；兜底 ⌘Z。

## 输出
  raw/source-856-groupinspector.json
  images/856src_*.png
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

TREE_CLIP = {"x": 40, "y": 100, "width": 250, "height": 420}
PANEL_CLIP = {"x": 1250, "y": 60, "width": 670, "height": 1000}

CAMERA_ICON = 'x="1.75"'
CHARACTER_ICON = "8.3125"

# ★ 读树行（沿用 854 的同口径：标签 span 的 class 含 `truncate pl-1`）
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

# ★★★ 读**右侧检查器面板**里所有可见的**数值输入框** ＋ 它们的上下文
# ★★★ ★ 不手打中文字段名 ⟹ ⟹ 靠结构：输入框的 type／placeholder／aria-label
# ★★★   ＋ 所在容器里的**非输入框文本**（那就是字段的 label）
READ_PANEL_FIELDS = r"""()=>{
  const out = [];
  // ★ 面板容器：右半屏里带输入框的区块
  document.querySelectorAll('input').forEach(inp=>{
    const r = inp.getBoundingClientRect();
    if(r.width<=0||r.height<=0) return;
    if(r.x < 900) return;                 // ★ 只要右半屏（检查器）
    const type = (inp.getAttribute('type')||'text').toLowerCase();
    if(type!=='number' && type!=='text' && type!=='range') return;
    // ★ 向上找最近的「区块容器」（带 label 的那层）
    let box = inp.parentElement, label = '', depth = 0;
    while(box && depth < 6){
      // ★ 这个容器里的**纯文本**（排除输入框自身与更深层的）就是 label
      const clone = box.cloneNode(true);
      clone.querySelectorAll('input,button,select,textarea').forEach(n=>n.remove());
      const txt = (clone.textContent||'').replace(/\s+/g,' ').trim();
      if(txt && txt.length <= 24){ label = txt; break; }
      box = box.parentElement; depth++;
    }
    // ★ 祖先链上的 aria-label / title / placeholder
    let aria = inp.getAttribute('aria-label')||'';
    let ph = inp.getAttribute('placeholder')||'';
    let anc = inp.parentElement, d2 = 0;
    while(anc && d2 < 5){
      if(!aria && anc.getAttribute('aria-label')) aria = anc.getAttribute('aria-label');
      if(!ph && anc.getAttribute('placeholder')) ph = anc.getAttribute('placeholder');
      anc = anc.parentElement; d2++;
    }
    out.push({
      type, x:Math.round(r.x), y:Math.round(r.y),
      w:Math.round(r.width), h:Math.round(r.height),
      value: inp.value, aria, placeholder: ph, label,
      min: inp.getAttribute('min'), max: inp.getAttribute('max'), step: inp.getAttribute('step'),
    });
  });
  out.sort((a,b)=> (a.y-b.y) || (a.x-b.x));
  return out;
}"""

# ★ 读右侧面板的**所有可见文本块**（用来认出面板有哪些 section 标题）
READ_PANEL_TEXT = r"""()=>{
  const out = [];
  document.querySelectorAll('div,span,label,p,h1,h2,h3,h4').forEach(e=>{
    const r = e.getBoundingClientRect();
    if(r.width<=0||r.height<=0) return;
    if(r.x < 900) return;
    const t = (e.textContent||'').replace(/\s+/g,' ').trim();
    if(!t || t.length > 40) return;
    // ★ 只要**叶子**文本块（没有子元素带文字的）
    let leaf = true;
    e.childNodes.forEach(n=>{
      if(n.nodeType===3 && (n.textContent||'').trim()) leaf = false;
    });
    if(!leaf) return;
    out.push({text:t, x:Math.round(r.x), y:Math.round(r.y),
              tag:e.tagName, cls:String(e.className||'').slice(0,80)});
  });
  out.sort((a,b)=> (a.y-b.y) || (a.x-b.x));
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


def shot(page, name, clip=None):
    p = SHOTS / ("856src_%s.png" % name)
    p.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(p), clip=clip or PANEL_CLIP)
    return p


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
            out["①基线类别"] = [kind_of(r) for r in base]

            cam = next((r for r in base if kind_of(r) == "camera"), None)
            chr_ = next((r for r in base if kind_of(r) == "character"), None)
            if cam is None or chr_ is None:
                out["★异常"] = "基线里没有机位或角色行"

            # ★★★ ① 先读「未选中任何东西」时的面板文本（基线）
            out["②基线面板文本"] = pg.evaluate(READ_PANEL_TEXT)
            out["②基线面板字段"] = pg.evaluate(READ_PANEL_FIELDS)
            shot(pg, "baseline-panel", PANEL_CLIP)

            # ── ② 选中一个角色 ⟹ 读角色检查器的字段（对照组）
            if chr_:
                click_row(pg, chr_)
                out["③选中角色后面板文本"] = pg.evaluate(READ_PANEL_TEXT)
                out["③选中角色后面板字段"] = pg.evaluate(READ_PANEL_FIELDS)
                shot(pg, "character-panel", PANEL_CLIP)

            # ── ③ ⌘+点角色 ⟹ 打组 ⟹ 选中这个组 ⟹ 读**组检查器**的字段 ★ 本批核心
            if cam and chr_:
                click_row(pg, cam)
                click_row(pg, chr_, modifier="Meta")
                pg.keyboard.press("Meta+g")
                pg.wait_for_timeout(1200)
                after = rows(pg)
                out["④⌘G后行"] = after
                out["④⌘G后类别"] = [kind_of(r) for r in after]
                shot(pg, "grouped", TREE_CLIP)

                # ★ 选中组行（第一个非缩进行 = 组标题行）
                grp = None
                for r in after:
                    if kind_of(r) == "other":
                        grp = r
                        break
                if grp:
                    click_row(pg, grp)
                    pg.wait_for_timeout(900)
                    out["⑤组检查器面板文本"] = pg.evaluate(READ_PANEL_TEXT)
                    out["⑤组检查器面板字段"] = pg.evaluate(READ_PANEL_FIELDS)
                    shot(pg, "group-panel", PANEL_CLIP)
                    out["⑤组检查器面板字段数"] = len(out["⑤组检查器面板字段"])

                    # ★★★ ⑥ 字段摘要（label／aria／placeholder／type／value）
                    # ★★★ ★ 只**读**不改 ⟹ ⟹ 探针不引入额外的副作用
                    edits = []
                    for f in out["⑤组检查器面板字段"]:
                        edits.append({"label": f["label"], "aria": f["aria"],
                                      "placeholder": f["placeholder"],
                                      "type": f["type"], "value": f["value"],
                                      "x": f["x"], "y": f["y"]})
                    out["⑥组检查器字段摘要"] = edits

            # ── 复原：解组
            try:
                pg.keyboard.press("Meta+Shift+d")
                pg.wait_for_timeout(1200)
            except Exception:
                pass
            final = rows(pg)
            out["⑦复原后行"] = final
            out["⑦复原后类别"] = [kind_of(r) for r in final]
            out["⑦是否回到基线"] = (
                [r["label"] for r in final] == [r["label"] for r in base]
            )
            shot(pg, "restored", TREE_CLIP)

    except Exception:
        out["★异常"] = traceback.format_exc()[-2500:]
    finally:
        RAW.mkdir(parents=True, exist_ok=True)
        (RAW / "source-856-groupinspector.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", RAW / "source-856-groupinspector.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
