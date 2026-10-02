#!/usr/bin/env python3
"""batch 883 源站探针：Esc 之后**音频节点还在不在选中态**？

## 这条比「焦点落在哪」更根本

882 查清了复刻侧的根因：`@xyflow/react` 的 `useNodesSelection` 在节点
**失去选中态**时 `requestAnimationFrame(() => nodeRef.blur())`。

那么问题就来了：**为什么源站没这个问题？** 三种可能，处置完全不同：

① 源站 Esc **不取消**节点选中 ⇒ 复刻「取消选中」本身是**更根本的差异**，
   我 882 的双 rAF 是在**治症状**
② 源站也取消选中，但它的节点实现**不带 blur** ⇒ 复刻是**库行为**差异，
   治症状可接受
③ 源站取消了选中、也 blur 了，但 blur 之后**有别的东西**把焦点抢回来
   ⇒ 复刻缺的是那个「抢回来」的东西

**三选一必须量，不许推测**（§69）。所以这批只问两个问题：

① 焦点在 Clear 上按 Esc 之后，音频节点**还是不是选中态**？
② 选中态用**什么**判？（类名？aria？边框？`data-*`？—— 不能靠猜）

⚠️ 判据必须**先量**出来再用。源站的节点 DOM 我只见过 `BUTTON`，类名片段
是 `…-node-…`；**选中态的标记形式从未量过**。所以本探针**先 dump 选中态
与未选中态两种状态下的节点属性差分**，再据此定判据。

## 边界

只点「音频」入口、选中节点、开「音色」、点筛选钮、点选项、按键。
**绝不**点生成/发送/购买/充值，**也绝不**点音色 chip 本身。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe883_escselect_src.py
"""

import json

OUT = "/tmp/b883-src-escselect.json"
LABEL = "性别"
PICK = "男"

# 节点的一切可观察属性（**两种状态都 dump**，靠差分找「选中」的标记）
NODE_DUMP_JS = """() => {
  const n = [...document.querySelectorAll('[aria-label^="音频 node"]')][0]
    || [...document.querySelectorAll('*')].find(e =>
         /node/.test((e.getAttribute('aria-label') || ''))
         && /音频/.test((e.getAttribute('aria-label') || '')));
  if (!n) return {no_node: true};
  const r = n.getBoundingClientRect();
  const cs = getComputedStyle(n);
  const attrs = {};
  for (const a of n.attributes) attrs[a.name] = (a.value || '').slice(0, 80);
  return {
    tag: n.tagName,
    aria: n.getAttribute('aria-label') || '',
    className: ((n.className || '') + ''),
    attrs,
    rect: [Math.round(r.x), Math.round(r.y),
           Math.round(r.width), Math.round(r.height)],
    border: cs.borderColor + ' / ' + cs.borderWidth,
    outline: cs.outlineColor + ' / ' + cs.outlineWidth,
    boxShadow: (cs.boxShadow || '').slice(0, 120),
    background: (cs.backgroundColor || ''),
    /* 祖先链上的类名 —— 选中框常画在**外层**容器上 */
    anc: (() => { const out = []; let p = n.parentElement;
      for (let i = 0; i < 5 && p; i++, p = p.parentElement) {
        const pr = p.getBoundingClientRect();
        const pcs = getComputedStyle(p);
        out.push({tag: p.tagName,
                  cls: ((p.className || '') + '').slice(0, 90),
                  border: pcs.borderColor + ' / ' + pcs.borderWidth,
                  boxShadow: (pcs.boxShadow || '').slice(0, 100),
                  rect: [Math.round(pr.x), Math.round(pr.y),
                         Math.round(pr.width), Math.round(pr.height)]});
      } return out; })(),
  };
}"""

FOCUS_JS = """() => { const a = document.activeElement;
  if (a === document.body) return {tag: 'BODY', aria: '(body)'};
  return {tag: a.tagName,
          aria: a.getAttribute('aria-label') || '',
          is_audio_node: !!(a.closest &&
            a.closest('[aria-label^="音频 node"]'))}; }"""

VOICES_JS = """() => [...document.querySelectorAll('*')].some(e =>
  (e.innerText||'').trim() === '全音色' && !e.querySelector('*'))"""


def ev(js, arg=None):
    return page.evaluate(js) if arg is None else page.evaluate(js, arg)


def diff(a, b):
    """两个 dump 之间的**差分** —— 选中态的标记形式就藏在这里面。
    只列**值不一样**的键（嵌套 dict 递归一层）。"""
    if not isinstance(a, dict) or not isinstance(b, dict):
        return {"before": a, "after": b} if a != b else {}
    out = {}
    for k in a:
        if k in ("anc", "attrs"):
            continue
        if a[k] != b.get(k):
            out[k] = {"未选中时": a[k], "Esc之后": b.get(k)}
    for sub in ("attrs", "anc"):
        if sub not in a or sub not in b:
            continue
        if isinstance(a[sub], dict) and isinstance(b[sub], dict):
            for k in a[sub]:
                if a[sub][k] != b[sub].get(k):
                    out[f"{sub}.{k}"] = {"未选中时": a[sub][k],
                                         "Esc之后": b[sub].get(k)}
        elif isinstance(a[sub], list) and isinstance(b[sub], list):
            for i, (x, y) in enumerate(zip(a[sub], b[sub])):
                for k in x:
                    if k != "rect" and x[k] != y.get(k):
                        out[f"{sub}[{i}].{k}"] = {"未选中时": x[k],
                                                 "Esc之后": y.get(k)}
    return out


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

    # ── 阶段 A：**未选中**时的节点 dump（基线）────────────────
    # ⚠️⚠️ 第一版这里按 **Escape** 取消选中，结果阶段 A 与阶段 B 的 dump
    #    **完全相同**（差分 0 处），于是打出了「判据盲区」。
    #    查下去发现是**前置态没成立**：源站 Escape 很可能**根本不取消节点选中**
    #    —— 也就是这批本来要查的那件事。于是「未选中」那一档压根没建起来，
    #    两档都是选中态，差分自然是 0。
    #    ⇒ 第四次「前置态没成立被当成数据」。而且它伪装成「判据盲区」——
    #    差分 0 既可能是「没有选中态这个维度」，也可能是「两档一样」。
    #
    # 第二版改用**旁证**判「未选中」，不再靠读 class 猜：
    #   节点**选中**时音频生成面板（NodeToolbar）在 DOM 里；
    #   **未选中**时它不在。
    # 每次切换之后都**验一遍**这个旁证，不成立就记账，不往下走。
    def toolbar_present():
        return bool(page.locator('button[aria-label^="音色"]').count())

    def click_blank():
        """点**空白画布**取消选中（Escape 在源站不管用，见上）。"""
        spot = ev("""() => {
          for (const [x, y] of [[1180, 980], [1240, 900], [1100, 1050],
                                [1280, 820], [300, 1000]]) {
            const t = document.elementFromPoint(x, y);
            if (t && t.closest('.react-flow__pane')
                && !t.closest('.react-flow__node')) return [x, y];
          }
          return null;
        }""")
        if not spot:
            return "找不到空白画布落点"
        page.mouse.click(spot[0], spot[1])
        page.wait_for_timeout(900)
        return None

    # 先确认「点空白能取消选中」这件事**本身**成立
    why_a = click_blank()
    sel_after_blank = toolbar_present()
    out["probe_blank_clears_selection"] = {
        "why": why_a, "toolbar_present_after_blank": sel_after_blank}
    print(f"\n== 阶段 A 前置校验：点空白后工具条还在吗 "
          f"{sel_after_blank}（应为 False 才算取消成功）==")
    if sel_after_blank:
        out["verdict"] = ("前置态没成立：点空白**没能**取消选中"
                          "（工具条还在）⇒ 整个 A/B/C 三阶段都测不了，"
                          "**不是**「源站没有选中态」")
        print("  !! " + out["verdict"])
    else:
        d_unsel = ev(NODE_DUMP_JS)
        out["dump_unselected"] = d_unsel
        print("\n== 阶段 A：未选中时的节点 ==")
        if d_unsel.get("no_node"):
            print("  !! 找不到节点 ⇒ 判据盲区（不是「没有节点」）")
        else:
            print(f"   tag={d_unsel['tag']} aria={d_unsel['aria']!r}")
            print(f"   class={d_unsel['className'][:90]!r}")
            print(f"   border={d_unsel['border']}  "
                  f"outline={d_unsel['outline']}")
            print(f"   boxShadow={d_unsel['boxShadow'][:80]!r}")

    # ── 阶段 B：**选中**时的节点 dump ────────────────────────
    if tid and not out.get("verdict"):
        pt2 = ev("""(tid) => {
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
        if pt2:
            page.mouse.click(pt2[0], pt2[1])
            page.wait_for_timeout(1200)
        out["toolbar_present_when_selected"] = toolbar_present()
        # ⚠️⚠️ 第二跑栽在这：第一版**只是把旁证打印出来**（`工具条在吗 False`），
        #   然后**照样往下跑**，于是阶段 B 拿到的其实还是**未选中**那一档
        #   ⇒ 差分又是 0 ⇒ 又打出一句「判据盲区」。
        #   旁证既然已经拿到了，就该**拿来把关**：不成立就**记账退出**，
        #   不许把「没选中」的状态当成「选中态的数据」往下传。
        #   （这跟 876c 那个 `reopened=False` 记成「值没了」同族。）
        if not out["toolbar_present_when_selected"]:
            out["verdict"] = ("前置态没成立：点节点**没能选中**"
                              "（工具条不在）⇒ 阶段 B 的 dump 还是**未选中**"
                              "那一档 ⇒ 差分必然是 0。"
                              "**不是**「源站没有选中态」，也不是「判据盲区」。"
                              "根子在「怎么在源站可靠地选中一个节点」"
                              "这个**前置问题**本身还没解决 —— "
                              "不许靠换落点反复硬试（§77 机制未验死之前"
                              "不许改判据）")
            print("  !! " + out["verdict"])
        d_sel = ev(NODE_DUMP_JS)
        out["dump_selected"] = d_sel
        print(f"\n== 阶段 B：选中时的节点（工具条在吗 "
              f"{out['toolbar_present_when_selected']}，应为 True）==")
        if d_sel.get("no_node"):
            print("  !! 找不到节点")
        else:
            print(f"   class={d_sel['className'][:90]!r}")
            print(f"   border={d_sel['border']}  "
                  f"outline={d_sel['outline']}")
            print(f"   boxShadow={d_sel['boxShadow'][:80]!r}")

    dd = {}
    if out.get("verdict"):
        pass                       # 前置态没成立 ⇒ **不许**算差分
    elif out.get("dump_unselected") and out.get("dump_selected"):
        dd = diff(out["dump_unselected"], out["dump_selected"])
        out["diff_unselected_vs_selected"] = dd
        print(f"\n== 差分（未选中 vs 选中）{len(dd)} 处 ==")
        for k, v in dd.items():
            print(f"   {k}:\n      未选中={str(v['未选中时'])[:70]!r}"
                  f"\n      选中  ={str(v['Esc之后'])[:70]!r}")

    # ── 阶段 C：开音色库 → 选值 → Clear 上按 Esc → 再 dump ──────
    if tid and dd is not None and not out.get("verdict"):
        def reselect():
            p = ev("""(tid) => {
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
            if p:
                page.mouse.click(p[0], p[1])
                page.wait_for_timeout(1500)
            return True

        for _ in range(3):
            if ev(VOICES_JS):
                break
            reselect()
            vt = page.locator('button[aria-label^="音色"]')
            if vt.count():
                vt.first.click(timeout=8000)
                page.wait_for_timeout(1800)
        rec = {"voices_open": ev(VOICES_JS)}
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
        rec["clear_shown"] = bool(ev(
            """(label) => !!document.querySelector(
                 `[aria-label="Clear ${label} filter"]`)""", LABEL))
        rec["dump_before_esc"] = ev(NODE_DUMP_JS)
        rec["focus_before"] = ev(FOCUS_JS)
        if rec["clear_shown"]:
            ev("""(label) => {
              const b = document.querySelector(
                `[aria-label="Clear ${label} filter"]`);
              if (b) b.focus();
            }""", LABEL)
            page.keyboard.press("Escape")
            page.wait_for_timeout(1000)
        rec["dump_after_esc"] = ev(NODE_DUMP_JS)
        rec["focus_after"] = ev(FOCUS_JS)
        d_after = rec["dump_after_esc"]
        if d_after.get("no_node"):
            rec["verdict"] = "前置态没成立：Esc 之后找不到节点（测不到，不是「没了」）"
        else:
            de = diff(rec["dump_before_esc"], d_after)
            rec["diff_before_vs_after_esc"] = de
            # 判据**由阶段 A/B 的差分推出来**，不是先写好再来套
            keys = set(dd.keys())
            still_selected = [k for k in keys
                              if de.get(k, {}).get("Esc之后")
                              == dd[k]["选中"]
                              and de.get(k, {}).get("未选中时")
                              == dd[k]["未选中时"]]
            rec["keys_that_still_look_selected"] = still_selected
            rec["keys_that_changed_toward_unselected"] = [
                k for k in de
                if k in dd and de[k]["Esc之后"] == dd[k]["未选中时"]]
            print(f"\n== 阶段 C：Clear 上按 Esc ==")
            print(f"   焦点：{rec['focus_before']['aria']!r} → "
                  f"{rec['focus_after']['aria']!r}")
            print(f"   Esc 前后节点差分 {len(de)} 处")
            print(f"   **仍与「选中」一致**的标记：{still_selected}")
            print(f"   **变回「未选中」**的标记："
                  f"{rec['keys_that_changed_toward_unselected']}")
            if still_selected:
                rec["verdict"] = (
                    "源站 Esc 之后**节点仍处于选中态** ⇒ ① 号解释成立："
                    "复刻「取消选中」才是**更根本的差异**，"
                    "882 的双 rAF 是在**治症状**。")
            elif rec["keys_that_changed_toward_unselected"]:
                rec["verdict"] = (
                    "源站 Esc 之后节点**变回未选中**，但焦点仍落在它上面 ⇒ "
                    "③ 号解释成立：源站有「blur 之后把焦点抢回来」的东西，"
                    "复刻缺的是它。")
            else:
                rec["verdict"] = (
                    "两阶段都没量出可用的「选中」标记 ⇒ **判据盲区**，"
                    "不是「源站没有选中态」。要换个标记维度（截图/伪元素）重测。")
            print(f"\n== {rec['verdict']}")
        out["esc"] = rec
    # ⚠️⚠️ 第一版这里是**无条件** `out["verdict"] = "sampled"` ——
    #   前面记的「前置态没成立」会被**这一行冲掉**，读 JSON 的人只看到
    #   `verdict: sampled`，以为整批跑成了。这跟 876c 那个
    #   `reopened=False` 记成「值没了」是同一种病：**成功的标签盖掉了
    #   失败的记录**。改成**已经有记账就不覆盖**。
    if not out.get("verdict"):
        out["verdict"] = "sampled"
    else:
        print(f"\n（本批**不**标 sampled —— 已有前置态记账："
              f"{out['verdict'][:60]}…）")

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n== 已写 {OUT} ==")
