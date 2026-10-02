#!/usr/bin/env python3
"""batch 889b 源站探针：补 889 第一跑**没做到**的两件事。

## 为什么要补

889 第一跑（`/tmp/b889-src-esclanding.json`）四种前置态各 2/2 稳定，
查到一条**新路径**：

| 前置态 | 落点 | 工具条 |
|---|---|---|
| 芯片 / Clear / 我设计的 `nofocus` | 节点本体 | False |
| **`layer_open`（焦点在层内）** | **焦点回到芯片** | **True** |

但第一跑**有两个洞**，这批专门补：

### 洞 1：`nofocus` **没有复现 888 的前置态**（我自己把前置态设计错了）

889 的 `rebuild()` 最后一步是**程序化聚焦芯片去设值**，所以等到按 Esc 时
焦点其实**停在芯片上**（第一跑读数确实是 `焦点='性别: 男'`）⇒ 那根本不是
「没聚焦」。

888 的真实前置态是：**鼠标点节点中心 → 面板开了 → 马上按 Esc**，
**全程没程序化设过焦点、连值都没设**。所以要**原样**复现它：纯鼠标、
不碰 `set_value()`、不碰任何 `focus()`。

⇒ 这一跑才能回答「`Canvas` 那个落点到底在什么前置态下出现」。

### 洞 2：874 的「值保留」在**它自己的前置态**下**从没被同一次运行读过**

§98/§99 记的是：874 说「值保留」，887 说「层收着时被清」，两跑都成立但
**不是同一次运行、也不是同一前置态**。889 第一跑查出了 `layer_open` 这条
路径（Esc 只关层、工具条仍 True），但**没读值**。

⇒ 这批在 `layer_open` 前置态下**重开音色库读一次值**，把 874 那条读数
在**它自己的前置态**里复核一遍。

## 结论口径

- 每种 2 次；**只有 2/2 同一类**才写「该前置态 ⇒ 该落点」
- 读不到就记账，**不许**把「没开回来」写成「值没了」（876c 栽过）

## 计费边界

只点「音频」入口、点画布空白、点/聚焦节点本体、开「音色」、点**筛选**芯片、
点筛选选项、按键。**绝不**点生成/发送/购买/充值，**也绝不**点音色库网格里
的音色 chip 本身。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe889b_esclanding2_src.py
"""

import json

OUT = "/tmp/b889b-src-esclanding2.json"
LABEL = "性别"
PICK = "男"
REPS = 2

FOCUS_JS = """() => { const a = document.activeElement;
  if (a === document.body) return {tag: 'BODY', aria: '(body)',
                                   text: '', in_audio_node: false,
                                   in_listbox: false};
  return {tag: a.tagName,
          aria: a.getAttribute('aria-label') || '',
          text: (a.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 20),
          in_audio_node: !!(a.closest && a.closest(
            '.react-flow__node-audio')),
          in_listbox: !!(a.closest && a.closest('[role=listbox]'))}; }"""

TOOLBAR_JS = """() => !!document.querySelector('button[aria-label^="音色"]')"""
VOICES_JS = """() => [...document.querySelectorAll('*')].some(e =>
  (e.innerText||'').trim() === '全音色' && !e.querySelector('*'))"""

LAYER_OPEN_JS = """(label) => !!(
  document.querySelector(
    `[role-testid] [role=listbox][aria-label="${label} options"]`)
  || document.querySelector(`[role=listbox][aria-label="${label} options"]`))"""

CENTER_JS = """(tid) => {
  const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
  if (!n) return null;
  const r = n.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
}"""

# ⚠️ 落点**元素**的 `data-testid`：888 只记了 aria='Canvas'，这跑把它到底是
# 哪个元素也记下来（`.react-flow__pane`？画布容器？），免得只凭 aria 猜。
FOCUS_TARGET_JS = """() => { const a = document.activeElement;
  if (!a || a === document.body) return null;
  const t = a.closest('[data-testid]');
  const p = a.closest('.react-flow__pane');
  return {self_testid: a.getAttribute('data-testid') || '',
          closest_testid: t ? t.getAttribute('data-testid') : null,
          in_pane: !!p,
          pane_testid: p ? p.getAttribute('data-testid') : null,
          className: (a.className || '').toString().slice(0, 80)}; }"""

CHIP_JS = """(label) => {
  for (const b of document.querySelectorAll('button[aria-expanded]')) {
    const a = b.getAttribute('aria-label') || '';
    if (a.startsWith('Clear ')) continue;
    if (a.startsWith(label + ':')) {
      const r = b.getBoundingClientRect();
      return {aria: a, text: (b.innerText || '').trim(),
              rect: [Math.round(r.x), Math.round(r.y),
                     Math.round(r.width), Math.round(r.height)]};
    }
  }
  return null;
}"""

CLEAR_JS = """(label) => !!document.querySelector(
  `[aria-label="Clear ${label} filter"]`)"""


def ev(js, arg=None):
    return page.evaluate(js) if arg is None else page.evaluate(js, arg)


def classify(f):
    if f.get("in_audio_node"):
        return "节点本体"
    if f.get("aria") == "Canvas":
        return "Canvas"
    if f.get("tag") == "BODY":
        return "body"
    return "其他"


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

    def select_node():
        for _ in range(3):
            if ev(TOOLBAR_JS):
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

    def set_value():
        c = ev(CHIP_JS, LABEL)
        if not c:
            return None
        xy = [c["rect"][0] + c["rect"][2] // 2, c["rect"][1] + c["rect"][3] // 2]
        page.mouse.click(xy[0], xy[1])
        page.wait_for_timeout(900)
        if not ev(LAYER_OPEN_JS, LABEL):
            return None
        o = page.get_by_text(PICK, exact=True).first
        if not o.count():
            return None
        o.click(timeout=8000)
        page.wait_for_timeout(900)
        return ev(CLEAR_JS, LABEL)

    def chip_value():
        c = ev(CHIP_JS, LABEL)
        return c["text"] if c else None

    runs = []

    # ── 洞 1：`pure_mouse` —— **原样**复现 888 的前置态 ────────────
    # 纯鼠标：点节点中心，**不**碰 set_value、**不**碰任何 focus()
    if not tid:
        out["verdict"] = "插不进音频节点（前置态没成立）"
    else:
        for rep in range(1, REPS + 1):
            rec = {"kind": "pure_mouse", "rep": rep,
                   "precond": "鼠标点节点中心，不设值、不设焦点（888 原样）"}
            c = ev(CENTER_JS, tid)
            if not c:
                rec["verdict"] = "前置态没成立：算不出节点中心"
                runs.append(rec)
                print(f"  !! {rec['verdict']}")
                continue
            page.mouse.click(c[0], c[1])
            page.wait_for_timeout(1200)
            rec["toolbar_before"] = ev(TOOLBAR_JS)
            if not rec["toolbar_before"]:
                rec["verdict"] = "前置态没成立：点节点中心没开出面板"
                runs.append(rec)
                print(f"  !! {rec['verdict']}")
                continue
            rec["layer_open_before"] = ev(LAYER_OPEN_JS, LABEL)
            rec["focus_before"] = ev(FOCUS_JS)
            rec["focus_target_before"] = ev(FOCUS_TARGET_JS)

            page.keyboard.press("Escape")
            page.wait_for_timeout(1200)

            rec["focus_after"] = ev(FOCUS_JS)
            rec["focus_target_after"] = ev(FOCUS_TARGET_JS)
            rec["landing"] = classify(rec["focus_after"])
            rec["toolbar_after"] = ev(TOOLBAR_JS)
            rec["verdict"] = "sampled"
            runs.append(rec)
            print(f"\n[pure_mouse #{rep}] {rec['precond']}")
            print(f"   按前：焦点={rec['focus_before']['aria']!r}"
                  f"/{rec['focus_before']['text']!r}"
                  f"  在节点内={rec['focus_before']['in_audio_node']}"
                  f"  工具条={rec['toolbar_before']}")
            print(f"   按前那个元素：{json.dumps(rec['focus_target_before'], ensure_ascii=False)}")
            print(f"   按后：{rec['landing']}  焦点={rec['focus_after']['aria']!r}"
                  f"  工具条={rec['toolbar_after']}")
            print(f"   按后那个元素：{json.dumps(rec['focus_target_after'], ensure_ascii=False)}")

        # ── 洞 2：`layer_open` + **同一次运行**读值（874 的前置态）──
        for rep in range(1, REPS + 1):
            rec = {"kind": "layer_open_value", "rep": rep,
                   "precond": "设值 → 鼠标点芯片开层（焦点在层内）→ Esc"}
            why = None
            if not select_node():
                why = "节点没选中"
            elif not open_voices():
                why = "音色库没开"
            elif not ev(CLEAR_JS, LABEL) and not set_value():
                why = "芯片设不上值"
            if why:
                rec["verdict"] = f"前置态没成立：{why}"
                runs.append(rec)
                print(f"  !! [layer_open_value #{rep}] {rec['verdict']}")
                continue
            c = ev(CHIP_JS, LABEL)
            xy = [c["rect"][0] + c["rect"][2] // 2, c["rect"][1] + c["rect"][3] // 2]
            page.mouse.click(xy[0], xy[1])
            page.wait_for_timeout(900)
            rec["layer_open_before"] = ev(LAYER_OPEN_JS, LABEL)
            if not rec["layer_open_before"]:
                rec["verdict"] = "前置态没成立：点芯片后层没开"
                runs.append(rec)
                print(f"  !! [layer_open_value #{rep}] {rec['verdict']}")
                continue
            rec["value_before"] = chip_value()
            rec["focus_before"] = ev(FOCUS_JS)

            page.keyboard.press("Escape")
            page.wait_for_timeout(1200)

            rec["focus_after"] = ev(FOCUS_JS)
            rec["landing"] = classify(rec["focus_after"])
            rec["toolbar_after"] = ev(TOOLBAR_JS)
            rec["layer_open_after"] = ev(LAYER_OPEN_JS, LABEL)
            # 值：**重开**再读（当场读会被「层关了 / 面板收了」污染）
            rec["reopened"] = open_voices()
            if rec["reopened"]:
                rec["value_after"] = chip_value()
                rec["value_survived"] = (rec["value_after"] == rec["value_before"])
            else:
                rec["value_after"] = None
                rec["value_survived"] = None
                rec["verdict"] = ("前置态没成立：Esc 之后音色库没开回来 ⇒ "
                                  "「值还在不在」测不到（**不是**「值没了」）")
            rec["verdict"] = rec.get("verdict", "sampled")
            runs.append(rec)
            print(f"\n[layer_open_value #{rep}] {rec['precond']}")
            print(f"   按前：焦点={rec['focus_before']['aria']!r}"
                  f"  层内={rec['focus_before']['in_listbox']}"
                  f"  层开着={rec['layer_open_before']}  值={rec['value_before']!r}")
            print(f"   按后：{rec['landing']}  焦点={rec['focus_after']['aria']!r}"
                  f"  工具条={rec['toolbar_after']}  层开着={rec['layer_open_after']}")
            print(f"   值：重开={rec['reopened']}  {rec['value_before']!r} → "
                  f"{rec['value_after']!r}  ⇒ "
                  f"{'保留' if rec['value_survived'] else ('被清' if rec['value_survived'] is False else '测不到')}")

        out["runs"] = runs
        summary = {}
        for kind in ("pure_mouse", "layer_open_value"):
            rs = [r for r in runs if r["kind"] == kind]
            ls = [r.get("landing") for r in rs if r.get("landing")]
            vs = [r.get("value_survived") for r in rs
                  if r.get("value_survived") is not None]
            summary[kind] = {
                "landings": ls,
                "n_sampled": len(ls),
                "stable": len(ls) == REPS and len(set(ls)) == 1,
                "landing": ls[0] if ls and len(set(ls)) == 1 else None,
                "value_survived": vs,
                "value_stable": len(vs) == REPS and len(set(vs)) == 1,
            }
        out["summary"] = summary
        print("\n== 汇总 ==")
        for kind, s in summary.items():
            print(f"  {kind:18s} 落点={s['landings']} "
                  f"{'稳定' if s['stable'] else '不稳定/样本不足'}"
                  f"  值存活={s['value_survived']}"
                  f" {'稳定' if s['value_stable'] else ''}")
        out["verdict"] = "sampled"

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n== 已写 {OUT} ==")
