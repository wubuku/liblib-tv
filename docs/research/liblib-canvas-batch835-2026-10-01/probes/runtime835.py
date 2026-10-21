#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 835：在**当前** clone 上量 748 的 C3／C4 侧运行时事实，并核对关系式不变量。

★ 与 `static835.py` 配对：那一支做**静态侧**归因（每个多出来的 `data-*` 归属到哪个批次），
  这一支做**运行时侧**（首屏多少种、走完 7 枚 rail 累计多少种、每枚带出多少种）。

★ 口径**必须与 748 逐字一致**（否则数字不可比）：
  - 静态：`\\b(data-[a-z0-9-]+)` 逐行扫 → 每文件去重 → 并集；另算 `dataset.` 派生名；
  - 运行时：`DUMP` 把**整页**所有 `data-*` 属性名收成集合（`data-director-*` 与非导演台的都算）；
  - rail：逐枚点开 → 与**累计已见集合**做差 ⟹ 「新增」＝这一枚**首次**带来的那些。

★ 这支只**读**，不改源码、不写仓库产物（结果落在 /tmp）。
"""
import json
import pathlib
import re
import sys

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
DESK = ROOT / "src/components/director"
BASE = "http://localhost:4317"
ATTR = re.compile(r"\b(data-[a-z0-9-]+)")
DATASET = re.compile(r"\.dataset\.([A-Za-z0-9_]+)\s*=")

DUMP = """() => { const out = {};
  for (const el of document.querySelectorAll('*'))
    for (const a of el.attributes)
      if (a.name.startsWith('data-')) out[a.name] = (out[a.name]||0)+1;
  return out; }"""
RAILS = """() => [...document.querySelectorAll('[data-director-rail-entry]')].map((e,i) => ({
    i, key: e.getAttribute('data-director-rail-entry'),
    title: e.getAttribute('title'), w: Math.round(e.getBoundingClientRect().width),
    h: Math.round(e.getBoundingClientRect().height) }))"""


def static():
    per, union, ds = {}, set(), set()
    for f in sorted(DESK.glob("*.tsx")):
        names = set()
        for line in f.read_text(encoding="utf-8").split("\n"):
            names.update(ATTR.findall(line))
            for m in DATASET.finditer(line):
                kebab = re.sub(r"([A-Z])", lambda x: "-" + x.group(1).lower(), m.group(1))
                ds.add("data-" + kebab)
        per[f.name] = sorted(names)
        union |= names
    return per, union, ds


def main():
    per, union, ds = static()
    eff = union | ds

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1280, "height": 1150})
        page = ctx.new_page()
        page.goto(BASE + "/?batch835=1", wait_until="domcontentloaded")
        page.wait_for_timeout(2500)
        page.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
        node = page.evaluate("""() => {
            const n = [...document.querySelectorAll('*')].find(e => e.getAttribute('data-node-type')==='script-execution'
                || (e.textContent||'').includes('分镜脚本'));
            if (n) { n.click(); return true; } return false; }""")
        page.wait_for_timeout(1200)
        page.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
        page.evaluate("""() => { const b=document.querySelector('[data-open-director]'); if(b) b.click(); }""")
        page.wait_for_timeout(1500)
        page.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
        opened = page.evaluate("() => Boolean(document.querySelector('[data-director-workspace]'))")
        print("导演台已打开：", opened, "（入口节点命中：", node, "）")

        first = set(page.evaluate(DUMP))
        rails = page.evaluate(RAILS)
        print("首屏 %d 种；rail %d 枚" % (len(first), len(rails)))
        seen = set(first)
        per_rail = []
        for r in rails:
            page.evaluate("(i) => { const e = document.querySelectorAll('[data-director-rail-entry]')[i]; if (e) e.click(); }", r["i"])
            page.wait_for_timeout(900)
            now = set(page.evaluate(DUMP))
            gained = sorted(now - seen)
            seen |= now
            per_rail.append({"i": r["i"], "key": r["key"], "title": r["title"],
                             "gainedCount": len(gained), "gained": gained})
            print("  [%d] %-16s %-12s 新增 %3d 种，累计 %d" % (r["i"], r["key"], r["title"], len(gained), len(seen)))
            page.evaluate("(i) => { const e = document.querySelectorAll('[data-director-rail-entry]')[i]; if (e) e.click(); }", r["i"])
            page.wait_for_timeout(500)
        page.close()
        ctx.close()
        browser.close()

    residue = sorted(eff - seen)
    extra = sorted(seen - eff)
    extra_canvas = [n for n in extra if not n.startswith("data-director-")]
    extra_dataset = [n for n in extra if n in ds]
    extra_unprefixed = [n for n in extra if n.startswith("data-director-") and n not in ds]

    zero = [r for r in per_rail if r["gainedCount"] == 0]
    biggest = max(per_rail, key=lambda r: r["gainedCount"])

    # ★ 关系式不变量（与绝对数字无关）
    seen_owners = {}
    for k, v in per.items():
        for n in v:
            seen_owners.setdefault(n, []).append(k)
    shared = {n: f for n, f in seen_owners.items() if len(f) > 1}
    inv = {
        "求和 - 并集 == 跨文件重复数": sum(len(v) for v in per.values()) - len(union) ==
                                        sum(len(f) - 1 for f in shared.values()),
        "有效并集 == 字面量并集 + 派生名增量": len(eff) == len(union) + len(ds - union),
        "首屏 ⊆ 累计": first.issubset(seen),
        "累计 = 首屏 + 各枚新增之和": len(seen) == len(first) + sum(r["gainedCount"] for r in per_rail),
        "累计 = 导演台属性 + 非并集": len(seen) == len(seen & eff) + len(extra),
        "有效并集 = 见过 + 残留": len(eff) == len(seen & eff) + len(residue),
        "非并集 = 画布残留 + dataset 盲区 + 无前缀导演台": len(extra) == len(extra_canvas) + len(extra_dataset) + len(extra_unprefixed),
        "dataset 盲区已不在并集外": extra_dataset == [],
        "每枚 rail 的新增都是首次出现": all(
            not (set(r["gained"]) & (seen - set(r["gained"]))) for r in per_rail),
    }

    out = {
        "静态": {"fileCount": len(per), "sumByFile": sum(len(v) for v in per.values()),
                 "unionCount": len(union), "effectiveUnionCount": len(eff),
                 "perFileCount": {k: len(v) for k, v in per.items()},
                 "sharedNames": sorted(shared), "datasetDerived": sorted(ds)},
        "运行时": {"firstPaintCount": len(first), "afterRailWalkCount": len(seen),
                   "directorKindsSeen": len(seen & eff), "extraOnPage": len(extra),
                   "extraCanvasLeftover": extra_canvas, "extraDatasetBlindSpot": extra_dataset,
                   "extraUnprefixedDirector": extra_unprefixed,
                   "residueAfterWalk": len(residue)},
        "rail": {"perRail": per_rail, "zeroGain": [r["key"] for r in zero],
                 "zeroGainCount": len(zero),
                 "biggest": {"key": biggest["key"], "gainedCount": biggest["gainedCount"]},
                 "gains": {r["key"]: r["gainedCount"] for r in per_rail}},
        "关系式不变量": inv,
    }
    print("\n=== 关系式不变量 ===")
    for k, v in inv.items():
        print("  %s %s" % ("✔" if v else "✘", k))
    print("\n零新增：%s；最多的一枚：%s（%d 种）" % (
        [r["key"] for r in zero], biggest["key"], biggest["gainedCount"]))
    print("累计 %d = 导演台 %d + 非并集 %d；残留 %d" % (
        len(seen), len(seen & eff), len(extra), len(residue)))

    p = pathlib.Path("/tmp/b835-runtime.json")
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", p)
    return 0 if all(inv.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
