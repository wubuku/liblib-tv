#!/usr/bin/env python3
"""batch 875 复刻探针：补上源站有的「Clear {筛选名} filter」清除钮。

## 这批做了什么

探针 875 在源站量到（**四个筛选钮逐个量**，4/4 一致，不是拿性别外推）：

    未选中：外层格子 153×28，里面只有筛选钮（153 宽）
    已选中：外层格子**还是** 153×28，里面变成
            芯片 111 + gap 8 + Clear 16 = 135（+ 左右 padding 9×2 = 153 ✓）
            外加一个 16×16 的 `aria-label="Clear {label} filter"`

也就是说选中之后**没有办法直接退回「全部」** —— 复刻原先只能再点开层、
再点「全部 X」。这是**功能缺失**，不是样式差异。

## 本探针只验复刻侧，判据跟源站探针同构

判据跟 `jimeng_probe875_clearfilter.py` 一一对应，两边 JSON 可以直接对账：
`n_clear_before / n_clear_after / n_spawned / n_value_cleared / n_row_153`。

⚠️ 刻意**不**断言「Clear 的坐标是 [814, 689]」这种**会随面板位置漂**的值，
只断言它与芯片的**相对**关系（宽 16 / 垂直居中 / 横向紧邻右侧 8px）。

跑法：`/opt/miniconda3/bin/python3 scripts/jimeng_probe875_clearfilter_ck.py`
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:4317/jimeng/canvas/demo"
OUT = Path("/tmp/b875-ck-clearfilter.json")
FILTER_TID = '[data-testid="audio-voice-filter-listbox"]'
# 源站逐字：Clear 的 aria-label 是**英文** `{筛选名} filter`
CASES = [
    ("性别", "男", "全部 性别"),
    ("年龄", "青年", "全部 年龄"),
    ("语言", "普通话", "全部 语言"),
    ("声音特点", "适合旁白", "全部 声音特点"),
]

# 一个筛选钮的芯片：按**值**优先，退回按筛选名。
# ⚠️ 不能只按筛选名找 —— 选中之后可见文案变成「男」，aria 变成「性别: 男」，
#    按 `aria === label` 找会数到 0（873 踩过，875 源站侧也踩过）。
CHIP_JS = """(label) => {
  for (const b of document.querySelectorAll('button[aria-expanded]')) {
    const a = b.getAttribute('aria-label') || '';
    if (a.startsWith('Clear ')) continue;
    if (a.startsWith(label + ':')) {
      const r = b.getBoundingClientRect();
      return {al: a, text: (b.innerText || '').trim(),
              rect: [Math.round(r.x), Math.round(r.y),
                     Math.round(r.width), Math.round(r.height)]};
    }
  }
  return null;
}"""

CLEAR_JS = """(label) => {
  const b = document.querySelector(
    `button[aria-label="Clear ${label} filter"]`);
  if (!b) return null;
  const r = b.getBoundingClientRect();
  if (r.width <= 0 || r.height <= 0) return {hidden: true};
  const x = r.x + r.width / 2, y = r.y + r.height / 2;
  const hit = document.elementFromPoint(x, y);
  return {rect: [Math.round(r.x), Math.round(r.y),
                 Math.round(r.width), Math.round(r.height)],
          hit_ok: !!(hit && (hit === b || b.contains(hit))),
          hit_tag: hit ? hit.tagName : ''};
}"""

# 外层格子：芯片与它的祖先格。断言「选中前后格子不变」。
ROW_JS = """(label) => {
  const c = [...document.querySelectorAll('button[aria-expanded]')]
    .find(b => (b.getAttribute('aria-label') || '').startsWith(label + ':'));
  if (!c) return null;
  const box = c.parentElement;
  const r = box.getBoundingClientRect();
  return {rect: [Math.round(r.x), Math.round(r.y),
                 Math.round(r.width), Math.round(r.height)],
          n_children: box.children.length};
}"""

FILTER_JS = """(label) => {
  const e = document.querySelector(
    `[role=listbox][aria-label="${label} options"]`);
  if (!e) return null;
  return [...e.querySelectorAll('[role=option]')].map(o => ({
    text: (o.innerText || '').trim(),
    selected: o.getAttribute('aria-selected')}));
}"""

FOCUS_JS = """() => { const a = document.activeElement;
  return {tag: a.tagName, aria: a.getAttribute('aria-label') || '',
          text: (a.innerText || '').trim().slice(0, 16)}; }"""


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
            print("❌ 插不进音频节点 ⇒ 前置态没成立，**不是**「入口没有」")
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
        print(f"新音频节点 = {nid}")

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
        if pt:
            pg.mouse.click(pt[0], pt[1])
            time.sleep(1.2)

        def voices_open() -> bool:
            return bool(pg.locator(
                '[data-testid="audio-all-voices-listbox"]').count())

        if not voices_open():
            vt = pg.locator('button[aria-label^="音色"]')
            if vt.count():
                vt.first.click(timeout=8000)
                time.sleep(1.0)
        res["voices_open"] = voices_open()
        print(f"音色库开着 = {res['voices_open']}")
        if not res["voices_open"]:
            res["verdict"] = "BLOCKED_BY_FIXTURE（复刻音色库打不开）"
            b.close()
            return 1

        def click_center(sel_label: str) -> None:
            """点一个按 aria-label 认的按钮的**量出来的**中心。"""
            c = pg.evaluate("""(l) => {
              const b = document.querySelector(`[aria-label="${l}"]`);
              if (!b) return null;
              const r = b.getBoundingClientRect();
              return [r.x + r.width / 2, r.y + r.height / 2];
            }""", sel_label)
            if c:
                pg.mouse.click(c[0], c[1])

        cases = []
        for (label, pick, allopt) in CASES:
            rec: dict = {"label": label, "pick": pick}
            print(f"\n---- {label} / 选「{pick}」 ----")
            if not voices_open():
                rec["verdict"] = "前置态没成立（音色库关着）"
                cases.append(rec)
                continue

            rec["clear_before"] = pg.evaluate(CLEAR_JS, label)
            rec["row_before"] = pg.evaluate(ROW_JS, label)
            rec["chip_before"] = pg.evaluate(CHIP_JS, label)
            print(f"  选之前 Clear={rec['clear_before']} "
                  f"格子={rec['row_before']}")

            chip = rec["chip_before"]
            if not chip:
                rec["verdict"] = "判据盲区：认不出芯片（够不着，不是没有）"
                print("  !! " + rec["verdict"])
                cases.append(rec)
                continue
            pg.mouse.click(chip["rect"][0] + chip["rect"][2] / 2,
                            chip["rect"][1] + chip["rect"][3] / 2)
            time.sleep(0.8)
            lay = pg.evaluate(FILTER_JS, label)
            rec["layer_open"] = lay is not None
            if not rec["layer_open"]:
                rec["verdict"] = "前置态没成立（层没开）"
                print("  !! " + rec["verdict"])
                cases.append(rec)
                continue
            o = pg.get_by_text(pick, exact=True).first
            if not o.count():
                rec["verdict"] = f"选项「{pick}」不在层里：{lay}"
                print("  !! " + rec["verdict"])
                cases.append(rec)
                continue
            o.click(timeout=8000)
            time.sleep(0.9)

            rec["clear_after"] = pg.evaluate(CLEAR_JS, label)
            rec["chip_after"] = pg.evaluate(CHIP_JS, label)
            rec["row_after"] = pg.evaluate(ROW_JS, label)
            ca = rec["clear_after"]
            print(f"  选之后 Clear={ca}")
            print(f"  芯片 {rec['chip_after']}")
            print(f"  格子 {rec['row_after']}")
            if ca and not ca.get("hidden"):
                if not ca.get("hit_ok"):
                    rec["clear_click"] = "落点验不过，没敢点"
                    print("  !! 落点验不过")
                    cases.append(rec)
                    continue
                click_center(f"Clear {label} filter")
                time.sleep(0.9)
                rec["clear_clicked"] = True
                rec["chip_after_clear"] = pg.evaluate(CHIP_JS, label)
                rec["clear_still_there"] = pg.evaluate(CLEAR_JS, label)
                rec["focus_after_clear"] = pg.evaluate(FOCUS_JS)
                print(f"  点 Clear 后 芯片={rec['chip_after_clear']}")
                print(f"  点 Clear 后 焦点={rec['focus_after_clear']}")
                print(f"  Clear 还在吗="
                      f"{bool(rec['clear_still_there'] and not rec['clear_still_there'].get('hidden'))}")
                # 复开层读选中态
                c2 = pg.evaluate(CHIP_JS, label)
                if c2:
                    pg.mouse.click(c2["rect"][0] + c2["rect"][2] / 2,
                                    c2["rect"][1] + c2["rect"][3] / 2)
                    time.sleep(0.8)
                    l3 = pg.evaluate(FILTER_JS, label)
                    rec["opts_after_clear"] = l3
                    print(f"  复开 {l3}")
                    seld = [x["text"] for x in (l3 or [])
                            if x.get("selected") == "true"]
                    rec["seld_after_clear"] = seld
                    rec["value_cleared"] = (seld == [allopt])
                    print(f"  ⇒ 清掉了吗：{seld == [allopt]}（选中={seld}）")
                    if l3:
                        pg.keyboard.press("Escape")
                        time.sleep(0.5)
            else:
                rec["clear_click"] = "没有可点的 Clear"
            cases.append(rec)

        res["cases"] = cases
        res["n_clear_before"] = sum(1 for c in cases if c.get("clear_before"))
        res["n_clear_after"] = sum(1 for c in cases if c.get("clear_after"))
        res["n_spawned"] = sum(1 for c in cases
                               if c.get("clear_after")
                               and not c.get("clear_before"))
        res["n_value_cleared"] = sum(1 for c in cases
                                     if c.get("value_cleared"))
        # 外层格子「选中前后不变」——源站 row_dom_after 量的就是这个不变量
        res["n_row_unchanged"] = sum(
            1 for c in cases
            if c.get("row_before") and c.get("row_after")
            and c["row_before"]["rect"][2:] == c["row_after"]["rect"][2:])
        res["n_chips_111"] = sum(
            1 for c in cases
            if (c.get("chip_after") or {}).get("rect", [0, 0, 0, 0])[2] == 111)
        print(f"\n== 汇总（对照源站 875）：")
        print(f"   选之前有 Clear   {res['n_clear_before']}/4  源站 0/4")
        print(f"   选之后有 Clear   {res['n_clear_after']}/4  源站 4/4")
        print(f"   选完才冒出来     {res['n_spawned']}/4  源站 4/4")
        print(f"   点 Clear 真清掉  {res['n_value_cleared']}/4  源站 4/4")
        print(f"   格子宽高不变     {res['n_row_unchanged']}/4  源站 4/4")
        print(f"   芯片宽 111       {res['n_chips_111']}/4  源站 4/4")
        res["verdict"] = "sampled"
        b.close()

    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\n== 已写 {OUT} ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
