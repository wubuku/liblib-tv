#!/usr/bin/env python3
"""batch 871 源站探针：音色库的**筛选下拉**（`性别 options`）键盘行为。

## 为什么取这个

批 870 刚把这一层修好（展开方向、几何、`aria-label` 全部按源站实测对齐），
但**只对齐了版式**。键盘行为源站**一概没取**：

  · 复刻侧现在 `focus_at_open=False`（开层**不**接管焦点）；
  · 源站是不是也这样 —— **不知道**。

不许拿「源站大概也这样」把这一块糊过去（847）。所以本批去取样。

## 量的东西（每项**独立**，不许用一项证明另一项）

  ① `at_open_inside` —— 开层**那一刻**焦点在不在层内
  ② `walk`         —— 从头按 Tab，几次能进得去
  ③ `traps`        —— 已经在层里，连按 Tab 会不会跑出去
  ④ `arrows_move`  —— 层内按方向键，焦点/选中会不会动
  ⑤ `esc_closes` / `esc_to` —— Esc 收不收层、焦点回不回到那个筛选钮

②③ 必须分开（861 的教训：曾用 `fill()` 的实验当焦点证据）。
④ 的 False 要分清是「源站方向键坏了」还是「无处可去」（内容只有 3 项时
可能只动一下就到底 —— 轨迹要留着，别只留结论）。

## 计费边界

只点「音频」入口、选中节点、开「音色」、点「性别」。**绝不**点生成/发送/购买。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe871_voicefilter_kb.py
"""

import json

OUT = "/tmp/b871-src-voicefilter-kb.json"
MAX_WALK = 40      # ② 最多按几次 Tab（871 第一版 12 次不够，见下）
MAX_TRAPS = 6      # ③ 已经在层里，最多连按几次

# 层身份：**用批 870 量到的源站事实**指认，不按类名（源站 class 与复刻无关，
# 853a 吃过一次亏 —— 按类名找抓到的是整页容器）。
IDENT_JS = """() => {
  const out = [];
  for (const e of document.querySelectorAll('[role=listbox],[role=menu],[role=dialog]')) {
    const r = e.getBoundingClientRect();
    if (r.width < 60 || r.height < 40) continue;
    const al = e.getAttribute('aria-label') || '';
    if (!al.includes('options')) continue;
    out.push({aria: al, role: e.getAttribute('role'),
              rect: [Math.round(r.x), Math.round(r.y),
                     Math.round(r.width), Math.round(r.height)],
              n_opts: e.querySelectorAll('[role=option]').length,
              txt: (e.innerText || '').trim().slice(0, 40)});
  }
  return out;
}"""

# 焦点现在在不在某个 aria 含 options 的层内
FOCUS_IN_JS = """() => {
  const a = document.activeElement;
  if (!a || a === document.body) return {inside: false, at: 'body'};
  const layer = a.closest('[role=listbox],[role=menu],[role=dialog]');
  const opts = layer ? layer.querySelectorAll('[role=option]') : null;
  return {inside: !!(layer && (layer.getAttribute('aria-label')||'').includes('options')),
          at: a.tagName + '/' + (a.getAttribute('role') || '')
              + '/' + (a.innerText || '').trim().slice(0, 12),
          in_any_layer: !!layer,
          layer_aria: layer ? (layer.getAttribute('aria-label') || '') : '',
          idx: opts ? [...opts].indexOf(a) : -1,
          n_opts: opts ? opts.length : 0};
}"""


def reopen_filter():
    """把筛选层**重新开出来**，并确认它真开着。

    ⚠️⚠️ 871 第二版栽在这里：② 连按 40 次 Tab 的途中，筛选层**已经被关掉了**
    （Tab 走到音色库的 chip 上，blur 收起下拉），于是 ③ 的 `find()` 返回
    undefined、④ 报「层=False」、⑤ 的「收层=True」也是**因为它本来就关着**。
    三项**全是无效测量**，而它们长得跟真结论一模一样。
    ⇒ 每一项测量都要**自己**建立前置态，并且**先验证前置态成立**再动手。
    """
    if page.evaluate(IDENT_JS):
        return True
    chip = page.get_by_text("性别", exact=True).first
    if not chip.count():
        return False
    chip.click(timeout=8000)
    page.wait_for_timeout(800)
    return bool(page.evaluate(IDENT_JS))


out = {}
page.goto(
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create",
    wait_until="domcontentloaded", timeout=90000)
page.wait_for_timeout(10000)
page.set_viewport_size({"width": 1512, "height": 1200})
page.wait_for_timeout(2500)
out["url"] = page.url
out["logged_in"] = page.locator('button[aria-label="音频"]').count() > 0
print(f"== 登录态/画布：{out['logged_in']} ==")

if not out["logged_in"]:
    out["verdict"] = "BLOCKED_BY_FIXTURE（登录态没了）"
    print("!! " + out["verdict"])
else:
    # 插音频节点 → 选中
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

    # 开音色库 → 点「性别」
    chip_ok = False
    vt = page.locator('button[aria-label^="音色"]')
    out["voice_trigger_n"] = vt.count()
    if vt.count():
        vt.first.click(timeout=8000)
        page.wait_for_timeout(1000)
        out["layers_after_voices"] = page.evaluate(IDENT_JS)
        chip = page.get_by_text("性别", exact=True).first
        if chip.count():
            chip.click(timeout=8000)
            page.wait_for_timeout(900)
            chip_ok = True
    out["filter_open"] = chip_ok
    out["layer"] = page.evaluate(IDENT_JS)
    print(f"== 筛选层 {out['layer']} ==")
    if not out["layer"]:
        out["verdict"] = "no_filter_layer（没打开筛选层）"
    else:
        # ① 开层即焦点
        out["at_open"] = page.evaluate(FOCUS_IN_JS)
        print(f"① 开层焦点：{out['at_open']}")

        # ② walk：Tab 能不能进得去
        #    ⚠️⚠️ 871 第一版把焦点 blur 回 body、然后从页面开头按 12 次 Tab，
        #    结果 12 次全走在**音色库本体的 chip** 上（年龄/语言/…/桃花庵主），
        #    `walk_steps=None`。**那不是「Tab 进不去」** —— 轨迹明摆着
        #    Tab 序列**压根没经过**筛选层（它在 chip 群之后）。上限不够 ≠ 进不去
        #    （775 早就记过这条）。所以：上限调大，并且**如实带出 capped 标记**。
        page.evaluate("() => { if (document.activeElement "
                      "&& document.activeElement.blur) "
                      "document.activeElement.blur(); }")
        page.wait_for_timeout(300)
        walk = []
        for i in range(1, MAX_WALK + 1):
            page.keyboard.press("Tab")
            page.wait_for_timeout(140)
            f = page.evaluate(FOCUS_IN_JS)
            walk.append({"n": i, "inside": f.get("inside"), "at": f.get("at")})
            if f.get("inside"):
                break
        out["walk"] = walk
        out["walk_steps"] = next((w["n"] for w in walk if w["inside"]), None)
        out["walk_capped"] = out["walk_steps"] is None
        print(f"② 从零 Tab：{out['walk_steps']} 次进得去"
              f"（上限 {MAX_WALK}，capped={out['walk_capped']}）")
        for w in walk[-6:]:
            print(f"     {w['n']:>2} inside={w['inside']} at={w['at']!r}")

        # ③ traps：**先把焦点放进层内**，再连按 Tab。
        #    ⚠️ 第一版没做这一步 —— ② 结束时焦点在某个 chip 上（不在层内），
        #    于是 ③ 量的其实是「从层外按 Tab 会去哪」，**不是**「层内困不困」。
        #    那种数字记进基线表就是拿无效测量当证据。
        out["reopen_for_traps"] = reopen_filter()
        print(f"③ 重开筛选层：{out['reopen_for_traps']}")
        out["pre_traps_inside"] = page.evaluate(FOCUS_IN_JS).get("inside")
        if not out["pre_traps_inside"]:
            page.evaluate("""() => {
              const l = [...document.querySelectorAll('[role=listbox]')]
                .find(e => (e.getAttribute('aria-label')||'').includes('options'));
              const o = l && l.querySelector('[role=option]');
              if (o && o.focus) o.focus();
            }""")
            page.wait_for_timeout(250)
            out["pre_traps_inside"] = page.evaluate(FOCUS_IN_JS).get("inside")
        print(f"③ 前置：焦点已在层内 = {out['pre_traps_inside']}")
        if not out["pre_traps_inside"]:
            out["traps"] = None
            out["traps_escape_at"] = None
            out["traps_why"] = "前置态没成立（焦点**进不去**层内）—— "\
                               "**不是**「层内不困」"
            print("   ⚠ " + out["traps_why"])
        else:
            traps = []
            for i in range(1, MAX_TRAPS + 1):
                page.keyboard.press("Tab")
                page.wait_for_timeout(150)
                f = page.evaluate(FOCUS_IN_JS)
                traps.append({"n": i, "inside": f.get("inside"),
                              "at": f.get("at")})
            out["traps"] = traps
            out["traps_escape_at"] = next(
                (t["n"] for t in traps if not t["inside"]), None)
            print(f"③ 层内连按 Tab：第 {out['traps_escape_at']} 次逃出"
                  f"（None = {MAX_TRAPS} 次都没逃）")
            for t in traps:
                print(f"     {t['n']:>2} inside={t['inside']} at={t['at']!r}")

        # ④ 方向键：**先确认焦点真在选项上**再按。
        #    ⚠️ 第一版直接 `.focus()` 完就按，读回来 `idx=-1, n_opts=0`
        #    —— 那说明**压根没找着那个层**（`find()` 拿到 undefined 就静默
        #    return 了）。把这种数字写成「源站方向键不动」就是拿无效测量当结论。
        out["reopen_for_arrows"] = reopen_filter()
        print(f"④ 重开筛选层：{out['reopen_for_arrows']}")
        out["pre_arrows"] = page.evaluate("""() => {
          const l = [...document.querySelectorAll('[role=listbox]')]
            .find(e => (e.getAttribute('aria-label')||'').includes('options'));
          if (!l) return {found: false};
          const o = l.querySelector('[role=option]');
          if (!o) return {found: true, n_opts: 0};
          o.focus();
          return {found: true, n_opts: l.querySelectorAll('[role=option]').length};
        }""")
        page.wait_for_timeout(250)
        before_arrow = page.evaluate(FOCUS_IN_JS)
        if not (out["pre_arrows"].get("found")
                and before_arrow.get("idx") == 0):
            out["arrows"] = None
            out["arrows_move"] = None
            out["arrows_why"] = (
                f"前置态没成立（层={out['pre_arrows'].get('found')}，"
                f"焦点 idx={before_arrow.get('idx')}）—— **不是**「方向键不动」")
            print(f"④ ⚠ {out['arrows_why']}")
        else:
            page.keyboard.press("ArrowDown")
            page.wait_for_timeout(220)
            after_arrow = page.evaluate(FOCUS_IN_JS)
            page.keyboard.press("ArrowDown")
            page.wait_for_timeout(220)
            after_arrow2 = page.evaluate(FOCUS_IN_JS)
            out["arrows"] = {"before": before_arrow, "after1": after_arrow,
                             "after2": after_arrow2}
            out["arrows_move"] = (
                after_arrow.get("idx") != before_arrow.get("idx")
                or after_arrow2.get("idx") != after_arrow.get("idx"))
            print(f"④ 方向键：idx {before_arrow.get('idx')} → "
                  f"{after_arrow.get('idx')} → {after_arrow2.get('idx')}"
                  f"（n_opts={before_arrow.get('n_opts')}）")

        # ⑤ Esc —— ⚠️ 同样要先确认层**开着**，「按 Esc 之后没了」才说明
        #    是 Esc 收的；层本来就关着的话，这一步是**恒真**的。
        out["reopen_for_esc"] = reopen_filter()
        out["esc_layer_open_before"] = bool(page.evaluate(IDENT_JS))
        print(f"⑤ 重开筛选层：{out['reopen_for_esc']}，"
              f"按 Esc 前层开着 = {out['esc_layer_open_before']}")
        page.keyboard.press("Escape")
        page.wait_for_timeout(700)
        out["esc_closes"] = not page.evaluate(IDENT_JS)
        out["esc_focus_to"] = page.evaluate("""() => {
          const a = document.activeElement;
          if (!a || a === document.body) return 'body';
          return a.tagName + '/' + (a.getAttribute('aria-label') || a.innerText || '')
                 .trim().slice(0, 16);
        }""")
        print(f"⑤ Esc：收层={out['esc_closes']} 焦点落到 "
              f"{out['esc_focus_to']!r}")
        out["verdict"] = "sampled"

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n== 已写 {OUT} ==")
print(f"== 结论：{out.get('verdict')} ==")
