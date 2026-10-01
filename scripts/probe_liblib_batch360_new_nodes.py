#!/usr/bin/env python3
"""liblib「默认画布里不存在的节点类型」+ 浮层 普查探针 (Batch 360)

358/359 覆盖: 画布外框 16 态 + fixture 里 10 个节点的编辑面 + 3 个浮层。
**没覆盖**的是: 通过「添加节点」面板能新建、但 fixture 里没有的节点类型 ——
音频 / 智能剪辑 / 逐帧拉片。它们的编辑面板一次都没进过。

跳过「导演台」(script-execution): 它打开的是 DirectorDesk, 那是另一条线,
且有并行 session 正在改(src/components/director/* 有未提交 WIP) ——
现在去普查会把人家的在途改动混进我的结果。**跨线不碰。**

判据与 batch359 完全一致(同一套扫描器与「例外须自证惰性」规则), 只换覆盖面。

用法: python scripts/probe_liblib_batch360_new-nodes.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
OUT = ROOT / "docs" / "research" / "liblib-batch360-2026-10-01" / "new-nodes-census.json"

import sys  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts"))
from probe_liblib_batch359_node_surfaces import (  # noqa: E402
    SCAN_JS,
    classify,
    close_all,
)

# (面板按钮文案, data-add-node-entry 的值 = AddNodePanel 里的 entry.type)
# ⚠️ 第一版把 CSS 类名当成了 entry 的值, 三个类型全部「面板里没有该类型」被跳过。
# 探针如实报了跳过而不是假装测过 —— 这正是它该有的行为。
NEW_NODE_TYPES = [
    ("音频", "audio"),
    ("智能剪辑", "video-clip"),
    ("逐帧拉片", "shot-breakdown"),
]


def create_node(page: Page, label: str, entry_type: str) -> str | None:
    """通过「添加节点」面板新建一个节点, 返回其 data-id。"""
    before = set(page.evaluate(
        """() => Array.from(document.querySelectorAll('.react-flow__node'))
             .map(n => n.getAttribute('data-id')).filter(Boolean)"""
    ))
    panel_btn = page.get_by_role("button", name="添加节点", exact=True)
    panel_btn.click(force=True)
    page.wait_for_timeout(500)
    entry = page.locator(f"[data-add-node-entry='{entry_type}']")
    if entry.count() == 0:
        # 面板里没有这个类型, 记下来而不是假装测过
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        return None
    entry.first.click(force=True)
    page.wait_for_timeout(1400)
    after = page.evaluate(
        """() => Array.from(document.querySelectorAll('.react-flow__node'))
             .map(n => n.getAttribute('data-id')).filter(Boolean)"""
    )
    new = [n for n in after if n not in before]
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)
    return new[0] if new else None


def run(page: Page) -> dict[str, Any]:
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_selector(".react-flow__node", timeout=30000)
    page.wait_for_timeout(600)

    states: dict[str, Any] = {"__default__": classify(page.evaluate(SCAN_JS))}
    created: dict[str, Any] = {}

    for label, entry_type in NEW_NODE_TYPES:
        close_all(page)
        nid = create_node(page, label, entry_type)
        created[label] = nid
        if nid is None:
            states[f"new:{label}"] = {"__skipped__": "面板里没有该类型, 未测"}
            continue
        # 选中它, 让编辑面板浮出来
        page.locator(f'.react-flow__node[data-id="{nid}"]').first.evaluate("(el) => el.click()")
        page.wait_for_timeout(900)
        st = classify(page.evaluate(SCAN_JS))
        st["_nodeId"] = nid
        states[f"new:{label}"] = st

    states["_created"] = created
    return states


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            states = run(page)
        finally:
            browser.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(states, ensure_ascii=False, indent=2))

    tot_s = tot_d = skipped = 0
    for name, st in states.items():
        if name.startswith("_"):
            continue
        if "__skipped__" in st:
            skipped += 1
            print(f"=== {name}: 跳过 —— {st['__skipped__']}")
            continue
        s, d = st["silentDiscard"], st["deadControls"]
        tot_s += len(s)
        tot_d += len(d)
        if not s and not d:
            print(f"=== {name}: inputs={st['inputs']} controls={st['controls']} — 无问题")
            continue
        print(f"\n=== {name}: inputs={st['inputs']} controls={st['controls']}")
        for i in s:
            print(f"   静默丢弃 <{i['tag']} type={i['type']!r}> ph={i['ph']!r} aria={i['aria']!r}")
        for c in d:
            print(f"   点了没反应 <{c['tag']}> aria={c['aria']!r} "
                  f"text={c['text']!r} data={c['data']}")
    print(f"\n合计: 静默丢弃 {tot_s} / 死控件 {tot_d} / 跳过 {skipped}  ->  {OUT}")


if __name__ == "__main__":
    main()
