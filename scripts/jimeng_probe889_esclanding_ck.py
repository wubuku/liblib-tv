#!/usr/bin/env python3
"""batch 889 复刻探针：同一组前置态，量 Esc 之后焦点**落哪**。

## 源站 889/889b/889c 已经查清的规则（889c 隔离出变量 = 按 Esc 前焦点）

| 按 Esc 前焦点 | 落点 | 工具条 | 面板 |
|---|---|---|---|
| 筛选**芯片** | 该音频节点本体 | False | 收 |
| **Clear** | 该音频节点本体 | False | 收 |
| **节点本体** | 该音频节点本体 | False | 收 |
| **画布（点过空白）** | **原地不动（仍在画布）** | False | 收 |
| **筛选层内**的选项 | **回到筛选芯片** | **True** | **只关层** |

⇒ 一句话：**落点由「按 Esc 之前焦点在哪」决定**。焦点在被卸载的工具条
里 ⇒ 落到该节点；焦点在筛选层里 ⇒ 回芯片；焦点在画布上 ⇒ 原地不动。

## 这里只量复刻侧同一条规则

每种前置态 **2 次**；**只有 2/2 同一类**才写「该前置态 ⇒ 该落点」。
读数一律带 **tag + aria + text + 在不在音频节点内 + 在不在层内** ——
只印 aria 那一版在 888 收尾把「落对了」显示成「没落」。

⚠️ 判**落点**钉**身份**（`in_audio_node`）不钉 aria 字面量：
复刻节点**不带** `aria-label='音频 node: 音频 N'`，那是源站才有的。

跑法：`/opt/miniconda3/bin/python3 scripts/jimeng_probe889_esclanding_ck.py`
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:4317/jimeng/canvas/demo"
OUT = Path("/tmp/b889-ck-esclanding.json")
LABEL = "性别"
PICK = "男"
REPS = 2

FOCUS_JS = """() => { const a = document.activeElement;
  if (!a || a === document.body) return {tag: 'BODY', aria: '(body)', text: '',
    in_audio_node: false, in_listbox: false};
  return {tag: a.tagName,
          aria: a.getAttribute('aria-label') || '',
          text: (a.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 20),
          in_audio_node: !!(a.closest && a.closest(
            '.react-flow__node-audio')),
          in_listbox: !!(a.closest && a.closest('[role=listbox]'))}; }"""

TOOLBAR_JS = """() => !!document.querySelector('button[aria-label^="音色"]')"""
VOICES_JS = """() => !!document.querySelector(
  '[data-testid="audio-all-voices-listbox"]')"""
LAYER_OPEN_JS = """(label) => !!(
  document.querySelector(
    `[role-testid] [role=listbox][aria-label="${label} options"]`)
  || document.querySelector(`[role=listbox][aria-label="${label} options"]`))"""
CENTER_JS = """(tid) => {
  const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
  if (!n) return null;
  const r = n.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
}"""
CHIP_JS = """(label) => {
  for (const b of document.querySelectorAll('button[aria-expanded]')) {
    const a = b.getAttribute('aria-label') || '';
    if (a.startsWith('Clear ')) continue;
    if (a.startsWith(label + ':')) {
      const r = b.getBoundingClientRect();
      return {aria: a, text: (b.innerText || '').trim(),
              rect: [Math.round(r.x), Math.round(r.y),
                     Math.round(r.width), Math.round(r.height)]};
    }
  }
  return null;
}"""
FOCUS_CHIP_JS = """(label) => {
  for (const b of document.querySelectorAll('button[aria-expanded]')) {
    const a = b.getAttribute('aria-label') || '';
    if (a.startsWith('Clear ')) continue;
    if (a.startsWith(label + ':')) {
      b.focus();
      return {focused: document.activeElement === b, aria: a};
    }
  }
  return {no_chip: true};
}"""
FOCUS_CLEAR_JS = """(label) => {
  const b = document.querySelector(`[aria-label="Clear ${label} filter"]`);
  if (!b) return {no_clear: true};
  b.focus();
  return {focused: document.activeElement === b,
          aria: b.getAttribute('aria-label') || ''};
}"""
CLEAR_JS = """(label) => !!document.querySelector(
  `[aria-label="Clear ${label} filter"]`)"""
# 点画布空白：与源站 888/889c **同一组候选坐标**；全落空时回落到
# pane 矩形里离所有节点最远的角（记录用的是哪一种）
BLANK_JS = """() => {
  for (const [x, y] of [[1300, 1000], [1360, 920], [1220, 1080],
                        [1400, 840], [400, 1080], [1500, 1000]]) {
    const t = document.elementFromPoint(x, y);
    if (t && t.closest('.react-flow__pane')
        && !t.closest('.react-flow__node')) return {xy: [x, y], from: 'list'};
  }
  const p = document.querySelector('.react-flow__pane');
  if (!p) return null;
  const r = p.getBoundingClientRect();
  const x = Math.round(r.x + r.width - 30);
  const y = Math.round(r.y + r.height - 30);
  const t = document.elementFromPoint(x, y);
  if (t && t.closest('.react-flow__pane') && !t.closest('.react-flow__node'))
    return {xy: [x, y], from: 'pane_rect'};
  return null;
}"""


def classify(f: dict) -> str:
    if f.get("in_audio_node"):
        return "节点本体"
    if f.get("aria") == "Canvas":
        return "Canvas"
    if f.get("tag") == "BODY":
        return "body"
    return "其他"


def main() -> int:
    url = os.environ.get("SNAP_URL", URL)
    res: dict = {"url": url}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_context(viewport={"width": 1680, "height": 1050}).new_page()
        pg.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(4)

        before = set(pg.evaluate(
            "() => [...document.querySelectorAll('.react-flow__node')]"
            ".map(n => n.getAttribute('data-testid'))"))
        t = pg.locator('button[aria-label="音频"]').first
        if not t.count():
            print("❌ 插不进音频节点 ⇒ 前置态没成立")
            b.close()
            return 1
        t.click(timeout=8000)
        time.sleep(2.0)
        new = [x for x in pg.evaluate(
            "() => [...document.querySelectorAll('.react-flow__node')]"
            ".map(n => n.getAttribute('data-testid'))") if x not in before]
        if not new:
            print("❌ 集合差分是空 ⇒ 插节点没生效")
            b.close()
            return 1
        nid = new[0]
        res["audio_node"] = nid
        pg.keyboard.press("Escape")
        time.sleep(0.4)

        def ev(js, arg=None):
            return pg.evaluate(js) if arg is None else pg.evaluate(js, arg)

        def blank():
            """点画布空白，让焦点落到画布上（889c 证明这**不会**被随后的
            点节点拉回节点 ⇒ 按 Esc 前焦点就留在画布）。"""
            r = ev(BLANK_JS)
            if r:
                pg.mouse.click(r["xy"][0], r["xy"][1])
                time.sleep(0.8)
            return r

        def select_node():
            for _ in range(3):
                if ev(TOOLBAR_JS):
                    return True
                c = ev(CENTER_JS, nid)
                if not c:
                    return False
                pg.mouse.click(c[0], c[1])
                time.sleep(1.0)
                if ev(TOOLBAR_JS):
                    return True
            return False

        def open_voices():
            for _ in range(3):
                if ev(VOICES_JS):
                    return True
                if not ev(TOOLBAR_JS):
                    select_node()
                vt = pg.locator('[aria-label="音色: 音色库"]')
                if not vt.count():
                    vt = pg.locator('button[aria-label^="音色"]')
                if vt.count():
                    vt.first.click(timeout=8000)
                    time.sleep(1.6)
                    if ev(VOICES_JS):
                        return True
            return ev(VOICES_JS)

        def set_value():
            c = ev(CHIP_JS, LABEL)
            if not c:
                return None
            xy = [c["rect"][0] + c["rect"][2] // 2,
                  c["rect"][1] + c["rect"][3] // 2]
            pg.mouse.click(xy[0], xy[1])
            time.sleep(0.9)
            if not ev(LAYER_OPEN_JS, LABEL):
                return None
            o = pg.get_by_text(PICK, exact=True).first
            if not o.count():
                return None
            o.click(timeout=8000)
            time.sleep(0.9)
            return ev(CLEAR_JS, LABEL)

        def rebuild(with_value=True):
            if not select_node():
                return "节点没选中"
            if not open_voices():
                return "音色库没开"
            if with_value and not ev(CLEAR_JS, LABEL):
                if not set_value():
                    return "芯片设不上值"
            return None

        def chip_center():
            c = ev(CHIP_JS, LABEL)
            if not c:
                return None
            return [c["rect"][0] + c["rect"][2] // 2,
                    c["rect"][1] + c["rect"][3] // 2]

        runs = []
        KINDS = ["chip", "clear", "canvas", "layer_open"]

        for kind in KINDS:
            for rep in range(1, REPS + 1):
                rec: dict = {"kind": kind, "rep": rep}
                why = None
                if kind == "canvas":
                    # ⚠️ 这一条**不走 rebuild()**：要的是 888/889c 的原样前置态
                    # —— **先点空白**（焦点落画布）**再**点节点中心开面板。
                    if ev(TOOLBAR_JS):
                        pg.keyboard.press("Escape")
                        time.sleep(0.8)
                    r = blank()
                    rec["blank_spot"] = r
                    c = ev(CENTER_JS, nid)
                    if not c:
                        why = "算不出节点中心"
                    else:
                        pg.mouse.click(c[0], c[1])
                        time.sleep(1.1)
                        if not ev(TOOLBAR_JS):
                            why = "点空白+点中心没开出面板"
                else:
                    why = rebuild()
                    if not why and kind == "chip":
                        r = ev(FOCUS_CHIP_JS, LABEL)
                        if not r.get("focused"):
                            why = f"聚焦点到芯片失败 {r}"
                    elif not why and kind == "clear":
                        if not ev(CLEAR_JS, LABEL):
                            why = "Clear 不存在（芯片没值）"
                        else:
                            r = ev(FOCUS_CLEAR_JS, LABEL)
                            if not r.get("focused"):
                                why = f"聚焦点到 Clear 失败 {r}"
                    elif not why and kind == "layer_open":
                        xy = chip_center()
                        if not xy:
                            why = "找不到筛选芯片"
                        else:
                            pg.mouse.click(xy[0], xy[1])
                            time.sleep(0.9)
                            if not ev(LAYER_OPEN_JS, LABEL):
                                why = "点芯片后层没开"
                if why:
                    rec["verdict"] = f"前置态没成立：{why}"
                    runs.append(rec)
                    print(f"  !! [{kind} #{rep}] {rec['verdict']}")
                    continue

                time.sleep(0.35)
                rec["focus_before"] = ev(FOCUS_JS)
                rec["layer_open_before"] = ev(LAYER_OPEN_JS, LABEL)
                rec["toolbar_before"] = ev(TOOLBAR_JS)

                pg.keyboard.press("Escape")
                time.sleep(1.0)

                rec["focus_after"] = ev(FOCUS_JS)
                rec["landing"] = classify(rec["focus_after"])
                rec["toolbar_after"] = ev(TOOLBAR_JS)
                rec["layer_open_after"] = ev(LAYER_OPEN_JS, LABEL)
                rec["verdict"] = "sampled"
                runs.append(rec)
                print(f"\n[{kind} #{rep}]")
                print(f"   按前：焦点={rec['focus_before']['aria']!r}"
                      f"/{rec['focus_before']['text']!r}"
                      f"  在节点内={rec['focus_before']['in_audio_node']}"
                      f"  层内={rec['focus_before']['in_listbox']}"
                      f"  层开着={rec['layer_open_before']}"
                      f"  工具条={rec['toolbar_before']}")
                print(f"   按后：{rec['landing']}"
                      f"  焦点={rec['focus_after']['aria']!r}"
                      f"/{rec['focus_after']['text']!r}"
                      f"  在节点内={rec['focus_after']['in_audio_node']}"
                      f"  工具条={rec['toolbar_after']}"
                      f"  层开着={rec['layer_open_after']}")

        res["runs"] = runs
        summary = {}
        for kind in KINDS:
            ls = [r.get("landing") for r in runs if r["kind"] == kind]
            summary[kind] = {
                "landings": ls,
                "n_sampled": len(ls),
                "stable": len(ls) == REPS and len(set(ls)) == 1,
                "landing": ls[0] if ls and len(set(ls)) == 1 else None,
            }
        res["summary"] = summary
        print("\n== 汇总（复刻侧）==")
        for kind in KINDS:
            s = summary[kind]
            mark = "OK " if s["stable"] else ("?? " if s["n_sampled"] else "—  ")
            print(f"  {mark}{kind:11s} 落点={s['landings']}"
                  f"  {'稳定' if s['stable'] else '不稳定/样本不足'}")
        b.close()

    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\n== 已写 {OUT} ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
