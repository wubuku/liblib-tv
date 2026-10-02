#!/usr/bin/env python3
"""batch 876b：**先查机制**，再谈清除钮的键盘行为。

## 上一跑（876）为什么作废

876 想测「在 Clear 上按 Enter/Space/方向键/Esc」，做法是
`page.mouse.click(clear 的坐标)` 来给 Clear 聚焦。**错就在这里** ——
点 Clear **本身就是清除动作**：点完值已经回落、Clear 已经消失、焦点已经
回到芯片。于是 ③④⑤⑥ 测的全是「**在芯片上**按 X」：

  - ③「按 Enter 值没了」—— 那是**鼠标点**清的，不是 Enter
  - ⑤「方向键焦点不动、Clear 还在=False」—— Clear 在测量前就没了
  - ⑥「Esc 关掉了整个音色库面板」—— 焦点在芯片上，Esc 关的是面板

**又一次「量错对象 → 把够不着写成没有」**，而且这次伪装得很好：输出里
每个字段都有值、每个结论都自洽，只有前置态是假的。

## 这一跑只回答三个**机制**问题

① Clear 为什么**不在 Tab 序列里**？（876 的 ①② 看着是「Tab 走不到」，
   但 `tabIndex` 属性读出来是 0 —— 两者矛盾，必须查清是哪一边错了）
② Clear 能不能被**程序化聚焦**（`el.focus()`）？—— 决定键盘测试可不可行
③ Clear 在 DOM 里的**位置**相对 chip 在哪？（它在 chip 右边 8px，
   但 Tab 从 chip 直接到了下一个筛选钮 ⇒ 几何相邻 ≠ DOM 相邻）

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe876b_clearfilter_mech.py
"""

import json

OUT = "/tmp/b876b-src-clear-mech.json"
LABEL = "性别"
PICK = "男"

FOCUS_JS = """() => { const a = document.activeElement;
  if (a === document.body) return {tag: 'BODY', aria: '(body)'};
  return {tag: a.tagName, aria: a.getAttribute('aria-label') || ''}; }"""

# ① + ③：Tab 属性的两种读法、祖先链、DOM 位置
MECH_JS = """(label) => {
  const cl = document.querySelector(`[aria-label="Clear ${label} filter"]`);
  if (!cl) return {no_clear: true};
  const chain = [];
  let n = cl, inert = null, hidden = null;
  while (n && n !== document.body && chain.length < 10) {
    const at = ['inert', 'aria-hidden', 'tabindex', 'role'];
    const marks = [];
    for (const a of at) {
      const v = n.getAttribute(a);
      if (v !== null) marks.push(a + '=' + JSON.stringify(v));
    }
    chain.push(n.tagName + (marks.length ? '[' + marks.join(' ') + ']' : ''));
    if (n.hasAttribute('inert')) inert = n.tagName;
    if (n.getAttribute('aria-hidden') === 'true') hidden = n.tagName;
    n = n.parentElement;
  }
  // DOM 位置：全文档 button 里的序号
  const btns = [...document.querySelectorAll('button')];
  const ci = btns.indexOf(cl);
  const chip = btns.find(b => {
    const a = b.getAttribute('aria-label') || '';
    return a.startsWith(label + ':');
  });
  const pi = chip ? btns.indexOf(chip) : -1;
  return {
    attr_tabindex: cl.getAttribute('tabindex'),      // 属性
    prop_tabIndex: cl.tabIndex,                       // DOM 属性
    is_disabled: cl.disabled === true,
    inert_ancestor: inert,
    aria_hidden_ancestor: hidden,
    dom_index_of_clear: ci,
    dom_index_of_chip: pi,
    adjacent_in_dom: (ci >= 0 && pi >= 0 && ci - pi === 1),
    between: pi >= 0 && ci >= 0
      ? btns.slice(Math.min(pi, ci) + 1, Math.max(pi, ci))
          .map(b => b.getAttribute('aria-label') || b.tagName)
      : null,
    chain};
}"""

# ②：能不能程序化聚焦（**不发 click**！）
FOCUSABLE_JS = """(label) => {
  const cl = document.querySelector(`[aria-label="Clear ${label} filter"]`);
  if (!cl) return {no_clear: true};
  const r = cl.getBoundingClientRect();
  const before = document.activeElement;
  cl.focus();
  const a = document.activeElement;
  return {
    rect: [Math.round(r.x), Math.round(r.y),
           Math.round(r.width), Math.round(r.height)],
    before_aria: before.getAttribute
      ? (before.getAttribute('aria-label') || before.tagName) : '?',
    focused_ok: a === cl,
    focus_aria: a.getAttribute('aria-label') || a.tagName,
    /* 若 focus() 失败，浏览器会把焦点落到 body；这跟「Clear 不可聚焦」
       是两回事，所以分别记，别合并成一个布尔。 */
    fell_to_body: a === document.body};
}"""

CLEAR_JS = """(label) => {
  const b = document.querySelector(`[aria-label="Clear ${label} filter"]`);
  if (!b) return null;
  const r = b.getBoundingClientRect();
  if (r.width <= 0 || r.height <= 0) return {hidden: true};
  return {rect: [Math.round(r.x), Math.round(r.y),
                 Math.round(r.width), Math.round(r.height)]};
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

    def open_voices():
        if ev(VOICES_JS):
            return True
        vt = page.locator('button[aria-label^="音色"]')
        if not vt.count():
            return False
        vt.first.click(timeout=8000)
        page.wait_for_timeout(1000)
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

    def value_now():
        """当前值：**复开层**读（876 的 `value_state()` 靠 Esc 收层，
        而 Esc 在某些焦点下会关掉整个面板，所以这里改成点开再点芯片
        收回去，两步都靠点，不靠 Esc）。"""
        c = ev(CHIP_JS, LABEL)
        if not c:
            return None
        page.mouse.click(c["xy"][0], c["xy"][1])
        page.wait_for_timeout(700)
        o = ev(FILTER_JS, LABEL)
        if o:
            cc = ev(CHIP_JS, LABEL)          # 再点芯片收层
            if cc:
                page.mouse.click(cc["xy"][0], cc["xy"][1])
                page.wait_for_timeout(600)
        seld = [x["text"] for x in (o or []) if x.get("selected") == "true"]
        return seld[0] if seld else None

    # ── ① 机制：Tab 属性 / 祖先 / DOM 位置 ────────────────────
    why = ensure_clear()
    if why:
        out["verdict"] = f"前置态没成立：{why}"
    else:
        mech = ev(MECH_JS, LABEL)
        out["mech"] = mech
        print(f"\n① 机制：")
        print(f"   attr tabindex = {mech['attr_tabindex']!r}   "
              f"prop tabIndex = {mech['prop_tabIndex']}")
        print(f"   disabled={mech['is_disabled']}  "
              f"inert 祖先={mech['inert_ancestor']}  "
              f"aria-hidden 祖先={mech['aria_hidden_ancestor']}")
        print(f"   DOM 序号：chip={mech['dom_index_of_chip']} "
              f"clear={mech['dom_index_of_clear']} "
              f"紧邻={mech['adjacent_in_dom']}")
        print(f"   两者之间隔着：{mech['between']}")
        print(f"   祖先链 {mech['chain']}")

        # ── ② 程序化聚焦能不能成（**不发 click**）──────────────
        f1 = ev(FOCUSABLE_JS, LABEL)
        out["focusable"] = f1
        print(f"\n② el.focus() 之后：焦点={f1['focus_aria']!r} "
              f"成功={f1['focused_ok']} 掉到body={f1['fell_to_body']}")

        # ── ②b 聚焦在 Clear 上时，Enter / Space / 方向键 / Esc ──
        #    这一段**每个键都重建一次前置态**，且**绝不用鼠标点**
        kb = {}
        for name, key in (("enter", "Enter"), ("space", "Space"),
                          ("arrow_down", "ArrowDown"),
                          ("arrow_right", "ArrowRight"),
                          ("esc", "Escape")):
            w = ensure_clear()
            if w:
                kb[name] = {"verdict": f"前置态没成立：{w}"}
                continue
            before = value_now()
            fx = ev(FOCUSABLE_JS, LABEL)
            if not fx.get("focused_ok"):
                kb[name] = {"verdict": "焦点聚不到 Clear 上，这项没法测",
                            "focus": fx}
                print(f"\n   [{key}] 聚不到焦点 ⇒ 测不了")
                continue
            rec = {"before_val": before, "focus": ev(FOCUS_JS)}
            page.keyboard.press(key)
            page.wait_for_timeout(800)
            rec["clear_after"] = ev(CLEAR_JS, LABEL)
            rec["focus_after"] = ev(FOCUS_JS)
            rec["voices_open_after"] = ev(VOICES_JS)
            rec["filter_layer_after"] = bool(ev(FILTER_JS, LABEL))
            rec["val_after"] = (value_now() if ev(VOICES_JS)
                                else "面板没了")
            rec["fired_clear"] = (not rec["clear_after"]) or (
                rec["val_after"] != before)
            kb[name] = rec
            print(f"\n   [{key}] 起焦点={rec['focus']['aria']!r}  "
                  f"值 {before!r} → {rec['val_after']!r}  "
                  f"Clear 还在={bool(rec['clear_after'])}  "
                  f"面板还开={rec['voices_open_after']}  "
                  f"层还开={rec['filter_layer_after']}  "
                  f"⇒ 触发清除={rec['fired_clear']}")
        out["keyboard"] = kb
        out["verdict"] = "sampled"

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n== 已写 {OUT} ==")
