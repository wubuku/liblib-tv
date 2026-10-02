#!/usr/bin/env python3
"""batch 889 源站探针：按 Esc 之后焦点**落哪**，到底由**哪个变量**决定？

## 起因：两次读数不同，我第一次**把原因猜成了结论**

| 来源 | 按 Esc 之前 | 落点 |
|---|---|---|
| 885 / 887 | **程序化聚焦**到 Clear / 芯片 | **该音频节点本体** |
| 888 | **全程没设过焦点**（鼠标点完节点直接按 Esc） | `DIV` / `'Canvas'` |

888 那一跑**只记了 Esc 之后的落点，没记按之前焦点在哪**。所以「两次
读数不同」是**事实**，而「因为焦点起点不同、所以是**另一条路径**」是
**推测** —— §99 第一版把它写成了结论，889 先把它收回。

可能的变量有三个，**一次都没被单独控制过**：

1. 按 Esc 之前**焦点在哪**（芯片 / Clear / 层内 / 压根没聚焦）
2. **筛选层开没开**
3. 面板是不是**刚被鼠标点开**（鼠标点开 vs 键盘打开）

## 这批只做一件事：逐个前置态测，每种 2 次

| 编号 | 前置态 | 怎么建立 | 验什么才算前置态成立 |
|---|---|---|---|
| A | 焦点在**芯片**上 | 程序化 `focus()` 芯片 | `focused=True` 且焦点读数认得出是芯片 |
| B | 焦点在 **Clear** 上 | 程序化 `focus()` Clear | 先让芯片**有值**（Clear 才存在） |
| C | **没设过焦点** | 只用鼠标点节点中心 | 只记读数，**不干预**（888 的前置态） |
| D | 焦点在**筛选层内** | 鼠标点芯片开层 | 层开着 **且** 焦点 `in_listbox` |

⚠️ 每种都必须**从零重建前置态**（Esc 之后面板**真卸载**，888 实测），
重建路径：选中节点 → 开音色库 → 给芯片**设一个值** → 按前置态设焦点。
**每一次 Esc 之前都要把 `focus_before` 记进结果** —— 这正是 888 漏掉的。

## 结论口径

- 落点分四类：`节点本体`（`in_audio_node=True`）/ `Canvas` / `body` / `其他`
- **只有 2/2 同一类**才写「该前置态 ⇒ 该落点」
- 两次不一样就记「**不稳定**」，**不许**取多数表决当结论

## 计费边界

只点「音频」入口、点画布空白、点/聚焦节点本体、开「音色」、点**筛选**芯片、
点筛选选项、按键。**绝不**点生成/发送/购买/充值，**也绝不**点音色库网格里
的音色 chip 本身（那是另一批控件）。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe889_esclanding_src.py
"""

import json

OUT = "/tmp/b889-src-esclanding.json"
LABEL = "性别"
PICK = "男"
REPS = 2

# ⚠️ 焦点读数**必须带三样**：tag / aria / 在不在音频节点内。
# 只印 aria 那一版在复刻侧把「落对了」显示成「没落」（888 收尾记的坑）。
FOCUS_JS = """() => { const a = document.activeElement;
  if (a === document.body) return {tag: 'BODY', aria: '(body)',
                                   in_audio_node: false, in_listbox: false};
  return {tag: a.tagName,
          aria: a.getAttribute('aria-label') || '',
          text: (a.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 20),
          in_audio_node: !!(a.closest && a.closest(
            '.react-flow__node-audio')),
          in_listbox: !!(a.closest && a.closest('[role=listbox]'))}; }"""

TOOLBAR_JS = """() => !!document.querySelector('button[aria-label^="音色"]')"""
VOICES_JS = """() => [...document.querySelectorAll('*')].some(e =>
  (e.innerText||'').trim() === '全音色' && !e.querySelector('*'))"""

# 筛选层开没开（888 只查了面板在不在，没查**层**）
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

FOCUS_CHIP_JS = """(label) => {
  for (const b of document.querySelectorAll('button[aria-expanded]')) {
    const a = b.getAttribute('aria-label') || '';
    if (a.startsWith('Clear ')) continue;
    if (a.startsWith(label + ':')) {
      b.focus();
      return {focused: document.activeElement === b, aria: a};
    }
  }
  return {no_chip: true};
}"""

FOCUS_CLEAR_JS = """(label) => {
  const b = document.querySelector(`[aria-label="Clear ${label} filter"]`);
  if (!b) return {no_clear: true};
  b.focus();
  return {focused: document.activeElement === b,
          aria: b.getAttribute('aria-label') || ''};
}"""

CLEAR_JS = """(label) => !!document.querySelector(
  `[aria-label="Clear ${label} filter"]`)"""


def ev(js, arg=None):
    return page.evaluate(js) if arg is None else page.evaluate(js, arg)


def classify(f):
    """落点分四类。**不许**用 aria 字符串相等来判「是节点本体」——
    节点 testid 逐轮变，判据必须钉**身份**（`in_audio_node`）不钉字面量。"""
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
        """先验旁证（888 定）：开着就直接用，否则点节点中心，**绝不**先点空白
        —— Esc 之后节点已取消选中，多余的「点空白」若落在节点上就变成
        「选中→立刻取消」，净效果是把面板关掉。"""
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
        """给筛选芯片**设一个值**（点筛选芯片开层 → 点选项）。
        这是 887 已取过样的路径，**不是**点音色库网格里的音色 chip。"""
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

    def rebuild():
        """从零重建前置态。**每一步都验**，失败就记账不硬试。"""
        if not select_node():
            return "重建失败：节点没选中"
        if not open_voices():
            return "重建失败：音色库没开"
        # 设值（Clear 存在 ⇒ 有值）。已经是「有值」就不重复点。
        if not ev(CLEAR_JS, LABEL):
            if not set_value():
                return "重建失败：芯片设不上值"
        if ev(LAYER_OPEN_JS, LABEL):
            return "重建失败：层还开着（起点不干净）"
        return None

    def set_pre(kind):
        """建立四种前置态之一，**并验**。返回 (ok, 说明)。"""
        if kind == "chip":
            r = ev(FOCUS_CHIP_JS, LABEL)
            if not r.get("focused"):
                return False, f"聚焦点到芯片失败 {r}"
            return True, "程序化聚焦芯片"
        if kind == "clear":
            if not ev(CLEAR_JS, LABEL):
                return False, "Clear 不存在（芯片没值）"
            r = ev(FOCUS_CLEAR_JS, LABEL)
            if not r.get("focused"):
                return False, f"聚焦点到 Clear 失败 {r}"
            return True, "程序化聚焦 Clear"
        if kind == "nofocus":
            # ⚠️ **只记读数、绝不干预**：888 那一跑就是「鼠标点完节点直接按
            # Esc」。这里已经由 rebuild() 选中了节点，所以**什么都不做**，
            # 让焦点停在它自己落的地方。
            return True, "不干预（rebuild 之后直接按）"
        if kind == "layer_open":
            c = ev(CHIP_JS, LABEL)
            if not c:
                return False, "找不到筛选芯片"
            xy = [c["rect"][0] + c["rect"][2] // 2,
                  c["rect"][1] + c["rect"][3] // 2]
            page.mouse.click(xy[0], xy[1])
            page.wait_for_timeout(900)
            if not ev(LAYER_OPEN_JS, LABEL):
                return False, "点芯片后层没开"
            return True, "鼠标点芯片开层"
        return False, f"未知前置态 {kind}"

    KINDS = ["chip", "clear", "nofocus", "layer_open"]
    runs = []

    if not tid:
        out["verdict"] = "插不进音频节点（前置态没成立）"
    else:
        for kind in KINDS:
            for rep in range(1, REPS + 1):
                rec = {"kind": kind, "rep": rep}
                why = rebuild()
                if why:
                    rec["verdict"] = f"前置态没成立：{why}"
                    runs.append(rec)
                    print(f"  !! [{kind} #{rep}] {rec['verdict']}")
                    continue
                ok, how = set_pre(kind)
                rec["precond"] = how
                if not ok:
                    rec["verdict"] = f"前置态没成立：{how}"
                    runs.append(rec)
                    print(f"  !! [{kind} #{rep}] {rec['verdict']}")
                    continue
                page.wait_for_timeout(350)
                # ⚠️⚠️ **按 Esc 之前**的焦点读数 —— 888 漏掉的就是这一行。
                rec["focus_before"] = ev(FOCUS_JS)
                rec["layer_open_before"] = ev(LAYER_OPEN_JS, LABEL)
                rec["toolbar_before"] = ev(TOOLBAR_JS)

                page.keyboard.press("Escape")
                page.wait_for_timeout(1200)

                rec["focus_after"] = ev(FOCUS_JS)
                rec["landing"] = classify(rec["focus_after"])
                rec["toolbar_after"] = ev(TOOLBAR_JS)
                rec["layer_open_after"] = ev(LAYER_OPEN_JS, LABEL)
                rec["verdict"] = "sampled"
                runs.append(rec)
                print(f"\n[{kind} #{rep}] {how}")
                print(f"   按前：焦点={rec['focus_before']['aria']!r}"
                      f"/{rec['focus_before']['text']!r}"
                      f"  在节点内={rec['focus_before']['in_audio_node']}"
                      f"  层内={rec['focus_before']['in_listbox']}"
                      f"  层开着={rec['layer_open_before']}")
                print(f"   按后：{rec['landing']}"
                      f"  焦点={rec['focus_after']['aria']!r}"
                      f"  工具条={rec['toolbar_after']}"
                      f"  层开着={rec['layer_open_after']}")

        out["runs"] = runs
        # 汇总：**只有 2/2 同一类**才算「该前置态 ⇒ 该落点」
        summary = {}
        for kind in KINDS:
            ls = [r.get("landing") for r in runs if r["kind"] == kind]
            sampled = [x for x in ls if x]
            summary[kind] = {
                "landings": ls,
                "n_sampled": len(sampled),
                "stable": len(set(sampled)) == 1 and len(sampled) == REPS,
                "landing": sampled[0] if len(set(sampled)) == 1 else None,
            }
        out["summary"] = summary
        print("\n== 汇总 ==")
        for kind in KINDS:
            s = summary[kind]
            mark = "OK " if s["stable"] else ("?? " if s["n_sampled"] else "—  ")
            print(f"  {mark}{kind:11s} 落点={s['landings']}"
                  f"  {'稳定' if s['stable'] else '不稳定/样本不足'}")
        out["verdict"] = "sampled"

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n== 已写 {OUT} ==")
