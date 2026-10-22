#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 839 前置检查的**自检**：证明它**能发现**陈旧 chunk，而不是永远说「一致」。

★ 为什么必须做这个：前置检查是**否定性判据**（「没发现不一致」）⟹
  ⟹ 一个永远返回「一致」的检查器，会把**所有**陈旧读数都放过去 ⟹
  ⟹ 而且它**不报错、只给绿灯** ⟹ 这是最贵的一种失败。

⟹ 三条臂：
  A. **值不同** ⟹ 伪造一份「服务端 chunk」把 `.cs-asset-strip` 的 left 改成 100px
     ⟹ ⟹ 必须报出 `.cs-asset-strip` 的 left 差异。
  B. **选择器缺失** ⟹ 伪造一份**空**的服务端 chunk ⟹ ⟹ 必须报「服务端 chunk 里找不到」。
  C. **真·端到端** ⟹ 真的把磁盘改掉 ⟹ 在 watcher 追平之前**必须**至少抓到一次差异
     ⟹ （证明「抓取 → 解析 → 比对」这条链在**真**链路上也有效，而不只是 monkeypatch 有效）。

★ C 那条是**尽力而为**：watcher 可能在我第一次调用前就追平了 ⟹
  ⟹ 那时如实记成「这次没抓到瞬时差异」⟹ **不**当成通过 ⟹ 但 A/B 两条仍然成立。
"""
import importlib.util
import pathlib
import re
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[4]
GATE = ROOT / "scripts/verify-liblib-batch839.py"

spec = importlib.util.spec_from_file_location("g839", GATE)
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


def main() -> int:
    results = []

    # ── A. 值不同 ────────────────────────────────────────────────────
    fake = g.served_css()
    m = re.search(r"\.cs-asset-strip\s*\{([^}]*)\}", fake)
    # ★ 替换**全部**出现处（第一版只替换了第一个 ⟹ 而第一个属于 `.cs-voice-row`
    #   ⟹ 断言却查 `.cs-asset-strip` ⟹ 报「没报出差异」⟹ 是**测试自己写错了位置**）。
    stale = fake.replace("left: 139px;", "left: 100px;")
    if not m or stale == fake:
        print("★ 伪造样本没造出来（服务端 chunk 里没有 left: 139px）⟹ 中止")
        return 2
    orig = g.served_css
    g.served_css = lambda: stale
    try:
        drift = g.css_drift()
    finally:
        g.served_css = orig
    results.append({
        "臂": "A 值不同",
        "注入": "伪造服务端 chunk：.cs-asset-strip 的 left 139px→100px",
        "报出的差异": drift.get(".cs-asset-strip"),
        "是否报出left差异": (
            ".cs-asset-strip" in drift
            and "left" in (drift.get(".cs-asset-strip") or {})),
    })

    # ── B. 选择器缺失 ────────────────────────────────────────────────
    g.served_css = lambda: ""
    try:
        drift_b = g.css_drift()
    finally:
        g.served_css = orig
    results.append({
        "臂": "B 选择器缺失",
        "注入": "伪造一份**空**的服务端 chunk",
        "报出的选择器": sorted(drift_b.keys()),
        "是否四个都报缺失": all(
            "找不到" in json_str(drift_b.get(s, {})) for s in g.CRITICAL_SELECTORS),
    })

    # ── C. 真·端到端（改磁盘 ⟹ 抓瞬时差异） ──────────────────────────
    css = g.CSS_FILE
    original = css.read_text(encoding="utf-8")
    caught = None
    try:
        mutated = original.replace("  left: 139px;\n  top: 114px;",
                                   "  left: 137px;\n  top: 114px;", 1)
        if mutated == original:
            print("★ 注入锚点没找到 ⟹ 中止")
            return 2
        css.write_text(mutated, encoding="utf-8")
        t0 = time.time()
        while time.time() - t0 < 20:
            d = g.css_drift()
            if d:
                caught = d
                break
            time.sleep(0.2)
    finally:
        css.write_text(original)
    results.append({
        "臂": "C 真·端到端",
        "注入": "真的把磁盘 .cs-asset-strip 的 left 改成 137px",
        "是否抓到差异": caught is not None,
        "抓到的差异": caught,
        "★说明": "watcher 可能在我第一次调用前就追平 ⟹ 那时如实记 False，"
                 "**不**当成通过；A／B 两条仍然成立",
    })

    ok_ab = (results[0]["是否报出left差异"]
             and results[1]["是否四个都报缺失"])
    print("\n".join(__import__("json").dumps(r, ensure_ascii=False, indent=1)
                    for r in results))
    print(f"\n自检：{'通过' if ok_ab else '未通过'}（A／B 两条为硬要求）")
    out = ROOT / "docs/research/liblib-canvas-batch839-2026-10-01/raw/preflight-selftest-839.json"
    out.write_text(__import__("json").dumps(
        {"结果": results, "A／B是否通过": ok_ab}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print("写入", out)
    return 0 if ok_ab else 1


def json_str(obj) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False)


if __name__ == "__main__":
    sys.exit(main())
