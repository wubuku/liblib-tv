#!/usr/bin/env python3
"""batch 867：剩下那些 `role="dialog"` 浮层，**逐个先探再判**。

§84 范围限制第二条：复刻里另外几个 `role="dialog"` 浮层
（`JimengAiDrawer` / `JimengNodeSummaryPopover` / `JimengProjectPanel` /
`JimengTextNode` 全屏 / `JimengSubjectNode` 元数据 / `JimengTimelineNode`
全屏）**仍未进状态表、仍未测**。判据（865 的模态语义、866 的分桶）现在
**已经有能力管它们了**，但**没测就是没测**。

## 入口**不靠静态分析**去判（864 的三次翻车都栽在这上面）

每个层给一组**候选选择器**，让浏览器去试。判定只认一件事：
**点完层出没出现**。

    probed             点开了，量到了
    candidates_missed  这组候选一个都没命中 ⇒ **只是这组候选的结论**，
                        **不等于**「UI 上打不开」（第一版把它叫 no_ui_path，
                        那个名字就在替探针的失败背书）
    path_failed        有候选命中但层没出来 ⇒ 前置态没成立，不下结论

⚠️ 「候选都没命中」只说明**这组候选**没命中，不等于「UI 上打不开」——
所以 `no_ui_path` 那一栏必须写明**候选是什么**，让人能接着找。

## 判据与审计**逐字同款**

`paintsOver` / `EDGE` / 4 边全被不透明外人盖住 + 遍历到焦点自己的祖先就停
—— §841 记着这判据被证伪过三次，各写各的等于第四次犯同样的错。
「算不算真模态」用的是 865 那条（定位 + 铺满视口 ≥90% + 不透明，自身**或**
某个孩子），探针 865 拿 4 个已知答案的层实测过零判错。

## `walk` 与 `traps` 是**两个独立测量**

`walk` 只回答「几步进得去」，`traps` 回答「进去之后出不出得来」。
用前者的结果证明后者，就是 864 记的「用 A 的测量证明 B」。

⚠️ 跑法（**自己起浏览器**）：
    /opt/miniconda3/bin/python3 scripts/jimeng_probe867_dialogs.py
**只诊断，不改产品。**
"""

import json
import os
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "http://localhost:4317/jimeng/canvas/demo"
OUT = Path("/tmp/b867-dialogs.json")

# (名字, 层 testid, 候选入口选择器, 备注)
# ⚠️ 节点内浮层的入口**必须先选中节点**才会出现 —— 工具条只在选中时渲染。
#    第一版探针**没做**这一步，于是三个候选全部「没命中」，而那个结论
#    **不是**「UI 上打不开」的证据，是「探针自己没走到前置态」。
#    这跟 864 记的「静态分析判可达性判错三次」是同一类病，只是这次错在
#    探针自己身上。`needs_node: True` 就是给这些层加的前置动作。
CASES = [
    # (名字, 层 testid, 候选入口选择器, 备注, **先选中哪个节点**)
    # ⚠️ 节点内浮层的入口**必须先选中节点**才会出现 —— 工具条只在选中时
    #    渲染。第一版探针**没做**这一步，于是三个候选全部「没命中」，而那个
    #    结论**不是**「UI 上打不开」的证据，是「探针自己没走到前置态」。
    #    这跟 864 记的「静态分析判可达性判错三次」是同一类病，只是这次错在
    #    探针自己身上。
    ("顶栏·节点摘要", "topbar-node-summary",
     ['[data-testid="canvas-node-summary-trigger"]'], "顶栏「节点 2」药丸", None),
    ("顶栏·项目面板", "topbar-project-panel",
     ['[data-testid="canvas-project-trigger"]'], "顶栏「项目」", None),
    ("时间线·全屏", "timeline-fullscreen",
     ['[data-testid="rf__node-timeline"] button[aria-label="全屏编辑"]',
      '[data-testid="rf__node-timeline"] button:has-text("全屏")',
      '[data-testid="rf__node-timeline"] [role="toolbar"] button:nth-child(4)'],
     "时间线节点工具条的全屏入口", '[data-testid="rf__node-timeline"]'),
    ("文本·全屏编辑", "text-fullscreen",
     ['[data-testid^="rf__node-text"] button[aria-label="全屏编辑"]',
      '[data-testid^="rf__node-text"] button:has-text("全屏")'],
     "§83 待办记「源站文本工具条有全屏入口，复刻没有」—— 这里去验一验",
     '[data-testid^="rf__node-text"]'),
    ("主体·元数据编辑器", "subject-metadata-editor",
     ['[data-testid^="rf__node-subject"] button:has-text("添加描述")',
      '[data-testid^="rf__node-subject"] button[aria-label="主体元数据"]'],
     "主体节点的「添加描述…」", '[data-testid^="rf__node-subject"]'),
    ("AI 侧栏", "canvas-agent-drawer",
     ['button[aria-label="与 AI 对话"]',
      '[data-testid="canvas-sidecar-launcher"]'],
     "右下角「与 AI 对话」", None),
]

# ── 判据：与审计逐字同款（覆盖 / 焦点环看不看得见）────────────────────
COVER_JS = r"""
(tid) => {
  const layer = document.querySelector(`[data-testid="${tid}"]`);
  const a = document.activeElement;
  if (!a || a === document.body) return {state: 'body', inside: false};
  const inside = !!(layer && layer.contains(a));
  const nameOf = (e) => (e ? (e.tagName + '/'
      + (e.getAttribute('data-testid') || e.getAttribute('aria-label')
         || (e.className || '').toString().replace(/\s+/g, ' ').slice(0, 40))
      || (e.innerText || '').trim().slice(0, 14)) : null);
  const b = a.getBoundingClientRect();
  if (b.width < 1 || b.height < 1) return {state: 'other', inside: inside};
  const paintsOver = (e, a) => {
    for (let n = e; n && n !== document.body; n = n.parentElement) {
      if (n === a || (n.contains && n.contains(a))) return false;
      const bg = getComputedStyle(n).backgroundColor || '';
      if (bg !== 'rgba(0, 0, 0, 0)'
          && !bg.startsWith('rgba(0, 0, 0, 0)')) return true;
    }
    return false;
  };
  const EDGE = [[b.left - 1, b.top + b.height / 2],
                [b.right + 1, b.top + b.height / 2],
                [b.x + b.width / 2, b.top - 1],
                [b.x + b.width / 2, b.bottom + 1]];
  let edges = 0, firstName = null;
  for (const [ex, ey] of EDGE) {
    const st = document.elementsFromPoint(ex, ey) || [];
    const t = st[0] || null;
    if (!t) continue;
    if (t === a || a.contains(t) || (t.contains && t.contains(a))) continue;
    if (!paintsOver(t, a)) continue;
    edges += 1;
    if (firstName === null) firstName = nameOf(t);
  }
  return {state: inside ? 'inside' : (edges === EDGE.length ? 'covered' : 'other'),
          inside: inside, edges_covered: edges, edges_total: EDGE.length,
          top: firstName, al: (a.getAttribute('aria-label') || '').slice(0, 30),
          tid: a.getAttribute('data-testid') || '',
          w: Math.round(b.width), h: Math.round(b.height)};
}
"""

# ── 865 那条「算不算真模态」（单一来源，同审计）────────────────────────
MODALISH_JS = r"""
(tid) => {
  const el = document.querySelector(`[data-testid="${tid}"]`);
  if (!el) return {modalish: false, why: '层不存在'};
  const vw = innerWidth, vh = innerHeight;
  const opaque = (n) => {
    const bg = getComputedStyle(n).backgroundColor || '';
    return bg !== 'rgba(0, 0, 0, 0)' && !bg.startsWith('rgba(0, 0, 0, 0)');
  };
  const covers = (r) => r.width >= vw * 0.9 && r.height >= vh * 0.9;
  const positioned = (n) => {
    const p = getComputedStyle(n).position;
    return p === 'fixed' || p === 'absolute';
  };
  for (let n = el; n && n !== document.body; n = n.parentElement) {
    const r = n.getBoundingClientRect();
    if (!positioned(n) || !covers(r)) continue;
    if (opaque(n)) return {modalish: true, via: '自身不透明',
                           why: n.tagName + ' 定位且铺满视口、自身不透明'};
    for (const c of n.children) {
      const cr = c.getBoundingClientRect();
      if (covers(cr) && opaque(c))
        return {modalish: true, via: '不透明孩子',
                why: n.tagName + ' 定位且铺满视口，有一个铺满且不透明的孩子'};
    }
  }
  return {modalish: false, why: '没有「定位 + 铺满视口 + 不透明」的祖先'};
}
"""


def n_focusable(pg, tid: str) -> int:
    return pg.evaluate(
        "([t]) => document.querySelector(`[data-testid=\"${t}\"]`)"
        ".querySelectorAll('button:not([disabled]),"
        "[role=\"menuitem\"],input,a[href]').length", [tid])


def walk(pg, tid: str, steps: int = 30) -> dict:
    at_open = pg.evaluate(COVER_JS, tid)
    cov = ins = 0
    first_cov = None
    trace: list[str] = []
    for i in range(1, steps + 1):
        pg.keyboard.press("Tab")
        s = pg.evaluate(COVER_JS, tid)
        if len(trace) < 20:
            trace.append(f"{i}:{s.get('state')}:al={s.get('al') or '-'}")
        if s.get("inside"):
            ins += 1
        if (s.get("edges_covered") == s.get("edges_total")
                and s.get("edges_total")):
            cov += 1
            if first_cov is None:
                first_cov = {"at_tab": i, "al": s.get("al"),
                             "top": s.get("top"),
                             "edges": f"{s.get('edges_covered')}"
                                      f"/{s.get('edges_total')}"}
        if s.get("inside") and i >= 3:
            break
    return {"at_open": at_open, "covered_n": cov, "inside_n": ins,
            "first_cov": first_cov, "trace": trace}


def traps(pg, tid: str, n: int) -> dict:
    """**进去之后**会不会又跑出去 —— `walk` 量不到这个（864 记的教训）。"""
    out_n, seq = 0, []
    for _ in range(n + 2):
        pg.keyboard.press("Tab")
        s = pg.evaluate(COVER_JS, tid)
        seq.append("in" if s.get("inside") else f"OUT({s.get('al') or '-'})")
        if not s.get("inside"):
            out_n += 1
    return {"pressed": n + 2, "escaped": out_n, "seq": seq,
            "traps": out_n == 0}


def main() -> int:
    url = os.environ.get("SNAP_URL", URL)
    res: dict = {"probed": {}, "candidates_missed": [],
                "path_failed": []}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_context(viewport={"width": 1680, "height": 1050}).new_page()
        pg.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(4)

        print("===== 逐个先探再判 =====")
        for name, tid, cands, note, node_sel in CASES:
            print(f"\n-- {name}（{tid}）")
            print(f"   备注：{note}")
            pg.reload(wait_until="domcontentloaded", timeout=60000)
            time.sleep(3.2)
            if node_sel:
                # ⚠️ 前置动作：先**选中**那个节点，工具条才会渲染。
                #    少了这一步，「候选没命中」量的是探针自己没走到前置态。
                n_here = pg.locator(node_sel).count()
                if n_here:
                    bb = pg.locator(node_sel).first.bounding_box()
                    if bb:
                        # 点节点**内容**而不是工具条（点边缘可能正好点在按钮上）
                        cx = bb["x"] + bb["width"] * 0.5
                        cy = bb["y"] + min(bb["height"] * 0.5, 40)
                        hit = pg.evaluate(
                            "([x,y])=>{const e=document.elementFromPoint(x,y);"
                            "return e?e.tagName+'/'+(e.getAttribute('data-testid')"
                            "||e.getAttribute('aria-label')||''):null;}", [cx, cy])
                        print(f"   前置：点选 {node_sel} 中心 "
                              f"({int(cx)},{int(cy)}) 落点={hit}")
                        pg.mouse.click(cx, cy)
                        time.sleep(1.0)
                else:
                    print(f"   前置：页面里**没有** {node_sel} ⇒ "
                          f"这个节点压根不在画布上（前置态没成立，不是「入口没有」）")
            # 先看看页面里到底有没有这些候选（**只问存在性，不点**）
            avail = [(c, pg.locator(c).count()) for c in cands]
            print("   候选存在性：" + "，".join(
                f"{c}={'有' if n else '无'}" for c, n in avail))
            used = None
            for c, n in avail:
                if not n:
                    continue
                try:
                    pg.locator(c).first.click(timeout=5000)
                except Exception:
                    continue
                time.sleep(1.0)
                if pg.locator(f'[data-testid="{tid}"]').count():
                    used = c
                    break
            if used is None:
                if all(n == 0 for _, n in avail):
                    print("   ✗ **一个候选都没命中** ⇒ 这一组候选下 UI 打不开。"
                          "（只说明**这组候选**没命中，不等于「UI 上打不开」）")
                    res["candidates_missed"].append({
                        "name": name, "testid": tid, "candidates": cands,
                        "why": "候选选择器全部未命中 —— 是**候选**的结论，"
                               "不是「UI 打不开」的结论"})
                else:
                    print(f"   ❌ 候选点得到（{[c for c, n in avail if n]}）"
                          f"但层 {tid} 没出现 ⇒ **前置态没成立**，不下结论")
                    res["path_failed"].append({
                        "name": name, "testid": tid,
                        "candidates_present": [c for c, n in avail if n],
                        "why": "点得到但层没出现"})
                continue
            print(f"   ✓ 用 {used!r} 打开了")
            time.sleep(0.8)
            rect = pg.evaluate(
                "([t])=>{const e=document.querySelector("
                "`[data-testid=\"${t}\"]`);const r=e.getBoundingClientRect();"
                "return [Math.round(r.x),Math.round(r.y),"
                "Math.round(r.width),Math.round(r.height)];}", [tid])
            nf = n_focusable(pg, tid)
            mi = pg.evaluate(MODALISH_JS, tid) or {}
            w = walk(pg, tid)
            tr = traps(pg, tid, nf)
            at = w["at_open"] or {}
            takes = at.get("inside") is True
            print(f"   层矩形={rect}  层内可聚焦项={nf}  "
                  f"真模态={mi.get('modalish')}（{mi.get('via') or mi.get('why')}）")
            print(f"   开层时焦点 = {json.dumps(at, ensure_ascii=False)[:150]}")
            print(f"   ⇒ 接管焦点 = **{'是' if takes else '否'}**"
                  f"｜焦点环看不见 {w['covered_n']} 次"
                  f"｜进层后 Tab {tr['pressed']} 次跑出去 {tr['escaped']} 次")
            if w["first_cov"]:
                print(f"   ★ 首个看不见的焦点位 = "
                      f"{json.dumps(w['first_cov'], ensure_ascii=False)}")
            print(f"   轨迹前 5 步：{(w['trace'] or [])[:5]}")
            res["probed"][name] = {
                "testid": tid, "used_selector": used, "rect": rect,
                "focusable_in_layer": nf, "modalish": mi,
                "takes_focus_at_open": takes, "covered_n": w["covered_n"],
                "inside_steps": w["inside_n"], "traps_tab": tr["traps"],
                "escaped_after_enter": tr["escaped"], "trap_seq": tr["seq"],
                "first_covered": w["first_cov"], "focus_at_open": at,
                "trace": w["trace"]}
        b.close()
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n== 已写 {OUT} ==")
    print(f"探到 {len(res['probed'])}｜候选没命中 {len(res['candidates_missed'])}"
          f"｜前置态没成立 {len(res['path_failed'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
