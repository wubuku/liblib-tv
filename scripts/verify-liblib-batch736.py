#!/usr/bin/env python3
"""batch 736 验收：导演台（clone 侧）交互元素普查 + 焦点围栏 + 两套键盘契约

## 起点

735 把画布侧的 `data-inert` 族收官（46 写点 / 97 枚 / 五口径）。
导演台是另一个子系统，也是复刻优先级最高的两块之一，但至今没有过一轮普查。
本批全部读数来自 clone —— 入口是种子里那张 `script-execution` 卡上的
`[data-open-director]`（`ScriptExecutionNode.tsx:51-62`），**不碰源站**。

## 决定性读数

### ① 静态 195 写点 → 运行时 142 枚
`src/components/director/**` 静态 button 141 / input 50 / select 4；
打开台子后挂载 142 枚（111 button + 21 input + 10 个 `div[role=…]`）。

### ② 焦点围栏是真的，但它是**自己算的那份列表**
`useDirectorFocusContainment.ts:149-172` 在 desk 的 root 上监听 keydown，
每按一次 Tab 就 `preventDefault()` 并按自己那份 `focusable` 列表前移、到尾回���。
root 内 136 枚匹配 `FOCUSABLE_SELECTOR`，五个过滤器过后 **124** 枚进列表（差 12）。

### ③ **5 枚 `role=treeitem` + 1 枚 `role=separator`：ARIA 说它是控件，键盘完全够不着**
六枚全是 `div`、**`tabIndex: -1`（显式排除，不是漏写）**、有几何、不在陷阱列表里、`focus()` 失败。
其中 5 枚是对象树的树节点（角色01/咖啡桌/冷掉的咖啡/咖啡馆背景/机位01），
1 枚是「拖动调整时间轴高度」的分隔条 —— 三者都是鼠标可拖的东西。

### ④ 12 枚无可及名，10 枚是**看得见的输入框**
9 个变换数值框（position/rotation/scale 各 3）+ 1 个对象改名框（248×28），
加 2 个隐藏的 `type=file`（0×0 / 1×1）。

### ⑤ 自然 Tab 200 步：**0 次逃出**，97 种停靠名

### ⑥ 两个键盘契约靠**显式状态守卫**互斥 —— 不是靠冒泡路径碰巧
| | 按 30 次 Tab |
|---|---|
| 台开 | 30/30 被 `preventDefault`；add-node 面板入口 0 → **0**（不开） |
| 台关 | **0** 次被 `preventDefault`；add-node 面板入口 → **9**（被 Tab 打开） |

`page.tsx:1312` `if (uiState.activeDirectorNodeId) return;` 让画布整套键盘契约在台开时整体下线，
`:1313` 另有 `resolveLibTVBlockingForegroundSurface` 列的 **10** 个阻塞前台面（`:1401` 挂在 `window` 上）。
**我原本猜「两个契约靠 DOM 位置互斥」，源码否掉了这个猜** —— 记在方法论里。

### ⑦ 同一个应用里两套「不可达」语义：画布 46 处自证惰性，导演台 **0** 处
导演台用的是**原生 `inert` 属性**（`DirectorDesk.tsx:1182/1282`），但只在**移动端**作用域生效；
桌面宽度下 142 枚里 `inert` 命中 **0**、`aria-disabled` 命中 **0**（原生 `disabled` 7 枚）。

## 判据

C1  静态写点 141 button / 50 input / 4 select
C2  入口 `[data-open-director]` 存在，点开后台面挂载
C3  运行时 142 枚 = 111 button + 21 input + 10 div[role]
C4  围栏列表 136 → 124
C5  5 枚 treeitem + 1 枚 separator 全部 tabIndex=-1 / 不在陷阱 / focus() 失败
C6  12 枚无可及名，其中 10 枚是可见输入
C7  自然 Tab 200 步 0 逃出 / 95 种停靠名
C8  两契约互斥的运行时读数（台开 30/30 prevented、面板不开；台关 0 prevented、面板开）
C9  互斥机制是显式状态守卫（源码两行）
C10 原生 inert / aria-disabled 在 142 枚里 0 命中
"""

import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch736-2026-10-01"
BASE = "http://localhost:4317"
W, H = 1440, 1000
TAB_STEPS = 200
TAB_PROBE_STEPS = 30

# 与 useDirectorFocusContainment.ts:5-17 逐字一致
TRAP_SELECTOR = ("a[href],area[href],button,input,select,textarea,iframe,object,embed,"
                 "[contenteditable='true'],[tabindex]")

DESK = '[data-director-focus-scope="workspace"]'


# ---------------------------------------------------------------- 静态
def static_write_points():
    counts = Counter()
    per_file = {}
    for path in sorted(ROOT.glob("src/components/director/*.tsx")):
        src = path.read_text(encoding="utf-8")
        b = len(re.findall(r"<button\b", src))
        i = len(re.findall(r"<input\b", src))
        s = len(re.findall(r"<select\b", src))
        per_file[path.name] = {"button": b, "input": i, "select": s}
        counts["button"] += b
        counts["input"] += i
        counts["select"] += s
    return counts, per_file


def static_guards():
    """C9：两个键盘契约靠哪两行互斥。

    `resolveLibTVBlockingForegroundSurface(uiState)` 在 1294 还有另一个调用点，
    所以这里要的是**紧跟在导演台早退之后**的那一行，不能取首个匹配。
    """
    page = (ROOT / "src/app/page.tsx").read_text(encoding="utf-8")
    lines = page.split("\n")
    director_guard = None
    surface_guard = None
    window_hook = None
    for n, line in enumerate(lines, start=1):
        if "if (uiState.activeDirectorNodeId) return;" in line and director_guard is None:
            director_guard = n
            continue
        if director_guard is not None and n == director_guard + 1 \
                and "resolveLibTVBlockingForegroundSurface(uiState)" in line:
            surface_guard = n
        if 'window.addEventListener("keydown", handleKeyDown)' in line and window_hook is None:
            window_hook = n
    ctx = (ROOT / "src/lib/libtvSelectionCommandContext.ts").read_text(encoding="utf-8")
    surfaces = re.findall(r"if \(snapshot\.(\w+)\) return", ctx)
    return {"directorGuardLine": director_guard, "surfaceGuardLine": surface_guard,
            "windowHookLine": window_hook, "blockingSurfaces": surfaces}


# ---------------------------------------------------------------- 运行时
ENUM = """() => {
  const root = document.querySelector('[data-director-focus-scope="workspace"]');
  if (!root) return {error: 'no-desk'};
  const sel = 'button, input, select, textarea, [role="button"], [role="switch"], [role="slider"], [role="tab"], [role="tablist"], [role="treeitem"], [role="separator"]';
  return [...root.querySelectorAll(sel)].map(el => {
    const cs = getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    let owner = 'root';
    let n = el;
    while (n && n !== root) {
      const a = [...n.attributes].find(x => x.name.startsWith('data-director'));
      if (a) { owner = a.name + '=' + (a.value || '').slice(0, 24); break; }
      n = n.parentElement;
    }
    el.focus();
    return {
      tag: el.tagName.toLowerCase(),
      type: el.getAttribute('type') || '',
      role: el.getAttribute('role') || '',
      label: el.getAttribute('aria-label') || '',
      title: el.getAttribute('title') || '',
      text: (el.textContent || '').trim().slice(0, 18),
      placeholder: el.getAttribute('placeholder') || '',
      disabled: el.hasAttribute('disabled'),
      ariaDisabled: el.getAttribute('aria-disabled'),
      inertSelf: el.hasAttribute('inert'),
      inertAncestor: !!el.closest('[inert]'),
      w: Math.round(rect.width), h: Math.round(rect.height),
      display: cs.display, visibility: cs.visibility,
      focusable: document.activeElement === el,
      owner: owner,
    };
  });
}"""


def ax_roles(cdp, selector):
    root = cdp.send("DOM.getDocument", {"depth": -1})["root"]["nodeId"]
    ids = cdp.send("DOM.querySelectorAll", {"nodeId": root, "selector": selector})["nodeIds"]
    out = []
    for nid in ids:
        try:
            backend = cdp.send("DOM.describeNode", {"nodeId": nid})["node"]["backendNodeId"]
            tree = cdp.send("Accessibility.getPartialAXTree", {"backendNodeId": backend, "fetchRelatives": False})
        except Exception:
            out.append(None)
            continue
        own = next((n for n in tree.get("nodes", []) if n.get("role")), None) or {}
        out.append({"role": (own.get("role") or {}).get("value"),
                    "name": (own.get("name") or {}).get("value"),
                    "ignored": own.get("ignored")})
    return out


def goto(page, tag):
    page.goto(f"{BASE}/?batch736={tag}", wait_until="networkidle", timeout=90_000)
    page.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
    page.mouse.move(W - 4, 4)
    page.wait_for_timeout(1_300)


def open_desk(page):
    page.evaluate("() => { document.querySelector('[data-open-director]').click(); }")
    page.wait_for_timeout(2_000)


def close_desk(page):
    page.evaluate("""() => { const b = [...document.querySelectorAll('button')]
      .find(x => (x.getAttribute('aria-label') || '') === '关闭' || (x.textContent || '').trim() === '关闭');
      if (b) b.click(); }""")
    page.wait_for_timeout(1_200)


def add_node_entries(page):
    return page.evaluate("""() => [...document.querySelectorAll('button')]
      .filter(b => (b.getAttribute('data-add-node-entry') || '').length > 0).length""")


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    print("=== 静态 ===")
    counts, per_file = static_write_points()
    guards = static_guards()
    print(f"  写点 button {counts['button']} / input {counts['input']} / select {counts['select']}")
    print(f"  守卫: 导演台早退 :{guards['directorGuardLine']}，前台面 :{guards['surfaceGuardLine']}，"
          f"window 挂钩 :{guards['windowHookLine']}，阻塞面 {len(guards['blockingSurfaces'])} 种")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H})
        cdp = page.context.new_cdp_session(page)
        cdp.send("Accessibility.enable")

        goto(page, "main")
        entry = page.evaluate("() => document.querySelector('[data-open-director]') ? 'found' : 'MISSING'")
        print(f"\n=== 入口 [data-open-director]: {entry} ===")
        open_desk(page)

        rows = page.evaluate(ENUM)
        desk_present = page.evaluate(f"() => Boolean(document.querySelector('{DESK}'))")
        print(f"  台面挂载: {desk_present}   交互元素: {len(rows)}")
        print("  按 tag:", dict(Counter(r["tag"] for r in rows)))

        # 围栏列表
        trap = page.evaluate("""([sel]) => {
          const root = document.querySelector('[data-director-focus-scope="workspace"]');
          const isDisabled = (el) => el.disabled === true;
          const isHidden = (el) => {
            if (el.matches("[hidden], [aria-hidden='true'], [inert]")) return true;
            if (el.closest("[hidden], [aria-hidden='true'], [inert]")) return true;
            const s = getComputedStyle(el);
            return s.display === 'none' || s.visibility === 'hidden';
          };
          const all = [...root.querySelectorAll(sel)];
          const list = all.filter(el => !(el.tabIndex < 0 || isDisabled(el)
            || el.getAttribute('type') === 'hidden' || isHidden(el))
            && el.getClientRects().length > 0);
          const desc = (el) => el.getAttribute('aria-label') || el.getAttribute('title')
            || (el.textContent || '').trim() || el.tagName.toLowerCase();
          return {all: all.length, list: list.length,
                  treeitem: [...root.querySelectorAll('[role="treeitem"]')].map(el => ({
                    name: desc(el), tag: el.tagName.toLowerCase(), tabIndex: el.tabIndex,
                    rects: el.getClientRects().length, inTrap: list.includes(el)})),
                  separator: [...root.querySelectorAll('[role="separator"]')].map(el => ({
                    name: desc(el), tag: el.tagName.toLowerCase(), tabIndex: el.tabIndex,
                    rects: el.getClientRects().length, inTrap: list.includes(el)}))};
        }""", [TRAP_SELECTOR])
        print(f"  围栏列表: 匹配 {trap['all']} → 进列表 {trap['list']}")
        print(f"  role=treeitem {len(trap['treeitem'])} 枚 / role=separator {len(trap['separator'])} 枚")

        ax = ax_roles(cdp, DESK + " button, " + DESK + " input, " + DESK + " select, "
                      + DESK + " [role=button], " + DESK + " [role=switch], "
                      + DESK + " [role=tab], " + DESK + " [role=treeitem], " + DESK + " [role=separator]")
        print("  AX role 分布:", dict(Counter((a or {}).get("role") for a in ax)))
        print("  AX ignored=true:", sum(1 for a in ax if a and a.get("ignored")),
              " AX 无名:", sum(1 for a in ax if not (a or {}).get("name")))

        # 自然 Tab
        page.evaluate("""() => { window.__hits = []; }""")
        page.evaluate("""() => {
          window.__k = (e) => { if (e.key !== 'Tab') return;
            setTimeout(() => { const a = document.activeElement;
              const root = document.querySelector('[data-director-focus-scope="workspace"]');
              const inside = root && root.contains(a);
              window.__hits.push(inside
                ? ((a.getAttribute('aria-label') || a.getAttribute('title') || a.textContent || a.tagName).trim().slice(0, 24))
                : '<<ESCAPED:' + a.tagName.toLowerCase() + '>>'); }, 0); };
          document.addEventListener('keydown', window.__k, true);
        }""")
        for _ in range(TAB_STEPS):
            page.keyboard.press("Tab")
        hits = page.evaluate("() => window.__hits")
        page.evaluate("() => document.removeEventListener('keydown', window.__k, true)")
        inside = [h for h in hits if not h.startswith("<<ESCAPED")]
        escaped = [h for h in hits if h.startswith("<<ESCAPED")]
        print(f"  自然 Tab {TAB_STEPS} 步: 停在台内 {len(inside)} / 逃出 {len(escaped)}，"
              f"不同停靠名 {len(set(inside))} 种")

        # 两套键盘契约：台开
        page.evaluate("() => { window.__prevented = 0; }")
        page.evaluate("""() => { window.__p = (e) => { if (e.key === 'Tab' && e.defaultPrevented) window.__prevented++; };
          document.addEventListener('keydown', window.__p, false); }""")
        before_open = add_node_entries(page)
        for _ in range(TAB_PROBE_STEPS):
            page.keyboard.press("Tab")
        open_reading = {"entriesBefore": before_open, "entriesAfter": add_node_entries(page),
                        "prevented": page.evaluate("() => window.__prevented")}
        print(f"  台开按 {TAB_PROBE_STEPS} 次 Tab: add-node 入口 {before_open} → "
              f"{open_reading['entriesAfter']}，被 preventDefault {open_reading['prevented']} 次")

        # 两套键盘契约：台关
        close_desk(page)
        closed = page.evaluate(f"() => !document.querySelector('{DESK}')")
        page.evaluate("() => { window.__prevented = 0; }")
        for _ in range(TAB_PROBE_STEPS):
            page.keyboard.press("Tab")
        closed_reading = {"deskGone": closed, "entriesAfter": add_node_entries(page),
                          "prevented": page.evaluate("() => window.__prevented")}
        print(f"  台关按 {TAB_PROBE_STEPS} 次 Tab（closed={closed}）: add-node 入口 → "
              f"{closed_reading['entriesAfter']}，被 preventDefault {closed_reading['prevented']} 次")

        page.close()
        browser.close()

    unnamed = [r for r in rows if not r["label"] and not r["title"] and not r["text"] and not r["placeholder"]]
    unnamed_visible = [r for r in unnamed if r["w"] > 1 and r["h"] > 1]
    treeitem_rows = [r for r in rows if r["role"] == "treeitem"]
    separator_rows = [r for r in rows if r["role"] == "separator"]
    aria_rows = treeitem_rows + separator_rows
    aria_unreachable = 0
    for row in aria_rows:
        if not row["focusable"]:
            aria_unreachable += 1
    aria_in_trap = 0
    for item in trap["treeitem"] + trap["separator"]:
        if item["inTrap"]:
            aria_in_trap += 1

    summary = {
        "staticButton": counts["button"], "staticInput": counts["input"], "staticSelect": counts["select"],
        "staticTotal": sum(counts.values()),
        "entryFound": entry, "deskMounted": desk_present,
        "runtimeTotal": len(rows),
        "runtimeButton": sum(1 for r in rows if r["tag"] == "button"),
        "runtimeInput": sum(1 for r in rows if r["tag"] == "input"),
        "runtimeDivRole": sum(1 for r in rows if r["tag"] == "div"),
        "trapAll": trap["all"], "trapList": trap["list"],
        "treeitem": len(trap["treeitem"]), "separator": len(trap["separator"]),
        "ariaRoleUnreachable": aria_unreachable,
        "ariaRoleInTrap": aria_in_trap,
        "unnamed": len(unnamed), "unnamedVisible": len(unnamed_visible),
        "focusFail": sum(1 for r in rows if not r["focusable"]),
        "focusFailNoDisabled": sum(1 for r in rows if not r["focusable"] and not r["disabled"]),
        "inertHits": sum(1 for r in rows if r["inertSelf"] or r["inertAncestor"]),
        "ariaDisabledHits": sum(1 for r in rows if r["ariaDisabled"]),
        "nativeDisabled": sum(1 for r in rows if r["disabled"]),
        "tabSteps": TAB_STEPS, "tabInside": len(inside), "tabEscaped": len(escaped),
        "tabDistinct": len(set(inside)),
        "openReading": open_reading, "closedReading": closed_reading,
        "directorGuardLine": guards["directorGuardLine"],
        "surfaceGuardLine": guards["surfaceGuardLine"],
        "blockingSurfaces": len(guards["blockingSurfaces"]),
    }
    print("\n=== 汇总 ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    checks = [
        ("C1 静态写点 141/50/4",
         (counts["button"], counts["input"], counts["select"]) == (141, 50, 4), str(dict(counts))),
        ("C2 入口存在且台面挂载",
         entry == "found" and desk_present is True, f"entry={entry} desk={desk_present}"),
        ("C3 运行时 142 = 111 button + 21 input + 10 div[role]",
         (len(rows), summary["runtimeButton"], summary["runtimeInput"], summary["runtimeDivRole"])
         == (142, 111, 21, 10),
         f"{len(rows)} = {summary['runtimeButton']}+{summary['runtimeInput']}+{summary['runtimeDivRole']}"),
        ("C4 围栏列表 136 → 124",
         (trap["all"], trap["list"]) == (136, 124), f"{trap['all']} → {trap['list']}"),
        ("C5 5 treeitem + 1 separator 全 tabIndex=-1 / 不在陷阱 / focus() 失败",
         len(trap["treeitem"]) == 5 and len(trap["separator"]) == 1
         and summary["ariaRoleUnreachable"] == 6 and summary["ariaRoleInTrap"] == 0
         and all(t["tabIndex"] == -1 for t in trap["treeitem"] + trap["separator"]),
         f"treeitem={len(trap['treeitem'])} separator={len(trap['separator'])} "
         f"unreachable={summary['ariaRoleUnreachable']} inTrap={summary['ariaRoleInTrap']}"),
        ("C6 12 枚无可及名，其中 10 枚是可见输入",
         (len(unnamed), len(unnamed_visible)) == (12, 10),
         f"{len(unnamed)} 枚无名 / {len(unnamed_visible)} 枚可见"),
        ("C7 自然 Tab 200 步 0 逃出 / 97 种停靠名",
         (len(inside), len(escaped), len(set(inside))) == (200, 0, 97),
         f"inside={len(inside)} escaped={len(escaped)} distinct={len(set(inside))}"),
        ("C8 两契约互斥：台开 30/30 prevented 且面板不开；台关 0 prevented 且面板开",
         open_reading["prevented"] == 30 and open_reading["entriesAfter"] == 0
         and closed_reading["prevented"] == 0 and closed_reading["entriesAfter"] == 9
         and closed_reading["deskGone"] is True,
         json.dumps({"open": open_reading, "closed": closed_reading}, ensure_ascii=False)),
        ("C9 互斥机制是显式状态守卫（:1312 早退 + :1313 前台面 + 10 个阻塞面）",
         guards["directorGuardLine"] == 1312 and guards["surfaceGuardLine"] == 1313
         and guards["windowHookLine"] == 1401 and len(guards["blockingSurfaces"]) == 10,
         json.dumps(guards, ensure_ascii=False)),
        ("C10 inert / aria-disabled 在 142 枚里 0 命中",
         summary["inertHits"] == 0 and summary["ariaDisabledHits"] == 0,
         f"inert={summary['inertHits']} aria-disabled={summary['ariaDisabledHits']} "
         f"原生 disabled={summary['nativeDisabled']}"),
    ]

    print("\n=== 判据 ===")
    failures = []
    for name, ok, detail in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}  ⟵ {detail}")
        if not ok:
            failures.append(name)

    payload = {
        "static": {"counts": dict(counts), "perFile": per_file, "guards": guards},
        "run": {"rows": rows, "trap": trap, "ax": ax,
                "tab": {"steps": TAB_STEPS, "inside": len(inside), "escaped": len(escaped),
                        "distinct": len(set(inside)),
                        "topStops": Counter(inside).most_common(12)},
                "keyboard": {"open": open_reading, "closed": closed_reading}},
        "summary": summary,
        "failures": failures,
    }
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    print(f"\n{len(checks) - len(failures)}/{len(checks)} 判据通过；写入 {AUDIT_DIR / 'runtime-audit.json'}")
    try:
        subprocess.run(["git", "status", "--porcelain", "src"], cwd=ROOT, check=True)
    except Exception:
        pass
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
