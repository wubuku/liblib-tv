#!/usr/bin/env python3
"""batch 845 源站探针（第三轮）：**先验判据本身站不站得住**，再谈结论。

前两轮各自露了一处硬伤，两处都得排掉，否则 §63 会建立在错前提上：

  ① 第二轮的「进到层里了吗」要求浮层有**不透明底**
     （`bg !== rgba(0,0,0,0)`），而源站搜索面板 `canvas-feature-panel` 恰恰是
     透明底（子元素自己带底色）。于是它被判成"Tab 40 次都没进得去" ——
     **这是判据盲区，不是事实**：第一轮的轨迹明明白白 Tab 第 1 站就落在
     `placeholder="搜索节点..."` 上。
  ② 两轮的「被遮住了吗」都用 `elementFromPoint` + 包含关系判。但报出来的挡路者
     是 `DIV/text-flow-node-full`，而焦点所在那个是
     `rf__node-node_3bfb9r79qe`（role=group）—— 如果前者是后者的**后代**，
     那这个点用户看到的就是焦点自己，**根本不算被遮**。这正是批 843 在复刻侧
     踩过的同一种假缺陷（报了个菜单里压根没有的「音色: 音色库」）。

所以这一轮把判据换成**权威版本**：`document.elementsFromPoint` 返回该点
**完整的绘制栈**，栈顶才是用户真正看到的那个。判据：

    栈顶既不是焦点自己，也不是它的后代 → 那它**才是真的被盖住了**，
    并把盖住它的那个元素记下来。

同时把旧判据的结论**并排**打出来。两个判据在同一步上不一致，本身就是
判据出错的证据 —— 这一条比任何结论都重要。
"""

import json

MAX_TABS = 45

page.goto(
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create",
    wait_until="domcontentloaded", timeout=90000)
page.wait_for_timeout(10000)

# 一次 evaluate 干完一件事：读焦点 + 读绘制栈 + 顺手按"层"判 inside/outside
STEP_JS = """() => {
  const a = document.activeElement;
  if (!a || a === document.body) return {state: 'body'};
  const r = a.getBoundingClientRect();
  const al = (a.getAttribute('aria-label') || '').trim().slice(0, 28);
  const tid = a.getAttribute('data-testid') || '';
  const txt = (a.innerText || a.getAttribute('placeholder') || '')
                .trim().replace(/\\s+/g, ' ').slice(0, 22);
  if (r.width < 1 || r.height < 1)
    return {state: 'other', al, tid, txt, w: Math.round(r.width),
            h: Math.round(r.height)};
  const cx = r.x + r.width / 2, cy = r.y + r.height / 2;

  // ── 权威判据：完整绘制栈，栈顶 = 用户真正看到的 ──────────────────
  const stack = document.elementsFromPoint(cx, cy) || [];
  const top = stack[0] || null;
  const topIsSelfOrKid = !!(top && (top === a || a.contains(top)));
  const covered_strict = !!(top && !topIsSelfOrKid);
  // 祖先不算「盖住」：祖先的底本来就画在下面
  const topIsAncestor = !!(top && top.contains(a));

  // ── 旧判据（复刻侧同款），留着并排比 ─────────────────────────────
  const hit = document.elementFromPoint(cx, cy);
  const covered_soft = !!(hit && !a.contains(hit) && !hit.contains(hit));

  const name = (e) => {
    if (!e) return null;
    const id = e.getAttribute('data-testid') || e.getAttribute('aria-label')
               || (e.className || '').toString().replace(/\\s+/g, ' ').slice(0, 40)
               || (e.innerText || '').trim().slice(0, 14);
    return e.tagName + '/' + id;
  };
  return {state: covered_strict ? 'covered' : 'other', al, tid, txt,
          w: Math.round(r.width), h: Math.round(r.height),
          covered_strict, covered_soft, topIsAncestor,
          top: name(top), soft_hit: name(hit),
          stack_len: stack.length,
          stack_top3: stack.slice(0, 3).map(name),
          // 焦点所在点到最外层的祖先链，好看出它属于哪棵树
          chain: (() => { const c = []; let e = a;
                          for (let i = 0; e && i < 6; i++, e = e.parentElement)
                            c.push(name(e)); return c; })()};
}"""


def tab_through(tag, layer_testids):
    page.evaluate("""() => { const a = document.activeElement;
        if (a && a.blur) a.blur(); return true; }""")
    n_strict = n_soft = 0
    first_strict = first_soft = None
    disagree = []
    entered = None
    for i in range(1, MAX_TABS + 1):
        page.keyboard.press("Tab")
        s = page.evaluate(STEP_JS)
        if s.get("state") == "body":
            continue
        if s.get("covered_strict"):
            n_strict += 1
            if first_strict is None:
                first_strict = {"at_tab": i, "al": s["al"], "tid": s["tid"],
                                "size": f"{s['w']}x{s['h']}", "by": s["top"]}
        if s.get("covered_soft"):
            n_soft += 1
            if first_soft is None:
                first_soft = {"at_tab": i, "al": s["al"], "tid": s["tid"],
                              "by": s["soft_hit"]}
        if bool(s.get("covered_strict")) != bool(s.get("covered_soft")):
            disagree.append({"at_tab": i, "al": s["al"], "tid": s["tid"],
                             "strict": s.get("covered_strict"),
                             "soft": s.get("covered_soft"),
                             "top": s.get("top"), "soft_hit": s.get("soft_hit"),
                             "topIsAncestor": s.get("topIsAncestor"),
                             "chain": s.get("chain")})
        # 「在不在层里」用 testid 判（不靠不透明底 —— 那正是上一轮栽的地方）
        where = page.evaluate("""(tids) => {
          const a = document.activeElement;
          for (const t of tids) {
            const e = document.querySelector(`[data-testid="${t}"]`);
            if (e && e.contains(a)) return t;
          }
          return null;
        }""", layer_testids)
        if where:
            entered = {"at_tab": i, "in": where, "al": s.get("al"),
                       "txt": s.get("txt")}
            break
    return {"state": tag, "entered": entered,
            "entered_tabs": (entered or {}).get("at_tab"),
            "n_strict": n_strict, "n_soft": n_soft,
            "first_strict": first_strict, "first_soft": first_soft,
            "disagree": disagree,
            "why": None if entered else f"Tab {MAX_TABS} 次都没进到 {layer_testids}"}


def reset():
    page.keyboard.press("Escape")
    page.wait_for_timeout(800)


out = {}

# ── ① 顶栏搜索（源站搜索面板 testid 已确认：`canvas-feature-panel`）─────
reset()
t = page.evaluate("""() => {
  const bs = [...document.querySelectorAll('[data-testid=canvas-panel-launcher]')];
  const r = bs[0].getBoundingClientRect();
  return {x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2)};
}""")
page.mouse.click(t["x"], t["y"])
page.wait_for_timeout(1800)
panel = page.evaluate("""() => {
  const e = document.querySelector('[data-testid=canvas-feature-panel]');
  if (!e) return null;
  const r = e.getBoundingClientRect();
  return {tid: e.getAttribute('data-testid'), role: e.getAttribute('role') || '',
          al: e.getAttribute('aria-label') || '',
          tabindex: e.getAttribute('tabindex'),
          w: Math.round(r.width), h: Math.round(r.height),
          x: Math.round(r.x), y: Math.round(r.y),
          focusables: e.querySelectorAll(
            'a[href],button,input,select,textarea,[tabindex]').length};
}""")
print("== 源站搜索面板 ==", json.dumps(panel, ensure_ascii=False))
out["顶栏·搜索"] = {"panel": panel,
                    "probe": tab_through("顶栏·搜索", ["canvas-feature-panel"])}
reset()

# ── ② 画布右键菜单（源站 testid `canvas-context-menu`，role=menu）────────
spot = page.evaluate("""() => {
  for (const [x, y] of [[430, 620], [420, 660], [450, 700]]) {
    const e = document.elementFromPoint(x, y);
    if (!e || e.closest('[data-id]')) continue;
    if (!e.closest('.react-flow__pane, .react-flow__renderer')) continue;
    return {x, y};
  }
  return null;
}""")
if spot:
    page.mouse.click(spot["x"], spot["y"], button="right")
    page.wait_for_timeout(1400)
    menu = page.evaluate("""() => {
      const e = document.querySelector('[data-testid=canvas-context-menu]');
      if (!e) return null;
      const r = e.getBoundingClientRect();
      const items = [...e.querySelectorAll('[role=menuitem],button,li')]
        .map(x => ({tag: x.tagName, role: x.getAttribute('role') || '',
                    al: (x.getAttribute('aria-label') || '').slice(0, 20),
                    txt: (x.innerText || '').trim().slice(0, 14),
                    tabindex: x.getAttribute('tabindex')}));
      return {role: e.getAttribute('role'), w: Math.round(r.width),
              h: Math.round(r.height), items};
    }""")
    print("== 源站右键菜单 ==", json.dumps(menu, ensure_ascii=False)[:700])
    out["画布右键菜单"] = {"menu": menu,
                          "probe": tab_through("画布右键菜单",
                                               ["canvas-context-menu"])}
    reset()

# ── ③ 时间线全屏（源站 `timeline-fullscreen-editor`，role=dialog）───────
node = page.evaluate("""() => {
  for (const n of document.querySelectorAll('[data-id]')) {
    const b = [...n.querySelectorAll('button,[role=menuitem]')]
      .find(x => (x.getAttribute('aria-label') || '').includes('全屏编辑'));
    if (!b) continue;
    const rn = n.getBoundingClientRect(), rb = b.getBoundingClientRect();
    return {nodeId: n.getAttribute('data-id'),
            al: n.getAttribute('aria-label') || '',
            nx: Math.round(rn.x + rn.width / 2), ny: Math.round(rn.y + rn.height / 2),
            bx: Math.round(rb.x + rb.width / 2), by: Math.round(rb.y + rb.height / 2)};
  }
  return null;
}""")
print("== 带「全屏编辑」的节点 ==", json.dumps(node, ensure_ascii=False))
if node:
    page.mouse.click(node["nx"], node["ny"])
    page.wait_for_timeout(1600)
    b2 = page.evaluate("""() => {
      const b = [...document.querySelectorAll('button,[role=menuitem]')]
        .find(x => (x.getAttribute('aria-label') || '').includes('全屏编辑'));
      if (!b) return null;
      const r = b.getBoundingClientRect();
      return {x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2)};
    }""")
    if b2:
        page.mouse.click(b2["x"], b2["y"])
        page.wait_for_timeout(2800)
        out["时间线全屏"] = {"probe": tab_through(
            "时间线全屏", ["timeline-fullscreen-editor"])}

print("\n\n===== 判据自证：新旧两个判据并排 =====")
for k, v in out.items():
    p = v["probe"]
    print("=" * 74)
    print(f"【{k}】进到层里：第 {p.get('entered_tabs')} 次 "
          f"{json.dumps(p.get('entered'), ensure_ascii=False)}")
    print(f"  严格判据（elementsFromPoint 栈顶）报被遮 {p['n_strict']} 次"
          f"  首个={json.dumps(p.get('first_strict'), ensure_ascii=False)}")
    print(f"  旧判据（elementFromPoint+包含）报被遮 {p['n_soft']} 次"
          f"  首个={json.dumps(p.get('first_soft'), ensure_ascii=False)}")
    print(f"  **两判据不一致的步数：{len(p['disagree'])}**")
    for d in p["disagree"][:4]:
        print("     ", json.dumps(d, ensure_ascii=False)[:300])
    if p.get("why"):
        print("  ", p["why"])
