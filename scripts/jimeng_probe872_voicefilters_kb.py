#!/usr/bin/env python3
"""batch 872 源站探针：音色库**四个筛选钮逐个**取键盘样。

## 为什么不能只测一个

§89 明确记了一条范围限制：源站**只取了「性别」**一个筛选钮，另外三个
（年龄 / 语言 / 声音特点）**没逐个取** —— 「它们是同一个组件的四个实例」
这句话是**推测**，不是取样。

同一个组件 ≠ 行为一定一样：选项数不同（3 / 6 / 4 / 6）、文案长度不同、
面板高度不同（源站实测「性别」161×124、「声音特点」就该更高），
**Tab 序列的位置**也不同（它在 chip 群里的第几个，决定了 Tab 要走多远）。
所以必须**逐个**量。

## 每项测量的前置态**各自**建立（871 的血泪）

871 第二版栽在：② 连按 40 次 Tab 的途中层**已经被关掉**，于是 ③ 读到
「层不存在」、④ 读到「层=False」、⑤ 的「收层=True」是因为它本来就关着。
三项**全是无效测量**，而它们长得跟真结论一模一样。

本探针因此把「打开某个筛选层」做成一个**带验证**的动作：
`ensure_filter(label)` 返回**它真的确认层开着**才继续；每项测量前都调它。

## 计费边界

只点「音频」入口、选中节点、开「音色」、点四个筛选钮。
**绝不**点生成/发送/购买/充值。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe872_voicefilters_kb.py
"""

import json

OUT = "/tmp/b872-src-voicefilters-kb.json"
LABELS = ["性别", "年龄", "语言", "声音特点"]
MAX_WALK = 40      # ② 上限。⚠️ 上限不够 ≠ 进不去（775），必须带 capped
MAX_TRAPS = 6      # ③

IDENT_JS = """(label) => {
  const out = [];
  for (const e of document.querySelectorAll('[role=listbox],[role=menu],[role=dialog]')) {
    const r = e.getBoundingClientRect();
    if (r.width < 60 || r.height < 40) continue;
    const al = e.getAttribute('aria-label') || '';
    if (al !== label + ' options') continue;
    out.push({aria: al, role: e.getAttribute('role'),
              rect: [Math.round(r.x), Math.round(r.y),
                     Math.round(r.width), Math.round(r.height)],
              n_opts: e.querySelectorAll('[role=option]').length,
              txt: (e.innerText || '').trim().slice(0, 60)});
  }
  return out;
}"""

FOCUS_IN_JS = """(label) => {
  const a = document.activeElement;
  if (!a || a === document.body) return {inside: false, at: 'body'};
  const layer = a.closest('[role=listbox],[role=menu],[role=dialog]');
  const want = label + ' options';
  const opts = layer ? layer.querySelectorAll('[role=option]') : null;
  return {inside: !!(layer && (layer.getAttribute('aria-label')||'') === want),
          at: a.tagName + '/' + (a.getAttribute('role') || '')
              + '/' + (a.innerText || '').trim().slice(0, 12),
          layer_aria: layer ? (layer.getAttribute('aria-label') || '') : '',
          idx: opts ? [...opts].indexOf(a) : -1,
          n_opts: opts ? opts.length : 0};
}"""


def ensure_voices():
    """音色库本体开着吗？不开就（重选节点 →）点开它，并**验证**开成了。

    ⚠️⚠️ 第一版拿 `page.locator('[role=listbox]').count()` 当「音色库开着」
    的判据 —— **错**：筛选层自己也是 `role=listbox`，于是「筛选层还开着」
    被读成「音色库开着」，直接 return True，后面去 `get_by_text("年龄")`
    找芯片时当然找不到 ⇒ 记成 BLOCKED_BY_FIXTURE。
    **一个判据查错了对象，就会把「我没够着」写成「它没有」** ——
    872 第一版四个里有两个就这样丢了。
    改成只认音色库**自己的标题**「全音色」。
    """
    if page.get_by_text("全音色", exact=True).count():
        return True
    vt = page.locator('button[aria-label^="音色"]')
    if not vt.count():
        return False
    vt.first.click(timeout=8000)
    page.wait_for_timeout(1000)
    if page.get_by_text("全音色", exact=True).count():
        return True
    # 兜底：重选一次节点再试（Tab 途中可能把选中态也弄掉了）
    if out.get("audio_node"):
        pt = page.evaluate("""(tid) => {
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
        }""", out["audio_node"])
        if pt:
            page.mouse.click(pt[0], pt[1])
            page.wait_for_timeout(900)
            if page.locator('button[aria-label^="音色"]').count():
                page.locator('button[aria-label^="音色"]').first.click(
                    timeout=8000)
                page.wait_for_timeout(1000)
                return bool(page.get_by_text("全音色", exact=True).count())
    return False


def ensure_filter(label):
    """把 `label` 那个筛选层开出来，并确认它**真的开着**。

    ⚠️ 先确认音色库本体开着 —— 否则筛选钮根本不在 DOM 里，
    「点不到」会被记成「入口没有」（§87 顺序写反那次的教训）。
    """
    if page.evaluate(IDENT_JS, label):
        return True
    if not ensure_voices():
        return False
    chip = page.get_by_text(label, exact=True).first
    if not chip.count():
        return False
    chip.click(timeout=8000)
    page.wait_for_timeout(800)
    return bool(page.evaluate(IDENT_JS, label))


def close_filter(label):
    """把这个筛选层收掉（Esc）。收不掉就点芯片钮。"""
    if not page.evaluate(IDENT_JS, label):
        return
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)
    if page.evaluate(IDENT_JS, label):
        chip = page.get_by_text(label, exact=True).first
        if chip.count():
            chip.click(timeout=6000)
            page.wait_for_timeout(500)


out = {"labels": {}}
page.goto(
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create",
    wait_until="domcontentloaded", timeout=90000)
page.wait_for_timeout(10000)
page.set_viewport_size({"width": 1512, "height": 1200})
page.wait_for_timeout(2500)
out["logged_in"] = page.locator('button[aria-label="音频"]').count() > 0
print(f"== 登录态/画布：{out['logged_in']} ==")

if not out["logged_in"]:
    out["verdict"] = "BLOCKED_BY_FIXTURE（登录态没了）"
    print("!! " + out["verdict"])
else:
    tid = None
    for cand in ('button[aria-label="音频"]', 'button:has-text("音频")'):
        loc = page.locator(cand)
        if not loc.count():
            continue
        before = set(page.evaluate(
            "() => [...document.querySelectorAll('.react-flow__node')]"
            ".map(n => n.getAttribute('data-testid')||'')"))
        loc.first.click(timeout=10000)
        page.wait_for_timeout(2500)
        after = page.evaluate(
            "() => [...document.querySelectorAll('.react-flow__node')]"
            ".map(n => n.getAttribute('data-testid')||'')")
        new = [t for t in after if t and t not in before]
        if new:
            tid = new[0]
            break
    out["audio_node"] = tid
    print(f"== 音频节点 {tid} ==")
    pt = None
    if tid:
        pt = page.evaluate("""(tid) => {
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

    for label in LABELS:
        rec = {"label": label}
        print(f"\n===== {label} =====")
        # ① 开层焦点
        if not ensure_filter(label):
            rec["verdict"] = "BLOCKED_BY_FIXTURE（打不开这个筛选层）"
            print("  ⚠ " + rec["verdict"])
            out["labels"][label] = rec
            continue
        rec["layer"] = page.evaluate(IDENT_JS, label)
        rec["at_open"] = page.evaluate(FOCUS_IN_JS, label)
        print(f"① 层 {rec['layer']}")
        print(f"① 开层焦点 {rec['at_open']}")

        # ② walk
        page.evaluate("() => { if (document.activeElement "
                      "&& document.activeElement.blur) "
                      "document.activeElement.blur(); }")
        page.wait_for_timeout(300)
        steps = None
        tail = []
        for i in range(1, MAX_WALK + 1):
            page.keyboard.press("Tab")
            page.wait_for_timeout(130)
            f = page.evaluate(FOCUS_IN_JS, label)
            tail.append({"n": i, "inside": f.get("inside"), "at": f.get("at")})
            if f.get("inside"):
                steps = i
                break
        rec["walk_steps"] = steps
        rec["walk_capped"] = steps is None
        print(f"② Tab：{steps} 次（capped={rec['walk_capped']}）"
              f" 末尾轨迹 {tail[-2:]}")

        # ③ traps（前置态：层开着 + 焦点在层内）
        ok3 = ensure_filter(label)
        rec["pre_traps_layer_open"] = ok3
        if ok3:
            page.evaluate("""(label) => {
              const l = [...document.querySelectorAll('[role=listbox]')]
                .find(e => (e.getAttribute('aria-label')||'') === label + ' options');
              const o = l && l.querySelector('[role=option]');
              if (o && o.focus) o.focus();
            }""", label)
            page.wait_for_timeout(250)
        pre3 = page.evaluate(FOCUS_IN_JS, label) if ok3 else {"inside": False}
        rec["pre_traps_inside"] = pre3.get("inside")
        if not rec["pre_traps_inside"]:
            rec["traps_escape_at"] = None
            rec["traps_why"] = "前置态没成立 —— **不是**「层内不困」"
        else:
            esc_at = None
            for i in range(1, MAX_TRAPS + 1):
                page.keyboard.press("Tab")
                page.wait_for_timeout(140)
                f = page.evaluate(FOCUS_IN_JS, label)
                if not f.get("inside"):
                    esc_at = i
                    break
            rec["traps_escape_at"] = esc_at
        print(f"③ 层内 Tab 逃出于第 {rec['traps_escape_at']} 次"
              f"（前置 {rec['pre_traps_inside']}）")

        # ④ 方向键（前置态：层开着 + 焦点在第 0 项）
        ok4 = ensure_filter(label)
        rec["reopen_for_arrows"] = ok4
        if ok4:
            page.evaluate("""(label) => {
              const l = [...document.querySelectorAll('[role=listbox]')]
                .find(e => (e.getAttribute('aria-label')||'') === label + ' options');
              const o = l && l.querySelector('[role=option]');
              if (o && o.focus) o.focus();
            }""", label)
            page.wait_for_timeout(250)
        b4 = page.evaluate(FOCUS_IN_JS, label) if ok4 else {"idx": -1}
        if b4.get("idx") == 0:
            page.keyboard.press("ArrowDown")
            page.wait_for_timeout(200)
            a1 = page.evaluate(FOCUS_IN_JS, label)
            page.keyboard.press("ArrowDown")
            page.wait_for_timeout(200)
            a2 = page.evaluate(FOCUS_IN_JS, label)
            rec["arrows_idx"] = [b4.get("idx"), a1.get("idx"), a2.get("idx")]
            rec["arrows_move"] = (a1.get("idx") != b4.get("idx")
                                  or a2.get("idx") != a1.get("idx"))
        else:
            rec["arrows_idx"] = None
            rec["arrows_move"] = None
            rec["arrows_why"] = (f"前置态没成立（idx={b4.get('idx')}）—— "
                                 f"**不是**「方向键不动」")
        print(f"④ 方向键 {rec.get('arrows_idx')} move={rec.get('arrows_move')}")

        # ⑤ Esc（前置态：层开着）
        ok5 = ensure_filter(label)
        rec["pre_esc_open"] = ok5
        page.keyboard.press("Escape")
        page.wait_for_timeout(600)
        rec["esc_closes"] = not page.evaluate(IDENT_JS, label) if ok5 else None
        rec["esc_focus_to"] = page.evaluate("""() => {
          const a = document.activeElement;
          if (!a || a === document.body) return 'body';
          return a.tagName + '/' + ((a.getAttribute('aria-label')
                  || a.innerText || '').trim().slice(0, 16));
        }""")
        print(f"⑤ Esc 收层={rec['esc_closes']} 焦点→{rec['esc_focus_to']!r}")
        rec["verdict"] = "sampled"
        out["labels"][label] = rec
        close_filter(label)

    # 四个都取到了吗？
    out["verdict"] = "sampled"
    out["all_sampled"] = all(
        (out["labels"].get(l) or {}).get("verdict") == "sampled"
        for l in LABELS)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n== 已写 {OUT} ==")
print(f"== 四个都取到样：{out.get('all_sampled')} ==")
