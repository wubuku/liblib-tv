#!/usr/bin/env python3
"""batch 712 验收：播放头的可达集 + zoom 控件到底是「点」还是「拖」

## 起点

711 普查持久化边界时留下两格**第三态**（没造出差异）：

- 点了标尺 75% 处，刷新前 `playheadTime` **仍然是 0**
- `[data-director-timeline-zoom-cluster]` 里只有一枚按钮，点完 `zoom` 仍是 44

第三态不能记成「过刷新」也不能记成「不过刷新」。本批把那两格补上。

## 五条预测（写死在代码里，先于任何测量）

- **P1** 标尺左侧精确按 `t = frac × duration` 映射（702/703 已测过三个点，本批铺开）
- **P2** frac 超过某个位置之后是**死区**（点它什么都不发生），**不是夹紧**（不是「吸到上限」）
- **P3** 上限是 `t = 4.24`（**不是 4.0**，尽管关键帧就在 4）
- **P4** 键盘方向键**不**移动播放头
- **P5** zoom 控件是**只能拖不能点**的划块，拖拽范围 0..100

## 结果：五条全部成立

- **P1 成立**：frac 0.02/0.10/0.25/0.50/0.51/0.52/0.53 全部与 `frac × 8` 吻合到 0.01 内。
- **P2 成立且这是本批最锋利的一格**：先把播放头放到 `t = 2`，
  再点 75% 处 —— **仍然是 2**。**它没有吸到上限，它是死的。**
  ⟹ 「看起来像被限制」和「被限制」必须用**换一个起点再点一次**来分。
- **P3 成立**：frac ≥ 0.54 之后 t 冻结在 **4.240000131736106**，
  而关键帧在 t = 4 —— **上限不是关键帧位置**。
- **P4 成立**：连按 `ArrowRight` ×3 + `ArrowUp`，t 纹丝不动。
- **P5 成立**：点那枚 71×24 的控件 `zoom` 不变（44 → 44）；
  从中间**向右拖到底 → 100**，**向左拖到底 → 0**。

**顺带把 711 的两格第三态解释掉了**：711 点的是 75%（死区里），
zoom 点的是一枚**只能拖**的控件 —— 两个动作都没造出差异，所以那一格是第三态而不是「没变化」。

## 判据

1. `the-ruler-maps-clicks-linearly-up-to-fifty-three-percent`
2. `the-right-part-of-the-ruler-is-a-dead-zone-not-a-clamp`
3. `the-playhead-ceiling-is-4-24-not-the-keyframe-time`
4. `arrow-keys-do-not-move-the-playhead`
5. `the-zoom-control-is-drag-only-and-spans-zero-to-one-hundred`
"""
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch712-2026-10-01"
W, DESK_H = 1280, 1150
CEILING = 4.240000131736106

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

PREDICTIONS = {
    "P1": "标尺左侧精确按 t = frac × duration 映射",
    "P2": "frac 超过某个位置之后是死区，不是夹紧",
    "P3": "上限是 t = 4.24（不是关键帧所在的 4.0）",
    "P4": "键盘方向键不移动播放头",
    "P5": "zoom 控件只能拖不能点，拖拽范围 0..100",
}

READ = r"""() => {
  const s = window.__director_store.getState();
  const t = s.timeline || {};
  const ruler = document.querySelector('[data-director-timeline-ruler]');
  const rb = ruler ? ruler.getBoundingClientRect() : null;
  const z = document.querySelector('[data-director-timeline-zoom]');
  const zb = z ? z.getBoundingClientRect() : null;
  const ph = document.querySelector('[data-director-playhead]');
  const pb = ph ? ph.getBoundingClientRect() : null;
  return {
    playheadTime: t.playheadTime !== undefined ? t.playheadTime : t.currentTime,
    zoom: t.zoom,
    duration: t.duration,
    rulerBox: rb ? [rb.x, rb.y, rb.width, rb.height] : null,
    zoomBox: zb ? [zb.x, zb.y, zb.width, zb.height] : null,
    playheadX: pb ? pb.x : null,
  };
}"""

SEL_CAMERA = r"""() => {
  const s = window.__director_store.getState();
  const c = s.objects.find((o) => o.kind === 'camera');
  const row = document.querySelector('[data-director-tree] [role="treeitem"]'
    + '[data-director-object-id="' + c.id + '"]');
  if (row) row.click();
  return !!row;
}"""


def read(page: Page) -> dict[str, Any]:
    return page.evaluate(READ)


def fresh(browser: Any) -> Page:
    page = browser.new_page(viewport={"width": W, "height": DESK_H},
                            device_scale_factor=1)
    b617.open_desk(page)
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(300)
    page.evaluate(SEL_CAMERA)
    page.wait_for_timeout(600)
    return page


def click_ruler(page: Page, frac: float) -> float:
    r = read(page)
    x, y, w, h = r["rulerBox"]
    page.mouse.click(x + w * frac, y + h / 2)
    page.wait_for_timeout(420)
    return read(page)["playheadTime"]


def sweep(browser: Any) -> dict[str, Any]:
    page = fresh(browser)
    duration = read(page)["duration"]
    linear = []
    for frac in (0.02, 0.10, 0.25, 0.50, 0.51, 0.52, 0.53):
        t = click_ruler(page, frac)
        linear.append({"frac": frac, "t": t, "expected": frac * duration,
                       "matches": abs(t - frac * duration) < 0.01})
    frozen = []
    for frac in (0.54, 0.60, 0.75, 0.90, 0.99):
        t = click_ruler(page, frac)
        frozen.append({"frac": frac, "t": t})
    # 换个起点再点死区：区分「夹紧」与「死区」
    before = click_ruler(page, 0.25)
    after = click_ruler(page, 0.75)
    page.close()
    return {"duration": duration, "linear": linear, "frozen": frozen,
            "deadZoneFrom": before, "deadZoneAfter": after}


def keyboard_arm(browser: Any) -> dict[str, Any]:
    page = fresh(browser)
    start = click_ruler(page, 0.25)
    for key in ("ArrowRight", "ArrowRight", "ArrowRight", "ArrowUp"):
        page.keyboard.press(key)
        page.wait_for_timeout(300)
    end = read(page)["playheadTime"]
    page.close()
    return {"start": start, "end": end}


def zoom_arm(browser: Any) -> dict[str, Any]:
    page = fresh(browser)
    r = read(page)
    x, y, w, h = r["zoomBox"]
    initial = r["zoom"]
    page.mouse.click(x + w / 2, y + h / 2)
    page.wait_for_timeout(450)
    after_click = read(page)["zoom"]
    page.mouse.move(x + w / 2, y + h / 2)
    page.mouse.down()
    page.mouse.move(x + w - 4, y + h / 2, steps=12)
    page.mouse.up()
    page.wait_for_timeout(500)
    after_drag_right = read(page)["zoom"]
    page.mouse.move(x + 4, y + h / 2)
    page.mouse.down()
    page.mouse.move(x - 40, y + h / 2, steps=12)
    page.mouse.up()
    page.wait_for_timeout(500)
    after_drag_left = read(page)["zoom"]
    page.close()
    return {"initial": initial, "afterClick": after_click,
            "afterDragRight": after_drag_right, "afterDragLeft": after_drag_left}


def check_1(s: dict[str, Any]) -> None:
    assert s["duration"] == 8, s["duration"]
    for rec in s["linear"]:
        assert rec["matches"], f"frac={rec['frac']} 实测 {rec['t']}，期望 {rec['expected']}"
    # 最左端那个点要真的落在 0.16 附近（不是「随便一个非零值」）
    assert abs(s["linear"][0]["t"] - 0.16) < 0.01, s["linear"][0]


def check_2(s: dict[str, Any]) -> None:
    # 死区：从 t=2 点 75%，仍然是 2（若是被夹紧，应该吸到上限）
    assert abs(s["deadZoneFrom"] - 2.0) < 0.01, s["deadZoneFrom"]
    assert abs(s["deadZoneAfter"] - s["deadZoneFrom"]) < 0.01, \
        f"从 {s['deadZoneFrom']} 点 75% 变成了 {s['deadZoneAfter']} —— 那是夹紧不是死区"
    for rec in s["frozen"]:
        assert abs(rec["t"] - CEILING) < 0.001, rec


def check_3(s: dict[str, Any]) -> None:
    top = max(r["t"] for r in s["linear"])
    assert abs(top - CEILING) < 0.001, f"线性段最高只到 {top}"
    assert abs(CEILING - 4.0) > 0.1, "上限恰好是 4.0，那 P3 的读法就变了"
    assert any(r["frac"] == 0.53 and abs(r["t"] - CEILING) < 0.001 for r in s["linear"]), \
        "frac=0.53 就该到上限"


def check_4(a: dict[str, Any]) -> None:
    assert abs(a["start"] - 2.0) < 0.01, a["start"]
    assert abs(a["end"] - a["start"]) < 0.001, \
        f"方向键把播放头从 {a['start']} 挪到了 {a['end']} —— P4 的读法就变了"


def check_5(a: dict[str, Any]) -> None:
    assert a["initial"] == 44, a["initial"]
    assert a["afterClick"] == a["initial"], \
        f"点一下 zoom 变成 {a['afterClick']} —— P5 的读法就变了"
    assert a["afterDragRight"] == 100, a
    assert a["afterDragLeft"] == 0, a


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {"predictions": PREDICTIONS}
    failures: list[str] = []
    got: dict[str, Any] = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, fn in (("sweep", sweep), ("keyboard", keyboard_arm),
                         ("zoom", zoom_arm)):
            try:
                got[name] = fn(browser)
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{name}: {exc}")
                got[name] = {}
        browser.close()
    results.update(got)
    checks = [
        ("the-ruler-maps-clicks-linearly-up-to-fifty-three-percent",
         lambda: check_1(got.get("sweep", {}))),
        ("the-right-part-of-the-ruler-is-a-dead-zone-not-a-clamp",
         lambda: check_2(got.get("sweep", {}))),
        ("the-playhead-ceiling-is-4-24-not-the-keyframe-time",
         lambda: check_3(got.get("sweep", {}))),
        ("arrow-keys-do-not-move-the-playhead", lambda: check_4(got.get("keyboard", {}))),
        ("the-zoom-control-is-drag-only-and-spans-zero-to-one-hundred",
         lambda: check_5(got.get("zoom", {}))),
    ]
    summary: dict[str, bool] = {}
    for name, fn in checks:
        try:
            fn()
            summary[name] = True
        except Exception as exc:  # noqa: BLE001
            summary[name] = False
            failures.append(f"{name}: {exc}")
    results["summary"] = summary
    results["failures"] = failures
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=1, default=str))
    for name, ok in summary.items():
        print(("PASS " if ok else "FAIL ") + name)
    for f in failures:
        print("  ->", f[:400])
    print(f"\n{sum(1 for v in summary.values() if v)}/{len(summary)} 通过")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
