#!/usr/bin/env python3
"""batch 876c：把 876 的三处**起点错**钉死，拿到能写进基线的结论。

## 876/876b 各自错在哪（两次都伪装得很好）

**876 的 ③④⑤⑥**：用 `mouse.click(Clear 坐标)` 去聚焦 Clear —— 但点 Clear
**本身就是清除**，点完 Clear 已经消失、焦点已回芯片。测的全是「芯片上按 X」。
（这一处 876b 已经用 `el.focus()` 修对了。）

**876 的 ①**：用 `mouse.click(chip 坐标)` 去聚焦芯片 —— 但芯片是 **toggle**，
点它会**打开筛选层**，焦点落到层内第一项（`全部 性别`）。于是 876 读到的
`start.aria == '男'` 其实**不是芯片**（芯片的 aria 是 `性别: 男`），
「Tab1 到年龄」是「**从层内** Tab 出去」（§82 实测这一层不困 Tab），
跟「Tab 走不到 Clear」**完全无关**。876 把这个当成了「Tab 到不了 Clear」。

**876b 残留的疑点**：876b 量到 Clear 的 `tabIndex=0`、DOM 里**紧跟**芯片
（序号 70→71，中间 0 个元素）、`el.focus()` 成功 —— 那 Tab **理应**能走到它。
两处结论打架，必须有一个是错的。876c 用**程序化 focus 芯片**当起点重测。

## 这一跑的三件事

① 焦点**真的在芯片上**（程序化 focus，不点）→ Tab 轨迹，看**经过没经过** Clear
② 方向键在 Clear 上：焦点**每一步**落在谁身上（不只看动没动）
③ Clear 上按 Esc 之后 —— **重开**音色库读值。只有这样才能分清
   「先触发清除、再关面板」和「只关面板、值还在」：当场读会被面板已关
   这一事实污染（Clear 读不到、值读不到，看起来像两件事同时发生）。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe876c_clearfilter_kb2.py
"""

import json

OUT = "/tmp/b876c-src-clear-kb2.json"
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

# 芯片的**程序化聚焦** + 它在 DOM 里的序号（用来跟 Clear 比邻接关系）
FOCUS_CHIP_JS = """(label) => {
  const b = [...document.querySelectorAll('button[aria-expanded]')]
    .find(x => { const a = x.getAttribute('aria-label') || '';
                 return !a.startsWith('Clear ') && a.startsWith(label + ':'); });
  if (!b) return null;
  const btns = [...document.querySelectorAll('button')];
  b.focus();
  return {focused: document.activeElement === b,
          aria: b.getAttribute('aria-label'),
          dom_index: btns.indexOf(b),
          /* 芯片和 Clear 之间隔着谁 —— Tab 序列的真正解释 */
          between: (() => {
            const cl = document.querySelector(
              `[aria-label="Clear ${label} filter"]`);
            if (!cl) return null;
            const ci = btns.indexOf(cl);
            const pi = btns.indexOf(b);
            return btns.slice(Math.min(pi, ci) + 1, Math.max(pi, ci))
              .map(x => x.getAttribute('aria-label') || x.tagName);
          })()};
}"""

FILTER_JS = """(label) => {
  const e = document.querySelector(
    `[role=listbox][aria-label="${label} options"]`);
  if (!e) return null;
  return [...e.querySelectorAll('[role=option]')].map(o => ({
    text: (o.innerText || '').trim(),
    selected: o.getAttribute('aria-selected')}));
}"""

VOICES_JS = """() => [...document.querySelectorAll('*')].some(e =>
  (e.innerText||'').trim() === '全音色' && !e.querySelector('*'))"""


def ev(js, arg=None):
    return page.evaluate(js) if arg is None else page.evaluate(js, arg)


def value_now():
    """当前值：**点开层读、点芯片收**。全程不按 Esc ——
    Esc 在某些焦点下会关掉整个面板（876b 实测），用它收层等于
    把被测对象换掉了。

    ⚠️ 第一版这里多写了个 `pg_obj` 形参，函数体里根本没用（它靠模块级
    的 `page`）⇒ 一到第二段就 `TypeError: missing 1 required positional
    argument`。已经跑出来的 ① 不受影响（它在崩之前就打印完了）。"""
    c = ev(CHIP_JS, LABEL)
    if not c:
        return None
    page.mouse.click(c["xy"][0], c["xy"][1])
    page.wait_for_timeout(700)
    o = ev(FILTER_JS, LABEL)
    if o:
        cc = ev(CHIP_JS, LABEL)
        if cc:
            page.mouse.click(cc["xy"][0], cc["xy"][1])
            page.wait_for_timeout(600)
    seld = [x["text"] for x in (o or []) if x.get("selected") == "true"]
    return seld[0] if seld else None


out = {}
page.goto(
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create",
    wait_until="domcontentloaded", timeout=90000)
page.wait_for_timeout(10000)
page.set_viewport_size({"width": 1512, "height": 1200})
page.wait_for_timeout(2500)
out["logged_in"] = page.locator('button[aria-label="音频"]').count() > 0
print(f"== 登录态 {out['logged_in']} ==")

if not out["logged_in"]:
    out["verdict"] = "BLOCKED_BY_FIXTURE（登录态没了）"
else:
    tid = None
    for cand in ('button[aria-label="音频"]', 'button:has-text("音频")'):
        loc = page.locator(cand)
        if not loc.count():
            continue
        before = set(ev("() => [...document.querySelectorAll('.react-flow__node')]"
                        ".map(n => n.getAttribute('data-testid')||'')"))
        loc.first.click(timeout=10000)
        page.wait_for_timeout(2500)
        after = ev("() => [...document.querySelectorAll('.react-flow__node')]"
                   ".map(n => n.getAttribute('data-testid')||'')")
        new = [t for t in after if t and t not in before]
        if new:
            tid = new[0]
            break
    out["audio_node"] = tid
    if tid:
        pt = ev("""(tid) => {
          const n = document.querySelector(
            `.react-flow__node[data-testid="${tid}"]`);
          if (!n) return null;
          const r = n.getBoundingClientRect();
          const CTRL = 'button,[role=button],a,input,select,textarea';
          for (const [fx,fy] of [[0.5,0.5],[0.5,0.25],[0.25,0.5],[0.75,0.5]]) {
            const x = r.x + r.width*fx, y = r.y + r.height*fy;
            const t = document.elementFromPoint(x, y);
            if (t && n.contains(t) && !t.closest(CTRL)) return [x, y];
          }
          return null;
        }""", tid)
        if pt:
            page.mouse.click(pt[0], pt[1])
            page.wait_for_timeout(1200)

    def reselect_node():
        """Esc 之后**音频生成面板整个收起**了（焦点实测落在
        `音频 node: 音频 NN` 这个**节点本体**上），于是
        `[aria-label="音色: 音色库"]` 压根不在 DOM 里 ——
        重开失败不是「点不到」，是**按钮没了**。
        「我没检测到」必须先确认「我够得着」：所以这里把前置态
        **重新搭起来**（重新选中节点 → 面板回来 → 再开音色库），
        而不是记成「值没了」。"""
        if page.locator('[aria-label="音色: 音色库"]').count():
            return True
        if tid:
            pt = ev("""(tid) => {
              const n = document.querySelector(
                `.react-flow__node[data-testid="${tid}"]`);
              if (!n) return null;
              const r = n.getBoundingClientRect();
              const CTRL = 'button,[role=button],a,input,select,textarea';
              for (const [fx,fy] of [[0.5,0.5],[0.5,0.25],[0.25,0.5],[0.75,0.5]]) {
                const x = r.x + r.width*fx, y = r.y + r.height*fy;
                const t = document.elementFromPoint(x, y);
                if (t && n.contains(t) && !t.closest(CTRL)) return [x, y];
              }
              return null;
            }""", tid)
            if pt:
                page.mouse.click(pt[0], pt[1])
                page.wait_for_timeout(1500)
        return page.locator('[aria-label="音色: 音色库"]').count() > 0

    def open_voices():
        """开音色库。三级前置态，每级都**验过**才往下走：
           ① 音色库已经开着？ ② 面板在不在？不在就**重新选中节点**
           ③ 点底行第三个选择器 + 重试。
        ⚠️ 第一版只点一次、等 1 秒就下结论，876c 前两跑都
        `reopened=False` —— 而判据把它当成了「值没了」：
        **第四次「把够不着写成没有」**，还印出了肯定句。"""
        for _ in range(3):
            if ev(VOICES_JS):
                return True
            if not reselect_node():
                continue
            for sel in ('[aria-label="音色: 音色库"]',
                        'button[aria-label^="音色"]'):
                vt = page.locator(sel)
                if vt.count():
                    vt.first.click(timeout=8000)
                    page.wait_for_timeout(1800)
                    if ev(VOICES_JS):
                        return True
        return ev(VOICES_JS)

    def ensure_clear():
        if not open_voices():
            return "音色库打不开"
        c = ev(CHIP_JS, LABEL)
        cl = ev(CLEAR_JS, LABEL)
        if c and cl and not cl.get("hidden"):
            return None
        if not c:
            return "认不出筛选芯片"
        page.mouse.click(c["xy"][0], c["xy"][1])
        page.wait_for_timeout(700)
        o = page.get_by_text(PICK, exact=True).first
        if not o.count():
            return f"选项「{PICK}」不在层里"
        o.click(timeout=8000)
        page.wait_for_timeout(900)
        cl = ev(CLEAR_JS, LABEL)
        if not cl or cl.get("hidden"):
            return "选完 Clear 没出现"
        return None

    res = {}

    # ── ① 焦点真在芯片上 → Tab 到底经过没经过 Clear ────────────
    why = ensure_clear()
    if why:
        res["tab"] = {"verdict": f"前置态没成立：{why}"}
    else:
        start = ev(FOCUS_CHIP_JS, LABEL)
        cl = ev(CLEAR_JS, LABEL)
        rec = {"start": start, "start_focus": ev(FOCUS_JS),
               "clear_dom_index": cl["dom_index"],
               "clear_tabindex": [cl["attr_tabindex"], cl["prop_tabIndex"]],
               "traj": []}
        for _ in range(5):
            page.keyboard.press("Tab")
            page.wait_for_timeout(220)
            rec["traj"].append(ev(FOCUS_JS))
        rec["reached_clear"] = any(
            t["aria"] == f"Clear {LABEL} filter" for t in rec["traj"])
        rec["tab1_is_clear"] = (rec["traj"][0]["aria"]
                                == f"Clear {LABEL} filter")
        res["tab"] = rec
        print(f"\n① 起点：程序化 focus 芯片 → 成功={start['focused']} "
              f"焦点={rec['start_focus']['aria']!r}")
        print(f"   芯片 DOM 序号={start['dom_index']}  "
              f"Clear DOM 序号={cl['dom_index']}  "
              f"两者之间隔着={start['between']}")
        for i, t in enumerate(rec["traj"]):
            mk = (" ←Clear" if t["aria"] == f"Clear {LABEL} filter"
                  else ("  [层内]" if t["in_listbox"] else ""))
            print(f"   Tab{i+1}: {t['tag']}/{t['aria']!r} {t['text']!r}{mk}")
        print(f"   ⇒ 经过 Clear={rec['reached_clear']}  "
              f"Tab1 就是 Clear={rec['tab1_is_clear']}")

    # ── ② 方向键在 Clear 上：每一步焦点落在谁身上 ──────────────
    why = ensure_clear()
    if why:
        res["arrows"] = {"verdict": f"前置态没成立：{why}"}
    else:
        before = value_now()
        ev("""(label) => {
          const b = document.querySelector(`[aria-label="Clear ${label} filter"]`);
          if (b) b.focus();
        }""", LABEL)
        rec = {"before_val": before, "focus": ev(FOCUS_JS), "traj": []}
        for k in ("ArrowDown", "ArrowRight", "ArrowUp", "ArrowLeft"):
            page.keyboard.press(k)
            page.wait_for_timeout(250)
            rec["traj"].append({"key": k, "focus": ev(FOCUS_JS)})
        rec["clear_after"] = ev(CLEAR_JS, LABEL)
        rec["val_after"] = value_now()
        rec["moved"] = len({t["focus"]["aria"] for t in rec["traj"]}) > 1
        res["arrows"] = rec
        print(f"\n② Clear 上按方向键（起 {rec['focus']['aria']!r}，"
              f"值 {before!r}）：")
        for t in rec["traj"]:
            print(f"   {t['key']:11s} → {t['focus']['tag']}/"
                  f"{t['focus']['aria']!r} {t['focus']['text']!r}")
        print(f"   ⇒ 焦点移动={rec['moved']}  值 {before!r}→{rec['val_after']!r}"
              f"  Clear 还在={bool(rec['clear_after'])}")

    # ── ③ Esc：**重开**读值，分清「清除了」和「只关面板」 ───────
    why = ensure_clear()
    if why:
        res["esc"] = {"verdict": f"前置态没成立：{why}"}
    else:
        before = value_now()
        ev("""(label) => {
          const b = document.querySelector(`[aria-label="Clear ${label} filter"]`);
          if (b) b.focus();
        }""", LABEL)
        rec = {"before_val": before, "focus": ev(FOCUS_JS)}
        page.keyboard.press("Escape")
        page.wait_for_timeout(900)
        rec["voices_open_after"] = ev(VOICES_JS)
        rec["filter_layer_after"] = bool(ev(FILTER_JS, LABEL))
        rec["focus_after"] = ev(FOCUS_JS)
        # ⚠️ 关键：**重开**音色库再读值。当场读会被「面板已经关了」
        #    污染（Clear 读不到、值读不到，看着像清除也发生了）。
        reopened = open_voices()
        rec["reopened"] = reopened
        # ⚠️⚠️ 判据必须把「**没开回来**」和「**值没了**」分成两栏。
        #   第一版 `value_survived = (val_after_reopen == before)`，
        #   reopened=False 时两边必然不等 ⇒ 印出肯定句「值没了」——
        #   第四次「查错对象 → 把够不着写成没有」。
        #   读不到就**记账**，不许出结论。
        if not reopened:
            rec["verdict"] = ("前置态没成立：Esc 之后**音色库没开回来**，"
                              "所以「值还在不在」**测不到**（不是「值没了」）")
            rec["value_survived"] = None      # None = 未知，不是 False
            print(f"\n③ Clear 上按 Esc：起焦点={rec['focus']['aria']!r}")
            print(f"   按下之后：音色库还开着={rec['voices_open_after']}  "
                  f"焦点={rec['focus_after']['aria']!r}")
            print(f"   !! {rec['verdict']}")
        else:
            rec["clear_after_reopen"] = ev(CLEAR_JS, LABEL)
            rec["val_after_reopen"] = value_now()
            rec["value_survived"] = (rec["val_after_reopen"] == before)
            print(f"\n③ Clear 上按 Esc：起焦点={rec['focus']['aria']!r}")
            print(f"   按下之后：音色库还开着={rec['voices_open_after']}  "
                  f"筛选层开着={rec['filter_layer_after']}  "
                  f"焦点={rec['focus_after']['aria']!r}")
            print(f"   重开音色库：{reopened}  值 {before!r} → "
                  f"{rec['val_after_reopen']!r}  "
                  f"Clear 又出现={bool(rec['clear_after_reopen'])}")
            print(f"   ⇒ 值在 Esc 之后"
                  f"{'还在（Esc 只关面板，没触发清除）' if rec['value_survived'] else '没了（Esc 触发了清除）'}")

    out.update(res)
    out["verdict"] = "sampled"

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n== 已写 {OUT} ==")
