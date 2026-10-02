#!/usr/bin/env python3
"""batch 888 源站探针：Esc 关掉音频生成面板之后，**怎么重新打开它**？

## 这是当前最高频的阻塞点

同一个前置问题已经挡了**四跑**：883 两跑 + 887 一跑 + 886 兜底那次。
现象一模一样：**Esc 之后音频生成面板整个收起**，
`button[aria-label^="音色"]` **不在 DOM 里** ⇒ 后续所有「重开再读」的动作
都做不了。

而它挡住的每一条都很要紧：

- 883/885：「Esc 之后节点还在不在选中态」
- 887：「芯片上按 Esc 之后**值**还在不在」

所以这批**只查这一件事**，把它当**独立问题**解决，而不是继续在那些
探针里打补丁。

## 先要分清的三种可能（处置完全不同）

① 面板只是**隐藏**（`display:none` / `visibility:hidden` / 高度 0）
   ⇒ 重开方式：让节点**重新选中**
② 面板真的**卸载**了（DOM 里没有这个元素）
   ⇒ 重开方式同上，但要**先让节点选中**
③ Esc 把**整个工具栏**（不止这一个面板）都收了，而重开需要
   **别的入口**（比如双击节点、右键、或者某个快捷键）

三者的判据不同，所以**先量「Esc 之后那个元素还在不在 DOM 里」**，
再量「怎么让它回来」。

## 逐个试**重开手段**（每次都验旁证）

| 手段 | 说明 |
|---|---|
| reselect | 点节点中心（884 实测可靠） |
| dblclick | 双击节点 |
| rightclick | 右键节点（会不会出画布菜单？） |
| Enter / Space | 节点聚焦后按（源站节点是 `BUTTON` 吗？**未量**） |
| Escape_then_reselect | 先 Esc 再点（有些实现要两步） |

⚠️ 每种手段**独立测**，失败**记账**不硬试；成功也要**重复 2 次**
（884 的教训：一次成功不叫可靠）。

## 计费边界

只点「音频」入口、点画布空白、点/双击/右键节点、按键、开音色库。
**绝不**点生成/发送/购买/充值，**也绝不**点音色 chip 本身。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe888_reopen_src.py
"""

import json

OUT = "/tmp/b888-src-reopen.json"

FOCUS_JS = """() => { const a = document.activeElement;
  if (a === document.body) return {tag: 'BODY', aria: '(body)'};
  return {tag: a.tagName,
          aria: a.getAttribute('aria-label') || '',
          is_node: !!(a.closest && a.closest('.react-flow__node'))}; }"""

# Esc 之后：那个工具条**元素**还在不在 DOM 里？是什么状态？
AFTER_ESC_JS = """(tid) => {
  const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
  if (!n) return {no_node: true};
  // 1) 面板本体在不在 DOM 里
  const panel = document.querySelector('button[aria-label^="音色"]');
  const form = n.querySelector('form');
  const toolbar = n.querySelector('.react-flow__node-toolbar')
    || document.querySelector('.react-flow__node-toolbar');
  const probe = (el) => {
    if (!el) return null;
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    return {tag: el.tagName,
            display: cs.display, visibility: cs.visibility,
            opacity: cs.opacity,
            rect: [Math.round(r.x), Math.round(r.y),
                   Math.round(r.width), Math.round(r.height)],
            in_dom: el.isConnected,
            /* 点它中心会落到谁身上 —— 不可点的话中心会落到别的元素 */
            hit_at_center: (() => {
              const t = document.elementFromPoint(
                r.x + r.width / 2, r.y + r.height / 2);
              if (!t) return null;
              return t.tagName + '/'
                + ((t.getAttribute('aria-label')
                    || t.className || '') + '').slice(0, 40);
            })()};
  };
  return {
    voice_btn: probe(panel),
    node_form: probe(form),
    toolbar: probe(toolbar),
    /* 节点自己还在不在「选中」形态：看它的 class 有没有 selected */
    node_class: ((n.className || '') + '').slice(0, 120),
    node_has_selected_class: /\\bselected\\b/.test(
      ((n.className || '') + '')),
    /* 节点上有没有 aria-pressed / aria-selected 之类的选中标记 */
    node_aria_selected: n.getAttribute('aria-selected'),
    node_aria_pressed: n.getAttribute('aria-pressed'),
    focus: (() => { const a = document.activeElement;
      return {tag: a === document.body ? 'BODY' : a.tagName,
              aria: a.getAttribute
                ? (a.getAttribute('aria-label') || '') : ''}; })(),
  };
}"""

TOOLBAR_JS = """() => !!document.querySelector('button[aria-label^="音色"]')"""


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

    def center():
        return ev("""(tid) => {
          const n = document.querySelector(
            `.react-flow__node[data-testid="${tid}"]`);
          if (!n) return null;
          const r = n.getBoundingClientRect();
          return [Math.round(r.x + r.width / 2),
                  Math.round(r.y + r.height / 2)];
        }""", tid)

    def blank():
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

    if not tid:
        out["verdict"] = "插不进音频节点（前置态没成立）"
    else:
        blank()
        c = center()
        if c:
            page.mouse.click(c[0], c[1])
        page.wait_for_timeout(1100)
        rec = {"opened_initially": ev(TOOLBAR_JS)}
        print(f"\n== 阶段 1：先选中节点，面板开着吗 "
              f"{rec['opened_initially']} ==")
        if not rec["opened_initially"]:
            out["verdict"] = ("前置态没成立：连**第一次**选中都没开出面板 ⇒ "
                              "本轮不测（不是「Esc 收不掉」）")
            print("  !! " + out["verdict"])
        else:
            # ── 阶段 2：按 Esc，看面板**元素**还在不在 ──────────
            page.keyboard.press("Escape")
            page.wait_for_timeout(1100)
            rec["toolbar_after_esc"] = ev(TOOLBAR_JS)
            rec["dom_after_esc"] = ev(AFTER_ESC_JS, tid)
            da = rec["dom_after_esc"]
            print(f"\n== 阶段 2：Esc 之后 ==")
            print(f"   工具条按钮还在吗 {rec['toolbar_after_esc']}")
            if da.get("no_node"):
                print("   !! 节点本身不见了")
            else:
                for k in ("voice_btn", "node_form", "toolbar"):
                    v = da.get(k)
                    if v is None:
                        print(f"   {k:10s}: **不在 DOM 里**")
                    else:
                        print(f"   {k:10s}: 在 DOM 里 display={v['display']} "
                              f"visibility={v['visibility']} "
                              f"rect={v['rect']} 中心命中={v['hit_at_center']!r}")
                print(f"   节点 class = {da['node_class']!r}")
                print(f"   有 selected 类 = {da['node_has_selected_class']}  "
                      f"aria-selected={da['node_aria_selected']!r}  "
                      f"aria-pressed={da['node_aria_pressed']!r}")
                print(f"   焦点 = {da['focus']}")
                hidden_but_present = any(
                    da.get(k) is not None for k in
                    ("voice_btn", "node_form", "toolbar"))
                rec["hidden_but_present"] = hidden_but_present

            # ── 阶段 3：逐个试重开手段，每种**重复 2 次** ────────
            print(f"\n== 阶段 3：逐个试重开手段（每种 2 次）==")
            results = {}

            def attempt(name, action):
                succ = 0
                det = []
                for _ in range(2):
                    if ev(TOOLBAR_JS):      # 已经是开着的，先关掉
                        page.keyboard.press("Escape")
                        page.wait_for_timeout(900)
                    action()
                    page.wait_for_timeout(1100)
                    ok = ev(TOOLBAR_JS)
                    det.append(ok)
                    succ += 1 if ok else 0
                results[name] = {"n_success": succ, "n_try": 2, "detail": det,
                                 "reliable": succ == 2}
                print(f"   {name:18s} {succ}/2  "
                      f"{'✅ 可靠' if succ == 2 else '❌'}")
                return succ == 2

            def resel():
                c2 = center()
                if c2:
                    page.mouse.click(c2[0], c2[1])
            attempt("reselect", resel)

            def dbl():
                c2 = center()
                if c2:
                    page.mouse.dblclick(c2[0], c2[1])
            attempt("dblclick", dbl)

            def rclk():
                c2 = center()
                if c2:
                    page.mouse.click(c2[0], c2[1], button="right")
            attempt("rightclick", rclk)

            def key_on_node():
                c2 = center()
                if c2:
                    page.mouse.click(c2[0], c2[1])
                    page.wait_for_timeout(600)
                    page.keyboard.press("Enter")
            attempt("enter_on_node", key_on_node)

            def space_on_node():
                c2 = center()
                if c2:
                    page.mouse.click(c2[0], c2[1])
                    page.wait_for_timeout(600)
                    page.keyboard.press("Space")
            attempt("space_on_node", space_on_node)

            out["reopen_attempts"] = results
            rel = [k for k, v in results.items() if v["reliable"]]
            out["reliable_reopen"] = rel
            print(f"\n== 可靠的重开手段：{rel}")
            if not rel:
                out["verdict"] = (
                    "**五种重开手段全试了**（各 2 次），一次都没把面板开回来 "
                    "⇒ 「Esc 之后怎么重开音频生成面板」这个**前置问题本身**"
                    "**未解决**。⚠️ 这**不是**「面板收不掉」（那是反向问题，"
                    "收得掉已经验过 4 遍），而是「**收掉之后回不来**」。"
                    "要查的方向：① 那个元素在不在 DOM 里（阶段 2 已量）"
                    "② 是不是需要先**切到别的节点再切回来**"
                    "③ 是不是有别的入口（顶栏？右键？）")
                print("  !! " + out["verdict"])
            else:
                out["verdict"] = "sampled"
            out["result"] = rec

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n== 已写 {OUT} ==")
