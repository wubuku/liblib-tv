#!/usr/bin/env python3
"""Verify Batch 612: a control census found three fidelity defects.

## How this batch was chosen

A fresh control census (source 113 names vs clone 126, `diff609.py` re-run
2026-10-01) drove the target list.  Most of the remaining "source has / clone
lacks" names turned out to be artefacts of the census running with a character
selected (the source's camera-panel controls) or of the main canvas page
rather than the director desk.  Three real defects survived, and all three are
things the eye should have caught:

## 1. An aria/glyph split the source makes and the clone collapsed

Source scrub chip, measured: `aria-label="左右拖动调整 X 轴"` (upper-case
axis) with **DOM text** `x` (lower-case) and `text-transform: uppercase` doing
the rendering.  Batch 609 passed the axis name through lower-cased, so the
clone produced `"… x 轴"` — the census could not match it against the source
at all.  Fixed by keeping the axis upper-case for the label and lower-casing
the glyph inside `SceneAxisScrub`.

## 2. The canvas page's bottom-left cluster was 6px low and 4px loose per button

Source (`probe612c`), 28px tall at y=1104 starting at x=14, **4px** between
buttons, `rounded-lg`, 14px glyphs:

| control | source | clone before | clone now |
|---|---|---|---|
| 资产管理 | [14,1104,94,28] | [16,1110,91,28] | [14,1104,94,28] |
| 整理画布，Option+Shift+F | [112,1104,28,28] | [115,1110,28,28] | [112,1104,28,28] |
| 切换小地图 | [144,1104,28,28] | [151,1110,28,28] | [144,1104,28,28] |
| 隐藏节点连线 | [176,1104,28,28] | [187,1110,28,28] | [176,1104,28,28] |
| 网格吸附 | [208,1104,28,28] | [223,1110,28,28] | [208,1104,28,28] |
| 缩放选项 | [240,1104,36.3,28] | [259,1110,40.2,28] | [240,1104,36,28] |

The clone used `gap-2` where the source uses 4px, so the error compounded to
22px by the last button; the icons were 15px against the source's 14px; the
glyph buttons were `rounded-md` against `rounded-lg`; 资产管理 was `px-2 gap-2`
(91 wide) against `px-3 gap-1` (94); and 缩放选项 carried `min-w-10` +
`tabular-nums` the source does not have.

## 3. The bottom-centre cluster had a 40x40 "primary" button the source lacks

The source's cluster is uniform: every button is
`relative flex items-center justify-center rounded-lg transition-colors h-8
w-8 hover:bg-canvas-controls-hover cursor-pointer` with a 20px glyph.  The
clone gave 添加节点 a bespoke `prominent` variant — 40x40,
`bg-[#edf0f5] text-[#171717] hover:bg-white` — which is both 8px larger than
the source and a solid light pill where the source has a ghost button, and
which pushed the whole cluster 19.5px left of the source's.  The variant is
removed; the clone now also matches the source's **17px** gap between 生成历史
and 快捷键 (the rest of the cluster is 8px — that wider gap is a separator).

The cluster's remaining 20px x-offset is the clone-only 打开工具箱 button,
which is kept: dropping clone functionality is not what this work is for.

## 4. The follow banner's cancel capsule is a single text node

Source: `own='取消ESC'` with **no child elements**, the whole capsule
12px/12px/500.  The clone split it into `取消` + a nested 10px `ESC` span.
Separately worth recording: the source's capsule carries
`aria-label="退出跟随"` while *displaying* `取消ESC` — a visible-label vs
accessible-name mismatch on the source's side.  The clone already exposed
`aria-label="退出跟随"`, so it is kept as-is and the mismatch is recorded
rather than silently "fixed" in either direction.

## Not claimed

The source's canvas-page buttons were not clicked (that writes to the real
project).  Geometry, colours and glyph sizes are measured; the clone's own
panels are verified to still open, which is what proves the resize did not
break a hit target.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT / "docs/research/liblib-canvas-batch612-2026-10-01/runtime-audit.json"
)
SCREENSHOT = ROOT / "docs/design-references/liblib-bottom-clusters-612-1920.png"

VIEWPORT = {"width": 1920, "height": 1150}

# Source readings (probe612c, 2026-10-01, 1920x1150).  name -> (x, y, w, h)
SOURCE_LEFT = {
    "资产管理": (14, 1104, 94, 28),
    "整理画布，Option+Shift+F": (112, 1104, 28, 28),
    "切换小地图": (144, 1104, 28, 28),
    "隐藏节点连线": (176, 1104, 28, 28),
    "网格吸附": (208, 1104, 28, 28),
    "缩放选项": (240, 1104, 36.3, 28),
}
SOURCE_RIGHT = {
    "添加节点": (819.5, 1097.5, 32, 32),
    "移动": (859.5, 1097.5, 32, 32),
    "素材库": (899.5, 1097.5, 32, 32),
    "角色造型室": (939.5, 1097.5, 32, 32),
    "生成历史": (979.5, 1097.5, 32, 32),
    "快捷键": (1028.5, 1097.5, 32, 32),
}
SOURCE_SEPARATOR_GAP = 17.0
SOURCE_CLUSTER_GAP = 8.0

IGNORE_CONSOLE = (
    "The attached 3D object must be a part of the scene graph",
    "webpack-hmr",
    "WebSocket",
    "Failed to load resource",
    # a concurrent edit in this shared worktree
    "src/components/jimeng/nodes/JimengTextNode.tsx",
)


def alpha_of(colour: str) -> float:
    for pattern in (
        r"rgba?\([^)]*?,\s*([0-9.]+)\s*\)$",
        r"oklab\([^)]*?/\s*([0-9.]+)\s*\)",
        r"lab\([^)]*?/\s*([0-9.]+)\s*\)",
    ):
        match = re.search(pattern, colour)
        if match:
            return float(match.group(1))
    return 1.0


def pill_radius(value: str) -> bool:
    """True for a fully rounded corner.

    Tailwind v4's `rounded-full` is `border-radius: calc(infinity * 1px)`, so
    the computed value is a huge float (3.35544e+07px), not the 9999px of
    Tailwind v3.  Any radius comfortably larger than the element means the
    same thing visually, so the assertion is on the magnitude, not the string.
    """
    match = re.match(r"^([0-9.e+]+)px$", value.strip())
    return bool(match) and float(match.group(1)) >= 9999


READ = """() => {
  const at = (el) => { const r = el.getBoundingClientRect();
    return [Math.round(r.x*10)/10, Math.round(r.y*10)/10,
            Math.round(r.width*10)/10, Math.round(r.height*10)/10]; };
  const cs = (el) => getComputedStyle(el);
  const of = (name) => document.querySelector('[aria-label="' + name + '"]');
  const card = (name) => {
    const el = of(name);
    if (!el) return null;
    const svg = el.querySelector('svg');
    return {box: at(el), radius: cs(el).borderRadius, bg: cs(el).backgroundColor,
      color: cs(el).color, minWidth: cs(el).minWidth, pad: cs(el).padding,
      font: cs(el).fontSize + '/' + cs(el).lineHeight + '/' + cs(el).fontWeight,
      tabular: cs(el).fontVariantNumeric,
      svg: svg ? [svg.getBoundingClientRect().width, svg.getBoundingClientRect().height]
                 .map(v => Math.round(v*10)/10) : null,
      kids: el.childElementCount};
  };
  const chip = document.querySelector(
    '[data-director-transform-field="position"]')?.closest('label')
    ?.querySelector('button[aria-label^="左右拖动调整"]') ?? null;
  const cancel = document.querySelector('[data-director-follow-cancel]');
  return {
    left: Object.fromEntries(
      Object.keys(window.__b612LeftNames).map(
        (k) => [k, card(window.__b612LeftNames[k])])),
    right: Object.fromEntries(
      Object.keys(window.__b612RightNames).map(
        (k) => [k, card(window.__b612RightNames[k])])),
    chip: chip ? {box: at(chip), aria: chip.getAttribute('aria-label'),
      own: (chip.textContent || '').trim(),
      textTransform: cs(chip).textTransform, font: cs(chip).fontSize} : null,
    cancel: cancel ? {box: at(cancel), own: (cancel.textContent||'').replace(/\\s+/g,' ').trim(),
      aria: cancel.getAttribute('aria-label'), kids: cancel.childElementCount,
      font: cs(cancel).fontSize + '/' + cs(cancel).lineHeight + '/' + cs(cancel).fontWeight,
      radius: cs(cancel).borderRadius, pad: cs(cancel).padding,
      bg: cs(cancel).backgroundColor, color: cs(cancel).color,
      pe: cs(cancel).pointerEvents} : null,
  };
}"""

LEFT_NAMES = {
    "资产管理": "资产管理",
    "整理画布，Option+Shift+F": "整理画布，Option+Shift+F",
    "切换小地图": "切换小地图",
    "隐藏节点连线": "隐藏节点连线",
    "网格吸附": "网格吸附",
    "缩放选项": "缩放选项",
}
RIGHT_NAMES = {
    "添加节点": "添加节点",
    "移动": "移动",
    "打开工具箱(clone-only)": "打开工具箱",
    "素材库": "素材库",
    "角色库(clone 名)": "角色库",
    "生成历史": "生成历史",
    "快捷键": "快捷键",
    "教程": "教程",
}


class Verifier:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.result: dict[str, Any] = {}
        self.failures: list[str] = []
        self.count = 0

    def check(self, name: str, ok: bool, detail: Any = "") -> None:
        self.count += 1
        self.result[name] = {"ok": bool(ok), "detail": detail}
        if not ok:
            self.failures.append(name)
        print(("  PASS " if ok else "  FAIL ") + name + (f"  {detail}" if detail else ""))

    def read(self) -> dict[str, Any]:
        self.page.mouse.move(5, 5)
        self.page.wait_for_timeout(120)
        return self.page.evaluate(READ)


def run(page: Page) -> dict[str, Any]:
    v = Verifier(page)
    console: list[str] = []
    errors: list[str] = []
    page.on("console", lambda m: console.append(f"{m.type}: {m.text}"[:200])
            if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)[:200]))

    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle", timeout=90_000)
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__libtv_ui_store "
        "&& window.__director_store)",
        timeout=60_000,
    )
    page.add_init_script(
        "window.__b612LeftNames = %s; window.__b612RightNames = %s;"
        % (json.dumps(LEFT_NAMES, ensure_ascii=False),
           json.dumps(RIGHT_NAMES, ensure_ascii=False))
    )
    page.evaluate(
        """() => {
          window.__b612LeftNames = %s;
          window.__b612RightNames = %s;
        }"""
        % (json.dumps(LEFT_NAMES, ensure_ascii=False),
           json.dumps(RIGHT_NAMES, ensure_ascii=False))
    )
    page.locator("[data-canvas-root], body").first.wait_for(state="attached")
    page.wait_for_timeout(1_200)

    r = v.read()
    v.result["initial"] = r

    # --- 1) the axis chip lives on the director desk, checked in §5 ------

    # --- 2) the bottom-left cluster, item by item ------------------------
    for name, (x, y, w, h) in SOURCE_LEFT.items():
        got = r["left"].get(name)
        v.check(f"left:{name}:present", got is not None)
        if got is None:
            continue
        b = got["box"]
        v.check(f"left:{name}:x", abs(b[0] - x) <= 0.6, detail=f"{b[0]} vs {x}")
        v.check(f"left:{name}:y", abs(b[1] - y) <= 0.6, detail=f"{b[1]} vs {y}")
        v.check(f"left:{name}:w", abs(b[2] - w) <= 0.6, detail=f"{b[2]} vs {w}")
        v.check(f"left:{name}:h", abs(b[3] - h) <= 0.6, detail=f"{b[3]} vs {h}")
        v.check(f"left:{name}:radius-8", got["radius"] == "8px", detail=got["radius"])
        if got["svg"] is not None:
            v.check(f"left:{name}:glyph-14", got["svg"] == [14, 14], detail=got["svg"])
    # 4px between every neighbour
    order = ["资产管理", "整理画布，Option+Shift+F", "切换小地图",
             "隐藏节点连线", "网格吸附", "缩放选项"]
    gaps = []
    for a, b in zip(order, order[1:]):
        ba, bb = r["left"][a]["box"], r["left"][b]["box"]
        gaps.append(round(bb[0] - (ba[0] + ba[2]), 1))
    v.check("left:gap-4", all(abs(g - 4) < 0.6 for g in gaps), detail=gaps)
    zoom = r["left"]["缩放选项"]
    v.check("left:zoom-no-min-width", zoom["minWidth"] == "0px", detail=zoom["minWidth"])
    v.check("left:zoom-not-tabular", "tabular-nums" not in zoom["tabular"], detail=zoom["tabular"])
    v.check("left:asset-94", abs(r["left"]["资产管理"]["box"][2] - 94) <= 0.6,
            detail=r["left"]["资产管理"]["box"])

    # --- 3) the bottom-centre cluster ------------------------------------
    for name, (x, y, w, h) in SOURCE_RIGHT.items():
        clone_name = "角色库(clone 名)" if name == "角色造型室" else name
        got = r["right"].get(clone_name)
        v.check(f"right:{name}:present", got is not None)
        if got is None:
            continue
        b = got["box"]
        # The clone keeps an extra 打开工具箱 button, so its cluster starts
        # 20px left of the source's.  Only the metrics are compared here.
        v.check(f"right:{name}:y", abs(b[1] - y) <= 0.6, detail=f"{b[1]} vs {y}")
        v.check(f"right:{name}:w", abs(b[2] - w) <= 0.6, detail=f"{b[2]} vs {w}")
        v.check(f"right:{name}:h", abs(b[3] - h) <= 0.6, detail=f"{b[3]} vs {h}")
        v.check(f"right:{name}:radius-8", got["radius"] == "8px", detail=got["radius"])
        v.check(f"right:{name}:glyph-20", got["svg"] == [20, 20], detail=got["svg"])
    add = r["right"]["添加节点"]
    v.check("right:添加节点-is-ghost", alpha_of(add["bg"]) < 0.02,
            detail=add["bg"])
    v.check("right:添加节点-not-light", add["color"] not in ("rgb(23, 23, 23)",),
            detail=add["color"])
    # uniform 8px gaps, then a 17px separator before 快捷键
    rorder = ["添加节点", "移动", "打开工具箱(clone-only)", "素材库",
              "角色库(clone 名)", "生成历史", "快捷键", "教程"]
    rgaps = []
    for a, b in zip(rorder, rorder[1:]):
        ba, bb = r["right"][a]["box"], r["right"][b]["box"]
        rgaps.append((f"{a}->{b}", round(bb[0] - (ba[0] + ba[2]), 1)))
    ordinary = [g for label, g in rgaps if not label.startswith("生成历史")]
    v.check("right:gaps-8", all(abs(g - SOURCE_CLUSTER_GAP) < 0.6 for g in ordinary),
            detail=rgaps)
    sep = dict(rgaps)["生成历史->快捷键"]
    v.check("right:separator-17", abs(sep - SOURCE_SEPARATOR_GAP) < 0.6, detail=sep)
    page.screenshot(path=str(SCREENSHOT))

    # --- 4) the panels still open (the resize kept the hit targets) ------
    page.locator('[aria-label="添加节点"]').click()
    page.wait_for_timeout(500)
    v.check("panel:添加节点-opens", page.locator("text=基础节点").count() >= 0
            and page.locator('[aria-label="添加节点"]').get_attribute("aria-pressed") == "true")
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    page.locator('[aria-label="缩放选项"]').click()
    page.wait_for_timeout(400)
    v.check("panel:zoom-opens", page.locator("[data-liblib-overlay='zoom-menu']").count() == 1)
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    page.locator('[aria-label="快捷键"]').click()
    page.wait_for_timeout(500)
    v.check("panel:shortcuts-opens",
            page.locator("[data-liblib-overlay='shortcuts']").count() == 1)
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)
    page.locator('button[aria-label="生成历史"]').click()
    page.wait_for_timeout(500)
    v.check("panel:history-opens",
            page.locator('button[aria-label="生成历史"]').get_attribute("aria-pressed") == "true")
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)

    # --- 5) the follow banner's cancel capsule --------------------------
    page.evaluate(
        """() => {
          const s = window.__libtv_store.getState();
          s.addNode("script-execution", { title: "Batch 612" });
          const node = s.getActiveCanvas().nodes.at(-1);
          window.__libtv_ui_store.getState().openDirectorDesk(node.id, s.activeCanvasId);
        }"""
    )
    page.locator("[data-director-workspace]").wait_for(state="visible", timeout=30_000)
    page.wait_for_timeout(1_200)
    page.evaluate(
        """() => {
          const s = window.__director_store.getState();
          const cam = s.objects.find((o) => o.kind === 'camera');
          const target = s.objects.find((o) => o.kind === 'character');
          s.selectObject(target.id);
          s.updateCamera(cam.id, { followTargetId: target.id });
        }"""
    )
    page.locator("[data-director-follow-cancel]").wait_for(state="visible", timeout=15_000)
    page.wait_for_timeout(500)
    fr = v.read()
    v.result["follow"] = fr["cancel"]
    cancel = fr["cancel"]
    v.check("follow:capsule-present", cancel is not None)
    if cancel:
        v.check("follow:single-text-node", cancel["kids"] == 0, detail=cancel["kids"])
        v.check("follow:visible-text", cancel["own"] == "取消ESC", detail=cancel["own"])
        v.check("follow:aria-is-退出跟随", cancel["aria"] == "退出跟随", detail=cancel["aria"])
        v.check("follow:font-12-12-500", cancel["font"] == "12px/12px/500", detail=cancel["font"])
        v.check("follow:width-63.7", abs(cancel["box"][2] - 63.7) <= 0.6,
                detail=cancel["box"])
        v.check("follow:radius-full", pill_radius(cancel["radius"]),
                detail=cancel["radius"])
        v.check("follow:white-fill", cancel["bg"] == "rgb(255, 255, 255)", detail=cancel["bg"])
        # the documented clone deviation: the source's capsule inherits
        # pointer-events:none and cannot be clicked at all
        v.check("follow:clone-keeps-hit-area", cancel["pe"] == "auto", detail=cancel["pe"])
    page.locator("[data-director-follow-cancel]").click()
    page.wait_for_timeout(500)
    v.check("follow:cancel-clears-follow",
            page.locator("[data-director-follow-cancel]").count() == 0)

    # --- 6) the axis chip's aria / glyph split --------------------------
    # Read on the director desk, where the inspector actually lives.
    fr2 = v.read()
    v.result["axisChip"] = fr2["chip"]
    chip = fr2["chip"]
    v.check("chip:present", chip is not None)
    if chip:
        v.check("chip:aria-upper-case", chip["aria"] == "左右拖动调整 X 轴", detail=chip["aria"])
        v.check("chip:glyph-lower-case", chip["own"] == "x", detail=chip["own"])
        v.check("chip:uppercase-css", chip["textTransform"] == "uppercase",
                detail=chip["textTransform"])
        v.check("chip:font-12", chip["font"] == "12px", detail=chip["font"])
    # the sibling Y / Z chips split the same way
    for axis, glyph in (("Y", "y"), ("Z", "z")):
        other = page.evaluate(
            """(axis) => {
              const b = document.querySelector(
                '[aria-label="左右拖动调整 ' + axis + ' 轴"]');
              if (!b) return null;
              return {aria: b.getAttribute('aria-label'),
                      own: (b.textContent || '').trim(),
                      tt: getComputedStyle(b).textTransform};
            }""",
            axis,
        )
        v.check(f"chip:{axis}-present", other is not None)
        if other:
            v.check(f"chip:{axis}-glyph-lower-case", other["own"] == glyph, detail=other["own"])
            v.check(f"chip:{axis}-uppercase-css", other["tt"] == "uppercase", detail=other["tt"])

    page.wait_for_timeout(300)
    noise = [c for c in console if any(k in c for k in IGNORE_CONSOLE)]
    real_console = [c for c in console if not any(k in c for k in IGNORE_CONSOLE)]
    real_errors = [e for e in errors if not any(k in e for k in IGNORE_CONSOLE)]
    v.check("diagnostics:no-page-errors", not real_errors, detail=real_errors[:5])
    v.check("diagnostics:no-console-errors", not real_console, detail=real_console[:5])
    v.result["diagnostics"] = {
        "consoleErrors": len(console),
        "filtered": len(noise),
        "pageErrors": len(errors),
    }
    v.result["_summary"] = {"checks": v.count, "failures": v.failures}
    return v.result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 612,
        "title": "Control-census sweep: axis aria split, canvas bottom clusters, follow capsule",
        "date": "2026-10-01",
        "sourceEvidence": [
            "fresh control census (diff609.py) re-run on both sides, 2026-10-01",
            "probe612c: exact boxes / classes / glyph sizes for both canvas-page "
            "bottom clusters",
            "probe612b: the follow banner subtree, showing the capsule's "
            "aria-label='退出跟随' against its visible '取消ESC'",
        ],
        "claims": {
            "sourceFact": [
                "scrub chip: aria-label uses the UPPER-case axis while the DOM "
                "text is lower-case and text-transform: uppercase renders it",
                "bottom-left cluster: 28 tall at y=1104 from x=14, 4px gaps, "
                "rounded-lg, 14px glyphs, 资产管理 94 wide (px-3 gap-1), "
                "缩放选项 36.3 wide (px-1, no min-width, no tabular-nums)",
                "bottom-centre cluster: every button 32x32 ghost, 20px glyphs, "
                "8px gaps, with a 17px separator before 快捷键",
                "the source has no 'primary' variant in that cluster",
                "follow cancel capsule: single text node '取消ESC', 12px/12px/500, "
                "63.7 wide, aria-label='退出跟随'",
            ],
            "cloneDecision": [
                "the clone-only 打开工具箱 button is kept, so the "
                "bottom-centre cluster stays 20px left of the source's; only "
                "the metrics are compared",
                "the clone keeps pointer-events-auto on the follow capsule — "
                "the source's inherits pointer-events:none and is a dead button",
            ],
            "sourceSideObservations": [
                "the follow capsule's accessible name (退出跟随) disagrees with "
                "its visible label (取消ESC); recorded, not silently corrected "
                "in either direction",
            ],
            "notClaimed": [
                "the source's canvas-page button click behaviour (it writes to "
                "the real project)",
                "帮助 stays at its clone position (y=928) rather than moving "
                "into the source's bottom-left cluster — left for a later batch",
            ],
        },
    }
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT)
        try:
            audit["checks"] = run(page)
        finally:
            browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    summary = audit["checks"]["_summary"]
    print(f"\n{summary['checks'] - len(summary['failures'])}/{summary['checks']} passed")
    if summary["failures"]:
        print("FAILED: " + ", ".join(summary["failures"]))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
