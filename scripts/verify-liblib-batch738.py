#!/usr/bin/env python3
"""batch 738 验收：flyout 的两个子菜单（群众 3x3 / 几何模型）

## 起点

737 把 53 枚未挂载写点归因时，**没有逐个打开 flyout 里的两个子菜单**
（群众 3x3 / 几何模型）。而 `DirectorIconRail.tsx` 的 batch 625 注释留了一条待验的读数：
几何子菜单的 `z-50` 曾被嵌套层叠上下文压成「有效 z 30」，在 1280×720 埋掉 5 枚、
1100×700 埋掉 6 枚；625 用 `createPortal` + `z-[160]` 修掉了。
本批验的是**修好之后的当前状态**，不是复现那个 bug。

## 决定性读数

### ① 群众 (3x3)：1 写点 → 5 枚，全在 portal 里
`data-director-crowd-dialog`，实测 `position: fixed` + `z-index: 160` + 不在 workspace 根内。
3 个 `number` 输入框（`rows` 93×28 / `columns` 93×28 / `spacing` 194×28）+ 2 个按钮（取消/添加 48×28）。
根外 button：47 → **52**。

### ② 几何模型子菜单：**8 枚，不是 625 清单里的 6 枚**
上传文件 / 立方体 / 球体 / 圆柱体 / 环状体 / 圆锥 / **棱锥** / **添加空对象**。
源码 `IconRail.tsx:98-107` 就是 8 项，且 `pyramid` 与 `empty-object` 都是
**batch 590（`a42a394a`，与子菜单同一笔）引入的**。
⟹ **625 注释里括号列的 6 项是「被埋掉的那几枚」的清单，不是子菜单的完整清单** ——
拿它当全量会少算 2 枚。

### ③ 两个视口下 8 枚**全部可见可点** ⟹ 625 的「埋掉」不复现
| 视口 | 子菜单盒子 | 8 枚 |
|---|---|---|
| 1440×1000 | 204×270 @(52,508) | 8/8 在视口内、`opacity: 1`、`pointer-events: auto`、`focus()` 全成功 |
| 1100×700 | 204×270 @(52,422) | 8/8 同上 |

625 说「1280×720 埋掉 5 枚、1100×700 埋掉 6 枚」—— **当前树里读不到这个现象**。

### ④ 子菜单的 `z-50` 现在只在 portal 容器内部生效
子菜单自身 computed `z-index: 50` / `position: absolute`，
但它的父容器是 `position: fixed` 的 portal（`z-index: 160`）⟹
**50 参与的是 portal 容器内部的排序，不再与时间线（z-40） competes**。
这正是 625 的修法；读数确认它生效。

### ⑤ 画幅比例 flyout 7 枚在 1100×700 全可见 ⟹ 625「埋掉 9:16」不复现
自适应 / 21:9 / 16:9 / 4:3 / 1:1 / 3:4 / **9:16**（103×72，9:16 底边 573 < 700）。

### ⑥ 附带撞见：11 枚 `删除连线` 手柄 `pointer-events: none`
723 记过「11 枚连线手柄 8×8 中心命中 0/11」，当时没记成因。
本批实测：这 11 枚**全部 8×8 且 `pointer-events: none`** ⟹
鼠标事件根本不落在它们身上。**「0/11 命中」与「pe=none」同源**（本批用 `elementFromPoint` 独立复验）。

## 判据

C1  群众弹窗：portal + z-160，1 写点 → 5 枚（3 number + 2 button）
C2  几何子菜单 8 枚，且源码 8 项、pyramid/empty-object 来自 batch 590
C3  1440×1000：8/8 在视口内 + opacity 1 + pe auto + focus() 成功
C4  1100×700：8/8 同上（625「埋掉 6 枚」不复现）
C5  子菜单 computed z-index=50 / absolute，父容器 fixed portal ⟹ 50 只在容器内生效
C6  画幅比例 7 枚（含 9:16）在 1100×700 全在视口内
C7  根外 button 轨迹 47 → 52（群众）→ 55（几何）
C8  两个子菜单的控件都不在 workspace 根内 ⟹ 不在围栏管辖内
C9  11 枚 `删除连线` 手柄 8×8 且 pe=none，中心 `elementFromPoint` 命中 0/11
"""

import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch738-2026-10-01"
BASE = "http://localhost:4317"
DESK = '[data-director-focus-scope="workspace"]'

GEOMETRY_IDS = ["geometry-upload", "cube", "sphere", "cylinder", "torus", "cone", "pyramid", "empty-object"]
ASPECT_LABELS = ["自适应", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16"]


def static_menu():
    src = (ROOT / "src/components/director/DirectorIconRail.tsx").read_text(encoding="utf-8")
    lines = src.split("\n")
    geo_ids = re.findall(r'\{ id: "([a-z0-9-]+)", label: "[^"]+", icon: \w+ \}', src)
    crowd_keys = re.findall(r'data-director-crowd-input=\{(\w+)\}', src)
    z_line = None
    for n, line in enumerate(lines, start=1):
        if "RAIL_FLYOUT_Z = " in line and z_line is None:
            z_line = n
    return {"geometryOptionIds": [g for g in geo_ids if g in GEOMETRY_IDS],
            "crowdInputKeys": crowd_keys, "railFlyoutZLine": z_line,
            "geometrySubmenuZClass": "z-50" if 'z-50 w-[204px]' in src else None}


def menu_state(page):
    return page.evaluate("""([desk]) => {
      const root = document.querySelector(desk);
      const sub = document.querySelector('[data-director-geometry-submenu]');
      const dialog = document.querySelector('[data-director-crowd-dialog]');
      const box = (el) => { const r = el.getBoundingClientRect();
        return {w: Math.round(r.width), h: Math.round(r.height), x: Math.round(r.x), y: Math.round(r.y)}; };
      const inView = (el) => { const r = el.getBoundingClientRect();
        return r.x >= 0 && r.y >= 0 && r.right <= window.innerWidth && r.bottom <= window.innerHeight; };
      const buttons = (root2) => [...root2.querySelectorAll('button')].map(el => {
        el.focus();
        return {id: el.getAttribute('data-director-geometry-option'),
                label: (el.textContent || '').trim().slice(0, 12),
                w: Math.round(el.getBoundingClientRect().width),
                h: Math.round(el.getBoundingClientRect().height),
                opacity: getComputedStyle(el).opacity,
                pe: getComputedStyle(el).pointerEvents,
                inViewport: inView(el), focusOk: document.activeElement === el};
      });
      return {
        submenuPresent: !!sub,
        submenuBox: sub ? {...box(sub), zIndex: getComputedStyle(sub).zIndex,
                           position: getComputedStyle(sub).position,
                           parentIsFixedPortal: !!sub.closest('div[style*="fixed"]'),
                           inRoot: root.contains(sub)} : null,
        options: sub ? buttons(sub) : [],
        dialogPresent: !!dialog,
        dialog: dialog ? {zIndex: getComputedStyle(dialog).zIndex,
                          position: getComputedStyle(dialog).position,
                          inRoot: root.contains(dialog),
                          inFixedPortal: !!dialog.closest('div[style*="fixed"]'),
                          inputs: [...dialog.querySelectorAll('input')].map(i => ({
                            key: i.getAttribute('data-director-crowd-input'), type: i.getAttribute('type'),
                            ...box(i)})),
                          buttons: [...dialog.querySelectorAll('button')].map(x => ({
                            label: (x.textContent || '').trim().slice(0, 10), ...box(x)}))} : null,
        outRootButtons: [...document.querySelectorAll('button, input, select, [role="button"]')]
          .filter(el => !root.contains(el)).length,
        aspectOptions: [...document.querySelectorAll('button')].filter(x => !root.contains(x))
          .filter(x => ['自适应','21:9','16:9','4:3','1:1','3:4','9:16'].includes((x.textContent||'').trim()))
          .map(x => ({label: (x.textContent||'').trim(), ...box(x), inViewport: inView(x)})),
      };
    }""", [DESK])


def edge_handles(page):
    """11 枚连线删除手柄：尺寸、pointer-events、中心 elementFromPoint 命中谁。"""
    return page.evaluate("""() => {
      const hs = [...document.querySelectorAll('button')].filter(b => (b.getAttribute('aria-label') || '') === '删除连线');
      return hs.map(el => { const r = el.getBoundingClientRect();
        const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
        const hit = document.elementFromPoint(cx, cy);
        return {w: Math.round(r.width), h: Math.round(r.height),
                pe: getComputedStyle(el).pointerEvents, opacity: getComputedStyle(el).opacity,
                hitIsSelf: hit === el,
                hitLabel: hit ? ((hit.getAttribute && (hit.getAttribute('aria-label') || hit.getAttribute('data-id')))
                                 || hit.className || hit.tagName).toString().slice(0, 30) : null}; });
    }""")


def open_desk(page, tag, w, h):
    page.goto(f"{BASE}/?batch738={tag}", wait_until="networkidle", timeout=90_000)
    page.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
    page.mouse.move(w - 4, 4)
    page.wait_for_timeout(1_300)
    page.evaluate("() => { document.querySelector('[data-open-director]').click(); }")
    page.wait_for_timeout(2_000)


def open_char_flyout(page):
    page.evaluate("""() => { const b = document.querySelector('[data-director-rail-entry="add-character"]');
      if (b) b.click(); }""")
    page.wait_for_timeout(900)


def click_option(page, option_id):
    return page.evaluate("""(o) => { const b = document.querySelector('[data-director-character-option="' + o + '"]');
      if (!b) return 'MISSING'; b.click(); return 'clicked'; }""", option_id)


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    print("=== 静态 ===")
    menu = static_menu()
    print(f"  源码几何项 {len(menu['geometryOptionIds'])} 个: {menu['geometryOptionIds']}")
    print(f"  群众输入键: {menu['crowdInputKeys']}；RAIL_FLYOUT_Z 在 :{menu['railFlyoutZLine']}；"
          f"子菜单 z 类: {menu['geometrySubmenuZClass']}")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        out = {}

        # ---------- 1440×1000 ----------
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        open_desk(page, "large", 1440, 1000)
        open_char_flyout(page)
        large_base = menu_state(page)
        print(f"\n=== 1440×1000 ===")
        print(f"  flyout 开着：根外 button {large_base['outRootButtons']} 枚；"
              f"几何子菜单在不在={large_base['submenuPresent']}；群众对话框在不在={large_base['dialogPresent']}")

        how_crowd = click_option(page, "crowd-3x3")
        page.wait_for_timeout(900)
        crowd = menu_state(page)
        print(f"\n--- 群众 (3x3)（{how_crowd}）---")
        print(f"  对话框: {json.dumps(crowd['dialog'], ensure_ascii=False)}")
        print(f"  根外 button: {large_base['outRootButtons']} → {crowd['outRootButtons']}")

        # 关群众、开几何
        page.evaluate("""() => { const d = document.querySelector('[data-director-crowd-dialog]');
          if (d) { const x = [...d.querySelectorAll('button')]
            .find(b => ['取消','关闭'].includes((b.textContent||'').trim())); if (x) x.click(); } }""")
        page.wait_for_timeout(700)
        if not page.evaluate("""() => Boolean(document.querySelector('[data-director-character-option="geometry"]'))"""):
            open_char_flyout(page)
        how_geo = click_option(page, "geometry")
        page.wait_for_timeout(900)
        geo = menu_state(page)
        print(f"\n--- 几何模型子菜单（{how_geo}）---")
        print(f"  盒子: {json.dumps(geo['submenuBox'], ensure_ascii=False)}")
        for o in geo["options"]:
            print(f"    {o['id']:14s} {o['w']}x{o['h']} 在视口内={o['inViewport']} "
                  f"opacity={o['opacity']} pe={o['pe']} focus()={o['focusOk']}")
        print(f"  根外 button: {crowd['outRootButtons']} → {geo['outRootButtons']}")

        handles_large = edge_handles(page)
        print(f"\n  连线删除手柄 {len(handles_large)} 枚："
              f"pe 全为 none = {all(h['pe'] == 'none' for h in handles_large)}；"
              f"中心命中自己 = {sum(1 for h in handles_large if h['hitIsSelf'])}/{len(handles_large)}")
        page.close()

        # ---------- 1100×700 ----------
        page2 = browser.new_page(viewport={"width": 1100, "height": 700})
        open_desk(page2, "small", 1100, 700)
        open_char_flyout(page2)
        click_option(page2, "geometry")
        page2.wait_for_timeout(900)
        geo_small = menu_state(page2)
        print(f"\n=== 1100×700 ===")
        print(f"  盒子: {json.dumps(geo_small['submenuBox'], ensure_ascii=False)}")
        for o in geo_small["options"]:
            print(f"    {o['id']:14s} {o['w']}x{o['h']} 在视口内={o['inViewport']} focus()={o['focusOk']}")

        # 画幅比例
        page2.evaluate("""() => { const g = document.querySelector('[data-director-character-option="geometry"]');
          if (g) g.click(); }""")
        page2.wait_for_timeout(500)
        page2.evaluate("""() => { const a = document.querySelector('[data-director-rail-entry="aspect-ratio"]');
          if (a) a.click(); }""")
        page2.wait_for_timeout(900)
        aspect = menu_state(page2)
        print(f"\n  画幅比例 {len(aspect['aspectOptions'])} 枚：")
        for a in aspect["aspectOptions"]:
            print(f"    {a['label']!r:8s} {a['w']}x{a['h']} @({a['x']},{a['y']}) 在视口内={a['inViewport']}")
        page2.close()
        browser.close()

    options_large = geo["options"]
    options_small = geo_small["options"]
    aspect_all_in = all(a["inViewport"] for a in aspect["aspectOptions"])
    summary = {
        "staticGeometryItems": len(menu["geometryOptionIds"]),
        "crowdInputKeys": len(menu["crowdInputKeys"]),
        "crowdInputs": len(crowd["dialog"]["inputs"]) if crowd["dialog"] else 0,
        "crowdButtons": len(crowd["dialog"]["buttons"]) if crowd["dialog"] else 0,
        "crowdTotal": (len(crowd["dialog"]["inputs"]) + len(crowd["dialog"]["buttons"])) if crowd["dialog"] else 0,
        "crowdZIndex": crowd["dialog"]["zIndex"] if crowd["dialog"] else None,
        "crowdPosition": crowd["dialog"]["position"] if crowd["dialog"] else None,
        "crowdInRoot": crowd["dialog"]["inRoot"] if crowd["dialog"] else None,
        "geometryCountLarge": len(options_large),
        "geometryCountSmall": len(options_small),
        "geometryAllVisibleLarge": all(o["inViewport"] and o["opacity"] == "1" and o["pe"] == "auto"
                                       and o["focusOk"] for o in options_large),
        "geometryAllVisibleSmall": all(o["inViewport"] and o["opacity"] == "1" and o["pe"] == "auto"
                                       and o["focusOk"] for o in options_small),
        "submenuZIndex": geo["submenuBox"]["zIndex"],
        "submenuPosition": geo["submenuBox"]["position"],
        "submenuParentFixedPortal": geo["submenuBox"]["parentIsFixedPortal"],
        "submenuInRoot": geo["submenuBox"]["inRoot"],
        "outRootFlyout": large_base["outRootButtons"],
        "outRootCrowd": crowd["outRootButtons"],
        "outRootGeometry": geo["outRootButtons"],
        "aspectCount": len(aspect["aspectOptions"]),
        "aspectAllInViewport": aspect_all_in,
        "handles": len(handles_large),
        "handlesAllPeNone": all(h["pe"] == "none" for h in handles_large),
        "handlesAllTiny": all(h["w"] == 8 and h["h"] == 8 for h in handles_large),
        "handlesSelfHit": sum(1 for h in handles_large if h["hitIsSelf"]),
    }
    print("\n=== 汇总 ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    checks = [
        ("C1 群众弹窗 portal + z-160，1 写点 → 5 枚（3 number + 2 button）",
         summary["crowdInputs"] == 3 and summary["crowdButtons"] == 2
         and summary["crowdTotal"] == 5 and summary["crowdZIndex"] == "160"
         and summary["crowdPosition"] == "fixed" and summary["crowdInRoot"] is False,
         f"inputs={summary['crowdInputs']} buttons={summary['crowdButtons']} "
         f"z={summary['crowdZIndex']} pos={summary['crowdPosition']} inRoot={summary['crowdInRoot']}"),
        ("C2 几何子菜单 8 枚，源码 8 项且 pyramid/empty-object 在其中",
         summary["staticGeometryItems"] == 8 and summary["geometryCountLarge"] == 8
         and [o["id"] for o in options_large] == GEOMETRY_IDS,
         f"静态 {summary['staticGeometryItems']} 项 / 运行时 {summary['geometryCountLarge']} 枚："
         f"{[o['id'] for o in options_large]}"),
        ("C3 1440×1000：8/8 在视口内 + opacity 1 + pe auto + focus() 成功",
         summary["geometryAllVisibleLarge"] is True, str(summary["geometryAllVisibleLarge"])),
        ("C4 1100×700：8/8 同上（625「埋掉 6 枚」不复现）",
         summary["geometryAllVisibleSmall"] is True and summary["geometryCountSmall"] == 8,
         f"small {summary['geometryCountSmall']} 枚 allVisible={summary['geometryAllVisibleSmall']}"),
        ("C5 子菜单 computed z-index=50 / absolute，父容器是 fixed portal",
         summary["submenuZIndex"] == "50" and summary["submenuPosition"] == "absolute"
         and summary["submenuParentFixedPortal"] is True and summary["submenuInRoot"] is False,
         f"z={summary['submenuZIndex']} pos={summary['submenuPosition']} "
         f"parentFixed={summary['submenuParentFixedPortal']} inRoot={summary['submenuInRoot']}"),
        ("C6 画幅比例 7 枚（含 9:16）在 1100×700 全在视口内",
         summary["aspectCount"] == 7 and summary["aspectAllInViewport"] is True,
         f"{summary['aspectCount']} 枚 allIn={summary['aspectAllInViewport']}："
         f"{[a['label'] for a in aspect['aspectOptions']]}"),
        ("C7 根外 button 轨迹 47 → 52 → 55",
         (summary["outRootFlyout"], summary["outRootCrowd"], summary["outRootGeometry"])
         == (47, 52, 55),
         f"{summary['outRootFlyout']} → {summary['outRootCrowd']} → {summary['outRootGeometry']}"),
        ("C8 两个子菜单的控件都不在 workspace 根内",
         summary["crowdInRoot"] is False and summary["submenuInRoot"] is False,
         f"crowd inRoot={summary['crowdInRoot']} / geometry inRoot={summary['submenuInRoot']}"),
        ("C9 11 枚连线删除手柄 8×8 且 pe=none，中心命中自己 0/11",
         summary["handles"] == 11 and summary["handlesAllPeNone"] is True
         and summary["handlesAllTiny"] is True and summary["handlesSelfHit"] == 0,
         f"{summary['handles']} 枚 8x8={summary['handlesAllTiny']} peNone={summary['handlesAllPeNone']} "
         f"selfHit={summary['handlesSelfHit']}"),
    ]

    print("\n=== 判据 ===")
    failures = []
    for name, ok, detail in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}  ⟵ {detail}")
        if not ok:
            failures.append(name)

    payload = {
        "static": {"menu": menu, "railFlyoutZLine": menu["railFlyoutZLine"]},
        "run": {"large": {"base": large_base, "crowd": crowd, "geometry": geo,
                          "handles": handles_large},
                "small": {"geometry": geo_small, "aspect": aspect}},
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
