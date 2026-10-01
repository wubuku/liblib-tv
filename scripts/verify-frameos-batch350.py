#!/usr/bin/env python3

"""Verify Batch 350: 裁剪表单会静默丢弃用户输入 —— 填了宽高, 确认后节点毫无变化。

缺陷（克隆侧，用户可见）:
`FrameosNodeFloatingToolbar` 的裁剪态（Batch 279 源站采样的 UI 外观）里:
  - `裁剪宽度` / `裁剪高度` 是 `<input defaultValue={480}>` 的**非受控**输入,
    全仓没有任何代码读过它们 —— 那个 480 与节点实际尺寸也毫无关系;
  - 「✓ 确认裁剪」只做 `window.alert("已确认裁剪 (mock)")` + 退出裁剪态;
  - 于是**用户认真填的数字被整个丢弃，节点一点没变**，而 UI 弹了确认。

比普通 mock 更坏的地方: 这是一条**接受输入并静默丢弃**的表单。

修复（不新增 store API，不发明裁剪语义）:
  - 宽高改**受控**, 进入裁剪态时用**节点当前尺寸**初始化（而不是写死的 480）;
  - 裁剪框（参考线 + 8 手柄）跟随输入尺寸, 锚在节点左上角;
  - 「确认裁剪」复用节点拖拽手柄用的**同一对** action:
    `beginResize`（入历史快照） + `resizeNode`（落尺寸）→ 自动可撤销;
  - 屏幕坐标 ↔ 流坐标显式换算（nodeRect 是屏幕坐标, 宽高是流坐标 ——
    与 Batch 342 同源的坐标系陷阱）;
  - 解析不出数字就不落, 也不谎报成功。

断言:
1. 自检: 能进裁剪态且裁剪框在位（防假绿前提）;
2. 宽高输入初值 = **节点当前尺寸**（不是与实际无关的 480）;
3. 改宽高 → **裁剪框尺寸跟着变**（输入真的在驱动画面）;
4. 「确认裁剪」→ 节点 style 宽高**精确等于**输入值;
5. 裁剪框屏幕尺寸 = 输入值 × zoom（坐标系换算正确）;
6. 确认后**退出裁剪态**;
7. 裁剪**可撤销**（复用 beginResize 的历史快照, 与全 app 语义一致）;
8. 撤销后节点尺寸**精确回到**裁剪前;
9. 最小值夹取: 输入 50 → 落到与拖拽手柄相同的下限 200×120;
10. 解析失败（空字符串）→ **不谎报成功**, 节点尺寸不变;
11. 诊断零错误。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT / "docs" / "research" / "liblib-frameos-batch350-2026-10-01" / "runtime-audit.json"
)
sys.path.insert(0, str(ROOT / "scripts"))
from frameos_verify_common import attach_errors, goto_clean_canvas  # noqa: E402

# 节点 style 尺寸 + 屏幕 rect + 裁剪框, 一次性读齐。
# **按 node id 读, 不按 selectedNodeId 读** —— `undo()` 里明确写了
# `selectedNodeId: null`（快照恢复丢掉选中, 是有意的显式设计）,
# 所以任何「撤销之后」的状态都必须用稳定 id 取, 否则会读到 None 而误判成
# 「撤销把节点删了」。踩过这个坑: 撤销明明精确还原了 300×169, 探针却报 (None,None)。
NODE_ID = "image-1"
STATE_JS = """
(id) => {
  const s = window.__frameos_store.getState();
  const n = s.nodes.find((x) => x.id === id);
  const el = n ? document.querySelector(`.react-flow__node[data-id="${id}"]`) : null;
  const r = el ? el.getBoundingClientRect() : null;
  const crop = document.querySelector('[data-frameos-crop-rect]');
  const cr = crop ? crop.getBoundingClientRect() : null;
  return {
    selectedId: s.selectedNodeId,
    nodePresent: !!n,
    styleW: n && n.style ? n.style.width : null,
    styleH: n && n.style ? n.style.height : null,
    screenW: r ? r.width : null,
    screenH: r ? r.height : null,
    croppingNodeId: s.croppingNodeId,
    pastLen: s.past.length,
    cropRect: cr ? { w: cr.width, h: cr.height } : null,
  };
}
"""


def read_state(page: Page) -> dict[str, Any]:
    return page.evaluate(STATE_JS, NODE_ID)


def enter_crop(page: Page) -> None:
    """选中一个有内容的图片节点 → 点「裁剪」进裁剪态。"""
    page.locator('.react-flow__node[data-id="image-1"]').click()
    page.wait_for_timeout(700)
    page.get_by_label("裁剪", exact=True).first.click()
    page.wait_for_selector("[data-frameos-crop-rect]", timeout=8000)


def set_size(page: Page, w: str, h: str) -> None:
    page.get_by_label("裁剪宽度", exact=True).fill(w)
    page.get_by_label("裁剪高度", exact=True).fill(h)
    page.wait_for_timeout(350)


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool, detail: str = "") -> None:
        assert ok, f"batch350 check failed: {name} {detail}".strip()
        result["checks"].append(name)

    errors = attach_errors(page)
    goto_clean_canvas(page, BASE_URL)

    enter_crop(page)
    st0 = read_state(page)
    result["on_enter"] = st0
    # 防假绿: 裁剪态没进 / 框没画出来, 后面全是空谈
    check("setup:in-crop-mode", st0["croppingNodeId"] == "image-1",
          f"croppingNodeId={st0['croppingNodeId']}")
    check("setup:crop-rect-present", st0["cropRect"] is not None, "裁剪框没渲染")
    check("setup:node-has-size", bool(st0["styleW"] and st0["styleH"]),
          f"styleW={st0['styleW']} styleH={st0['styleH']}")

    w_in = page.get_by_label("裁剪宽度", exact=True).input_value()
    h_in = page.get_by_label("裁剪高度", exact=True).input_value()
    result["initial_inputs"] = {"w": w_in, "h": h_in}
    # 初值必须是节点当前尺寸, 不是与实际无关的 480
    check("input:initialized-from-node", int(w_in) == int(st0["styleW"])
          and int(h_in) == int(st0["styleH"]),
          f"input=({w_in},{h_in}) style=({st0['styleW']},{st0['styleH']})")

    # ── 输入驱动裁剪框 ──
    zoom = st0["screenW"] / st0["styleW"] if st0["styleW"] else 1
    target_w, target_h = 420, 260
    set_size(page, str(target_w), str(target_h))
    st1 = read_state(page)
    result["after_typing"] = st1
    check("input:drives-crop-rect",
          st1["cropRect"] is not None
          and abs(st1["cropRect"]["w"] - target_w * zoom) <= 2
          and abs(st1["cropRect"]["h"] - target_h * zoom) <= 2,
          f"rect={st1['cropRect']} expect=({target_w * zoom:.1f},{target_h * zoom:.1f}) zoom={zoom:.4f}")
    check("input:not-applied-yet", st1["styleW"] == st0["styleW"],
          f"还没点确认, 尺寸不该变: {st1['styleW']} vs {st0['styleW']}")

    # ── 确认裁剪 → 落尺寸 ──
    page.get_by_label("确认裁剪", exact=True).click()
    page.wait_for_timeout(600)
    st2 = read_state(page)
    result["after_confirm"] = st2
    check("confirm:applies-size",
          st2["styleW"] == target_w and st2["styleH"] == target_h,
          f"style=({st2['styleW']},{st2['styleH']}) expect=({target_w},{target_h})")
    check("confirm:exits-crop-mode", st2["croppingNodeId"] is None,
          f"croppingNodeId={st2['croppingNodeId']}")

    # ── 可撤销 ──
    check("undo:history-pushed", st2["pastLen"] > st0["pastLen"],
          f"past {st0['pastLen']} -> {st2['pastLen']}")
    page.keyboard.press("Meta+z")
    page.wait_for_timeout(700)
    st3 = read_state(page)
    result["after_undo"] = st3
    check("undo:restores-size",
          st3["styleW"] == st0["styleW"] and st3["styleH"] == st0["styleH"],
          f"style=({st3['styleW']},{st3['styleH']}) expect=({st0['styleW']},{st0['styleH']})")
    # 撤销是快照恢复, 不该把节点弄丢(与「还原到同样尺寸」是两件事)
    check("undo:node-still-present", st3["nodePresent"] is True, "撤销后节点不见了")

    # ── 最小值夹取(与拖拽手柄同一对下限 200×120) ──
    enter_crop(page)
    set_size(page, "50", "30")
    page.get_by_label("确认裁剪", exact=True).click()
    page.wait_for_timeout(600)
    st4 = read_state(page)
    result["clamped"] = st4
    check("clamp:min-size", st4["styleW"] == 200 and st4["styleH"] == 120,
          f"style=({st4['styleW']},{st4['styleH']}) expect=(200,120)")

    # ── 解析失败 → 不谎报成功 ──
    enter_crop(page)
    st5 = read_state(page)
    set_size(page, "", "")
    page.get_by_label("确认裁剪", exact=True).click()
    page.wait_for_timeout(600)
    st6 = read_state(page)
    result["invalid_input"] = {"before": st5, "after": st6}
    check("invalid:no-false-success",
          st6["styleW"] == st5["styleW"] and st6["styleH"] == st5["styleH"],
          f"解析失败却改了尺寸: ({st5['styleW']},{st5['styleH']}) -> ({st6['styleW']},{st6['styleH']})")

    check("diagnostics:zero", not errors, f"errors={errors[:3]}")
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 350,
        "defect": "裁剪宽高是非受控输入且从无代码读取；「确认裁剪」只 alert 就退出，"
                  "用户填的数字被静默丢弃、节点毫无变化",
        "fix": "受控输入(初值=节点当前尺寸) + 裁剪框跟随 + 复用 beginResize/resizeNode "
               "落尺寸(自动可撤销) + 屏幕↔流坐标显式换算",
    }
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            audit["desktop"] = run_desktop(page)
        finally:
            browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2))
    print(
        f"Batch 350 verification passed: {len(audit['desktop']['checks'])} checks, "
        f"{audit['desktop']['diagnostics']['console']} diagnostics. "
        "The crop form now really applies the entered W×H to the node (it previously "
        "silently discarded the input), the crop rectangle tracks the inputs in screen "
        "space, the change is undoable, and unparseable input changes nothing."
    )


if __name__ == "__main__":
    main()
