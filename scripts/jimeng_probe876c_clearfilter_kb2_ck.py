#!/usr/bin/env python3
"""batch 876 复刻探针：清除钮的键盘行为，逐条对账源站 876c。

## 源站 876c 测到的（三次复现一致）

| 行为 | 源站 |
|---|---|
| Tab 序列 | 芯片 → **Clear** → 年龄 → 语言 → 声音特点 → 音色网格 |
|         | Clear **在** Tab 序列里（DOM 紧邻芯片，`tabIndex=0`） |
| Enter   | **触发清除**（值→全部 X，Clear 消失，**面板还开着**） |
| Space   | **触发清除**（同上） |
| 方向键  | 焦点**不动**（四个方向都留在 Clear 上），值不变 ⇒ **不接** |
| Esc     | **触发清除 + 关掉整个音色库面板**，焦点落到**音频节点本体** |

## 本探针只量复刻侧

⚠️ 876 第一跑**作废**，两处起点错（都写进 876 探针注释里）：
- 用 `mouse.click(Clear)` 聚焦 —— 但点 Clear **本身就是清除**
- 用 `mouse.click(chip)` 聚焦 —— 但芯片是 **toggle**，点它会**打开筛选层**，
  焦点落到层内第一项，于是「Tab1 到年龄」其实是「从层内 Tab 出去」，
  被我读成了「Tab 走不到 Clear」⇒ 876c 用**程序化 focus** 重测，结论相反

所以这里也用**程序化 focus**，一处鼠标点击都不发（除了重建前置态）。

## 预期会不一样的**那一条**

Esc：源站是「清除 + 关面板」。复刻的 Esc handler 挂在**筛选层**上
（`audio-voice-filter-listbox`），而 Clear 在**音色库 header**里、不在层内
⇒ Esc **不该冒泡到层**。到底会什么都不做、还是被别处接走，**必须实测**。

跑法：`/opt/miniconda3/bin/python3 scripts/jimeng_probe876c_clearfilter_kb2_ck.py`
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:4317/jimeng/canvas/demo"
OUT = Path("/tmp/b876-ck-clearfilter-kb2.json")
LABEL = "性别"
PICK = "男"

FOCUS_JS = """() => { const a = document.activeElement;
  if (a === document.body) return {tag: 'BODY', aria: '(body)'};
  return {tag: a.tagName,
          aria: a.getAttribute('aria-label') || '',
          text: (a.innerText || '').trim().replace(/\\s+/g,' ').slice(0, 16),
          in_listbox: !!(a.closest && a.closest('[role=listbox]'))}; }"""

CLEAR_JS = """(label) => {
  const b = document.querySelector(`[aria-label="Clear ${label} filter"]`);
  if (!b) return null;
  const r = b.getBoundingClientRect();
  if (r.width <= 0 || r.height <= 0) return {hidden: true};
  return {rect: [Math.round(r.x), Math.round(r.y),
                 Math.round(r.width), Math.round(r.height)],
          attr_tabindex: b.getAttribute('tabindex'),
          prop_tabIndex: b.tabIndex,
          dom_index: [...document.querySelectorAll('button')].indexOf(b)};
}"""

CHIP_JS = """(label) => {
  for (const b of document.querySelectorAll('button[aria-expanded]')) {
    const a = b.getAttribute('aria-label') || '';
    if (a.startsWith('Clear ')) continue;
    if (a.startsWith(label + ':')) {
      const r = b.getBoundingClientRect();
      return {aria: a, text: (b.innerText || '').trim(),
              xy: [Math.round(r.x + r.width / 2),
                   Math.round(r.y + r.height / 2)]};
    }
  }
  return null;
}"""

FOCUS_CHIP_JS = """(label) => {
  const b = [...document.querySelectorAll('button[aria-expanded]')]
    .find(x => { const a = x.getAttribute('aria-label') || '';
                 return !a.startsWith('Clear ') && a.startsWith(label + ':'); });
  if (!b) return null;
  const btns = [...document.querySelectorAll('button')];
  b.focus();
  const cl = document.querySelector(`[aria-label="Clear ${label} filter"]`);
  return {focused: document.activeElement === b,
          aria: b.getAttribute('aria-label'),
          dom_index: btns.indexOf(b),
          clear_dom_index: cl ? btns.indexOf(cl) : -1,
          between: (() => {
            if (!cl) return null;
            const ci = btns.indexOf(cl), pi = btns.indexOf(b);
            return btns.slice(Math.min(pi, ci) + 1, Math.max(pi, ci))
              .map(x => x.getAttribute('aria-label') || x.tagName);
          })()};
}"""

FOCUS_CLEAR_JS = """(label) => {
  const b = document.querySelector(`[aria-label="Clear ${label} filter"]`);
  if (!b) return {no_clear: true};
  b.focus();
  return {focused: document.activeElement === b,
          aria: document.activeElement.getAttribute('aria-label') || ''};
}"""

FILTER_JS = """(label) => {
  const e = document.querySelector(
    `[role-testid] [role=listbox][aria-label="${label} options"]`)
    || document.querySelector(`[role=listbox][aria-label="${label} options"]`);
  if (!e) return null;
  return [...e.querySelectorAll('[role=option]')].map(o => ({
    text: (o.innerText || '').trim(),
    selected: o.getAttribute('aria-selected')}));
}"""

VOICES_JS = """() => !!document.querySelector(
  '[data-testid="audio-all-voices-listbox"]')"""

# ⚠️⚠️ 批 888 补：Esc 的行为由**两个**变量决定（887 实测）——
#   **焦点在哪**（§95/§96）**和层开没开**。874 那一跑**层是开着的**
#   （为了读 `aria-selected` 特意重开过层），所以它读到的「值保留」
#   **只对「层开着」成立**。
#   芯片的 onKeyDown 只在**焦点在芯片上**时触发，而**层开着时焦点在层内**
#   （871 实测开层接管焦点）⇒ 芯片 handler 那条路径上**层必然是收着的**，
#   而那时源站是**清值**（887：`男 → 性别`、Clear 重开后不在）。
#   所以这里把「层开没开」**显式记进结果**，别再让它隐在探针的起点里 ——
#   874 就是在隐式起点上读错了结论。
LAYER_OPEN_JS = """(label) => !!(
  document.querySelector(
    `[role-testid] [role=listbox][aria-label="${label} options"]`)
  || document.querySelector(`[role=listbox][aria-label="${label} options"]`))"""


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
            return pg.evaluate(VOICES_JS)

        def layer_open() -> bool:
            return pg.evaluate(LAYER_OPEN_JS, LABEL)

        def focus_desc(d: dict) -> str:
            """把焦点读数**渲染成人能判**的一句话。

            ⚠️⚠️ 888 补：第一版这几处都只印 `aria`，于是复刻侧的落点
            （`DIV` / `text='音频 1'` / `aria` 为**空**）打出来是
            `焦点=''` —— 看着像「焦点丢了」，其实**正落在该音频节点本体**
            上（886 定的落点）。源站节点带
            `aria-label='音频 node: 音频 N'`，**复刻节点不带**，只印
            aria 就把「落对了」**显示成「没落」**。
            ⇒ 读数的**呈现**本身也会骗人：先证「到底读到了什么」再下结论。
            """
            a = d.get("aria") or ""
            t = (d.get("text") or "").strip()
            return f"{d.get('tag')}/aria={a!r}/text={t!r}"

        def reselect() -> bool:
            if pg.locator('[aria-label^="音色"]').count():
                return True
            if pt:
                pg.mouse.click(pt[0], pt[1])
                time.sleep(1.5)
            return pg.locator('[aria-label^="音色"]').count() > 0

        def open_voices() -> bool:
            for _ in range(3):
                if voices_open():
                    return True
                if not reselect():
                    continue
                vt = pg.locator('button[aria-label^="音色"]')
                if vt.count():
                    vt.first.click(timeout=8000)
                    time.sleep(1.6)
                    if voices_open():
                        return True
            return voices_open()

        def chip():
            return pg.evaluate(CHIP_JS, LABEL)

        def value_now():
            """⚠️⚠️ 这个读法**有破坏性**，而且已经害了本探针第一跑。

            它靠「点芯片开层 → 读选项 → 点芯片收层」来读 `aria-selected`，
            属于**诊断动作改被诊断状态**（我自己的纪律里就写着这条）。
            后果实测到了：跑完这一句之后 `FOCUS_CLEAR_JS` 报 `no_clear`
            —— Clear **不见了**，于是 Enter/Space/方向键三项全记成
            「聚不到焦点 ⇒ 测不了」，③ 的 `before_val` 也变成了
            「全部 性别」（前置态本该是「男」）。

            换成**零破坏**读法：芯片的**可见文案本身就是值** ——
            源站 874 实测选完 `first_text='男'`，未选中时是筛选名；
            复刻 `{filterSel[label] ?? label}` 完全同构。
            于是不点任何东西就能读到值。

            保留本函数只作**交叉校验**用（要确认层内 `aria-selected`
            与文案一致），默认不调。"""
            c = chip()
            if not c:
                return None
            pg.mouse.click(c["xy"][0], c["xy"][1])
            time.sleep(0.7)
            o = pg.evaluate(FILTER_JS, LABEL)
            if o:
                cc = chip()
                if cc:
                    pg.mouse.click(cc["xy"][0], cc["xy"][1])
                    time.sleep(0.6)
            seld = [x["text"] for x in (o or []) if x.get("selected") == "true"]
            return seld[0] if seld else None

        def value_text():
            """零破坏读值：只读芯片的**可见文案**（不发任何点击）。
            选中某个具体值时文案就是那个值；未选中时是筛选名。
            配合 `clear_present` 一起用，就能无歧义地判「有没有值」。"""
            c = chip()
            return c["text"] if c else None

        def clear_present():
            cl = pg.evaluate(CLEAR_JS, LABEL)
            return bool(cl) and not cl.get("hidden")

        def ensure_clear() -> str | None:
            if not open_voices():
                return "音色库打不开"
            c = chip()
            cl = pg.evaluate(CLEAR_JS, LABEL)
            if c and cl and not cl.get("hidden"):
                return None
            if not c:
                return "认不出筛选芯片"
            pg.mouse.click(c["xy"][0], c["xy"][1])
            time.sleep(0.7)
            o = pg.get_by_text(PICK, exact=True).first
            if not o.count():
                return f"选项「{PICK}」不在层里"
            o.click(timeout=8000)
            time.sleep(0.9)
            cl = pg.evaluate(CLEAR_JS, LABEL)
            if not cl or cl.get("hidden"):
                return "选完 Clear 没出现"
            return None

        # ── ① Tab ─────────────────────────────────────────────
        why = ensure_clear()
        if why:
            res["tab"] = {"verdict": f"前置态没成立：{why}"}
        else:
            start = pg.evaluate(FOCUS_CHIP_JS, LABEL)
            cl = pg.evaluate(CLEAR_JS, LABEL)
            rec = {"start": start, "start_focus": pg.evaluate(FOCUS_JS),
                   "clear_dom_index": cl["dom_index"],
                   "clear_tabindex": [cl["attr_tabindex"], cl["prop_tabIndex"]],
                   "traj": []}
            for _ in range(5):
                pg.keyboard.press("Tab")
                time.sleep(0.22)
                rec["traj"].append(pg.evaluate(FOCUS_JS))
            rec["reached_clear"] = any(
                x["aria"] == f"Clear {LABEL} filter" for x in rec["traj"])
            rec["tab1_is_clear"] = (rec["traj"][0]["aria"]
                                    == f"Clear {LABEL} filter")
            res["tab"] = rec
            print(f"\n① 起点 focus 芯片 → 成功={start['focused']} "
                  f"焦点={rec['start_focus']['aria']!r}")
            print(f"   芯片序号={start['dom_index']} Clear 序号="
                  f"{cl['dom_index']} 之间隔着={start['between']}")
            for i, x in enumerate(rec["traj"]):
                mk = (" ←Clear" if x["aria"] == f"Clear {LABEL} filter"
                      else ("  [层内]" if x["in_listbox"] else ""))
                print(f"   Tab{i+1}: {x['tag']}/{x['aria']!r} {x['text']!r}{mk}")
            print(f"   ⇒ 经过 Clear={rec['reached_clear']}  "
                  f"Tab1 就是 Clear={rec['tab1_is_clear']}")

        # ── ② Enter / Space / 方向键 ───────────────────────────
        for name, key in (("enter", "Enter"), ("space", "Space"),
                          ("arrow_down", "ArrowDown"),
                          ("arrow_right", "ArrowRight")):
            why = ensure_clear()
            if why:
                res[name] = {"verdict": f"前置态没成立：{why}"}
                continue
            before_val = value_text()
            fx = pg.evaluate(FOCUS_CLEAR_JS, LABEL)
            if not fx.get("focused"):
                res[name] = {"verdict": "聚不到 Clear 上，测不了", "focus": fx}
                print(f"\n   [{key}] 聚不到焦点 ⇒ 测不了")
                continue
            rec = {"before_val": before_val, "focus": pg.evaluate(FOCUS_JS)}
            pg.keyboard.press(key)
            time.sleep(0.8)
            rec["clear_after"] = pg.evaluate(CLEAR_JS, LABEL)
            rec["focus_after"] = pg.evaluate(FOCUS_JS)
            rec["voices_open_after"] = voices_open()
            rec["val_after"] = value_text() if voices_open() else "面板没了"
            rec["fired_clear"] = (not rec["clear_after"]) or (
                rec["val_after"] != before_val)
            res[name] = rec
            print(f"\n   [{key}] 起焦点={rec['focus']['aria']!r}  "
                  f"值 {before_val!r}→{rec['val_after']!r}  "
                  f"Clear 还在={bool(rec['clear_after'])}  "
                  f"面板还开={rec['voices_open_after']}  "
                  f"焦点后={rec['focus_after']['aria']!r}  "
                  f"⇒ 触发清除={rec['fired_clear']}")

        # ── ③ Esc（源站是「清除 + 关面板」，这里是差异点）───────
        why = ensure_clear()
        if why:
            res["esc"] = {"verdict": f"前置态没成立：{why}"}
        else:
            before_val = value_text()
            fx = pg.evaluate(FOCUS_CLEAR_JS, LABEL)
            rec = {"before_val": before_val, "focus": pg.evaluate(FOCUS_JS)}
            pg.keyboard.press("Escape")
            time.sleep(0.9)
            rec["voices_open_after"] = voices_open()
            rec["filter_layer_after"] = bool(
                pg.evaluate(FILTER_JS, LABEL))
            rec["focus_after"] = pg.evaluate(FOCUS_JS)
            reopened = open_voices()
            rec["reopened"] = reopened
            # ⚠️ 读不到就记账，不出结论（源站 876c 前两跑栽在这）
            if not reopened:
                rec["verdict"] = ("前置态没成立：Esc 之后音色库没开回来，"
                                  "「值还在不在」测不到（不是「值没了」）")
                rec["value_survived"] = None
                print(f"\n③ Clear 上按 Esc：面板还开="
                      f"{rec['voices_open_after']} 焦点="
                      f"{focus_desc(rec['focus_after'])}")
                print(f"   !! {rec['verdict']}")
            else:
                rec["clear_after_reopen"] = pg.evaluate(CLEAR_JS, LABEL)
                rec["val_after_reopen"] = value_text()
                rec["value_survived"] = (rec["val_after_reopen"] == before_val)
                print(f"\n③ Clear 上按 Esc：起焦点={rec['focus']['aria']!r}")
                print(f"   按下后：面板还开={rec['voices_open_after']} "
                      f"焦点={focus_desc(rec['focus_after'])}")
                print(f"   重开：{reopened}  值 {before_val!r} → "
                      f"{rec['val_after_reopen']!r}  "
                      f"Clear 又出现={bool(rec['clear_after_reopen'])}")
                print(f"   ⇒ 值{'还在' if rec['value_survived'] else '没了'}")
            res["esc"] = rec

        # ── ④ 焦点在**芯片**上按 Esc ──
        #    ⚠️⚠️ 888 更正：这段原来写着「874 源站：只收层、值保留」，
        #    那是 874 那一跑的**读数**，而它**层是开着的**。887 在**同一次
        #    运行**里读到芯片这条路径上**值被清**（`男 → 性别`、Clear 重开后
        #    不在）⇒ 层**收着**时源站是**清值**。
        #    ⇒ 结论措辞按 887 改回来：「值**没了**」才是**与源站一致**；
        #      「还在」反而是**与源站相反**（第一版的措辞正好说反了 ——
        #      探针把一条被限定过适用范围的读数当成了普适结论）。
        why = ensure_clear()
        if why:
            res["esc_on_chip"] = {"verdict": f"前置态没成立：{why}"}
        else:
            before_val = value_text()
            pg.evaluate(FOCUS_CHIP_JS, LABEL)
            rec = {"before_val": before_val,
                   "focus": pg.evaluate(FOCUS_JS),
                   # 第三个变量**显式**记下来：层开没开（874 就栽在这）
                   "layer_open_before_esc": layer_open()}
            pg.keyboard.press("Escape")
            time.sleep(0.9)
            rec["voices_open_after"] = voices_open()
            rec["focus_after"] = pg.evaluate(FOCUS_JS)
            reopened = open_voices()
            rec["reopened"] = reopened
            if not reopened:
                rec["verdict"] = "前置态没成立：音色库没开回来，测不到"
                rec["value_survived"] = None
                print(f"\n④ 芯片上按 Esc：面板还开={rec['voices_open_after']}  "
                      f"!! {rec['verdict']}")
            else:
                rec["val_after"] = value_text()
                rec["value_survived"] = (rec["val_after"] == before_val)
                verdict = (
                    "值被清了（与 887 源站一致：层收着时清值）"
                    if not rec["value_survived"] else
                    "值还在（⚠️ 与 887 源站相反：层收着时该清）")
                print(f"\n④ 芯片上按 Esc：起焦点={rec['focus']['aria']!r}  "
                      f"层开着={rec['layer_open_before_esc']}  "
                      f"面板还开={rec['voices_open_after']}  "
                      f"焦点={focus_desc(rec['focus_after'])}")
                print(f"   值 {before_val!r} → {rec['val_after']!r}  "
                      f"⇒ {verdict}")
            res["esc_on_chip"] = rec

        b.close()

    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\n== 已写 {OUT} ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
