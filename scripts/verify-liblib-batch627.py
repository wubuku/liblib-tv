#!/usr/bin/env python3
"""batch 627 验收：普查不再丢弃「视口外控件」，并对导演台自身控件立下几何边界合同。

## 为什么要做这一批

626 在 rail 与时间轴的浮层上抓到两个真缺陷，形态是「末尾活控件挂在视口外」。
回头查成因，发现**普查按构造就看不见这类控件** —— 617 的共享 `AUDIT_JS` 里有
一行：

    if (cx < 0 || cy < 0 || cx > innerWidth || cy > innerHeight) continue;

中心点落在视口外的控件被**静默丢弃**：不进 `items`、不记进任何桶。所以它们不是
「被判失败」，而是「从未被枚举」。这有两层后果，第二层更隐蔽：

1. 626 的两个缺陷能一路躲过 619–625；
2. 窄屏下大部分工具条内容本就该在窗口之外（618/621 的 776px 内容），于是普查的
   **分母在窄屏会自己缩水** —— 一个「控件数变少」的读数看起来像好事。

改法：把 `continue` 换成「照常分类并额外标 `offViewport`」，剩下的判断完全交给
已有的 `isClipped`：

- 落在某个裁剪祖先之外 → `clipped`，滚得到，**记不失败**（621 的窄屏工具条）
- 不在任何裁剪祖先之外 → 真的够不着，落进 `covered`，与其他伤亡同等看待

## 三条合同

1. **没有任何控件是「视口外且够不着」的** —— 扫遍 623 立的 86 个宽度。
2. **新分支真的跑过**（非空转）—— 每个宽度上视口外控件数都 > 0。这条最关键：
   一份「零缺陷」若来自一条静默的 `continue`，和一个真的干净桌面长得一模一样。
3. **旧代码确实是瞎的**（差分断言）—— 同一页上并排跑「旧的 continue 版」与
   「新的分类版」，断言 `新版总数 − 旧版总数 == 新版视口外控件数`。差值恒等于
   分类数，就证明新代码没有顺手多收别的控件，也没有漏收。

## 顺带记下 898/899 的断点崖

这批的读数把 623 立的断点又印证了一遍：视口外控件数在 898 是 71、到 899 骤降到
15，`total` 同时从 123 升到 130 —— 窄屏把更多控件塞进横向滚动容器，桌面反过来
放得下更多。**沿用不修**（见 621/623 的约定），只记录。

## 不声称

- 不声称源站的任何行为。这批改的是**普查的量法**，一个字符都没碰界面。
- 不声称窄屏工具条的 776px 内容「放得下」—— 它们仍然需要横向滚动才见尾部，
  这里只主张「滚得到」，这正是 `clipped` 的原义。
"""
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def _load(name: str, path: Path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


b617 = _load("b617", ROOT / "scripts/verify-liblib-batch617.py")
b623 = _load("b623", ROOT / "scripts/verify-liblib-batch623.py")

WIDTHS = list(b623.WIDTHS)
CROSSCHECK = list(b623.CROSSCHECK)
DENSE, COARSE = b623.DENSE, b623.COARSE

# The pre-627 shape of the census: a bare `continue` that dropped every control
# whose centre was outside the viewport, and no offViewport flag at all.  Kept
# here so the verifier can measure the blindness instead of asserting it.
_LEGACY_DROP = ("    const offViewport = cx < 0 || cy < 0 || cx > innerWidth "
                "|| cy > innerHeight;")
LEGACY_AUDIT_JS = b617.AUDIT_JS
assert _LEGACY_DROP in LEGACY_AUDIT_JS, "AUDIT_JS no longer has the shape 627 expects"
LEGACY_AUDIT_JS = LEGACY_AUDIT_JS.replace(
    _LEGACY_DROP,
    "    if (cx < 0 || cy < 0 || cx > innerWidth || cy > innerHeight) continue;")
LEGACY_AUDIT_JS = LEGACY_AUDIT_JS.replace(
    "    const hit = offViewport ? null : document.elementFromPoint(cx, cy);",
    "    const hit = document.elementFromPoint(cx, cy);")
# the legacy shape never had the flag on the record, so it cannot name it
LEGACY_AUDIT_JS = LEGACY_AUDIT_JS.replace(
    "      box: b, z: s.zIndex, own, clipped, offViewport,",
    "      box: b, z: s.zIndex, own, clipped,")
assert "offViewport," not in LEGACY_AUDIT_JS.split("items.push")[1].split("panel:")[0]


def prep(page) -> None:
    page.mouse.move(5, 5)
    page.wait_for_timeout(160)
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal'))"
                  " el.remove(); }")


def measure(page) -> dict[str, Any]:
    r = page.evaluate(b617.AUDIT_JS, list(b617.TRANSIENT_OVERLAYS))
    legacy = page.evaluate(LEGACY_AUDIT_JS, list(b617.TRANSIENT_OVERLAYS))
    cov = [b for b in r["covered"] if b["label"] not in b617.KNOWN_BLOCKED]
    return {
        "total": r["total"],
        "offViewport": len(r["offViewportItems"]),
        "unreachable": [(b["label"], b["box"], b["data"])
                        for b in r["offViewportUnreachable"]],
        "scrollable": len(r["offViewportScrollable"]),
        "covered": [(b["label"], b["hitLabel"]) for b in cov],
        "legacyTotal": legacy["total"],
        "legacyCovered": len([b for b in legacy["covered"]
                              if b["label"] not in b617.KNOWN_BLOCKED]),
    }


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


def main() -> int:
    v = Verifier()
    sweep: dict[str, Any] = {}
    cross: dict[str, Any] = {}
    with sync_playwright() as p:
        br = p.chromium.launch()
        page = br.new_page(viewport={"width": 1920, "height": 900},
                           device_scale_factor=1)
        b617.open_desk(page)
        for w in WIDTHS:
            page.set_viewport_size({"width": w, "height": 900})
            page.wait_for_timeout(200)
            prep(page)
            sweep[w] = measure(page)
        page.close()

        for w in CROSSCHECK:
            fresh = br.new_page(viewport={"width": w, "height": 900},
                                device_scale_factor=1)
            b617.open_desk(fresh)
            prep(fresh)
            cross[w] = measure(fresh)
            fresh.close()
        br.close()

    out = {
        "batch": 627,
        "title": "the census classifies off-viewport controls instead of dropping "
                 "them, and holds the desk's own controls to the same geometric "
                 "boundary batch 626 held the overlays to",
        "date": "2026-10-01",
        "widths": WIDTHS,
        "sweep": {str(k): val for k, val in sweep.items()},
        "freshLoadCrosscheck": {str(k): val for k, val in cross.items()},
    }

    v.check(f"the-sweep-covers-{len(WIDTHS)}-widths", len(sweep) == len(WIDTHS),
            detail={"dense": len(DENSE), "coarse": len(COARSE)})

    bad = {w: r["unreachable"] for w, r in sweep.items() if r["unreachable"]}
    v.check("no-width-has-an-off-viewport-unreachable-control", not bad,
            detail={str(w): r[:3] for w, r in list(bad.items())[:6]})

    # non-vacuity: the new branch must fire everywhere, or "zero" would mean
    # nothing.  A silent `continue` looks exactly like a clean desk.
    vacuous = [w for w, r in sweep.items() if r["offViewport"] == 0]
    v.check("every-width-actually-exercised-the-off-viewport-branch", not vacuous,
            detail=vacuous[:8])

    # the differential: the legacy shape dropped exactly the controls the new
    # shape now classifies, and nothing else.
    drift = {w: (r["total"] - r["legacyTotal"], r["offViewport"])
             for w, r in sweep.items()
             if r["total"] - r["legacyTotal"] != r["offViewport"]}
    v.check("the-new-classification-added-exactly-the-off-viewport-controls",
            not drift, detail={str(w): d for w, d in list(drift.items())[:6]})
    blind = [w for w, r in sweep.items() if r["legacyTotal"] >= r["total"]]
    v.check("the-legacy-continue-was-blind-at-every-width", not blind,
            detail=blind[:8])

    # the change must not have disturbed the stacking half
    covbad = {w: r["covered"] for w, r in sweep.items() if r["covered"]}
    v.check("no-width-has-a-covered-control", not covbad,
            detail={str(w): r[:3] for w, r in list(covbad.items())[:6]})

    mism = [w for w in CROSSCHECK
            if (sweep[w]["total"], sweep[w]["offViewport"])
            != (cross[w]["total"], cross[w]["offViewport"])]
    v.check(f"the-{len(CROSSCHECK)}-fresh-loads-agree-with-the-resized-page",
            not mism, detail=mism)

    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    audit = ROOT / "docs/research/liblib-canvas-batch627-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED: " + f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())
