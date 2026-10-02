#!/usr/bin/env python3
"""batch 868 诊断：文本节点**选中之后**，工具条里到底有哪些按钮？

`text-fullscreen` 点了两轮都打不开。§84/§85 都写着「先探再判」，所以这里
不猜，直接把工具条的**内容**倒出来。

⚠️ ��意 `elementFromPoint` 验落点（843 的教训）：点坐标之前先确认那儿是
什么，别点到一个「看起来像按钮」的东西上。

⚠️ 只诊断，不改产品。
跑法：/opt/miniconda3/bin/python3 scripts/jimeng_probe868_textbar.py
"""

import json
import os
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "http://localhost:4317/jimeng/canvas/demo"
OUT = Path("/tmp/b868-textbar.json")

# ⚠️⚠️ 868 在这里连栽 4 次：下面这个「一个大函数、返回整个对象」的写法在
#   **插完文本节点之后**必定抛 `Cannot read properties of undefined
#   (reading 'push')`，而**插节点之前**同一段表达式跑得好好的。属性名无关
#   （`tooltbars`→`zzz` 一样炸）、单行化无关、隔离复现不出来。
#   **根因未验死**（⚠️ 未验证，不许当结论写）：不排除是 Playwright 对
#   「含嵌套箭头返回对象字面量的多行表达式」的处理问题，也可能是页面在插入
#   文本节点后装了什么全局/代理。**判据：症状确定，机制未知。**
#   处置：拆成几个**各干一件事**的小 evaluate。顺带的好处是失败可归因 ——
#   一步一步量，哪一步坏了就是哪一步坏，不必在一大坨里猜。
def q_count(pg, sel: str) -> int:
    return pg.evaluate("(s) => document.querySelectorAll(s).length", sel)


def q_text_expand(pg) -> dict:
    return pg.evaluate("""() => {
      const bs = [...document.querySelectorAll('button[aria-label="\u5168\u5c4f"]')];
      return {text_expand: document.querySelectorAll('[data-testid="text-expand"]').length,
              aria_fullscreen: bs.length,
              in_toolbar: bs.filter(b => !!b.closest('.react-flow__node-toolbar')).length,
              visible: bs.filter(b => { const r = b.getBoundingClientRect();
                                        return r.width > 1 && r.height > 1; }).length};
    }""")


def q_toolbar_buttons(pg, owner_tid: str) -> list[dict]:
    return pg.evaluate("""(tid) => {
      const n = document.querySelector('.react-flow__node[data-testid="' + tid + '"]');
      if (!n) return null;
      const tb = n.querySelector('.react-flow__node-toolbar');
      if (!tb) return null;
      return [...tb.querySelectorAll('button')].map(b => ({
        al: b.getAttribute('aria-label') || '',
        tid: b.getAttribute('data-testid') || '',
        txt: (b.innerText || '').trim().slice(0, 12),
      }));
    }""", owner_tid)


def q_editing(pg) -> bool:
    return pg.evaluate("() => !!document.querySelector("
                       "'.react-flow__node.selected [contenteditable]')")


def node_tids(pg) -> list[str]:
    return pg.evaluate(
        "() => [...document.querySelectorAll('.react-flow__node')]"
        ".map(n => n.getAttribute('data-testid'))")


def select(pg, tid: str) -> bool:
    pg.evaluate("() => document.querySelectorAll('.react-flow__node.selected')"
                ".forEach(n => n.dispatchEvent(new MouseEvent('mousedown', "
                "{bubbles: true})))")
    pt = pg.evaluate("""(tid) => {
      const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
      if (!n) return null;
      const r = n.getBoundingClientRect();
      const CTRL = 'button,[role=button],a,input,select,textarea';
      for (const [fx, fy] of [[0.5,0.5],[0.5,0.25],[0.25,0.5],[0.75,0.5]]) {
        const x = r.x + r.width * fx, y = r.y + r.height * fy;
        const top = document.elementFromPoint(x, y);
        if (top && n.contains(top) && !top.closest(CTRL)) return [x, y];
      }
      return null;
    }""", tid)
    if not pt:
        return False
    # ⚠️ 点之前**验落点**（843）：确认那儿确实是这个节点、且不是控件
    hit = pg.evaluate("([x,y])=>{const e=document.elementFromPoint(x,y);"
                      "return e?e.tagName+'/'+(e.getAttribute('contenteditable')"
                      "?':editable':'')+'|'+(e.className||'').toString()"
                      ".slice(0,26):null;}", list(pt))
    pg.mouse.click(pt[0], pt[1])
    time.sleep(0.8)
    return pg.locator(".react-flow__node.selected").count() == 1, hit


def main() -> int:
    url = os.environ.get("SNAP_URL", URL)
    res = {}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_context(viewport={"width": 1680, "height": 1050}).new_page()
        pg.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(4)

        before = set(node_tids(pg))
        pg.locator('button[aria-label="文本"]').first.click(timeout=8000)
        time.sleep(2.0)
        new = [t for t in node_tids(pg) if t not in before]
        print("=== 插入文本节点 ===")
        print(f"  新节点 testid = {new}")
        if not new:
            print("  ❌ 插不出文本节点")
            b.close()
            return 1
        nid = new[0]

        print("\n=== 刚插出来（自带编辑态？）===")
        res["just_inserted"] = {"editing": q_editing(pg),
                               "toolbars_on_page": q_count(
                                   pg, ".react-flow__node-toolbar"),
                               **q_text_expand(pg)}
        d = res["just_inserted"]
        print(f"  有编辑面={d['editing']}  text-expand={d['text_expand']}  "
              f"aria=全屏 {d['aria_fullscreen']}（在工具条内 {d['in_toolbar']}，"
              f"可见 {d['visible']}）")
        print("\n=== 选中一次 ===")
        r = select(pg, nid)
        sel_ok = r[0] if isinstance(r, tuple) else r
        hit = r[1] if isinstance(r, tuple) else None
        print(f"  选中={sel_ok} 落点={hit}")
        res["after_select"] = {"editing": q_editing(pg), **q_text_expand(pg),
                               "buttons": q_toolbar_buttons(pg, nid)}
        d = res["after_select"]
        print(f"  有编辑面={d['editing']}  text-expand={d['text_expand']}  "
              f"aria=全屏 {d['aria_fullscreen']}（在工具条内 {d['in_toolbar']}，"
              f"可见 {d['visible']}）")
        print(f"  该节点工具条按钮（{len(d['buttons'] or [])} 枚）:")
        for btn in (d["buttons"] or []):
            print(f"     al={btn['al']!r} tid={btn['tid']!r} txt={btn['txt']!r}")

        # ⚠️ 关键一步：审计 D 段（文本调色板）能打开 `text-bg-palette`，
        #    它在 insert→select 之后还做了**双击进编辑、再重新选中**。
        #    工具条的挂载条件是 `selected && !editing` —— 光「选中」不够，
        #    得先**经过一次编辑态**。上面量到的「0 枚按钮」就是缺这一步。
        print("\n=== 双击进编辑，再重新选中（审计 D 段的序列）===")
        nl = pg.locator(f'.react-flow__node[data-testid="{nid}"]')
        if nl.count():
            try:
                nl.first.dblclick(timeout=8000)
                time.sleep(1.2)
            except Exception as e:
                print(f"  双击失败：{str(e).splitlines()[0][:70]}")
        print(f"  进编辑后：有编辑面={q_editing(pg)}")
        r2 = select(pg, nid)
        ok2 = r2[0] if isinstance(r2, tuple) else r2
        print(f"  重新选中={ok2}")
        res["after_edit_reselect"] = {
            "editing": q_editing(pg), **q_text_expand(pg),
            "buttons": q_toolbar_buttons(pg, nid)}
        d2 = res["after_edit_reselect"]
        print(f"  有编辑面={d2['editing']}  text-expand={d2['text_expand']}  "
              f"aria=全屏 {d2['aria_fullscreen']}（在工具条内 {d2['in_toolbar']}，"
              f"可见 {d2['visible']}）")
        print(f"  该节点工具条按钮（{len(d2['buttons'] or [])} 枚）:")
        for btn in (d2["buttons"] or []):
            print(f"     al={btn['al']!r} tid={btn['tid']!r} txt={btn['txt']!r}")

        # 直接点它，看层出不出来
        print("\n=== 点 text-expand，看 text-fullscreen 出不出来 ===")
        te = pg.locator('[data-testid="text-expand"]')
        n_te = te.count()
        print(f"  text-expand 计数={n_te} 可见={te.first.is_visible() if n_te else '-'}")
        if n_te:
            bb = te.first.bounding_box()
            if bb:
                cx, cy = bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2
                hit = pg.evaluate("([x,y])=>{const e=document.elementFromPoint(x,y);"
                                  "return e?e.tagName+'/'+(e.getAttribute('data-testid')"
                                  "||e.getAttribute('aria-label')||''):null;}", [cx, cy])
                print(f"  点坐标 ({int(cx)},{int(cy)}) 落点={hit}  ← 先验落点再点")
                te.first.click(timeout=6000)
                time.sleep(1.5)
                got = pg.locator('[data-testid="text-fullscreen"]').count()
                print(f"  点后 text-fullscreen 计数 = {got}")
                res["after_click"] = {"hit": hit, "text_fullscreen": got}
                if got:
                    fs = pg.evaluate("""() => {
                      const e = document.querySelector('[data-testid="text-fullscreen"]');
                      const r = e.getBoundingClientRect();
                      return {rect: [Math.round(r.x), Math.round(r.y),
                                     Math.round(r.width), Math.round(r.height)],
                              role: e.getAttribute('role') || '',
                              focusables: e.querySelectorAll(
                                'button:not([disabled]),input,a[href],' +
                                '[role="menuitem"]').length};
                    }""")
                    print(f"  全屏层：{json.dumps(fs, ensure_ascii=False)}")
                    res["fullscreen_layer"] = fs
            pg.keyboard.press("Escape")
            time.sleep(0.6)

        print("\n=== 取消选中（点空白）后 ===")
        pg.mouse.click(1400, 700)
        time.sleep(0.8)
        res["after_deselect"] = q_text_expand(pg)
        d = res["after_deselect"]
        print(f"  text-expand={d['text_expand']}  aria=全屏 {d['aria_fullscreen']}")

        print("\n=== 全文搜 text-expand / aria=全屏 ===")
        res["global"] = pg.evaluate("""() => ({
          text_expand: document.querySelectorAll('[data-testid="text-expand"]').length,
          aria_fullscreen: [...document.querySelectorAll(
            'button[aria-label="全屏"]')].map(b => {
              const n = b.closest('.react-flow__node');
              const tb = b.closest('.react-flow__node-toolbar');
              return {in_node: n ? n.getAttribute('data-testid') : null,
                      in_toolbar: !!tb,
                      visible: (() => { const r = b.getBoundingClientRect();
                                        return r.width > 1 && r.height > 1; })()};
            }),
          fullscreen_layer: document.querySelectorAll(
            '[data-testid="text-fullscreen"]').length,
        })""")
        print("  " + json.dumps(res["global"], ensure_ascii=False, indent=2))
        b.close()
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n== 已写 {OUT} ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
