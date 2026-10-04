#!/usr/bin/env python3
"""batch 743 验收：45 处记账入口的门控到底在哪一层 —— 两态逐项差集，不是数量

## 起点

742 查完「有没有调用点」（记账 33 个命令 / 45 处 LibTV 入口），但「有调用点」
不等于「用户点得到」。本批把门控条件测成**两态逐项差集**：

    status:"failed"（种子 fixture） vs  status:"ready"（新建节点）

## 为什么必须逐项比、不能比数量

第一版只比了总数：failed 卡 18 个可交互元素、ready 卡 21 个 ⟹ 差 3。
但「多 3 个」不能回答「哪些命令点不到」——元素增删和命令门控是两件事。
逐项比完才发现：**11 个按钮文案完全一致、差集为空**，
节点内只差 `data-inert` 里的 **1 枚「播放视频」**、工具栏再差 2 枚
（撤销/重做视频处理）⟹ **合计差 3 枚**。

## 决定性读数

### ① 45 处入口的文件归属：VideoNode 一个组件独占 16 处
`VideoNode.tsx` 16 · `app/page.tsx` 12 · `ImageNode.tsx` 5 · `ShotBreakdownNode.tsx` 4 ·
`DirectorDesk.tsx` 3 · `AddNodePanel.tsx` 2 · `CanvasEmptyState.tsx` 1 ·
`DirectorAiImportModal.tsx` 1 · `StoryboardBoard.tsx` 1

### ② 两态逐项差集：按钮文案**完全相同**（11 vs 11），`data-inert` 只差 1 枚

| | 节点内可交互 | button | `data-inert` | input | 1px 宽 input |
|---|---|---|---|---|---|
| 种子卡 `status:"failed"` | 18 | 15 | **3** | 3 | 3 |
| 新建卡 `status:"ready"` | 21 | 17 | **4** | 4 | 3 |

节点内 `data-inert` 差集 = **`["播放视频"]`**（`ready` 多这一枚，`VideoNode.tsx:498`）；
工具栏（节点外）差集 = **`["撤销视频处理", "重做视频处理"]`** ⟹ **合计 3 枚**。
两卡共有的 3 枚：<该功能> / <翻译视频提示词> / <该设置>（都在 `<footer>` 内）。

⟹ **`status` 不是这些记账命令的门控**。第一版按「failed 卡少 3 个元素」
准备写成「failed 卡少 3 个命令入口」，逐项一比就作废了。

### ③ 在 `failed` 卡上点「首帧生成视频」：`past` 0→1，**节点边一点没动**
节点 10→10、边 11→11，但 `data.attempt` 被写入。
这与 `canvasStore.ts` 里 batch 255 的注释写的一致：
「既有 image→video 边（如预设图）时仅记录 attempt 状态、跳过图创建」。

### ④ 在 `ready` 卡上点同一个芯片：节点 +1、边 +1、`past` +1
⟹ 两态的芯片都可达、都记账，**差别是「有没有已有入边图片」，不是 `status`**。

## 判据

C1  45 处 LibTV 记账入口的文件归属分布（VideoNode 独占 16）
C2  两态逐项差集：11 个按钮文案差集**为空**
C3  `data-inert` 差集恰好 1 枚「播放视频」
C4  `failed` 卡上点「首帧生成视频」：`past` 0→1、节点边不变、`data.attempt` 被写入
C5  `ready` 卡上点同一芯片：节点 +1、边 +1、`past` +1（两态都可达）
C6  节点之外的 `data-inert` 两态各有几枚 —— 对账 734 记的「新卡自身 6 枚」
"""

import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch743-2026-10-01"
AUDIT_742 = ROOT / "docs/research/liblib-canvas-batch742-2026-10-01/runtime-audit.json"
BASE = "http://localhost:4317"
W, H = 1280, 1150


def load_entries():
    """直接读 742 的 runtime-audit 取入口表，不重跑普查（口径单一来源）。"""
    a = json.loads(AUDIT_742.read_text(encoding="utf-8"))
    return a["summary"]["libtv_entries"]


# 视频节点内可交互元素清单（含 data-inert 的 aria/title）
INVENTORY = """(id) => {
  const node = document.querySelector(`.react-flow__node[data-id="${id}"]`);
  if (!node) return {found: false};
  const grab = (el) => ({
    tag: el.tagName.toLowerCase(),
    inert: el.hasAttribute('data-inert'),
    aria: el.getAttribute('aria-label') || '',
    title: el.getAttribute('title') || '',
    text: (el.textContent || '').trim().slice(0, 16),
    w: Math.round(el.getBoundingClientRect().width),
    parent: (el.parentElement && el.parentElement.tagName.toLowerCase()) || '',
  });
  // 注意：all 必须先 map(grab) 成对象再筛。第一版直接对**原始 DOM 元素**读
  // e.tag，恒为 undefined ⟹ buttons/inputs 全读成 0（又是一次「读数像模像样、
  // 实际什么都没验到」）。
  const all = [...node.querySelectorAll('button,[role="button"],input,select,a,[data-inert]')]
    .map(grab);
  const inert = all.filter(x => x.inert);
  const buttons = all.filter(e => e.tag === 'button');
  return {
    found: true,
    total: all.length, buttons: buttons.length,
    inertCount: inert.length, inert,
    buttonTexts: buttons.filter(b => b.text).map(b => b.text).sort(),
    inertKeys: inert.map(i => i.aria || i.title || i.text || '?').sort(),
    inputs: all.filter(e => e.tag === 'input').length,
    narrowInputs: all.filter(e => e.tag === 'input' && e.w <= 1).length,
  };
}"""

SNAP = """() => {
  const s = window.__libtv_store.getState();
  const g = s.getActiveCanvas();
  const h = s.historyByCanvas[g.id] || {past: [], future: []};
  const vids = g.nodes.filter(n => n.type === 'video').map(n => ({
    id: n.id, status: (n.data && n.data.status) || null,
    attempt: (n.data && n.data.attempt) || null,
    hasImageEdge: g.edges.some(e => e.target === n.id &&
      (g.nodes.find(x => x.id === e.source) || {}).type === 'image'),
  }));
  return {nodeCount: g.nodes.length, edgeCount: g.edges.length,
          past: h.past.length, future: h.future.length, videos: vids};
}"""


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    entries = load_entries()

    # ---- C1 静态：入口的文件归属 ----
    by_file = Counter()
    total_sites = 0
    for sites in entries.values():
        for path, _ln in sites:
            by_file[path] += 1
            total_sites += 1
    print("=== C1 静态：45 处 LibTV 记账入口的文件归属 ===")
    print(f"  命令 {len(entries)} 个 / 调用点 {total_sites} 处 / 文件 {len(by_file)} 个")
    for path, n in by_file.most_common():
        print(f"    {n:>3}  {path}")
    video_n = by_file.get("src/components/nodes/VideoNode.tsx", 0)

    # 源码侧：batch 255 那条注释（「既有 image→video 边时仅记录 attempt、跳过建图」）
    store = (ROOT / "src/store/canvasStore.ts").read_text(encoding="utf-8").split("\n")
    attempt_comment = next(
        (i + 1 for i, l in enumerate(store)
         if "既有 image→video 边" in l or "既有 image" in l and "跳过" in l), None)
    play_inert = next(
        (i + 1 for i, l in enumerate(
            (ROOT / "src/components/nodes/VideoNode.tsx").read_text(encoding="utf-8").split("\n"))
         if 'aria-label="播放视频"' in l), None)
    print(f"\n  源码：batch 255「跳过建图」注释在 canvasStore.ts:{attempt_comment}；"
          f"「播放视频」data-inert 在 VideoNode.tsx:{play_inert}")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H})
        page.goto(f"{BASE}/?batch743=1", wait_until="networkidle", timeout=90_000)
        page.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
        page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
        page.wait_for_timeout(1_200)

        # ---- 种子的 failed 卡 ----
        seed_id = page.evaluate("""() => {
          const s = window.__libtv_store.getState();
          const v = s.getActiveCanvas().nodes.find(n => n.type === 'video');
          if (!v) return null;
          s.selectElements({nodeIds: [v.id], edgeIds: []});
          return v.id; }""")
        page.wait_for_timeout(900)
        s0 = page.evaluate(SNAP)
        seed = page.evaluate(INVENTORY, seed_id)
        OUTSIDE = """(id) => {
          const node = document.querySelector(`.react-flow__node[data-id="${id}"]`);
          return [...document.querySelectorAll('[data-inert]')].filter(el => !node.contains(el))
            .map(el => {
              const inFlow = Boolean(el.closest('.react-flow__pane,[data-canvas-tool],footer,aside,nav'));
              return {key: el.getAttribute('aria-label') || el.getAttribute('title') ||
                            (el.textContent||'').trim().slice(0,14) || '?',
                      inNodeArea: inFlow};
            }); }"""
        outside_seed = page.evaluate(OUTSIDE, seed_id)

        # ---- 在 failed 卡上点「首帧生成视频」 ----
        p0 = page.evaluate(SNAP)
        clicked = page.evaluate("""(id) => {
          const b = [...document.querySelectorAll(`.react-flow__node[data-id="${id}"] button`)]
            .find(x => (x.textContent || '').includes('首帧生成视频'));
          if (!b) return false; b.click(); return true; }""", seed_id)
        page.wait_for_timeout(1_000)
        p1 = page.evaluate(SNAP)
        v_seed_after = next((v for v in p1["videos"] if v["id"] == seed_id), None)
        v_seed_before = next((v for v in p0["videos"] if v["id"] == seed_id), None)

        # ---- 新建 ready 卡做对照 ----
        new_id = page.evaluate("""() => {
          const s = window.__libtv_store.getState();
          const before = new Set(s.getActiveCanvas().nodes.map(n => n.id));
          s.addNode('video');
          const after = window.__libtv_store.getState().getActiveCanvas().nodes;
          const n = after.find(x => !before.has(x.id));
          window.__libtv_store.getState().selectElements({nodeIds: [n.id], edgeIds: []});
          return n.id; }""")
        page.wait_for_timeout(1_100)
        new = page.evaluate(INVENTORY, new_id)
        outside_new = page.evaluate(OUTSIDE, new_id)
        r0 = page.evaluate(SNAP)
        clicked2 = page.evaluate("""(id) => {
          const b = [...document.querySelectorAll(`.react-flow__node[data-id="${id}"] button`)]
            .find(x => (x.textContent || '').includes('首帧生成视频'));
          if (!b) return false; b.click(); return true; }""", new_id)
        page.wait_for_timeout(1_000)
        r1 = page.evaluate(SNAP)
        v_new_after = next((v for v in r1["videos"] if v["id"] == new_id), None)

        page.close()
        browser.close()

    text_only_new = sorted(set(new["buttonTexts"]) - set(seed["buttonTexts"]))
    text_only_seed = sorted(set(seed["buttonTexts"]) - set(new["buttonTexts"]))
    inert_new = sorted(set(new["inertKeys"]) - set(seed["inertKeys"]))
    inert_seed = sorted(set(seed["inertKeys"]) - set(new["inertKeys"]))
    # 节点外（工具栏/面板）的差集 —— 第一版只比节点内，把这 2 枚漏了。
    # 用**集合差**而不是位置过滤：顶栏那 2 枚（开通会员/积分余额）在两态都在，
    # 会在差里自然抵消；位置过滤（closest footer/nav）不可靠，顶栏也命中。
    out_new = sorted({x["key"] for x in outside_new} - {x["key"] for x in outside_seed})
    out_seed = sorted({x["key"] for x in outside_seed} - {x["key"] for x in outside_new})

    print("\n=== 两态逐项对照 ===")
    print(f"  种子 failed 卡：total={seed['total']} button={seed['buttons']} "
          f"inert={seed['inertCount']} input={seed['inputs']} 窄 input={seed['narrowInputs']}")
    print(f"    按钮文案 {json.dumps(seed['buttonTexts'], ensure_ascii=False)}")
    print(f"    inert 键  {json.dumps(seed['inertKeys'], ensure_ascii=False)}")
    print(f"    节点外 inert {len(outside_seed)} 枚 {json.dumps(outside_seed, ensure_ascii=False)}")
    print(f"  新建 ready 卡：total={new['total']} button={new['buttons']} "
          f"inert={new['inertCount']} input={new['inputs']} 窄 input={new['narrowInputs']}")
    print(f"    按钮文案 {json.dumps(new['buttonTexts'], ensure_ascii=False)}")
    print(f"    inert 键  {json.dumps(new['inertKeys'], ensure_ascii=False)}")
    print(f"    节点外 inert {len(outside_new)} 枚 {json.dumps(outside_new, ensure_ascii=False)}")
    print(f"\n  按钮文案差集  ready-failed={json.dumps(text_only_new, ensure_ascii=False)}  "
          f"failed-ready={json.dumps(text_only_seed, ensure_ascii=False)}  ⟹ "
          f"{'**完全一致**' if not text_only_new and not text_only_seed else '有差异'}")
    print(f"  inert 差集（节点内）ready-failed={json.dumps(inert_new, ensure_ascii=False)}  "
          f"failed-ready={json.dumps(inert_seed, ensure_ascii=False)}")
    print(f"  inert 差集（节点外·工具栏/面板）ready-failed={json.dumps(out_new, ensure_ascii=False)}  "
          f"failed-ready={json.dumps(out_seed, ensure_ascii=False)}")
    print(f"  ⟹ 两态 data-inert 合计差 {len(inert_new)+len(out_new)} 枚")

    print(f"\n=== failed 卡上点「首帧生成视频」（点击成功={clicked}）===")
    print(f"  {json.dumps(p0, ensure_ascii=False)}")
    print(f"  → {json.dumps(p1, ensure_ascii=False)}")
    print(f"  这张卡本身：attempt {v_seed_before['attempt']!r} → {v_seed_after['attempt']!r}；"
          f"已有 image 入边={v_seed_after['hasImageEdge']}")
    print(f"\n=== ready 卡上点同一芯片（点击成功={clicked2}）===")
    print(f"  {json.dumps(r0, ensure_ascii=False)}")
    print(f"  → {json.dumps(r1, ensure_ascii=False)}")
    print(f"  这张卡本身：status={v_new_after['status']}、已有 image 入边={v_new_after['hasImageEdge']}")

    summary = {
        "static": {"commands": len(entries), "sites": total_sites,
                   "byFile": dict(by_file), "videoNodeSites": video_n,
                   "attemptCommentLine": attempt_comment, "playInertLine": play_inert},
        "seed_failed": {k: seed[k] for k in
                        ("total", "buttons", "inertCount", "inputs", "narrowInputs",
                         "buttonTexts", "inertKeys")},
        "new_ready": {k: new[k] for k in
                      ("total", "buttons", "inertCount", "inputs", "narrowInputs",
                       "buttonTexts", "inertKeys")},
        "diff": {"buttonTextsNewOnly": text_only_new, "buttonTextsSeedOnly": text_only_seed,
                 "inertNewOnly": inert_new, "inertSeedOnly": inert_seed,
                 "outsideNewOnly": out_new, "outsideSeedOnly": out_seed,
                 "inertTotalDelta": len(inert_new) + len(out_new)},
        "outsideInert": {"seed": outside_seed, "new": outside_new},
        "clickFailed": {"clicked": clicked, "before": p0, "after": p1,
                        "attemptBefore": v_seed_before["attempt"],
                        "attemptAfter": v_seed_after["attempt"],
                        "hasImageEdge": v_seed_after["hasImageEdge"]},
        "clickReady": {"clicked": clicked2, "before": r0, "after": r1,
                       "status": v_new_after["status"],
                       "hasImageEdge": v_new_after["hasImageEdge"]},
    }
    print("\n=== 汇总 ===")
    for k, v in summary.items():
        print(f"  {k}: {json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v}")

    checks = [
        ("C1 45 处记账入口 / 29 个非空命令（33 键中 4 个空表）；VideoNode 独占 16 处",
         total_sites == 45 and len(entries) == 33
         and len([1 for v in entries.values() if v]) == 29 and video_n == 16
         and by_file.get("src/app/page.tsx") == 12
         and attempt_comment is not None and play_inert is not None,
         json.dumps(summary["static"], ensure_ascii=False)),
        ("C2 两态逐项：11 个按钮文案差集为空（status 不是门控）",
         not text_only_new and not text_only_seed
         and seed["buttonTexts"] == new["buttonTexts"]
         and len(seed["buttonTexts"]) == 11,
         json.dumps({"seed": seed["buttonTexts"], "new": new["buttonTexts"],
                     "newOnly": text_only_new, "seedOnly": text_only_seed},
                    ensure_ascii=False)),
        ("C3 data-inert 差集：节点内 1 枚「播放视频」+ 工具栏 2 枚 = 合计 3 枚",
         seed["inertCount"] == 3 and new["inertCount"] == 4
         and inert_new == ["播放视频"] and inert_seed == []
         and out_new == ["撤销视频处理", "重做视频处理"] and out_seed == [],
         json.dumps({"inNode": {"seed": seed["inertKeys"], "new": new["inertKeys"],
                                "newOnly": inert_new, "seedOnly": inert_seed},
                     "outside": {"seed": outside_seed, "new": outside_new,
                                 "newOnly": out_new, "seedOnly": out_seed}},
                    ensure_ascii=False)),
        ("C4 failed 卡上点「首帧生成视频」：past +1、节点边不变、data.attempt 被写入",
         clicked and p1["past"] == p0["past"] + 1
         and p1["nodeCount"] == p0["nodeCount"] and p1["edgeCount"] == p0["edgeCount"]
         and v_seed_before["attempt"] is None and v_seed_after["attempt"] is not None
         and v_seed_after["hasImageEdge"] is True,
         json.dumps(summary["clickFailed"], ensure_ascii=False)),
        ("C5 ready 卡上同一芯片：节点 +1、边 +1、past +1 ⟹ 两态都可达",
         clicked2 and r1["nodeCount"] == r0["nodeCount"] + 1
         and r1["edgeCount"] == r0["edgeCount"] + 1 and r1["past"] == r0["past"] + 1
         and v_new_after["status"] == "ready",
         json.dumps(summary["clickReady"], ensure_ascii=False)),
        ("C6 对账 734「新卡自身 6 枚」：新卡 节点内 4 + 工具栏 2 = 6；种子 3 + 0 = 3",
         new["inertCount"] + len(out_new) == 6 and seed["inertCount"] + len(out_seed) == 3
         and out_new == ["撤销视频处理", "重做视频处理"] and out_seed == []
         and sorted({x["key"] for x in outside_seed} & set(out_new)) == [],
         json.dumps({"ready": {"inNode": new["inertCount"], "outside": outside_new},
                     "failed": {"inNode": seed["inertCount"], "outside": outside_seed},
                     "outsideNewOnly": out_new, "outsideSeedOnly": out_seed},
                    ensure_ascii=False)),
    ]

    print("\n=== 判据 ===")
    passed = 0
    for label, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
        print(f"        {detail}")
        passed += bool(ok)

    audit = {
        "batch": 743,
        "title": "45 处记账入口的门控：两态逐项差集 —— 按钮文案完全一致，status 不是门控",
        "verdict": f"{passed}/{len(checks)}",
        "summary": summary,
        "checks": [{"label": l, "pass": bool(o), "detail": d} for l, o, d in checks],
        "conclusions": [
            "45 处记账入口分布：VideoNode 16 / app/page.tsx 7 / ImageNode 5 / "
            "ShotBreakdownNode 4 / DirectorDesk 3 / AddNodePanel 2 / 三处各 1。",
            "两态逐项差集：11 个按钮文案**完全一致** ⟹ status:\"failed\" 不是记账命令的门控。",
            "data-inert 差集恰好 1 枚「播放视频」（failed 3 / ready 4）—— "
            "种子上少的就是这一枚，不是「少一整套」。",
            "failed 卡上点「首帧生成视频」真记账（past 0→1）但节点边不变，且 data.attempt "
            "被写入 —— 与 canvasStore.ts 里 batch 255 的注释一致（既有 image→video 边时"
            "只记 attempt、跳过建图）；该卡已有 image 入边=true。",
            "ready 卡上同一芯片节点 +1、边 +1、past +1 ⟹ 两态芯片都可达、都记账。",
        ],
        "relationTo734": [
            "734 记的「新卡自身 6 枚 data-inert（播放视频 + 该功能/翻译视频提示词/该设置 + "
            "撤销视频处理/重做视频处理）」与本批读数方向一致：新卡 4 枚在节点内。",
            "**需要收窄的一处**：734 那句「同一套 UI 在默认画布上看不到那几处」"
            "—— 实测种子 failed 卡上**仍有 3 枚**（该功能 / 翻译视频提示词 / 该设置）"
            "在 `<footer>` 里正常渲染，只少「播放视频」1 枚。"
            "属「读数对、理由需收窄」，纠正记在本批，不改历史批次。",
            "734 的「7 个写点」量的是 data-inert 写点普查（730 的 46），"
            "本批量的是记账命令入口（742 的 29）—— **两个口径不可混**。",
        ],
        "retracted": [
            "**撤回「failed 卡比 ready 卡少 3 个命令入口」**（第一版只比总数）："
            "failed 18 个可交互元素 vs ready 21 个，差 3；但逐项比完 11 个按钮文案"
            "**差集为空**，真正只差 data-inert 里的 1 枚「播放视频」。"
            "「元素总数差」与「命令入口差」是两件事。",
        ],
        "notClaimed": [
            "不声称 3 枚共有的 data-inert 写点是否真的该在 failed 态出现 —— 未取证。",
            "不声称种子 fixture 的 failed 是不是有意 —— 未取证（承 734 待拍板）。",
            "只测了「首帧生成视频」一个芯片在两态下的行为；其余 15 个 VideoNode 命令"
            "未逐个做两态对照。",
            "「窄 input」（3 枚 1px 宽）只记了读数，未查成因（与挂起项「姿态圆点 1px」相关，未取证）。",
            "不声称源站视频卡 failed/ready 两态的控件集合 —— 未取证。",
        ],
    }
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n写入 {AUDIT_DIR / 'runtime-audit.json'}")
    print(f"\n判据 {passed}/{len(checks)}")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
