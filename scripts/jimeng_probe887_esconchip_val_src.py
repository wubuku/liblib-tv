#!/usr/bin/env python3
"""batch 887 源站探针：芯片上按 Esc，**一次运行里同时**读「落点」和「值」。

## 补的是哪条缺口

886 取到了源站「芯片上按 Esc」的**焦点落点**（该音频节点本体），但没取
**值** —— 它只记了 `Clear 还在=False`，而那只是**层关了导致控件消失**，
**推不出**值被清了。

而 874（另一次运行）测过「芯片上按 Esc **值保留**」。
两条各有源站证据，但**不在同一次运行里** ⇒ 按 §「不许把两次运行的
证据合并成一句」的口径，这里补一次**同时**读两样的。

## 怎么读「值」才不被「层关了」污染

不能**当场**读：Esc 之后层已关、芯片已卸载，什么都读不到。
必须 **重新打开音色库再读**（886 探针里 `reselect_node()` 干过这件事，
这里复用同一套三级前置态）。

## 定位纪律（884/885 之后的新规矩）

- 定位**全部**用 `data-testid`
- 选节点用 **center 落点**（884 实测 5 策略各 2/2）+ 旁证（工具条）把关
- 聚焦芯片用**程序化 `focus()`**（芯片是 toggle，点了会开层 —— 876 的教训）

## 计费边界

只点「音频」入口、点画布空白、点节点本体、开「音色」、点筛选钮、点选项、按键。
**绝不**点生成/发送/购买/充值，**也绝不**点音色 chip 本身。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe887_esconchip_val_src.py
"""

import json

OUT = "/tmp/b887-src-esconchip-val.json"
LABEL = "性别"
PICK = "男"

FOCUS_JS = """() => { const a = document.activeElement;
  if (a === document.body) return {tag: 'BODY', aria: '(body)'};
  return {tag: a.tagName,
          aria: a.getAttribute('aria-label') || '',
          in_audio_node: !!(a.closest && a.closest(
            '.react-flow__node-audio'))}; }"""

TOOLBAR_JS = """() => !!document.querySelector('button[aria-label^="音色"]')"""
VOICES_JS = """() => [...document.querySelectorAll('*')].some(e =>
  (e.innerText||'').trim() === '全音色' && !e.querySelector('*'))"""

CENTER_JS = """(tid) => {
  const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
  if (!n) return null;
  const r = n.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
}"""

# 程序化聚焦芯片 + 读它的**可见文案**（= 当前值；未选中时是筛选名）
CHIP_JS = """(label) => {
  for (const b of document.querySelectorAll('button[aria-expanded]')) {
    const a = b.getAttribute('aria-label') || '';
    if (a.startsWith('Clear ')) continue;
    if (a.startsWith(label + ':')) {
      return {aria: a, text: (b.innerText || '').trim(),
              rect: [Math.round(b.getBoundingClientRect().x),
                     Math.round(b.getBoundingClientRect().y),
                     Math.round(b.getBoundingClientRect().width),
                     Math.round(b.getBoundingClientRect().height)]};
    }
  }
  return null;
}"""

FOCUS_CHIP_JS = """(label) => {
  for (const b of document.querySelectorAll('button[aria-expanded]')) {
    const a = b.getAttribute('aria-label') || '';
    if (a.startsWith('Clear ')) continue;
    if (a.startsWith(label + ':')) {
      b.focus();
      return {focused: document.activeElement === b,
              aria: b.getAttribute('aria-label') || ''};
    }
  }
  return {no_chip: true};
}"""

CLEAR_JS = """(label) => !!document.querySelector(
  `[aria-label="Clear ${label} filter"]`)"""


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
    print(f"== 音频节点 {tid} ==")

    def click_blank():
        spot = ev("""() => {
          for (const [x, y] of [[1300, 1000], [1360, 920], [1220, 1080],
                                [1400, 840], [400, 1080]]) {
            const t = document.elementFromPoint(x, y);
            if (t && t.closest('.react-flow__pane')
                && !t.closest('.react-flow__node')) return [x, y];
          }
          return null;
        }""")
        if spot:
            page.mouse.click(spot[0], spot[1])
            page.wait_for_timeout(800)

    def select_node():
        """⚠️ 批 888 **修掉一个模板缺陷**：原来这里**先点空白画布**再点节点。
        那对「确保起点是未选中」有用，但**Esc 之后**调用时：Esc 已经把节点
        **取消选中**了，那一下多余的「点空白」若**落在节点上**，就变成
        「点节点（选中）→ 立刻再点（取消）」⇒ 净效果是**把面板关掉** ——
        887 第一跑「重开失败」就是这么来的。

        888 实测：Esc 之后面板**真卸载**（不在 DOM），而**单纯点节点中心**
        **2/2 可靠**（五种重开手段各 2/2）。
        所以：**先验旁证**，开着就直接用；否则点节点，**绝不**先点空白。"""
        for _ in range(3):
            if ev(TOOLBAR_JS):          # **先验旁证**，开着就直接用
                return True
            c = ev(CENTER_JS, tid)
            if not c:
                return False
            page.mouse.click(c[0], c[1])
            page.wait_for_timeout(1000)
            if ev(TOOLBAR_JS):
                return True
        return False

    def open_voices():
        """三级前置态，每级都**验过**才往下走（886 同款）。
        Esc 之后音频生成面板**整个收起**，`音色: 音色库` 压根不在 DOM 里 ——
        不是「点不到」，是**按钮没了**。"""
        for _ in range(3):
            if ev(VOICES_JS):
                return True
            if not ev(TOOLBAR_JS):
                select_node()
            vt = page.locator('[aria-label="音色: 音色库"]')
            if not vt.count():
                vt = page.locator('button[aria-label^="音色"]')
            if vt.count():
                vt.first.click(timeout=8000)
                page.wait_for_timeout(1800)
                if ev(VOICES_JS):
                    return True
        return ev(VOICES_JS)

    def chip_value():
        """当前值：芯片的**可见文案**（选中时=值，未选中时=筛选名）。
        **零破坏**读法，不点任何东西。"""
        c = ev(CHIP_JS, LABEL)
        return c["text"] if c else None

    if not tid:
        out["verdict"] = "插不进音频节点（前置态没成立）"
    elif not select_node():
        out["verdict"] = ("前置态没成立：center 落点试 3 次都没选中 ⇒ 本轮不测")
        print("  !! " + out["verdict"])
    else:
        rec = {}
        rec["voices_open"] = open_voices()
        if rec["voices_open"]:
            c = ev(CHIP_JS, LABEL)
            if c:
                pg_xy = [c["rect"][0] + c["rect"][2] // 2,
                         c["rect"][1] + c["rect"][3] // 2]
                page.mouse.click(pg_xy[0], pg_xy[1])
                page.wait_for_timeout(800)
                o = page.get_by_text(PICK, exact=True).first
                if o.count():
                    o.click(timeout=8000)
                    page.wait_for_timeout(900)
        rec["clear_shown_before"] = ev(CLEAR_JS, LABEL)
        rec["value_before"] = chip_value()
        fc = ev(FOCUS_CHIP_JS, LABEL)
        rec["focus_chip"] = fc
        rec["focus_before"] = ev(FOCUS_JS)
        if not fc.get("focused"):
            rec["verdict"] = "前置态没成立：聚焦点到芯片失败 ⇒ 本轮不测"
            print("  !! " + rec["verdict"])
        else:
            page.keyboard.press("Escape")
            page.wait_for_timeout(1100)
            # ── 同一帧读到的东西：落点（当场）──
            rec["focus_after"] = ev(FOCUS_JS)
            rec["toolbar_after"] = ev(TOOLBAR_JS)
            rec["clear_after_shown"] = ev(CLEAR_JS, LABEL)
            # ── 值（**重开**读，当场读会被「层关了」污染）──
            reopened = open_voices()
            rec["reopened"] = reopened
            if not reopened:
                rec["value_after"] = None
                rec["verdict"] = ("前置态没成立：Esc 之后音色库**没开回来** ⇒ "
                                  "「值还在不在」**测不到**（不是「值没了」）")
                print("  !! " + rec["verdict"])
            else:
                rec["value_after"] = chip_value()
                rec["clear_after_reopen"] = ev(CLEAR_JS, LABEL)
                rec["value_survived"] = (rec["value_after"]
                                         == rec["value_before"])
                rec["verdict"] = (
                    "芯片上按 Esc：**落点**=该音频节点本体（886 复现），"
                    f"**值** {rec['value_before']!r} → {rec['value_after']!r} ⇒ "
                    f"{'保留' if rec['value_survived'] else '被清了'}"
                    f"（Clear 重开后{'还在' if rec['clear_after_reopen'] else '不在'}）")
                print(f"\n== 芯片上按 Esc（一次运行，两样同时读）==")
                print(f"   焦点 {rec['focus_before']['aria']!r} → "
                      f"{rec['focus_after']['aria']!r}"
                      f"（在音频节点={rec['focus_after']['in_audio_node']}）")
                print(f"   工具条 {rec['toolbar_after']}（False = 节点也取消选中）")
                print(f"   值 {rec['value_before']!r} → "
                      f"{rec['value_after']!r}  "
                      f"Clear 重开后={rec['clear_after_reopen']}")
                print(f"\n== {rec['verdict']}")
            out["result"] = rec
        if not out.get("verdict"):
            out["verdict"] = "sampled"

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n== 已写 {OUT} ==")
