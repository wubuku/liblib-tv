#!/usr/bin/env python3
"""batch 849：普查有 24 个状态，键盘只探到 12 层 —— **差的 12 个去哪了**。

§66 顺带说「视频生成面板的 4 个下拉在审计里从来没被探过」。复查代码发现
`EXPECTED_STATES` 里**有**这 5 个状态（面板 + 4 个下拉）且 `skipped = 0`
—— 它们**跑了**。所以真正的问题不是「没跑」，而是：

    普查跑了 24 个状态，键盘探针只在其中 12 个上开到了层。

把 12 个缺口逐个归位（读 b841 输出，不是猜的）：

    空态 / 视频工具条 / 视频生成面板      3 个**本来就没有浮层**
                                          （画布壳、工具条、面板本体都不是层）
    视频生成面板 4 个下拉                  6 个**应该有层**却没认出来 ← 真缺口
    音频生成面板 5 个下拉                  5 个**应该有层**却没认出来 ← 真缺口

判据 `open_layer()` 有一条 `if (e.closest(SHELL)) continue`，而 **SHELL 里含
`.react-flow__node`** —— 如果下拉是渲染在**节点内部**（`div.relative` 里，
和触发器同一支），它会被**自己的壳**筛掉。这正是 840 那条「按身份排除，别按尺寸」
的同一个形状，但方向相反：那次是壳太大被误认成层，这次是层太深被误认成壳。

这一轮跑判决性实验，并把**9 个缺口**和**已识别的层**放在一起跑 ——
没有阴性对照，实验就分不清「探针坏了」和「判据盲区」。

⚠️ 节点定位必须用 `data-testid`（审计的 `.react-flow__node[data-testid=…]`），
   不是 `data-id`（复刻的 data-id 是 `video-empty-1`，不带 `rf__node-` 前缀）。
   第一版拿 `data-id="rf__node-video-empty-1"` 找，压根找不到节点 ——
   前置态没成立却硬往下跑，是最坏的一种失败。
"""

import json

from playwright.sync_api import sync_playwright

URL = "http://localhost:4317/jimeng/canvas/demo"

# ── 与 jimeng_unclickable_audit.py 的 open_layer() **逐字同款** ─────────
OPEN_LAYER_JS = """() => {
  const SHELL = 'react-flow__renderer, react-flow__pane, '
              + 'react-flow__viewport, react-flow__nodes, '
              + 'react-flow__node, react-flow__node-toolbar';
  const LAYER = '.react-flow__node-panel, [role=menu], [role=listbox], '
              + '[role=dialog], [role=popover], [data-testid$="-listbox"], '
              + '[data-testid$="-menu"], [data-testid$="-panel"], '
              + '[data-testid$="-palette"]';
  for (const e of document.querySelectorAll(LAYER)) {
    const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden') continue;
    const r = e.getBoundingClientRect();
    if (r.width < 40 || r.height < 20) continue;
    if (e.closest(SHELL)) continue;
    if (e.closest('nextjs-portal')) continue;
    const hasFocusable = e.querySelector(
      'button,[href],input,select,textarea,[tabindex]:not([tabindex="-1"]),'
      + '[role=menuitem],[role=option]');
    if (!hasFocusable) continue;
    return e.getAttribute('data-testid')
        || e.getAttribute('aria-label') || e.getAttribute('role') || '?';
  }
  return '';
}"""

# 逐条体检：候选层 + **每一条判据的通过与否**（不猜是哪条 reject 的）
DIAGNOSE_JS = """(expectedTid) => {
  const SHELL = 'react-flow__renderer, react-flow__pane, '
              + 'react-flow__viewport, react-flow__nodes, '
              + 'react-flow__node, react-flow__node-toolbar';
  const LAYER = '.react-flow__node-panel, [role=menu], [role=listbox], '
              + '[role=dialog], [role=popover], [data-testid$="-listbox"], '
              + '[data-testid$="-menu"], [data-testid$="-panel"], '
              + '[data-testid$="-palette"]';
  const rows = [];
  for (const e of document.querySelectorAll(LAYER)) {
    const s = getComputedStyle(e);
    const r = e.getBoundingClientRect();
    const tid = e.getAttribute('data-testid') || '';
    // 命中 SHELL 里**哪一条**（只报最深的那条，够定位了）
    const shellHit = e.closest(SHELL);
    const inShell = !!shellHit;
    const inPortal = !!e.closest('nextjs-portal');
    const hasFocusable = !!e.querySelector(
      'button,[href],input,select,textarea,[tabindex]:not([tabindex="-1"]),'
      + '[role=menuitem],[role=option]');
    const visible = s.display !== 'none' && s.visibility !== 'hidden';
    const big = r.width >= 40 && r.height >= 20;
    const passes = visible && big && !inShell && !inPortal && hasFocusable;
    rows.push({tid, role: e.getAttribute('role') || '',
               w: Math.round(r.width), h: Math.round(r.height),
               visible, big, inShell, inPortal, hasFocusable, passes,
               isExpected: tid === expectedTid,
               shellHit: shellHit
                 ? (shellHit.tagName.toLowerCase() + '.'
                    + (shellHit.className || '').toString()
                       .replace(/\\s+/g, ' ').trim().split(' ')[0])
                 : '',
               z: s.zIndex, pos: s.position,
               chain: (() => {
                 const c = []; let n = e;
                 for (let i = 0; n && i < 6; i++, n = n.parentElement) {
                   const cn = (n.className || '').toString()
                     .replace(/\\s+/g, ' ').trim();
                   const cls = cn ? '.' + cn.split(' ')[0] : '';
                   c.push((n.getAttribute('data-testid')
                           ? '[' + n.getAttribute('data-testid') + ']' : '')
                          + n.tagName.toLowerCase() + cls);
                 }
                 return c.join(' < ');
               })()});
  }
  return {rows, found: (function() {
    for (const r of rows) if (r.passes) return r.tid || '(无 tid)';
    return '';
  })()};
}"""

# 与审计 select_node() 同款的落点扫描（843/840 同病：点歪了就是假零）
SELECT_JS = """(tid) => {
  const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
  if (!n) return null;
  const r = n.getBoundingClientRect();
  const CTRL = 'button,[role=button],a,input,select,textarea';
  for (const [fx, fy] of [[0.5,0.5],[0.5,0.25],[0.25,0.5],[0.75,0.5],
                          [0.5,0.75],[0.2,0.2],[0.8,0.8]]) {
    const x = r.x + r.width * fx, y = r.y + r.height * fy;
    const top = document.elementFromPoint(x, y);
    if (top && n.contains(top) && !top.closest(CTRL))
      return [Math.round(x), Math.round(y), (top.getAttribute('data-testid') || top.tagName)];
  }
  return null;
}"""

NODE_TIDS_JS = """() => [...document.querySelectorAll('.react-flow__node')]
  .map(n => n.getAttribute('data-testid'))"""

# 前置态：节点到底选中了没有？（「我没检测到」之前先确认「我够得着」）
SELECTED_JS = """() => ({
  selected: [...document.querySelectorAll('.react-flow__node.selected')]
    .map(n => n.getAttribute('data-testid')),
  toolbars: document.querySelectorAll('.react-flow__node-toolbar').length,
  panels: document.querySelectorAll('.react-flow__node-panel').length,
})"""

# 缺口组（审计里没进 kb_rows 的 9 个） + 阴性对照组（审计里**认出来了**的）
# ⚠️ trig 一律**自带作用域**：`node-toolbar button[…], node-panel button[…]`。
#    写成 scope="A, B" 再拼 `f"{scope} {trig}"` 会得到
#        "A, B button[…]"
#    —— 逗号的优先级让整条变成「**A** 或 **B 里的按钮**」，`.first` 命中的是
#    **A 自己**（那个 div），点了个寂寞。审计的 `open_dropdown`/`try_measure`
#    就是这个写法，它正是那 9 个状态「跑了却没开层」的原因。
GAP = [
    ("缺口", "视频·模型", 'button[aria-label^="选择模型"]', "gen-model-listbox"),
    ("缺口", "视频·尺寸", 'button[aria-label^="视频尺寸选项"]', "gen-video-size-listbox"),
    ("缺口", "视频·模式", 'button[aria-label^="生成模式"]', "gen-mode-listbox"),
    ("缺口", "视频·时长", 'button[aria-label^="选择视频生成时长"]', "gen-duration-listbox"),
    ("对照", "视频工具条·截取帧", 'button:text-is("截取帧")', "video-toolbar-capture-menu"),
    ("对照", "视频工具条·工具", 'button:text-is("工具")', "video-toolbar-tools-menu"),
]

# 清场：Escape **不行** —— 审计里明令禁止（会取消选中 → 工具条卸载 →
# 顺带把还没扫的浮层弄没了，判据会**假装**没查到）。要**点回各自的触发器**。
CLOSE_TIDS = ["gen-model-listbox", "gen-video-size-listbox", "gen-mode-listbox",
              "gen-duration-listbox", "video-toolbar-capture-menu",
              "video-toolbar-tools-menu"]
CLOSE_TRIG = {
    "gen-model-listbox": 'button[aria-label^="选择模型"]',
    "gen-video-size-listbox": 'button[aria-label^="视频尺寸选项"]',
    "gen-mode-listbox": 'button[aria-label^="生成模式"]',
    "gen-duration-listbox": 'button[aria-label^="选择视频生成时长"]',
    "video-toolbar-capture-menu": '.react-flow__node-toolbar button:text-is("截取帧")',
    "video-toolbar-tools-menu": '.react-flow__node-toolbar button:text-is("工具")',
}

out: dict = {"runs": [], "preflight": {}}


def main() -> int:
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        c = b.new_context(viewport={"width": 1680, "height": 1050})
        pg = c.new_page()
        pg.goto(URL, wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(9000)

        tids = pg.evaluate(NODE_TIDS_JS)
        print("== 画布节点 ==", tids)
        out["preflight"]["nodes"] = tids
        if "rf__node-video-empty-1" not in (tids or []):
            print("!! 画布上没有 rf__node-video-empty-1（前置态没成立）")
            out["preflight"]["fatal"] = "没有视频生成节点"
            c.close(); b.close()
            return 2

        pt = pg.evaluate(SELECT_JS, "rf__node-video-empty-1")
        print("== 选点落点 ==", pt)
        out["preflight"]["select_point"] = pt
        if not pt:
            print("!! 选不中视频节点（前置态没成立）")
            out["preflight"]["fatal"] = "选不中视频节点"
            c.close(); b.close()
            return 2
        # 每个节点只选中一次；**每轮开头都重新断言选中态** ——
        # 上一轮点了个寂寞导致节点掉选中的话，后面的层全都不开，
        # 结论会变成「层不在 DOM 里 ⇒ 层没开」，把脚本 bug 记到产品头上。
        def focus(tid: str) -> bool:
            p = pg.evaluate(SELECT_JS, tid)
            if not p:
                print(f"!! 选不中 {tid}（前置态没成立）")
                return False
            pg.mouse.click(p[0], p[1])
            pg.wait_for_timeout(1400)
            st = pg.evaluate(SELECTED_JS)
            ok = st["selected"] == [tid]
            print(f"-- 选中 {tid}: selected={st['selected']} "
                  f"toolbar={st['toolbars']} panel={st['panels']} "
                  f"{'✓' if ok else '✗ 前置态没成立'}")
            return ok

        for kind, name, trig, want in [r for r in GAP if r[0] == "缺口"]:
            if not focus("rf__node-video-empty-1"):
                out["runs"].append({"kind": kind, "name": name, "want": want,
                                    "why": "节点没选中", "recognized": False})
                continue
            _safe(pg, out, kind, name, trig, want)

        for kind, name, trig, want in [r for r in GAP if r[0] == "对照"]:
            if not focus("rf__node-video-local-1"):
                out["runs"].append({"kind": kind, "name": name, "want": want,
                                    "why": "节点没选中", "recognized": False})
                continue
            _safe(pg, out, kind, name, trig, want)

        c.close(); b.close()

    with open("/tmp/b849-openlayer.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    _summary(out)
    return 0


def _safe(pg, out: dict, kind: str, name: str, trig: str, want: str) -> None:
    """单条测量抛异常**不许带走整轮**。

    审计的 `insert()` 早写过这条（一次 30s 超时会带崩**整份**审计，前面所有状态
    的结果全丢）。本探针第二轮又犯了一次：对照组那个 `document.querySelector`
    的 SyntaxError 让缺口组跑完的 4 条**一条都没落盘**。异常按「前置态没成立」
    记账，然后继续跑下一条。
    """
    try:
        out["runs"].append(_one(pg, kind, name, trig, want))
    except Exception as e:
        print(f"   ⚠ 测量抛异常: {type(e).__name__}: {str(e)[:120]}")
        out["runs"].append({"kind": kind, "name": name, "want": want,
                            "why": f"异常 {type(e).__name__}", "recognized": False})
    finally:
        _close(pg, out)


def _close(pg, out: dict) -> None:
    """把开着的层**点回它自己的触发器**（不是 Escape —— 见 CLOSE_TIDS 上方注释）。

    漏下去比漏报更坏：残着的层会被下一轮的 `open_layer()` 先撞上，于是
    后面几个状态都在报同一层，而对照组的「没认出来」会被误读成判据盲区。
    """
    for tid in CLOSE_TIDS:
        if not pg.locator(f'[data-testid="{tid}"]').count():
            continue
        loc = pg.locator(CLOSE_TRIG[tid])
        if not loc.count():
            continue
        try:
            loc.first.click(timeout=4000)
            pg.wait_for_timeout(300)
        except Exception:
            pass
    left = [t for t in CLOSE_TIDS if pg.locator(f'[data-testid="{t}"]').count()]
    if left:
        print(f"   ⚠ 清场没关干净: {left} ⇒ 下一轮 open_layer() 会撞上它们")
        out.setdefault("leaks", []).append(left)


def _one(pg, kind: str, name: str, trig: str, want: str) -> dict:
    print("=" * 78)
    print(f"【{kind}】{name}  期望层 {want!r}  触发器 {trig}")
    rec: dict = {"kind": kind, "name": name, "want": want, "trigger": trig}
    if pg.locator(f'[data-testid="{want}"]').count():
        print("   层已开着（跳过点击 —— 再点一次是**关掉**它，§59）")
    else:
        loc = pg.locator(trig)
        if not loc.count():
            print("   ⚠ 触发器 count=0 ⇒ 前置态没成立")
            rec["why"] = "触发器不存在"
            return rec
        # 落点先验：`loc.first` 到底是谁、点下去会不会落到别的东西上。
        # ⚠️ 必须在**元素上下文**里量：`trig` 可能是 Playwright 的
        #    `button:text-is("截取帧")`，`document.querySelector` 不认这个语法
        #    （第一版就这么炸的：SyntaxError → 整轮跑到一半崩，缺口组白跑）。
        rec["hit"] = loc.first.evaluate("""(l) => {
          const r = l.getBoundingClientRect();
          const x = r.x + r.width / 2, y = r.y + r.height / 2;
          const top = document.elementFromPoint(x, y);
          return {tag: l.tagName, tid: l.getAttribute('data-testid') || '',
                  al: l.getAttribute('aria-label') || '',
                  txt: (l.innerText || '').trim().slice(0, 12),
                  top_al: top ? (top.getAttribute('aria-label') || top.tagName) : '',
                  top_inside: !!(top && l.contains(top)),
                  on_screen: r.width > 0 && r.height > 0};
        }""")
        print(f"   落点体检: {rec['hit']}")
        if not rec["hit"] or not rec["hit"]["on_screen"]:
            rec["why"] = "触发器不在屏上"
            return rec
        try:
            loc.first.click(timeout=8000)
        except Exception as e:
            print("   ⚠ 点击失败:", type(e).__name__)
            rec["why"] = f"点击失败 {type(e).__name__}"
            return rec
        pg.wait_for_timeout(900)

    got = pg.evaluate(OPEN_LAYER_JS)
    diag = pg.evaluate(DIAGNOSE_JS, want)
    rec["open_layer"] = got
    rec["recognized"] = (got == want)
    verdict = "✓ 认出来了" if got == want else "✗ 没认出来"
    print(f"   open_layer() = {got!r}   {verdict}")

    exp = [r for r in diag["rows"] if r["isExpected"]]
    if not exp:
        print("   ⚠ 期望的层**不在 DOM 里** ⇒ 层没开（脚本/产品问题，不是判据盲区）")
        rec["in_dom"] = False
    else:
        e = exp[0]
        rec["in_dom"] = True
        rec["layer"] = e
        print(f"   期望层: tid={e['tid']!r} role={e['role']!r} {e['w']}×{e['h']} "
              f"z={e['z']} pos={e['pos']}")
        for k in ("visible", "big", "inShell", "inPortal", "hasFocusable", "passes"):
            print(f"      {k:<13} = {e[k]}")
        if e["inShell"]:
            print(f"      命中 SHELL 于 = {e['shellHit']}   ← **判据盲区**")
        print(f"   祖先链: {e['chain']}")
        # ⚠️ `inShell/inPortal` 是**取反**的：为 False 才是**通过**。
        #    第一版写成 `if not e[k]` ⇒ 「不在壳里」被记成「被 inShell reject」，
        #    对照组六条判据全过却打印两条 reject —— **假红**，比假零更难发现。
        rec["rejected_by"] = (
            ([] if e["visible"] else ["visible"])
            + ([] if e["big"] else ["big"])
            + (["inShell"] if e["inShell"] else [])
            + (["inPortal"] if e["inPortal"] else [])
            + ([] if e["hasFocusable"] else ["hasFocusable"]))
        print(f"   ⇒ 被这几条 reject: {rec['rejected_by'] or '（无）'}")
    rec["all_tids"] = [r["tid"] for r in diag["rows"]]
    return rec


def _summary(out: dict) -> None:
    print("\n" + "=" * 78)
    print("汇总")
    gaps = [r for r in out["runs"] if r["kind"] == "缺口"]
    ctl = [r for r in out["runs"] if r["kind"] == "对照"]
    print(f"  缺口 {len(gaps)} 个：认出来 "
          f"{sum(1 for r in gaps if r.get('recognized'))} / {len(gaps)}")
    print(f"  对照 {len(ctl)} 个：认出来 "
          f"{sum(1 for r in ctl if r.get('recognized'))} / {len(ctl)}")
    if ctl and not all(r.get("recognized") for r in ctl):
        print("  ⚠ **对照组自己就没全认出来** ⇒ 探针有问题，缺口结论不成立")
    for r in out["runs"]:
        if r["kind"] == "缺口" and not r.get("recognized"):
            why = ("层没进 DOM" if r.get("in_dom") is False
                   else "判据 reject: " + ",".join(r.get("rejected_by") or []))
            print(f"    · {r['name']:<16} {why}")
    print("\n明细 /tmp/b849-openlayer.json")


if __name__ == "__main__":
    raise SystemExit(main())
