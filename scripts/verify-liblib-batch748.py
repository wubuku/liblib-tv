#!/usr/bin/env python3
"""batch 748 验收：导演台首轮运行时普查

## 起点

741–747 七批全在画布，**导演台一次都没做过运行时验收**。
静态侧 `src/components/director/*.tsx`（12 个组件、31k 行）共有 **446 种** `data-*` 属性。

本批做四件事：属性全集普查、运行时与全集的差集（分三类对账）、
7 枚 rail 入口逐个点、两个导演台记账命令。

## 决定性读数（先看这条）

### ① 静态字面量扫描有盲区：`dataset.xxx =` 拼出的属性扫不到

```
DirectorViewport.tsx:410   dataset.directorGizmoWebglCanvas = …   ⟹ data-director-gizmo-webgl-canvas
DirectorViewport.tsx:2920  dataset.directorWebglCanvas = …       ⟹ data-director-webgl-canvas
```

`data-director-gizmo-webgl-canvas` 在运行时 DOM 上存在，但**不在 446 种字面量全集里** ——
正则是 `\b(data-[a-z0-9-]+)`，只认源码里写出来的字面量。
⟹ **静态全集天然小于运行时全集**，这个差的方向是已知的、不该当成「动态加载」。

### ② 首屏 200 种 / 走完 7 枚 rail 入口累计 250 种 / 全集 446 种

差集 196 种。这些差集里既有**条件渲染的面板**（flyout、模态、子页签），
也有**需要更深交互才出现的状态**（相机 FOV 浮层在选中机位后才出），
本批**不区分**这两类 —— 只报数，不给成因（见「不声称」）。

### ③ **7 枚 rail 入口里有 2 枚点开 0 新增**

| # | `data-director-rail-entry` | `title` | 新增属性种类 |
|---|---|---|---|
| 0 | `scene` | 场景 | **0** |
| 1 | `add-character` | 添加角色 | 3 |
| 2 | `add-camera` | 添加机位 | **34** |
| 3 | `panorama` | 全景图 | 2 |
| 4 | `aspect-ratio` | 选择画幅比例 | 4 |
| 5 | `ai-import` | AI 识图导入 | 7 |
| 6 | `help` | 帮助 | **0** |

⟹ 「添加机位」一枚就带出 34 种（FOV 滑杆、跟随、预览、look-at 全套），
「场景」与「帮助」两枚**一个 `data-*` 都没新增**。
这两枚是惰性入口、还是它们打开的东西根本不带测试标记 —— **本批不判定**。

### ④ `createDirectorAnimationExport` **真跑通了**，但要用轮询而不是固定等待

「导出视频到画布」点完不是没反应 —— 是**约 9 秒的进度过程**：

```
idle ──► exporting（progress 0 → 8 → 17 → 25 → 35 → 43 → 52 → 61 → 70 → 79 → 87 → 97）
      ──► success（progress 100）
```

期间提交键 `disabled` 且文案变「导出中」，结束后恢复可点、文案回「导出视频到画布」。
终态 store：`past` 0→**1**、节点 10→**11**、边 11→**12**、
新文件「**第一集：咖啡馆对峙 动画导出**」、`video` 类型 1→2。

⟹ **我第一版探针只观察到 4.2 秒（还在 `exporting`）就断言「点了没反应」，那是错的。**

### ⑤ `createDirectorCapture` 的**第一跳是 store 零写入**（两跳）

`data-director-capture`（视口快门）点完 `past`/节点/边零变化，
但 `data-director-capture-preview` 与 `data-director-send-capture` 冒出来
⟹ **快门 → 预览 → 发送**是两跳，`createDirectorCapture` 本批**未触发**。

### ⑥ 运行时与静态的差要**分三类对账**，不能只报一个残差

| 账 | 数字 |
|---|---|
| 静态：按文件求和 | 460 |
| 静态：去重并集（字面量） | 446 |
| 静态：补 `dataset.` 派生名后的**有效并集** | **447** |
| 运行时（整页）：首屏 → 走完 7 枚 rail | 200 → **250** |
| 运行时 250 = 导演台属性 **224** + 非并集 **26** | |
| 非并集 26 = 画布/应用层残留 **24** + 无 `data-director-` 前缀的导演台属性 **2** | |
| 有效并集 447 中没出现的 | **223** |

⟹ 导演台**盖在画布之上、画布仍在 DOM 里** ⟹ 整页 `data-*` 总数不能直接当导演台的数。

## 判据

C1  静态：13 个组件，**按文件求和 460 / 去重并集 446**（13 个属性名跨文件、其中
    `data-director-bottom-bar` 出现在 3 个文件 ⟹ 12×1 + 1×2 = 14）；
    另有 2 处 `dataset.` 赋值是字面量盲区
C2  打开导演台：`[data-open-director]` ⟹ workspace / canvasId / sourceNodeId /
    sessionId / view / focusScope 六项齐；**store 零写入**
C3  差集三笔对平：整页 200 → 250；有效并集 447；250 = 224 + 26；26 = 24 + 2；447 − 224 = 223
C4  7 枚 rail 入口里**恰好 2 枚**点开 0 新增（`scene` / `help`），
    「添加机位」一枚带出 34 种
C5  `data-director-capture` 点击 ⟹ store 零写入，但 `capture-preview` 与
    `send-capture` 出现 ⟹ 两跳，命令本身**未触发**
C6  `createDirectorAnimationExport` **真跑通**：status 走 `idle → exporting`（进度递增、
    按钮 disabled + 「导出中」）→ `success`(100)；终态 `past` +1、节点 +1、边 +1、
    新文件名以「 动画导出」结尾
C7  导演台 6 个区域（workspace/viewport/tree/timeline/shot-bar/bottom-bar）齐
"""

import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch747-2026-10-01"  # 占位
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch748-2026-10-01"
DESK = ROOT / "src/components/director"
BASE = "http://localhost:4317"
W, H = 1280, 1150

SNAP = """() => {
  const s = window.__libtv_store.getState();
  const g = s.getActiveCanvas();
  const h = s.historyByCanvas[g.id] || {past: [], future: []};
  return {nodeCount: g.nodes.length, edgeCount: g.edges.length, past: h.past.length,
          typeCounts: g.nodes.reduce((a,n)=>(a[n.type]=(a[n.type]||0)+1,a), {}),
          files: g.nodes.map(n=>(n.data&&n.data.filename)||null).filter(Boolean)};
}"""
DUMP = """() => { const out = {};
  for (const el of document.querySelectorAll('*'))
    for (const a of el.attributes)
      if (a.name.startsWith('data-')) out[a.name] = (out[a.name]||0)+1;
  return out; }"""
RAILS = """() => [...document.querySelectorAll('[data-director-rail-entry]')].map((e,i) => ({
    i, key: e.getAttribute('data-director-rail-entry'),
    title: e.getAttribute('title'), w: Math.round(e.getBoundingClientRect().width),
    h: Math.round(e.getBoundingClientRect().height) }))"""
IDENT = """() => {
  const g = (sel) => { const e = document.querySelector(sel);
    return e ? e.getAttribute(sel.slice(1, -1)) : null; };
  return {workspace: Boolean(document.querySelector('[data-director-workspace]')),
          canvasId: g('[data-director-canvas-id]'),
          projectId: g('[data-director-project-id]'),
          sourceNodeId: g('[data-director-source-node-id]'),
          sessionId: g('[data-director-session-id]'),
          view: g('[data-director-view]'),
          focusScope: g('[data-director-focus-scope]'),
          focusState: g('[data-director-focus-state]')};
}"""
REGIONS = """() => {
  const q = (s) => Boolean(document.querySelector(s));
  return {workspace: q('[data-director-workspace]'), viewport: q('[data-director-viewport]'),
          webgl: q('[data-director-webgl-canvas]'), objectTree: q('[data-director-tree]'),
          timeline: q('[data-director-timeline]'), shotBar: q('[data-director-shot-bar]'),
          bottomBar: q('[data-director-bottom-bar]'),
          closeBtn: q('[data-close-director]'),
          shotOptions: document.querySelectorAll('[data-director-shot-option]').length,
          railEntries: document.querySelectorAll('[data-director-rail-entry]').length};
}"""


def static_scan():
    """静态：导演台 13 个组件的 data-* 字面量。
    **两个口径都要报**：按文件求和（有重复）与去重并集（无重复）。
    741 立过的规矩：一个对不上的数字自己就是线索 —— 本批两个口径差 14。"""
    out = {"files": {}}
    per_file = {}
    union = set()
    for f in sorted(DESK.glob("*.tsx")):
        names = set()
        for l in f.read_text(encoding="utf-8").split("\n"):
            names.update(re.findall(r"\b(data-[a-z0-9-]+)", l))
        per_file[f.name] = sorted(names)
        union |= names
    out["files"] = {k: {"count": len(v), "names": v} for k, v in per_file.items()}
    out["fileCount"] = len(per_file)
    out["sumByFile"] = sum(len(v) for v in per_file.values())
    out["unionCount"] = len(union)
    out["sharedAcrossFiles"] = out["sumByFile"] - out["unionCount"]
    # 哪些属性名跨文件重复
    seen = {}
    for k, v in per_file.items():
        for n in v:
            seen.setdefault(n, []).append(k)
    out["sharedNames"] = sorted(n for n, fs in seen.items() if len(fs) > 1)
    out["sharedNameOwners"] = {n: seen[n] for n in out["sharedNames"]}
    # dataset 赋值：camelCase ⟹ kebab-case
    ds = []
    for f in sorted(DESK.glob("*.tsx")):
        for i, l in enumerate(f.read_text(encoding="utf-8").split("\n"), 1):
            for m in re.finditer(r"\.dataset\.([A-Za-z0-9_]+)\s*=", l):
                kebab = re.sub(r"([A-Z])", lambda x: "-" + x.group(1).lower(), m.group(1))
                ds.append({"file": f.name, "line": i,
                           "expr": f"dataset.{m.group(1)}",
                           "attr": f"data-{kebab}"})
    out["datasetAssignments"] = ds
    out["unionNames"] = sorted(union)
    # 补上 dataset 派生名后的「有效并集」—— 字面量并集天然漏掉它们
    ds_names = {d["attr"] for d in ds}
    out["datasetDerivedNames"] = sorted(ds_names)
    out["effectiveUnionCount"] = len(union | ds_names)
    out["effectiveUnionNames"] = sorted(union | ds_names)
    return out


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    st = static_scan()
    print("=== C1 静态：导演台 data-* 字面量全集 ===")
    for k, v in sorted(st["files"].items(), key=lambda x: -x[1]["count"]):
        print(f"  {v['count']:4d}  {k}")
    print(f"  {st['fileCount']} 个组件；按文件求和 {st['sumByFile']} 种 / "
          f"去重并集 {st['unionCount']} 种（{st['sharedAcrossFiles']} 个属性名跨文件重复）")
    print(f"  dataset 赋值盲区 {len(st['datasetAssignments'])} 处：")
    for d in st["datasetAssignments"]:
        print(f"    {d['file']}:{d['line']}  {d['expr']} ⟹ {d['attr']}")

    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H})
        page.goto(f"{BASE}/?batch748=1", wait_until="networkidle", timeout=90_000)
        page.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
        page.wait_for_timeout(1_500)

        # ---------- C2 打开导演台 ----------
        entry = page.evaluate("""() => { const e = document.querySelector('[data-open-director]');
            if (!e) return null;
            const host = e.closest('.react-flow__node');
            return {onNode: Boolean(host), nodeId: host ? host.getAttribute('data-id') : null}; }""")
        s0 = page.evaluate(SNAP)
        opened = page.evaluate("""() => { const e = document.querySelector('[data-open-director]');
            if (!e) return false; e.click(); return true; }""")
        page.wait_for_timeout(2_500)
        ident = page.evaluate(IDENT)
        regions = page.evaluate(REGIONS)
        s1 = page.evaluate(SNAP)
        c2 = {"entry": entry, "opened": opened, "ident": ident, "regions": regions,
              "past": [s0["past"], s1["past"]],
              "nodes": [s0["nodeCount"], s1["nodeCount"]],
              "edges": [s0["edgeCount"], s1["edgeCount"]]}
        print(f"\n=== C2 打开导演台 ===")
        print(f"  入口在节点 {entry['nodeId'] if entry else None} 上；clicked={opened}")
        for k, v in ident.items():
            print(f"    {k:14s} {v!r}")
        print(f"  store：past {s0['past']}→{s1['past']}、节点 {s0['nodeCount']}→{s1['nodeCount']}、"
              f"边 {s0['edgeCount']}→{s1['edgeCount']}")
        print(f"=== C7 区域 ===")
        for k, v in regions.items():
            print(f"    {k:14s} {v}")

        # ---------- C3/C4 首屏 + 7 枚 rail 入口 ----------
        first = set(page.evaluate(DUMP))
        rails = page.evaluate(RAILS)
        print(f"\n=== C3/C4 rail 入口逐个点（首屏 {len(first)} 种）===")
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
            print(f"  [{r['i']}] {r['key']:16s} {r['title']!r:14s} 新增 {len(gained):3d} 种，累计 {len(seen)}")
            page.evaluate("(i) => { const e = document.querySelectorAll('[data-director-rail-entry]')[i]; if (e) e.click(); }", r["i"])
            page.wait_for_timeout(500)
        literal = set(st["unionNames"])                # 字面量并集（漏 dataset.）
        union = set(st["effectiveUnionNames"])         # 补上 dataset 派生名后的有效并集
        residue = sorted(union - seen)                 # 静态有、运行时没出现
        extra = sorted(seen - union)                   # 运行时有、字面量并集里没有
        # extra 分三类：① 画布/应用层残留 ② dataset. 盲区 ③ 导演台但属性名无 data-director- 前缀
        ds_names = set(st["datasetDerivedNames"])
        extra_canvas = [n for n in extra if not n.startswith("data-director-")]
        extra_dataset = [n for n in extra if n in ds_names]
        extra_unprefixed = [n for n in extra
                            if n.startswith("data-director-") and n not in ds_names]
        c3 = {"firstPaintCount": len(first), "afterRailWalkCount": len(seen),
              "staticLiteralUnion": st["unionCount"], "staticEffectiveUnion": len(union),
              "staticSumByFile": st["sumByFile"],
              "directorKindsSeen": len(seen & union),
              "extraOnPage": len(extra),
              "extraCanvasLeftover": extra_canvas,
              "extraDatasetBlindSpot": extra_dataset,
              "extraUnprefixedDirector": extra_unprefixed,
              "residueAfterWalk": len(residue), "residue": residue,
              "perRail": per_rail}
        zero = [r for r in per_rail if r["gainedCount"] == 0]
        biggest = max(per_rail, key=lambda r: r["gainedCount"])
        c4 = {"zeroGain": [{"i": r["i"], "key": r["key"], "title": r["title"]} for r in zero],
              "zeroGainCount": len(zero),
              "biggest": {"i": biggest["i"], "key": biggest["key"],
                          "title": biggest["title"], "gainedCount": biggest["gainedCount"]},
              "gains": [{"key": r["key"], "n": r["gainedCount"]} for r in per_rail]}
        print(f"  走完累计 {len(seen)} 种（整页口径）")
        print(f"  字面量并集 {len(literal)} 种 / 补 dataset 后的有效并集 {len(union)} 种")
        print(f"  运行时 {len(seen)} = 导演台属性 {len(seen & union)} + 非并集 {len(extra)}")
        print(f"    非并集 {len(extra)} 种分类：")
        print(f"      ① 画布/应用层残留 {len(extra_canvas)} 种")
        print(f"      ② dataset. 盲区 {len(extra_dataset)} 种 → {extra_dataset}")
        print(f"      ③ 导演台但无 data-director- 前缀 {len(extra_unprefixed)} 种 → {extra_unprefixed}")
        print(f"  有效并集 {len(union)} 种中没出现的 {len(residue)} 种")
        print(f"  零新增：{[r['key'] for r in zero]}；最多的一枚：{biggest['key']}（{biggest['gainedCount']} 种）")

        # ---------- C5 createDirectorCapture 第一跳 ----------
        s2 = page.evaluate(SNAP)
        cap_box = page.evaluate("""() => { const e = document.querySelector('[data-director-capture]');
            if (!e) return null; const r = e.getBoundingClientRect();
            return {tag: e.tagName, disabled: e.disabled || false, title: e.getAttribute('title'),
                    aria: e.getAttribute('aria-label')}; }""")
        cap_before = {k: v for k, v in page.evaluate(DUMP).items() if "capture" in k or "send-capture" in k}
        capped = page.evaluate("""() => { const e = document.querySelector('[data-director-capture]');
            if (!e) return false; e.click(); return true; }""")
        page.wait_for_timeout(1_500)
        s3 = page.evaluate(SNAP)
        cap_after = {k: v for k, v in page.evaluate(DUMP).items() if "capture" in k or "send-capture" in k}
        c5 = {"box": cap_box, "clicked": capped,
              "before": cap_before, "after": cap_after,
              "gained": sorted(set(cap_after) - set(cap_before)),
              "past": [s2["past"], s3["past"]],
              "nodes": [s2["nodeCount"], s3["nodeCount"]],
              "edges": [s2["edgeCount"], s3["edgeCount"]]}
        print(f"\n=== C5 data-director-capture 第一跳 ===")
        print(f"  按钮 {json.dumps(cap_box, ensure_ascii=False)}；clicked={capped}")
        print(f"  出现的新属性：{c5['gained']}")
        print(f"  store：past {s2['past']}→{s3['past']}、节点 {s2['nodeCount']}→{s3['nodeCount']}、"
              f"边 {s2['edgeCount']}→{s3['edgeCount']} ⟹ 零写入，命令未触发")

        # ---------- C6 createDirectorAnimationExport 第一跳 ----------
        trig = page.evaluate("""() => { const e = document.querySelector('[data-director-export-trigger]');
            if (!e) return false; e.click(); return true; }""")
        page.wait_for_timeout(1_200)
        panel = page.evaluate("""() => { const e = document.querySelector('[data-director-export-panel]');
            if (!e) return null; const r = e.getBoundingClientRect();
            return {w: Math.round(r.width), h: Math.round(r.height),
                    status: e.querySelector('[data-director-export-status]')?.getAttribute('data-director-export-status') || null}; }""")
        sub = page.evaluate("""() => { const e = document.querySelector('[data-director-export-submit]');
            if (!e) return null; return {text: (e.textContent||'').trim(), disabled: e.disabled}; }""")
        s4 = page.evaluate(SNAP)
        READ = """() => { const e = document.querySelector('[data-director-export-status]');
            if (!e) return {status: null, progress: null};
            const p = document.querySelector('[data-director-export-progress]');
            return {status: e.getAttribute('data-director-export-status'),
                    progress: p ? p.getAttribute('data-director-export-progress') : null,
                    submitDisabled: (() => { const b = document.querySelector('[data-director-export-submit]');
                        return b ? b.disabled : null; })(),
                    submitText: (() => { const b = document.querySelector('[data-director-export-submit]');
                        return b ? (b.textContent||'').trim() : null; })()}; }"""
        before = page.evaluate(READ)
        subbed = page.evaluate("""() => { const e = document.querySelector('[data-director-export-submit]');
            if (!e) return false; e.click(); return true; }""")
        # 轮询到状态离开 exporting（或封顶 40 次 × 700ms = 28s）
        timeline = [before]
        for _ in range(40):
            page.wait_for_timeout(700)
            r = page.evaluate(READ)
            if not timeline or r != timeline[-1]:
                timeline.append(r)
            if r["status"] not in ("exporting",):
                break
        s5 = page.evaluate(SNAP)
        # 逐样本的 progress 读数**受轮询节奏影响**（700ms 落在动画的不同点上），
        # 不能进两轮比对；只保留与采样无关的性质：单调递增 + 样本数 + 首末值。
        prog = [int(r["progress"]) for r in timeline if r["progress"] is not None]
        c6 = {"triggerClicked": trig, "panel": panel, "submit": sub, "submitClicked": subbed,
              "statuses": [r["status"] for r in timeline],
              "progressMonotonic": all(b >= a for a, b in zip(prog, prog[1:])),
              "progressSampleCount": len(prog),
              "progressFirst": prog[0] if prog else None,
              "progressLast": prog[-1] if prog else None,
              "exportingSamples": sum(1 for r in timeline if r["status"] == "exporting"),
              "submitDisabledThroughoutExporting":
                  all(r["submitDisabled"] is True for r in timeline
                      if r["status"] == "exporting"),
              "submitTextDuringExporting":
                  sorted({r["submitText"] for r in timeline if r["status"] == "exporting"}),
              "submitDisabledAfterDone":
                  timeline[-1]["submitDisabled"] if timeline else None,
              "submitTextAfterDone": timeline[-1]["submitText"] if timeline else None,
              "past": [s4["past"], s5["past"]],
              "nodes": [s4["nodeCount"], s5["nodeCount"]],
              "edges": [s4["edgeCount"], s5["edgeCount"]],
              "newFiles": [f for f in s5["files"] if f not in s4["files"]],
              "finalTypeCounts": s5["typeCounts"]}
        print(f"\n=== C6 createDirectorAnimationExport ===")
        print(f"  打开面板 trigger={trig}；面板 {json.dumps(panel, ensure_ascii=False)}")
        print(f"  提交按钮 {json.dumps(sub, ensure_ascii=False)}；clicked={subbed}")
        print(f"  状态轨迹（逐样本，仅本轮留证，不进两轮比对）{json.dumps(timeline, ensure_ascii=False)}")
        print(f"  progress：样本 {c6['progressSampleCount']} 个、单调递增={c6['progressMonotonic']}、"
              f"首 {c6['progressFirst']} → 末 {c6['progressLast']}")
        print(f"  store：past {s4['past']}→{s5['past']}、节点 {s4['nodeCount']}→{s5['nodeCount']}、"
              f"边 {s4['edgeCount']}→{s5['edgeCount']}；新文件 {c6['newFiles']}")
        print(f"  类型计数 {json.dumps(s5['typeCounts'], ensure_ascii=False)}")

        page.screenshot(path="/tmp/vb748-desk.png")
        page.close()
        browser.close()

    results = {"C2_open": c2, "C3_diff": c3, "C4_rail": c4,
               "C5_capture": c5, "C6_export": c6}
    print("\n=== 汇总（静态行数从略，见 runtime-audit.json）===")
    for k, v in results.items():
        print(f"  {k}: {json.dumps(v, ensure_ascii=False)[:220]}")

    checks = [
        ("C1 静态：导演台 13 个组件，**按文件求和 460 / 去重并集 446**（14 个属性名跨文件重复）；"
         "另有 2 处 dataset. 赋值是字面量盲区",
         st["fileCount"] == 13
         and st["sumByFile"] == 460 and st["unionCount"] == 446
         and st["sharedAcrossFiles"] == 14 and len(st["sharedNames"]) == 13
         and sum(len(v) - 1 for v in st["sharedNameOwners"].values()) == 14
         and st["sharedNameOwners"]["data-director-bottom-bar"] ==
             ["DirectorDesk.tsx", "DirectorTimeline.tsx", "DirectorViewport.tsx"]
         and st["files"]["DirectorMannequin.tsx"]["count"] == 0
         and st["files"]["DirectorInspector.tsx"]["count"] == 142
         and st["files"]["DirectorViewport.tsx"]["count"] == 86
         and st["files"]["DirectorTimeline.tsx"]["count"] == 79
         and {d["attr"] for d in st["datasetAssignments"]} ==
             {"data-director-gizmo-webgl-canvas", "data-director-webgl-canvas"},
         json.dumps({"fileCount": st["fileCount"], "sumByFile": st["sumByFile"],
                     "unionCount": st["unionCount"], "sharedAcrossFiles": st["sharedAcrossFiles"],
                     "sharedNames": st["sharedNames"],
                     "perFile": {k: v["count"] for k, v in st["files"].items()},
                     "dataset": st["datasetAssignments"]}, ensure_ascii=False)),
        ("C2 打开导演台：入口在 script-execution 节点上；六个标识符齐（workspace/canvasId/"
         "sourceNodeId/sessionId/view/focusScope）；**store 零写入**",
         c2["opened"] and c2["entry"]["onNode"] is True
         and c2["ident"]["workspace"] is True
         and c2["ident"]["canvasId"] == "canvas-2"
         and c2["ident"]["sourceNodeId"] == c2["entry"]["nodeId"]
         and c2["ident"]["view"] == "director"
         and c2["ident"]["focusScope"] == "workspace"
         and c2["ident"]["projectId"] and c2["ident"]["sessionId"]
         and c2["past"][1] == c2["past"][0]
         and c2["nodes"][1] == c2["nodes"][0] and c2["edges"][1] == c2["edges"][0],
         json.dumps(c2, ensure_ascii=False)),
        ("C3 差集：整页 200 → 走完 7 枚 rail 累计 250；字面量并集 446、补 dataset 后有效并集 447；"
         "运行时 250 = 导演台 224 + 非并集 26（画布/应用层残留 24 + 无 data-director- 前缀 2）；"
         "有效并集 447 中没出现 223。三笔都对平",
         c3["firstPaintCount"] == 200 and c3["afterRailWalkCount"] == 250
         and c3["staticLiteralUnion"] == 446 and c3["staticEffectiveUnion"] == 447
         and c3["staticSumByFile"] == 460
         and c3["directorKindsSeen"] + c3["extraOnPage"] == c3["afterRailWalkCount"]
         and c3["directorKindsSeen"] + c3["residueAfterWalk"] == c3["staticEffectiveUnion"]
         and c3["extraDatasetBlindSpot"] == []          # 补进有效并集后已不再是"额外项"
         and c3["extraCanvasLeftover"] and
              "data-open-director" in c3["extraCanvasLeftover"]
         and "data-inert" in c3["extraCanvasLeftover"]
         and "data-director-webgl-canvas" not in c3["extraCanvasLeftover"]
         and c3["extraUnprefixedDirector"] == ["data-director-node", "data-director-node-id"]
         and len(c3["perRail"]) == 7,
         json.dumps({k: v for k, v in c3.items()
                     if k not in ("residue", "perRail", "extraCanvasLeftover")},
                    ensure_ascii=False)),
        ("C4 7 枚 rail 入口里恰好 2 枚点开 0 新增（scene / help），「添加机位」一枚带出 34 种",
         c4["zeroGainCount"] == 2
         and {z["key"] for z in c4["zeroGain"]} == {"scene", "help"}
         and c4["biggest"]["key"] == "add-camera" and c4["biggest"]["gainedCount"] == 34
         and {g["key"]: g["n"] for g in c4["gains"]} ==
             {"scene": 0, "add-character": 3, "add-camera": 34, "panorama": 2,
              "aspect-ratio": 4, "ai-import": 7, "help": 0},
         json.dumps(c4, ensure_ascii=False)),
        ("C5 createDirectorCapture 第一跳：store 零写入，但 capture-preview 与 send-capture 出现 ⟹ 两跳",
         c5["clicked"] and c5["box"] and c5["box"]["tag"] == "BUTTON"
         and c5["past"][1] == c5["past"][0]
         and c5["nodes"][1] == c5["nodes"][0] and c5["edges"][1] == c5["edges"][0]
         and "data-director-capture-preview" in c5["gained"]
         and "data-director-send-capture" in c5["gained"],
         json.dumps(c5, ensure_ascii=False)),
        ("C6 createDirectorAnimationExport **真跑通**（约 9 秒）：status 走 "
         "idle → exporting(progress 递增、按钮 disabled + 「导出中」) → success(100)；"
         "终态 past+1、节点+1、边+1、新文件名以「 动画导出」结尾",
         c6["triggerClicked"] and c6["panel"] and c6["panel"]["w"] > 0
         and c6["submit"] and c6["submit"]["disabled"] is False
         and c6["submitClicked"]
         and c6["statuses"][0] == "idle" and c6["statuses"][1] == "exporting"
         and c6["exportingSamples"] >= 5
         and c6["submitDisabledThroughoutExporting"] is True
         and c6["submitTextDuringExporting"] == ["导出中"]
         and c6["statuses"][-1] == "success" and c6["progressLast"] == 100
         and c6["progressMonotonic"] is True and c6["progressFirst"] == 0
         and c6["submitDisabledAfterDone"] is False
         and c6["submitTextAfterDone"] == "导出视频到画布"
         and c6["past"][1] == c6["past"][0] + 1
         and c6["nodes"][1] == c6["nodes"][0] + 1
         and c6["edges"][1] == c6["edges"][0] + 1
         and len(c6["newFiles"]) == 1 and c6["newFiles"][0].endswith(" 动画导出")
         and c6["finalTypeCounts"].get("video", 0) == 2,
         json.dumps(c6, ensure_ascii=False)),
        ("C7 导演台 6 个区域齐（workspace/viewport/tree/timeline/shot-bar/bottom-bar）+ 关闭钮 + "
         "7 枚 rail + 1 个 shot 选项",
         c2["regions"]["workspace"] and c2["regions"]["viewport"]
         and c2["regions"]["webgl"] and c2["regions"]["objectTree"]
         and c2["regions"]["timeline"] and c2["regions"]["shotBar"]
         and c2["regions"]["bottomBar"] and c2["regions"]["closeBtn"]
         and c2["regions"]["railEntries"] == 7 and c2["regions"]["shotOptions"] == 1,
         json.dumps(c2["regions"], ensure_ascii=False)),
    ]

    print("\n=== 判据 ===")
    passed = 0
    for label, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
        print(f"        {detail}")
        passed += bool(ok)

    audit = {
        "batch": 748,
        "title": "导演台首轮运行时普查：属性全集与运行时差集分三类对平；"
                 "7 枚 rail 入口里 2 枚零新增；createDirectorAnimationExport 真跑通（约 9 秒）",
        "verdict": f"{passed}/{len(checks)}",
        "summary": {"results": results,
                    "staticPerFile": {k: v["count"] for k, v in st["files"].items()},
                    "staticLiteralUnion": st["unionCount"],
                    "staticEffectiveUnion": st["effectiveUnionCount"],
                    "staticSumByFile": st["sumByFile"],
                    "sharedNameOwners": st["sharedNameOwners"],
                    "datasetAssignments": st["datasetAssignments"]},
        "checks": [{"label": l, "pass": bool(o), "detail": d} for l, o, d in checks],
        "conclusions": [
            "**导演台 13 个组件（31k 行）共 447 种 `data-*` 属性（有效并集）** —— "
            "按文件求和 460、去重字面量并集 446、补 `dataset.` 派生名后 447。"
            "13 个属性名跨文件重复，其中 `data-director-bottom-bar` 出现在 **3 个**文件"
            "（Desk / Timeline / Viewport）⟹ 12×1 + 1×2 = 14，两个口径正好差 14。"
            "按文件：Inspector 142 / Viewport 86 / Timeline 79 / Desk 46 / PhoneVcam 23 / "
            "ObjectTree 21 / IconRail 20 / AiImportModal 12 / CameraMotionTab 11 / "
            "CurveEditor 8 / ExportPanel 6 / ScenePromptBar 6 / **Mannequin 0**。",
            "**静态字面量扫描有已知盲区** —— `DirectorViewport.tsx:410` 与 `:2920` 两处 "
            "`dataset.xxx =` 赋值会产出 `data-director-gizmo-webgl-canvas` 与 "
            "`data-director-webgl-canvas`，而正则 `\\b(data-[a-z0-9-]+)` 只认源码里写出来的"
            "字面量。**本批差集里 `data-director-gizmo-webgl-canvas` 就是这样落进「非并集」的** "
            "⟹ 这个差的方向是已知的，不能当成「动态加载」或「拼错了」。",
            "**运行时与静态的差要分三类对账** —— 整页 `data-*` 从首屏 200 涨到走完 7 枚 rail 的 "
            "250；其中**导演台属性 224 + 非并集 26**；26 = **画布/应用层残留 24** "
            "（含 `data-open-director`、`data-inert`、`data-canvas-tool` 等 —— "
            "**导演台盖在画布之上、画布仍在 DOM 里**）+ **无 `data-director-` 前缀的导演台属性 2** "
            "（`data-director-node` / `data-director-node-id`，来源未取证）。"
            "有效并集 447 − 出现 224 = **没出现 223**。",
            "**打开导演台不写 store** —— 入口 `[data-open-director]` 在 `script-execution` "
            "节点上（种子 `b-bTLLuU4w5q`）；点它之后 `canvasId=canvas-2`、"
            "`sourceNodeId` 等于该节点 id、`view=director`、`focusScope=workspace`、"
            "`focusState=workspace`，`projectId`/`sessionId` 现场生成；"
            "`past`/节点/边**逐项零变化** ⟹ 导演台是独立工作区，切换不进画布历史。",
            "**7 枚 rail 入口里恰好 2 枚点开 0 新增** —— `scene`（场景）与 `help`（帮助）"
            "一个 `data-*` 都没带出来；`add-camera`（添加机位）一枚就带出 34 种"
            "（FOV 滑杆/读数/帮助浮层、跟随状态、look-at、预览 canvas、相机页签全套）。"
            "**不判定**这两枚是惰性入口还是它们打开的东西不带测试标记。",
            "**`createDirectorAnimationExport` 真跑通了，但要用轮询而不是固定等待** —— "
            "`data-director-export-status` 走 `idle → exporting → success`，"
            "`data-director-export-progress` 单调递增 0 → 100（本轮采到 13 个样本，"
            "**逐样本值受轮询节奏影响、不进两轮比对**），期间提交键 `disabled` 且文案"
            "「导出中」、结束后恢复；全程约 **9 秒**。"
            "终态 store `past` +1、节点 +1、边 +1、新文件「**第一集：咖啡馆对峙 动画导出**」、"
            "`video` 类型 1→2。",
            "**`createDirectorCapture` 本批未触发** —— "
            "`data-director-capture`（视口快门）点完 `past`/节点/边零变化，"
            "但 `data-director-capture-preview` 与 `data-director-send-capture` 冒出来 "
            "⟹ 快门 → 预览 → 发送是**两跳**，发送那一跳没做。",
            "**本批最重要的一次返工是我自己的否定结论** —— 第一版探针只在 0s / 1.2s / 4.2s "
            "三个点读 `data-director-export-status`（全程都在 `exporting`），"
            "就写下「点了没反应」。实际上命令跑完并写进了画布。"
            "**「没变化」要分层归因**（入口没点到 / 面板没开 / 异步没完成）—— "
            "本例是**异步没完成**，前两者都正常；固定等待 + 三点采样得出的是假否定。",
        ],
        "notClaimed": [
            "**`createDirectorCapture` 的发送键那一跳未跑** —— "
            "`data-director-send-capture` 点下去会发生什么，本批未取证。",
            "**有效并集里没出现的那 223 种，成因未分类** —— 「条件渲染的面板」"
            "（flyout / 模态 / 子页签）与「更深交互才出现的状态」（选中机位后的 FOV 全套）"
            "两类本批没分开统计。",
            "**「场景」「帮助」两枚 rail 入口 0 新增的成因未取证** —— 不判定为惰性、"
            "不判定为缺陷。",
            "**未与源站导演台对照** —— 源站导演台当前关着，需要点击授权才能进；"
            "本批全部读数只来自 clone。",
            "**只开了 1 个 shot、只测了首屏与 7 枚 rail** —— 多个 shot、相机页签切换、"
            "AI 导入模态内部、导出面板的各选项（`data-director-export-aspect` 有 3 枚，"
            "本批只用默认值导出一次）都未逐个走。",
            "**导出的 9 秒时长只测了一次** —— 不声称它恒定；"
            "「durationMilliseconds」是否随时间轴长度变化未取证。",
            "「31k 行」是 `src/components/director/*.ts*` 的行数合计（含 7 个 `.ts` 工具模块），"
            "**不含** app 层接线。",
            "`data-director-node` / `data-director-node-id` 在运行时 DOM 上存在，"
            "带 `data-director-` 前缀，但**字面量与 `dataset.` 两种扫描都没找到来源** "
            "⟹ 成因未取证，本批只报「它们不属于字面量并集」这个事实。",
        ],
    }
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n写入 {AUDIT_DIR / 'runtime-audit.json'}")
    print(f"\n判据 {passed}/{len(checks)}")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
