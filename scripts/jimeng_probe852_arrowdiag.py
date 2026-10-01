#!/usr/bin/env python3
"""batch 852 诊断：③ 方向键为什么一直测不到（**每一步都交出原因**）。

850 和 851 在「方向键」这一项上都失败，而两批的失败信息**都是空的** ——
851b 的 refocus 只有在**早退**分支带 `why`，走完到最后的分支只 `return {ok: ...}`，
于是失败时打印出来的是 `why=None`。849 早就写过：
**只交一个 `ok:False` 等于交一张没有地址的病历**。这一轮就是去把病历补全。

量 6 个层（视频生成面板 4 + 音频 2），每一步都记：

  1. 标记在不在（`[data-probe850]`）
  2. 标记元素的 tag/role/矩形/可见性
  3. 层里**可聚焦项**有几个，分别是谁（disabled 的不算 —— 846 记过
     「disabled 按钮不能接收焦点」，846b 当时就是被这一条绊倒的）
  4. `focus()` 之后 `activeElement` 是谁、在不在层内、层矩形多大
  5. 若在层内：按 ArrowDown ×4 的**完整轨迹**
  6. 若不在层内：**为什么**（层矩形 vs 焦点矩形，差多少）

只诊断，不改产品。
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jimeng_kb_probe_lib import (  # noqa: E402
    FOCUS_JS, SNAP_JS, UNMARK_JS, ensure_open, mark_layer,
)

MAX_KEYS = 4
page.set_viewport_size({"width": 1512, "height": 1200})

# 一次性把「层里有什么 + 焦点在哪 + 为什么不在层内」全交出来
DIAG_JS = """(lay) => {
  const L = document.querySelector('[data-probe850]');
  const a = document.activeElement;
  const out = {marked: !!L, focus_who: null, items: [], why_not: null};
  if (a && a !== document.body) {
    out.focus_who = {tag: a.tagName,
                     al: (a.getAttribute('aria-label') || '').slice(0, 40),
                     tid: a.getAttribute('data-testid') || '',
                     role: a.getAttribute('role') || '',
                     tabindex: a.getAttribute('tabindex'),
                     txt: (a.innerText || '').trim().slice(0, 16),
                     rect: (() => { const r = a.getBoundingClientRect();
                        return [Math.round(r.x), Math.round(r.y),
                                Math.round(r.width), Math.round(r.height)]; })()};
  }
  if (!L) { out.why_not = '层上没有标记（data-probe850 不存在）'; return out; }
  const lr = L.getBoundingClientRect();
  out.layer = {tag: L.tagName, role: L.getAttribute('role') || '',
               cls: (L.className || '').toString().replace(/\\s+/g, ' ').slice(0, 40),
               rect: [Math.round(lr.x), Math.round(lr.y),
                      Math.round(lr.width), Math.round(lr.height)],
               display: getComputedStyle(L).display,
               visibility: getComputedStyle(L).visibility};
  // 层里所有**可能**可聚焦的，逐个报「能不能聚焦」
  const cand = L.querySelectorAll('button,[href],input,select,textarea,'
                                + '[tabindex],[role=option],[role=menuitem],'
                                + '[contenteditable]');
  for (const e of cand) {
    const r = e.getBoundingClientRect();
    out.items.push({
      tag: e.tagName, role: e.getAttribute('role') || '',
      al: (e.getAttribute('aria-label') || '').slice(0, 30),
      txt: (e.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 14),
      tabindex: e.getAttribute('tabindex'),
      disabled: !!e.disabled,
      aria_disabled: e.getAttribute('aria-disabled'),
      on_screen: r.width >= 1 && r.height >= 1,
      // ⚠️⚠️ **不许真的 focus 来试探**（batch 852 修正）。第一版这里
      //    `e.focus(); return document.activeElement === e` ——
      //    遍历下来 `activeElement` 就停在**最后一个**能聚焦的项上，
      //    「起点」被诊断本身改掉了，于是 `moved` 判错
      //    （音频·音色模型只有 2 项，起点被推到第 2 项 ⇒ 再按方向键
      //    无处可去 ⇒ 报 moved=False，**假阴**）。
      //    846 早就写过同一件事：判断可聚焦性**不能真的去 focus**。
      //    这里改成**纯属性推断**：disabled / aria-disabled / tabindex=-1 /
      //    不在屏上，四条任一命中就不可聚焦。
      focusable: !e.disabled
                 && e.getAttribute('aria-disabled') !== 'true'
                 && e.getAttribute('tabindex') !== '-1'
                 && r.width >= 1 && r.height >= 1,
    });
  }
  out.n_items = out.items.length;
  out.n_focusable = out.items.filter(i => i.focusable).length;
  if (a && a !== document.body) {
    const r = a.getBoundingClientRect();
    const inside = r.x >= lr.x - 1 && r.y >= lr.y - 1
                && r.right <= lr.x + lr.width + 1
                && r.bottom <= lr.y + lr.height + 1;
    if (!inside) {
      out.why_not = `焦点矩形 ${JSON.stringify(out.focus_who.rect)} 不在层矩形 `
        + `${JSON.stringify(out.layer.rect)} 内`
        + (L.contains(a) ? '（**但它确实是层的后代** ⇒ 只是矩形超出了层）' : '');
    }
  }
  return out;
}"""


def open_and_probe(name, trig_aria):
    print("=" * 76)
    print(f"【{name}】{trig_aria!r}")
    cands = page.evaluate("""(aria) => {
      const out = [];
      for (const l of document.querySelectorAll(`button[aria-label^="${aria}"]`)) {
        const s = getComputedStyle(l);
        const r = l.getBoundingClientRect();
        const x = r.x + r.width/2, y = r.y + r.height/2;
        const t = (document.elementsFromPoint(x, y) || [])[0] || null;
        out.push({al: l.getAttribute('aria-label') || '',
                  ok: s.display !== 'none' && s.visibility !== 'hidden'
                      && r.width > 0 && r.height > 0
                      && x >= 0 && y >= 0 && x <= innerWidth && y <= innerHeight
                      && !!(t && (t === l || l.contains(t)))});
      }
      return out;
    }""", trig_aria)
    usable = [c for c in cands if c["ok"]]
    print(f"   可点的同名触发器 {len(usable)}/{len(cands)}")
    if not usable:
        print("   ⚠ 没有可点的触发器 ⇒ 前置态没成立")
        return {"name": name, "why": "无可点触发器"}
    pt = usable[0]
    r = pt["al"] and None
    rect = page.evaluate("""(aria) => {
      for (const l of document.querySelectorAll(`button[aria-label^="${aria}"]`)) {
        const s = getComputedStyle(l);
        const rr = l.getBoundingClientRect();
        if (s.display === 'none' || s.visibility === 'hidden') continue;
        if (rr.width < 1 || rr.height < 1) continue;
        return [Math.round(rr.x), Math.round(rr.y),
                Math.round(rr.width), Math.round(rr.height)];
      }
      return null;
    }""", trig_aria)
    click_xy = (rect[0] + rect[2] // 2, rect[1] + rect[3] // 2)

    page.mouse.click(*click_xy)
    page.wait_for_timeout(900)
    before = page.evaluate(SNAP_JS)
    m = mark_layer(page, {"role": ""})
    if not m.get("ok"):
        page.mouse.click(*click_xy)
        page.wait_for_timeout(900)
        m = mark_layer(page, {"role": ""})
    if not m.get("ok"):
        print("   ⚠ 打不上标记 ⇒ 认层失败")
        return {"name": name, "why": "认层失败"}
    print(f"   标记: how={m.get('how')} rect={m.get('rect')}")

    # ⭐ 关键：用 ensure_open 把层**开着**，再诊断
    m2 = ensure_open(page, {"role": ""}, click_xy, note="诊断前")
    if not m2.get("ok"):
        print("   ⚠ ensure_open 失败 ⇒ 层打不开")
        return {"name": name, "why": "ensure_open 失败"}
    print(f"   ensure_open: how={m2.get('how')} rect={m2.get('rect')}")

    lay = m2["rect"] + [""]
    # ⚠️ 起点必须**在诊断之前**单独读一次（诊断里要遍历层内所有候选项，
    #    哪怕改成纯属性推断，顺序也可能在未来某版变回 focus 试探；
    #    把起点钉在这里，被诊断的代码就再也碰不到它了）
    start0 = page.evaluate("""() => {
      const a = document.activeElement;
      if (!a || a === document.body) return null;
      return {txt: (a.innerText || '').trim().slice(0, 20),
              al: (a.getAttribute('aria-label') || '').slice(0, 30),
              role: a.getAttribute('role') || '',
              ti: a.getAttribute('tabindex')};
    }""")
    print(f"   ★ 诊断前起点: {start0}")
    diag = page.evaluate(DIAG_JS, lay)
    print(f"   标记在={diag['marked']} 层={diag.get('layer')}")
    print(f"   候选项 {diag.get('n_items')} 个、**当场能聚焦** {diag.get('n_focusable')} 个")
    for i, it in enumerate(diag.get("items", [])[:8]):
        print(f"     [{i}] {it['tag']}/{it['role'] or '-'} al={it['al'][:24]!r} "
              f"ti={it['tabindex']} disabled={it['disabled']} "
              f"on_screen={it['on_screen']} focusable={it['focusable']}")
    print(f"   焦点: {diag.get('focus_who')}")
    print(f"   为什么不在层内: {diag.get('why_not')}")

    rec_extra = None
    # 若此刻焦点已在层内，量 ArrowDown
    seq, moved = [], False
    start = ((start0 or {}).get("txt"),
             ((start0 or {}).get("al") or "")[:24])
    if diag["marked"] and not diag.get("why_not"):
        for _ in range(MAX_KEYS):
            page.keyboard.press("ArrowDown")
            s = page.evaluate(DIAG_JS, lay)
            seq.append({"who": (s.get("focus_who") or {}).get("txt"),
                        "al": ((s.get("focus_who") or {}).get("al") or "")[:24],
                        "in": not bool(s.get("why_not"))})
        # ⚠️⚠️ **必须把按之前的起点算进去**（batch 852 的核心修正）。
        #    原来只对「按完之后」的 4 个点去重：`16:9` → `1` → `1` → `1` → `1`
        #    去重后只有 1 个 ⇒ moved=False。而**第一次移动恰恰发生在
        #    起点 → 第一次之间**，被漏掉了。
        #    源站这四层实测都是「**走一步就停**」：漫游 tabindex（一个 ti=0、
        #    其余 ti=-1）按下 ArrowDown 焦点移到下一项，但**不更新 tabindex**，
        #    于是 ti=-1 的项不在 tab 序里，再按无处可去。
        #    这正是 §64 那条判据的**反向**发作：moved=True 会掩盖「跳格」，
        #    moved=False 会掩盖「动了第一步」。**布尔判据永远要配轨迹。**
        moved = len({(x["who"], x["al"]) for x in seq} | {start}) > 1
        rec_extra = {"start": start, "seq": seq}
        print(f"   起点: who={start[0]!r} al={start[1]!r}")
        print(f"   ArrowDown ×{MAX_KEYS}: moved={moved}（**含起点**）")
        for i, x in enumerate(seq):
            print(f"     {i + 1}: who={x['who']!r} al={x['al']!r} in_layer={x['in']}")
    else:
        print("   ⚠ 焦点不在层内 ⇒ **不按方向键**（按了量的是层外轨迹）")

    page.evaluate(UNMARK_JS)
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)
    return {"name": name, "diag": diag, "seq": seq, "moved": moved,
            "measured": bool(seq),
            "start": (rec_extra or {}).get("start") if diag["marked"]
                      and not diag.get("why_not") else None}


# ══ 源站跑起来 ════════════════════════════════════════════════════════
page.goto(
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create",
    wait_until="domcontentloaded", timeout=90000)
page.wait_for_timeout(10000)
page.set_viewport_size({"width": 1512, "height": 1200})
page.wait_for_timeout(2500)

results = {}
SELECT = """(tid) => {
  const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`)
         || document.querySelector('.react-flow__node');
  if (!n) return null;
  const r = n.getBoundingClientRect();
  const CTRL = 'button,[role=button],a,input,select,textarea';
  for (const [fx, fy] of [[0.5,0.5],[0.5,0.25],[0.25,0.5],[0.75,0.5],
                          [0.5,0.75],[0.2,0.2],[0.8,0.8]]) {
    const x = r.x + r.width*fx, y = r.y + r.height*fy;
    const t = document.elementFromPoint(x, y);
    if (t && n.contains(t) && !t.closest(CTRL)) return [Math.round(x), Math.round(y)];
  }
  return null;
}"""
NODE_TIDS = """() => [...document.querySelectorAll('.react-flow__node')]
  .map(n => n.getAttribute('data-testid') || '')"""


def pick_and_click(tid):
    pt = page.evaluate(SELECT, tid)
    if not pt:
        print(f"!! 选不中 {tid} ⇒ 前置态没成立")
        return False
    page.mouse.click(pt[0], pt[1])
    page.wait_for_timeout(1300)
    return True


# ── 视频生成面板 4 层 ──────────────────────────────────────────────────
for nm, aria in [("视频·模型", "选择模型"), ("视频·尺寸", "视频尺寸选项"),
                 ("视频·模式", "生成模式"), ("视频·时长", "选择视频生成时长")]:
    if pick_and_click("rf__node-node_236ctpehgg"):
        results[nm] = open_and_probe(nm, aria)

# ── 音频生成面板 2 层（源站这一版画布能插音频节点，851a 实测）────────────
before = set(page.evaluate(NODE_TIDS))
ab = page.locator('button[aria-label="音频"]')
if ab.count():
    ab.first.click(timeout=10000)
    page.wait_for_timeout(2500)
    new = [t for t in page.evaluate(NODE_TIDS) if t not in before]
    print(f"\n== 插入音频节点: {new} ==")
    if new:
        for nm, aria in [("音频·音色模型", "选择模型"),
                         ("音频·生成模式", "音频生成")]:
            if pick_and_click(new[0]):
                results[nm] = open_and_probe(nm, aria)
    else:
        print("!! 插不出音频节点（前置态没成立）")
else:
    print("\n!! 左栏没有音频按钮")

with open("/tmp/b852-arrowdiag.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print("\n明细 /tmp/b852-arrowdiag.json")
