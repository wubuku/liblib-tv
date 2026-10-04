#!/usr/bin/env python3
"""batch 745 验收：B 档剩下 7 个两段式命令逐个走完 —— 把「入口可达」升成「命令真跑」

## 起点

744 把 16 个记账命令分成 A 档 8（两态都可达）/ B 档 8（只有 `status === "ready"` 可达），
但 B 档里**只实测了「智能续写」的入口**，其余 7 个标为未取证。本批把它们逐个走完。

## 7 个命令的入口链（源码 + 稳定选择器）

| 命令 | 段数 | 入口链 | 面板提交按钮 |
|---|---|---|---|
| `addDerivedNode:1608`（逐帧拉片） | **1** | 工具栏按钮「逐帧拉片」→ `onCreateBreakdown` | — |
| `createVideoFrameCapture:2032`（抽帧） | **1** | `[data-video-frame-menu-trigger]` → `[data-video-frame-kind="current"]` | — |
| `createAudioSplit:1899`（音视频分离） | **1 + 600ms** | `[data-video-audio-menu-trigger]` → `[data-video-audio-mode="av"]`（`VideoNode.tsx:242` `delayMs: 600` 异步任务） | — |
| `createSubtitleErase:1766`（智能去字幕） | **2** | `[data-video-subtitle-menu-trigger]` → `[data-video-subtitle-mode="smart"]` | `[data-subtitle-erase-submit]` |
| `createSmartMatting:2508`（智能抠像） | **2** | `[data-video-picture-edit-menu-trigger]` → `[data-video-picture-edit-action="matting"]` | `[data-smart-matting-generate]` |
| `createPictureEdit:2615`（主体消除） | **2** | `[data-video-picture-edit-menu-trigger]` → `[data-video-picture-edit-action="subjectRemove"]` | `[data-picture-edit-submit]` |
| `createDepthMotionCapture:2143`（深度动作捕捉） | **2** | `[data-video-depth-motion-trigger]` | `[data-depth-motion-submit]` |

四个面板的门控同样是 `status === "ready"`（`VideoNode.tsx:748-801`），
所以这 7 个在 `failed` 卡上**全部不可达**（承 744）。

## 判据

C1  7 个命令的入口链选择器逐个命中（入口那一跳）
C2  3 个两段式命令的面板真的出现（面板根属性命中）
C3  3 个两段式命令的提交按钮命中，且提交后 store 有真实后果
C4  4 个一段式命令（逐帧拉片 / 抽帧 / 音视频分离 / + 抽帧入口）一步到位并记账
C5  每个命令都产出一条历史（`past` +1），无一个空提交
C6  汇总表：7 个命令 × 「段数 / 面板是否出现 / 节点边变化 / past」
"""

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch745-2026-10-01"
BASE = "http://localhost:4317"
W, H = 1280, 1150

# 7 个 B 档命令的入口链（不含面板提交）
CHAINS = [
    {"cmd": "addDerivedNode", "label": "逐帧拉片", "steps": 1,
     "open": "text:逐帧拉片", "wait": 1200},
    {"cmd": "createVideoFrameCapture", "label": "抽帧", "steps": 1,
     "open": "sel:[data-video-frame-menu-trigger]|[data-video-frame-kind=\"current\"]",
     "wait": 1200},
    {"cmd": "createAudioSplit", "label": "音视频分离", "steps": 1,
     "open": "sel:[data-video-audio-menu-trigger]|[data-video-audio-mode=\"av\"]",
     "wait": 2200},   # VideoNode.tsx:242 的 delayMs: 600，异步任务完成后才落 store
    {"cmd": "createSubtitleErase", "label": "智能去字幕", "steps": 2,
     "open": "sel:[data-video-subtitle-menu-trigger]|[data-video-subtitle-mode=\"smart\"]",
     "panel": "[data-subtitle-erase-panel]", "submit": "[data-subtitle-erase-submit]",
     "wait": 1200},
    {"cmd": "createSmartMatting", "label": "智能抠像", "steps": 2,
     "open": "sel:[data-video-picture-edit-menu-trigger]|[data-video-picture-edit-action=\"matting\"]",
     "panel": "[data-smart-matting-panel]", "submit": "[data-smart-matting-generate]",
     "wait": 1200},
    # 这两个还有**第三层门控：视频时长**（VideoNode.tsx:265 / :338 / :342）：
    # >15 秒或 <2.5 秒直接 return 并弹 feedback 横幅。新建卡默认时长 30 秒 ⟹ 被拒。
    {"cmd": "createPictureEdit", "label": "主体消除", "steps": 2,
     "open": "sel:[data-video-picture-edit-menu-trigger]|[data-video-picture-edit-action=\"subjectRemove\"]",
     "panel": "[data-picture-edit-panel]", "submit": "[data-picture-edit-submit]",
     "feedback": "[data-video-picture-edit-feedback]",
     "durationGate": True, "wait": 1200},
    {"cmd": "createDepthMotionCapture", "label": "深度动作捕捉", "steps": 2,
     "open": "sel:[data-video-depth-motion-trigger]",
     "panel": "[data-depth-motion-panel]", "submit": "[data-depth-motion-submit]",
     "feedback": "[data-video-depth-motion-feedback]",
     "durationGate": True, "wait": 1200},
]

SNAP = """() => {
  const s = window.__libtv_store.getState();
  const g = s.getActiveCanvas();
  const h = s.historyByCanvas[g.id] || {past: [], future: []};
  return {nodeCount: g.nodes.length, edgeCount: g.edges.length,
          past: h.past.length, future: h.future.length,
          nodeIds: g.nodes.map(n => n.id).sort(), edgeIds: g.edges.map(e => e.id).sort(),
          types: g.nodes.map(n => n.type).sort()};
}"""

# 点入口链：text 形式按按钮文本点；sel 形式按 "|" 拆成两级，**分两次 evaluate**
OPEN_TEXT_JS = """(label) => {
  const btn = [...document.querySelectorAll('button')]
    .find(b => (b.textContent || '').trim().includes(label));
  if (!btn) return false;
  btn.click(); return true;
}"""
OPEN_CLICK_JS = """(sel) => {
  const el = document.querySelector(sel);
  if (!el) return false;
  el.click(); return true;
}"""
EXISTS_JS = """(sel) => Boolean(document.querySelector(sel))"""

PANEL_JS = """(a) => {
  const panel = document.querySelector(a.panel);
  const sub = document.querySelector(a.submit);
  return {present: Boolean(panel),
          submit: Boolean(sub),
          // 主体消除的提交是 disabled={!canSubmit} —— 没在画面上标记主体就点不动
          submitDisabled: sub ? Boolean(sub.disabled) : null};
}"""

CLICK_JS = """(sel) => {
  const el = document.querySelector(sel);
  if (!el) return false;
  el.click(); return true;
}"""


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H})

        for spec in CHAINS:
            # 每条命令**重载页面** ⟹ 独立基线 past=0（承 743/744 的口径）
            page.goto(f"{BASE}/?batch745=1", wait_until="networkidle", timeout=90_000)
            page.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
            page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
            page.wait_for_timeout(1_100)
            # 新建一张 ready 视频卡并单选（B 档的门控前提）
            vid = page.evaluate("""() => {
              const s = window.__libtv_store.getState();
              const before = new Set(s.getActiveCanvas().nodes.map(n => n.id));
              s.addNode('video');
              const g = window.__libtv_store.getState().getActiveCanvas();
              const v = g.nodes.find(n => !before.has(n.id));
              s.selectElements({nodeIds: [v.id], edgeIds: []});
              return {id: v.id, status: (v.data && v.data.status) || null,
                      duration: (v.data && v.data.durationSeconds) || null}; }""")
            page.wait_for_timeout(1_100)

            b0 = page.evaluate(SNAP)
            # 注意：ok 用**布尔值**累积，不要回头去解析日志字符串。
            # 第一版写 `all(x.endswith("True"))`，而第二条日志以 "(exists=True)" 结尾
            # ⟹ 读出 entryOk=False，**而命令其实真跑了**（节点 +1、audio 节点出现）。
            entry_log, hits = [], []
            if spec["open"].startswith("text:"):
                label = spec["open"][5:]
                hit = page.evaluate(OPEN_TEXT_JS, label)
                hits.append(hit)
                entry_log.append(f"clicked text:{label} -> {hit}")
            else:
                parts = spec["open"][4:].split("|")
                trigger = parts[0]
                hit = page.evaluate(OPEN_CLICK_JS, trigger)
                hits.append(hit)
                entry_log.append(f"clicked {trigger} -> {hit}")
                if len(parts) == 2:
                    item = parts[1]
                    page.wait_for_timeout(700)      # 等 React 重渲染，菜单才会出现
                    seen = page.evaluate(EXISTS_JS, item)
                    entry_log.append(f"{item} 出现={seen}")
                    hit2 = page.evaluate(OPEN_CLICK_JS, item) if seen else False
                    hits.append(hit2)
                    entry_log.append(f"clicked {item} -> {hit2}")
            opened = {"ok": all(hits) and len(hits) >= 1, "log": entry_log}
            # 反馈横幅 1800ms 后自动消失（VideoNode.tsx:270/:331 setTimeout(...,1800)）
            # ⟹ 必须在点完入口后**立刻**读。第一版等到 wait 结束才读，两条都读成 null，
            #    差点把「UI 有说明」这一格判成 FAIL。
            page.wait_for_timeout(400)
            feedback = None
            if spec.get("feedback"):
                feedback = page.evaluate(
                    """(sel) => { const el = document.querySelector(sel);
                       return el ? (el.textContent || '').trim() : null; }""",
                    spec["feedback"])
            page.wait_for_timeout(spec["wait"])

            panel_seen, submit_present, submitted = None, None, False
            if spec["steps"] == 2:
                page.wait_for_timeout(600)
                panel_seen = page.evaluate(
                    PANEL_JS, {"panel": spec["panel"], "submit": spec["submit"]})
                submit_present = panel_seen["submit"]
                if submit_present:
                    submitted = page.evaluate(CLICK_JS, spec["submit"])
                    page.wait_for_timeout(1_600)

            a1 = page.evaluate(SNAP)
            row = {
                "cmd": spec["cmd"], "label": spec["label"], "steps": spec["steps"],
                "nodeStatus": vid["status"], "nodeDuration": vid["duration"],
                "durationGate": spec.get("durationGate", False),
                "rejectedFeedback": feedback,
                "entryOk": opened["ok"], "entryLog": opened["log"],
                "panelPresent": panel_seen["present"] if panel_seen else None,
                "submitPresent": submit_present, "submitted": submitted,
                "submitDisabled": (panel_seen or {}).get("submitDisabled"),
                "past0": b0["past"], "past1": a1["past"],
                "nodes0": b0["nodeCount"], "nodes1": a1["nodeCount"],
                "edges0": b0["edgeCount"], "edges1": a1["edgeCount"],
                "newNodes": sorted(set(a1["nodeIds"]) - set(b0["nodeIds"])),
                "newEdges": sorted(set(a1["edgeIds"]) - set(b0["edgeIds"])),
                "newTypes": sorted(set(a1["types"]) - set(b0["types"])),
            }
            results.append(row)
            print(f"  {spec['label']:8s}（{spec['cmd']}, {spec['steps']} 段）"
                  f" 入口={opened['ok']}"
                  + (f" 面板={panel_seen['present']} 提交按钮={submit_present} 已点={submitted}"
                     if spec["steps"] == 2 else "")
                  + f" → past {row['past0']}→{row['past1']}、"
                  f"节点 {row['nodes0']}→{row['nodes1']}、边 {row['edges0']}→{row['edges1']}"
                  + (f"、新节点类型 {row['newTypes']}" if row["newTypes"] else ""))

        # ---- 时长门控的对照：把 durationSeconds 改成 10 秒再点一次 ----
        duration_gate_rerun = {}
        for spec in [c for c in CHAINS if c.get("durationGate")]:
            page.goto(f"{BASE}/?batch745=dur", wait_until="networkidle", timeout=90_000)
            page.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
            page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
            page.wait_for_timeout(1_100)
            vid = page.evaluate("""() => {
              const s = window.__libtv_store.getState();
              const before = new Set(s.getActiveCanvas().nodes.map(n => n.id));
              s.addNode('video');
              const g = window.__libtv_store.getState().getActiveCanvas();
              const v = g.nodes.find(n => !before.has(n.id));
              s.updateNodeData(v.id, {durationSeconds: 10});      // 只改时长
              window.__libtv_store.getState().selectElements({nodeIds: [v.id], edgeIds: []});
              return {id: v.id, duration: 10}; }""")
            page.wait_for_timeout(1_100)
            d0 = page.evaluate(SNAP)
            parts = spec["open"][4:].split("|")
            page.evaluate(OPEN_CLICK_JS, parts[0])
            page.wait_for_timeout(700)
            if len(parts) == 2:
                page.evaluate(OPEN_CLICK_JS, parts[1])
            page.wait_for_timeout(spec["wait"])
            pan = page.evaluate(
                PANEL_JS, {"panel": spec["panel"], "submit": spec["submit"]})
            page.wait_for_timeout(500)
            pan = page.evaluate(
                PANEL_JS, {"panel": spec["panel"], "submit": spec["submit"]})
            if pan["submit"]:
                page.evaluate(CLICK_JS, spec["submit"])
                page.wait_for_timeout(1_600)
            d1 = page.evaluate(SNAP)
            duration_gate_rerun[spec["cmd"]] = {
                "duration": vid["duration"], "panel": pan["present"],
                "submit": pan["submit"], "submitDisabled": pan["submitDisabled"],
                "past0": d0["past"], "past1": d1["past"],
                "nodes0": d0["nodeCount"], "nodes1": d1["nodeCount"],
            }
            print(f"  [对照] {spec['label']}：duration=10 → 面板={pan['present']}、"
                  f"提交={pan['submit']}、past {d0['past']}→{d1['past']}、"
                  f"节点 {d0['nodeCount']}→{d1['nodeCount']}")

        page.close()
        browser.close()

    gated = [r for r in results if r["durationGate"]]
    clean = [r for r in results if not r["durationGate"]]
    print("\n=== 汇总表：7 个 B 档命令 ===")
    print(f"  {'命令':28s} {'段':>2} {'入口':>4} {'面板':>4} {'past':>7} {'节点':>7} {'边':>7} 新增节点类型")
    for r in results:
        panel = "—" if r["panelPresent"] is None else ("✓" if r["panelPresent"] else "✗")
        print(f"  {r['cmd']:28s} {r['steps']:>2} "
              f"{'✓' if r['entryOk'] else '✗':>4} {panel:>4} "
              f"{str(r['past0']) + '→' + str(r['past1']):>7} "
              f"{str(r['nodes0']) + '→' + str(r['nodes1']):>7} "
              f"{str(r['edges0']) + '→' + str(r['edges1']):>7} "
              f"{','.join(r['newTypes']) or '—'}")

    checks = [
        ("C1 7 个命令的入口链逐个命中（每一跳都点到）",
         len(results) == 7 and all(r["entryOk"] for r in results),
         json.dumps({r["cmd"]: r["entryLog"] for r in results}, ensure_ascii=False)),
        ("C2 无时长门控的 5 个命令：3 个一段式 + 2 个两段式，全部真跑并记账",
         len(clean) == 5 and all(r["past1"] == r["past0"] + 1 for r in clean)
         and all(r["nodes1"] > r["nodes0"] for r in clean),
         json.dumps({r["cmd"]: {"steps": r["steps"], "panel": r["panelPresent"],
                                "past": [r["past0"], r["past1"]],
                                "nodes": [r["nodes0"], r["nodes1"]],
                                "newTypes": r["newTypes"]} for r in clean},
                    ensure_ascii=False)),
        ("C3 两个有时长门控的命令：默认 30 秒下面板不出现、store 不动、**但 UI 有说明**",
         len(gated) == 2
         and all(r["panelPresent"] is False and r["submitPresent"] is False
                 and r["past1"] == r["past0"] and r["nodes1"] == r["nodes0"]
                 and r["rejectedFeedback"] for r in gated)
         and all(r["nodeDuration"] == 30 for r in gated),
         json.dumps({r["cmd"]: {"duration": r["nodeDuration"],
                                "panel": r["panelPresent"],
                                "past": [r["past0"], r["past1"]],
                                "feedback": r["rejectedFeedback"]} for r in gated},
                    ensure_ascii=False)),
        ("C4 时长对照：改成 10 秒后**两个面板都出现**；深度动作捕捉提交后 past +1 且建节点",
         len(duration_gate_rerun) == 2
         and all(v["panel"] and v["submit"] for v in duration_gate_rerun.values())
         and duration_gate_rerun["createDepthMotionCapture"]["past1"]
             == duration_gate_rerun["createDepthMotionCapture"]["past0"] + 1
         and duration_gate_rerun["createDepthMotionCapture"]["nodes1"]
             > duration_gate_rerun["createDepthMotionCapture"]["nodes0"],
         json.dumps(duration_gate_rerun, ensure_ascii=False)),
        ("C4b 主体消除是**三段式**：面板出来了但提交按钮 disabled（要先在画面上标记主体）",
         duration_gate_rerun["createPictureEdit"]["submitDisabled"] is True
         and duration_gate_rerun["createPictureEdit"]["past1"]
             == duration_gate_rerun["createPictureEdit"]["past0"]
         and duration_gate_rerun["createPictureEdit"]["nodes1"]
             == duration_gate_rerun["createPictureEdit"]["nodes0"],
         json.dumps(duration_gate_rerun["createPictureEdit"], ensure_ascii=False)),
        ("C5 每个命令都在 status===\"ready\" 的新卡上验（744 的 B 档门控前提）",
         all(r["nodeStatus"] == "ready" for r in results),
         json.dumps({r["cmd"]: r["nodeStatus"] for r in results}, ensure_ascii=False)),
        ("C6 门控是**时长**、不是别的：只改 durationSeconds 一个字段就从「被拒」变「可跑」",
         all(v["duration"] == 10 for v in duration_gate_rerun.values())
         and all(r["nodeDuration"] == 30 for r in gated),
         json.dumps({"default": {r["cmd"]: r["nodeDuration"] for r in gated},
                     "rerun": {k: v["duration"] for k, v in duration_gate_rerun.items()}},
                    ensure_ascii=False)),
    ]

    print("\n=== 判据 ===")
    passed = 0
    for label, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
        print(f"        {detail}")
        passed += bool(ok)

    audit = {
        "batch": 745,
        "title": "B 档 7 个两段式命令逐个走完：3 个一段式 + 3 个两段式全部真跑并记账",
        "verdict": f"{passed}/{len(checks)}",
        "summary": {"results": results,
                    "clean": [r["cmd"] for r in clean],
                    "gated": [r["cmd"] for r in gated],
                    "durationGateRerun": duration_gate_rerun},
        "checks": [{"label": l, "pass": bool(o), "detail": d} for l, o, d in checks],
        "conclusions": [
            "B 档 7 个命令逐个走完：**5 个真跑通**（逐帧拉片 / 抽帧 / 音视频分离 一步到位；"
            "智能去字幕 / 智能抠像 两段式），每个都 past +1 且新建了真实节点。",
            "音视频分离一步产生 **2 个新节点**（audio-split + silent-video）与 2 条边。",
            "**另 2 个（主体消除 / 深度动作捕捉）还有第三层门控：视频时长** —— "
            "新建卡默认 `durationSeconds: 30`，>15 秒被直接 return。",
            "但**这不是静默失败**：UI 用 `data-video-picture-edit-feedback` / "
            "`data-video-depth-motion-feedback` 横幅写明了原因"
            "（\"视频大于15秒，暂不支持该功能\" / \"视频时长超过处理上限…\"）。",
            "**门控就是时长**：只把 `durationSeconds` 改成 10 秒（其余字段不动），"
            "两个面板立刻出现。深度动作捕捉提交后 past +1 并新建节点。",
            "**主体消除是三段式**：面板出现后提交按钮 `disabled`（`disabled={!canSubmit}`），"
            "要先在画面上标记主体才能提交 —— 本批未做标记那一跳，故它的 createPictureEdit 未被触发。",
            "⟹ 门控是**四层**不是三层：L1 选中且单选 / L2 status===\"ready\"（toolbar 与 5 个面板）/ "
            "L3 durationSeconds 2.5~15 秒（主体消除、深度动作捕捉）/ L4 status!==\"pending\"（generator 面板）。",
        ],
        "notClaimed": [
            "两个时长门控命令只验了上界（30 秒被拒）与 10 秒可用；**下界 <2.5 秒未验**，未取证。",
            "「新建视频卡默认 30 秒」是否有意 —— 未取证（承 734 待拍板① 的同类问题）。",
            "抽帧只验了 `frameKind=\"current\"`；`first`/`last` 三种 kind 未逐个验，未取证。",
            "音视频分离只验了 `av` 模式；`vocals`（人声提取）/ `background`（背景音提取）未验。",
            "主体消除只验了 `subjectRemove`；`subjectModify`/`subjectReplace` 未验。",
            "面板提交后是否有异步任务（如 depth-motion 的 delayMs 520）—— 本批的等待时长可能不够，"
            "但读数已显示节点新建，未见二次变更，未取证是否还有后续阶段。",
            "主体消除的「标记主体」那一跳没做 ⟹ `createPictureEdit` 本批**未真跑**，"
            "只证到「面板能开、提交按钮 disabled」。时长下界 <2.5 秒的提示文案未验。",
            "多选态（selectedNodeCount>1）下这 7 个命令全部不可达那一格未测。",
        ],
    }
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n写入 {AUDIT_DIR / 'runtime-audit.json'}")
    print(f"\n判据 {passed}/{len(checks)}")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
