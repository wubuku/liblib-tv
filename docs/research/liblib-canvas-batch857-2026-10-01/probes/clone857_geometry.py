#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 857 clone 探针：**「添加角色」浮层 vs 场景树的几何重叠与命中测试**。

## ★ 为什么要有这个探针

源站逐字（`raw/source-857-contract.json` ＋ 源站 chunk）显示：

  `e?null:(0,i.jsxs)("div",{className:"flex w-[232px] min-w-0 flex-col bg-[#171717]",
    children:["scene"===z?n:null,"character"===z?(…添加角色…)]})`

⟹ ⟹ **源站的左侧面板是「模式切换」**：`z` 只能是 `"scene"`（场景树）**或**
`"character"`（添加角色）⟹ ⟹ **两者互斥、永远不同时出现**
⟹ ⟹ 源站在「添加角色」模式下**根本看不到场景树**。

而 clone 把「添加角色」做成 **rail 上的浮层（portal 覆盖层）**
⟹ ⟹ 场景树**仍然在浮层下面可见**
⟹ ⟹ ★ 于是浮层会**拦截落在它矩形上的指针事件**
⟹ ⟹ 这正是 batch 45 门禁迁移后红的直接原因
（点组行的 toggle 时被浮层里的 `[data-director-character-option]` 截走）。

## ★ 本探针读什么（全部是**绝对几何** ＋ **DOM 命中测试**）

1. 浮层 `[data-director-character-flyout]` 的矩形
2. 场景树 `[data-director-tree]` 的矩形
3. 两者**是否相交**、相交面积
4. ★ **命中测试**：`document.elementFromPoint(组行 toggle 的中心)`
   ⟹ ⟹ 回答「用户点得到那个按钮吗」
5. ★ **阳性对照**：命中测试要**打两次** ——
   一次打在**被遮挡**的组行 toggle 上（期望命中浮层里的东西 ⟹ 遮挡），
   一次打在**没被遮挡**的地方（期望命中场景树本身）⟹ ⟹
   ★ 否则「elementFromPoint 返回 null」会被误读成「没有遮挡」。

## 输出
  raw/clone-857-geometry.json
  images/857clone_flyout-overlap.png
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch857-2026-10-01"
RAW = BATCH / "raw"
SHOTS = BATCH / "images"
BASE = "http://localhost:4317"

TREE_CLIP = {"x": 0, "y": 0, "width": 420, "height": 900}

# ★ 一次读齐：矩形 + 命中测试
READ_GEOMETRY = r"""()=>{
  const rect = e => {
    if(!e) return null;
    const r = e.getBoundingClientRect();
    return {x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height),
            right:Math.round(r.right), bottom:Math.round(r.bottom)};
  };
  const flyout = document.querySelector('[data-director-character-flyout]');
  const tree = document.querySelector('[data-director-tree]');
  const toggle = document.querySelector("[data-director-group-action='toggle']");
  const probe = (el) => {
    if(!el) return null;
    const r = el.getBoundingClientRect();
    const cx = r.left + r.width/2, cy = r.top + r.height/2;
    const hit = document.elementFromPoint(cx, cy);
    return {
      目标矩形: rect(el),
      命中点: {x:Math.round(cx), y:Math.round(cy)},
      命中元素: hit ? (hit.tagName + (hit.getAttribute('data-director-character-option')
        ? '[option=' + hit.getAttribute('data-director-character-option') + ']'
        : (hit.getAttribute('data-director-group-action')
        ? '[group-action=' + hit.getAttribute('data-director-group-action') + ']' : ''))) : null,
      命中是否就是目标: hit === el,
      命中是否落在浮层内: !!(hit && flyout && flyout.contains(hit)),
      命中是否落在场景树内: !!(hit && tree && tree.contains(hit)),
    };
  };
  // ★ 阳性对照：找一个**一定不在浮层矩形内**的场景树元素
  let control = null;
  const treeEls = tree ? Array.from(tree.querySelectorAll('[data-director-object-kind]')) : [];
  for(const el of treeEls){
    const r = el.getBoundingClientRect();
    if(r.width<=0||r.height<=0) continue;
    const cx = r.left + r.width/2, cy = r.top + r.height/2;
    if(flyout){
      const fr = flyout.getBoundingClientRect();
      if(cx>=fr.left && cx<=fr.right && cy>=fr.top && cy<=fr.bottom) continue;
    }
    control = el; break;
  }
  return {
    浮层: rect(flyout),
    场景树: rect(tree),
    浮层内选项数: flyout ? flyout.querySelectorAll('[data-director-character-option]').length : 0,
    浮层矩形内是否有场景树元素: (()=>{
      if(!flyout||!tree) return null;
      const fr = flyout.getBoundingClientRect();
      return Array.from(tree.querySelectorAll('[data-director-object-kind],[data-director-group-action]'))
        .filter(el=>{ const r=el.getBoundingClientRect();
          return r.width>0 && r.height>0 && r.left<fr.right && r.right>fr.left && r.top<fr.bottom && r.bottom>fr.top; }).length;
    })(),
    被遮挡的组行toggle: probe(toggle),
    阳性对照_未被遮挡的场景树行: probe(control),
    场景树行数: treeEls.length,
  };
}"""


def open_desk(pg):
    pg.goto(BASE + "/", wait_until="domcontentloaded")
    pg.wait_for_timeout(3000)
    pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
    pg.wait_for_function("() => Boolean(window.__director_store)", timeout=90_000)
    pg.wait_for_timeout(1500)
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
    pg.wait_for_timeout(6500)
    pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")


def main() -> int:
    out = {"批次": "batch 857", "探针": "clone857_geometry",
           "问题": "clone 的「添加角色」浮层是否与场景树重叠并拦截指针"}
    RAW.mkdir(parents=True, exist_ok=True)
    SHOTS.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            open_desk(page)
            out["①打开导演台"] = "OK"

            # 造一个组行（★ 用 clone 的 addCrowdArray ⟹ 它会建组 ⟹ 场景树里就有组行了）
            page.evaluate(
                "() => window.__director_store.getState().addCrowdArray({rows:1, columns:2, spacing:1.2})"
            )
            page.wait_for_timeout(800)

            # 打开 rail 的「添加角色」浮层
            page.locator("[data-director-rail-entry='add-character']").click(timeout=15000)
            page.wait_for_timeout(500)
            flyout = page.locator("[data-director-character-flyout]")
            out["②浮层可见"] = flyout.is_visible()

            out["③几何与命中"] = page.evaluate(READ_GEOMETRY)
            shot = SHOTS / "857clone_flyout-overlap.png"
            page.screenshot(path=str(shot), clip=TREE_CLIP)
            out["③截图"] = shot.name

            # ★ 关闭浮层的可用手段（逐个试，记下哪个真的关掉了）
            closers = []
            for entry in ["scene", "help"]:
                try:
                    page.locator("[data-director-rail-entry='%s']" % entry).click(timeout=8000)
                    page.wait_for_timeout(400)
                    still = page.locator("[data-director-character-flyout]").count()
                    closers.append({"入口": entry, "点完浮层元素数": still})
                    if still == 0:
                        break
                except Exception as exc:
                    closers.append({"入口": entry, "错误": str(exc)[:160]})
            out["④关闭浮层的手段"] = closers
        except Exception:
            out["★异常"] = traceback.format_exc()[-2500:]
        finally:
            browser.close()
    p = RAW / "clone-857-geometry.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if "★异常" not in out else 1


if __name__ == "__main__":
    sys.exit(main())
