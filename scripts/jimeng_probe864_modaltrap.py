#!/usr/bin/env python3
"""batch 864：复刻侧另外 4 个视口级模态，焦点到底漏不漏 —— **先探再判**。

§81 抓到了 `video-fullscreen-preview` 不困焦点的真缺陷（Tab 走过 22 个被
它自己盖住的控件）。同一批在范围限制里记了 4 个**没探过**的视口级模态。
**未测 ≠ 没缺陷，也 ≠ 没发生** —— 本探针去把它们探出来。

## ⚠️ 本探针的方法论：浏览器是权威，静态分析只是提示

前两版都把「UI 可不可达」判错过，**两个方向都错过**：

- 第 1 版：只数「文件里出现过 `setXxxOpen(true)`」⇒ 把
  `JimengShortcutsPanel` 判成**有入口**。那行是
  `onOpenShortcuts={() => setShortcutsOpen(true)}` —— 只是把回调当 prop
  传下去。
- 第 2 版：改成「prop 传递 ⇒ 不可达」⇒ 把 `JimengProjectInfoModal` 判成
  **不可达**（假阴性）。而 `JimengMoreMenu` 由顶栏「更多」按钮渲染，
  `项目信息` 点得开。
- 第 3 版：加一跳追接收方是否渲染 ⇒ 又把 `JimengHelpMenu` 判成「无条件
  渲染」⇒ 假阳性。它挂在 `{helpOpen ? (...) : null}` 下面，而我那个
  「往前 8 行找 `{x ? … : null}`」的正则，因为 `? (` 和 `: null` 跨行，
  **没匹配上**。

三版都在拿**文本形状**回答「用户点得到吗」这个问题。文本形状不是答案，
**点一下看层出不出来**才是。所以本版：静态只输出成「提示」，判定权交给浏览器。

## 判据与审计**逐字同款**

`paintsOver` / `EDGE` / 4 边全被不透明外人盖住才判 covered —— 抄
`jimeng_unclickable_audit.py`，**不重新发明**。判据被证伪过三次
（§841：第 1 版太松、第 2 版太严、第 3 版问错问题），自己另写一份就是
第四次犯同样的错。

## 三种「没结果」分开记账

- `probed` —— 点开了，量到了。
- `no_ui_path` —— **没有 UI 入口**（静态事实：置 true 的调用点 = 0）。
  这是「无入口死代码路径」，**不是**「焦点陷阱没做好」，也**不推断**它打开
  后会怎样。
- `path_failed` —— 有入口但点了层没出来 ⇒ **前置态没成立**，不下结论。

跑法（**自己起浏览器**，不能用 `jimeng_headless.py run` 注入 `page` ——
那个是源站登录态）：

    /opt/miniconda3/bin/python3 scripts/jimeng_probe864_modaltrap.py

⚠️ 要求 dev server 在跑（默认 http://localhost:4317，`SNAP_URL` 可覆盖）。
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
OUT = Path("/tmp/b864-modaltrap.json")

# (组件, 置 true 的 setter, data-testid, 打开路径)
# ⚠️ 打开路径必须**逐个模态写全**。第 1 版只分了「AssetsModal 走工具条、
#    其它全走更多菜单」两档，于是测 ShortcutsPanel 时又点了一次「项目信息」，
#    报「层没出现」—— 那**不是**关于 ShortcutsPanel 的证据，是探针自己点错了。
#    记一条假证据比不记更坏。
MODALS = [
    ("JimengAssetsModal", "setAssetsOpen", "jimeng-assets-modal",
     ["button[aria-label=\"资产库\"]"], "工具条「资产库」"),
    ("JimengProjectInfoModal", "setProjectInfoOpen", "project-info-modal",
     ["[data-testid=\"canvas-more-trigger\"]", "[role=\"menuitem\"]:text-is(\"项目信息\")"],
     "顶栏「更多」→「项目信息」"),
    ("JimengOfflineDialog", "setOfflineDialog", "jimeng-offline-dialog",
     None, None),
    ("JimengShortcutsPanel", "setShortcutsOpen", "topbar-shortcuts-panel",
     None, None),
]

# ── 判据：与审计逐字同款 ───────────────────────────────────────────────
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
  let edges = 0, firstTop = null, firstName = null;
  for (const [ex, ey] of EDGE) {
    const st = document.elementsFromPoint(ex, ey) || [];
    const t = st[0] || null;
    if (!t) continue;
    if (t === a || a.contains(t) || (t.contains && t.contains(a))) continue;
    if (!paintsOver(t, a)) continue;
    edges += 1;
    if (firstTop === null) { firstTop = t; firstName = nameOf(t); }
  }
  return {state: inside ? 'inside' : (edges === EDGE.length ? 'covered' : 'other'),
          inside: inside, edges_covered: edges, edges_total: EDGE.length,
          top: firstName, al: (a.getAttribute('aria-label') || '').slice(0, 30),
          tid: a.getAttribute('data-testid') || '',
          w: Math.round(b.width), h: Math.round(b.height)};
}
"""


def static_hints(setter: str, comp: str) -> dict:
    """静态**提示**（不是判定）：置 true 的调用点在哪儿，直接的 vs 传递的。"""
    direct: list[str] = []
    indirect: list[str] = []
    for p in sorted(ROOT.glob("src/**/*.tsx")):
        if p.name == f"{comp}.tsx":
            continue
        for i, ln in enumerate(p.read_text(encoding="utf-8",
                                           errors="ignore").splitlines(), 1):
            if f"{setter}(true)" not in ln:
                continue
            (indirect if "=>" in ln else direct).append(
                f"{p.relative_to(ROOT)}:{i}  {ln.strip()[:88]}")
    return {"direct_call_sites": direct, "indirect_call_sites": indirect,
            "note": "静态只作提示：'点得开吗'以浏览器实测为准"
                    "（本探针前两版都栽在文本形状上，见文件头）"}


def click_verified(pg, selector: str, label: str) -> str:
    """点之前**先验落点**（843 的教训：不验落点，点到的不是你想点的）。"""
    el = pg.locator(selector).first
    el.wait_for(state="visible", timeout=8000)
    box = el.bounding_box()
    if not box:
        return f"{label}: 没矩形"
    hit = pg.evaluate(
        "([x,y]) => { const e=document.elementFromPoint(x,y);"
        " return e ? e.tagName+'/'+(e.getAttribute('data-testid')"
        "   ||e.getAttribute('aria-label')||'') : null; }",
        [box["x"] + box["width"] / 2, box["y"] + box["height"] / 2])
    tid = el.get_attribute("data-testid")
    taria = el.get_attribute("aria-label")
    tgt = (el.evaluate("e => e.tagName") or "") + "/" + (tid or taria or "")
    ok = hit is not None and (
        hit == tgt or (taria and taria in hit) or (tid and tid in hit)
        or hit.split("/")[-1] in tgt)
    if not ok:
        return f"{label}: ❌落点不符 hit={hit!r} 目标={tgt!r}"
    el.click()
    return f"{label}: 落点已验 hit={hit} 目标={tgt}"


def walk(pg, tid: str, steps: int = 30) -> dict:
    at_open = pg.evaluate(COVER_JS, tid)
    covered_n = inside_n = 0
    first_covered = None
    trace: list[str] = []
    for i in range(1, steps + 1):
        pg.keyboard.press("Tab")
        s = pg.evaluate(COVER_JS, tid)
        if len(trace) < 24:
            trace.append(f"{i}:{s.get('state')}:al={s.get('al') or '-'}"
                         f":tid={s.get('tid') or '-'}")
        if s.get("inside"):
            inside_n += 1
        if (s.get("edges_covered") == s.get("edges_total")
                and s.get("edges_total")):
            covered_n += 1
            if first_covered is None:
                first_covered = {"at_tab": i, "al": s.get("al"),
                                 "tid": s.get("tid"), "top": s.get("top"),
                                 "edges": f"{s.get('edges_covered')}"
                                          f"/{s.get('edges_total')}"}
        if s.get("inside") and i >= 3:
            break
    return {"focus_at_open": at_open, "covered_n": covered_n,
            "inside_n": inside_n, "first_covered": first_covered,
            "trace": trace}


def traps(pg, tid: str, n_focusable: int) -> dict:
    """**进去之后**会不会又跑出去 —— 前面的 `walk` 量不到这个。

    ⚠️ `walk` 一进层就在第 3 步 break 了（它只回答「几步进得去」）。
    可 `useModalFocusTrap` 承诺的是**另一件事**：进去之后 Tab 在层内**环绕**。
    拿 `walk` 的结果当陷阱的证据，等于用 A 的测量证明 B。
    所以这里独立地再按 `n + 2` 次（n = 层内可聚焦项数，多按两次保证越过末项），
    数落在层外的次数。
    """
    out_n, seq = 0, []
    for i in range(n_focusable + 2):
        pg.keyboard.press("Tab")
        s = pg.evaluate(COVER_JS, tid)
        seq.append("in" if s.get("inside") else f"OUT({s.get('al') or '-'})")
        if not s.get("inside"):
            out_n += 1
    return {"pressed": n_focusable + 2, "escaped": out_n, "seq": seq,
            "traps": out_n == 0}


def main() -> int:
    url = os.environ.get("SNAP_URL", URL)
    results: dict = {"probed": {}, "no_ui_path": [], "path_failed": [],
                     "static_hints": {}}

    print("===== A 静态提示（不是判定） =====")
    for comp, setter, tid, path, how in MODALS:
        h = static_hints(setter, comp)
        results["static_hints"][comp] = h
        print(f"  {comp}")
        for s in h["direct_call_sites"]:
            print(f"      直接调用 {s}")
        for s in h["indirect_call_sites"]:
            print(f"      回调传递 {s}")
        if not h["direct_call_sites"] and not h["indirect_call_sites"]:
            print("      置 true 的调用点 = 0")

    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_context(viewport={"width": 1680, "height": 1050}).new_page()
        pg.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(4)

        print("\n===== B 浏览器实测（判定在这里） =====")
        for comp, setter, tid, path, how in MODALS:
            print(f"\n-- {comp} --")
            if path is None:
                print("  无 UI 入口（静态：置 true 的调用点 = 0）⇒ 不探测、"
                      "不推断它打开后会怎样")
                results["no_ui_path"].append({
                    "component": comp, "testid": tid,
                    "why": "UI 上打不开（置 true 的调用点 = 0）——"
                           "属「无入口死代码路径」，与「焦点陷阱没做好」"
                           "是**两个不同的问题**；未测"})
                continue
            # 每个模态**重载一次页面**再测：不用「Esc + 手动 remove 掉
            # 所有 dialog」那种硬拆。那是破坏性测量，会把上一个模态留在
            # store 里的残状态一起带走，第二个模态测的就不是干净起点
            #（846 栽过「三个破坏性测量串着跑，只有第一个是准的」）。
            pg.reload(wait_until="domcontentloaded", timeout=60000)
            time.sleep(3.5)
            for step in path:
                print("  " + click_verified(pg, step, step))
                time.sleep(0.7)
            time.sleep(1.0)
            if pg.locator(f'[data-testid="{tid}"]').count() == 0:
                print(f"  ❌ 走了 {how} 但层 {tid} 没出现 ⇒ **前置态没成立**，"
                      f"不下结论")
                results["path_failed"].append({
                    "component": comp, "testid": tid, "path": how,
                    "why": "点了但层没出现"})
                continue
            rect = pg.evaluate(
                "([t])=>{const e=document.querySelector("
                "`[data-testid=\"${t}\"]`);const r=e.getBoundingClientRect();"
                "return [Math.round(r.x),Math.round(r.y),"
                "Math.round(r.width),Math.round(r.height)];}", [tid])
            n_focus = pg.evaluate(
                "([t])=>document.querySelector(`[data-testid=\"${t}\"]`)"
                ".querySelectorAll('button:not([disabled]),"
                "[role=\"menuitem\"],input,a[href]').length", [tid])
            w = walk(pg, tid)
            at = w["focus_at_open"] or {}
            takes = at.get("inside") is True
            tr = traps(pg, tid, n_focus)
            print(f"  打开方式={how}  层矩形={rect}  层内可聚焦项={n_focus}")
            print(f"  开层时焦点 = {json.dumps(at, ensure_ascii=False)[:170]}")
            print(f"  ⇒ 开层时焦点在层内 = **{'是' if takes else '否'}**"
                  f"（state={at.get('state')}）")
            print(f"  Tab 走查：进层 {w['inside_n']} 步｜"
                  f"焦点环看不见 {w['covered_n']} 次")
            print(f"  进层后再按 Tab {tr['pressed']} 次：跑出去 {tr['escaped']} 次"
                  f" ⇒ **{'困住了' if tr['traps'] else '没困住'}**"
                  f"  {tr['seq']}")
            if w["first_covered"]:
                print(f"  ★ 首个看不见的焦点位 = "
                      f"{json.dumps(w['first_covered'], ensure_ascii=False)}")
            print(f"  轨迹前 6 步：{(w['trace'] or [])[:6]}")
            results["probed"][comp] = {
                "testid": tid, "how": how, "rect": rect,
                "focusable_in_layer": n_focus,
                "takes_focus_at_open": takes, "state_at_open": at.get("state"),
                "covered_n": w["covered_n"], "inside_steps": w["inside_n"],
                "traps_tab": tr["traps"], "escaped_after_enter": tr["escaped"],
                "trap_seq": tr["seq"],
                "first_covered": w["first_covered"], "trace": w["trace"],
                "focus_at_open": at}
        b.close()

    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(f"\n== 已写 {OUT} ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
