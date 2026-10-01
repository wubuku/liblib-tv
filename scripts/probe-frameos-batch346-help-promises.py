#!/usr/bin/env python3
"""Batch 346 探针：帮助面板承诺的交互，是否**条条兑现**。

背景（Batch 344 的延伸 —— 承诺必须兑现）:
Batch 344 抓到菜单标注的 ⌫ 快捷键根本不工作。帮助面板
(`FrameosHelpPanel`，按 ? 打开) 是一张**19 条的承诺清单**，而它列出的每一条
都应当真的能用。本探针逐条实测其中**带键盘/鼠标动作**的那些。

帮助面板原文（`SECTIONS`）:
  创作:  双击空白→添加节点 / ⌘C / ⌘X / ⌘V / ⌘D / ⌥拖动节点 / ⌘S
  缩放:  双击节点→聚焦填满视口 / ⌘+ / ⌘− / ⌘0 / 双指捏合 / ⌘滚轮
  移动:  空格拖动 / 左键拖动 / 双指平移 / 中键右键拖动 / 滚轮平移
  其他:  ⌘Z / ⌘⇧Z / ⌫ / ⌘F / M / ? / Esc

代码审计已发现两条**页面上没有任何 handler**:
  - `onDoubleClick` 只出现在分组标签(改名) 上, 画布本身没有双击 handler
  - `panActivationKeyCode` 未设置(靠 React Flow 默认值, 需实测确认)
另存疑: `panOnScroll` 与 `zoomOnScroll` **同时为 true**, 而帮助面板声称
  「鼠标滚轮 ⌘滚轮=缩放」+「滚轮=平移」。

用法: ~/.venvs/liblib-harness/bin/python scripts/probe-frameos-batch346-help-promises.py
"""

import json
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from frameos_verify_common import attach_errors, goto_clean_canvas  # noqa: E402

BASE_URL = "http://localhost:4317"

STATE_JS = """
() => {
  const s = window.__frameos_store.getState();
  const t = document.querySelector('.react-flow__viewport');
  return {
    nodeCount: s.nodes.length,
    nodeIds: s.nodes.map((n) => n.id),
    transform: t ? t.style.transform : null,
  };
}
"""

# 找一个空白点: 反复试画布中心附近, 直到该点不落在任何节点上
EMPTY_POINT_JS = """
() => {
  const nodes = Array.from(document.querySelectorAll('.react-flow__node'));
  const rects = nodes.map((n) => n.getBoundingClientRect());
  for (let y = 120; y < window.innerHeight - 120; y += 40) {
    for (let x = 120; x < window.innerWidth - 120; x += 40) {
      const hit = rects.some(
        (r) => x >= r.left && x <= r.right && y >= r.top && y <= r.bottom
      );
      if (!hit) return { x, y, tried: nodes.length };
    }
  }
  return null;
}
"""

# 视口平移量与缩放量 —— 用来区分「平移」与「缩放」
VP_JS = """
() => {
  const t = document.querySelector('.react-flow__viewport');
  if (!t) return null;
  const m = t.style.transform.match(
    /translate\\(([-\\d.]+)px,\\s*([-\\d.]+)px\\) scale\\(([\\d.]+)\\)/
  );
  if (!m) return { raw: t.style.transform };
  return { tx: parseFloat(m[1]), ty: parseFloat(m[2]), scale: parseFloat(m[3]) };
}
"""


def _vp(v):
    return v if isinstance(v, dict) and "tx" in v and "scale" in v else None


def moved(v0, v1):
    """视口是否被**平移**（忽略缩放带来的附带位移）。"""
    a, b = _vp(v0), _vp(v1)
    if a is None or b is None:
        return None
    return abs(b["tx"] - a["tx"]) > 1 or abs(b["ty"] - a["ty"]) > 1


def zoomed(v0, v1):
    """视口是否被**缩放**（这才是「聚焦填满视口」的可观测证据）。"""
    a, b = _vp(v0), _vp(v1)
    if a is None or b is None:
        return None
    return abs(b["scale"] - a["scale"]) > 0.01


def main() -> int:
    out: dict = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 950})
        errors = attach_errors(page)
        goto_clean_canvas(page, BASE_URL)

        empty = page.evaluate(EMPTY_POINT_JS)
        out["empty_point"] = empty
        if not empty:
            print("!! 找不到空白点")
            return 1

        # ── A 承诺「双击空白处添加节点」──
        before = page.evaluate(STATE_JS)
        page.mouse.dblclick(empty["x"], empty["y"])
        page.wait_for_timeout(700)
        out["A_dblclick_empty"] = page.evaluate(STATE_JS)
        out["A_before"] = before

        # ── B 承诺「聚焦填满视口」: 只对**双击未被节点自己消费**的类型成立 ──
        # 文本节点双击=进入编辑(FrameosTextNode stopPropagation),
        # 视频节点双击=预览(FrameosVideoNode), 只有图片等会冒泡。
        # 先 ⌘0 重置视图, 否则部分节点在视口外, 逐类型验证会变成「跳过」。
        page.keyboard.press("Meta+0")
        page.wait_for_timeout(900)
        per_type = page.evaluate(
            """() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
                 const id = n.getAttribute('data-id');
                 const r = n.getBoundingClientRect();
                 return { id, cx: r.left + r.width / 2, cy: r.top + r.height / 2,
                          type: id.split('-')[0] };
               })"""
        )
        vp_start = page.evaluate(VP_JS)
        per_type_result = []
        for item in per_type:
            if item["cx"] < 2 or item["cx"] > 1598 or item["cy"] < 2 or item["cy"] > 948:
                per_type_result.append({**item, "offscreen": True})
                continue
            before_i = page.evaluate(VP_JS)
            page.mouse.dblclick(item["cx"], item["cy"])
            page.wait_for_timeout(700)
            after_i = page.evaluate(VP_JS)
            per_type_result.append({
                **item,
                "focused": (zoomed(before_i, after_i) is True)
                or (moved(before_i, after_i) is True),
            })
        out["B_per_type"] = per_type_result
        out["B_before"] = vp_start

        # ── B2 文本节点双击应进入编辑(而非聚焦) ──
        # 逐类型循环会移动视口, 所以这里**必须**先重置视图并**重新取坐标** ——
        # 沿用循环前的旧坐标会点到空气 (上一轮就因此误报 enters_edit=false)。
        page.keyboard.press("Meta+0")
        page.wait_for_timeout(900)
        text_node = page.evaluate(
            """() => {
              const n = document.querySelector('.react-flow__node[data-id^="text-"]');
              if (!n) return null;
              const r = n.getBoundingClientRect();
              return { cx: r.left + r.width / 2, cy: r.top + r.height / 2,
                       id: n.getAttribute('data-id') };
            }"""
        )
        if text_node:
            page.mouse.dblclick(text_node["cx"], text_node["cy"])
            page.wait_for_timeout(700)
            out["B2_text_dblclick"] = page.evaluate(
                """() => ({
                   textareas: document.querySelectorAll(
                     '.react-flow__node textarea').length,
                 })"""
            )
            out["B2_text_node"] = text_node

        # ── C 承诺「空格拖动」平移画布 ──
        vp0 = page.evaluate(VP_JS)
        page.keyboard.down("Space")
        page.mouse.move(empty["x"], empty["y"])
        page.mouse.down()
        for i in range(6):
            page.mouse.move(empty["x"] - (i + 1) * 15, empty["y"] - (i + 1) * 10)
            page.wait_for_timeout(16)
        page.mouse.up()
        page.keyboard.up("Space")
        page.wait_for_timeout(400)
        out["C_space_drag"] = {"before": vp0, "after": page.evaluate(VP_JS)}

        # ── D 滚轮: 帮助面板称「⌘滚轮=缩放」「滚轮=平移」──
        page.mouse.move(empty["x"], empty["y"])
        vp1 = page.evaluate(VP_JS)
        page.mouse.wheel(0, 300)          # 裸滚轮
        page.wait_for_timeout(500)
        vp2 = page.evaluate(VP_JS)
        page.keyboard.down("Meta")
        page.mouse.wheel(0, 300)          # ⌘ + 滚轮
        page.keyboard.up("Meta")
        page.wait_for_timeout(500)
        vp3 = page.evaluate(VP_JS)
        out["D_wheel"] = {"start": vp1, "after_plain": vp2, "after_meta": vp3}

        # ── E 对照: 承诺「⌥ 拖动节点」复制 ──
        # 同理: 前面的步骤改过视口, 必须重置并重取坐标。
        page.keyboard.press("Meta+0")
        page.wait_for_timeout(900)
        page.evaluate(
            "() => { window.__frameos_store.getState().selectNode(null); return true; }"
        )
        n2_box = page.evaluate(
            """() => {
              const n = document.querySelector('.react-flow__node');
              const r = n.getBoundingClientRect();
              return { x: r.left, y: r.top, w: r.width, h: r.height,
                       id: n.getAttribute('data-id') };
            }"""
        )
        b2 = n2_box
        before_e = page.evaluate(STATE_JS)
        page.keyboard.down("Alt")
        page.mouse.move(b2["x"] + b2["w"] / 2, b2["y"] + b2["h"] / 2)
        page.mouse.down()
        for i in range(5):
            page.mouse.move(
                b2["x"] + b2["w"] / 2 + (i + 1) * 12,
                b2["y"] + b2["h"] / 2 + (i + 1) * 9,
            )
            page.wait_for_timeout(20)
        page.mouse.up()
        page.keyboard.up("Alt")
        page.wait_for_timeout(600)
        out["E_alt_drag"] = {"before": before_e, "after": page.evaluate(STATE_JS)}

        out["consoleErrors"] = errors
        browser.close()

    a_before, a_after = out["A_before"], out["A_dblclick_empty"]
    c = out["C_space_drag"]
    d = out["D_wheel"]

    print("=== batch346 帮助面板承诺对账 ===")
    print(f"空白点: {out['empty_point']}")
    print(f"[A 双击空白→添加节点]  nodes {a_before['nodeCount']} → {a_after['nodeCount']}")
    print("[B 逐节点类型双击→是否聚焦]")
    for t in out["B_per_type"]:
        if t.get("offscreen"):
            print(f"   {t['id']:<10} (在视口外, 跳过)")
        else:
            print(f"   {t['id']:<10} focused={t['focused']}")
    print(f"[B2 文本节点双击]     {out.get('B2_text_dblclick')}")
    print(f"[C 空格拖动]         视口 {c['before']} → {c['after']}")
    print(f"[D 裸滚轮]           视口 {d['start']} → {d['after_plain']}")
    print(f"[D ⌘+滚轮]           视口 {d['after_plain']} → {d['after_meta']}")
    print(f"[E ⌥拖动→复制]       nodes {out['E_alt_drag']['before']['nodeCount']} "
          f"→ {out['E_alt_drag']['after']['nodeCount']}")
    if out["consoleErrors"]:
        print(f"console errors: {out['consoleErrors']}")

    print("\n=== 判定 ===")
    print(json.dumps({
        "A_dblclick_empty_adds_node": a_after["nodeCount"] > a_before["nodeCount"],
        "B_image_node_focuses": any(
            t.get("focused") for t in out["B_per_type"] if t["type"] == "image"
        ),
        "B_text_node_does_NOT_focus": all(
            not t.get("focused") for t in out["B_per_type"] if t["type"] == "text"
        ),
        "B_text_node_enters_edit": (
            (out.get("B2_text_dblclick") or {}).get("textareas", 0) > 0
        ),
        "C_space_drag_pans": moved(c["before"], c["after"]),
        "D_plain_wheel_pans": moved(d["start"], d["after_plain"]),
        "D_plain_wheel_zooms": zoomed(d["start"], d["after_plain"]),
        "D_meta_wheel_zooms": zoomed(d["after_plain"], d["after_meta"]),
        "D_meta_wheel_pans": moved(d["after_plain"], d["after_meta"]),
        "E_alt_drag_duplicates": (
            out["E_alt_drag"]["after"]["nodeCount"] > out["E_alt_drag"]["before"]["nodeCount"]
        ),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
