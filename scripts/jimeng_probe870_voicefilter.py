#!/usr/bin/env python3
"""batch 870 诊断：音色库的**筛选面板**是不是四个同时展开着？

## 起因（不是猜的，是读源码读出来的，但要量）

869 改 `open_layer()` 成「取最里层」之后，音频生成面板·全音色那一态的层归属
从 `audio-all-voices-listbox` 变成了 `audio-voice-filter-listbox`
（**筛选子面板**，见 `JimengAudioGenPanel.tsx:615`）。

顺着查源码，发现一处可疑的渲染条件（`JimengAudioGenPanel.tsx:608`）：

    {options ? ( <div … data-testid="audio-voice-filter-listbox"> … ) : null}

`options` 是 `FILTERS` 里写死的**非空数组**（性别/年龄/语言/声音特点 四组），
**没有任何「这个筛选开没开」的条件**。照字面读：只要「全音色」这一层开着，
**四个筛选面板就同时渲染**。

⚠️ 但**读源码不等于结论**（864 定的：静态只准当提示，浏览器实测才判定）。
所以本探针只量三件事：
  ① 打开「全音色」时，`audio-voice-filter-listbox` 有几个、分别在哪儿、
     可见不可见；
  ② 点其中一个筛选钮之后，**数量有没有变**、有没有哪个能关上；
  ③ 审计的 `open_layer()` 此刻认到的是哪一个。

⚠️ 源站这几个筛选面板的行为**没取样** —— 所以本探针**只描述复刻现状**，
不判「源站是不是也这样」。

## 判据同款，不复制一份

`open_layer()` 的 JS 直接从 `jimeng_unclickable_audit.py` 里取（同 869）。

跑法：`/opt/miniconda3/bin/python3 scripts/jimeng_probe870_voicefilter.py`
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "http://localhost:4317/jimeng/canvas/demo"
OUT = Path("/tmp/b870-voicefilter.json")
AUDIT = ROOT / "scripts" / "jimeng_unclickable_audit.py"

FILTER_TID = '[data-testid="audio-voice-filter-listbox"]'
VOICES_TID = '[data-testid="audio-all-voices-listbox"]'


def _extract_js(src: str, anchor: str) -> str:
    """从审计源码里取出 `anchor` 之后第一段 evaluate 的 JS。

    ⚠️ 定界符**拼出来**而不是写出来：写成字面量会被
    `jimeng_probe_js_syntax_check.py` 当成本探针的内联 JS 去解析
    （869 第一版就这么被带偏过一轮）。取不到就**抛**，不返回空串 ——
    静默取空会让探针「量了个空」还照样报通过。
    """
    i = src.index(anchor)
    open_kw = "page.evaluate(" + '"' * 3
    close_kw = '"' * 3 + ")"
    j = src.index(open_kw, i) + len(open_kw)
    k = src.index(close_kw, j)
    return src[j:k]


def _filters(pg) -> list[dict]:
    return pg.evaluate("""(sel) => [...document.querySelectorAll(sel)].map(e => {
      const r = e.getBoundingClientRect();
      const cs = getComputedStyle(e);
      const vis = r.width > 1 && r.height > 1
                  && cs.visibility !== 'hidden' && cs.display !== 'none';
      let top = null;
      if (vis) {
        const t = document.elementFromPoint(r.x + r.width / 2,
                                            r.y + r.height / 2);
        top = t ? (t.closest(sel) ? '自己' : t.tagName + '/'
                   + ((t.className || '') + '').slice(0, 30)) : null;
      }
      return {al: e.getAttribute('aria-label') || '',
              rect: [Math.round(r.x), Math.round(r.y),
                     Math.round(r.width), Math.round(r.height)],
              visible: vis, options: e.querySelectorAll('[role=option]').length,
              hit_at_center: top};
    })""", FILTER_TID)


def main() -> int:
    url = os.environ.get("SNAP_URL", URL)
    asrc = AUDIT.read_text(encoding="utf-8")
    open_layer_js = _extract_js(asrc, "def open_layer()")
    m = re.search(r'MODALISH_JS\s*=\s*"""(.*?)"""', asrc, re.S)
    if not m:
        print("❌ 取不到审计的 MODALISH_JS")
        return 1
    modalish_js = m.group(1)
    res: dict = {}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_context(viewport={"width": 1680, "height": 1050}).new_page()
        pg.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(4)

        # 插一个音频节点（集合差分，不按序号 —— 跟审计同一个认法）
        before = set(pg.evaluate(
            "() => [...document.querySelectorAll('.react-flow__node')]"
            ".map(n => n.getAttribute('data-testid'))"))
        t = pg.locator('button[aria-label="音频"]').first
        if not t.count():
            print("❌ 插不进音频节点 ⇒ 前置态没成立，**不是**「入口没有」")
            b.close()
            return 1
        t.click(timeout=8000)
        time.sleep(2.0)
        new = [x for x in pg.evaluate(
            "() => [...document.querySelectorAll('.react-flow__node')]"
            ".map(n => n.getAttribute('data-testid'))") if x not in before]
        print(f"新音频节点 = {new}")
        if not new:
            b.close()
            return 1
        nid = new[0]

        # 选中它（用审计那套：Escape 清场 + 找非控件落点）
        pg.keyboard.press("Escape")
        time.sleep(0.4)
        pt = pg.evaluate("""(tid) => {
          const n = document.querySelector(
            `.react-flow__node[data-testid="${tid}"]`);
          if (!n) return null;
          const r = n.getBoundingClientRect();
          const CTRL = 'button,[role=button],a,input,select,textarea';
          for (const [fx, fy] of [[0.5,0.5],[0.5,0.25],[0.25,0.5],[0.75,0.5]]) {
            const x = r.x + r.width * fx, y = r.y + r.height * fy;
            const top = document.elementFromPoint(x, y);
            if (top && n.contains(top) && !top.closest(CTRL)) return [x, y];
          }
          return null;
        }""", nid)
        if not pt:
            print("❌ 选不中音频节点")
            b.close()
            return 1
        pg.mouse.click(pt[0], pt[1])
        time.sleep(0.9)
        print(f"选中数 = {pg.locator('.react-flow__node.selected').count()}")

        # 打开「音色」（审计的路径：aria-label^="音色"，scope 含 node-panel）
        trig = pg.locator('.react-flow__node-toolbar button[aria-label^="音色"],'
                          '.react-flow__node-panel button[aria-label^="音色"]')
        print(f"「音色」触发器计数 = {trig.count()}")
        if not trig.count():
            print("❌ 触发器不在 DOM")
            b.close()
            return 1
        trig.first.click(timeout=8000)
        time.sleep(1.2)
        res["voices_open"] = pg.locator(VOICES_TID).count() > 0
        print(f"「全音色」层开着？{res['voices_open']}")

        # ① 一打开就量
        res["at_open"] = _filters(pg)
        res["open_layer_at_open"] = pg.evaluate(open_layer_js)
        print(f"\n① 刚打开：筛选面板 {len(res['at_open'])} 个，"
              f"open_layer() 认到 {res['open_layer_at_open']!r}")
        for f in res["at_open"]:
            print(f"   {f['al']!r} {f['rect']} 可见={f['visible']} "
                  f"选项={f['options']} 中心落点={f['hit_at_center']}")

        # ② 点其中一个筛选钮，看数量变不变、能不能关上
        res["after_click"] = {}
        chip = pg.locator(f'{VOICES_TID} button', has_text="性别").first
        if chip.count():
            bb = chip.bounding_box()
            if bb:
                cx, cy = bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2
                res["after_click"]["hit"] = pg.evaluate(
                    "([x,y])=>{const e=document.elementFromPoint(x,y);"
                    "return e?e.tagName+'/'+(e.innerText||'').trim().slice(0,10)"
                    ":null;}", [cx, cy])
            chip.click(timeout=6000)
            time.sleep(1.0)
            res["after_click"]["filters"] = _filters(pg)
            res["after_click"]["n"] = len(res["after_click"]["filters"])
            res["after_click"]["open_layer"] = pg.evaluate(open_layer_js)
            print(f"\n② 点「性别」之后：筛选面板 "
                  f"{res['after_click']['n']} 个（点之前 "
                  f"{len(res['at_open'])}），open_layer() 认到 "
                  f"{res['after_layer'] if False else res['after_click']['open_layer']!r}")
            for f in res["after_click"]["filters"]:
                print(f"   {f['al']!r} {f['rect']} 可见={f['visible']}")
        else:
            print("\n② 找不到「性别」筛选钮")
            res["after_click"]["n"] = None

        # ③ 再点一次同一个钮，看它能不能**关上**
        if chip.count():
            chip.click(timeout=6000)
            time.sleep(1.0)
            res["after_second_click"] = {"n": len(_filters(pg))}
            print(f"\n③ 再点一次「性别」：筛选面板 "
                  f"{res['after_second_click']['n']} 个")

        # ── 批 873：选完一个选项之后 ──────────────────────────────────
        #   源站实测（探针 873）：选「男」**和**选「全部 性别」**都**自动收层，
        #   焦点回到筛选钮。复刻原先用 `filterSel[label] !== undefined` 当
        #   开合标志 ⇒ 选中值还在 ⇒ **层收不起来**。873 拆成两个状态修的。
        res["after_select"] = {}
        # ⚠️ ③ 刚把层关上了，选项**已经不在 DOM 里** ⇒ 不先重开的话
        #   `get_by_text("男")` 数到 0，整段被静默跳过（第一版就这样白跑一轮）。
        if pg.locator(FILTER_TID).count() == 0:
            chip0 = pg.get_by_text("性别", exact=True).first
            if chip0.count():
                chip0.click(timeout=6000)
                time.sleep(0.8)
        if pg.locator(FILTER_TID).count() > 0:
            pick = pg.get_by_text("男", exact=True).first
            if pick.count():
                pick.click(timeout=6000)
                time.sleep(0.9)
                res["after_select"] = {
                    "panel_closed": pg.locator(FILTER_TID).count() == 0,
                    "chip_text": pg.evaluate("""() => {
                      for (const b of document.querySelectorAll('button')) {
                        const t = (b.innerText || '').trim();
                        if (t === '男' || t === '女'
                            || t === '全部 性别' || t === '性别') {
                          const r = b.getBoundingClientRect();
                          if (r.width < 20 || r.height < 10) continue;
                          return {t, expanded: b.getAttribute('aria-expanded')};
                        }
                      }
                      return null;
                    }"""),
                    "focus": pg.evaluate("""() => {
                      const a = document.activeElement;
                      if (!a || a === document.body) return 'body';
                      return a.tagName + '/' + ((a.innerText || '')
                             .trim().slice(0, 12));
                    }"""),
                }
                print("\n④ 选「男」之后：层收了="
                      f"{res['after_select']['panel_closed']}"
                      f" 芯片={res['after_select']['chip_text']}"
                      f" 焦点={res['after_select']['focus']!r}")
                # ⚠️ 关键回归点：芯片文案**已经变成「男」**了，此时再点它
                #   必须还能把层打开 —— 源站探针 873 第二轮就栽在这里
                #   （按旧文案「性别」去找，找不到 ⇒ 记成「前置态没成立」）。
                chip = pg.get_by_text("男", exact=True).first
                res["reopen_with_new_label"] = False
                if chip.count():
                    chip.click(timeout=6000)
                    time.sleep(0.8)
                    res["reopen_with_new_label"] = (
                        pg.locator(FILTER_TID).count() > 0)
                print(f"   文案变「男」之后再点它能重开="
                      f"{res['reopen_with_new_label']}")

        res["modalish_of_filter"] = pg.evaluate(modalish_js,
                                                 "audio-voice-filter-listbox")
        b.close()

    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\n== 已写 {OUT} ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
