#!/usr/bin/env python3
"""batch 737 验收：导演台那 53 枚「静态写了、初始没挂载」的写点归因 + 围栏的边界

## 起点

736 测出静态 195 写点、初始状态只挂 142 枚，缺口 53 枚没逐个归因。
本批把它们逐个打开，并顺带把 736 的两个读数重新审了一遍 —— **审出 736 自己的一处测法错**。

## 决定性读数

### ① 五个 flyout/modal 入口读 +0 —— 是**探针范围错**，不是「它们不加东西」
`DirectorIconRail.tsx:308` 的 `createPortal` 把 flyout 挂在 **`[data-director-focus-scope="workspace"]` 之外**。
我第一版探针把计数范围限死在 workspace 根内，于是五个入口全读 +0。
⟹ **736 的「运行时 142 枚」与「围栏列表 124 枚」都是「根内」口径**，这是范围声明、不是缺陷。

### ② 逐个打开后的增量（初始 142 为基线）

| 入口 | 增量 | 新出现的族 |
|---|---|---|
| 角色页签「姿势」 | **净 +12** | 出现 **45**（`pose-preset` **20** + `pose-control` **25**）、消失 **33**（属性页整组），切回可逆 |
| 手机运镜面板 | +2 | `phone-vcam-panel` 1 + `phone-vcam-connect` 1 |
| 曲线编辑器 | +13（含时间轴行被换掉的部分） | `curve-preset` 5 + `curve-handle` 2 + `back-to-timeline` 1 |
| 导出面板 | 0 | — |
| 机位页签「运动轨迹」 | −27 | 属性页整组消失，`motion-*` 5 枚进来 |
| 机位页签「截图」 | −30 | `capture-clear-all` 1 + `capture-send-all` 1 |
| 观测到的峰值 | **174** | 手机运镜面板 + 机位属性页 |

「姿势」一个页签 **45 枚** ⟹ 静态 195 那个数里，最大的一族藏在 `DirectorMannequin`/`DirectorInspector` 的姿势面板里。

### ③ 围栏在台内**确实生效**（冒泡阶段读数）
焦点在台内按 20 次 Tab：**20/20 被 `preventDefault`**、落点 **20/20 在台内**。
与 736 的读数一致。

### ④ **推翻我自己探针的一处测法错**
探针 B/C 把监听挂在 **`capture: true`** 上读 `e.defaultPrevented` ——
捕获阶段先于目标节点的处理器跑，那一刻它必然还是 false ⟹ **「被拦 0 次」是测法错，不是行为错**。
同一组数据在冒泡阶段是 20/20。**736 的验收器用的就是冒泡阶段，读数没错。**

### ⑤ 围栏的边界：它管得了「里面」，管不了「外面」
`useDirectorFocusContainment.ts:174` 把 `keydown` 挂在 **root** 上 ⟹ 事件不经过 root 就够不着它。

| 起点 | 20 步 Tab 的冒泡计数 | 落点归属 |
|---|---|---|
| 台内 | **20 / 20 被拦** | 台内 20 |
| **台外** | **0 / 20 被拦** | **台外 20** |
| 台外 + `Shift+Tab` | 17 / 20 被拦 | 台外 1 + body 1 + **台内 18** |

⟹ 围栏**不能把已经在台外的焦点拉回来**（台外按 Tab 一路走在画布控件上）；
但**反向能进** —— 从台外往回走 2 步就跨进台内，一进去就被接管。

### ⑥ 台外那 47 枚是真实存在的
11 个 `删除连线` + 画布顶栏 8（项目菜单/工作区名称/画布 2/工作流/故事板/发布与分享/开通会员/积分余额）
+ 底部坞 6（打开工具箱/素材库/角色库/生成历史/快捷键/教程）+ 添加节点/移动/打开导演台→/取消 ESC 等。

### ⑦ 键盘**走不到**台外那个状态
点开「添加角色」flyout 后焦点**留在台内**（停在轨按钮上），
接着 30 步 Tab **30/30 在台内**；连续 8 轮「点开 → Tab 5 步 → 再点」焦点**始终在台内**。
⟹ **围栏的缺口是潜伏的，不是键盘可达的** —— 唯一进去的方式是程序化 `focus()`（或将来某条把焦点交出去的代码路径）。

## 判据

C1  静态 195 写点（沿用 736 口径）
C2  flyout 走 portal、在 workspace 根之外（`createPortal` @ IconRail.tsx:308）
C3  打开「添加角色」flyout，根外 +11 枚
C4  围栏在台内生效：20 步 Tab 冒泡 20/20 被拦、落点 20/20 在台内
C5  围栏对台外焦点无效：20 步 Tab 冒泡 0/20、落点 20/20 在台外
C6  反向能进：起点「项目菜单」、flyout 关闭时 Shift+Tab 20 步里 2 步内进入台内，此后 18 步在台内
C7  捕获阶段读 defaultPrevented 恒 0（测法错的证据，与 C4 同一组数据）
C8  键盘走不到台外：flyout 开着时 30 步 Tab 全在台内 + 8 轮开关焦点不回退
C9  「姿势」页签：出现 45 / 消失 33 / 净增 12 / 切回属性页可逆
C10 台外 36 枚（关闭态）/ 47 枚（flyout 开着），其中 11 枚是连线删除手柄
"""

import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch737-2026-10-01"
BASE = "http://localhost:4317"
W, H = 1440, 1000
DESK = '[data-director-focus-scope="workspace"]'
INTERACTIVE = 'button, input, select, textarea, [role="button"], [role="switch"], [role="slider"], [role="tab"], [role="tablist"], [role="treeitem"], [role="separator"]'

CLASSIFY_JS = """() => {
  const a = document.activeElement;
  const root = document.querySelector('[data-director-focus-scope="workspace"]');
  if (!a || a === document.body) return {where: 'body', label: 'body'};
  const inDesk = !!(root && root.contains(a));
  const inFly = !inDesk && !!a.closest('div[style*="fixed"]');
  return {where: inDesk ? 'desk' : inFly ? 'flyout' : 'outside',
          label: ((a.getAttribute && (a.getAttribute('aria-label') || a.getAttribute('title'))) || a.textContent || a.tagName).trim().slice(0, 20)};
}"""


def static_write_points():
    counts = Counter()
    for path in sorted(ROOT.glob("src/components/director/*.tsx")):
        src = path.read_text(encoding="utf-8")
        counts["button"] += len(re.findall(r"<button\b", src))
        counts["input"] += len(re.findall(r"<input\b", src))
        counts["select"] += len(re.findall(r"<select\b", src))
    return counts


def static_portal():
    src = (ROOT / "src/components/director/DirectorIconRail.tsx").read_text(encoding="utf-8")
    lines = src.split("\n")
    line_no = None
    for n, line in enumerate(lines, start=1):
        if "createPortal(" in line and line_no is None:
            line_no = n
    rail_entries = re.findall(r'\{ id: "([a-z-]+)", label: "([^"]+)", icon: \w+, kind: "(\w+)" \}', src)
    character_flyout = re.findall(r'\{ id: "[a-z0-9-]+", label: "[^"]+", kind: "(\w+)"', src)
    return {"createPortalLine": line_no, "railEntries": rail_entries,
            "characterFlyoutItems": len(character_flyout)}


def open_desk(page, tag):
    page.goto(f"{BASE}/?batch737={tag}", wait_until="networkidle", timeout=90_000)
    page.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
    page.mouse.move(W - 4, 4)
    page.wait_for_timeout(1_300)
    page.evaluate("() => { document.querySelector('[data-open-director]').click(); }")
    page.wait_for_timeout(2_000)


def count_groups(page):
    """按最近的 data-* 祖先归组；分别数「根内」与「根外」。"""
    return page.evaluate("""([desk, sel]) => {
      const root = document.querySelector(desk);
      const label = (el) => ((el.getAttribute && (el.getAttribute('aria-label') || el.getAttribute('title')))
        || (el.textContent || '').trim() || el.tagName).slice(0, 22);
      const inRoot = {}, outRoot = {};
      for (const el of document.querySelectorAll(sel)) {
        const bucket = root.contains(el) ? inRoot : outRoot;
        let n = el, key = 'root';
        while (n && n !== root) {
          const a = [...n.attributes].find(x => x.name.startsWith('data-director'));
          if (a) { key = a.name; break; }
          n = n.parentElement;
        }
        bucket[key] = (bucket[key] || 0) + 1;
      }
      return {inRoot: inRoot, outRoot: outRoot,
              inRootTotal: [...document.querySelectorAll(sel)].filter(e => root.contains(e)).length,
              outRootTotal: [...document.querySelectorAll(sel)].filter(e => !root.contains(e)).length,
              outNames: [...document.querySelectorAll(sel)].filter(e => !root.contains(e)).map(label)};
    }""", [DESK, INTERACTIVE])


def click_attr(page, selector):
    return page.evaluate("""(s) => { const b = document.querySelector(s);
      if (!b) return 'MISSING';
      if (b.hasAttribute('disabled')) return 'DISABLED';
      b.click(); return 'clicked'; }""", selector)


def install_listeners(page):
    page.evaluate("() => { window.__log = []; window.__cap = 0; window.__bub = 0; }")
    page.evaluate(CLASSIFY_JS.replace("() => {", "window.__classify = () => {", 1).replace("};", "};"))
    page.evaluate("""() => {
      window.__capK = (e) => { if (e.key === 'Tab' && e.defaultPrevented) window.__cap++; };
      window.__bubK = (e) => { if (e.key === 'Tab' && e.defaultPrevented) window.__bub++; };
      window.__logK = (e) => { if (e.key !== 'Tab') return;
        setTimeout(() => { window.__log.push(window.__classify()); }, 0); };
      document.addEventListener('keydown', window.__capK, true);
      document.addEventListener('keydown', window.__bubK, false);
      document.addEventListener('keydown', window.__logK, true);
    }""")


def uninstall_listeners(page):
    page.evaluate("""() => {
      document.removeEventListener('keydown', window.__capK, true);
      document.removeEventListener('keydown', window.__bubK, false);
      document.removeEventListener('keydown', window.__logK, true);
    }""")


def walk(page, steps, shift=False):
    install_listeners(page)
    for _ in range(steps):
        page.keyboard.press("Shift+Tab" if shift else "Tab")
    log = page.evaluate("() => window.__log")
    cap = page.evaluate("() => window.__cap")
    bub = page.evaluate("() => window.__bub")
    uninstall_listeners(page)
    where = Counter(x["where"] for x in log)
    return {"steps": steps, "shift": shift, "capturePrevented": cap, "bubblePrevented": bub,
            "desk": where.get("desk", 0), "flyout": where.get("flyout", 0),
            "outside": where.get("outside", 0), "body": where.get("body", 0),
            "firstSix": log[:6]}


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    print("=== 静态 ===")
    counts = static_write_points()
    portal = static_portal()
    print(f"  写点 button {counts['button']} / input {counts['input']} / select {counts['select']}"
          f"  合计 {sum(counts.values())}")
    print(f"  createPortal 在 IconRail.tsx:{portal['createPortalLine']}；轨入口 {len(portal['railEntries'])} 个；"
          f"添加角色 flyout {portal['characterFlyoutItems']} 项")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H})

        # ---------- 打开台：先量「根内 / 根外」 ----------
        open_desk(page, "portal")
        closed_state = count_groups(page)
        print(f"\n=== 根内 {closed_state['inRootTotal']} 枚 / 根外 {closed_state['outRootTotal']} 枚 ===")
        print(f"  根外可及名 top: {Counter(closed_state['outNames']).most_common(8)}")

        # ---------- 打开 flyout ----------
        page.evaluate("""() => { const b = document.querySelector('[data-director-rail-entry="add-character"]');
          b.focus(); b.click(); }""")
        page.wait_for_timeout(1_000)
        flyout_state = count_groups(page)
        out_added = flyout_state["outRootTotal"] - closed_state["outRootTotal"]
        flyout_names = sorted(set(flyout_state["outNames"]) - set(closed_state["outNames"]))
        print(f"\n=== 打开「添加角色」flyout ===")
        print(f"  根内 {flyout_state['inRootTotal']}（{flyout_state['inRootTotal'] - closed_state['inRootTotal']:+d}）"
              f"  根外 {flyout_state['outRootTotal']}（{out_added:+d}）")
        print(f"  根外新增可及名: {flyout_names}")

        # ---------- C4 焦点在台内 ----------
        page.evaluate("""() => { const root = document.querySelector('[data-director-focus-scope="workspace"]');
          root.querySelector('button').focus(); }""")
        m_inside = walk(page, 20)
        print(f"\n=== 焦点在台内，20 次 Tab ===")
        print(f"  捕获 {m_inside['capturePrevented']} / 冒泡 {m_inside['bubblePrevented']}；"
              f"落点 desk {m_inside['desk']} flyout {m_inside['flyout']} outside {m_inside['outside']}")

        # ---------- C8 键盘走不到台外：30 步 + 8 轮开关 ----------
        page.evaluate("""() => { const b = document.querySelector('[data-director-rail-entry="add-character"]');
          if (b) b.click(); }""")
        page.wait_for_timeout(600)
        after_click = page.evaluate("window.__classify")
        m_fly = walk(page, 30)
        cycles = []
        for _ in range(8):
            page.evaluate("""() => { const b = document.querySelector('[data-director-rail-entry="add-character"]');
              if (b) b.click(); }""")
            page.wait_for_timeout(500)
            pos = page.evaluate("window.__classify")
            lg = walk(page, 5)
            cycles.append({"afterClick": pos["where"], "desk": lg["desk"],
                           "flyout": lg["flyout"], "outside": lg["outside"]})
        print(f"\n=== flyout 开着时 30 步 Tab ===")
        print(f"  点击后焦点 {after_click['where']}；落点 desk {m_fly['desk']} flyout {m_fly['flyout']} "
              f"outside {m_fly['outside']} body {m_fly['body']}")
        print(f"  8 轮开关：每次 {json.dumps(cycles, ensure_ascii=False)}")

        # ---------- C5 焦点在台外 ----------
        moved = page.evaluate("""() => { const root = document.querySelector('[data-director-focus-scope="workspace"]');
          const b = [...document.querySelectorAll('button')].find(x => !root.contains(x) && x.getAttribute('aria-label'));
          if (!b) return 'NONE'; b.focus();
          return document.activeElement === b ? (b.getAttribute('aria-label') || '') : 'FAILED'; }""")
        page.wait_for_timeout(300)
        m_outside = walk(page, 20)
        print(f"\n=== 焦点程序化搬到台外（{moved}），20 次 Tab ===")
        print(f"  捕获 {m_outside['capturePrevented']} / 冒泡 {m_outside['bubblePrevented']}；"
              f"落点 desk {m_outside['desk']} outside {m_outside['outside']}")

        # ---------- C6 台外 Shift+Tab 反向能进 ----------
        # flyout 必须先关掉、起点必须点名：r1 这一格之所以两轮读数不同，
        # 是因为 flyout 一直开着 ⟹ Shift+Tab 会先撞进 portal 里的 flyout。
        page.evaluate("""() => { const fly = [...document.querySelectorAll('button')]
          .find(x => x.closest('div[style*="fixed"]')); if (fly) fly.click(); }""")
        page.wait_for_timeout(700)
        start_label = page.evaluate("""() => { const root = document.querySelector('[data-director-focus-scope="workspace"]');
          const b = [...document.querySelectorAll('button')]
            .find(x => (x.getAttribute('aria-label') || '') === '项目菜单');
          if (!b) return 'MISSING'; b.focus();
          return document.activeElement === b ? '项目菜单' : 'FAILED'; }""")
        m_back = walk(page, 20, shift=True)
        first_desk = None
        for i, step in enumerate(m_back["firstSix"]):
            if step["where"] == "desk":
                first_desk = i
                break
        print(f"  起点 {start_label}")
        print(f"\n=== 台外 Shift+Tab 20 次 ===")
        print(f"  捕获 {m_back['capturePrevented']} / 冒泡 {m_back['bubblePrevented']}；"
              f"落点 desk {m_back['desk']} outside {m_back['outside']} body {m_back['body']}；"
              f"前 6 步里首次进台内 = 第 {first_desk} 步")

        # ---------- C9 「姿势」页签 +45 ----------
        page.evaluate("""() => { const b = [...document.querySelectorAll('button')]
          .find(x => (x.getAttribute('aria-label') || '') === '关闭'); if (b) b.click(); }""")
        page.wait_for_timeout(1_000)
        open_desk(page, "pose")
        pose_base = count_groups(page)
        page.evaluate("""() => { const n = document.querySelector('[data-director-object-id="director-character-lead"]');
          if (n) { n.dispatchEvent(new MouseEvent('mousedown', {bubbles:true, clientX:0, clientY:0}));
                   n.dispatchEvent(new MouseEvent('mouseup', {bubbles:true, clientX:0, clientY:0}));
                   n.click(); } }""")
        page.wait_for_timeout(1_000)
        sel_state = count_groups(page)
        how = click_attr(page, '[data-director-character-tab="pose"]')
        page.wait_for_timeout(1_000)
        pose_state = count_groups(page)
        pose_delta = pose_state["inRootTotal"] - sel_state["inRootTotal"]
        pose_groups = {k: v for k, v in pose_state["inRoot"].items()
                       if v != sel_state["inRoot"].get(k, 0)}
        for k, v in sel_state["inRoot"].items():
            if v != pose_state["inRoot"].get(k, 0):
                pose_groups[k] = -v
        pose_added = sum(v for v in pose_groups.values() if v > 0)
        pose_removed = -sum(v for v in pose_groups.values() if v < 0)
        # 可逆性：切回属性页应当回到原数
        page.evaluate("""() => { const b = document.querySelector('[data-director-character-tab="properties"]');
          if (b) b.click(); }""")
        page.wait_for_timeout(1_000)
        back_state = count_groups(page)
        pose_reversible = back_state["inRootTotal"] == sel_state["inRootTotal"]
        print(f"\n=== 角色页签「姿势」({how}) ===")
        print(f"  选中角色后根内 {sel_state['inRootTotal']} → 姿势页签 {pose_state['inRootTotal']}（{pose_delta:+d}）")
        print(f"  出现 {pose_added} 枚 / 消失 {pose_removed} 枚 / 净增 {pose_delta}"
              f" / 切回属性页 {back_state['inRootTotal']}（可逆={pose_reversible}）")

        page.close()
        browser.close()

    cycles_outside = sum(c["outside"] for c in cycles)
    summary = {
        "staticSites": sum(counts.values()),
        "createPortalLine": portal["createPortalLine"],
        "railEntries": len(portal["railEntries"]),
        "inRootClosed": closed_state["inRootTotal"],
        "outRootClosed": closed_state["outRootTotal"],
        "inRootFlyout": flyout_state["inRootTotal"],
        "outRootFlyout": flyout_state["outRootTotal"],
        "flyoutOutAdded": out_added,
        "flyoutOutNames": len(flyout_names),
        "insideCapture": m_inside["capturePrevented"], "insideBubble": m_inside["bubblePrevented"],
        "insideDeskStops": m_inside["desk"], "insideOutsideStops": m_inside["outside"],
        "outsideCapture": m_outside["capturePrevented"], "outsideBubble": m_outside["bubblePrevented"],
        "outsideDeskStops": m_outside["desk"], "outsideOnlyStops": m_outside["outside"],
        "backBubble": m_back["bubblePrevented"], "backDeskStops": m_back["desk"],
        "backOutsideStops": m_back["outside"], "backBodyStops": m_back["body"],
        "firstDeskStep": first_desk,
        "fly30Desk": m_fly["desk"], "fly30Flyout": m_fly["flyout"], "fly30Outside": m_fly["outside"],
        "cyclesAllInsideDesk": all(c["desk"] == 5 and c["outside"] == 0 for c in cycles),
        "cyclesOutsideTotal": cycles_outside,
        "poseDelta": pose_delta,
        "posePreset": pose_state["inRoot"].get("data-director-pose-preset", 0),
        "poseControl": pose_state["inRoot"].get("data-director-pose-control", 0),
        "poseAdded": pose_added, "poseRemoved": pose_removed,
        "poseReversible": pose_reversible,
        "shiftStart": start_label,
    }
    print("\n=== 汇总 ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    checks = [
        ("C1 静态 195 写点", summary["staticSites"] == 195, str(summary["staticSites"])),
        ("C2 flyout 走 createPortal（IconRail.tsx:308）",
         summary["createPortalLine"] == 308 and summary["railEntries"] == 6,
         json.dumps({"createPortalLine": portal["createPortalLine"],
                     "railEntries": [e[0] for e in portal["railEntries"]]}, ensure_ascii=False)),
        ("C3 打开「添加角色」flyout：根内不变、根外 +11",
         summary["inRootFlyout"] == summary["inRootClosed"] and summary["flyoutOutAdded"] == 11
         and summary["flyoutOutNames"] == 11,
         f"根内 {summary['inRootClosed']}→{summary['inRootFlyout']}；根外 "
         f"{summary['outRootClosed']}→{summary['outRootFlyout']}（+{summary['flyoutOutAdded']}）"),
        ("C4 台内 20 步 Tab：冒泡 20/20 被拦、落点 20/20 在台内",
         summary["insideBubble"] == 20 and summary["insideDeskStops"] == 20
         and summary["insideOutsideStops"] == 0,
         f"bubble={summary['insideBubble']} desk={summary['insideDeskStops']} outside={summary['insideOutsideStops']}"),
        ("C5 台外 20 步 Tab：冒泡 0/20、落点 20/20 在台外",
         summary["outsideBubble"] == 0 and summary["outsideOnlyStops"] == 20
         and summary["outsideDeskStops"] == 0,
         f"bubble={summary['outsideBubble']} outside={summary['outsideOnlyStops']} desk={summary['outsideDeskStops']}"),
        ("C6 台外 Shift+Tab：起点「项目菜单」时 2 步内进台内、此后 18 步在台内（可复现）",
         summary["shiftStart"] == "项目菜单" and summary["backDeskStops"] == 18
         and summary["backOutsideStops"] == 1 and summary["backBodyStops"] == 1
         and summary["firstDeskStep"] == 2 and summary["backBubble"] == 17,
         f"起点={summary['shiftStart']} desk={summary['backDeskStops']} "
         f"outside={summary['backOutsideStops']} body={summary['backBodyStops']} "
         f"冒泡={summary['backBubble']} 首次进台内=第{summary['firstDeskStep']}步"),
        ("C7 捕获阶段读 defaultPrevented 恒 0（测法错的证据）",
         summary["insideCapture"] == 0 and summary["outsideCapture"] == 0,
         f"台内 capture={summary['insideCapture']} / 台外 capture={summary['outsideCapture']}"),
        ("C8 键盘走不到台外：flyout 开着 30 步全在台内 + 8 轮开关焦点不回退",
         summary["fly30Desk"] == 30 and summary["fly30Outside"] == 0
         and summary["cyclesAllInsideDesk"] is True and summary["cyclesOutsideTotal"] == 0,
         f"30 步 desk={summary['fly30Desk']} outside={summary['fly30Outside']}；"
         f"8 轮全在台内={summary['cyclesAllInsideDesk']}"),
        ("C9 「姿势」页签：出现 45 / 消失 33 / 净增 12 / 切回可逆",
         summary["posePreset"] == 20 and summary["poseControl"] == 25
         and summary["poseAdded"] == 45 and summary["poseRemoved"] == 33
         and summary["poseDelta"] == 12 and summary["poseReversible"] is True,
         f"出现={summary['poseAdded']}(preset {summary['posePreset']}+control "
         f"{summary['poseControl']}) 消失={summary['poseRemoved']} 净增={summary['poseDelta']} "
         f"可逆={summary['poseReversible']}"),
        ("C10 台外 36 枚（关闭态）/ 47 枚（flyout 开着），其中 11 枚是连线删除手柄",
         summary["outRootClosed"] == 36 and summary["outRootFlyout"] == 47
         and Counter(closed_state["outNames"])["删除连线"] == 11,
         f"关闭态根外 {summary['outRootClosed']} 枚 / flyout 开着 {summary['outRootFlyout']} 枚；"
         f"删除连线 {Counter(closed_state['outNames'])['删除连线']} 枚"),
    ]

    print("\n=== 判据 ===")
    failures = []
    for name, ok, detail in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}  ⟵ {detail}")
        if not ok:
            failures.append(name)

    payload = {
        "static": {"counts": dict(counts), "portal": portal},
        "run": {"closed": closed_state, "flyout": flyout_state,
                "walkInside": m_inside, "walkOutside": m_outside, "walkBack": m_back,
                "walkFlyout30": m_fly, "cycles": cycles, "afterFlyoutClick": after_click,
                "pose": {"base": pose_base["inRootTotal"], "selected": sel_state["inRootTotal"],
                         "afterTab": pose_state["inRootTotal"], "delta": pose_delta,
                         "changedGroups": pose_groups}},
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
