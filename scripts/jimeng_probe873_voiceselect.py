#!/usr/bin/env python3
"""batch 873 源站探针：在音色筛选里**选完一个选项之后**会发生什么？

## 为什么补这一步

§870–872 把这一层从「无条件常驻 + 点不到 + 关不掉」一路修到与源站对齐，
测的全是**打开**这一侧：开层接管焦点 / 不困 Tab / 方向键移动 / Esc 收层。

**选完**呢？点「男」之后：
  · 筛选层会不会自己收起？
  · 那个筛选钮上的文案会不会从「性别」变成「男」？
  · 焦点落到哪儿（还在层里 / 回到钮上 / 掉到 body）？
  · 音色网格会不会跟着变（筛选生效）？

一条都没测过。**刚修好的一块，只测了一半，等于没测完。**

## 计费边界

只点「音频」入口、选中节点、开「音色」、点筛选钮、点选项。
**绝不**点生成/发送/购买/充值 —— 「音色」chip 本身也**不点**
（点了会真的去生成，属计费动作；这里只量「筛选」这一侧）。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe873_voiceselect.py
"""

import json

OUT = "/tmp/b873-src-voiceselect.json"
LABEL = "性别"
PICK = "男"          # 第 2 个选项（第 1 个是「全部 性别」，不测它）

IDENT_JS = """(label) => [...document.querySelectorAll('[role=listbox]')]
  .filter(e => (e.getAttribute('aria-label')||'') === label + ' options')
  .map(e => { const r = e.getBoundingClientRect();
    return {rect: [Math.round(r.x), Math.round(r.y),
                   Math.round(r.width), Math.round(r.height)],
            n_opts: e.querySelectorAll('[role=option]').length}; })"""

CHIP_JS = """(label) => {
  for (const b of document.querySelectorAll('button,[role=button]')) {
    const own = (b.innerText || '').trim();
    if (own === label || own.startsWith(label)) {
      const r = b.getBoundingClientRect();
      if (r.width < 20 || r.height < 10) continue;
      return {own, expanded: b.getAttribute('aria-expanded'),
              rect: [Math.round(r.x), Math.round(r.y),
                     Math.round(r.width), Math.round(r.height)]};
    }
  }
  return null;
}"""

VOICE_CHIPS_JS = """() => {
  // 音色网格：数一下可见的音色 chip（用最小祖先法，853b/854 同款思路）
  const all = [...document.querySelectorAll('*')].filter(e => {
    const t = (e.innerText || '').trim();
    return t.length > 0 && t.length < 12 && e.children.length === 0
           && e.getBoundingClientRect().width > 20;
  });
  return {n_small_text: all.length};
}"""

FOCUS_JS = """() => {
  const a = document.activeElement;
  if (!a || a === document.body) return 'body';
  return a.tagName + '/' + ((a.getAttribute('aria-label') || a.innerText || '')
          .trim().slice(0, 16));
}"""

SELECTED_JS = """(label) => {
  const l = [...document.querySelectorAll('[role=listbox]')]
    .find(e => (e.getAttribute('aria-label')||'') === label + ' options');
  if (!l) return null;
  return [...l.querySelectorAll('[role=option]')].map(o => ({
    text: (o.innerText || '').trim(),
    selected: o.getAttribute('aria-selected'),
  }));
}"""


def ensure_voices():
    if page.get_by_text("全音色", exact=True).count():
        return True
    vt = page.locator('button[aria-label^="音色"]')
    if not vt.count():
        return False
    vt.first.click(timeout=8000)
    page.wait_for_timeout(1000)
    return bool(page.get_by_text("全音色", exact=True).count())


def ensure_filter(label):
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


out = {}
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

    rec = {"label": LABEL, "pick": PICK}
    if not ensure_filter(LABEL):
        rec["verdict"] = "BLOCKED_BY_FIXTURE（打不开筛选层）"
        print("⚠ " + rec["verdict"])
    else:
        # ── 选之前的三张快照 ────────────────────────────────────────
        rec["before"] = {
            "layer": page.evaluate(IDENT_JS, LABEL),
            "chip": page.evaluate(CHIP_JS, LABEL),
            "focus": page.evaluate(FOCUS_JS),
            "options": page.evaluate(SELECTED_JS, LABEL),
        }
        print(f"选之前：chip={rec['before']['chip']}")
        print(f"        options={rec['before']['options']}")

        # ⚠️ 先验落点再点（843 的教训）
        opt = page.get_by_text(PICK, exact=True).first
        n_opt = opt.count()
        rec["option_count"] = n_opt
        hit = None
        if n_opt:
            bb = opt.bounding_box()
            if bb:
                cx, cy = bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2
                hit = page.evaluate(
                    "([x,y])=>{const e=document.elementFromPoint(x,y);"
                    "return e?e.tagName+'/'+((e.innerText||'').trim().slice(0,10))"
                    "+'/role='+(e.getAttribute('role')||''):null;}", [cx, cy])
        rec["hit"] = hit
        print(f"选项「{PICK}」计数={n_opt} 落点={hit}")
        if not n_opt:
            rec["verdict"] = "BLOCKED_BY_FIXTURE（选项不在 DOM 里）"
        else:
            opt.click(timeout=8000)
            page.wait_for_timeout(1000)
            # ── 选之后 ─────────────────────────────────────────────
            rec["after"] = {
                "layer": page.evaluate(IDENT_JS, LABEL),
                "chip": page.evaluate(CHIP_JS, LABEL),
                "focus": page.evaluate(FOCUS_JS),
                "voices": page.evaluate(VOICE_CHIPS_JS),
            }
            rec["closes_itself"] = not rec["after"]["layer"]
            rec["chip_text_before"] = (rec["before"]["chip"] or {}).get("own")
            rec["chip_text_after"] = (rec["after"]["chip"] or {}).get("own")
            rec["chip_text_changed"] = (rec["chip_text_before"]
                                        != rec["chip_text_after"])
            rec["chip_expanded_after"] = (rec["after"]["chip"] or {}).get(
                "expanded")
            print(f"选之后：层还在？{bool(rec['after']['layer'])}"
                  f" ⇒ 自己收起={rec['closes_itself']}")
            print(f"        chip 文案 {rec['chip_text_before']!r} → "
                  f"{rec['chip_text_after']!r}（变了={rec['chip_text_changed']}）"
                  f" aria-expanded={rec['chip_expanded_after']!r}")
            print(f"        焦点 → {rec['after']['focus']!r}")
            rec["verdict"] = "sampled"
    out.update(rec)

    # ── 第二个选项：选「全部 性别」**也**收不收？─────────────────────
    # ⚠️ 第一版只量了「男」。复刻那边两条路径走**同一个 onClick**，
    #    「同一个回调 ⇒ 行为一样」是**推测**不是取样（§92 刚为此栽过：
    #    「同一个组件的四个实例」也是这么被信了的）。所以两条都量。
    if rec.get("verdict") == "sampled":
        # ⚠️⚠️ 按**文字**找芯片这条路已经废了：选完「男」之后芯片文案变成
        #   「男」，`get_by_text("性别")` 数不到 ⇒ `ensure_filter` 直接返回
        #   False ⇒ 第二轮两项全记成「前置态没成立」。
        #   这是「查错对象 → 把够不着写成没有」的**第五次**（§87 顺序、
        #   §88 作用域、871 层中途被关、872 ensure_voices 判错、这一处）。
        #   改用**开层时记下的芯片坐标**重新点回去 —— 坐标是**量出来的**，
        #   不依赖它此刻叫什么名字；点之前照例**验落点**（843）。
        _rect = (rec.get("before", {}).get("chip") or {}).get("rect")
        rec["chip_rect_reused"] = _rect
        for pick in ["全部 性别", "男"]:
            hit2 = None
            if _rect and page.evaluate(IDENT_JS, LABEL) == []:
                if not ensure_voices():
                    rec.setdefault("second_round", {})[pick] = {
                        "why": "音色库打不开（前置态没成立）"}
                    continue
                cx = _rect[0] + _rect[2] / 2
                cy = _rect[1] + _rect[3] / 2
                hit2 = page.evaluate(
                    "([x,y])=>{const e=document.elementFromPoint(x,y);"
                    "if(!e)return null;const b=e.closest('button,[role=button]');"
                    "return b?b.tagName+'/'+((b.innerText||'').trim().slice(0,10))"
                    ":e.tagName+'(不是按钮)';}", [cx, cy])
                rec.setdefault("chip_hits", {})[pick] = hit2
                if not hit2 or hit2.endswith("(不是按钮)"):
                    rec.setdefault("second_round", {})[pick] = {
                        "why": f"芯片坐标落点={hit2}（不是按钮 ⇒ 前置态没成立）"}
                    continue
                page.mouse.click(cx, cy)
                page.wait_for_timeout(800)
            if not ensure_filter(LABEL):
                rec.setdefault("second_round", {})[pick] = {
                    "why": "打不开筛选层（前置态没成立）"}
                continue
            o = page.get_by_text(pick, exact=True).first
            if not o.count():
                rec.setdefault("second_round", {})[pick] = {
                    "why": "选项不在 DOM 里"}
                continue
            o.click(timeout=8000)
            page.wait_for_timeout(900)
            rec.setdefault("second_round", {})[pick] = {
                "closes_itself": not page.evaluate(IDENT_JS, LABEL),
                "focus": page.evaluate(FOCUS_JS),
            }
            print(f"  选「{pick}」→ 自己收起="
                  f"{rec['second_round'][pick]['closes_itself']} 焦点→"
                  f"{rec['second_round'][pick]['focus']!r}")
        sr = rec.get("second_round", {})
        if all(isinstance(v, dict) and "closes_itself" in v
               for v in sr.values()):
            same = len({v["closes_itself"] for v in sr.values()}) == 1
            print("== 两个选项的收起行为一致：", same,
                  {k: v["closes_itself"] for k, v in sr.items()})
        else:
            print("== 有一项没量到（不合并成结论）")

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n== 已写 {OUT} ==")
print(f"== 结论：{out.get('verdict')} ==")
