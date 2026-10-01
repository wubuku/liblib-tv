"""Jimeng clone batch 806 verifier — 节点连接手柄（+ 环钮）实名 / 几何 / 外观 / 出现时机。

Contract (SOURCE_FACT 2026-10-03 登录态实测，@1512×950 画布 / 100% zoom，
docs/research/jimeng-canvas-batch806-2026-10-03/handle2-source.json)：

  1. 实名  `Create connected node before {标题}` / `... after {标题}`
           —— 标题动态插值（实测 视频 1 / 音频 4 / 音频 5）
  2. 命中盒 <button> 36×36，rounded-lg 8px，无底色无边框
  3. 外观  盒内是**空心圆环**，外径 ≈24px，1px 描边，环内完全透明，
           中心一个 ≈8~10px 的 `+` 字形
  4. 位置  垂直居中；水平紧贴节点缘**外侧**，间隙 2~4px
  5. 时机  **仅选中时挂载**（未选中时 querySelectorAll 恒为 0，不是 CSS 隐藏）
  6. 范围  四类节点两侧都有（含带媒体的视频节点）

两个踩过的坑写进了断言写法：

  - **必须先做缩放归一化**。demo 默认视口 73%，不归一就量到 26×26 而不是
    36×36（26/36 = 0.7222），会得出「尺寸不对」的假结论。所以先从
    `.react-flow__viewport` 的 transform 矩阵取 zoom，长度全部除以它。
  - 间隙/居中用**相对断言**，不写死绝对坐标——绝对坐标会随 demo 初始
    视口和节点位置漂移，变成 brittle 的假失败。

并发提醒：+ 钮现在四类节点都有，所以断言「四类都在」而不是「只有视频节点有」。
"""

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")
CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}

KIND_CLASS = {
    "video": ".react-flow__node-video",
    "image": ".react-flow__node-image",
    "text": ".react-flow__node-text",
    "audio": ".react-flow__node-audio",
}

PROBE = """(sel) => {
  const vpEl = document.querySelector('.react-flow__viewport');
  let zoom = 1;
  try {
    const t = getComputedStyle(vpEl).transform;
    if (t && t !== 'none') zoom = new DOMMatrixReadOnly(t).a;
  } catch (e) { /* 拿不到就按 1 处理：断言会因尺寸不符而失败，而不是静默通过 */ }
  const n = document.querySelector(sel);
  if (!n) return {err: 'no node', zoom};
  const nr = n.getBoundingClientRect();
  const q = (w) => n.querySelector(`button[aria-label^="Create connected node ${w}"]`);
  const out = {zoom, node: {
    rect: [nr.x, nr.y, nr.width, nr.height],
    title: (n.textContent || '').trim().slice(0, 12),
  }};
  const side = (el) => {
    if (!el) return null;
    const b = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    const ring = el.firstElementChild;
    const rs = ring ? getComputedStyle(ring) : null;
    const rb = ring ? ring.getBoundingClientRect() : null;
    return {
      aria: el.getAttribute('aria-label'),
      tag: el.tagName.toLowerCase(),
      // 世界坐标（长度已除以 zoom；中心点保留屏幕坐标，断言时再比）
      size: [b.width / zoom, b.height / zoom],
      cx: b.x + b.width / 2, cy: b.y + b.height / 2,
      bg: s.backgroundColor,
      ring: rb ? {d: [rb.width / zoom, rb.height / zoom],
                  radius: parseFloat(rs.borderRadius) || 0,
                  bg: rs.backgroundColor} : null,
      testid: el.getAttribute('data-testid'),
    };
  };
  out.left = side(q('before'));
  out.right = side(q('after'));
  out.hotLeft = !!n.querySelector('.react-flow__handle-left');
  out.hotRight = !!n.querySelector('.react-flow__handle-right');
  return out;
}"""

# 未选中时 + 钮是否还在 DOM 里（源站：不在）
COUNT_BTN = """(sel) => {
  const n = document.querySelector(sel);
  if (!n) return -1;
  return n.querySelectorAll('button[aria-label^="Create connected node"]').length;
}"""


def main() -> int:
    failures: list[str] = []
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page(viewport=VIEWPORT, locale="zh-CN")
        try:
            pg.goto(CANVAS_URL, wait_until="domcontentloaded")
            pg.wait_for_timeout(2600)
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(400)

            video = KIND_CLASS["video"]

            # ── 1. 未选中：+ 钮不得挂载（源站实测恒为 0 个）──
            n_btn = pg.evaluate(COUNT_BTN, video)
            if n_btn != 0:
                failures.append(
                    f"unselected node still mounts {n_btn} + handle button(s) "
                    "(source: not in DOM at all until selected)"
                )

            # ── 2. 选中后：实名 / 两侧 / 几何 / 外观 ──
            pg.locator(video).first.click(position={"x": 400, "y": 160})
            pg.wait_for_timeout(600)

            d = pg.evaluate(PROBE, video)
            if d.get("err"):
                failures.append(d["err"])
            else:
                z = d["zoom"]
                if not (0.5 < z < 1.5):
                    failures.append(f"unexpected viewport zoom {z:.3f}")
                nr = d["node"]["rect"]
                node_left, node_right = nr[0], nr[0] + nr[2]
                node_cy = nr[1] + nr[3] / 2
                for side, want_word, edge, sign in (
                    ("left", "before", node_left, -1),
                    ("right", "after", node_right, +1),
                ):
                    s = d[side]
                    if not s:
                        failures.append(f"{side} + handle button missing on selected node")
                        continue
                    # 2a 实名（含动态标题）
                    if not s["aria"].startswith(f"Create connected node {want_word} "):
                        failures.append(
                            f"{side} aria = {s['aria']!r}, want prefix "
                            f"'Create connected node {want_word} '"
                        )
                    elif not s["aria"].split(" ", 3)[3].strip():
                        failures.append(f"{side} aria carries no node title: {s['aria']!r}")
                    # 2b 命中盒 36×36（世界坐标）
                    if round(s["size"][0]) != 36 or round(s["size"][1]) != 36:
                        failures.append(
                            f"{side} hit box {s['size'][0]:.1f}x{s['size'][1]:.1f}, want 36x36"
                        )
                    # 2c 自身无底色
                    if s["bg"] not in ("rgba(0, 0, 0, 0)", "transparent"):
                        failures.append(f"{side} button has a background: {s['bg']}")
                    # 2d 贴缘外侧，间隙 2~4px（世界坐标；源站实测 2/3/4）
                    gap = (sign * (s["cx"] - edge) - 18 * z) / z
                    if not (1.5 <= gap <= 4.5):
                        failures.append(
                            f"{side} gap to node edge = {gap:+.1f}px, want 2~4 (source 3)"
                        )
                    # 2e 垂直居中
                    if abs(s["cy"] - node_cy) > 1.0 * z:
                        failures.append(
                            f"{side} vertical center off by {(s['cy'] - node_cy) / z:+.1f}px"
                        )
                    # 2f 空心环 24px
                    if not s["ring"]:
                        failures.append(f"{side} has no ring child")
                    else:
                        if round(s["ring"]["d"][0]) != 24 or round(s["ring"]["d"][1]) != 24:
                            failures.append(
                                f"{side} ring {s['ring']['d'][0]:.1f}x{s['ring']['d'][1]:.1f}, want 24x24"
                            )
                        # rounded-full 的 computed 半径是个巨大的 px 数（≈3.35e7），
                        # 判「是不是圆」要看半径是否 ≥ 半个环宽
                        if s["ring"]["radius"] < s["ring"]["d"][0] / 2 - 0.5:
                            failures.append(
                                f"{side} ring radius {s['ring']['radius']:.0f}px is not a circle"
                            )
                        if s["ring"]["bg"] not in ("rgba(0, 0, 0, 0)", "transparent"):
                            failures.append(
                                f"{side} ring is filled ({s['ring']['bg']}); source ring is hollow"
                            )
                    if s["testid"] != f"jimeng-connect-{side}":
                        failures.append(f"{side} testid = {s['testid']!r}")

                if not d["hotLeft"] or not d["hotRight"]:
                    failures.append("60x120 invisible hot zones missing (batch 17 contract)")

                # 2g 标题插值：实名末尾要跟得上节点标题
                title = d["node"]["title"]
                for side in ("left", "right"):
                    s = d[side]
                    if s and title and title.split()[0] in s["aria"]:
                        continue
                    if s:
                        failures.append(
                            f"{side} aria {s['aria']!r} does not interpolate node title {title!r}"
                        )

            pg.screenshot(path=str(REFERENCE_DIR / "jimeng-clone-batch806-handles.png"))

            # ── 3. 其余三类节点也接上了（源站：四类都两侧有）──
            for kind, sel in KIND_CLASS.items():
                if kind == "video":
                    continue
                loc = pg.locator(sel)
                if loc.count() == 0:
                    continue
                loc.first.click(position={"x": 40, "y": 20})
                pg.wait_for_timeout(450)
                got = pg.evaluate(COUNT_BTN, sel)
                if got != 2:
                    failures.append(f"{kind} node exposes {got} + handle button(s), want 2")
                pg.keyboard.press("Escape")
                pg.wait_for_timeout(250)
        finally:
            b.close()

    if failures:
        print("FAIL batch806")
        for f in failures:
            print("  -", f)
        return 1
    print("PASS batch806 — 连接手柄：实名/36×36 命中盒/空心环 24px/贴缘 3px/仅选中挂载/四类节点")
    return 0


if __name__ == "__main__":
    sys.exit(main())
