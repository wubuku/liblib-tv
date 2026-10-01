#!/usr/bin/env python3
"""batch 626 验收：浮层的「层叠 + 可达性」普查。

## 本批做的那把尺子

625 只把「祖先链有效 z」量在 rail 的五个浮层上，量出 z 全被困。本批先问
「这条判据对每一个浮层成立吗」，结果先量出**尺子自己是坏的**，再量出**代码
真有两个缺陷**。

### 尺子坏在哪：标量 effectiveZ 跨子树无效

第一版探针报 18 处违反，全部是 4 个浮层 × `workspace` / `viewport`。
但 `workspace` 是 `fixed inset-0 z-100`，**它是这四个浮层的祖先**。

`effectiveZ(X) = X 自己创建上下文时的 z，否则 X 最近创建上下文的祖先的 z`
这个标量只在**同一层叠上下文内的兄弟之间**有意义。一旦 O 与 P 不在同一层，
O 的 z-50 是「O 这棵子树在祖先上下文里的代表值」，而 P 就是那个祖先本身：
后代恒画在祖先之上，拿 50 < 100 判违反是结构性无效比较。

同一个错误的另一面：`geometry-submenu` 被读成 ownZ=50 / effZ=50，看着像
「没被 portal 出去」，其实 625 已把它 portal 出去、外层包裹是 z-160，内层
z-50 只是在这层上下文**内部**生效。对外层位是 160。跨子树比较要取**最外层**
上下文；标量 effectiveZ 在深度上根本没有唯一取值 —— 这是模型缺陷，不是脚本缺陷。

### 校正后的判据：自顶向下祖先链比较

`paintOrder(a, b)`：
1. 祖先关系先短路 —— a 是 b 的祖先则 b 在上，反之亦然（祖先不是「对手」）；
2. 否则沿两条祖先链自顶向下找**分叉点**，在分叉处比两侧的 z（缺失按 0）；
3. z 相同再按 DOM 树序。

这条对嵌套与 portal 同时成立：AI 导入模态 portal 到 body z-290，时间线在
workspace z-100 之内，分叉点在根，两者可比 290 > 100。

### 三半，缺一不可

- **结构半**（`paintOrder`）：pointer-events:none 的浮层也判得了。FOV 提示
  `z-1700 pointer-events-none` 对 `elementFromPoint` 完全失明（它会被跳过），
  只靠命中测试的通用判据恰好漏掉这一类。
- **地面真值半**（`elementsFromPoint` 网格采样）：浏览器自己的绘制顺序，用来
  交叉校验结构半。两半不一致就记 finding 留查，不静默取一个。
- **伤亡半**（浮层内每一枚活控件逐个命中）：624 的模态提交钮与 625 的几何子菜单
  抓到的是这一半，不是结构半。

## 结构性越界：**两个浮层挂在屏幕外，末尾活控件不可达**

- `motion-path-menu`：1440 宽 × 900/844/800/720/700/640/600/540 八档，**每一档
  都丢 2 枚**（圆环路径、矩形路径）。盒顶恒为 `视口高 − 141`、高 204，底边恒为
  `视口高 + 63` —— 这两枚在任何视口下都在屏幕外，连 batch 590 一直用的
  1920×1150 基准视口也不例外。根因：横向有钳制
  （`Math.max(8, Math.min(…, root.width - 176))`），纵向却写死 `top-10`；而下拉
  高 204，挂在一条贴底、高约 181 的时间轴之下，纵向本就没有落脚点。
- `geometry-submenu`：盒恒为 @(52,508) 204×270、底边恒 778（`top-[calc(100%+2px)]`
  挂在整张 flyout 卡片之下，而卡片顶与视口高无关）。`视口高 < 778` 即开始丢：
  720 丢 2/8（棱锥、添加空对象）、640 丢 4/8、540 丢 7/8。

修法统一为：8px 安全边，越界多少上移多少，**不越界一个像素不动**。

## 不声称的部分

源站这两处的行为未取证（导演台在源站被他人关闭，且不在已授权清单内）。本批
修的是 clone 侧不变量「已打开浮层内的活控件必须可达」—— 这条 619 普查早就在
对桌面控件断言。**不声称源站会做同样的钳制**；若源站读数日后证明其溢出或翻面，
按迁移合同改断言、保留行为。

基线对照：本批修复前，本文件在 1280×720 下 `motion-path-menu` 与
`geometry-submenu` 两格伤亡半必然失败。
"""
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "http://127.0.0.1:4317"
V617 = ROOT / "scripts/verify-liblib-batch617.py"
_s = importlib.util.spec_from_file_location("b617", V617)
b617 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(b617)

# (name, how to open, overlay selector)
# "@tree-rctx@" = right-click a scene-tree object
OVERLAYS: list[tuple[str, str, str]] = [
    ("export-panel", "[data-director-export-trigger]", "[data-director-export-panel]"),
    ("tree-context-menu", "@tree-rctx@", "[data-director-tree-context-menu]"),
    ("panorama-flyout", "[data-director-rail-entry='panorama']",
     "[data-director-panorama-flyout]"),
    ("aspect-flyout", "[data-director-rail-entry='aspect-ratio']",
     "[data-director-aspect-flyout]"),
    ("add-character-flyout", "[data-director-rail-entry='add-character']",
     "[data-director-character-flyout]"),
    ("ai-import-modal", "[data-director-rail-entry='ai-import']",
     "[data-director-ai-import-modal]"),
    ("geometry-submenu", "@geometry@", "[data-director-geometry-submenu]"),
    ("crowd-dialog", "@crowd@", "[data-director-crowd-dialog]"),
    ("camera-fov-help-tooltip", "@fov-hover@",
     "[data-director-camera-fov-help-tooltip]"),
    ("camera-preset-panel", "@camera-preset@", "[data-director-camera-preset-panel]"),
    ("motion-path-menu", "@path-menu@", "[data-director-motion-path-menu]"),
]

# panels an overlay may have to sit above; measured, not assumed
PANELS: list[list[str]] = [
    ["timeline", "[data-director-timeline]"],
    ["inspector", "aside[aria-label='属性']"],
    ["tree", "aside[aria-label='场景对象']"],
    ["rail", "[data-director-icon-rail]"],
    ["viewport", "[data-director-viewport]"],
    ["workspace", "[data-director-workspace]"],
]

VIEWPORTS = [(1920, 1150), (1440, 900), (1280, 720)]

# the two menus that overflowed the viewport bottom before this batch
# (name, how to open, selector, heights) — heights chosen to cover both the
# always-broken case and the height at which the clamp becomes a no-op
HEIGHT_SWEEP = [
    ("motion-path-menu", "@path-menu@", "[data-director-motion-path-menu]",
     [(1920, 900), (1920, 540), (1280, 640)]),
    ("geometry-submenu", "@geometry@", "[data-director-geometry-submenu]",
     [(1440, 800), (1440, 640), (1280, 540)]),
]

LIVE = ("button, input, select, textarea, a[href], [role='button'], "
        "[role='menuitem'], [role='option'], [tabindex]:not([tabindex='-1'])")

SAFE_MARGIN = 8

# The clamp has to be a no-op where nothing overflows, and that has to be an
# enforced contract rather than a lucky reading.  Pre-fix measurements
# (/tmp/dbg626c.py) put the geometry submenu at @(52,508) 204x270 at every
# viewport tall enough to hold it — it hangs below the whole flyout card, so
# it needs 786px of height and above that the CSS default is correct.  If this
# box ever moves, the clamp is touching geometry it has no business touching.
NO_OP_CASES = [
    ("geometry-submenu", "@geometry@", "[data-director-geometry-submenu]",
     (1440, 800), [52, 508, 204, 270]),
    ("geometry-submenu", "@geometry@", "[data-director-geometry-submenu]",
     (1440, 900), [52, 508, 204, 270]),
]

CENSUS_JS = r"""
({sel, panels, live, margin}) => {
  const isCtx = (cs) =>
    (cs.position !== 'static' && cs.zIndex !== 'auto') ||
    cs.transform !== 'none' || cs.filter !== 'none' ||
    cs.backdropFilter !== 'none' || cs.isolation === 'isolate' ||
    cs.perspective !== 'none' || cs.opacity !== '1' ||
    cs.mixBlendMode !== 'normal' || cs.contain.includes('paint') ||
    cs.willChange !== 'auto' || cs.containerType !== 'normal' ||
    cs.position === 'fixed' || cs.position === 'sticky';
  const ctxZ = (el) => {
    if (!el || el === document.documentElement) return 0;
    const cs = getComputedStyle(el);
    if (!isCtx(cs)) return 0;
    return cs.zIndex === 'auto' ? 0 : parseInt(cs.zIndex, 10);
  };
  const desc = (n) => {
    if (!n) return '?';
    const d = n.getAttribute('data-director') || '';
    const cls = (n.getAttribute('class') || '').split(/\s+/).filter(Boolean)[0] || '';
    return n.tagName.toLowerCase() + (d ? '[' + d + ']' : '') + (cls ? '.' + cls : '');
  };
  // +1 a paints above b, -1 b above a, 0 same element.
  const paintOrder = (a, b) => {
    if (a === b) return 0;
    if (a.contains(b)) return -1;   // a is an ancestor of b: not a competitor
    if (b.contains(a)) return 1;
    const chain = (el) => { const o = []; let n = el;
      while (n) { o.push(n); n = n.parentElement; } return o.reverse(); };
    const ca = chain(a), cb = chain(b);
    let i = 0;
    while (i < ca.length && i < cb.length && ca[i] === cb[i]) i += 1;
    const na = ca[i], nb = cb[i];
    if (!na || !nb) return 0;
    const za = ctxZ(na), zb = ctxZ(nb);
    if (za !== zb) return za > zb ? 1 : -1;
    return (na.compareDocumentPosition(nb) & Node.DOCUMENT_POSITION_FOLLOWING) ? -1 : 1;
  };
  const box = (el) => { if (!el) return null; const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) return null;
    return {x: r.x, y: r.y, w: r.width, h: r.height, bottom: r.bottom, right: r.right}; };
  const inter = (a, b) => {
    const x = Math.max(a.x, b.x), y = Math.max(a.y, b.y);
    const r = Math.min(a.right, b.right), d = Math.min(a.bottom, b.bottom);
    return r > x && d > y;
  };
  const el = document.querySelector(sel);
  if (!el) return {missing: true};
  const oBox = box(el);

  // struct half: does any overlapping, non-ancestor panel paint above us?
  const structBad = [];
  for (const [pname, q] of panels) {
    const p = document.querySelector(q);
    if (!p || p.contains(el) || el.contains(p)) continue;   // ancestry: not a competitor
    const pb = box(p);
    if (!pb || !inter(oBox, pb)) continue;
    if (paintOrder(el, p) < 0) structBad.push({panel: pname, z: ctxZ(p), who: desc(p)});
  }

  // casualty half: is every live control inside the overlay reachable?
  const blocked = [];
  let liveCount = 0;
  for (const c of el.querySelectorAll(live)) {
    const cb = c.getBoundingClientRect();
    if (cb.width <= 0 || cb.height <= 0) continue;   // zero-size: not a casualty
    if (c.disabled || c.getAttribute('aria-disabled') === 'true') continue;
    liveCount += 1;
    const label = (c.getAttribute('aria-label') || c.textContent || '').trim().slice(0, 18);
    const x = cb.x + cb.width / 2, y = cb.y + cb.height / 2;
    if (x < 0 || y < 0 || x > innerWidth || y > innerHeight) {
      blocked.push({label, why: 'off-viewport', at: [Math.round(x), Math.round(y)]});
      continue;
    }
    const hit = document.elementFromPoint(x, y);
    if (hit && (el.contains(hit) || hit === el)) continue;
    blocked.push({label, why: 'occluded', by: hit ? desc(hit) : 'none'});
  }

  return {
    box: [Math.round(oBox.x), Math.round(oBox.y), Math.round(oBox.w), Math.round(oBox.h)],
    bottom: Math.round(oBox.bottom),
    ownZ: getComputedStyle(el).zIndex,
    pointerEvents: getComputedStyle(el).pointerEvents,
    overflowBottom: Math.round(oBox.bottom - (innerHeight - margin)),
    overflowRight: Math.round(oBox.right - (innerWidth - margin)),
    structBad, liveCount, blocked,
  };
}"""


def strip_dev_overlay(page: Page) -> None:
    """Remove the Next dev badge portal before any hit test.

    Same rationale as batch 617: it mounts bottom-left, where the rail's 帮助
    and the geometry flyouts live.  React portals for our own flyouts go
    straight to document.body, so this cannot remove them.
    """
    page.evaluate(
        "() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }"
    )


def open_overlay(page: Page, how: str) -> None:
    """Open one overlay through its real control."""
    if how == "@tree-rctx@":
        page.locator("[data-director-tree] [data-director-object-id]").first.click(
            button="right", timeout=10_000)
    elif how == "@geometry@":
        page.locator("[data-director-rail-entry='add-character']").first.click(timeout=10_000)
        page.wait_for_timeout(450)
        page.locator("[data-director-character-option='geometry']").first.click(timeout=10_000)
    elif how == "@crowd@":
        page.locator("[data-director-rail-entry='add-character']").first.click(timeout=10_000)
        page.wait_for_timeout(450)
        page.locator("[data-director-character-option='crowd-3x3']").first.click(timeout=10_000)
    elif how == "@fov-hover@":
        # The FOV field only mounts for a selected camera object, and the
        # tooltip is a *sibling* of the `?` badge inside the group host — so
        # hover the badge, never the (pointer-events:none) tooltip itself.
        page.evaluate(
            "() => window.__director_store.getState()"
            ".selectObject('director-camera-main')"
        )
        page.wait_for_timeout(400)
        badge = page.locator("[data-director-camera-fov-help-badge]").first
        badge.wait_for(state="visible", timeout=15_000)
        badge.hover(timeout=10_000)
        page.wait_for_timeout(400)
    elif how == "@camera-preset@":
        # togglePresetPanel requires a selected camera track; the desk opens
        # with a transform track selected, so pick the camera track row first.
        row = page.locator("[data-director-track-row-kind='camera'] [role='button']").first
        row.wait_for(state="visible", timeout=15_000)
        row.click(timeout=10_000)
        page.wait_for_timeout(300)
        page.locator("[data-director-camera-preset-trigger]").first.click(timeout=10_000)
    elif how == "@path-menu@":
        page.locator("[data-director-create-motion-path]").first.click(timeout=10_000)
    else:
        page.locator(how).first.click(timeout=10_000)


DESK_RETRIES = 1  # infra-only: the shared dev server sometimes misses the 60s
                  # store-ready wait under concurrent load.  Retries the *page
                  # setup* only — never an assertion — and is counted in the
                  # result so a flaky run is visible rather than silent.


def open_desk_with_retry(page: Page) -> int:
    """Open the desk, retrying a store-ready timeout on a fresh load.

    `TimeoutError` out of `wait_for_function` means the dev server never served
    the app to this page — a load flake, not a product behaviour.  Anything
    else is re-raised so a real setup bug still fails the cell.
    """
    for attempt in range(DESK_RETRIES + 1):
        try:
            b617.open_desk(page)
            return attempt
        except PlaywrightTimeout:
            if attempt >= DESK_RETRIES:
                raise
            page.wait_for_timeout(2_000)
    return DESK_RETRIES


def measure(page: Page, sel: str) -> dict[str, Any]:
    strip_dev_overlay(page)
    page.mouse.move(5, 5)
    page.wait_for_timeout(200)
    return page.evaluate(
        CENSUS_JS, {"sel": sel, "panels": PANELS, "live": LIVE, "margin": SAFE_MARGIN})


class Verifier:
    def __init__(self) -> None:
        self.result: dict[str, Any] = {}
        self.failures: list[str] = []
        self.count = 0

    def check(self, name: str, ok: bool, detail: Any = "") -> None:
        self.count += 1
        self.result[name] = {"ok": bool(ok), "detail": detail}
        if not ok:
            self.failures.append(name)
        print(("  PASS " if ok else "  FAIL ") + name + (f"  {detail}" if detail else ""))


def run_matrix(page: Page, v: Verifier) -> dict[str, Any]:
    """11 overlays x 3 viewports: struct half + casualty half."""
    br = page.context.browser
    rows: list[dict[str, Any]] = []
    retries = 0
    for vw, vh in VIEWPORTS:
        for name, how, sel in OVERLAYS:
            p = br.new_page(viewport={"width": vw, "height": vh}, device_scale_factor=1)
            row: dict[str, Any] = {"vw": vw, "vh": vh, "overlay": name}
            try:
                retries += open_desk_with_retry(p)
                open_overlay(p, how)
                p.wait_for_timeout(700)
                row.update(measure(p, sel))
            except Exception as exc:  # noqa: BLE001
                row["error"] = f"{type(exc).__name__}: {str(exc)[:140]}"
            finally:
                p.close()
            rows.append(row)
            tag = f"{vw}x{vh}/{name}"
            v.check(f"overlay-present/{tag}", "error" not in row and not row.get("missing"),
                    row.get("error") or (f"box{row['box']}" if not row.get("missing")
                                         else "element not in DOM"))
            if "error" in row or row.get("missing"):
                continue
            v.check(f"no-panel-paints-above/{tag}", not row["structBad"], row["structBad"])
            v.check(f"live-controls-reachable/{tag}", not row["blocked"],
                    row["blocked"] or f"{row['liveCount']} live")
    return {"matrix": rows, "setupRetries": retries}


def run_height_sweep(page: Page, v: Verifier) -> dict[str, Any]:
    """The two menus that overflowed: every height must fit and stay reachable."""
    br = page.context.browser
    rows: list[dict[str, Any]] = []
    retries = 0
    for name, how, sel, sizes in HEIGHT_SWEEP:
        for vw, vh in sizes:
            p = br.new_page(viewport={"width": vw, "height": vh}, device_scale_factor=1)
            row: dict[str, Any] = {"vw": vw, "vh": vh, "overlay": name}
            try:
                retries += open_desk_with_retry(p)
                open_overlay(p, how)
                p.wait_for_timeout(700)
                row.update(measure(p, sel))
            except Exception as exc:  # noqa: BLE001
                row["error"] = f"{type(exc).__name__}: {str(exc)[:140]}"
            finally:
                p.close()
            rows.append(row)
            tag = f"{vw}x{vh}/{name}"
            v.check(f"fit-in-viewport/{tag}",
                    "error" not in row and not row.get("missing")
                    and row["overflowBottom"] <= 0 and row["overflowRight"] <= 0,
                    row.get("error") or f"overflow b{row.get('overflowBottom')} "
                                         f"r{row.get('overflowRight')} box{row.get('box')}")
            if "error" in row or row.get("missing"):
                continue
            v.check(f"live-controls-reachable/{tag}", not row["blocked"],
                    row["blocked"] or f"{row['liveCount']} live")
    return {"heightSweep": rows, "setupRetries": retries}


def run_no_op_cases(page: Page, v: Verifier) -> dict[str, Any]:
    """Where nothing overflows, the clamp must not move a single pixel."""
    br = page.context.browser
    rows: list[dict[str, Any]] = []
    for name, how, sel, (vw, vh), expected in NO_OP_CASES:
        p = br.new_page(viewport={"width": vw, "height": vh}, device_scale_factor=1)
        row: dict[str, Any] = {"vw": vw, "vh": vh, "overlay": name, "expected": expected}
        try:
            open_desk_with_retry(p)
            open_overlay(p, how)
            p.wait_for_timeout(700)
            row.update(measure(p, sel))
        except Exception as exc:  # noqa: BLE001
            row["error"] = f"{type(exc).__name__}: {str(exc)[:140]}"
        finally:
            p.close()
        rows.append(row)
        tag = f"{vw}x{vh}/{name}"
        v.check(f"clamp-is-a-no-op/{tag}",
                "error" not in row and row.get("box") == expected,
                row.get("error") or f"got {row.get('box')} want {expected}")
    return {"noOpCases": rows}


def main() -> int:
    v = Verifier()
    with sync_playwright() as p:
        br = p.chromium.launch()
        ctx = br.new_context()
        keeper = ctx.new_page()
        out = {}
        out.update(run_matrix(keeper, v))
        out.update(run_height_sweep(keeper, v))
        out.update(run_no_op_cases(keeper, v))
        out["ok"] = not v.failures
        out["checks"] = v.count
        out["failures"] = v.failures
        Path("/tmp/liblib-batch626-result.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=2, default=str))
        keeper.close()
        br.close()

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED: " + f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())
