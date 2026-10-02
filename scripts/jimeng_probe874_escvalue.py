#!/usr/bin/env python3
"""batch 874 源站探针：两件**必须查清**才敢往下写的事。

## ① 「焦点落点那个 BUTTON 到底是什么」

批 873 读到焦点落在 `BUTTON/性别: 男`，就照着这个形式给复刻补了
`aria-label={`${label}: ${value}`}`。但 874 按「aria-label 以 `性别: ` 开头」
去找那个筛选芯片，**读不到** —— 说明**那个焦点元素未必是筛选芯片**。

把一个来路不明的形式抄进产品（847），比不抄更坏。所以本探针先把
那个元素的 tag / role / 矩形 / 祖先链 / 同类按钮列表**倒出来**。

## ② 选完一个值之后按 Esc，那个值**还在不在**

批 873 留的唯一一个**自选行为**：源站没取样，复刻按「收层 ≠ 取消选择」
实现（Esc 只关层、不清值）。这里去把样取回来。

## 计费边界

只点「音频」入口、选中节点、开「音色」、点筛选钮、点选项、按 Esc。
**绝不**点生成/发送/购买/充值，**也绝不**点音色 chip 本身。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe874_escvalue.py
"""

import json

OUT = "/tmp/b874-src-escvalue.json"
LABEL = "性别"
PICK = "男"

# 筛选层：aria-label 恰为 `{label} options`
FILTER_JS = """(label) => [...document.querySelectorAll('[role=listbox]')]
  .filter(e => (e.getAttribute('aria-label')||'') === label + ' options')
  .map(e => { const r = e.getBoundingClientRect();
    return {rect: [Math.round(r.x), Math.round(r.y),
                   Math.round(r.width), Math.round(r.height)],
            n_opts: e.querySelectorAll('[role=option]').length,
            opts: [...e.querySelectorAll('[role=option]')].map(o => ({
              text: (o.innerText||'').trim(),
              selected: o.getAttribute('aria-selected')}))}; })"""

# 焦点那个元素的全部身份信息 + 同页提到该筛选名的按钮清单
WHO_JS = """(label) => {
  const a = document.activeElement;
  const chain = [];
  let n = a;
  while (n && n !== document.body && chain.length < 8) {
    chain.push(n.tagName + '.' + ((n.className || '') + '')
      .split(' ').filter(Boolean).slice(0, 2).join('.'));
    n = n.parentElement;
  }
  const r = (a === document.body) ? {x:0,y:0,width:0,height:0}
                                  : a.getBoundingClientRect();
  const like = [...document.querySelectorAll('button,[role=button]')]
    .map(b => { const br = b.getBoundingClientRect();
      return {aria: b.getAttribute('aria-label') || '',
              text: (b.innerText || '').trim().slice(0, 14),
              role: b.getAttribute('role') || '',
              rect: [Math.round(br.x), Math.round(br.y),
                     Math.round(br.width), Math.round(br.height)]}; })
    .filter(x => x.aria.includes(label) || x.text.includes(label));
  return {is_body: a === document.body,
          tag: a.tagName, aria: a.getAttribute('aria-label') || '',
          text: (a.innerText || '').trim().slice(0, 18),
          role: a.getAttribute('role') || '',
          testid: a.getAttribute('data-testid') || '',
          title: a.getAttribute('title') || '',
          rect: [Math.round(r.x), Math.round(r.y),
                 Math.round(r.width), Math.round(r.height)],
          chain, n_like: like.length, like};
}"""

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

    def voices_open():
        return bool(page.get_by_text("全音色", exact=True).count())

    def open_voices():
        if voices_open():
            return True
        vt = page.locator('button[aria-label^="音色"]')
        if not vt.count():
            return False
        vt.first.click(timeout=8000)
        page.wait_for_timeout(1000)
        return voices_open()

    def chip_xy():
        """筛选芯片的坐标：**量**出来的，不按名字找
        （选完之后它会改名，按名字找必然数到 0 —— 873 的教训）。"""
        return page.evaluate("""(label) => {
          // 四个筛选芯片在同一行；从音色库面板里找「aria 含 label 或
          // 文本以 label 开头、且带 aria-expanded 或在那一行里」的按钮。
          const title = [...document.querySelectorAll('*')].find(e =>
            (e.innerText||'').trim() === '全音色'
            && !e.querySelector('*'));
          if (!title) return null;
          let box = title.parentElement;
          for (let i = 0; i < 6 && box; i++, box = box.parentElement) {
            const cands = [...box.querySelectorAll('button,[role=button]')]
              .filter(b => { const r = b.getBoundingClientRect();
                return r.height >= 20 && r.height <= 40 && r.width >= 100; });
            if (cands.length >= 4) {
              const t = (cands[0].innerText || '').trim();
              const r = cands[0].getBoundingClientRect();
              return {xy: [Math.round(r.x + r.width / 2),
                           Math.round(r.y + r.height / 2)],
                      first_text: t, n_cands: cands.length,
                      texts: cands.map(c => (c.innerText||'').trim())};
            }
          }
          return null;
        }""", LABEL)

    rec = {}
    # ── ① 选一个具体值，看焦点落在谁身上 ───────────────────────────
    if not open_voices():
        rec["why"] = "音色库打不开（前置态没成立）"
    else:
        c0 = chip_xy()
        rec["chip_xy_before"] = c0
        if c0:
            page.mouse.click(c0["xy"][0], c0["xy"][1])
            page.wait_for_timeout(800)
        lay = page.evaluate(FILTER_JS, LABEL)
        rec["layer_open"] = bool(lay)
        rec["layer_opts_before"] = (lay[0]["opts"] if lay else None)
        print(f"芯片行 {c0}")
        if lay:
            o = page.get_by_text(PICK, exact=True).first
            if o.count():
                o.click(timeout=8000)
                page.wait_for_timeout(900)
            rec["who_after_pick"] = page.evaluate(WHO_JS, LABEL)
            w = rec["who_after_pick"]
            print(f"\n① 选「{PICK}」之后焦点：tag={w['tag']} "
                  f"aria={w['aria']!r} text={w['text']!r} rect={w['rect']}")
            print(f"   祖先链 {w['chain']}")
            print(f"   同页提到「{LABEL}」的按钮 {w['n_like']} 个：")
            for x in w["like"]:
                print(f"     aria={x['aria']!r} text={x['text']!r} "
                      f"rect={x['rect']}")
            rec["layer_after_pick"] = page.evaluate(FILTER_JS, LABEL)

            # ── ② 重开层 → 按 Esc → 值还在不在 ─────────────────────
            c1 = chip_xy()
            rec["chip_xy_after"] = c1
            if c1:
                page.mouse.click(c1["xy"][0], c1["xy"][1])
                page.wait_for_timeout(800)
            rec["layer_reopened"] = bool(page.evaluate(FILTER_JS, LABEL))
            rec["opts_at_reopen"] = (
                page.evaluate(FILTER_JS, LABEL)[0]["opts"]
                if rec["layer_reopened"] else None)
            print(f"\n② 重开：{rec['layer_reopened']} 选项="
                  f"{rec.get('opts_at_reopen')}")
            if rec["layer_reopened"]:
                page.keyboard.press("Escape")
                page.wait_for_timeout(800)
                rec["layer_after_esc"] = bool(page.evaluate(FILTER_JS, LABEL))
                rec["chip_after_esc"] = page.evaluate(WHO_JS, LABEL)
                rec["focus_after_esc"] = page.evaluate(WHO_JS, LABEL)
                c2 = chip_xy()
                rec["chip_text_after_esc"] = (c2 or {}).get("first_text")
                print(f"   Esc 后：层还开着={rec['layer_after_esc']} "
                      f"芯片第一枚文案={rec['chip_text_after_esc']!r}")
                if rec["opts_at_reopen"] and rec["layer_after_esc"] is False:
                    # 用**重开时**读到的 aria-selected 跟 Esc 之后重开读到的比
                    if c2:
                        page.mouse.click(c2["xy"][0], c2["xy"][1])
                        page.wait_for_timeout(800)
                        l3 = page.evaluate(FILTER_JS, LABEL)
                        rec["opts_after_esc_reopen"] = (
                            l3[0]["opts"] if l3 else None)
                        print(f"   Esc 之后再开：选项="
                              f"{rec.get('opts_after_esc_reopen')}")
                        rec["value_survived_esc"] = (
                            rec.get("opts_after_esc_reopen")
                            == rec.get("opts_at_reopen"))
                        print(f"   ⇒ 选中值在 Esc 之后**"
                              f"{'还在' if rec['value_survived_esc'] else '没了'}"
                              f"**")
                        if l3:
                            page.keyboard.press("Escape")
                            page.wait_for_timeout(500)
    out.update(rec)
    out["verdict"] = "sampled"

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n== 已写 {OUT} ==")
