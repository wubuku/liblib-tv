#!/usr/bin/env python3
"""batch 875 源站探针：那个 16×16 的「Clear 性别 filter」到底是什么。

## 从哪冒出来的

批 874 倒焦点元素身份时，撞见同页**第二个**提到「性别」的按钮：
`aria="Clear 性别 filter"`，16×16 @ [788, 662]，就贴在芯片右边 8px。
复刻没有这个东西。但**它什么时候在**还不知道 —— 可能一直常驻（像 869
挖出的音音色库筛选面板那样 4 个无条件常驻），也可能是**选完之后才冒出来**。

两种猜法对应完全相反的修法：
- 一直常驻 ⇒ 复刻少了 4 个常驻控件，真缺陷；
- 选完才出现 ⇒ 那是「清除这一个筛选」的按钮，复刻缺的是**功能**。

所以先量「它在不在」，再量「点了会怎样」。

## 三段取样，每段各自建立并验证前置态

1. 刚开音色库、什么都没选 → header 里有哪些按钮
2. 选「男」→ 再列一次
3. 点那个 Clear → 再列一次 + 芯片文案 + 焦点落在谁身上

再逐个确认**四个**筛选钮都长这样（不能只凭性别外推，§「同类」）。

## 计费边界

只点「音频」入口、选中节点、开「音色」、点筛选钮、点选项、点 Clear、按 Esc。
**绝不**点生成/发送/购买/充值，**也绝不**点音色 chip 本身（Clear 不是 chip）。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe875_clearfilter.py
"""

import json

OUT = "/tmp/b875-src-clearfilter.json"
# 逐个走，不外推（871/872 的教训：抽样要抽样，别拿一个代表四个）
#
# ⚠️⚠️ 第一跑这四个「选哪个」是我**照着筛选名猜**的，错了两个：
#   `中文` 在语言层里**不存在**（真实选项是 普通话/中文方言/英文），
#   `温柔` 在声音特点层里也**不存在**（真实选项是 适合旁白/情景演绎/…）。
# 探针把「选项名猜错」和「源站没有这个选项」分得清清楚楚 —— 层开得好好的，
# 只是 `get_by_text` 数到 0。**这就是不能按「同类」推测判缺陷**（§69）：
# 性别有 Clear，不等于另外三个不用量。
# 这次用的是**层里读到的真名**。
CASES = [
    ("性别", "男", "全部 性别"),
    ("年龄", "青年", "全部 年龄"),
    ("语言", "普通话", "全部 语言"),
    ("声音特点", "适合旁白", "全部 声音特点"),
]

# 选完之后那一行**变形了**（153×28 → 111×26，x 也挪了 9），
# 说明 Clear 未必是「挤在芯片右边」那么简单。整行元素连 rect 一起倒出来。
ROW_JS = """(label) => {
  const hs = [...document.querySelectorAll('header')]
    .filter(h => /filter|音色|catalog/i.test(h.className || ''));
  const h = hs[0];
  if (!h) return null;
  const walk = (root, depth) => {
    const out = [];
    for (const e of root.children) {
      const r = e.getBoundingClientRect();
      out.push({d: depth,
        tag: e.tagName,
        cls: ((e.className || '') + '').slice(0, 60),
        aria: e.getAttribute('aria-label') || '',
        text: (e.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 24),
        rect: [Math.round(r.x), Math.round(r.y),
               Math.round(r.width), Math.round(r.height)]});
      if (depth < 2) out.push(...walk(e, depth + 1));
    }
    return out;
  };
  return walk(h, 0);
}"""

# 音色库 header 里的**所有**按钮，不按尺寸过滤 —— Clear 只有 16×16，
# 按尺寸筛会把它当噪声丢掉（869 挖面板时就是这么找到 4 个无条件常驻的）
HEADER_JS = """(label) => {
  const hs = [...document.querySelectorAll('header')]
    .filter(h => /filter|音色|catalog/i.test(h.className || ''));
  const h = hs[0];
  if (!h) return {n_header: 0, btns: []};
  return {n_header: hs.length,
    header_class: (h.className || ''),
    btns: [...h.querySelectorAll('button,[role=button]')].map(b => {
      const r = b.getBoundingClientRect();
      return {aria: b.getAttribute('aria-label') || '',
              text: (b.innerText || '').trim().slice(0, 16),
              expanded: b.getAttribute('aria-expanded'),
              rect: [Math.round(r.x), Math.round(r.y),
                     Math.round(r.width), Math.round(r.height)]};
    }).filter(x => x.rect[2] > 0 && x.rect[3] > 0)};
}"""

# 找到某个筛选钮的芯片坐标：从 header 里认 aria/text 命中该 label 的那个
CHIP_JS = """(label) => {
  const hs = [...document.querySelectorAll('header')]
    .filter(h => /filter|音色|catalog/i.test(h.className || ''));
  const h = hs[0];
  if (!h) return null;
  for (const b of h.querySelectorAll('button,[role=button]')) {
    const aria = b.getAttribute('aria-label') || '';
    const t = (b.innerText || '').trim();
    // 「性别: 男」「年龄」都算这个筛选钮的芯片；「Clear 性别 filter」不算
    if (aria.startsWith('Clear ')) continue;
    if (aria === label || aria.startsWith(label + ':') || t === label) {
      const r = b.getBoundingClientRect();
      return {xy: [Math.round(r.x + r.width / 2),
                   Math.round(r.y + r.height / 2)],
              aria, text: t,
              rect: [Math.round(r.x), Math.round(r.y),
                     Math.round(r.width), Math.round(r.height)]};
    }
  }
  return null;
}"""

# 找到 Clear 按钮的坐标（点之前先验落点，别盲点）
CLEAR_JS = """(label) => {
  const want = 'Clear ' + label + ' filter';
  const b = document.querySelector(`[aria-label="${want}"]`);
  if (!b) return null;
  const r = b.getBoundingClientRect();
  if (r.width <= 0 || r.height <= 0) return {hidden: true, aria: want};
  const x = r.x + r.width / 2, y = r.y + r.height / 2;
  const hit = document.elementFromPoint(x, y);
  return {xy: [Math.round(x), Math.round(y)], aria: want,
          rect: [Math.round(r.x), Math.round(r.y),
                 Math.round(r.width), Math.round(r.height)],
          hit_ok: !!(hit && (hit === b || b.contains(hit))),
          hit_tag: hit ? hit.tagName : ''};
}"""

FILTER_JS = """(label) => [...document.querySelectorAll('[role=listbox]')]
  .filter(e => (e.getAttribute('aria-label')||'') === label + ' options')
  .map(e => { const r = e.getBoundingClientRect();
    return {rect: [Math.round(r.x), Math.round(r.y),
                   Math.round(r.width), Math.round(r.height)],
            opts: [...e.querySelectorAll('[role=option]')].map(o => ({
              text: (o.innerText||'').trim(),
              selected: o.getAttribute('aria-selected')}))}; })"""

FOCUS_JS = """() => { const a = document.activeElement;
  return {tag: a.tagName, aria: a.getAttribute('aria-label') || '',
          text: (a.innerText || '').trim().slice(0, 16)}; }"""


def ev(js, arg=None):
    return page.evaluate(js) if arg is None else page.evaluate(js, arg)


def enter_canvas():
    page.goto(
        "https://jimeng.jianying.com/ai-tool/ai-canvas/"
        "64b58cd5-7b04-4312-890a-09f2d1d3399f"
        "?enter_from=project_list&from_page=create",
        wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(10000)
    page.set_viewport_size({"width": 1512, "height": 1200})
    page.wait_for_timeout(2500)


def make_audio_node():
    for cand in ('button[aria-label="音频"]', 'button:has-text("音频")'):
        loc = page.locator(cand)
        if not loc.count():
            continue
        before = set(ev(
            "() => [...document.querySelectorAll('.react-flow__node')]"
            ".map(n => n.getAttribute('data-testid')||'')"))
        loc.first.click(timeout=10000)
        page.wait_for_timeout(2500)
        after = ev("() => [...document.querySelectorAll('.react-flow__node')]"
                   ".map(n => n.getAttribute('data-testid')||'')")
        new = [t for t in after if t and t not in before]
        if new:
            return new[0]
    return None


def open_voices():
    if page.get_by_text("全音色", exact=True).count():
        return True
    vt = page.locator('button[aria-label^="音色"]')
    if not vt.count():
        return False
    vt.first.click(timeout=8000)
    page.wait_for_timeout(1000)
    return bool(page.get_by_text("全音色", exact=True).count())


out = {}
enter_canvas()
out["logged_in"] = page.locator('button[aria-label="音频"]').count() > 0
print(f"== 登录态 {out['logged_in']} ==")

if not out["logged_in"]:
    out["verdict"] = "BLOCKED_BY_FIXTURE（登录态没了）"
else:
    tid = make_audio_node()
    out["audio_node"] = tid
    print(f"== 音频节点 {tid} ==")
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

    cases = []
    if not open_voices():
        cases.append({"verdict": "BLOCKED_BY_FIXTURE（音色库打不开）"})
    else:
        # ── 段 0：什么都没选时，header 里都有什么 ──────────────────
        base = ev(HEADER_JS, "?")
        print(f"\n== 段 0 未选任何值：header {base.get('n_header')} 个，"
              f"按钮 {len(base.get('btns', []))} 个 ==")
        for b in base.get("btns", []):
            print(f"   aria={b['aria']!r} text={b['text']!r} "
                  f"expanded={b['expanded']!r} rect={b['rect']}")
        out["header_pristine"] = base

        for (label, pick, allopt) in CASES:
            rec = {"label": label, "pick": pick}
            print(f"\n---- {label} / 选「{pick}」 ----")
            if not open_voices():
                rec["verdict"] = "前置态没成立（音色库关着）"
                cases.append(rec)
                continue

            # ① 现状：这个筛选钮的 Clear 在不在
            rec["clear_before"] = ev(CLEAR_JS, label)
            cb = rec["clear_before"]
            print(f"  选之前 Clear {label}: "
                  f"{'有' if cb and not cb.get('hidden') else '没有'}"
                  + (f" {cb}" if cb else ""))

            # ② 点芯片 → 层开 → 点选项（**验过坐标落点再点**）
            chip = ev(CHIP_JS, label)
            rec["chip_before"] = chip
            if not chip:
                rec["verdict"] = "判据盲区：认不出芯片（够不着，不是没有）"
                print("  !! " + rec["verdict"])
                cases.append(rec)
                continue
            page.mouse.click(chip["xy"][0], chip["xy"][1])
            page.wait_for_timeout(800)
            lay = ev(FILTER_JS, label)
            rec["layer_open"] = bool(lay)
            if not lay:
                rec["verdict"] = "前置态没成立（层没开）"
                print("  !! " + rec["verdict"])
                cases.append(rec)
                continue
            o = page.get_by_text(pick, exact=True).first
            if not o.count():
                rec["verdict"] = f"选项「{pick}」不在层里：" + \
                    str(lay[0]["opts"])
                print("  !! " + rec["verdict"])
                cases.append(rec)
                continue
            o.click(timeout=8000)
            page.wait_for_timeout(900)
            rec["selected_opts"] = ev(FILTER_JS, label)

            # ③ 选完之后：Clear 冒出来了吗
            rec["clear_after"] = ev(CLEAR_JS, label)
            ca = rec["clear_after"]
            print(f"  选之后 Clear {label}: "
                  f"{'有' if ca and not ca.get('hidden') else '没有'}"
                  + (f" {ca}" if ca else ""))
            rec["chip_after"] = ev(CHIP_JS, label)
            print(f"  芯片变成 {rec['chip_after']}")
            if label == "性别":
                # 抓在**清掉之前** —— 变形就发生在选中这一刻
                rec["row_dom_after"] = ev(ROW_JS, label)

            # ④ 点 Clear 会怎样
            if ca and not ca.get("hidden"):
                if not ca.get("hit_ok"):
                    rec["clear_click"] = "落点验不过，没敢点"
                    print("  !! 落点验不过（elementFromPoint 不在按钮上）")
                else:
                    page.mouse.click(ca["xy"][0], ca["xy"][1])
                    page.wait_for_timeout(900)
                    rec["clear_clicked"] = True
                    rec["chip_after_clear"] = ev(CHIP_JS, label)
                    rec["clear_still_there"] = ev(CLEAR_JS, label)
                    rec["focus_after_clear"] = ev(FOCUS_JS)
                    rec["filter_list_after_clear"] = ev(HEADER_JS, label)
                    # 复开层看选中态
                    c2 = ev(CHIP_JS, label)
                    if c2:
                        page.mouse.click(c2["xy"][0], c2["xy"][1])
                        page.wait_for_timeout(800)
                        l3 = ev(FILTER_JS, label)
                        rec["opts_after_clear"] = (
                            l3[0]["opts"] if l3 else None)
                        print(f"  点 Clear 之后复开："
                              f"{rec.get('opts_after_clear')}")
                        rec["value_cleared"] = rec["opts_after_clear"] == [
                            {"text": allopt, "selected": "true"}]
                        print(f"  芯片 {rec['chip_after_clear']}；"
                              f"焦点 {rec['focus_after_clear']}")
                        print(f"  Clear 还在吗："
                              f"{bool(rec['clear_still_there'] and not rec['clear_still_there'].get('hidden'))}")
                        # ⚠️⚠️ 判据第一跑写成上面那行：拿**一个** option
                        # 去比**一整列** option，永远不等，于是 2/2 明明清掉了
                        # 却记成 0/2。第五次「量错对象」（§87/§88/871/872/873
                        # 同族）。判据必须是「整列里选中项等于什么」：
                        opts = rec.get("opts_after_clear") or []
                        seld = [x["text"] for x in opts
                                if x.get("selected") == "true"]
                        rec["seld_after_clear"] = seld
                        rec["value_cleared"] = (seld == [allopt])
                        print(f"  ⇒ 清掉了吗：{seld == [allopt]}"
                              f"（当前选中={seld}）")
                        if l3:
                            # 收层，别留个开着的东西
                            page.keyboard.press("Escape")
                            page.wait_for_timeout(500)
            else:
                rec["clear_click"] = "没有可点的 Clear"
            cases.append(rec)

        out["cases"] = cases
        n_clear = sum(1 for c in cases if c.get("clear_after"))
        n_spawn = sum(1 for c in cases
                      if c.get("clear_after") and not c.get("clear_before"))
        n_cleared = sum(1 for c in cases if c.get("value_cleared"))
        out["n_with_clear_after"] = n_clear
        out["n_spawned_by_select"] = n_spawn
        out["n_value_cleared"] = n_cleared
        print(f"\n== 汇总：选完后有 Clear 的 {n_clear}/4；"
              f"选完才冒出来的 {n_spawn}/4；"
              f"点 Clear 真清掉的 {n_cleared}/{n_clear} ==")
        out["verdict"] = "sampled"

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n== 已写 {OUT} ==")
