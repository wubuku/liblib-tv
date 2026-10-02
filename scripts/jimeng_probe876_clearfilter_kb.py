#!/usr/bin/env python3
"""batch 876 源站探针：那个「Clear {筛选名} filter」清除钮的**键盘**行为。

## ⛔ 本文件**整跑作废**（2026-10-02，批 876 定，verifier AA.1 钉住）

**读这里的任何输出都���错的。** 作废原因有**两处**，都出在「用什么办法
把焦点放到被测元素上」——被测元素还没测到，状态已经被测量动作改了：

1. ③④⑤⑥ 用 `page.mouse.click(Clear 的坐标)` 聚焦 Clear。**点 Clear 本身就是
   清除** —— 点完值已回落、Clear 已消失、焦点已回芯片。于是这四项测的全是
   「**在芯片上**按 X」。
2. ① 用 `page.mouse.click(芯片的坐标)` 聚焦芯片。但芯片是 **toggle**，点它会
   **打开筛选层**，焦点落到层内第一项（`全部 性别`）。所以 876 读到的
   `start.aria == '男'` 根本**不是芯片**（芯片的 aria 是 `性别: 男`），
   「Tab1 到年龄」是「**从层内** Tab 出去」，却被读成了「Tab 走不到 Clear」。

真结论由 `jimeng_probe876b_clearfilter_mech.py`（查机制）+ 
`jimeng_probe876c_clearfilter_kb2.py`（用**程序化 focus**，三次复现）给出：
**Tab1 就是 Clear** —— 和本跑读到的**正好相反**。

⚠️ 这个文件**故意留在库里**：只留跑对的那几个，半年后会有人重新踩同一个坑，
而且会以为「当时就是对的」。

## 为什么要单独取样

批 875 挖出清除钮并把**指针**路径量透了（4/4：未选中时不存在 / 选完出现 /
16×16 / 芯片右侧 8 / 点它值回落、自己消失、焦点回芯片）。但**键盘一条没测**。

复刻那边它就是个 `<button>`，**默认可 Tab 到** —— 可这是**框架默认值**，
不是源站行为。§82 定的规矩：源站没取样的行为**不许**当成「已对齐」，
更不许在 README 结论段用陈述句写。所以这批去把样取回来。

## 问的六件事（每件都**各自建立前置态**）

① Tab 能不能走到 Clear？—— 顺序是什么（chip → Clear → 下一个 chip？）
② Shift+Tab 反向走不走得通？
③ 在 Clear 上按 **Enter** —— 会不会清值？（键盘触发，不是鼠标点）
④ 在 Clear 上按 **Space** —— 同上
⑤ 在 Clear 上按**方向键** —— 有反应吗？
⑥ 在 Clear 上按 **Esc** —— 触发清除？只收层？还是关掉整个面板？

⚠️ ③/④ 属���「键盘触发清除」——**不涉及计费**（不是生成/发送/购买/充值，
也不是点音色 chip 本身）。⑥ 可能把面板关掉，测完必须重开音色库。

## 判据纪律

- 每项**各自**重建成「Clear 可见」的前置态，不用上一项的残留状态。
- 读**轨迹**（焦点每一步落在谁身上）而不是只读一个布尔 —— 布尔会掩盖
  「动了第一步」（872 的教训）。
- 定位靠**量出来的坐标** + `elementFromPoint` 验落点，不按会变的文案找。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe876_clearfilter_kb.py
"""

import json

OUT = "/tmp/b876-src-clearfilter-kb.json"
LABEL = "性别"
PICK = "男"

FOCUS_JS = """() => { const a = document.activeElement;
  if (a === document.body) return {tag: 'BODY', aria: '(body)', text: ''};
  return {tag: a.tagName,
          aria: a.getAttribute('aria-label') || '',
          text: (a.innerText || '').trim().replace(/\\s+/g,' ').slice(0, 18),
          role: a.getAttribute('role') || ''}; }"""

# 清除钮的身份（**不看可见文案** —— 它文案是空的）
CLEAR_JS = """(label) => {
  const b = document.querySelector(`[aria-label="Clear ${label} filter"]`);
  if (!b) return null;
  const r = b.getBoundingClientRect();
  if (r.width <= 0 || r.height <= 0) return {hidden: true};
  return {rect: [Math.round(r.x), Math.round(r.y),
                 Math.round(r.width), Math.round(r.height)],
          xy: [Math.round(r.x + r.width / 2),
               Math.round(r.y + r.height / 2)],
          in_tab_order: b.tabIndex >= 0};
}"""

# 筛选芯片：按 aria 前缀，不按可见文案（选中后文案会变）
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
    # 插音频节点 + 选中
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

    def value_state():
        """当前选中值 —— 靠**复开层**读，不靠猜芯片文案。"""
        c = ev(CHIP_JS, LABEL)
        if not c:
            return None
        page.mouse.click(c["xy"][0], c["xy"][1])
        page.wait_for_timeout(700)
        o = ev(FILTER_JS, LABEL)
        if o:
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
        seld = [x["text"] for x in (o or []) if x.get("selected") == "true"]
        return seld[0] if seld else None

    def ensure_clear():
        """把「Clear 可见」这个前置态**建立起来**（每项各自调一次）。"""
        if not open_voices():
            return "音色库打不开"
        # 已经有值就不用再选
        c = ev(CHIP_JS, LABEL)
        if c and ev(CLEAR_JS, LABEL) and not ev(CLEAR_JS, LABEL).get("hidden"):
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

    steps = {}

    # ── ① Tab 能不能走到 Clear ─────────────────────────────────
    why = ensure_clear()
    if why:
        steps["tab"] = {"verdict": f"前置态没成立：{why}"}
    else:
        cl = ev(CLEAR_JS, LABEL)
        chip = ev(CHIP_JS, LABEL)
        page.mouse.click(chip["xy"][0], chip["xy"][1])   # 焦点从芯片起
        page.wait_for_timeout(400)
        rec = {"start": ev(FOCUS_JS), "clear_in_tab_order": cl["in_tab_order"],
               "traj": []}
        for _ in range(6):
            page.keyboard.press("Tab")
            page.wait_for_timeout(220)
            rec["traj"].append(ev(FOCUS_JS))
        rec["reached_clear"] = any(t["aria"] == f"Clear {LABEL} filter"
                                   for t in rec["traj"])
        steps["tab"] = rec
        print(f"\n① Tab 轨迹（起 {rec['start']['aria']!r}，"
              f"tabIndex={cl['in_tab_order']}）：")
        for i, t in enumerate(rec["traj"]):
            mark = " ←Clear" if t["aria"] == f"Clear {LABEL} filter" else ""
            print(f"   Tab{i+1}: {t['tag']}/{t['aria']!r} {t['text']!r}{mark}")
        print(f"   ⇒ 走到了：{rec['reached_clear']}")

    # ── ② Shift+Tab 反向 ──────────────────────────────────────
    why = ensure_clear()
    if why:
        steps["shift_tab"] = {"verdict": f"前置态没成立：{why}"}
    else:
        chip = ev(CHIP_JS, LABEL)
        page.mouse.click(chip["xy"][0], chip["xy"][1])
        page.wait_for_timeout(400)
        rec = {"start": ev(FOCUS_JS), "traj": []}
        for _ in range(4):
            page.keyboard.press("Shift+Tab")
            page.wait_for_timeout(220)
            rec["traj"].append(ev(FOCUS_JS))
        rec["reached_clear"] = any(t["aria"] == f"Clear {LABEL} filter"
                                   for t in rec["traj"])
        steps["shift_tab"] = rec
        print(f"\n② Shift+Tab 轨迹：")
        for i, t in enumerate(rec["traj"]):
            mark = " ←Clear" if t["aria"] == f"Clear {LABEL} filter" else ""
            print(f"   Shift+Tab{i+1}: {t['tag']}/{t['aria']!r} {mark}")

    # ── ③④ Enter / Space 键触发 ──────────────────────────────
    for name, key in (("enter", "Enter"), ("space", "Space")):
        why = ensure_clear()
        if why:
            steps[name] = {"verdict": f"前置态没成立：{why}"}
            continue
        before_val = value_state()
        cl = ev(CLEAR_JS, LABEL)
        hit = ev("""(xy) => {
          const t = document.elementFromPoint(xy[0], xy[1]);
          return t ? t.tagName + '/' + ((t.closest('[aria-label^="Clear "]')
                 || {}).getAttribute?.('aria-label') || '') : '';
        }""", cl["xy"])
        page.mouse.click(cl["xy"][0], cl["xy"][1])
        page.wait_for_timeout(400)
        rec = {"before_val": before_val,
               "focus": ev(FOCUS_JS), "hit_at_xy": hit}
        page.keyboard.press(key)
        page.wait_for_timeout(800)
        rec["clear_after"] = ev(CLEAR_JS, LABEL)
        rec["focus_after"] = ev(FOCUS_JS)
        rec["val_after"] = value_state()
        rec["fired"] = (not rec["clear_after"]) or (
            rec["val_after"] != before_val)
        steps[name] = rec
        print(f"\n{'③' if name=='enter' else '④'} 按 {key}："
              f"焦点在 {rec['focus']['aria']!r}；"
              f"值 {before_val!r} → {rec['val_after']!r}；"
              f"Clear 还在={bool(rec['clear_after'])}；"
              f"⇒ 触发了={rec['fired']}")

    # ── ⑤ 方向键 ──────────────────────────────────────────────
    why = ensure_clear()
    if why:
        steps["arrows"] = {"verdict": f"前置态没成立：{why}"}
    else:
        cl = ev(CLEAR_JS, LABEL)
        page.mouse.click(cl["xy"][0], cl["xy"][1])
        page.wait_for_timeout(400)
        rec = {"start": ev(FOCUS_JS), "traj": []}
        for k in ("ArrowDown", "ArrowRight", "ArrowUp", "ArrowLeft"):
            page.keyboard.press(k)
            page.wait_for_timeout(250)
            rec["traj"].append({"key": k, "focus": ev(FOCUS_JS)})
        rec["clear_after"] = ev(CLEAR_JS, LABEL)
        rec["moved"] = len({t["focus"]["aria"] for t in rec["traj"]}) > 1
        steps["arrows"] = rec
        print(f"\n⑤ Clear 上按方向键：")
        for t in rec["traj"]:
            print(f"   {t['key']:11s} → {t['focus']['tag']}/"
                  f"{t['focus']['aria']!r} {t['focus']['text']!r}")
        print(f"   ⇒ 焦点移动了={rec['moved']}；"
              f"Clear 还在={bool(rec['clear_after'])}")

    # ── ⑥ Esc ────────────────────────────────────────────────
    why = ensure_clear()
    if why:
        steps["esc"] = {"verdict": f"前置态没成立：{why}"}
    else:
        before_val = value_state()
        cl = ev(CLEAR_JS, LABEL)
        page.mouse.click(cl["xy"][0], cl["xy"][1])
        page.wait_for_timeout(400)
        rec = {"before_val": before_val, "focus": ev(FOCUS_JS)}
        page.keyboard.press("Escape")
        page.wait_for_timeout(900)
        rec["clear_after"] = ev(CLEAR_JS, LABEL)
        rec["focus_after"] = ev(FOCUS_JS)
        rec["voices_still_open"] = ev(VOICES_JS)
        rec["filter_layer_open"] = bool(ev(FILTER_JS, LABEL))
        rec["val_after"] = value_state() if ev(VOICES_JS) else "面板没了"
        rec["fired"] = (not rec["clear_after"]) or (
            rec["val_after"] != before_val)
        steps["esc"] = rec
        print(f"\n⑥ Clear 上按 Esc：值 {before_val!r} → "
              f"{rec['val_after']!r}；Clear 还在="
              f"{bool(rec['clear_after'])}；音色库还开着="
              f"{rec['voices_still_open']}；⇒ 触发了清除={rec['fired']}")

    out["steps"] = steps
    out["verdict"] = "sampled"

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n== 已写 {OUT} ==")
