#!/usr/bin/env python3
"""batch 877 源站探针：清除钮的键盘行为，**四个筛选钮逐个**取样。

## 为什么要重取一遍

§93 的范围限制第 1 条：876 的键盘行为**只测了「性别」一个筛选钮**。
875 的**指针**行为是四钮逐个的（4/4），键盘侧不是 —— 而基线表里
`clear_in_tab_order` / `clear_enter_fires` / `clear_arrows_dead` /
`clear_esc_fires` 这几条写的是**这一层的**结论，不是「四个钮的」。

§69 定的规矩：**按同类推测不许当结论**。所以要么补测，要么把基线
降级成「只测过性别」。这批补测。

## 测四项（不是六项）

① **Tab 轨迹** —— Clear 是不是本钮的 Tab1（最可能因钮而异：DOM 位置）
② **Enter** —— 触发清除
③ **方向键** —— 焦点动不动（不接？）
④ **Esc** —— 清除 + 关面板

**Space 不单测**：它是原生 `<button>` 的默认激活键，与 Enter 同一个
浏览器行为路径；876 已在「性别」上实测过 Space 触发清除。重测四遍
同一件事不增加信息量。⚠️ 这一条是**我主动缩的量**，不是漏测 ——
要换成「Space 也许每个钮不同」那就把原文的「不增加信息量」删掉。

## 一次只让**一个**钮有值

Tab 序列会被其它钮的 Clear 污染（都选中时序列是 芯片→Clear→年龄→年龄的
Clear→…）。所以每一轮都先**清空全部四个**，再只选本钮。

## 判据纪律（876 的教训全部沿用）

- 定位用**量出来的坐标** + 程序化 `focus()`，**不发 click** 去聚焦 ——
  点 Clear 本身就是清除（876 整跑作废的原因之一）
- 读值用**零破坏**读法：芯片的可见文案就是值
- 读不到就记账，不出结论

## 计费边界

只点「音频」入口、选中节点、开「音色」、点筛选钮、点选项、点 Clear、按键。
**绝不**点生成/发送/购买/充值，**也绝不**点音色 chip 本身。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe877_clearfilter_kb_all.py
"""

import json

OUT = "/tmp/b877-src-clear-kb-all.json"

# 逐个走。选项名用的是 875 从层里读到的**真名**，不是照筛选名猜的
CASES = [
    ("性别", "男", "全部 性别"),
    ("年龄", "青年", "全部 年龄"),
    ("语言", "普通话", "全部 语言"),
    ("声音特点", "适合旁白", "全部 声音特点"),
]

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

# 芯片**程序化聚焦**（不点 —— 芯片是 toggle，点了会开层，876 就是栽在这）
FOCUS_CHIP_JS = """(label) => {
  const b = [...document.querySelectorAll('button[aria-expanded]')]
    .find(x => { const a = x.getAttribute('aria-label') || '';
                 return !a.startsWith('Clear ') && a.startsWith(label + ':'); });
  if (!b) return null;
  b.focus();
  return {focused: document.activeElement === b,
          aria: b.getAttribute('aria-label')};
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
        """Esc 之后**音频生成面板整个收起**（876c 实测：焦点落到
        `音频 node: 音频 NN` 这个节点本体上），`音色: 音色库` 压根不在
        DOM 里 —— 不是「点不到」，是**按钮没了**。
        「我没检测到」必须先确认「我够得着」。"""
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

    def chip(lb):
        return ev(CHIP_JS, lb)

    def clear_shown(lb):
        cl = ev(CLEAR_JS, lb)
        return bool(cl) and not cl.get("hidden")

    def value_text(lb):
        """**零破坏**读值：芯片的可见文案（选中时=值，未选中时=筛选名）。"""
        c = chip(lb)
        return c["text"] if c else None

    def set_value(lb, opt_text):
        """给某个筛选钮设值：点芯片开层 → 点选项。返回 None 表示成功。"""
        c = chip(lb)
        if not c:
            return f"认不出「{lb}」的筛选芯片"
        page.mouse.click(c["xy"][0], c["xy"][1])
        page.wait_for_timeout(700)
        o = ev(FILTER_JS, lb)
        if not o:
            return f"「{lb}」的层没打开"
        names = [x["text"] for x in o]
        if opt_text not in names:
            return f"选项「{opt_text}」不在「{lb}」层里：{names}"
        page.get_by_text(opt_text, exact=True).first.click(timeout=8000)
        page.wait_for_timeout(900)
        if not clear_shown(lb):
            return f"选完「{opt_text}」Clear 没出现"
        return None

    def clear_all():
        """把四个钮**全部**清空 —— Tab 序列会被别的钮的 Clear 污染，
        所以每轮只让一个钮有值。清空走「点 Clear」（875 已验证的路径）。"""
        if not open_voices():
            return "音色库打不开"
        for (lb, _, _) in CASES:
            if clear_shown(lb):
                page.evaluate(
                    """(label) => {
                      const b = document.querySelector(
                        `[aria-label="Clear ${label} filter"]`);
                      if (!b) return;
                      const r = b.getBoundingClientRect();
                      b.click();
                    }""", lb)
                page.wait_for_timeout(700)
        left = [lb for (lb, _, _) in CASES if clear_shown(lb)]
        return f"清空后还有 Clear：{left}" if left else None

    cases = []
    for (lb, pick, allopt) in CASES:
        rec = {"label": lb, "pick": pick}
        print(f"\n──── {lb} / 选「{pick}」 ────")

        def prep():
            """每项测量**各自**建立并验证前置态。"""
            w = clear_all()
            if w:
                return w
            return set_value(lb, pick)

        # ── ① Tab 轨迹 ───────────────────────────────────────
        why = prep()
        if why:
            rec["tab"] = {"verdict": f"前置态没成立：{why}"}
            print("  !! " + rec["tab"]["verdict"])
        else:
            rec["only_this_has_clear"] = [x for (x, _, _) in CASES
                                          if clear_shown(x)]
            start = ev(FOCUS_CHIP_JS, lb)
            r = {"start_focus": ev(FOCUS_JS), "traj": []}
            for _ in range(4):
                page.keyboard.press("Tab")
                page.wait_for_timeout(220)
                r["traj"].append(ev(FOCUS_JS))
            r["tab1_is_clear"] = (r["traj"][0]["aria"]
                                  == f"Clear {lb} filter")
            r["start_ok"] = start["focused"] if start else False
            rec["tab"] = r
            print(f"  ① 只有 {rec['only_this_has_clear']} 有 Clear；"
                  f"起点={r['start_focus']['aria']!r}")
            for i, t in enumerate(r["traj"]):
                mk = (" ←Clear" if t["aria"] == f"Clear {lb} filter" else "")
                print(f"     Tab{i+1}: {t['tag']}/{t['aria']!r} {t['text']!r}{mk}")
            print(f"     ⇒ Tab1 是本钮 Clear={r['tab1_is_clear']}")

        # ── ② Enter ──────────────────────────────────────────
        why = prep()
        if why:
            rec["enter"] = {"verdict": f"前置态没成立：{why}"}
        else:
            before = value_text(lb)
            fx = ev(FOCUS_CLEAR_JS, lb)
            r = {"before": before, "focus": fx}
            if not fx.get("focused"):
                r = {"verdict": "聚不到 Clear 上，测不了", "focus": fx}
            else:
                page.keyboard.press("Enter")
                page.wait_for_timeout(800)
                r["clear_after"] = clear_shown(lb)
                r["voices_open_after"] = ev(VOICES_JS)
                r["val_after"] = (value_text(lb) if ev(VOICES_JS)
                                  else "面板没了")
                r["fired"] = (not r["clear_after"]) or (
                    r["val_after"] != before)
            rec["enter"] = r
            print(f"  ② Enter：{r}")

        # ── ③ 方向键 ─────────────────────────────────────────
        why = prep()
        if why:
            rec["arrows"] = {"verdict": f"前置态没成立：{why}"}
        else:
            before = value_text(lb)
            fx = ev(FOCUS_CLEAR_JS, lb)
            r = {"before": before, "focus": fx}
            if not fx.get("focused"):
                r = {"verdict": "聚不到 Clear 上，测不了", "focus": fx}
            else:
                r["traj"] = []
                for k in ("ArrowDown", "ArrowRight"):
                    page.keyboard.press(k)
                    page.wait_for_timeout(250)
                    r["traj"].append({"key": k, "focus": ev(FOCUS_JS)})
                r["clear_after"] = clear_shown(lb)
                r["val_after"] = value_text(lb)
                r["moved"] = len({t["focus"]["aria"]
                                  for t in r["traj"]}) > 1
                r["fired"] = (not r["clear_after"]) or (
                    r["val_after"] != before)
            rec["arrows"] = r
            print(f"  ③ 方向键：焦点动={r.get('moved')} "
                  f"值 {before!r}→{r.get('val_after')!r} "
                  f"触发清除={r.get('fired')}")

        # ── ④ Esc ────────────────────────────────────────────
        why = prep()
        if why:
            rec["esc"] = {"verdict": f"前置态没成立：{why}"}
        else:
            before = value_text(lb)
            fx = ev(FOCUS_CLEAR_JS, lb)
            r = {"before": before, "focus": fx}
            if not fx.get("focused"):
                r = {"verdict": "聚不到 Clear 上，测不了", "focus": fx}
            else:
                page.keyboard.press("Escape")
                page.wait_for_timeout(900)
                r["voices_open_after"] = ev(VOICES_JS)
                r["focus_after"] = ev(FOCUS_JS)
                reopened = open_voices()
                r["reopened"] = reopened
                if not reopened:
                    # ⚠️ 读不到就记账，不出结论（876c 栽过）
                    r["verdict"] = ("前置态没成立：Esc 之后音色库没开回来，"
                                    "「值还在不在」测不到（不是「值没了」）")
                    r["value_survived"] = None
                else:
                    r["val_after_reopen"] = value_text(lb)
                    r["clear_after_reopen"] = clear_shown(lb)
                    r["value_survived"] = (r["val_after_reopen"] == before)
                    r["fired"] = not r["value_survived"]
            rec["esc"] = r
            print(f"  ④ Esc：面板还开={r.get('voices_open_after')} "
                  f"焦点后={r.get('focus_after', {}).get('aria')!r}")
            if "verdict" in r:
                print(f"     !! {r['verdict']}")
            else:
                print(f"     值 {before!r} → "
                      f"{r.get('val_after_reopen')!r}  "
                      f"⇒ 触发清除={r.get('fired')}")
        cases.append(rec)

    out["cases"] = cases
    ok = [c for c in cases if not any(
        isinstance(v, dict) and "verdict" in v
        for k, v in c.items() if k in ("tab", "enter", "arrows", "esc"))]
    out["n_fully_measured"] = len(ok)
    out["n_tab1_clear"] = sum(1 for c in cases
                              if (c.get("tab") or {}).get("tab1_is_clear") is True)
    out["n_enter_fires"] = sum(1 for c in cases
                               if (c.get("enter") or {}).get("fired") is True)
    out["n_arrows_dead"] = sum(1 for c in cases
                               if (c.get("arrows") or {}).get("fired") is False)
    out["n_esc_fires"] = sum(1 for c in cases
                             if (c.get("esc") or {}).get("fired") is True)
    out["n_esc_closes_voices"] = sum(1 for c in cases
                                    if (c.get("esc") or {}).get("voices_open_after") is False)
    print(f"\n== 汇总（对照 876 只测过「性别」的结论）：")
    print(f"   四项全测到的        {out['n_fully_measured']}/4")
    print(f"   Tab1 是本钮 Clear   {out['n_tab1_clear']}/4")
    print(f"   Enter 触发清除      {out['n_enter_fires']}/4")
    print(f"   方向键不触发        {out['n_arrows_dead']}/4")
    print(f"   Esc 触发清除        {out['n_esc_fires']}/4")
    print(f"   Esc 关掉音色库      {out['n_esc_closes_voices']}/4")
    out["verdict"] = "sampled"

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n== 已写 {OUT} ==")
