#!/usr/bin/env python3
"""batch 884 源站探针：先把前置问题解决 —— **在源站可靠地选中一个指定节点**。

## 为什么先做这个

883 的阶段 B 点节点**没选中**（旁证：工具条不在），于是「Esc 之后节点
还在不在选中态」两跑都测不到。那不是「测了没发现」，是**前置态没成立**。

而「点不中」这件事本身我从没查过。883 用的落点算法是「在节点矩形内找一个
`elementFromPoint` 命中节点内部、且不落在任何控件上的点」—— 一路都找不到
的话它返回 `null`，而 883 **只判了 `null` 就继续跑**。所以有两种可能：

  (a) 它返回了坐标，但那个坐标**点在节点上选不中**（节点内部有别的行为）
  (b) 它返回了 `null`（节点整个都被「控件」占满）⇒ 压根没有可点的落点

**这两种必须分开**，否则又是「把够不着写成没有」。

## 本跑只做两件事

① **查清楚 883 那个落点算法到底返回了什么**（有坐标？null？命中的是谁？）
② **逐个策略试选中**，每次都**验旁证**（工具条在不在），
   并且**重复试**——证明是「可靠」而不是「碰巧一次」

试的策略（按「越保守 → 越激进」排）：

| 策略 | 落点 |
|---|---|
| center | 矩形中心 |
| quarter | 四分点（上/左/右/下） |
| corner | 四角内缩 15% |
| edge_mid | 四边中点内缩 6px |
| inner_text | 找节点里**没有子元素**的最深文本节点，取它的中心 |
| by_aria | 直接用 `elementFromPoint` 沿一条**扫描线**找可点位置 |

⚠️ 每次点击后**必须验旁证**；旁证不成立就**记账退出这一策略**，
不许把「没选中」当成「选中了又取消了」。

## 计费边界

只点「音频」入口、点画布空白、点节点本体。**绝不**点生成/发送/购买/充值，
**也绝不**点音色 chip 本身。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe884_selectnode_src.py
"""

import json

OUT = "/tmp/b884-src-selectnode.json"

# ① 复刻 883 的落点算法，**看清它到底返回什么**
WHY_JS = """(tid) => {
  const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
  if (!n) return {no_node: true};
  const r = n.getBoundingClientRect();
  const CTRL = 'button,[role=button],a,input,select,textarea';
  const probes = [];
  let chosen = null;
  for (const [fx, fy] of [[0.5,0.5],[0.5,0.25],[0.25,0.5],[0.75,0.5]]) {
    const x = r.x + r.width * fx, y = r.y + r.height * fy;
    const t = document.elementFromPoint(x, y);
    const hit_node = !!(t && n.contains(t));
    const in_ctrl = !!(t && t.closest(CTRL));
    probes.push({at: [Math.round(x), Math.round(y)],
                 tag: t ? t.tagName : null,
                 cls: t ? ((t.className || '') + '').slice(0, 46) : '',
                 hit_node, in_ctrl,
                 pick: hit_node && !in_ctrl});
    if (hit_node && !in_ctrl && !chosen) chosen = [x, y];
  }
  return {rect: [Math.round(r.x), Math.round(r.y),
                 Math.round(r.width), Math.round(r.height)],
          chosen, probes,
          n_ctrl_inside: n.querySelectorAll(CTRL).length,
          n_children: n.children.length,
          /* 节点里**最深的**无子元素文本节点 —— 「inner_text」策略用 */
          deepest_text: (() => {
            let best = null;
            for (const e of n.querySelectorAll('*')) {
              if (e.children.length) continue;
              const t = (e.innerText || '').trim();
              if (!t) continue;
              const rr = e.getBoundingClientRect();
              if (rr.width < 4 || rr.height < 4) continue;
              best = {text: t.slice(0, 24), tag: e.tagName,
                      xy: [Math.round(rr.x + rr.width / 2),
                           Math.round(rr.y + rr.height / 2)],
                      rect: [Math.round(rr.x), Math.round(rr.y),
                             Math.round(rr.width), Math.round(rr.height)]};
              break;
            }
            return best;
          })()};
}"""

# 各策略的候选落点（**只算坐标，不点**）
STRATS_JS = """(tid) => {
  const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
  if (!n) return {no_node: true};
  const r = n.getBoundingClientRect();
  const CTRL = 'button,[role=button],a,input,select,textarea';
  const box = {l: r.left, t: r.top, w: r.width, h: r.height};
  const out = {};

  out.center = [[Math.round(box.l + box.w/2), Math.round(box.t + box.h/2)]];
  out.quarter = [[0.5,0.25],[0.25,0.5],[0.75,0.5],[0.5,0.75]].map(
    ([fx,fy]) => [Math.round(box.l + box.w*fx), Math.round(box.t + box.h*fy)]);
  out.corner = [[0.15,0.15],[0.85,0.15],[0.15,0.85],[0.85,0.85]].map(
    ([fx,fy]) => [Math.round(box.l + box.w*fx), Math.round(box.t + box.h*fy)]);
  out.edge_mid = [[0.5,0.04],[0.96,0.5],[0.5,0.96],[0.04,0.5]].map(
    ([fx,fy]) => [Math.round(box.l + box.w*fx), Math.round(box.t + box.h*fy)]);

  // inner_text：节点里**没有子元素**的最深文本节点
  let deepest = null;
  for (const e of n.querySelectorAll('*')) {
    if (e.children.length) continue;
    const tt = (e.innerText || '').trim();
    if (!tt) continue;
    const rr = e.getBoundingClientRect();
    if (rr.width < 4 || rr.height < 4) continue;
    if (e.closest(CTRL)) continue;
    deepest = [Math.round(rr.x + rr.width/2), Math.round(rr.y + rr.height/2)];
    break;
  }
  out.inner_text = deepest ? [deepest] : [];

  // scan：沿水平中线**扫**过去，找第一个「命中节点内部且不是控件」的点
  const scan = [];
  for (let i = 1; i <= 19; i++) {
    const x = Math.round(box.l + box.w * i / 20);
    const y = Math.round(box.t + box.h / 2);
    const t = document.elementFromPoint(x, y);
    if (t && n.contains(t) && !t.closest(CTRL)) { scan.push([x, y]); break; }
  }
  out.scan = scan;

  // 记录每个策略第一个落点的**命中对象**（验落点，别盲点）
  for (const k of Object.keys(out)) {
    const xy = out[k] && out[k][0];
    out[k + '_hit'] = xy ? (() => {
      const t = document.elementFromPoint(xy[0], xy[1]);
      if (!t) return null;
      return {tag: t.tagName,
              cls: ((t.className || '') + '').slice(0, 46),
              in_node: n.contains(t),
              in_ctrl: !!t.closest(CTRL)};
    })() : null;
  }
  return out;
}"""

TOOLBAR_JS = """() => !!document.querySelector('button[aria-label^="音色"]')"""

VOICES_JS = """() => [...document.querySelectorAll('*')].some(e =>
  (e.innerText||'').trim() === '全音色' && !e.querySelector('*'))"""


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
    # 插音频节点
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
    if not tid:
        out["verdict"] = "插不进音频节点（前置态没成立）"

    # ── ① 883 的落点算法到底返回了什么 ──────────────────────
    if tid:
        why = ev(WHY_JS, tid)
        out["why_883_algorithm"] = why
        print(f"\n== ① 883 落点算法的诊断 ==")
        if why.get("no_node"):
            print("  !! 找不到节点")
        else:
            print(f"   节点矩形 {why['rect']}  子元素 {why['n_children']} 个  "
                  f"内部控件 {why['n_ctrl_inside']} 个")
            print(f"   算法返回 chosen = {why['chosen']}")
            for p in why["probes"]:
                print(f"     探 {p['at']}: {p['tag']}/{p['cls'][:34]!r} "
                      f"在节点内={p['hit_node']} 在控件内={p['in_ctrl']} "
                      f"选中={p['pick']}")
            dt = why.get("deepest_text")
            print(f"   最深文本节点：{dt}")
            if why["chosen"] is None:
                out["why_883_picked_none"] = True
                print("   ⇒ **883 的算法返回了 null**：节点内部四个探点"
                      "要么不在节点内、要么落在控件上 ⇒ "
                      "**节点没有「非控件落点」**（不是「点不中」）")
            else:
                print("   ⇒ 算法**有**返回坐标；883 的失败另有原因")

        # ── ② 逐策略试选中，每个**重复 2 次**证明可靠 ─────────
        strats = ev(STRATS_JS, tid)
        out["strategies"] = {k: v for k, v in strats.items()
                             if not k.endswith("_hit")}
        print(f"\n== ② 逐策略试选中（每个重复 2 次）==")
        results = {}
        for name in ("center", "quarter", "corner", "edge_mid",
                     "inner_text", "scan"):
            hits = strats.get(name) or []
            hit0 = strats.get(name + "_hit")
            if not hits:
                results[name] = {"ok": False, "why": "算不出落点"}
                print(f"   {name:10s} ⇒ 无落点（{hit0}）")
                continue
            succ = 0
            tries = []
            for rep in range(2):
                # 每轮都先**取消选中**（点空白），确保起点一致
                spot = ev("""() => {
                  for (const [x, y] of [[1180, 980], [1240, 900],
                                        [1100, 1050], [1280, 820]]) {
                    const t = document.elementFromPoint(x, y);
                    if (t && t.closest('.react-flow__pane')
                        && !t.closest('.react-flow__node')) return [x, y];
                  }
                  return null;
                }""")
                if spot:
                    page.mouse.click(spot[0], spot[1])
                    page.wait_for_timeout(800)
                before_sel = ev(TOOLBAR_JS)
                xy = hits[0]
                page.mouse.click(xy[0], xy[1])
                page.wait_for_timeout(1000)
                after_sel = ev(TOOLBAR_JS)
                ok = (not before_sel) and after_sel
                tries.append({"before": before_sel, "after": after_sel,
                              "xy": xy, "ok": ok})
                succ += 1 if ok else 0
            results[name] = {"xy": hits[0], "hit": hit0,
                             "n_success": succ, "n_try": 2, "tries": tries,
                             "reliable": succ == 2}
            print(f"   {name:10s} 落点={hits[0]} 命中={hit0 and hit0['tag']}"
                  f"/{(hit0 or {}).get('cls','')[:26]!r} ⇒ {succ}/2 选中"
                  f"  {'✅ 可靠' if succ == 2 else '❌'}")
        out["strategy_results"] = results
        rel = [k for k, v in results.items() if v.get("reliable")]
        out["reliable_strategies"] = rel
        print(f"\n== 可靠策略：{rel}")
        if not rel:
            out["verdict"] = (
                "**没有可靠策略**（每个策略 2 次都没选中）⇒ "
                "「在源站选中一个指定节点」这个**前置问题本身**"
                "**未解决**（不是「节点选不中」—— 要先查为什么点不中，"
                "比如：是不是要点**别的**元素、或者要先 hover、"
                "或者源站节点的选择是**拖拽**触发的）")
            print("  !! " + out["verdict"])
        else:
            out["verdict"] = "sampled"

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n== 已写 {OUT} ==")
