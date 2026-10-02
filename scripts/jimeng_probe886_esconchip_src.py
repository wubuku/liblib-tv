#!/usr/bin/env python3
"""batch 886 源站探针：焦点在**芯片**上按 Esc，落在谁身上？

## 为什么测这条

§93 测的是「焦点在 **Clear** 上按 Esc」，§95/§97 测的也是它。但
**芯片**上按 Esc 是**另一条路径**，而复刻侧它落在 **`body`**。

而源站这一条**从未取样** —— 所以**现在还不能判它是差异**（§69：
按同类推测不许当结论）。这批去把样取回来。

## 三件要分清的事（别混）

① 焦点在**芯片**上按 Esc ⇒ 焦点落在谁身上？（本批的正题）
② 层有没有被收掉？（874 测过「值保留」，但落点从没量过）
③ 节点还在不在选中态？（885 测过 Clear 那条路径的，芯片这条**未知**）

## 定位纪律（885 之后的新规矩）

- 定位**全部**用 `data-testid`（884 查清：按 aria 找第一个会拿到示例节点）
- **程序化 `focus()`**，不点芯片（芯片是 toggle，点了会开层 —— 876 整跑作废的教训）
- 选节点用 **center 落点**（884 实测可靠），旁证（工具条在不在）把关

## 计费边界

只点「音频」入口、点画布空白、点节点本体、开「音色」、点筛选钮、点选项、按键。
**绝不**点生成/发送/购买/充值，**也绝不**点音色 chip 本身。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe886_esconchip_src.py
"""

import json

OUT = "/tmp/b886-src-esconchip.json"
LABEL = "性别"
PICK = "男"

FOCUS_JS = """() => { const a = document.activeElement;
  if (a === document.body) return {tag: 'BODY', aria: '(body)'};
  return {tag: a.tagName,
          aria: a.getAttribute('aria-label') || '',
          in_audio_node: !!(a.closest && a.closest(
            '.react-flow__node-audio')),
          in_filter_layer: !!(a.closest && a.closest('[role=listbox]')),
          in_toolbar: !!(a.closest && a.closest(
            '.react-flow__node-toolbar'))}; }"""

TOOLBAR_JS = """() => !!document.querySelector('button[aria-label^="音色"]')"""
VOICES_JS = """() => [...document.querySelectorAll('*')].some(e =>
  (e.innerText||'').trim() === '全音色' && !e.querySelector('*'))"""

CENTER_JS = """(tid) => {
  const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
  if (!n) return null;
  const r = n.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
}"""

# **程序化**聚焦芯片（不点 —— 芯片是 toggle，点了会开层）
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

FILTER_JS = """(label) => {
  const e = document.querySelector(
    `[role=listbox][aria-label="${label} options"]`);
  if (!e) return null;
  return [...e.querySelectorAll('[role=option]')].map(o => ({
    text: (o.innerText || '').trim(),
    selected: o.getAttribute('aria-selected')}));
}"""


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
        """center 落点（884 实测可靠）+ 旁证把关 + 三次重试。

        ⚠️ 批 888 **修掉一个模板缺陷**：原来这里**先点空白画布**再点节点。
        那是给「从选中态回到未选中、确保起点一致」用的 —— 探针**开头**没问题，
        但**Esc 之后**调用它时：Esc 已经把节点**取消选中**了，那一下多余的
        「点空白」若**落在节点上**，就变成「点节点（选中）→ 紧接着再点一次
        （取消）」⇒ 净效果是**把面板关掉**。

        888 实测：Esc 之后面板**真卸载**（`voice_btn` / `node_form` /
        `toolbar` 全不在 DOM），而**单纯点节点中心**（不点空白）**2/2 可靠**；
        五种重开手段各 2/2。

        所以：**先验旁证**，开着就直接用；只有确认没开才点节点，**绝不**先点空白。"""
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

    if not tid:
        out["verdict"] = "插不进音频节点（前置态没成立）"
    elif not select_node():
        out["verdict"] = ("前置态没成立：center 落点试 3 次都**没选中**"
                          "（旁证=工具条不在）⇒ 本轮不测。"
                          "**不是**「芯片上 Esc 没有行为」")
        print("  !! " + out["verdict"])
    else:
        rec = {"selected": True}
        for _ in range(3):
            if ev(VOICES_JS):
                break
            vt = page.locator('button[aria-label^="音色"]')
            if vt.count():
                vt.first.click(timeout=8000)
                page.wait_for_timeout(1800)
        rec["voices_open"] = ev(VOICES_JS)
        if rec["voices_open"]:
            c = ev("""(label) => {
              for (const b of document.querySelectorAll('button[aria-expanded]')) {
                const a = b.getAttribute('aria-label') || '';
                if (a.startsWith(label + ':')) {
                  const r = b.getBoundingClientRect();
                  return [Math.round(r.x + r.width/2),
                          Math.round(r.y + r.height/2)];
                }
              }
              return null;
            }""", LABEL)
            if c:
                page.mouse.click(c[0], c[1])
                page.wait_for_timeout(800)
                o = page.get_by_text(PICK, exact=True).first
                if o.count():
                    o.click(timeout=8000)
                    page.wait_for_timeout(900)
        rec["filter_set"] = bool(ev(
            """(label) => {
              const c = document.querySelector(`[aria-label="${label}: ${label}"]`)
                || [...document.querySelectorAll('button[aria-expanded]')]
                     .find(b => (b.getAttribute('aria-label')||'')
                           .startsWith(label + ':')
                           && (b.getAttribute('aria-label')||'')
                               .split(': ')[1] !== label);
              return !!c;
            }""", LABEL))
        rec["clear_shown"] = bool(ev(
            """(label) => !!document.querySelector(
                 `[aria-label="Clear ${label} filter"]`)""", LABEL))

        # ── 焦点**程序化**聚到芯片上（不点 —— 芯片是 toggle）─────
        fc = ev(FOCUS_CHIP_JS, LABEL)
        rec["focus_chip"] = fc
        rec["focus_before"] = ev(FOCUS_JS)
        rec["filter_layer_before"] = bool(ev(FILTER_JS, LABEL))
        rec["toolbar_before_esc"] = ev(TOOLBAR_JS)
        if not fc.get("focused"):
            rec["verdict"] = ("前置态没成立：聚焦点到芯片**失败** ⇒ 本轮不测")
            print("  !! " + rec["verdict"])
        else:
            page.keyboard.press("Escape")
            page.wait_for_timeout(1100)
            rec["focus_after"] = ev(FOCUS_JS)
            rec["filter_layer_after"] = bool(ev(FILTER_JS, LABEL))
            rec["toolbar_after_esc"] = ev(TOOLBAR_JS)
            rec["clear_after"] = bool(ev(
                """(label) => !!document.querySelector(
                     `[aria-label="Clear ${label} filter"]`)""", LABEL))
            # ⚠️⚠️ `clear_after=False` **推不出**「值被清了」——
            #   那个 Clear 住在**音色库层里**，Esc 之后**层整个关了**，
            #   控件随之消失，读到 False 是**必然**，与值无关。
            #   ⇒ 「芯片上按 Esc **值还在不在**」本探针**测不到**，
            #     **不许**拿 `clear_after` 当证据（要读值必须**重开**音色库，
            #     见 `jimeng_probe887_esconchip_val_src.py`）。
            #   同理，「落点」和「值」是**两件事**，不许混成一句。
            rec["clear_after_is_not_value_evidence"] = (
                "Clear 在层里，层关了它就没了 ⇒ False **推不出**值被清")
            rec["value_measured"] = False
            print(f"\n== 芯片上按 Esc ==")
            print(f"   按之前：焦点={rec['focus_before']['aria']!r}  "
                  f"层开着={rec['filter_layer_before']}  "
                  f"工具条={rec['toolbar_before_esc']}")
            print(f"   按之后：焦点={rec['focus_after']['aria']!r}  "
                  f"层开着={rec['filter_layer_after']}  "
                  f"工具条={rec['toolbar_after_esc']}  "
                  f"Clear 还在={rec['clear_after']}")
            fa = rec["focus_after"]
            if fa["tag"] == "BODY":
                rec["verdict"] = (
                    "源站芯片上按 Esc 焦点落 **body** ⇒ 复刻落 body "
                    "**与源站一致**，**不是差异**。")
            elif fa["in_audio_node"]:
                rec["verdict"] = (
                    "源站芯片上按 Esc 焦点落**该音频节点本体** ⇒ "
                    "复刻落 body 是**真差异**（与 Clear 那条路径不同！）。")
            elif fa["aria"]:
                rec["verdict"] = (
                    f"源站芯片上按 Esc 焦点落 `{fa['tag']}/{fa['aria']}`"
                    f"（在层内={fa['in_filter_layer']}、"
                    f"在工具条={fa['in_toolbar']}、"
                    f"在音频节点={fa['in_audio_node']}）⇒ 要逐项对账，"
                    f"**不许**笼统写成「落在某处」。")
            else:
                rec["verdict"] = "焦点读数异常，判据盲区，不出结论"
            print(f"\n== {rec['verdict']}")
        out["result"] = rec
        if not out.get("verdict"):
            out["verdict"] = "sampled"

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n== 已写 {OUT} ==")
