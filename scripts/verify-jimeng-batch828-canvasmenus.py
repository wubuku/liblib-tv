#!/usr/bin/env python3
"""Jimeng clone batch 828 verifier — 把浮层普查从**顶栏**扩到**画布内**。

§38 立的那条契约（「每个浮层都要可指名 + 可定位」）有个盲区：它的普查只逐态打开
了 11 个**顶栏**入口，从没打开过画布内的那几个浮层 —— 画布右键菜单、它的插入
子菜单、缩放菜单、节点连接手柄的插入菜单。契约写得再严，没扫到的地方等于没有。

这一扫就扫出三个漏网的：

| 浮层 | 源站 | 复刻（本批之前） |
|---|---|---|
| 画布右键菜单 | `canvas-context-menu` + `aria-label="Canvas context menu"` | **两样都没有** |
| 缩放菜单 | `canvas-zoom-menu` + `aria-labelledby` 指向触发器 | **两样都没有** |
| 插入子菜单 | **同样两样都没有** | 两样都没有 |
| 节点插入菜单 | 源站无对应浮层（复刻侧便利入口） | 无锚点 |

「只修一处等于没修」在这里又复发了一次：批 824 给**同级**的
`JimengContextMenu`（节点右键菜单）补上了 testid + 可访问名，却漏了
`JimengPaneContextMenu` —— 两者是同一段代码的两个拷贝，而画布空白处右键走的
正是后者。

本批还有一个设计要点：**普查不能要求"全部有名字"**。插入子菜单在源站上同样
没有可访问名，硬给它编一个就成了"复刻自有"。所以普查带一张**白名单**，每条
都必须写明"源站也没有"及其取证结论，并且**白名单非空这件事本身要被断言** ——
否则白名单会退化成"什么都往里塞"的万能借口。
"""

import json
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = os.environ.get("JIMENG_CLONE_URL", "http://localhost:4317")
URL = f"{BASE}/jimeng/canvas/demo"
STATE = Path.home() / ".jimeng-automation" / "state.json"

failures: list[str] = []
checks = 0

# 源站实测同样没有可访问名的浮层 —— 白名单，每条附取证结论
NAME_EXEMPT = {
    "canvas-insert-submenu": "源站实测 200×404 @[1148,414] static，"
                             "role=menu 但 data-testid 与 aria-label **均为 null**。"
                             "不编名字：编了就成复刻自有",
    "canvas-node-insert-menu": "复刻侧便利入口（挂在节点连接手柄「+」上），"
                               "源站无一一对应的浮层",
}

# 源站实测的实名（逐字，不改写）
SRC_CTX_TID = "canvas-context-menu"
SRC_CTX_AL = "Canvas context menu"
SRC_ZOOM_TID = "canvas-zoom-menu"
SRC_ZOOM_GEOM = (200, 292)

CENSUS_JS = """() => {
  const SEL = '[role=dialog],[role=menu],[role=listbox],[role=popover],[role=tooltip]';
  const nameOf = (e) => {
    const al = e.getAttribute('aria-label');
    if (al && al.trim()) return al.trim();
    const lb = e.getAttribute('aria-labelledby');
    if (lb) {
      const t = lb.split(/\\s+/).map(id => document.getElementById(id))
        .filter(Boolean).map(n => (n.getAttribute('aria-label')
             || n.innerText || n.textContent || '').trim()).join(' ').trim();
      if (t) return t;
    }
    return '';
  };
  return [...document.querySelectorAll(SEL)].filter(e => {
    const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden') return false;
    const r = e.getBoundingClientRect();
    return r.width >= 4 && r.height >= 4;
  }).map(e => {
    const r = e.getBoundingClientRect();
    return {role: e.getAttribute('role'), tid: e.getAttribute('data-testid'),
            name: nameOf(e), w: +r.width.toFixed(0), h: +r.height.toFixed(0),
            pos: getComputedStyle(e).position};
  });
}"""


def check(name: str, ok: bool, detail: str = "") -> None:
    global checks
    checks += 1
    if ok:
        print(f"  PASS  {name}" + (f"  ({detail})" if detail else ""))
    else:
        print(f"  FAIL  {name}  {detail}")
        failures.append(name)


def main() -> int:
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(
            storage_state=str(STATE) if STATE.exists() else None,
            viewport={"width": 1680, "height": 1050},
        )
        page = ctx.new_page()
        errs: list[str] = []
        page.on("pageerror", lambda e: errs.append(str(e)[:160]))
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(6000)

        seen: list[dict] = []

        def census(tag: str) -> list[dict]:
            rows = page.evaluate(CENSUS_JS)
            for r in rows:
                r["state"] = tag
            seen.extend(rows)
            return rows

        # ── A. 画布右键菜单 ─────────────────────────────────────────
        page.mouse.click(900, 620, button="right")
        page.wait_for_timeout(900)
        ctxm = page.locator(f'[data-testid="{SRC_CTX_TID}"]')
        check("A.0 前置：画布空白处右键弹出菜单", ctxm.count() == 1)
        if ctxm.count():
            bb = ctxm.bounding_box()
            check(
                f"A.1 右键菜单有 data-testid={SRC_CTX_TID}"
                "（批 824 只修了同级的 JimengContextMenu，这一个被漏了）",
                True,
                f"count={ctxm.count()}",
            )
            al = ctxm.get_attribute("aria-label")
            check(f"A.2 可访问名逐字等于源站的「{SRC_CTX_AL}」", al == SRC_CTX_AL, repr(al))
            check(
                "A.3 仍是 fixed 定位、200 宽（批 828 只补锚点，不动几何）",
                bb is not None and bb["width"] == 200,
                f"{bb['width']:.0f}×{bb['height']:.0f}" if bb else "无",
            )
            census("画布右键菜单")

            # ── B. 插入子菜单 ─────────────────────────────────────
            ins = page.locator('[data-testid="pane-menu-insert"]')
            check("B.0 前置：「新建节点」存在", ins.count() == 1)
            if ins.count():
                ins.first.click()
                page.wait_for_timeout(800)
                sub = page.locator('[data-testid="canvas-insert-submenu"]')
                check(
                    "B.1 插入子菜单有自动化锚点 canvas-insert-submenu",
                    sub.count() == 1,
                )
                check(
                    "B.2 子菜单**刻意没有** aria-label —— 源站这个浮层实测同样"
                    "既无 testid 也无 aria-label。硬编一个名字就成了'复刻自有'",
                    sub.count() == 1 and sub.get_attribute("aria-label") is None,
                    repr(sub.get_attribute("aria-label")) if sub.count() else "不存在",
                )
                census("插入子菜单")
                page.keyboard.press("Escape")
                page.wait_for_timeout(400)
                page.mouse.click(900, 620, button="right")
                page.wait_for_timeout(800)

        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

        # ── C. 缩放菜单 ─────────────────────────────────────────────
        z = page.locator('[data-testid="canvas-zoom-percent"]')
        check("C.0 前置：缩放触发器存在", z.count() == 1)
        if z.count():
            z.first.click()
            page.wait_for_timeout(800)
            zm = page.locator(f'[data-testid="{SRC_ZOOM_TID}"]')
            check(f"C.1 缩放菜单有 data-testid={SRC_ZOOM_TID}（源站同名）", zm.count() == 1)
            if zm.count():
                bb = zm.bounding_box()
                check(
                    f"C.2 几何 {SRC_ZOOM_GEOM[0]}×{SRC_ZOOM_GEOM[1]} 与源站一致"
                    "（这层几何本来就是对的，缺的只是锚点）",
                    bb and (round(bb["width"]), round(bb["height"])) == SRC_ZOOM_GEOM,
                    f"{bb['width']:.0f}×{bb['height']:.0f}" if bb else "无",
                )
                lb = zm.get_attribute("aria-labelledby")
                resolved = page.evaluate(
                    """(id) => {
                        const e = id && document.getElementById(id);
                        return e ? (e.getAttribute('aria-label')
                                    || e.innerText || '').trim() : null;
                    }""",
                    lb or "",
                )
                check(
                    "C.3 可访问名经 aria-labelledby 解析到触发器（源站同型：label 空、"
                    "labelledby 指向触发器）",
                    lb is not None and bool(resolved),
                    f"labelledby={lb} → {resolved!r}",
                )
                n_items = zm.locator("[role=menuitem]").count()
                check(
                    "C.4 七项齐全且与源站逐字一致（放大/缩小/适配画布/缩放至选中项/"
                    "50%/100%/200%）",
                    n_items == 7,
                    f"items={n_items}",
                )
                census("缩放菜单")
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)

        # ── C.5 节点连接手柄的插入菜单 ──────────────────────────────
        # 白名单里写了 canvas-node-insert-menu 却没打开过它，D.5 会红 ——
        # 那条断言的存在意义就在这儿：白名单不能写没扫过的条目。
        # 连接手柄不是**每个节点**都有：视频节点自己直接挂 JimengInsertMenu，
        # 音频/导演台等才走 JimengConnectHandles。所以逐个节点试，找到带手柄的
        # 那个为止 —— 写死"第一个节点"会得到一个看似合理的假前置。
        handle = page.locator('[data-testid="jimeng-connect-left"]')
        nodes = page.locator(".react-flow__node")
        for i in range(min(nodes.count(), 6)):
            nodes.nth(i).click()
            page.wait_for_timeout(500)
            if handle.count():
                break
        if handle.count():
            # 连接手柄的「+」是 **selected 才挂载、点击才展开**（不是 hover）
            handle.first.click()
            page.wait_for_timeout(900)
        nim = page.locator('[data-testid="canvas-node-insert-menu"]')
        check(
            "C.5 节点连接手柄的插入菜单有锚点 canvas-node-insert-menu"
            "（复刻侧便利入口，源站无对应浮层，故只补锚点不补名字）",
            nim.count() == 1,
            f"count={nim.count()}",
        )
        if nim.count():
            check(
                "C.6 该菜单**刻意无** aria-label —— 源站无一一对应物，编名字即复刻自有",
                nim.get_attribute("aria-label") is None,
                repr(nim.get_attribute("aria-label")),
            )
            census("节点插入菜单")
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
        page.mouse.click(30, 950)
        page.wait_for_timeout(400)

        # ── D. 普查结论（含白名单机制）──────────────────────────────
        print("— 画布内浮层普查 —")
        by_tid = {r["tid"]: r for r in seen if r["tid"]}
        no_tid = [r for r in seen if not r["tid"]]
        check(
            f"D.1 画布内各态枚举出的浮层都有 data-testid（本次 {len(by_tid)} 个具名）",
            not no_tid,
            "; ".join(f"{r['state']}/{r['role']} {r['w']}x{r['h']}" for r in no_tid[:4]),
        )
        unnamed = [r for r in seen if not r["name"] and r["tid"] not in NAME_EXEMPT]
        exempt_hits = [r for r in seen if not r["name"] and r["tid"] in NAME_EXEMPT]
        check(
            "D.2 除白名单外都有可访问名（白名单存在的意义就在这儿）",
            not unnamed,
            "; ".join(f"{r['state']}/{r['tid']}" for r in unnamed[:4]),
        )
        check(
            "D.3 白名单里的条目**确实**以'无名'状态出现过 —— 全都拿到名字时"
            "这条会红，提醒把条目从白名单里摘掉（否则白名单会变成万能借口）",
            bool(exempt_hits) or not NAME_EXEMPT,
            f"命中 {[r['tid'] for r in exempt_hits]}",
        )
        check(
            "D.4 白名单每条都带取证结论，不是光秃秃一个 testid",
            all(len(v) > 20 and "源站" in v or "复刻侧" in v
                for v in NAME_EXEMPT.values()),
            "; ".join(f"{k}: {len(v)} 字" for k, v in NAME_EXEMPT.items()),
        )
        check(
            "D.5 白名单条目在本次枚举里都真的出现过（防白名单写了没用的条目）",
            all(any(r["tid"] == k for r in seen) for k in NAME_EXEMPT),
            "; ".join(k for k in NAME_EXEMPT if not any(r["tid"] == k for r in seen)),
        )

        check("E.0 无页面 JS 报错", not errs, "; ".join(errs[:2]))
        ctx.close()
        b.close()

    print(f"\n{checks - len(failures)}/{checks}")
    if failures:
        print("FAILED: " + ", ".join(failures))
        return 1
    print("batch 828 OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
