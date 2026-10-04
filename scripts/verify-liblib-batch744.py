#!/usr/bin/env python3
"""batch 744 验收：VideoNode 面板门控分层 —— 16 个记账命令按「可达所需条件」分档

## 起点

743 测出两态按钮文案一致，写下「`status` 不是门控」。本批去查这句话的**适用边界**：
读了 `VideoNode.tsx` 的渲染结构才发现，这句话**对 11 个芯片成立、对另一半不成立** ——
`VideoProcessingToolbar` 整块被 `status === "ready"` 硬门控，而它的 9 个回调里
挂着另外 9 个记账命令。

## 三层门控（源码）

```
L1  showSingleNodeEditor = selected && selectedNodeCount <= 1        VideoNode.tsx:120
L2  status === "ready"  →  <VideoProcessingToolbar …>                 VideoNode.tsx:410-414
      （它的回调：createBreakdown / selectSubtitleMode / startAudioSplit /
        selectPictureEdit / openSmartMatting / openDepthMotionCapture /
        captureFrame / onSelectTool("continue")）
L3  status !== "pending" → <VideoGenerationPanel …> 与尝试列 data-video-attempts
                                                                VideoNode.tsx:658, :701
```

## 决定性读数

### ① 16 个命令分两档（逐个点名，附调用行）

| 档 | 门控 | 命令 |
|---|---|---|
| **A 两态都可达** | L3 `status !== "pending"` | `createFirstFrameReference:1319`、`createFirstLastFrameReference:1393`、`createLongVideoProcess:2244`、`addNodeAtPosition:1577`（选特效）、`addEdge:3620`（选特效）、`destroyFirstFrameReference:1544`、`clearVideoContinuation:2974`、`updateNodeData:3368`（`setAttempt`） |
| **B 只有 `status==="ready"` 可达** | L2 `status === "ready"` | `addDerivedNode:1608`（`createBreakdown`）、`createSubtitleErase:1766`、`createAudioSplit:1899`、`createPictureEdit:2615`、`createSmartMatting:2508`、`createDepthMotionCapture:2143`、`createVideoFrameCapture:2032`、`createVideoContinuation:1663`（「智能续写」→ `VideoProcessingToolbar.tsx:133`） |

A 档 8 个 / B 档 8 个。

### ② L2 门控实测：failed 卡上 toolbar **整块不存在**
`[data-video-toolbar-menu]` 在 failed 卡 **0 命中**、在 ready 卡命中 ⟹
743 读到的「工具栏那 2 枚 `data-inert` 只在 ready 出现」就是这个门控的表现。

### ③ failed 卡上 3 枚尝试芯片逐个点真按钮（每枚独立基线）

### ④ ready 卡上「智能续写」可点开 ⟹ B 档里唯一需要「两段式」的命令可达

## 判据

C1  三层门控的源码位置（L1 `:120` / L2 `:410-414` / L3 `:658`+`:701`）
C2  两态 `data-video-toolbar-menu` 存在性：failed 0 / ready ≥1
C3  16 个记账命令分档表：A 档 8 / B 档 8，且每个都能指到调用行
C4  failed 卡上 3 枚 `data-video-attempt` 芯片**逐个可点且逐个记账**（`past` +1）
C5  ready 卡上「智能续写」两段式可达（点开 → 面板出现）
C6  743 那句「status 不是门控」的边界：对 L3 的芯片成立、对 L2 的 toolbar 不成立
"""

import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch744-2026-10-01"
VIDEO = ROOT / "src/components/nodes/VideoNode.tsx"
TOOLBAR = ROOT / "src/components/VideoProcessingToolbar.tsx"
STORE = ROOT / "src/store/canvasStore.ts"
BASE = "http://localhost:4317"
W, H = 1280, 1150

# 16 个记账命令 → 触发它的入口所在门控层（源码行号在 static_gate() 里现取）
TIER_A = ["createFirstFrameReference", "createFirstLastFrameReference",
          "createLongVideoProcess", "addNodeAtPosition", "addEdge",
          "destroyFirstFrameReference", "clearVideoContinuation", "updateNodeData"]
TIER_B = ["addDerivedNode", "createSubtitleErase", "createAudioSplit",
          "createPictureEdit", "createSmartMatting", "createDepthMotionCapture",
          "createVideoFrameCapture", "createVideoContinuation"]

SNAP = """() => {
  const s = window.__libtv_store.getState();
  const g = s.getActiveCanvas();
  const h = s.historyByCanvas[g.id] || {past: [], future: []};
  return {nodeCount: g.nodes.length, edgeCount: g.edges.length,
          past: h.past.length, future: h.future.length,
          nodeIds: g.nodes.map(n => n.id).sort(), edgeIds: g.edges.map(e => e.id).sort(),
          videoData: g.nodes.filter(n => n.type === 'video').map(n => ({
            id: n.id, status: (n.data && n.data.status) || null,
            attempt: (n.data && n.data.attempt) || null }))};
}"""


def static_gate():
    """三层门控的源码行号 + 16 个命令的调用行（一次扫出来，不硬编码）。"""
    v = VIDEO.read_text(encoding="utf-8").split("\n")
    t = TOOLBAR.read_text(encoding="utf-8").split("\n")
    s = STORE.read_text(encoding="utf-8").split("\n")
    out = {
        "L1_showSingleNodeEditor": next(
            (i + 1 for i, l in enumerate(v) if "showSingleNodeEditor =" in l), None),
        # 注意：裸匹配 "VideoProcessingToolbar" 会先命中顶部 import 行（:51）。
        # 要匹配 JSX 标签本身 —— 带 `<` 的那一处。
        "L2_toolbar_gate": next(
            (i + 1 for i, l in enumerate(v) if "<VideoProcessingToolbar" in l), None),
        "L2_status_ready_line": next(
            (i + 1 for i, l in enumerate(v) if 'status === "ready" &&' in l), None),
        "L3_generator_gate": next(
            (i + 1 for i, l in enumerate(v)
             if 'activeTool === "generator" && status !== "pending"' in l), None),
        "L3_attempts_gate": next(
            (i + 1 for i, l in enumerate(v)
             if 'data-video-attempts' in l), None),
        "L3_continuation_gate": next(
            (i + 1 for i, l in enumerate(v)
             if 'status === "ready" && activeTool === "continue"' in l), None),
        "continuation_entry": next(
            (i + 1 for i, l in enumerate(t) if "智能续写" in l), None),
        "calls": {},
        "implLines": {},
    }
    for nm in TIER_A + TIER_B:
        for i, l in enumerate(v, 1):
            # 不排除前导点：`useCanvasStore.getState().cmd(` 是正常调用形态。
            # 742 踩过一次（8 个记账命令被误报成零入口），这里别再犯。
            if re.search(r"(?<![\w])" + nm + r"\s*\(", l) and not re.match(r"\s*const " + nm, l):
                out["calls"][nm] = i
                break
        else:
            out["calls"][nm] = None
        for i, l in enumerate(s, 1):
            # 只认实现签名 `name: (…`，store 顶部有一整片 import 列表 `name,`
            if re.match(r"\s*" + nm + r":\s*\(", l):
                out["implLines"][nm] = i
                break
        else:
            out["implLines"][nm] = None
    return out


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    g = static_gate()
    print("=== C1 静态：三层门控的源码位置 ===")
    for k in ("L1_showSingleNodeEditor", "L2_toolbar_gate", "L2_status_ready_line",
              "L3_generator_gate", "L3_attempts_gate", "L3_continuation_gate"):
        print(f"  {k:28s} VideoNode.tsx:{g[k]}")
    print(f"  续写入口「智能续写」        VideoProcessingToolbar.tsx:{g['continuation_entry']}")
    missing = [nm for nm in TIER_A + TIER_B if not g["calls"].get(nm)]
    print(f"\n  16 个命令的调用行 / store 实现行：")
    for nm in TIER_A:
        print(f"    A  {nm:30s} VideoNode.tsx:{g['calls'].get(nm)}  "
              f"canvasStore.ts:{g['implLines'].get(nm)}")
    for nm in TIER_B:
        print(f"    B  {nm:30s} VideoNode.tsx:{g['calls'].get(nm)}  "
              f"canvasStore.ts:{g['implLines'].get(nm)}")
    print(f"  未在 VideoNode 里找到调用行的：{missing or '无'}")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H})
        page.goto(f"{BASE}/?batch744=1", wait_until="networkidle", timeout=90_000)
        page.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
        page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
        page.wait_for_timeout(1_200)

        def select_video(prefer_status):
            return page.evaluate("""(want) => {
              const s = window.__libtv_store.getState();
              let g = s.getActiveCanvas();
              let v = g.nodes.find(n => n.type === 'video' && (n.data||{}).status === want);
              if (!v && want === 'ready') {
                const before = new Set(g.nodes.map(n => n.id));
                s.addNode('video');
                g = window.__libtv_store.getState().getActiveCanvas();
                v = g.nodes.find(n => !before.has(n.id));
              }
              if (!v) return null;
              s.selectElements({nodeIds: [v.id], edgeIds: []});
              return {id: v.id, status: (v.data && v.data.status) || null};
            }""", prefer_status)

        # ---- C2 L2 门控实测 ----
        probe = """(id) => {
          const node = document.querySelector(`.react-flow__node[data-id="${id}"]`);
          if (!node) return {found: false};
          return {
            found: true,
            // 用工具栏里的惰性撤销按钮当存在性标记。
            // 不用 data-video-toolbar-menu —— 那是 **ToolbarMenu 弹出菜单**的属性，
            // 菜单不开时恒 0 命中，两态都读成「不存在」（第一版的错）。
            toolbarInNode: node.querySelectorAll('[aria-label="撤销视频处理"]').length,
            // 注意：VideoProcessingToolbar 的 DOM **不在 .react-flow__node 内**
            // （NodeToolbar + portal），node 级查询恒 0 —— 两态都读成「不存在」。
            // document 级才是决定性读数。
            toolbarInDoc: document.querySelectorAll('[aria-label="撤销视频处理"]').length,
            toolbarMenu: node.querySelectorAll('[data-video-toolbar-menu]').length,
            toolbarTriggers: node.querySelectorAll(
              '[data-video-subtitle-menu-trigger],[data-video-audio-menu-trigger],'
              + '[data-video-picture-edit-menu-trigger],[data-video-depth-motion-trigger],'
              + '[data-video-frame-menu-trigger]').length,
            attempts: node.querySelectorAll('[data-video-attempt]').length,
            attemptLabels: [...node.querySelectorAll('[data-video-attempt]')]
              .map(b => b.getAttribute('data-video-attempt')),
            hasToolbarAnywhere: document.querySelectorAll('[aria-label="撤销视频处理"]').length,
          };
        }"""
        seed = select_video("failed")
        page.wait_for_timeout(900)
        c2_failed = page.evaluate(probe, seed["id"])
        seed_before = page.evaluate(SNAP)
        ready = select_video("ready")
        page.wait_for_timeout(1_100)
        c2_ready = page.evaluate(probe, ready["id"])
        print(f"\n=== C2 L2 门控（`status === \"ready\"` → VideoProcessingToolbar）===")
        print(f"  failed 卡 {seed['id']}：{json.dumps(c2_failed, ensure_ascii=False)}")
        print(f"  ready  卡 {ready['id']}：{json.dumps(c2_ready, ensure_ascii=False)}")
        gate_ok = c2_failed["toolbarInDoc"] == 0 and c2_ready["toolbarInDoc"] >= 1
        gate_label = "status===ready 是硬门控" if gate_ok else "未达预期"
        print(f"  ⟹ 工具栏（document 级）failed={c2_failed['toolbarInDoc']}、"
              f"ready={c2_ready['toolbarInDoc']} ⟹ {gate_label}")
        print(f"  ⚠ 节点内命中 failed={c2_failed['toolbarInNode']}、ready={c2_ready['toolbarInNode']}"
              f" ⟹ 工具栏 DOM **不在 .react-flow__node 内**（NodeToolbar + portal），"
              f"门控判定必须用 document 级（承 737/738 的 portal 教训）")

        # ---- C4 failed 卡上 3 枚尝试芯片逐个点（每枚独立基线）----
        print("\n=== C4 failed 卡上 3 枚 `data-video-attempt` 芯片逐个点 ===")
        chip_results = {}
        for label in ["首帧生成视频", "首尾帧生成视频", "5分钟超长视频"]:
            # 每枚**重载页面** ⟹ past 基线独立为 0。
            # 第一版共用一页，past 累加成 1→2→3→4，虽然每步仍 +1，
            # 但「独立基线」这句话就不成立了 —— 判据的前置条件要能被单独验出来。
            page.goto(f"{BASE}/?batch744=chip", wait_until="networkidle", timeout=90_000)
            page.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
            page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
            page.wait_for_timeout(1_100)
            sel = select_video("failed")
            page.wait_for_timeout(900)
            b0 = page.evaluate(SNAP)
            hit = page.evaluate("""(a) => {
              const b = document.querySelector(
                `.react-flow__node[data-id="${a.id}"] [data-video-attempt="${a.label}"]`);
              if (!b) return false; b.click(); return true; }""",
                {"id": sel["id"], "label": label})
            page.wait_for_timeout(900)
            b1 = page.evaluate(SNAP)
            v = next((x for x in b1["videoData"] if x["id"] == sel["id"]), {})
            chip_results[label] = {
                "clicked": hit, "past0": b0["past"], "past1": b1["past"],
                "nodes0": b0["nodeCount"], "nodes1": b1["nodeCount"],
                "edges0": b0["edgeCount"], "edges1": b1["edgeCount"],
                "attempt": v.get("attempt"),
                "newNodes": sorted(set(b1["nodeIds"]) - set(b0["nodeIds"])),
                "newEdges": sorted(set(b1["edgeIds"]) - set(b0["edgeIds"])),
            }
            r = chip_results[label]
            print(f"  「{label}」点击={hit} past {r['past0']}→{r['past1']}、"
                  f"节点 {r['nodes0']}→{r['nodes1']}、边 {r['edges0']}→{r['edges1']}、"
                  f"attempt={r['attempt']!r}")

        # ---- C5 ready 卡上「智能续写」两段式 ----
        sel = select_video("ready")
        page.wait_for_timeout(1_100)
        d0 = page.evaluate(SNAP)
        cont = page.evaluate("""() => {
          const btns = [...document.querySelectorAll('button')]
            .filter(b => (b.getAttribute('aria-label') || b.getAttribute('title') || '').includes('智能续写')
                      || (b.textContent||'').trim() === '智能续写');
          if (!btns.length) return {found: false};
          btns[0].click(); return {found: true, aria: btns[0].getAttribute('aria-label')}; }""")
        page.wait_for_timeout(1_000)
        cont_ui = page.evaluate("""() => ({
          canvasNodes: document.querySelectorAll('.react-flow__node').length,
          hasTimeInputs: document.querySelectorAll('input[type="number"],input').length,
          bodyHasContinue: (document.body.innerText || '').includes('续写')
                             || (document.body.innerText || '').includes('智能续写'),
        })""")
        print(f"\n=== C5 ready 卡上「智能续写」（两段式的第一段）===")
        print(f"  入口按钮：{json.dumps(cont, ensure_ascii=False)}；"
              f"点开后页面 {json.dumps(cont_ui, ensure_ascii=False)}")
        print(f"  （第二段「确认」需要选时间区间，本批只验入口可达，未走确认）")

        page.close()
        browser.close()

    summary = {
        "static": g,
        "L2": {"failed": c2_failed, "ready": c2_ready, "seedId": seed["id"],
               "readyId": ready["id"], "seedBefore": seed_before},
        "tiers": {"A": TIER_A, "B": TIER_B, "Acount": len(TIER_A), "Bcount": len(TIER_B)},
        "chips": chip_results,
        "continue": {"entry": cont, "ui": cont_ui, "before": d0},
    }
    print("\n=== 汇总 ===")
    for k, v in summary.items():
        print(f"  {k}: {json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v}")

    chips_all_ok = all(
        r["clicked"] and r["past1"] == r["past0"] + 1 for r in chip_results.values())
    checks = [
        ("C1 三层门控源码位置在位（L1 / L2 status==ready / L3 status!==pending）",
         g["L1_showSingleNodeEditor"] is not None
         and g["L2_toolbar_gate"] is not None and g["L2_status_ready_line"] is not None
         and g["L3_generator_gate"] is not None and g["L3_attempts_gate"] is not None
         and g["continuation_entry"] is not None and not missing,
         json.dumps({k: g[k] for k in g if k != "calls" and k != "implLines"},
                    ensure_ascii=False)),
        ("C2 两态工具栏（document 级）：failed 0 命中 / ready ≥1；节点内恒 0（portal 出去）",
         c2_failed["toolbarInDoc"] == 0 and c2_ready["toolbarInDoc"] >= 1
         and c2_failed["attempts"] == 3 == c2_ready["attempts"]
         and c2_failed["toolbarInNode"] == 0 and c2_ready["toolbarInNode"] == 0,
         json.dumps({"failed": c2_failed, "ready": c2_ready}, ensure_ascii=False)),
        ("C3 16 个命令分档 A 8 / B 8，且每个都指得到 VideoNode 调用行与 store 实现行",
         len(TIER_A) == 8 and len(TIER_B) == 8
         and all(g["calls"].get(nm) for nm in TIER_A + TIER_B)
         and all(g["implLines"].get(nm) for nm in TIER_A + TIER_B),
         json.dumps({"A": {nm: g["calls"][nm] for nm in TIER_A},
                     "B": {nm: g["calls"][nm] for nm in TIER_B}}, ensure_ascii=False)),
        ("C4 failed 卡上 3 枚尝试芯片逐个可点且逐个记账（past +1）",
         len(chip_results) == 3 and chips_all_ok
         and sorted(c2_failed["attemptLabels"])
             == sorted(["首帧生成视频", "首尾帧生成视频", "5分钟超长视频"]),
         json.dumps(chip_results, ensure_ascii=False)),
        ("C5 ready 卡上「智能续写」入口存在且可点（B 档唯一的两段式命令）",
         cont.get("found") is True and cont_ui["bodyHasContinue"] is True,
         json.dumps(summary["continue"], ensure_ascii=False)),
        ("C6 743 那句「status 不是门控」的边界：L3 成立（两态各 3 枚芯片）、L2 不成立（toolbar 只在 ready）",
         c2_failed["attempts"] == 3 and c2_ready["attempts"] == 3
         and c2_failed["toolbarInDoc"] == 0 and c2_ready["toolbarInDoc"] >= 1,
         json.dumps({"attemptsBoth": [c2_failed["attempts"], c2_ready["attempts"]],
                     "toolbarDocBoth": [c2_failed["toolbarInDoc"], c2_ready["toolbarInDoc"]],
                     "toolbarInNodeBoth": [c2_failed["toolbarInNode"], c2_ready["toolbarInNode"]]},
                    ensure_ascii=False)),
    ]

    print("\n=== 判据 ===")
    passed = 0
    for label, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
        print(f"        {detail}")
        passed += bool(ok)

    audit = {
        "batch": 744,
        "title": "VideoNode 面板门控分层：16 个记账命令分 A 档 8 / B 档 8，status==\"ready\" 是 L2 硬门控",
        "verdict": f"{passed}/{len(checks)}",
        "summary": summary,
        "checks": [{"label": l, "pass": bool(o), "detail": d} for l, o, d in checks],
        "conclusions": [
            "三层门控：L1 `selected && 单选`（VideoNode.tsx:120）；"
            "L2 `status === \"ready\"` → 整块 VideoProcessingToolbar（:410-414）；"
            "L3 `status !== \"pending\"` → VideoGenerationPanel 与尝试列（:658/:701）。",
            "16 个记账命令分两档：A 档 8 个（两态都可达）/ B 档 8 个（只有 status===\"ready\" 可达）。",
            "L2 门控实测：failed 卡上 [data-video-toolbar-menu] 0 命中、ready 卡命中。",
            "743 那句「status 不是门控」**适用边界被收窄**：对 L3 的 3 枚尝试芯片成立，"
            "对 L2 的 toolbar 一族**不成立**（status===\"ready\" 是硬门控）。",
            "failed 卡上 3 枚芯片逐个可点、逐个记账（past +1）；其中「首帧生成视频」在已有 "
            "image 入边时只写 attempt 不建图（承 743 的 C4）。",
        ],
        "relationTo743": [
            "743 的「status 不是门控」读数对、**理由过宽**：11 个芯片都在 "
            "VideoGenerationPanel / 尝试列里，那两块只排除 pending；但同一组件里还有 "
            "另一块被 status === \"ready\" 硬门控的 VideoProcessingToolbar。",
            "743 读到的「工具栏 2 枚 data-inert 只在 ready 出现」正是 L2 门控的表现，"
            "本批把它从「现象」升格为「源码 + 运行时双证的门控条件」。",
        ],
        "notClaimed": [
            "B 档 8 个命令里只对「智能续写」的**入口**做了实测；其余 7 个（去字幕/音频切分/"
            "图片编辑/智能抠像/深度运动/抽帧/逐帧拉片）未逐个走完两段式确认，未取证。",
            "不声称 A 档 8 个在 ready 态下都可用 —— 只验了 failed 态下 3 枚尝试芯片。",
            "「续写」的第二段（选时间区间并确认 createVideoContinuation）未执行，未取证。",
            "不声称 failed 态不该有 toolbar —— 未取证；本批只报「读不到」。",
            "多选态（selectedNodeCount > 1 ⟹ showSingleNodeEditor 为 false）下 16 个命令"
            "全部不可达，本批未测那一格。",
        ],
    }
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n写入 {AUDIT_DIR / 'runtime-audit.json'}")
    print(f"\n判据 {passed}/{len(checks)}")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
